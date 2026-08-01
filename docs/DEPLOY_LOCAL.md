# Deploy: local machine (macOS / Windows / Linux)

## One-time

```bash
cd ~/Downloads/idx-daily-recs
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python pipeline.py
python -m http.server 8000 -d site
```

## Optional: X sources (needs credentials)

X scraping is off by default. To enable locally:

1. Install/config the `xurl` CLI (your existing setup) so `xurl` is on `PATH`.
2. Run `python pipeline.py --with-x`.
3. X sources appear in the board; without the flag they show `skipped` in health.

## Scheduled runs (cron)

### macOS — launchd (user agent)

`~/Library/LaunchAgents/com.idxdaily.pipeline.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.idxdaily.pipeline</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-lc</string>
    <string>cd /Users/&lt;you&gt;/Downloads/idx-daily-recs &amp;&amp; .venv/bin/python pipeline.py &amp;&amp; .venv/bin/python -m http.server 8000 -d site</string>
  </array>
  <key>StartCalendarInterval</key>
  <array>
    <dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Hour</key><integer>16</integer><key>Minute</key><integer>0</integer></dict>
  </array>
  <key>RunAtLoad</key><true/>
</dict></plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.idxdaily.pipeline.plist
```

### Linux — systemd timer

```ini
# /etc/systemd/system/idxdaily.service
[Service]
WorkingDirectory=/home/<you>/Downloads/idx-daily-recs
ExecStart=/home/<you>/Downloads/idx-daily-recs/.venv/bin/python pipeline.py
```
```ini
# /etc/systemd/system/idxdaily.timer
[Timer]
OnCalendar=Mon-Fri 01:00,09:00   # UTC → 08:00/16:00 WIB
Persistent=true
[Install]
WantedBy=timers.target
```
```bash
sudo systemctl enable --now idxdaily.timer
```

### Windows — Task Scheduler

Two tasks (08:00, 16:00 WIB), action: `python.exe pipeline.py` in the repo dir.
