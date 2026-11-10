"""FUNDING-CARRY side line (Session 6, pre-registered in JOURNAL).
A. Fetch 5y BTCUSDT funding-rate history (fapi, paginated) -> funding CSV.
B. Descriptive analytics: share of negative periods, annualized regimes, monthly sums.
C. Two-leg carry SMOKE (revenue-structure study, NOT a gauntlet):
   long spot + short perp 1x => PnL = funding stream - fees (30bp round trip:
   spot 10bp/side + perp 5bp/side). Rule: ENTER when trailing-3 mean funding
   > +1bp/8h (flat before), EXIT when < -1bp/8h (in position). Funding accrued
   strictly between entry and exit prints (conservative). Baseline: always-in
   carry with one round trip. Reports trips, funding, fees, net, stream MDD.
   On a $100 account, both legs are ~$100 notional; basis/slip wiggle ignored
   (declared simplification)."""
import json
import os
import time
import urllib.request

import numpy as np
import pandas as pd

import config as C

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
CSV = os.path.join(ROOT, "data", "funding_BTCUSDT.csv")

FUND_URL = "https://fapi.binance.com/fapi/v1/fundingRate"
T_START = int(pd.Timestamp("2021-11-06", tz="UTC").timestamp() * 1000)
FEE_RT = 0.003          # 30bp round trip, pre-registered
TRAIL_N = 3
ENTER_BP = 0.0001       # +1bp/8h
EXIT_BP = -0.0001


def fetch_funding():
    if os.path.exists(CSV):
        df = pd.read_csv(CSV, parse_dates=["fundingTime"])
        return df
    recs = []
    start = T_START
    while True:
        u = f"{FUND_URL}?symbol=BTCUSDT&startTime={start}&limit=1000"
        page = json.loads(urllib.request.urlopen(u, timeout=30).read())
        if not page:
            break
        recs.extend(page)
        if len(page) < 1000:
            break
        last = page[-1]["fundingTime"]
        if last <= start:
            break
        start = last + 1
    df = pd.DataFrame(recs)
    df["fundingTime"] = pd.to_datetime(df["fundingTime"], unit="ms", utc=True).dt.tz_localize(None)
    df["fundingRate"] = df["fundingRate"].astype(float)
    df = df.drop_duplicates("fundingTime").sort_values("fundingTime")
    df.to_csv(CSV, index=False)
    return df


def analytics(df, md):
    r = df["fundingRate"]
    pos = r > 0
    ann = lambda x: x * 3 * 365  # 8h prints -> annualized
    md += ["## A. Analytics (BTCUSDT funding, full fetched span)", "",
           f"- Span: {df['fundingTime'].min().date()} -> {df['fundingTime'].max().date()}"
           f" ({len(df)} 8h prints)", "",
           f"- Positive prints: {pos.mean():.1%} | zero {(r == 0).mean():.1%} | "
           f"negative {(r < 0).mean():.1%}",
           f"- Mean rate: {ann(r.mean()):+.1%}/yr | mean given positive {ann(r[pos].mean()):+.1%}/yr | "
           f"mean given negative {ann(r[~pos].mean()):+.1%}/yr",
           f"- p95 rate {ann(r.quantile(0.95)):+.1%}/yr | p05 {ann(r.quantile(0.05)):+.1%}/yr",
           f"- Always-in carry reference: sum(rates) as % = {(r.sum()) * 100:+.2f}% "
           f"over span (~{ann(r.mean()):+.1%}/yr), no fees", ""]
    # monthly table (last 15 months)
    m = (r * 100).groupby(df["fundingTime"].dt.to_period("M")).sum()
    md += ["| Month | Funding sum % of notional |", "|---|---|"]
    for p, v in m.tail(15).items():
        md.append(f"| {p} | {v:+.3f}% |")
    md.append("")
    return md


def carry_smoke(df, md):
    r = df["fundingRate"].to_numpy()
    n = len(r)
    trail = pd.Series(r).rolling(TRAIL_N).mean().to_numpy()
    inpos = False
    entries, exits = [], []
    for i in range(TRAIL_N, n):
        if not inpos and np.isfinite(trail[i]) and trail[i] > ENTER_BP:
            inpos = True
            entries.append(int(i + 1))  # accrue from the NEXT print (conservative)
        elif inpos and np.isfinite(trail[i]) and trail[i] < EXIT_BP:
            inpos = False
            exits.append(int(max(0, i - 1)))  # accrue up to the print BEFORE the exit print
    if len(exits) < len(entries):  # open carry at span end -> force-close at last print
        exits.append(n - 1)
    if not entries:
        md += ["## C. Carry smoke (pre-registered rule)", "",
               "Rule NEVER fired positives-sustained in span - carry table empty.", ""]
        return md
    total_f = 0.0
    stream = []
    for e, x in zip(entries, exits):
        if x < e:  # degenerate slice (entry near span end) -> hold to last print
            x = n - 1
        total_f += float(r[e:x + 1].sum())
        stream.extend([0.0] + list(r[e:x + 1]))
    trips = len(entries)
    fees = trips * FEE_RT * 100  # $ on $100 notional (1 unit x 1x)
    net = total_f * 100 - fees
    st = pd.Series(stream).cumsum() * 100
    peak = np.maximum.accumulate(st.values) if len(st) else np.array([0.0])
    mdd = float((st.values - peak).min()) if len(st) else 0.0
    md += ["## C. Carry smoke with the pre-registered gating rule", "",
           f"- Round trips: {trips} | funding collected: {total_f * 100:+.2f}% of notional "
           f"| fees paid: {fees:.2f}% | NET: {net:+.2f} on $100 carry",
           f"- Carry-stream max drawdown (net-of-nothing): {mdd:+.2f} "
           f"(funding streams pay negative periods too)",
           f"- Always-in baseline (1 trip): {(r.sum()) * 100:.2f}% funding - 0.30% fees = "
           f"{r.sum() * 100 - 0.30:+.2f}",
           "- Comparison IS the point: the gate's job is to dodge negative-funding "
           "regimes without paying the fee churn - judged relative to baseline.", ""]
    return md


def main():
    os.makedirs(OUT, exist_ok=True)
    df = fetch_funding()
    print(f"[funding] fetched/loaded {len(df)} prints: {df['fundingTime'].min()} -> {df['fundingTime'].max()}")
    md = ["# FUNDING ANALYTICS + CARRY SMOKE (Session 6 side line, pre-registered)", "", ""]
    md = analytics(df, md)
    md = carry_smoke(df, md)
    path = os.path.join(OUT, "FUNDING_analytics.md")
    open(path, "w", encoding="utf-8").write("\n".join(md))
    print(f"[funding] written: {path}")


if __name__ == "__main__":
    main()
