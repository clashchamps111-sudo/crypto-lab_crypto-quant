"""ITEM A - OI FORWARD COLLECTOR (Session 9.5, pre-registered in JOURNAL).

Binance OI history endpoints only expose a trailing ~30-day window, so the
desk must accrue its own OI sample forward. This collector:
- backfills BTCUSDT + ETHUSDT USDT-M OI at 5m period for the last 30 days
  (paginated, /futures/data/openInterestHist - public, unsigned);
- appends (dedup by timestamp) into data/oi_collect/{SYMBOL}_oi.csv;
- ETHUSDT is the instrument-breadth probe (2 assets, cheap).
Liquidation archives (/fapi/v1/forceOrders) need signed keys and serve only
recent windows - NOT collected here; limitation stamped in JOURNAL.

Pre-registered hurdle: NO OI-hypothesis battery until >= 60 calendar days of
contiguous sample exist per symbol. Collector runs at session touches.
"""
import json
import os
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone

import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(ROOT, "data", "oi_collect")
URL = "https://fapi.binance.com/futures/data/openInterestHist"
PERIOD = "5m"
SYMS = ["BTCUSDT", "ETHUSDT"]
LIMIT = 500
BACKFILL_DAYS = 30


def fetch_oi(sym, start_ms, end_ms):
    out, start = [], start_ms
    while start < end_ms:
        q = urllib.parse.urlencode({"symbol": sym, "period": PERIOD,
                                    "startTime": start, "endTime": end_ms,
                                    "limit": LIMIT})
        u = f"{URL}?{q}"
        for attempt in range(3):
            try:
                page = json.loads(urllib.request.urlopen(u, timeout=30).read())
                break
            except Exception as e:
                if attempt == 2:
                    raise
                print(f"[oi] retry {attempt + 1}: {e.__class__.__name__}")
                time.sleep(3)
        if not page:
            break
        out.extend(page)
        nxt = int(page[-1]["timestamp"]) + 1
        if nxt <= start:
            break
        start = nxt
        if len(page) < LIMIT:
            break
        time.sleep(0.25)
    return out


def collect(sym):
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    path = os.path.join(DIR, f"{sym}_oi.csv")
    have = pd.read_csv(path, parse_dates=["timestamp"]) if os.path.exists(path) else pd.DataFrame()
    last_ms = int(have["timestamp"].max().value // 1e6) if len(have) else (now_ms - BACKFILL_DAYS * 86400000)
    start = min(last_ms + 1, now_ms - BACKFILL_DAYS * 86400000)
    rows = fetch_oi(sym, start, now_ms)
    if not rows:
        print(f"[oi] {sym}: endpoint returned nothing (network/HMAC?)")
        return
    df = pd.DataFrame(rows)[["symbol", "sumOpenInterest", "sumOpenInterestValue", "timestamp"]]
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.rename(columns={"sumOpenInterest": "oi", "sumOpenInterestValue": "oi_usdt"})
    alln = pd.concat([have, df]) if len(have) else df
    alln = alln.drop_duplicates("timestamp").sort_values("timestamp")
    alln.to_csv(path, index=False)
    span0, span1 = alln["timestamp"].min(), alln["timestamp"].max()
    days = (span1 - span0).total_seconds() / 86400
    print(f"[oi] {sym}: +{len(df)} rows -> total {len(alln)} | span {span0.date()} -> {span1.date()} "
          f"({days:.1f}d, hurdle 60d: {'MET' if days >= 60 else 'accumulating'})")


if __name__ == "__main__":
    os.makedirs(DIR, exist_ok=True)
    print(f"[oi] collector touch {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}")
    for s in SYMS:
        try:
            collect(s)
        except Exception as e:
            print(f"[oi] {s} FAILED: {e.__class__.__name__}: {str(e)[:120]}")
