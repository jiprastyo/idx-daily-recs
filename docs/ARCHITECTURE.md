# Architecture

```
            ┌───────────────────────────────  SCHEDULER  ───────────────────────────────┐
            │  GitHub Actions cron (08:00 & 16:00 WIB)  ·  local cron  ·  Termux/a-Shell │
            └──────────────────────────────────────┬─────────────────────────────────────┘
                                                   ▼
        ┌────────────────────────────────────  pipeline.py  ────────────────────────────┐
        │  for each source in scrapers/ :                                              │
        │    → fetch (HTTP GET/POST, YouTube RSS, optional X via local `xurl`)          │
        │    → extract records (ticker, action, target…) from HTML/PDF/JSON            │
        │    → every record: {date, source, ticker, action, …, source_url, scraped_at} │
        │  merge with data/recommendations.json by record id (no duplicates)            │
        │  write data/recommendations.json + data/health.json + data/latest.json        │
        └──────────────────────────────────────┬─────────────────────────────────────────┘
                                               ▼
                          ┌──────────────  site generator  ──────────────┐
                          │  site/index.html (single file, zero deps:   │
                          │  inline JSON + vanilla JS filters/tables)    │
                          └──────────────────────┬───────────────────────┘
                                                 ▼
                          GitHub Pages (static) · local http.server · any phone browser
```

## Layers

1. **Scrapers** (`scrapers/`) — one module per technique:
   - `api_sources.py` — JSON APIs: Shinhan `getData`, Minna Padi `daily-reports-ajax`, Verdhana research site, Yuanta homepage feed.
   - `lister_pdf.py` — "listing page → today's report → PDF/HTML → text" pattern for Tier A firms.
   - `page_embed.py` — NH Korindo (HTML article), Ajaib (HTML article).
   - `yt_rss.py` — YouTube channel RSS (no API key) for RHB, BNI, Mirae, Phillip, Maybank, Sinarmas, KAF.
   - `x_sources.py` — optional: X handles via local `xurl` CLI (needs credentials; skipped otherwise).
2. **Pipeline** (`pipeline.py`) — orchestrates, merges, writes JSON + builds the site.
3. **Site** (`site/index.html`) — generated, static, self-contained.

## Record schema (`data/recommendations.json`)

```json
{
  "id": "sha1(source|date|ticker|action|url)[:12]",
  "date": "2026-07-31",
  "source": "samuel",
  "source_name": "Samuel Sekuritas Indonesia",
  "ticker": "BBCA",
  "action": "BUY",
  "price": null,
  "target": 1115.0,
  "stop_loss": null,
  "note": "raw line containing the pick",
  "source_url": "https://…/report.pdf",
  "scraped_at": "2026-08-01T09:00:00+07:00",
  "confidence": "high|medium|low"
}
```

- `confidence`: `high` = structured source (API/typed field); `medium` = PDF with TP/target
  parsed; `low` = free-text regex (YouTube titles, narrative PDFs).
- Merging key = `id`; `date` is the **report's** date (WIB), not scrape date.
- All dates are Asia/Jakarta (`zoneinfo`, stdlib — no tzdata dependency on macOS/Ubuntu).

## Health (watchdog)

`data/health.json` per source: `{status: ok|no_new|failed|skipped, error?, last_ok, last_run}`.
The site renders a health table so a dead source (several small brokers' sites return 0
bytes) is visible instead of silently missing.

## Failure semantics

- A source that throws → recorded as `failed` with the exception, pipeline continues.
- A source with no new report for the latest trading day → `no_new` (not an error).
- X sources → `skipped` unless `xurl` is installed and configured locally.
