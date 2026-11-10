"""AUDIT CHARTER (pre-registered, finite). See JOURNAL Session 3 for criteria.
A. COST MATRIX  - frozen variants re-priced at 0bp / 2bp(maker) / 7bp(taker-band) per side.
B. POSITIVE CONTROL (freeze rule) - two documented-edge daily strategies through the
   identical 48m/12m walk-forward, maker costs + explicit per-day funding haircut.
   If BOTH fail -> ALL strategy verdicts FROZEN until the harness is fixed.
C. TRADE FORENSICS - machine-verify every entry of H01a(2y) and H03(4h deep) against
   bar-level manual recomputation. Any mismatch = engine bug, verdicts invalid.
D. Assumption book folded into B (funding modeled per hold-day, maker fee structure).
Writes out/audit_report.md. This battery IS the "multiple passes": many independent
confirmations, once each - not infinite re-runs."""
import os

import numpy as np
import pandas as pd

from backtesting import Backtest

import config as C
from indicators import vwap_daily
from strategies import (DailyMomentum, DailyRegime, DonchianBreakout, Rsi2Reversion,
                        ShortTrendPullback, TrendPullback, atr_w, ema, rsi_w)

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
KEYS = [("Return [%]", "Ret%"), ("Sharpe Ratio", "Sharpe"), ("Max. Drawdown [%]", "MaxDD%"),
        ("# Trades", "Trades"), ("Profit Factor", "PF"), ("Win Rate [%]", "Win%")]
COSTS = [("7bp (taker+slip+funding)", 0.0007), ("2bp (maker+slip)", 0.0002), ("0bp (gross)", 0.0)]


def num(x):
    try:
        x = float(x)
        return x if np.isfinite(x) else float("nan")
    except Exception:
        return float("nan")


def fmt(x, d=2):
    x = num(x)
    return f"{x:.{d}f}" if np.isfinite(x) else "n/a"


def row(stats):
    return {dst: num(stats.get(src, np.nan)) for src, dst in KEYS}


def load(sym, tf, suffix=""):
    path = os.path.join(ROOT, "data", f"{sym}_{tf}{suffix}.csv")
    df = pd.read_csv(path, parse_dates=["Date"], index_col="Date").astype(float)
    df[["Open", "High", "Low", "Close"]] = df[["Open", "High", "Low", "Close"]] / C.PRICE_SCALE
    return df


def split_for(df, suffix):
    tr_mos, te_mos = (C.TRAIN_MONTHS, C.TEST_MONTHS) if suffix == "_deep" else (18, 6)
    t0 = df.index[0]
    train_end = t0 + pd.DateOffset(months=tr_mos)
    test_end = train_end + pd.DateOffset(months=te_mos)
    return df[df.index < train_end], df[(df.index >= train_end) & (df.index < test_end)]


def eval_frozen(sym, tf, suffix, cls, params, commission, tag=""):
    df = load(sym, tf, suffix)
    use_v = params.pop("use_vwap", False)
    if use_v:
        df["VWAP"] = vwap_daily(df)
    train, test = split_for(df, suffix)
    attrs = dict(params)
    if use_v:
        attrs["_vwap"] = test["VWAP"].to_numpy()
        attrs["use_vwap"] = True
    bt = Backtest(test, type(f"A{tag}", (cls,), attrs), cash=C.CASH,
                  commission=commission, exclusive_orders=True)
    st = bt.run()
    r = row(st)
    r["comm"] = commission * 10000  # bp per side
    return r


# ---------------- A. COST MATRIX ----------------
MATRIX = [
    ("H01a 1h", "1h", "", TrendPullback, dict(n_fast=13, rsi_lo=35, atr_stop=2.5)),
    ("H01b 1h", "1h", "", TrendPullback, dict(n_fast=13, rsi_lo=35, atr_stop=2.5, use_vwap=True)),
    ("H02a 1h", "1h", "", ShortTrendPullback, dict(n_fast=9, atr_stop=2.5)),
    ("H02b 1h", "1h", "", ShortTrendPullback, dict(n_fast=9, atr_stop=2.5, use_vwap=True)),
    ("H02a 4h", "4h", "", ShortTrendPullback, dict(n_fast=5, atr_stop=1.5)),
    ("H02b 4h", "4h", "", ShortTrendPullback, dict(n_fast=5, atr_stop=1.5, use_vwap=True)),
    ("H04a 1h", "1h", "", Rsi2Reversion, dict(rsi_buy=5, atr_stop=1.5, time_stop=48)),
    ("H04a 4h", "4h", "", Rsi2Reversion, dict(rsi_buy=5, atr_stop=1.5, time_stop=48)),
    ("H03 1h deep", "1h", "_deep", DonchianBreakout, dict(n_enter=20, n_exit=10, atr_stop=3.0)),
    ("H03 4h deep", "4h", "_deep", DonchianBreakout, dict(n_enter=40, n_exit=10, atr_stop=2.0)),
]


