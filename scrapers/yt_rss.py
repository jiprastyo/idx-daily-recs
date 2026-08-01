"""YouTube channel RSS (no API key). Channel ID resolved from @handle at runtime."""
from __future__ import annotations

import datetime
import re
import xml.etree.ElementTree as ET

from .common import (fetch, make_record, TICKER_RE, NOISE, wib_now, WIB)

# key (must match SOURCE_REGISTRY yt_* keys) -> (display name, @handle or channel/UC…)
CHANNELS = {
    "yt_rhb": ("RHB Sekuritas Indonesia", "@rhbsekuritas"),
    "yt_bni": ("BNI Sekuritas", "@BNISekuritas"),
    "yt_mirae": ("Mirae Asset Sekuritas Indonesia", "@MiraeAssetSekuritas"),
    "yt_phillip": ("Phillip Sekuritas Indonesia", "@PhillipSekuritasIndonesia"),
    "yt_maybank": ("Maybank Sekuritas Indonesia", "@maybanksekuritas"),
    "yt_sinarmas": ("Sinarmas Sekuritas", "channel/UCDMD0mwkcz9pe-3rnmbn9WQ"),
    "yt_kaf": ("KAF Sekuritas Indonesia", "@KAFSekuritasIndonesia"),
}

# words that appear in channel names / boilerplate and are NOT tickers
CHANNEL_NOISE = {
    "RHB", "SEKURITAS", "INDONESIA", "BNI", "MIRAE", "ASSET", "PHILLIP", "MAYBANK",
    "SINARMAS", "KAF", "MORNING", "STOCK", "PICK", "DAILY", "UPDATE", "MARKET", "REPORT",
    "REVIEW", "BRIEFING", "OUTLOOK", "MEETING", "WEEKLY", "MONTHLY", "RECAP", "WATCH",
    "HARIAN", "REKOMENDASI", "SAHAM", "TODAY", "HARI", "INI", "LIVE", "TRADING",
    "CDS", "HSC", "IPO", "ETF", "FX", "P/E", "CAGR", "WIB", "JAKARTA", "GLOBAL",
}


def _resolve_channel_id(handle: str) -> str | None:
    if handle.startswith("channel/"):
        return handle.split("/")[1]
    try:
        page = fetch(f"https://www.youtube.com/{handle}/about", timeout=20)
    except Exception:
        return None
    m = re.search(r'"channelId":"(UC[\w-]{22})"', page)
    return m.group(1) if m else None


def _tickers_from_title(title: str) -> list[str]:
    toks = [t for t in TICKER_RE.findall(title)
            if t not in NOISE and t not in CHANNEL_NOISE]
    seen, out = set(), []
    for t in toks:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def run(ctx) -> list[dict]:
    out: list[dict] = []
    for key, (name, handle) in CHANNELS.items():
        cid = _resolve_channel_id(handle)
        if not cid:
            ctx.note(key, "channel_resolve_failed")
            continue
        try:
            feed = fetch(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}", timeout=30)
        except Exception as e:
            ctx.note(key, f"feed_error: {e}")
            continue
        try:
            root = ET.fromstring(feed)
        except ET.ParseError as e:
            ctx.note(key, f"feed_parse_error: {e}")
            continue
        ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
        for entry in root.findall("a:entry", ns)[:15]:
            title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
            published = entry.findtext("a:published", default="", namespaces=ns) or ""
            vid = entry.findtext("yt:videoId", default="", namespaces=ns)
            url = f"https://www.youtube.com/watch?v={vid}" if vid else ""
            try:
                dt = datetime.datetime.fromisoformat(published.replace("Z", "+00:00"))
                date = dt.astimezone(WIB).strftime("%Y-%m-%d")
            except Exception:
                date = ctx.today
            for t in _tickers_from_title(title):
                out.append(make_record(key, name, t, "N/A", url, date,
                                       note=f"YT: {title[:160]}", conf="low"))
    return out
