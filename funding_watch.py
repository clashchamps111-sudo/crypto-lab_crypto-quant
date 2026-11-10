"""FUNDING WATCH - the parked desk's only instrument (park protocol, Nov 9).

Fetches live BTCUSDT funding prints, stamps a dated baseline/alert entry into
out/funding_watch_log.md (append; log accumulates). Thresholds pre-registered:
  W2 RICH   : trailing-30d mean >= +10%/yr annualized  -> desk wake candidate
  W3 HOSTILE: trailing-30d negative-print share >= 40% -> LONG-perp era flag
              (opposite stack; NOT the standing short-perp carry)
Offline fallback: stamps from the historical CSV tail and marks the entry
STALE so no one mistakes it for live.
"""
import json
import os
import urllib.request
from datetime import datetime, timezone

import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
LOG = os.path.join(OUT, "funding_watch_log.md")
URL = "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=300"

W2_THRESHOLD = 0.10    # +10%/yr annualized (pre-registered)
W3_THRESHOLD = 0.40    # 40% negative prints (pre-registered)
TRAIL_30D = 90         # prints ~= 30 days


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "quant-watch/1"})
    d = json.loads(urllib.request.urlopen(req, timeout=30).read())
    df = pd.DataFrame(d)
    df["fundingTime"] = pd.to_datetime(df["fundingTime"], unit="ms")
    df["fundingRate"] = df["fundingRate"].astype(float)
    return df.sort_values("fundingTime").reset_index(drop=True), False


def stats(df):
    r = df["fundingRate"]
    t30 = r.tail(TRAIL_30D)
    return dict(n=len(df), latest=float(r.iloc[-1]),
                latest_avg=float(t30.mean()), neg_share=float((t30 < 0).mean()),
                first=str(df["fundingTime"].iloc[0]), last=str(df["fundingTime"].iloc[-1]))


def stamp(df, s, offline=None):
    ann = s["latest_avg"] * 3 * 365
    w2 = ann >= W2_THRESHOLD
    w3 = s["neg_share"] >= W3_THRESHOLD
    flags = []
    if w2:
        flags.append(f"W2-RICH (mean {ann:+.1%}/yr >= +10%)")
    if w3:
        flags.append(f"W3-HOSTILE (negative share {s['neg_share']:.1%} >= 40%)")
    line = ["", f"## {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
            + (f"  [STALE: {offline}]" if offline else ""),
            "",
            f"- Prints: {s['n']} live | span {s['first'][:16]} -> {s['last'][:16]}",
            f"- Latest print: {s['latest'] * 100:+.3f}%/8h "
            f"(= {s['latest'] * 3 * 365:+.1%}/yr if floor-pegged)",
            f"- Trailing-30d: mean {s['latest_avg'] * 100:+.3f}%/8h "
            f"(= {ann:+.1%}/yr) | negative share {s['neg_share']:.1%}",
            f"- Short-perp carry income right now: "
            f"{s['latest'] * 3 * 365:+.1%}/yr at the floor peg",
            f"- **ALERTS: {'; '.join(flags) if flags else 'none - desk stays parked, everything nominal'}**",
            ""]
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(line))
    return flags


def main():
    os.makedirs(OUT, exist_ok=True)
    try:
        df, _ = fetch()
        s = stats(df)
        flags = stamp(df, s)
        print(f"[watch] live prints {s['n']}: latest {s['latest'] * 100:+.3f}%/8h, "
              f"30d mean {s['latest_avg'] * 100:+.4f}%/8h ({s['latest_avg'] * 3 * 365:+.1%}/yr), "
              f"neg share {s['neg_share']:.1%}")
        print(f"[watch] flags: {'; '.join(flags) if flags else 'none - nominal, desk parked'}")
    except Exception as e:
        df = pd.read_csv(os.path.join(ROOT, "data", "funding_BTCUSDT.csv"),
                         parse_dates=["fundingTime"]).tail(TRAIL_30D)
        s = stats(df)
        flags = stamp(df, s, offline=f"fetch failed: {e.__class__.__name__}; CSV tail used")
        print(f"[watch] OFFLINE fallback stamps labeled STALE: {e}")
        print(f"[watch] flags: {flags if flags else 'none'}")
    print(f"[watch] log appended: {LOG}")


if __name__ == "__main__":
    main()