def cost_matrix(md):
    md += ["## A. Cost matrix (frozen params, OOS windows only)", "",
           "| Variant | 7bp Ret% | 7bp PF | 2bp Ret% | 2bp PF | 0bp Ret% | 0bp PF | Alive at 7bp? | Alive at maker? |",
           "|---|---|---|---|---|---|---|---|---|"]
    alive7, alive_m = 0, 0
    for tag, tf, suf, cls, params in MATRIX:
        r7 = eval_frozen("BTCUSDT", tf, suf, cls, dict(params), 0.0007, tag)
        rm = eval_frozen("BTCUSDT", tf, suf, cls, dict(params), 0.0002, tag)
        r0 = eval_frozen("BTCUSDT", tf, suf, cls, dict(params), 0.0, tag)
        a7 = num(r7["PF"]) > 1 and num(r7["Ret%"]) > 0
        am = num(rm["PF"]) > 1 and num(rm["Ret%"]) > 0
        alive7 += int(a7)
        alive_m += int(am)
        md.append(f"| {tag} | {fmt(r7['Ret%'])} | {fmt(r7['PF'])} | {fmt(rm['Ret%'])} | {fmt(rm['PF'])} "
                  f"| {fmt(r0['Ret%'])} | {fmt(r0['PF'])} | {str(a7)} | {str(am)} |")
    md += ["", f"- Alive at 7bp: {alive7}/{len(MATRIX)}. Alive at maker 2bp: {alive_m}/{len(MATRIX)}.",
           "- Verdict rule: a dead strategy only flips to MAKER-CANDIDATE if it is alive at 2bp AND dead at 7bp.",
           ""]
    return md, alive_m


# ---------------- B. POSITIVE CONTROLS ----------------
def daily_df(sym):
    df1h = load(sym, "1h", "_deep")
    agg = df1h.resample("1D", label="left", closed="left").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna()
    return agg


def bh_stats(px):
    r = np.diff(np.log(px))
    sh = float(r.mean() / r.std() * np.sqrt(365)) if r.std() > 0 else float("nan")
    peak = np.maximum.accumulate(px)
    return {"Ret%": (px[-1] / px[0] - 1) * 100, "Sharpe": sh, "MaxDD%": float((px / peak - 1).min() * 100)}


def run_control(tag, cls, grid, md):
    df = daily_df("BTCUSDT")
    test_start = df.index[0] + pd.DateOffset(months=C.TRAIN_MONTHS)
    test_end = test_start + pd.DateOffset(months=C.TEST_MONTHS)
    train, test = df[df.index < test_start], df[(df.index >= test_start) & (df.index < test_end)]
    bt = Backtest(train, type(f"{tag}opt", (cls,), {}), cash=C.CASH, commission=0.0003,
                  exclusive_orders=True)
    best = bt.optimize(**grid, maximize="Sharpe Ratio")
    strat = best["_strategy"] if "_strategy" in best.index else getattr(best, "_strategy", None)
    P = {g: getattr(strat, g) for g in grid}
    bt2 = Backtest(test, type(tag, (cls,), P), cash=C.CASH, commission=0.0003, exclusive_orders=True)
    st = bt2.run()
    r = row(st)
    days = (test.index[-1] - test.index[0]).days
    expo = num(st.get("Exposure Time [%]", 0)) / 100
    drag = expo * days * 0.03  # funding haircut: 3bp/day while in market (longs, avg funding)
    net_ret = num(r["Ret%"]) - drag
    bhrs = bh_stats(np.asarray(test["Close"]))
    bh_net = bhrs["Ret%"] - days * 0.03
    gates = {
        "net_ret>0": net_ret > 0,
        "Sharpe>0": num(r["Sharpe"]) > 0,
        "DD better than B&H by >=10pp": num(r["MaxDD%"]) >= bhrs["MaxDD%"] + 10,
        "trades>=3": num(r["Trades"]) >= 3,
    }
    md += [f"### {tag} (params: {', '.join(f'{k}={v:g}' for k, v in P.items())})", "",
           f"- Test stats: Ret {fmt(r['Ret%'])}%, Sharpe {fmt(r['Sharpe'])}, MaxDD {fmt(r['MaxDD%'])}%, "
           f"trades {r['Trades']:.0f}, PF {fmt(r['PF'])}",
           f"- Funding haircut: -{drag:.2f}% -> NET Ret {fmt(net_ret)}%",
           f"- B&H same window: Ret {fmt(bhrs['Ret%'])}% (net {fmt(bh_net)}%), MaxDD {fmt(bhrs['MaxDD%'])}%",
           f"- Gates: " + " | ".join(f"{k}: {'PASS' if v else 'FAIL'}" for k, v in gates.items()), ""]
    return gates


