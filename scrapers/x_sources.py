"""X (Twitter) sources via local `xurl` CLI. Requires credentials; skipped in CI.

Enable locally with:  python pipeline.py --with-x
Handles: @MaybankTradeID, @MiraeAssetID, @SM_Sekuritas, @Stockbit, @semesta_mg
"""
from __future__ import annotations

import shutil
import subprocess

HANDLES = [
    ("x_maybank", "Maybank Sekuritas Indonesia (X)", "MaybankTradeID"),
    ("x_mirae", "Mirae Asset Sekuritas Indonesia (X)", "MiraeAssetID"),
    ("x_sinarmas", "Sinarmas Sekuritas (X)", "SM_Sekuritas"),
    ("x_stockbit", "Stockbit (X)", "Stockbit"),
    ("x_semesta", "Semesta Indovest (X)", "semesta_mg"),
]


def run(ctx) -> list[dict]:
    if not ctx.with_x:
        return []  # pipeline marks skipped
    if not shutil.which("xurl"):
        ctx.note("x", "xurl CLI not found; install/configure credentials")
        return []
    out: list[dict] = []
    for key, name, handle in HANDLES:
        try:
            r = subprocess.run(
                ["xurl", "posts", "--handle", handle, "--limit", "20"],
                capture_output=True, text=True, timeout=60,
            )
            text = (r.stdout or "") + (r.stderr or "")
            # records extracted from raw post text
            from .common import extract_records, make_record
            for rec in extract_records(text):
                out.append(make_record(key, name, rec["ticker"], rec["action"],
                                       f"https://x.com/{handle}", ctx.today,
                                       target=rec["target"], note=f"@{handle} | {rec['note']}",
                                       conf="low"))
        except Exception as e:
            ctx.note(key, str(e))
    return out
