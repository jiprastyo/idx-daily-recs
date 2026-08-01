"""Structured sources: Shinhan getData API, Minna Padi AJAX, Verdhana site, Yuanta homepage."""
from __future__ import annotations

import json
import re
import urllib.parse
import warnings

import requests
import urllib3

from .common import (fetch, fetch_bytes, html_to_text, extract_records, make_record,
                     wib_now, latest_trading_day, UA, parse_idr)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SHINHAN_URL = "https://shinhansekuritas.co.id/research/getData"
SHINHAN_PAGE = "https://shinhansekuritas.co.id/research"
SHINHAN_BASE = "https://shinhansekuritas.co.id/file/"
MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}


def _date_from_filename(name: str, fallback: str) -> str:
    m = re.search(r"(\d{1,2})\s+([A-Z][a-z]+)\s+(\d{4})", name)
    if m and m.group(2) in MONTHS:
        return f"{m.group(3)}-{MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}"
    return fallback


def _session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    return s


def shinhan(ctx) -> list[dict]:
    """POST /research/getData (needs session cookie + Referer) -> {viewDaily, viewTopic, viewOutlook}."""
    s = _session()
    s.get(SHINHAN_PAGE, timeout=20)  # seed session
    r = s.post(SHINHAN_URL, timeout=30,
               headers={"Referer": SHINHAN_PAGE, "X-Requested-With": "XMLHttpRequest"})
    r.raise_for_status()
    data = r.json()
    out: list[dict] = []
    seen_files = set()
    for bucket in ("viewDaily", "viewTopic", "viewOutlook"):
        for item in (data.get(bucket, []) or [])[:2]:
            fname = str(item.get("file", "") or "")
            if not fname or fname in seen_files:
                continue
            seen_files.add(fname)
            url = SHINHAN_BASE + bucket.replace("view", "").lower() + "/" + urllib.parse.quote(fname)
            name = str(item.get("name", "") or item.get("title", "") or "")
            date = _date_from_filename(name, ctx.today)
            try:
                text = ctx.pdf_text(fetch_bytes(url, timeout=15))
            except Exception:
                continue  # one bad file shouldn't kill the bucket
            for rec in ctx.extract_records(text):
                out.append(make_record(
                    "shinhan", "Shinhan Sekuritas Indonesia", rec["ticker"], rec["action"],
                    url, date, target=rec["target"], note=f"{bucket}: {name} | {rec['note']}",
                    conf="medium"))
    return out


def minnapadi(ctx) -> list[dict]:
    """DataTables AJAX endpoint (Laravel CSRF): daily reports incl. 'Morning Dew' PDFs."""
    s = _session()
    page = s.get("https://minnapadi.com/daily-reports", timeout=30).text
    tok_m = re.search(r'listManager\.token = "([^"]+)"', page)
    if not tok_m:
        return []
    headers = {"Referer": "https://minnapadi.com/daily-reports",
               "X-Requested-With": "XMLHttpRequest"}
    xsrf = s.cookies.get("XSRF-TOKEN")
    if xsrf:
        headers["X-XSRF-TOKEN"] = urllib.parse.unquote(xsrf)
    r = s.post("https://minnapadi.com/daily-reports-ajax",
               data={"token": tok_m.group(1)}, headers=headers, timeout=30)
    r.raise_for_status()
    payload = r.json()
    items = payload.get("data", []) if isinstance(payload, dict) else []
    out: list[dict] = []
    for item in items[:5]:
        if not isinstance(item, dict):
            continue
        pdf = str(item.get("pdfUrl", "") or "")
        title = re.sub(r"<[^>]+>", "", str(item.get("title", "") or "")).strip()
        title = title or str(item.get("titleInd", "") or "")
        pub = re.sub(r"<[^>]+>", "", str(item.get("publishDate", "") or "")).strip()
        date = _date_from_filename(pub, ctx.today) if pub else ctx.today
        if not pdf:
            continue
        url = "https://minnapadi.com/" + urllib.parse.quote(pdf.lstrip("/"))
        try:
            text = ctx.pdf_text(fetch_bytes(url))
        except Exception:
            continue
        for rec in ctx.extract_records(text):
            out.append(make_record("minnapadi", "Minna Padi Investama Sekuritas Tbk",
                                   rec["ticker"], rec["action"], url, date,
                                   target=rec["target"], note=f"{title} | {rec['note']}",
                                   conf="medium"))
    return out


def verdhana(ctx) -> list[dict]:
    """Public research site (self-signed cert — verify disabled)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        home = fetch("https://verdhanaresearch.com", timeout=30, verify=False)
    slugs = re.findall(r'href="(https://verdhanaresearch\.com/[a-z0-9][a-z0-9\-]+-[a-z0-9]{3})"', home)
    out: list[dict] = []
    seen = set()
    for url in slugs[:6]:
        if url in seen:
            continue
        seen.add(url)
        try:
            text = html_to_text(fetch(url, timeout=30, verify=False))
        except Exception:
            continue
        date_m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        date = date_m.group(1) if date_m else ctx.today
        for rec in ctx.extract_records(text):
            out.append(make_record("verdhana", "Verdhana Sekuritas Indonesia", rec["ticker"],
                                   rec["action"], url, date, target=rec["target"],
                                   note=rec["note"], conf="medium"))
    return out


def yuanta(ctx) -> list[dict]:
    """Homepage Latest Research: 'YYYY-MM-DD HH:MM:SS' + '<title> ... BUY / TP: IDR:<n>'."""
    html = fetch("https://www.yuanta.co.id/", timeout=30)
    out: list[dict] = []
    for m in re.finditer(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", html):
        seg = html[m.start():m.start() + 1800]
        tp_m = re.search(r"(BUY|HOLD|SELL|ACCUMULATE|REDUCE)\s*/\s*TP\s*:\s*IDR\s*:?\s*([\d.,]+)",
                         seg, re.I)
        if not tp_m:
            continue
        title_html_m = re.search(r'class="research-content[^"]*"[^>]*>(.{0,600})', seg, re.S)
        title = re.sub(r"<[^>]+>", " ", title_html_m.group(1)) if title_html_m else ""
        ticker_m = re.search(r"\b([A-Z]{3,5})\b", title)
        if not ticker_m:
            continue
        ticker = ticker_m.group(1)
        if ticker in {"IDR", "MSCI", "IHSG", "LQ45", "TPY", "JCI"}:
            continue
        date = m.group(1)[:10]
        try:
            target = parse_idr(tp_m.group(2))
        except ValueError:
            target = None
        out.append(make_record("yuanta", "Yuanta Sekuritas Indonesia", ticker,
                               tp_m.group(1).upper(), "https://www.yuanta.co.id/", date,
                               target=target, note=title.strip()[:200], conf="medium"))
    return out
