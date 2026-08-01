# Deploy: Android & iPhone

Two usage modes: **view** (zero setup) and **run the pipeline** (Termux / a-Shell).

## View (both platforms — no setup)

The GitHub Pages URL works in any mobile browser:
`https://<user>.github.io/<repo>/`

## Android — run the pipeline in Termux

```bash
pkg install python git openssl
cd ~
git clone https://github.com/<user>/<repo>.git idx-daily-recs
cd idx-daily-recs
python -m venv .venv && source .venv/bin/activate
pip install requests pymupdf     # pymupdf wheels exist for arm64 Android
python pipeline.py
python -m http.server 8000 -d site   # open http://localhost:8000 in browser
```

Notes:
- Termux background cron: `pkg install termux-services` or use `termux-job-scheduler`
  (run at 08:00/16:00 WIB).
- TZ: `termux-setup-storage` is not needed; zoneinfo Asia/Jakarta is bundled.

## iPhone — run the pipeline in a-Shell

```bash
pip install requests pymupdf
git clone https://github.com/<user>/<repo>.git
cd <repo>
python pipeline.py
# serve: a-Shell has no background server; simplest is to open the generated
# site/index.html in Files → share → open in Safari (data is inlined at build time,
# so no server is required)
```

Notes:
- a-Shell supports `pip install` for pure-Python + many wheels; if `pymupdf` fails to
  build on iOS, install only `requests` and accept that PDF-text sources degrade to
  `failed` (HTML/JSON/YouTube sources still work) — see `docs/MAINTENANCE.md`.
- Re-run by hand whenever you want fresh data; cron on iOS requires the Shortcuts app +
  "Run script over SSH" or just manual runs.

## Alternative: fully managed mobile experience

Don't run anything on the phone — point it at the GitHub Pages URL. The site is built
for small screens (single column, filterable). This is the recommended path.
