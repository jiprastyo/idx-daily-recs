"""Listing-page sources: listing -> today's report -> PDF/HTML -> text -> records.

Each function is small and isolated so a layout change only breaks one source
(see docs/MAINTENANCE.md).
"""
from __future__ import annotations

import re

from .common import (fetch, fetch_bytes, html_to_text, extract_records, make_record,
                     latest_trading_day, NOISE)

DATE_PATTERNS = [
    (r"\d{1,2}[- ](?:Jan|Feb|Mar|Apr|Mei|May|Jun|Jul|Agu|Aug|Sep|Okt|Oct|Nov|Des|Dec)[- ]\d{4}", "short"),
    (r"\d{1,2} (?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember) \d{4}", "long-id"),
    (r"\d{4}-\d{2}-\d{2}", "iso"),
    (r"\d{1,2}-\w+-\d{4}", "slug"),
]


def _pick_link(html, patterns, exclude=()):
    """Return first href whose surrounding text/slug matches any pattern."""
    for pat, _kind in patterns:
        for m in re.finditer(pat, html):
            win = html[max(0, m.start() - 600):m.end() + 600]
            hrefs = re.findall(r'href="([^"]+)"', win)
            for h in reversed(hrefs):
                if h.startswith("javascript") or h in exclude:
                    continue
                return h
    return None


def _records_from_pdf(ctx, pdf_url, key, name, date, conf="medium"):
    try:
        text = ctx.pdf_text(fetch_bytes(pdf_url, timeout=60))
    except Exception:
        return []
    return [make_record(key, name, r["ticker"], r["action"], pdf_url, date,
                        target=r["target"], note=r["note"], conf=conf)
            for r in ctx.extract_records(text)]


def samuel(ctx) -> list[dict]:
    html = fetch("https://samuel.co.id/research-reports/", timeout=30)
    seg = html.split("Morning Briefs", 1)[1] if "Morning Briefs" in html else html
    hrefs = re.findall(r'href="(https://samuel\.co\.id/research-reports/[^"]+)"', seg)
    out: list[dict] = []
    for url in hrefs[:1]:
        text = html_to_text(fetch(url, timeout=30))
        for r in ctx.extract_records(text):
            out.append(make_record("samuel", "Samuel Sekuritas Indonesia", r["ticker"],
                                   r["action"], url, ctx.today, target=r["target"],
                                   note=r["note"], conf="medium"))
    return out


def nh(ctx) -> list[dict]:
    html = fetch("https://www.nhis.co.id/id/research/riset-reguler/", timeout=30)
    link = _pick_link(html, [(r"/id/daily-report-[\w-]+/", "slug")])
    out: list[dict] = []
    if link:
        if not link.startswith("http"):
            link = "https://www.nhis.co.id" + link
        text = html_to_text(fetch(link, timeout=30))
        for r in ctx.extract_records(text):
            out.append(make_record("nh", "NH Korindo Sekuritas Indonesia", r["ticker"],
                                   r["action"], link, ctx.today, target=r["target"],
                                   note=r["note"], conf="medium"))
    return out


def mnc(ctx) -> list[dict]:
    html = fetch("https://www.mncsekuritas.id/category/2/", timeout=30)
    hrefs = re.findall(r'href="(https://www\.mncsekuritas\.id/[^"]+)"', html)
    out: list[dict] = []
    for url in hrefs[:2]:
        try:
            text = html_to_text(fetch(url, timeout=30))
        except Exception:
            continue
        for r in ctx.extract_records(text):
            out.append(make_record("mnc", "MNC Sekuritas", r["ticker"], r["action"], url,
                                   ctx.today, target=r["target"], note=r["note"], conf="medium"))
    return out


def mega(ctx) -> list[dict]:
    html = fetch("https://www.megasekuritas.id/research.asp", timeout=30)
    pdfs = re.findall(r'href="([^"]+\.(?:pdf|PDF))"', html)
    out: list[dict] = []
    for p in pdfs[:1]:
        url = p if p.startswith("http") else "https://www.megasekuritas.id/" + p.lstrip("/")
        out += _records_from_pdf(ctx, url, "mega", "Mega Capital Sekuritas", ctx.today)
    return out


def waterfront(ctx) -> list[dict]:
    html = fetch("https://waterfrontsekuritas.com/research", timeout=30)
    pdfs = re.findall(r'href="([^"]+\.pdf[^"]*)"', html, re.I)
    out: list[dict] = []
    for p in pdfs[:1]:
        url = p if p.startswith("http") else "https://waterfrontsekuritas.com" + ("" if p.startswith("/") else "/") + p
        out += _records_from_pdf(ctx, url, "waterfront", "Waterfront Sekuritas Indonesia", ctx.today)
    return out


