---
title: Pravda Measure Rebuild 2026-11
type: report
date: 2026-11-15
run_id: hosted_20261116T012213Z
tags: [iip/monitor, common-crawl, measurement, correction]
---
> [!info] Navigation
> Tool → `cc_host_presence.py` (`README.md` §8) · Data → `io/runs/hosted_20261116T012213Z.csv` and `.jsonl` · Replaces the reading in the earlier `cc-monitor-*` reports · [[Status & Open Items]]

# Pravda Measure Rebuild

**Result.** The earlier monitor counted how often the string `news-pravda.com` is written in page text. It did not count pages published on that domain. Counting the pages Common Crawl actually fetched from the domain gives a different history: the domain first appears in mid-2024, rises about twelvefold between two consecutive crawls in late 2024, and has declined since. The rise in text mentions at snapshot 2025-30, which the June 2026 poster labeled a "coordinated push," coincides with a fall in hosted pages.

## 1. What was wrong with the first measure

The tracker's count for `news-pravda.com` in each Common Crawl snapshot [1] was read as a sign of content from the network entering the crawl. Three problems:

1. It is a mention count. Any page that writes the domain name is counted, including news coverage and fact-checks about the network.
2. It was not divided by snapshot size.
3. The series was called longitudinal, but every scheduled run queried the same seven 2025 snapshots, which do not change after publication. The reports of 2026-06-25, 2026-07-06 and 2026-08-10 hold the same table.

## 2. Method

`cc_host_presence.py` reads the URL index that Common Crawl publishes with each crawl [2]. For each crawl it counts index records whose URL is on `news-pravda.com` or any subdomain, keeps those fetched with HTTP status 200, and divides by the crawl's total page count from Common Crawl's crawl statistics [3]. Run on 2026-11-15 (UTC 2026-11-16) over all 32 crawls from CC-MAIN-2024-10 to CC-MAIN-2026-43.

Checks made:

- 33 offline tests against a synthetic index, including look-alike hostnames that must not be counted.
- The 15 most recent crawls were counted twice in separate runs. Every field matched.
- For CC-MAIN-2025-30 the full index directory file (970,754 lines) was downloaded and the relevant blocks selected by a plain linear scan. The scan and the tool's search selected the same four blocks.

## 3. Data

Crawl identifiers are year and ISO week. "Text mentions" is the tracker's existing count (run `run_20260810T100011Z`), shown only for the seven snapshots it covers.

| Crawl | Pages hosted (HTTP 200) | Hostnames | Crawl pages | Hosted per million | Text mentions (tracker) | Mentions per million |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| CC-MAIN-2024-10 | 0 | 0 | 3,106,525,566 | 0.00 |  |  |
| CC-MAIN-2024-18 | 0 | 0 | 2,786,800,057 | 0.00 |  |  |
| CC-MAIN-2024-22 | 0 | 0 | 2,709,877,975 | 0.00 |  |  |
| CC-MAIN-2024-26 | 264 | 4 | 2,798,047,026 | 0.09 |  |  |
| CC-MAIN-2024-30 | 640 | 8 | 2,546,630,395 | 0.25 |  |  |
| CC-MAIN-2024-33 | 742 | 8 | 2,315,926,416 | 0.32 |  |  |
| CC-MAIN-2024-38 | 455 | 13 | 2,800,893,463 | 0.16 |  |  |
| CC-MAIN-2024-42 | 1,819 | 14 | 2,495,190,754 | 0.73 |  |  |
| CC-MAIN-2024-46 | 21,161 | 44 | 2,687,811,747 | 7.87 |  |  |
| CC-MAIN-2024-51 | 16,832 | 39 | 2,635,362,356 | 6.39 |  |  |
| CC-MAIN-2025-05 | 19,218 | 50 | 3,031,278,337 | 6.34 | 1746 | 0.58 |
| CC-MAIN-2025-08 | 4,647 | 24 | 2,679,706,056 | 1.73 | 419 | 0.16 |
| CC-MAIN-2025-13 | 15,794 | 40 | 2,740,844,187 | 5.76 | 435 | 0.16 |
| CC-MAIN-2025-18 | 12,602 | 29 | 2,747,336,110 | 4.59 | 820 | 0.30 |
| CC-MAIN-2025-21 | 11,472 | 30 | 2,477,165,602 | 4.63 | 842 | 0.34 |
| CC-MAIN-2025-26 | 10,173 | 29 | 2,385,603,949 | 4.26 | 875 | 0.37 |
| CC-MAIN-2025-30 | 8,238 | 32 | 2,422,580,507 | 3.40 | 3753 | 1.55 |
| CC-MAIN-2025-33 | 6,827 | 29 | 2,442,493,478 | 2.80 |  |  |
| CC-MAIN-2025-38 | 5,707 | 32 | 2,385,964,209 | 2.39 |  |  |
| CC-MAIN-2025-43 | 4,534 | 30 | 2,616,796,857 | 1.73 |  |  |
| CC-MAIN-2025-47 | 3,916 | 29 | 2,294,472,912 | 1.71 |  |  |
| CC-MAIN-2025-51 | 4,068 | 31 | 2,169,087,279 | 1.88 |  |  |
| CC-MAIN-2026-04 | 3,659 | 30 | 2,329,630,755 | 1.57 |  |  |
| CC-MAIN-2026-08 | 3,858 | 30 | 2,166,991,722 | 1.78 |  |  |
| CC-MAIN-2026-12 | 3,649 | 26 | 1,974,845,234 | 1.85 |  |  |
| CC-MAIN-2026-17 | 3,830 | 30 | 2,191,936,300 | 1.75 |  |  |
| CC-MAIN-2026-21 | 3,523 | 30 | 2,164,140,877 | 1.63 |  |  |
| CC-MAIN-2026-25 | 3,811 | 29 | 2,098,491,742 | 1.82 |  |  |
| CC-MAIN-2026-30 | 4,023 | 30 | 2,149,001,456 | 1.87 |  |  |
| CC-MAIN-2026-34 | 4,008 | 32 | 2,139,617,681 | 1.87 |  |  |
| CC-MAIN-2026-39 | 4,232 | 35 | 2,171,285,702 | 1.95 |  |  |
| CC-MAIN-2026-43 | 4,369 | 34 | 2,169,426,757 | 2.01 |  |  |

