# Deploy: GitHub Pages (recommended)

Free, cron-friendly, git-as-database. The workflow runs the pipeline twice per trading
day, commits `data/`, and deploys `site/` via Pages.

## First push (3 min)

The repo is already committed and on branch `main`. One command (uses your authed `gh`
CLI; your GitHub username is detected automatically):

```bash
./scripts/push_to_github.sh
```

What it does: commits any leftovers → creates `jiprastyo/idx-daily-recs` (public) if
missing → pushes `main` → enables Pages with source **GitHub Actions** via the API →
triggers the first workflow run.

No `gh` CLI? Manual (2 min):
1. Create the repo at https://github.com/new — name `idx-daily-recs`, **public**
   (Pages is free only on public repos). Do NOT add a README (this repo has one).
2. `git remote add origin https://github.com/<you>/idx-daily-recs.git`
3. `git push -u origin main`
4. Repo → **Settings → Pages → Source: "GitHub Actions"**.

**Verify (1 min):** Actions tab → `daily-recs` run is green → open
`https://<you>.github.io/idx-daily-recs/` → board shows picks and the health table at
the bottom lists every source with its status (dead sources are visible, never silent).

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
