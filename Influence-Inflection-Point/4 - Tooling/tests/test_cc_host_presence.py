"""Offline tests for cc_host_presence.py. No network: the range fetcher is
replaced by one that serves a synthetic cluster.idx and CDX blocks from memory.

Run from the tooling directory:  python -m pytest tests -q
"""
from __future__ import annotations

import gzip
import json
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cc_host_presence as chp  # noqa: E402


# ---------------------------------------------------------------------------
# Synthetic index
# ---------------------------------------------------------------------------
def make_record(host: str, path: str, status: str = "200", mime: str = "text/html",
                digest: str | None = None) -> tuple[bytes, bytes]:
    surt = (chp.surt_host(host) + ")" + path).encode()
    rec = {"url": f"https://{host}{path}", "status": status, "mime": mime,
           "mime-detected": mime, "digest": digest or f"D{abs(hash((host, path)))}"}
    line = surt + b" 20250101000000 " + json.dumps(rec).encode()
    return surt, line


def build_index(records: list[tuple[bytes, bytes]], block_size: int):
    """Sort records bytewise, pack into gzip-member blocks, build cluster.idx."""
    records = sorted(records, key=lambda r: r[1])
    cdx, cluster_lines = b"", []
    for i in range(0, len(records), block_size):
        chunk = records[i:i + block_size]
        member = gzip.compress(b"\n".join(line for _, line in chunk) + b"\n")
        first_key = b" ".join(chunk[0][1].split(b" ", 2)[:2])
        cluster_lines.append(b"\t".join(
            [first_key, b"cdx-00000.gz", str(len(cdx)).encode(),
             str(len(member)).encode(), str(len(cluster_lines)).encode()]))
        cdx += member
    return b"\n".join(cluster_lines) + b"\n", cdx


def make_fetcher(cluster: bytes, cdx: bytes):
    calls = {"n": 0, "bytes": 0}

    def fetch(url: str, first: int, last: int) -> bytes:
        data = cluster if url.endswith("cluster.idx") else cdx
        calls["n"] += 1
        out = data[first:last + 1]
        calls["bytes"] += len(out)
        return out
    return fetch, calls


def filler(n: int, seed: int) -> list[tuple[bytes, bytes]]:
    rng = random.Random(seed)
    tlds = ["com", "org", "net", "de", "ru", "io"]
    out = []
    for i in range(n):
        name = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(3, 12)))
        out.append(make_record(f"{name}.{rng.choice(tlds)}", f"/p/{i}"))
    return out


TARGET = "news-pravda.com"


def target_records() -> list[tuple[bytes, bytes]]:
    recs = []
    recs += [make_record(TARGET, f"/world/{i}") for i in range(40)]
    recs += [make_record(f"usa.{TARGET}", f"/usa/{i}") for i in range(25)]
    recs += [make_record(f"france.{TARGET}", f"/fr/{i}") for i in range(10)]
    recs += [make_record(TARGET, f"/gone/{i}", status="404") for i in range(7)]
    recs += [make_record(TARGET, f"/moved/{i}", status="301") for i in range(3)]
    recs += [make_record(TARGET, "/feed.xml", mime="application/rss+xml")]
    # two URLs, same content hash
    recs += [make_record(TARGET, "/dup/a", digest="SAME"),
             make_record(TARGET, "/dup/b", digest="SAME")]
    return recs


def lookalikes() -> list[tuple[bytes, bytes]]:
    """Hosts that sort next to the target and must NOT be counted."""
    hosts = ["news-pravda-mirror.com", "news-pravdaa.com", "news-pravd.com",
             "news-pravda.com.evil.org", "anews-pravda.com", "news-pravda.co",
             "news-pravda0.com", "news-pravda.net"]
    return [make_record(h, f"/x/{i}") for h in hosts for i in range(5)]


EXPECTED = dict(captures_all=88, pages_200=78, pages_200_html=77,
                distinct_urls_200=78, distinct_digests_200=77, hosts_200=3)


def run_count(records, block_size, monkeypatch, probe=None, scan=None):
    if probe:
        monkeypatch.setattr(chp, "PROBE_BYTES", probe)
    if scan:
        monkeypatch.setattr(chp, "SCAN_BYTES", scan)
    cluster, cdx = build_index(records, block_size)
    fetch, calls = make_fetcher(cluster, cdx)
    res = chp.count_domain(fetch, "CC-MAIN-2025-30", TARGET, "t", len(cluster), 1_000_000)
    return res, calls, cluster


# ---------------------------------------------------------------------------
# Key handling
# ---------------------------------------------------------------------------
def test_surt_host():
    assert chp.surt_host("news-pravda.com") == "com,news-pravda"
    assert chp.surt_host("USA.News-Pravda.com.") == "com,news-pravda,usa"
    assert chp.surt_host("https://www.news-pravda.com/path") == "com,news-pravda"


@pytest.mark.parametrize("bad", ["", "localhost", "secret US biolabs in Ukraine",
                                 "exa mple.com", "com,news-pravda"])
def test_surt_host_rejects_non_domains(bad):
    with pytest.raises(ValueError):
        chp.surt_host(bad)


