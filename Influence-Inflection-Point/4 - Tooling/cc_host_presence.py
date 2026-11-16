#!/usr/bin/env python3
"""
cc_host_presence.py  (v0.1.0)
=============================

Hosted-page counter for the "Quantifying the Influence Inflection Point"
project. Companion to corpus_presence_tracker.py.

WHY THIS EXISTS
  corpus_presence_tracker.py counts how often a string such as
  "news-pravda.com" occurs in the *text* of each Common Crawl snapshot. That is
  a MENTION count: it rises when third parties (news reports, fact-checkers,
  link lists) write the domain name, and it is not adjusted for snapshot size.
  It cannot say how much content the domain itself contributed to a crawl.

  This tool answers the other half of the question. It reads Common Crawl's
  own URL index (the CDX index published with every crawl) and counts the
  page captures whose URL is HOSTED on the domain or one of its subdomains.
  It then divides by the crawl's total page count so snapshots of different
  size can be compared.

  Mentions and hosted pages are different measures. Report them separately.

HOW IT WORKS
  Each crawl publishes a sorted, block-compressed URL index under
  https://data.commoncrawl.org/cc-index/collections/<CRAWL>/indexes/ :
    cluster.idx      one line per ~3000-record block: first key, file, offset, length
    cdx-NNNNN.gz     the blocks themselves (concatenated gzip members)
  Keys are SURT-form URLs ("com,news-pravda,usa)/path 20250712..."), sorted
  bytewise. The tool binary-searches cluster.idx with HTTP range requests,
  then range-fetches only the blocks that can contain the domain. No API key
  and no full-index download are needed.

USAGE
  python3 cc_host_presence.py --domains news-pravda.com \\
      --crawls CC-MAIN-2025-05 CC-MAIN-2025-30
  python3 cc_host_presence.py --entities entities/watchlist.csv --all-since 2024-10
  python3 cc_host_presence.py --list-crawls

OUTPUT
  <out>/hosted_<runid>.csv     one row per (domain, crawl)
  <out>/hosted_<runid>.jsonl   same rows plus per-host breakdown

Read-only: issues GET requests against public Common Crawl data only.
License: MIT.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Iterator

__version__ = "0.1.0"

DATA_HOST = "https://data.commoncrawl.org/"
COLLECTIONS_INDEX = DATA_HOST + "cc-index/collections/index.html"
CRAWL_SIZE_CSV = ("https://commoncrawl.github.io/cc-crawl-statistics/"
                  "plots/crawlsize/monthly.csv")
USER_AGENT = (f"iip-cc-host-presence/{__version__} "
              "(research; github.com/bitterbuick/influence-inflection-point)")

DEFAULT_TIMEOUT = 60
MAX_RETRIES = 9                # data.commoncrawl.org answers 503 "SlowDown" under load
BACKOFF_SECONDS = 2.0          # doubled per attempt, capped at BACKOFF_CAP
BACKOFF_CAP = 60.0
POLITE_DELAY = 0.2
PROBE_BYTES = 16 * 1024        # window used for each binary-search probe
SCAN_BYTES = 512 * 1024        # window used for the forward scan
MAX_BLOCKS = 20000             # safety stop: ~60M captures for one domain

CRAWL_RE = re.compile(r"CC-MAIN-(\d{4})-(\d{2})")

# A range fetcher takes (url, first_byte, last_byte_inclusive) and returns bytes.
RangeFetcher = Callable[[str, int, int], bytes]


# ---------------------------------------------------------------------------
# Key handling
# ---------------------------------------------------------------------------
def surt_host(domain: str) -> str:
    """'usa.news-pravda.com' -> 'com,news-pravda,usa'. Leading 'www.' is dropped,
    as Common Crawl's SURT canonicalisation drops it."""
    d = domain.strip().lower().rstrip(".")
    d = re.sub(r"^[a-z]+://", "", d).split("/")[0].split(":")[0]
    if d.startswith("www."):
        d = d[4:]
    if not d or "." not in d or not re.fullmatch(r"[a-z0-9.-]+", d):
        raise ValueError(f"not a plain domain name: {domain!r}")
    return ",".join(reversed(d.split(".")))


def key_bounds(domain: str) -> tuple[bytes, bytes]:
    """Half-open byte range [lo, hi) covering the domain and all subdomains.

    After the host labels a SURT key continues with ')' (0x29, the host itself)
    or ',' (0x2c, a subdomain). No valid hostname character sorts between
    them, and '-' (0x2d) is the next byte up, so [host + ')', host + '-')
    selects exactly the host and its subdomains and excludes look-alikes such
    as 'news-pravda-mirror.com'. Hosts on explicit non-default ports
    ('host:8080)') fall outside this range and are not counted."""
    h = surt_host(domain).encode("ascii")
    return h + b")", h + b"-"


