# Maintenance

> A Hermes skill (`idx-daily-recs`) mirrors this doc set (run/debug/deploy/gotchas).
> Keep both in sync when behavior changes.

## Watchdog behavior

`data/health.json` is written every run. Statuses:

| status | meaning | action |
|---|---|---|
| `ok` | report found + records extracted | none |
| `no_new` | site reachable, no report for latest trading day yet | normal before publish time |
| `failed` | exception / empty page | investigate (below) |
| `skipped` | disabled (X without credentials) | none |

The site shows the health table, so a dead source is visible, not silent.

## Common failure modes & fixes

1. **Site returns 0 bytes / timeout** — several small brokers' domains are flaky or dead
   (BNC, Pacific, Makindo, Profindo, Lotus, Erdikha, Harita, YB, KIS returned 0 bytes in
   the 2026-08-01 survey). The scraper marks `failed`; check the domain manually.
2. **PDF text extraction empty** — the PDF is image-based (scanned). Options: OCR
   (add `marker-pdf`/`pymupdf` OCR), or drop the source. No fabricated records either way.
3. **Listing layout changed** — WordPress sites change themes; update the regex in the
   relevant scraper (`scrapers/lister_pdf.py`). Each scraper is small and isolated.
4. **API token rotation** — Minna Padi embeds `token=` in its page JS; re-read it from
   `https://minnapadi.com/daily-reports` (pattern `listManager.token = "…"`).
5. **YouTube channel ID changes** — the runtime resolver refreshes `channelId` from the
   `@handle` page each run; update the handle in `scrapers/yt_rss.py` if a channel renames.

## Adding a source

1. Add scraper function in the right module (API → `api_sources.py`, listing → `lister_pdf.py`, etc.).
2. Register it in `SOURCE_REGISTRY` in `pipeline.py` (`key, name, func`).
3. Run `python pipeline.py` — new source appears in `health.json` and the site automatically.
4. Update `docs/SOURCES.md` (URL, method, publish-time).

## Manual paste workflow (Instagram / app-only picks)

KGI daily picks, Trimegah Trima+ Picks, RHB/BNI IG posts are behind Instagram's login
wall. To include them without scraping:

1. Open `site/index.html` → "Add manual pick" form (or edit `data/manual.json`).
2. JSON shape: `{"date":"2026-07-31","source":"kgi_ig","ticker":"AADI","action":"BUY","target":null,"note":"…","source_url":"https://instagram.com/…"}`
3. Rerun `python pipeline.py` — manual records merge with the rest, tagged
   `source=manual_*`, `confidence=manual`.

## Known limits (honest)

- Free-text PDFs → `confidence: low`; the extractor takes the first 4-letter token near a
  rating keyword — false tickers are possible (IDR/MSCI/BELI etc. are in a stopword list).
- `confidence: medium` requires an explicit TP/target near the rating.
- Only the **latest** report per source per day is stored (plus history accumulation).
- YouTube titles only (no transcript parsing yet) — tickers in video titles only; channel
  boilerplate words (RHB, MORNING, STOCK…) are filtered, and records whose ticker lands in
  that filter are purged on every run.
- **IDR number format:** Indonesian amounts use dots for thousands (`1.310` = 1310) and
  commas for decimals. All parsing goes through `parse_idr()` in `scrapers/common.py` —
  never `float(s.replace(",", ""))` (that turns `1.310` into 1.31).
- **JS-rendered sites** (MNC, Waterfront, Victoria, Panin, MOST-403) cannot be scraped with
  plain HTTP; they appear as `failed`/`no_new` in health. Options if they become critical:
  headless browser (Playwright) in CI, or a per-site API reverse-engineering pass.
- **Flaky hosts:** shinhan/kiwoom/waterfront/yuanta occasionally hang in DNS/connect from
  some networks. Each source runs on its own daemon thread with a hard timeout
  (`SOURCE_TIMEOUTS` in `pipeline.py`), so one hung site never stalls the run.
- **Module/registry mismatch trap:** the source registry in `pipeline.py` references a
  specific function per key (`page_embed.ajaib`, `lister_pdf.samuel`, …). If you reimplement
  a scraper, update the module the registry points to — a fix to a dead copy does nothing
  (this happened with Ajaib on 2026-08-01). After edits, run
  `python -c "import pipeline"` and check the health table to confirm the new code is live.