def positive_controls(md):
    md += ["## B. Positive control battery (freeze rule)", "",
           "Documented-edge daily strategies, same walk-forward (48m train -> 12m judge Nov25-Nov26),",
           "maker costs 2bp+slip per side, funding haircut 3bp/day while long.", ""]
    g1 = run_control("H00a_DailyMomentum", DailyMomentum, dict(n_sma=[100, 150], n_roc=[20, 30, 50]), md)
    g2 = run_control("H00b_DailyRegime", DailyRegime, dict(n_sma=[100, 150, 200]), md)
    p1 = all(g1.values())
    p2 = all(g2.values())
    if p1 and p2:
        freeze = "BOTH PASS -> machine can certify green. Prior verdicts STAND."
    elif (not p1) and (not p2):
        freeze = "BOTH FAIL -> ALL STRATEGY VERDICTS FROZEN. Debug harness before any further testing."
    else:
        freeze = "MIXED -> suspicious harness. Freeze until explained."
    md += [f"**Freeze decision: {freeze}**", ""]
    return freeze


# ---------------- C. TRADE FORENSICS ----------------
def forensics(md):
    results = []
    # H01a 2y era: verify pullback conditions at signal bar (EntryBar-1)
    df = load("BTCUSDT", "1h", "")
    df["VWAP"] = vwap_daily(df)
    _, test = split_for(df, "")
    params = dict(n_fast=13, rsi_lo=35, atr_stop=2.5)
    bt = Backtest(test, type("F1", (TrendPullback,), params), cash=C.CASH,
                  commission=0.0007, exclusive_orders=True)
    st = bt.run()
    tr = st["_trades"]
    f = ema(test.Close, params["n_fast"]).to_numpy()
    s = ema(test.Close, 21).to_numpy()
    rg = ema(test.Close, 200).to_numpy()
    rv = rsi_w(test.Close, 14).to_numpy()
    o = np.asarray(test["Open"], float)
    violations, checked = 0, 0
    for _, t in tr.iterrows():
        sig = int(t["EntryBar"]) - 1
        if sig < 0:
            continue
        checked += 1
        ok = (test.Close.iloc[sig] > rg[sig] and f[sig] > s[sig]
              and test.Low.iloc[sig] <= f[sig] and test.Close.iloc[sig] > f[sig]
              and params["rsi_lo"] <= rv[sig] <= 65)
        if not ok:
            violations += 1
    results.append(("H01a 1h", checked, violations))

    # H03 4h deep: verify Donchian entries
    df = load("BTCUSDT", "4h", "_deep")
    _, test = split_for(df, "_deep")
    params = dict(n_enter=40, n_exit=10, atr_stop=2.0)
    bt = Backtest(test, type("F3", (DonchianBreakout,), params), cash=C.CASH,
                  commission=0.0007, exclusive_orders=True)
    st = bt.run()
    tr = st["_trades"]
    hh = pd.Series(np.asarray(test["High"], float)).rolling(40).max().shift(1).to_numpy()
    rg = ema(test.Close, 200).to_numpy()
    violations, checked = 0, 0
    for _, t in tr.iterrows():
        sig = int(t["EntryBar"]) - 1
        if sig < 0:
            continue
        checked += 1
        ok = (test.Close.iloc[sig] > hh[sig]) and (test.Close.iloc[sig] > rg[sig])
        if not ok:
            violations += 1
    results.append(("H03 4h deep", checked, violations))

    md += ["## C. Trade forensics", "",
           "| Strategy | Entries checked | Condition violations | Verdict |", "|---|---|---|---|"]
    for tag, n, v in results:
        md.append(f"| {tag} | {n} | {v} | {('ENGINE FAITHFUL' if v == 0 else 'BUG -> re-verdict everything')} |")
    md.append("")
    return all(v == 0 for _, _, v in results)


def main():
    os.makedirs(OUT, exist_ok=True)
    md = ["# AUDIT REPORT (Session 3) - pre-registered", "",
          f"Data: BTCUSDT. Frozen variants from JOURNAL. Costs per side as labeled. "
          f"Cash ${C.CASH:.0f}, risk {C.RISK_PCT * 100:.0f}%/trade.", ""]
    md, alive_m = cost_matrix(md)
    freeze_note = positive_controls(md)
    engine_ok = forensics(md)

    md += ["## FINAL STAMPS", "",
           f"- Engine forensics: {'FAITHFUL -> verdicts stay valid' if engine_ok else 'BUG -> verdicts suspended'}.",
           f"- Controls: {freeze_note}",
           f"- Cost matrix: {alive_m}/{len(MATRIX)} variants were alive at maker-only costs "
           "(H06 limit-entry emulation confirmed as the frontier hypothesis if >0).", ""]
    path = os.path.join(OUT, "audit_report.md")
    open(path, "w", encoding="utf-8").write("\n".join(md))
    print(f"[audit] written: {path}")


if __name__ == "__main__":
    main()
