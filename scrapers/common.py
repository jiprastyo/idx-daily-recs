"""Shared helpers for the IDX daily-recommendations pipeline (stdlib + requests + pymupdf)."""
from __future__ import annotations

import datetime
import hashlib
import html as _html
import json
import os
import re
from zoneinfo import ZoneInfo

WIB = ZoneInfo("Asia/Jakarta")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

TICKER_RE = re.compile(r"\b[A-Z]{2,5}\b")
RATING_RE = re.compile(
    r"(Trading Buy|Speculative Buy|Strong Buy|Accumulate|BUY|ADD|HOLD|NEUTRAL|"
    r"SELL|REDUCE|Trading Sell|Overweight|Underweight|Market Perform|Outperform|"
    r"Beli di harga|Beli\b|Jual\b|Tahan\b)",
    re.I,
)
TP_RE = re.compile(r"(?:TP|Target Price|Take Profit|Take-Profit|target)\s*[:=]?\s*(?:IDR\s*|Rp\s*)?([\d][\d.,]*)\b", re.I)
NUM_RE = re.compile(r"\d[\d.,]*")
NOISE = {"IDR", "TP", "WIB", "WITA", "IHSG", "JCI", "USD", "MSCI", "LQ45", "YTD", "PE", "PBV",
         "ROE", "EPS", "BVPS", "THE", "AND", "FOR", "FROM", "WITH", "THAT", "THIS", "YOUR",
         "HARI", "BULAN", "TAHUN", "SAHAM", "PASAR", "MODAL", "EMITEN", "KEPADA", "DALAM",
         "SEKTOR", "MENURUT", "PADA", "JUGA", "AKAN", "SUDAH", "MASIH", "TIDAK", "HASIL",
         "PERIODE", "HINGGA", "SELAMA", "SETELAH", "SEBELUM", "MELALUI", "DARI", "UNTUK",
         "BELI", "JUAL", "TAHAN", "TAKE", "PROFIT", "STOP", "LOSS", "HARGA", "POTENSI",
         "RETURN", "TRADE", "LIMIT", "SERTA", "KARENA", "ADALAH", "SUDAH", "DENGAN",
         "YANG", "DAN", "INI", "ITU", "ATAU", "DAN", "DALAM", "SEBAGAI", "BAGI", "AGAR"}


def normalize_action(rating: str) -> str:
    r = rating.upper()
    if "BELI" in r:
        return "BUY"
    if "JUAL" in r:
        return "SELL"
    if "TAHAN" in r:
        return "HOLD"
    if "BUY" in r:
        return "BUY"
    if "SELL" in r:
        return "SELL"
    if "HOLD" in r or "NEUTRAL" in r:
        return "HOLD"
    if "ACCUMULATE" in r or "OVERWEIGHT" in r or "OUTPERFORM" in r or "ADD" == r:
        return "ACCUMULATE"
    if "REDUCE" in r or "UNDERWEIGHT" in r:
        return "REDUCE"
    return r


def parse_idr(s: str) -> float:
    """Parse IDR amounts that mix Indonesian (1.265 = 1265) and English (6,800) formats."""
    s = re.sub(r"(?i)\b(?:Rp|IDR)\b\s*", "", s).strip().replace(" ", "")
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", s):      # dots = thousands, comma = decimal
        return float(s.replace(".", "").replace(",", "."))
    if re.fullmatch(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", s):      # commas = thousands, dot = decimal
        return float(s.replace(",", ""))
    return float(s.replace(",", "."))                          # plain or decimal comma


def wib_now() -> datetime.datetime:
    return datetime.datetime.now(WIB)


def latest_trading_day(now: datetime.datetime | None = None) -> datetime.date:
    now = now or wib_now()
    d = now.date()
    while d.weekday() >= 5:  # 5=Sat, 6=Sun
        d -= datetime.timedelta(days=1)
    return d


def fetch(url, timeout=20, method="GET", data=None, headers=None, binary=False, verify=True):
    import requests

    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    try:
        r = requests.request(method, url, timeout=timeout, data=data, headers=h, verify=verify)
    except requests.exceptions.SSLError:
        # several Indonesian broker sites serve broken TLS chains; retry unverified
        r = requests.request(method, url, timeout=timeout, data=data, headers=h, verify=False)
    r.raise_for_status()
    return r.content if binary else r.text


def fetch_bytes(url, timeout=35):
    return fetch(url, timeout=timeout, binary=True)


def pdf_text(data: bytes) -> str:
    import fitz  # pymupdf

    doc = fitz.open(stream=data, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def html_to_text(html_text: str) -> str:
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html_text, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return _html.unescape(re.sub(r"\s+", " ", t))


def extract_records(text: str, limit: int = 40, require_target: bool = False) -> list[dict]:
    """Conservative ticker+rating(+target) extraction from free text.

    Emits a record only when a rating keyword is present on a line and a plausible
    ticker token can be found on that line or the adjacent ones.
    """
    out: list[dict] = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for i, line in enumerate(lines):
        m = RATING_RE.search(line)
        if m:
            rating = normalize_action(m.group(1))
        else:
            continue
        cands = []
        for ln in (line, lines[i - 1] if i else "", lines[i + 1] if i + 1 < len(lines) else ""):
            for tok in TICKER_RE.findall(ln):
                if tok not in NOISE and tok != rating and tok not in cands:
                    cands.append(tok)
            if cands:
                break
        if not cands:
            continue
        target = None
        tp_m = TP_RE.search(line)
        if tp_m:
            try:
                target = parse_idr(tp_m.group(1))
            except ValueError:
                target = None
        if require_target and target is None:
            continue
        out.append({
            "ticker": cands[0],
            "action": rating,
            "target": target,
            "note": line[:200],
        })
        if len(out) >= limit:
            break
    return out


def make_record(src_key, src_name, ticker, action, url, date, target=None, price=None,
                stop=None, note="", conf="low"):
    rid = hashlib.sha1(f"{src_key}|{date}|{ticker}|{action}|{url}".encode()).hexdigest()[:12]
    return {
        "id": rid,
        "date": date,
        "source": src_key,
        "source_name": src_name,
        "ticker": ticker,
        "action": action,
        "price": price,
        "target": target,
        "stop_loss": stop,
        "note": note,
        "source_url": url,
        "scraped_at": wib_now().isoformat(timespec="seconds"),
        "confidence": conf,
    }


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default