def kbvalbury(ctx) -> list[dict]:
    html = fetch("https://www.kbvalbury.com/research/daily-technical-analysis", timeout=30)
    text = html_to_text(html)
    return [make_record("kbvalbury", "KB Valbury Sekuritas", r["ticker"], r["action"],
                        "https://www.kbvalbury.com/research/daily-technical-analysis",
                        ctx.today, target=r["target"], note=r["note"], conf="medium")
            for r in ctx.extract_records(text)]


def victoria(ctx) -> list[dict]:
    html = fetch("https://victoria-sekuritas.co.id/", timeout=30)
    pdfs = re.findall(r'href="([^"]*Daily[-_]Analysis[^"]*\.pdf)"', html, re.I)
    out: list[dict] = []
    for p in pdfs[:1]:
        url = p if p.startswith("http") else "https://victoria-sekuritas.co.id" + ("" if p.startswith("/") else "/") + p
        out += _records_from_pdf(ctx, url, "victoria", "Victoria Sekuritas Indonesia", ctx.today)
    return out


def kiwoom(ctx) -> list[dict]:
    html = fetch("https://www.kiwoom.co.id/market/getMarketReportMain", timeout=30)
    hrefs = re.findall(r'href="([^"]+)"', html)
    out: list[dict] = []
    for h in hrefs:
        if re.search(r"daily|report|market", h, re.I):
            url = h if h.startswith("http") else "https://www.kiwoom.co.id" + h
            try:
                if url.lower().endswith(".pdf"):
                    out += _records_from_pdf(ctx, url, "kiwoom", "Kiwoom Sekuritas Indonesia", ctx.today)
                else:
                    text = html_to_text(fetch(url, timeout=30))
                    out += [make_record("kiwoom", "Kiwoom Sekuritas Indonesia", r["ticker"],
                                        r["action"], url, ctx.today, target=r["target"],
                                        note=r["note"], conf="medium")
                            for r in ctx.extract_records(text)]
                if out:
                    break
            except Exception:
                continue
    return out


def binaartha(ctx) -> list[dict]:
    html = fetch("https://binaartha.com/technical-research.html", timeout=30)
    text = html_to_text(html)
    return [make_record("binaartha", "Binaartha Sekuritas", r["ticker"], r["action"],
                        "https://binaartha.com/technical-research.html", ctx.today,
                        target=r["target"], note=r["note"], conf="medium")
            for r in ctx.extract_records(text)]


def phintraco(ctx) -> list[dict]:
    html = fetch("https://phintracosekuritas.com/riset/", timeout=30)
    hrefs = re.findall(r'href="(https://phintracosekuritas\.com/[^"]+)"', html)
    out: list[dict] = []
    for url in hrefs[:2]:
        if "/riset/" in url and not url.endswith("/riset/"):
            try:
                text = html_to_text(fetch(url, timeout=30))
            except Exception:
                continue
            for r in ctx.extract_records(text):
                out.append(make_record("phintraco", "Phintraco Sekuritas", r["ticker"],
                                       r["action"], url, ctx.today, target=r["target"],
                                       note=r["note"], conf="medium"))
            if out:
                break
    return out


def panin(ctx) -> list[dict]:
    html = fetch("https://pans.co.id/riset", timeout=30)
    pdfs = re.findall(r'href="([^"]+\.pdf[^"]*)"', html, re.I)
    out: list[dict] = []
    for p in pdfs[:1]:
        url = p if p.startswith("http") else "https://pans.co.id" + ("" if p.startswith("/") else "/") + p
        out += _records_from_pdf(ctx, url, "panin", "Panin Sekuritas Tbk", ctx.today)
    return out


def artha(ctx) -> list[dict]:
    html = fetch("https://www.arthasekuritas.com/id/research-analysis.php", timeout=30)
    hrefs = re.findall(r'href="([^"]+)"', html)
    out: list[dict] = []
    for h in hrefs:
        if re.search(r"\.pdf|download|report", h, re.I):
            url = h if h.startswith("http") else "https://www.arthasekuritas.com/" + h.lstrip("/")
            try:
                out += _records_from_pdf(ctx, url, "artha", "Artha Sekuritas Indonesia", ctx.today)
            except Exception:
                continue
            if out:
                break
    return out


def ocbc(ctx) -> list[dict]:
    html = fetch("https://www.ocbcsekuritas.com/", timeout=30)
    text = html_to_text(html)
    return [make_record("ocbc", "OCBC Sekuritas Indonesia", r["ticker"], r["action"],
                        "https://www.ocbcsekuritas.com/", ctx.today, target=r["target"],
                        note=r["note"], conf="low")
            for r in ctx.extract_records(text)]


def maybank(ctx) -> list[dict]:
    html = fetch("https://www.maybank-ke.co.id/riset", timeout=30)
    text = html_to_text(html)
    return [make_record("maybank", "Maybank Sekuritas Indonesia", r["ticker"], r["action"],
                        "https://www.maybank-ke.co.id/riset", ctx.today, target=r["target"],
                        note=r["note"], conf="low")
            for r in ctx.extract_records(text)]