## 4. What the data show

1. **First appearance.** No page on the domain was fetched in the three crawls of early 2024. The first are in CC-MAIN-2024-26: 264 pages on 4 hostnames.
2. **One large step, in late 2024.** Between CC-MAIN-2024-42 and CC-MAIN-2024-46, hosted pages went from 1,819 to 21,161 (11.6 times) and hostnames from 14 to 44. Per million crawl pages: 0.73 to 7.87.
3. **Decline since.** Apart from one low crawl (CC-MAIN-2025-08), the count fell from 19,218 in CC-MAIN-2025-05 to 3,916 in CC-MAIN-2025-47, and has stayed between 3,500 and 4,400 in every crawl of 2026.
4. **Mentions and hosted pages do not move together.** Over the seven 2025 snapshots where both exist, the rank correlation is 0.11 (Spearman, n = 7). In CC-MAIN-2025-30 mentions rose from 875 to 3,753 while hosted pages fell from 10,173 to 8,238.
5. **Subdomains carry most of it.** The per-hostname breakdown is in the `.jsonl`. At the peak the largest hosts were the French, main, German, Polish, Ukrainian and Greek sites. In the latest crawl the German and French sites hold 60% of the pages.
6. **Little duplication.** At the peak, 21,161 pages had 20,609 distinct URLs and 21,034 distinct content hashes.

## 5. What the data do not show

- **Not publication volume.** These are pages Common Crawl chose to fetch. Each crawl gives a host a page budget from Common Crawl's own ranking and sampling. The late-2024 step can be the site expanding, the crawler raising the site's budget, or both. This data cannot separate them.
- **Not coordination.** A count series carries no information about who published or why. The poster's "step change = coordinated push" label was not supported by the mention series and is not supported by this one.
- **Not training exposure.** Presence in Common Crawl is not inclusion in any model's training data.
- **One domain.** The documented network uses many domains. This is `news-pravda.com` and its subdomains only.
- **Why mentions rose at 2025-30** is unexplained. Whether the tracker's search indexes cover each whole crawl has not been verified [1].

## 6. Next checks

1. Common Crawl publishes host and domain ranks with each web-graph release. Pulling the rank of `news-pravda.com` across late 2024 would test the crawler-budget explanation for the step.
2. Add reference domains of similar size to the watchlist, so a change specific to this domain can be told apart from a change in the crawl as a whole.
3. Sample the pages behind the 2025-30 mention count to see who was writing the domain name.

## References

[1] infini-gram mini, "Search engine and API over Common Crawl 2025 January to July crawls, DCLM-baseline and Pile." [Online]. Available: https://infini-gram-mini.io/
[2] Common Crawl Foundation, "Common Crawl index collections." [Online]. Available: https://data.commoncrawl.org/cc-index/collections/index.html
[3] Common Crawl Foundation, "Crawl statistics: crawl size," monthly.csv, retrieved Nov. 15, 2026. [Online]. Available: https://commoncrawl.github.io/cc-crawl-statistics/plots/crawlsize