def in_bounds(key: bytes, lo: bytes, hi: bytes) -> bool:
    return lo <= key < hi


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
def http_range_fetcher() -> RangeFetcher:
    try:
        import requests
    except ImportError:
        sys.exit("Missing dependency: pip install requests")
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    def fetch(url: str, first: int, last: int) -> bytes:
        last_err = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                r = session.get(url, headers={"Range": f"bytes={first}-{last}"},
                                timeout=DEFAULT_TIMEOUT)
                if r.status_code == 416:      # range starts past end of file
                    return b""
                r.raise_for_status()
                if r.status_code != 206:
                    raise RuntimeError(f"server ignored Range (HTTP {r.status_code})")
                time.sleep(POLITE_DELAY)
                return r.content
            except Exception as exc:  # noqa: BLE001 - retry on anything
                last_err = exc
                if attempt < MAX_RETRIES:
                    time.sleep(min(BACKOFF_CAP, BACKOFF_SECONDS * 2 ** (attempt - 1)))
        raise RuntimeError(f"range fetch failed after {MAX_RETRIES} tries: "
                           f"{url} [{first}-{last}]: {last_err}")
    return fetch


def http_get_text(url: str) -> str:
    import requests
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    return r.text


def http_content_length(url: str) -> int:
    import requests
    r = requests.head(url, headers={"User-Agent": USER_AGENT},
                      timeout=DEFAULT_TIMEOUT, allow_redirects=True)
    r.raise_for_status()
    return int(r.headers["Content-Length"])


# ---------------------------------------------------------------------------
# cluster.idx search
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Block:
    key: bytes          # first "surt timestamp" key in the block
    cdx_file: str
    offset: int
    length: int


def parse_cluster_line(line: bytes) -> Block:
    key, cdx_file, offset, length = line.split(b"\t")[:4]
    return Block(key, cdx_file.decode("ascii"), int(offset), int(length))


def _first_full_line(fetch: RangeFetcher, url: str, pos: int,
                     size: int) -> tuple[int, bytes] | None:
    """Return (start_offset, line) of the first complete line that starts at or
    after byte `pos`. A line starts at 0 or right after a newline."""
    if pos <= 0:
        start, window_from = 0, 0
    else:
        start, window_from = None, pos - 1     # include the preceding byte
    width = PROBE_BYTES
    while True:
        end = min(size, window_from + width) - 1
        if end < window_from:
            return None
        buf = fetch(url, window_from, end)
        if start is None:
            nl = buf.find(b"\n")
            if nl == -1:
                if end >= size - 1:
                    return None
                width *= 4
                continue
            start = window_from + nl + 1
        rel = start - window_from
        nl2 = buf.find(b"\n", rel)
        if nl2 != -1:
            return start, buf[rel:nl2]
        if end >= size - 1:                     # last line without trailing \n
            tail = buf[rel:]
            return (start, tail) if tail else None
        width *= 4


def find_blocks(fetch: RangeFetcher, cluster_url: str, size: int,
                lo: bytes, hi: bytes) -> list[Block]:
    """Blocks of the CDX index that can contain keys in [lo, hi).

    That is the last block whose first key is < lo (its tail may reach into the
    range) plus every block whose first key is in [lo, hi)."""
    # Binary search for the greatest byte offset `a` such that the first full
    # line at or after `a` has key < lo. Invariant: line_at(a) < lo (or a == 0).
    a, b = 0, size
    while b - a > PROBE_BYTES:
        mid = (a + b) // 2
        got = _first_full_line(fetch, cluster_url, mid, size)
        if got is None or got[1].split(b"\t", 1)[0] >= lo:
            b = mid
        else:
            a = got[0]
    # Forward scan from `a`: keep the last block below lo and all blocks in range.
    blocks: list[Block] = []
    predecessor: Block | None = None
    pos, carry, done = a, b"", False
    if a > 0:                                   # align to a line start
        got = _first_full_line(fetch, cluster_url, a, size)
        if got is None:
            return []
        pos = got[0]
    while not done and pos < size:
        buf = carry + fetch(cluster_url, pos, min(size, pos + SCAN_BYTES) - 1)
        pos += len(buf) - len(carry)
        lines = buf.split(b"\n")
        tail = lines.pop()
        if pos < size:
            carry = tail                        # partial line; finish next round
        else:
            carry = b""
            if tail:                            # final line without trailing \n
                lines.append(tail)
        for line in lines:
            if not line:
                continue
            blk = parse_cluster_line(line)
            if blk.key < lo:
                predecessor = blk
            elif blk.key < hi:
                blocks.append(blk)
            else:
                done = True
                break
            if len(blocks) > MAX_BLOCKS:
                raise RuntimeError("block limit exceeded; domain too large")
    return ([predecessor] if predecessor else []) + blocks