def phillip(ctx) -> list[dict]:
    html = fetch("https://www.phillip.co.id/", timeout=30)
    text = html_to_text(html)
    return [make_record("phillip", "Phillip Sekuritas Indonesia", r["ticker"], r["action"],
                        "https://www.phillip.co.id/", ctx.today, target=r["target"],
                        note=r["note"], conf="low")
            for r in ctx.extract_records(text)]


def uob(ctx) -> list[dict]:
    html = fetch("https://utrade.co.id/Research.aspx", timeout=30)
    text = html_to_text(html)
    return [make_record("uob", "UOB Kay Hian Sekuritas", r["ticker"], r["action"],
                        "https://utrade.co.id/Research.aspx", ctx.today, target=r["target"],
                        note=r["note"], conf="low")
            for r in ctx.extract_records(text)]


def cgs(ctx) -> list[dict]:
    html = fetch("https://www.cgsi.co.id/insights?lang=ID", timeout=30)
    hrefs = re.findall(r'href="(https://www\.cgsi\.co\.id/[^"]+)"', html)
    out: list[dict] = []
    for url in hrefs[:3]:
        if url.rstrip("/").endswith(("/insights", "/insights?lang=ID")):
            continue
        try:
            text = html_to_text(fetch(url, timeout=30))
        except Exception:
            continue
        for r in ctx.extract_records(text):
            out.append(make_record("cgs", "CGS International Sekuritas Indonesia", r["ticker"],
                                   r["action"], url, ctx.today, target=r["target"],
                                   note=r["note"], conf="low"))
        if out:
            break
    return out


def sucor(ctx) -> list[dict]:
    html = fetch("https://www.sucorsekuritas.com/product/research/", timeout=30)
    hrefs = re.findall(r'href="([^"]+)"', html)
    out: list[dict] = []
    for h in hrefs:
        if re.search(r"equity|report|research", h, re.I) and "product/research" not in h:
            url = h if h.startswith("http") else "https://www.sucorsekuritas.com" + h
            try:
                text = html_to_text(fetch(url, timeout=30))
            except Exception:
                continue
            for r in ctx.extract_records(text):
                out.append(make_record("sucor", "Sucor Sekuritas", r["ticker"], r["action"],
                                       url, ctx.today, target=r["target"], note=r["note"],
                                       conf="low"))
            if out:
                break
    return out


def sf(ctx) -> list[dict]:
    html = fetch("https://www.sfsekuritas.co.id/produk-layanan/research-recommendation", timeout=30)
    text = html_to_text(html)
    return [make_record("sf", "Surya Fajar Sekuritas", r["ticker"], r["action"],
                        "https://www.sfsekuritas.co.id/produk-layanan/research-recommendation",
                        ctx.today, target=r["target"], note=r["note"], conf="low")
            for r in ctx.extract_records(text)]


def evergreen(ctx) -> list[dict]:
    html = fetch("https://evergreensekuritas.co.id/news/riset", timeout=30)
    hrefs = re.findall(r'href="([^"]+)"', html)
    out: list[dict] = []
    for h in hrefs:
        if re.search(r"news|riset", h, re.I) and "news/riset" not in h:
            url = h if h.startswith("http") else "https://evergreensekuritas.co.id" + h
            try:
                text = html_to_text(fetch(url, timeout=30))
            except Exception:
                continue
            for r in ctx.extract_records(text):
                out.append(make_record("evergreen", "Evergreen Sekuritas Indonesia", r["ticker"],
                                       r["action"], url, ctx.today, target=r["target"],
                                       note=r["note"], conf="low"))
            if out:
                break
    return out


def reliance(ctx) -> list[dict]:
    html = fetch("https://reliancesekuritas.com/", timeout=30)
    pdfs = re.findall(r'href="([^"]+\.pdf[^"]*)"', html, re.I)
    out: list[dict] = []
    for p in pdfs[:1]:
        url = p if p.startswith("http") else "https://reliancesekuritas.com" + ("" if p.startswith("/") else "/") + p
        out += _records_from_pdf(ctx, url, "reliance", "Reliance Sekuritas Indonesia Tbk", ctx.today)
    return out


def most(ctx) -> list[dict]:
    html = fetch("https://www.most.co.id/riset", timeout=30)
    pdfs = re.findall(r'href="([^"]+\.pdf[^"]*)"', html, re.I)
    out: list[dict] = []
    for p in pdfs[:2]:
        url = p if p.startswith("http") else "https://www.most.co.id" + ("" if p.startswith("/") else "/") + p
        out += _records_from_pdf(ctx, url, "most", "Mandiri Sekuritas (MOST)", ctx.today)
    return out