def test_key_bounds_include_host_and_subdomains_only():
    lo, hi = chp.key_bounds(TARGET)
    inside = [b"com,news-pravda)/", b"com,news-pravda)/a?b=1",
              b"com,news-pravda,usa)/", b"com,news-pravda,zzz,deep)/x"]
    outside = [b"com,news-pravda-mirror)/", b"com,news-pravdaa)/", b"com,news-pravd)/",
               b"org,evil,com,news-pravda)/", b"com,news-pravda0)/", b"com,news-pravda:8080)/",
               b"com,news-pravd,x)/", b"net,news-pravda)/"]
    assert all(chp.in_bounds(k, lo, hi) for k in inside)
    assert not any(chp.in_bounds(k, lo, hi) for k in outside)


def test_host_of_surt():
    assert chp.host_of_surt(b"com,news-pravda,usa)/x/y") == "usa.news-pravda.com"


# ---------------------------------------------------------------------------
# End-to-end against the synthetic index
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("block_size", [1, 3, 7, 50, 3000])
@pytest.mark.parametrize("probe,scan", [(64, 256), (300, 1024), (16384, 524288)])
def test_counts_exact_across_block_and_window_sizes(block_size, probe, scan, monkeypatch):
    records = filler(4000, seed=1) + target_records() + lookalikes()
    res, _, _ = run_count(records, block_size, monkeypatch, probe, scan)
    assert res.error is None
    for k, v in EXPECTED.items():
        assert getattr(res, k) == v, k
    assert res.host_breakdown == {"news-pravda.com": 43, "usa.news-pravda.com": 25,
                                  "france.news-pravda.com": 10}
    assert res.pages_per_million == 78.0


def test_matches_brute_force_on_random_layouts(monkeypatch):
    for seed in range(25):
        rng = random.Random(seed)
        records = filler(rng.randint(50, 1500), seed=seed + 100) + lookalikes()
        tr = target_records()
        rng.shuffle(tr)
        records += tr[:rng.randint(0, len(tr))]
        lo, hi = chp.key_bounds(TARGET)
        want_all = sum(1 for surt, _ in records if chp.in_bounds(surt, lo, hi))
        res, _, _ = run_count(records, rng.choice([1, 2, 5, 13, 100]), monkeypatch,
                              probe=rng.choice([48, 200, 4096]), scan=rng.choice([128, 2048]))
        assert res.error is None and res.captures_all == want_all, seed


def test_absent_domain_counts_zero(monkeypatch):
    res, _, _ = run_count(filler(3000, seed=2) + lookalikes(), 25, monkeypatch, 256, 1024)
    assert res.error is None
    assert res.captures_all == 0 and res.pages_200 == 0 and res.hosts_200 == 0
    assert res.pages_per_million == 0.0


@pytest.mark.parametrize("host", ["aaa.aa", "zzzzzzzzzzzz.zz"])
def test_domain_at_index_edges(host, monkeypatch):
    """First and last keys in the whole index, with and without trailing newline."""
    records = filler(2000, seed=3) + [make_record(host, f"/e/{i}") for i in range(9)]
    for strip_newline in (False, True):
        cluster, cdx = build_index(records, 11)
        if strip_newline:
            cluster = cluster.rstrip(b"\n")
        monkeypatch.setattr(chp, "PROBE_BYTES", 128)
        monkeypatch.setattr(chp, "SCAN_BYTES", 512)
        fetch, _ = make_fetcher(cluster, cdx)
        res = chp.count_domain(fetch, "CC-MAIN-2025-30", host, "t", len(cluster), None)
        assert res.error is None and res.pages_200 == 9
        assert res.pages_per_million is None


def test_search_reads_a_small_part_of_cluster_idx(monkeypatch):
    records = filler(60000, seed=4) + target_records()
    res, calls, cluster = run_count(records, 20, monkeypatch, probe=2048, scan=8192)
    assert res.pages_200 == EXPECTED["pages_200"]
    assert calls["bytes"] < len(cluster) / 3


def test_fetch_error_is_recorded_not_raised():
    def boom(url, first, last):
        raise RuntimeError("network down")
    res = chp.count_domain(boom, "CC-MAIN-2025-30", TARGET, "t", 10_000, 5)
    assert res.error and "network down" in res.error and res.pages_200 == 0


# ---------------------------------------------------------------------------
# Lists, sizes, inputs
# ---------------------------------------------------------------------------
def test_parse_crawl_list_sorted_unique():
    html = "x CC-MAIN-2025-30 y CC-MAIN-2024-51 z CC-MAIN-2025-05 CC-MAIN-2025-30"
    assert chp.parse_crawl_list(html) == ["CC-MAIN-2024-51", "CC-MAIN-2025-05", "CC-MAIN-2025-30"]


def test_parse_crawl_sizes():
    text = "crawl,digest estim.,page,url\nCC-MAIN-2025-30,1,2422580507,3\nbad,row,x,y\n"
    assert chp.parse_crawl_sizes(text) == {"CC-MAIN-2025-30": 2422580507}


def test_load_domains_takes_only_domain_rows(tmp_path):
    f = tmp_path / "w.csv"
    f.write_text("entity,type,query\nnews-pravda.com,domain,news-pravda.com\n"
                 "secret US biolabs in Ukraine,narrative,x\nBoeing,real,Boeing\n")
    assert chp.load_domains(f) == ["news-pravda.com"]


def test_save_writes_csv_without_breakdown(tmp_path):
    r = chp.HostedResult("r", "t", TARGET, "CC-MAIN-2025-30", pages_200=5,
                         host_breakdown={"a": 5})
    csv_path, jsonl_path = chp.save([r], tmp_path, "r")
    assert "host_breakdown" not in csv_path.read_text().splitlines()[0]
    assert json.loads(jsonl_path.read_text())["host_breakdown"] == {"a": 5}