# ---------------------------------------------------------------------------
# CDX records
# ---------------------------------------------------------------------------
def iter_cdx_lines(raw: bytes) -> Iterator[bytes]:
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as gz:
        for line in gz:
            yield line.rstrip(b"\n")


def parse_cdx_line(line: bytes) -> tuple[bytes, dict] | None:
    """'surt timestamp {json}' -> (surt, record)."""
    try:
        surt, _ts, payload = line.split(b" ", 2)
        return surt, json.loads(payload)
    except (ValueError, json.JSONDecodeError):
        return None


def host_of_surt(surt: bytes) -> str:
    """'com,news-pravda,usa)/x' -> 'usa.news-pravda.com'."""
    labels = surt.split(b")", 1)[0].decode("ascii", "replace").split(",")
    return ".".join(reversed(labels))


@dataclass
class HostedResult:
    run_id: str
    queried_at: str
    domain: str
    crawl: str
    captures_all: int = 0            # every index record on the domain, any status
    pages_200: int = 0               # successful fetches (HTTP 200)
    pages_200_html: int = 0          # of those, detected as HTML
    distinct_urls_200: int = 0
    distinct_digests_200: int = 0    # distinct content hashes among 200s
    hosts_200: int = 0               # distinct hostnames with >= 1 successful page
    crawl_pages: int | None = None   # Common Crawl's page total for the crawl
    pages_per_million: float | None = None   # pages_200 / crawl_pages * 1e6
    blocks_fetched: int = 0
    error: str | None = None
    host_breakdown: dict = field(default_factory=dict)   # jsonl only


def tally(records: Iterable[tuple[bytes, dict]], lo: bytes, hi: bytes,
          res: HostedResult) -> None:
    urls, digests = set(), set()
    hosts: Counter = Counter()
    for surt, rec in records:
        if not in_bounds(surt, lo, hi):
            continue
        res.captures_all += 1
        if str(rec.get("status")) != "200":
            continue
        res.pages_200 += 1
        mime = (rec.get("mime-detected") or rec.get("mime") or "").lower()
        if "html" in mime:
            res.pages_200_html += 1
        urls.add(rec.get("url"))
        if rec.get("digest"):
            digests.add(rec["digest"])
        hosts[host_of_surt(surt)] += 1
    res.distinct_urls_200 = len(urls)
    res.distinct_digests_200 = len(digests)
    res.hosts_200 = len(hosts)
    res.host_breakdown = dict(hosts.most_common())


def count_domain(fetch: RangeFetcher, crawl: str, domain: str, run_id: str,
                 cluster_size: int, crawl_pages: int | None) -> HostedResult:
    res = HostedResult(run_id, datetime.now(timezone.utc).isoformat(), domain,
                       crawl, crawl_pages=crawl_pages)
    base = f"{DATA_HOST}cc-index/collections/{crawl}/indexes/"
    try:
        lo, hi = key_bounds(domain)
        blocks = find_blocks(fetch, base + "cluster.idx", cluster_size, lo, hi)
        res.blocks_fetched = len(blocks)

        def records() -> Iterator[tuple[bytes, dict]]:
            for blk in blocks:
                raw = fetch(base + blk.cdx_file, blk.offset,
                            blk.offset + blk.length - 1)
                for line in iter_cdx_lines(raw):
                    parsed = parse_cdx_line(line)
                    if parsed:
                        yield parsed
        tally(records(), lo, hi, res)
        if crawl_pages:
            res.pages_per_million = round(res.pages_200 / crawl_pages * 1e6, 4)
    except Exception as exc:  # noqa: BLE001 - record and continue with next crawl
        res.error = str(exc)
    return res


# ---------------------------------------------------------------------------
# Crawl lists and sizes
# ---------------------------------------------------------------------------
def crawl_sort_key(crawl: str) -> tuple[int, int]:
    m = CRAWL_RE.fullmatch(crawl)
    if not m:
        raise ValueError(f"not a crawl id: {crawl!r}")
    return int(m.group(1)), int(m.group(2))


def parse_crawl_list(html: str) -> list[str]:
    return sorted({m.group(0) for m in CRAWL_RE.finditer(html)}, key=crawl_sort_key)


def parse_crawl_sizes(csv_text: str) -> dict[str, int]:
    """Common Crawl's crawl-statistics table -> {crawl: pages}."""
    out = {}
    for row in csv.DictReader(io.StringIO(csv_text)):
        try:
            out[row["crawl"].strip()] = int(row["page"])
        except (KeyError, ValueError, AttributeError):
            continue
    return out


