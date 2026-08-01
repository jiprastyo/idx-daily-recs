#!/usr/bin/env python3
"""IDX daily-recommendations pipeline: scrape -> merge -> write JSON -> build static site.

Usage:
    python pipeline.py                 # run all sources (X skipped)
    python pipeline.py --with-x        # include local xurl X sources
    python pipeline.py --commit        # CI mode (same behavior; data committed by workflow)
    python pipeline.py --limit samuel,nh,shinhan   # run only these keys
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
import threading
from types import SimpleNamespace

from scrapers import api_sources, lister_pdf, page_embed, yt_rss, x_sources
from scrapers.common import (load_json, save_json, wib_now, latest_trading_day,
                             fetch, fetch_bytes, pdf_text, html_to_text,
                             extract_records, make_record)

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
SITE_DIR = os.path.join(ROOT, "site")
RECS_PATH = os.path.join(DATA_DIR, "recommendations.json")
HEALTH_PATH = os.path.join(DATA_DIR, "health.json")
LATEST_PATH = os.path.join(DATA_DIR, "latest.json")
MANUAL_PATH = os.path.join(DATA_DIR, "manual.json")
KEEP_DAYS = 90
BOARD_DAYS = 7
SOURCE_TIMEOUTS = {"shinhan": 240, "kiwoom": 180}  # these sites are slow/flaky from some networks

SOURCE_REGISTRY = [
    # (key, display name, callable, category)
    ("shinhan", "Shinhan Sekuritas Indonesia", api_sources.shinhan, "api"),
    ("minnapadi", "Minna Padi Investama Sekuritas", api_sources.minnapadi, "api"),
    ("verdhana", "Verdhana Sekuritas Indonesia", api_sources.verdhana, "api"),
    ("yuanta", "Yuanta Sekuritas Indonesia", api_sources.yuanta, "api"),
    ("samuel", "Samuel Sekuritas Indonesia", lister_pdf.samuel, "pdf"),
    ("nh", "NH Korindo Sekuritas Indonesia", page_embed.nh, "html"),
    ("ajaib", "Ajaib Sekuritas", page_embed.ajaib, "html"),
    ("mnc", "MNC Sekuritas", lister_pdf.mnc, "html"),
    ("mega", "Mega Capital Sekuritas", lister_pdf.mega, "pdf"),
    ("waterfront", "Waterfront Sekuritas Indonesia", lister_pdf.waterfront, "pdf"),
    ("kbvalbury", "KB Valbury Sekuritas", lister_pdf.kbvalbury, "html"),
    ("victoria", "Victoria Sekuritas Indonesia", lister_pdf.victoria, "pdf"),
    ("kiwoom", "Kiwoom Sekuritas Indonesia", lister_pdf.kiwoom, "pdf"),
    ("binaartha", "Binaartha Sekuritas", lister_pdf.binaartha, "html"),
    ("phintraco", "Phintraco Sekuritas", lister_pdf.phintraco, "html"),
    ("panin", "Panin Sekuritas Tbk", lister_pdf.panin, "pdf"),
    ("artha", "Artha Sekuritas Indonesia", lister_pdf.artha, "pdf"),
    ("ocbc", "OCBC Sekuritas Indonesia", lister_pdf.ocbc, "html"),
    ("maybank", "Maybank Sekuritas Indonesia", lister_pdf.maybank, "html"),
    ("phillip", "Phillip Sekuritas Indonesia", lister_pdf.phillip, "html"),
    ("uob", "UOB Kay Hian Sekuritas", lister_pdf.uob, "html"),
    ("cgs", "CGS International Sekuritas Indonesia", lister_pdf.cgs, "html"),
    ("sucor", "Sucor Sekuritas", lister_pdf.sucor, "html"),
    ("sf", "Surya Fajar Sekuritas", lister_pdf.sf, "html"),
    ("evergreen", "Evergreen Sekuritas Indonesia", lister_pdf.evergreen, "html"),
    ("reliance", "Reliance Sekuritas Indonesia Tbk", lister_pdf.reliance, "pdf"),
    ("most", "Mandiri Sekuritas (MOST)", lister_pdf.most, "pdf"),
    ("yt_rhb", "RHB Sekuritas (YouTube)", yt_rss.run, "social"),
    ("yt_bni", "BNI Sekuritas (YouTube)", yt_rss.run, "social"),
    ("yt_mirae", "Mirae Asset Sekuritas (YouTube)", yt_rss.run, "social"),
    ("yt_phillip", "Phillip Sekuritas (YouTube)", yt_rss.run, "social"),
    ("yt_maybank", "Maybank Sekuritas (YouTube)", yt_rss.run, "social"),
    ("yt_sinarmas", "Sinarmas Sekuritas (YouTube)", yt_rss.run, "social"),
    ("yt_kaf", "KAF Sekuritas Indonesia (YouTube)", yt_rss.run, "social"),
    ("x", "X sources (optional)", x_sources.run, "social"),
]


def make_ctx(args, today):
    notes: dict = {}

    def note(key, msg):
        notes.setdefault(key, []).append(str(msg))

    return SimpleNamespace(
        today=today.isoformat(),
        with_x=args.with_x,
        note=note,
        notes=notes,
        fetch=fetch,
        fetch_bytes=fetch_bytes,
        pdf_text=pdf_text,
        html_to_text=html_to_text,
        extract_records=extract_records,
        make_record=make_record,
    )


def run_source(key, name, fn, ctx):
    started = wib_now()
    try:
        recs = fn(ctx) or []
        recs = [r for r in recs if r.get("ticker")]
        status = "ok" if recs else "no_new"
        return status, recs, None, started
    except Exception as e:  # noqa: BLE001 — one bad source must not kill the pipeline
        return "failed", [], f"{type(e).__name__}: {e}", started


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-x", action="store_true", help="include local xurl X sources")
    ap.add_argument("--commit", action="store_true", help="CI mode (data committed by workflow)")
    ap.add_argument("--limit", default="", help="comma-separated source keys to run")
    args = ap.parse_args()

    today = latest_trading_day()
    ctx = make_ctx(args, today)

    existing = load_json(RECS_PATH, [])
    by_id = {r["id"]: r for r in existing if isinstance(r, dict)}
    health = load_json(HEALTH_PATH, {})

    limit = {k.strip() for k in args.limit.split(",") if k.strip()}
    registry = SOURCE_REGISTRY
    if limit:
        registry = [s for s in registry if s[0] in limit]

    # Every source runs on its own daemon thread (uninterruptible DNS/SSL hangs on
    # some brokers' sites must not stall the run); each is collected with a hard cap.
    results = []
    launched = []
    for item in registry:
        key, name, fn, cat = item
        if key.startswith("yt_"):
            continue
        box: dict = {}

        def target(box=box, key=key, name=name, fn=fn):
            box["res"] = run_source(key, name, fn, ctx)

        t = threading.Thread(target=target, daemon=True)
        t.start()
        launched.append((item, box, t))

    for item, box, t in launched:
        key, name, fn, cat = item
        t.join(SOURCE_TIMEOUTS.get(key, 120))
        if t.is_alive():
            status, recs, err = "failed", [], f"timed out after {SOURCE_TIMEOUTS.get(key, 120)}s"
            started = wib_now()
        else:
            status, recs, err, started = box["res"]
        if key == "x" and not args.with_x:
            status, err = "skipped", "run with --with-x (local xurl + credentials)"
        results.append((key, name, cat, status, recs, err, started))
        flag = "OK " if status == "ok" else (".. " if status in ("no_new", "skipped") else "!! ")
        print(f"{flag} {key:12s} {status:6s} {len(recs):3d} recs"
              + (f"  [{err}]" if err else ""), flush=True)

    # YouTube channels: single run, one registry row covers all; tag per channel
    yt_keys = [s[0] for s in registry if s[0].startswith("yt_")]
    if yt_keys:
        try:
            yt_recs = yt_rss.run(ctx) or []
        except Exception as e:  # noqa: BLE001
            yt_recs = []
            for k in yt_keys:
                ctx.note(k, f"yt error: {e}")
        for r in yt_recs:
            by_id[r["id"]] = r
        by_channel: dict[str, list] = {}
        for r in yt_recs:
            by_channel.setdefault(r["source"], []).append(r)
        for k in yt_keys:
            recs = by_channel.get(k, [])
            results.append((k, yt_rss.CHANNELS.get(k, (k, ""))[0], "social",
                            "ok" if recs else "no_new", recs, None, wib_now()))

    for key, name, cat, status, recs, err, started in sorted(results):
        for r in recs:
            by_id[r["id"]] = r
        notes = ctx.notes.get(key) or []
        health[key] = {
            "name": name,
            "category": cat,
            "status": status,
            "records": len(recs),
            "error": err,
            "notes": notes[:5],
            "last_run": started.isoformat(timespec="seconds"),
            "last_ok": started.isoformat(timespec="seconds") if status in ("ok", "no_new") else
                       health.get(key, {}).get("last_ok"),
        }

    # manual records (paste workflow, docs/MAINTENANCE.md)
    for r in load_json(MANUAL_PATH, []):
        if isinstance(r, dict) and r.get("ticker"):
            r.setdefault("id", "manual_" + hashlib.sha1(
                json.dumps(r, sort_keys=True).encode()).hexdigest()[:12])
            r.setdefault("scraped_at", wib_now().isoformat(timespec="seconds"))
            r.setdefault("confidence", "manual")
            by_id[r["id"]] = r

    # purge records from sources no longer in the registry (renames, removed scrapers)
    valid_sources = {s[0] for s in SOURCE_REGISTRY}
    yt_noise = getattr(yt_rss, "CHANNEL_NOISE", set())
    records = sorted(
        (r for r in by_id.values()
         if ((r.get("source", "") in valid_sources
              or str(r.get("source", "")).startswith("manual"))
             and not (str(r.get("source", "")).startswith("yt_")
                      and r.get("ticker", "") in yt_noise))),
        key=lambda r: r.get("date", ""), reverse=True)
    cutoff = (wib_now() - datetime.timedelta(days=KEEP_DAYS)).date().isoformat()
    records = [r for r in records if r.get("date", "") >= cutoff]

    save_json(RECS_PATH, records)
    save_json(HEALTH_PATH, health)
    board = [r for r in records if r.get("date", "") >=
             (wib_now() - datetime.timedelta(days=BOARD_DAYS)).date().isoformat()]
    save_json(LATEST_PATH, {"generated_at": wib_now().isoformat(timespec="seconds"),
                            "trading_day": today.isoformat(), "records": board})

    build_site(records, board, health, today)

    ok = sum(1 for h in health.values() if h.get("status") == "ok")
    print(f"\nDONE: {len(records)} records kept · {ok}/{len(health)} sources ok · "
          f"board covers {BOARD_DAYS}d · site/ built")


def build_site(records, board, health, today):
    os.makedirs(SITE_DIR, exist_ok=True)
    sources = [{"key": k, "name": v.get("name", k), "status": v.get("status", "?")}
               for k, v in sorted(health.items())]
    payload = {
        "generated_at": wib_now().strftime("%Y-%m-%d %H:%M WIB"),
        "trading_day": today.isoformat(),
        "records": board,
        "sources": sources,
        "health": health,
    }
    html = SITE_TEMPLATE.replace("__PAYLOAD__", json.dumps(payload, ensure_ascii=False))
    with open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


SITE_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IDX Daily Stock Recommendations</title>
<style>
:root{--bg:#0d1117;--card:#161b22;--line:#30363d;--tx:#e6edf3;--mut:#8b949e;--acc:#58a6ff;
--buy:#3fb950;--hold:#d29922;--sell:#f85149;--low:#8b949e}
*{box-sizing:border-box}
body{margin:0;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
background:var(--bg);color:var(--tx)}
header{padding:18px 20px;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;
gap:10px;align-items:baseline;justify-content:space-between}
h1{font-size:20px;margin:0} .mut{color:var(--mut);font-size:13px}
main{max-width:1100px;margin:0 auto;padding:16px}
.filters{display:flex;flex-wrap:wrap;gap:10px;margin:10px 0 16px}
.filters input,.filters select{background:var(--card);border:1px solid var(--line);color:var(--tx);
padding:7px 10px;border-radius:8px;font-size:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:10px 0}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--mut);font-weight:600;position:sticky;top:0;background:var(--card)}
.action{display:inline-block;padding:1px 8px;border-radius:20px;font-weight:700;font-size:12px}
.buy{background:#1f3d2b;color:var(--buy)} .hold{background:#3d311f;color:var(--hold)}
.sell{background:#3d1f1f;color:var(--sell)} .na{background:#21262d;color:var(--low)}
.tag{color:var(--acc);text-decoration:none} .tag:hover{text-decoration:underline}
.health td:first-child{white-space:nowrap}
.ok{color:var(--buy)} .no_new{color:var(--hold)} .failed{color:var(--sell)} .skipped{color:var(--mut)}
footer{padding:16px;color:var(--mut);font-size:12px;border-top:1px solid var(--line);margin-top:24px}
@media(max-width:640px){thead{display:none} tr{display:block;border:1px solid var(--line);
border-radius:8px;margin:8px 0;padding:8px} td{display:block;border:0;padding:3px 4px}
td:before{content:attr(data-l);color:var(--mut);font-size:11px;display:block}}
</style>
</head>
<body>
<header>
  <h1>IDX Daily Stock Recommendations</h1>
  <span class="mut" id="meta"></span>
</header>
<main>
  <div class="filters">
    <input id="fTicker" placeholder="Filter ticker… (BBCA)" style="width:180px">
    <select id="fSource"></select>
    <select id="fAction">
      <option value="">Any action</option>
      <option>BUY</option><option>TRADING BUY</option><option>ACCUMULATE</option>
      <option>ADD</option><option>HOLD</option><option>NEUTRAL</option>
      <option>SELL</option><option>REDUCE</option>
    </select>
    <select id="fDate"></select>
  </div>
  <div class="card" style="padding:6px 14px"><span class="mut" id="count"></span></div>
  <div class="card" style="padding:0;overflow-x:auto">
    <table><thead><tr>
      <th>Date</th><th>Source</th><th>Ticker</th><th>Action</th><th>Target</th>
      <th>Note / link</th><th>Conf</th>
    </tr></thead><tbody id="rows"></tbody></table>
  </div>
  <h2 style="font-size:16px;margin-top:28px">Source health</h2>
  <div class="card" style="padding:0;overflow-x:auto">
    <table class="health"><thead><tr><th>Source</th><th>Status</th><th>Records</th><th>Last run</th><th>Error / notes</th></tr></thead>
    <tbody id="healthRows"></tbody></table>
  </div>
  <p class="mut" style="margin-top:14px">Manual picks (Instagram / app-only feeds): edit
  <code>data/manual.json</code> and rerun <code>python pipeline.py</code> — see docs/MAINTENANCE.md.</p>
</main>
<footer>Generated by idx-daily-recs pipeline · data is informational, not investment advice ·
every record links to its original source URL.</footer>
<script>
const D = __PAYLOAD__;
const esc = s => String(s ?? '').replace(/[&<>"']/g, c =>
  ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const actionClass = a => {
  const x = (a||'').toUpperCase();
  if (x.includes('BUY')) return 'buy'; if (x.includes('HOLD')||x.includes('NEUTRAL')) return 'hold';
  if (x.includes('SELL')||x.includes('REDUCE')) return 'sell'; return 'na';
};
document.getElementById('meta').textContent =
  `Trading day ${D.trading_day} · generated ${D.generated_at} · ${D.records.length} picks in last 7 days`;
const sel = document.getElementById('fSource');
D.sources.forEach(s => { const o=document.createElement('option'); o.value=s.key; o.textContent=s.name; sel.appendChild(o); });
const dates = [...new Set(D.records.map(r=>r.date))].sort().reverse();
const dSel = document.getElementById('fDate');
dates.forEach(d => { const o=document.createElement('option'); o.value=d; o.textContent=d; dSel.appendChild(o); });
function render(){
  const ft=document.getElementById('fTicker').value.trim().toUpperCase();
  const fs=document.getElementById('fSource').value;
  const fa=document.getElementById('fAction').value.toUpperCase();
  const fd=document.getElementById('fDate').value;
  const rows=D.records.filter(r =>
    (!ft || (r.ticker||'').toUpperCase().includes(ft)) &&
    (!fs || r.source===fs) &&
    (!fa || (r.action||'').toUpperCase().includes(fa)) &&
    (!fd || r.date===fd));
  document.getElementById('count').textContent = `${rows.length} of ${D.records.length} picks`;
  const tb=document.getElementById('rows'); tb.innerHTML='';
  rows.slice(0,300).forEach(r=>{
    const tr=document.createElement('tr');
    const tgt=r.target!=null?('IDR '+r.target.toLocaleString('en-US',{maximumFractionDigits:0})):'—';
    tr.innerHTML=
      `<td data-l="Date">${esc(r.date)}</td>`+
      `<td data-l="Source"><a class="tag" href="${esc(r.source_url||'#')}" target="_blank" rel="noopener">${esc(r.source_name||r.source)}</a></td>`+
      `<td data-l="Ticker"><b>${esc(r.ticker)}</b></td>`+
      `<td data-l="Action"><span class="action ${actionClass(r.action)}">${esc(r.action)}</span></td>`+
      `<td data-l="Target">${tgt}</td>`+
      `<td data-l="Note">${esc((r.note||'').slice(0,160))}</td>`+
      `<td data-l="Conf">${esc(r.confidence||'')}</td>`;
    tb.appendChild(tr);
  });
}
['fTicker','fSource','fAction','fDate'].forEach(id=>document.getElementById(id).addEventListener('input',render));
const hb=document.getElementById('healthRows');
D.sources.forEach(s=>{
  const h=D.health?.[s.key]||{};
  const tr=document.createElement('tr');
  tr.innerHTML=`<td>${esc(s.name)}</td><td class="${esc(s.status)}">${esc(s.status)}</td>
    <td>${h.records??''}</td><td>${esc((h.last_run||'').slice(0,16))}</td>
    <td>${esc((h.error||(h.notes||[]).join('; '))||'')}</td>`;
  hb.appendChild(tr);
});
render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    sys.exit(main())
