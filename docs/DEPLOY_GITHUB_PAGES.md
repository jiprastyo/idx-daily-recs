# Deploy: GitHub Pages (recommended)

Free, cron-friendly, git-as-database. The workflow runs the pipeline twice per trading
day, commits `data/`, and deploys `site/` via Pages.

## One-time setup (5 min)

1. Push this repo to GitHub.
2. Repo **Settings → Pages → Source: "GitHub Actions"** (not branch deploy).
3. Workflow is already at `.github/workflows/daily.yml`; triggers:
   - `cron: '0 1 * * 1-5'` → **08:00 WIB** (after the morning report cluster)
   - `cron: '0 9 * * 1-5'` → **16:00 WIB** (after the post-close cluster)
   - `workflow_dispatch` → manual "Run workflow" button
4. Permissions are declared in the workflow: `contents: write` (commit data),
   `pages: write` + `id-token: write` (deploy).

## What each run does

```
pip install -r requirements.txt
python pipeline.py --commit     # scrape → merge → write data/ + site/
git add data && git commit && git push   # history = the database
upload-pages-artifact site/ → deploy-pages
```

## Cost & limits

- Free: 2,000 action minutes/month public repos (private: 2,000 too); each run ≈ 2–4 min.
- Cron is UTC in workflow files; WIB = UTC+7 (already accounted for above).
- If a scheduled run is delayed, `pipeline.py` still uses the **latest trading day** and
  `no_new` states are not errors.

## Changing schedule

Edit the `cron:` lines in `.github/workflows/daily.yml`:

| Desired | cron (UTC) |
|---|---|
| 08:00 & 16:00 WIB (default) | `0 1 * * 1-5`, `0 9 * * 1-5` |
| once daily 16:00 WIB | `0 9 * * 1-5` |
| include weekends | remove `1-5` |

## Verification

After first run: open `https://<user>.github.io/<repo>/` → board shows today's picks +
per-source health table. Check `data/health.json` in the repo for per-source status.
