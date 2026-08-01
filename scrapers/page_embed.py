"""HTML-article sources: NH Korindo + Ajaib (report content embedded in the page)."""
from __future__ import annotations

import re

from .common import fetch, html_to_text, extract_records, make_record


def nh(ctx) -> list[dict]:
    """Latest Daily Report article from the riset-reguler listing."""
    html = fetch("https://www.nhis.co.id/id/research/riset-reguler/", timeout=30)
    m = re.search(r'href="([^"]*/id/daily-report-[\w-]+/)"', html)
    if not m:
        return []
    url = m.group(1)
    if url.startswith("/"):
        url = "https://www.nhis.co.id" + url
    text = html_to_text(fetch(url, timeout=30))
    return [make_record("nh", "NH Korindo Sekuritas Indonesia", r["ticker"], r["action"],
                        url, ctx.today, target=r["target"], note=r["note"], conf="medium")
            for r in ctx.extract_records(text)]


def ajaib(ctx) -> list[dict]:
    """Ajaib daily article: blocks of 'TICKER ... Beli di harga RpX Take Profit RpY Stop Loss RpZ'."""
    from .common import parse_idr, NOISE
    html = fetch("https://ajaib.co.id/saham/rekomendasi-saham", timeout=30)
    text = html_to_text(html)
    out: list[dict] = []
    block_re = re.compile(
        r"Beli di harga Rp([\d.,]+)\s+Take Profit Rp([\d.,]+)\s+Stop Loss Rp([\d.,]+)", re.I)
    tick_re = re.compile(r"\b([A-Z]{3,5})\b")
    for m in block_re.finditer(text):
        back = text[max(0, m.start() - 140):m.start()]
        ticker = None
        for t in reversed(tick_re.findall(back)):  # nearest ALL-CAPS token before the block
            if t.upper() not in NOISE:
                ticker = t
                break
        if not ticker:
            continue
        try:
            price = parse_idr(m.group(1))
            target = parse_idr(m.group(2))
            stop = parse_idr(m.group(3))
        except ValueError:
            continue
        out.append(make_record("ajaib", "Ajaib Sekuritas", ticker, "BUY",
                               "https://ajaib.co.id/saham/rekomendasi-saham", ctx.today,
                               price=price, target=target, stop=stop,
                               note=f"Beli {price:g} / TP {target:g} / SL {stop:g}",
                               conf="high"))
    return out
