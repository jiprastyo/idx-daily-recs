# IDX Daily Stock Recommendations Aggregator

Aggregates daily stock research & recommendations from Indonesian securities firms
(Tier A public PDFs + Shinhan/Minna Padi/Verdhana APIs + YouTube/X socials) into a
zero-dependency static site + normalized JSON, deployable to **GitHub Pages**, runnable
**locally** (macOS/Windows/Linux), and viewable/runable from **Android (Termux)** and
**iPhone (a-Shell)**.

**This repo is self-contained and independent of any other project.**

## Quick start (local)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python pipeline.py                 # scrapes, merges data/, builds site/
python -m http.server 8000 -d site # preview at http://localhost:8000
```

Outputs:
- `data/recommendations.json` — normalized records (the database, git-committed)
- `data/health.json` — per-source run status (watchdog)
- `site/index.html` — the dashboard (single file, no runtime deps)

## Deploy

- **GitHub Pages** → [`docs/DEPLOY_GITHUB_PAGES.md`](docs/DEPLOY_GITHUB_PAGES.md) — one-command push: `./scripts/push_to_github.sh`
- **Local machine** → see [`docs/DEPLOY_LOCAL.md`](docs/DEPLOY_LOCAL.md)
- **Android / iPhone** → see [`docs/DEPLOY_MOBILE.md`](docs/DEPLOY_MOBILE.md)

### Push to GitHub (one command)

```bash
./scripts/push_to_github.sh            # gh CLI authed: creates repo, pushes main, enables Pages, triggers first run
./scripts/push_to_github.sh my-name    # custom repo name
```

No `gh` CLI? The script prints the 4 manual steps (create repo → add remote → push → enable Pages).

## Documentation (read these)

| Doc | Contents |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Pipeline flow, data schema, record lifecycle |
| [`docs/SOURCES.md`](docs/SOURCES.md) | Every source: URL, method, publish-time, status |
| [`docs/DEPLOY_GITHUB_PAGES.md`](docs/DEPLOY_GITHUB_PAGES.md) | CI cron + Pages setup, step by step |
| [`docs/DEPLOY_LOCAL.md`](docs/DEPLOY_LOCAL.md) | Local runs, cron (launchd/systemd/Task Scheduler) |
| [`docs/DEPLOY_MOBILE.md`](docs/DEPLOY_MOBILE.md) | Termux (Android) + a-Shell (iPhone) |
| [`docs/MAINTENANCE.md`](docs/MAINTENANCE.md) | Watchdog behavior, adding a source, known limits |

## Data integrity rules

1. **No fabricated data.** Every record carries `source_url` + `scraped_at` + real date.
2. Extraction is conservative: a record is only emitted when a ticker + rating token is
   actually found; otherwise the source is marked in `health.json` (not silently skipped).
3. `pipeline.py` merges by record `id` — reruns never duplicate.
4. Records from sources no longer in the registry (renames, removed scrapers) and YouTube
   records whose ticker is a filter word are purged automatically on each run.
5. All monetary values go through `parse_idr()` (dots = thousands, commas = decimals).