def load_domains(path: Path) -> list[str]:
    """Rows of type 'domain' from a tracker entities CSV (entity,type,query)."""
    with path.open(newline="", encoding="utf-8") as fh:
        return [(r.get("entity") or "").strip() for r in csv.DictReader(fh)
                if (r.get("type") or "").strip() == "domain"
                and (r.get("entity") or "").strip()]


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
CSV_FIELDS = [f for f in HostedResult.__dataclass_fields__ if f != "host_breakdown"]


def save(results: list[HostedResult], out_dir: Path, run_id: str) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"hosted_{run_id}.csv"
    jsonl_path = out_dir / f"hosted_{run_id}.jsonl"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in results:
            w.writerow(asdict(r))
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for r in results:
            fh.write(json.dumps(asdict(r)) + "\n")
    return csv_path, jsonl_path


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--domains", nargs="*", default=[], help="Domains to count")
    p.add_argument("--entities", type=Path,
                   help="Tracker entities CSV; rows with type=domain are used")
    p.add_argument("--crawls", nargs="*", default=[],
                   help="Crawl ids, e.g. CC-MAIN-2025-30")
    p.add_argument("--all-since", metavar="YYYY-WW",
                   help="Use every published crawl from this id onward")
    p.add_argument("--list-crawls", action="store_true",
                   help="Print published crawl ids and exit")
    p.add_argument("--out", type=Path, default=Path("runs"))
    args = p.parse_args()

    published = parse_crawl_list(http_get_text(COLLECTIONS_INDEX))
    if args.list_crawls:
        print("\n".join(published))
        return

    domains = list(args.domains)
    if args.entities:
        domains += load_domains(args.entities)
    domains = list(dict.fromkeys(domains))
    if not domains:
        sys.exit("No domains given (--domains or --entities with type=domain rows).")
    for d in domains:
        key_bounds(d)                            # validate early

    crawls = list(args.crawls)
    if args.all_since:
        floor = crawl_sort_key("CC-MAIN-" + args.all_since)
        crawls += [c for c in published if crawl_sort_key(c) >= floor]
    crawls = sorted(dict.fromkeys(crawls), key=crawl_sort_key)
    if not crawls:
        sys.exit("No crawls given (--crawls or --all-since).")
    unknown = [c for c in crawls if c not in published]
    if unknown:
        sys.exit(f"Not published on data.commoncrawl.org: {unknown}")

    sizes = parse_crawl_sizes(http_get_text(CRAWL_SIZE_CSV))
    fetch = http_range_fetcher()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    print(f"Run hosted_{run_id}: {len(domains)} domain(s) x {len(crawls)} crawl(s)\n")

    results: list[HostedResult] = []
    for crawl in crawls:
        cluster_url = f"{DATA_HOST}cc-index/collections/{crawl}/indexes/cluster.idx"
        try:
            cluster_size = http_content_length(cluster_url)
        except Exception as exc:  # noqa: BLE001
            for d in domains:
                results.append(HostedResult(run_id, datetime.now(timezone.utc).isoformat(),
                                            d, crawl, error=f"cluster.idx: {exc}"))
            print(f"[{crawl}] cluster.idx unavailable: {exc}")
            continue
        for d in domains:
            res = count_domain(fetch, crawl, d, run_id, cluster_size, sizes.get(crawl))
            results.append(res)
            shown = res.error or (f"pages_200={res.pages_200:>7}  "
                                  f"hosts={res.hosts_200:>4}  "
                                  f"per_million={res.pages_per_million}")
            print(f"[{crawl}] {d:<28} {shown}")
        save(results, args.out, run_id)          # checkpoint: keep finished crawls

    csv_path, jsonl_path = save(results, args.out, run_id)
    print(f"\nSaved {len(results)} rows ->\n  {csv_path}\n  {jsonl_path}")
    if any(r.error for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
# CAVEATS (read before drawing inferences):
#  1. A capture count is what Common Crawl FETCHED, not what the site
#     published. Each crawl gives every host a page budget set by Common
#     Crawl's own ranking and sampling, so a change between crawls can come
#     from the crawler's allocation as well as from the site.
#  2. pages_per_million divides by the crawl's total successful page count from
#     Common Crawl's crawl statistics. It removes snapshot-size differences; it
#     does not remove the allocation effect in caveat 1.
#  3. Subdomains are included. For a network that spreads content across
#     country subdomains, hosts_200 is as informative as the page count.
#  4. Common Crawl presence is not inclusion in any model's training data.
#  5. Compare with the tracker's mention counts only as two separate series.
#     The infini-gram-mini indexes are built from the same crawls, but this
#     tool has not verified that each index covers its whole crawl.
# ---------------------------------------------------------------------------
