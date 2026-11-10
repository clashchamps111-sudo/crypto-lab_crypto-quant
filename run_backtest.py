"""Walk-forward harness v2 - HYPOTHESIS FACTORY.
Golden rules unchanged:
1. The optimizer only ever sees the TRAIN window.
2. Every result charged realistic costs (config.COMMISSION_PER_SIDE).
3. Grid <= 16 combos per optimization pass (no brute-force overfitting).
4. TEST window evaluated ONCE with the chosen params. Absolute truth.
Per-hypothesis write-up in out/<ID>_report.md + combined session summary.
H01 evidence preserved in out/H01_report.md (DEAD)."""
import os

import numpy as np
import pandas as pd

from backtesting import Backtest

import config as C
from indicators import vwap_daily
from strategies import DonchianBreakout, Rsi2Reversion, ShortTrendPullback

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")

KEYS = [("Return [%]", "Ret%"), ("Sharpe Ratio", "Sharpe"), ("Max. Drawdown [%]", "MaxDD%"),
        ("# Trades", "Trades"), ("Profit Factor", "PF"), ("Win Rate [%]", "Win%")]

HYPOTHESES = {
    # H02: mirrored bear-regime short on perp 1x. Funding note: shorts often
    # RECEIVE funding in positive-funding markets - cost model stays conservative.
    "H02": dict(cls=ShortTrendPullback,
                grid=dict(n_fast=[5, 9, 13], atr_stop=[1.5, 2.5]),
                vwap=(False, True), tfs=C.TIMEFRAMES),
    # H03: classic Donchian 20/10 breakout, long-only, bull regime gate, no TP.
    "H03": dict(cls=DonchianBreakout,
                grid=dict(n_enter=[20, 40], n_exit=[10, 20], atr_stop=[2.0, 3.0]),
                vwap=(False,), tfs=C.TIMEFRAMES),
    # H04: RSI(2) dip reversion inside bull regime.
    "H04": dict(cls=Rsi2Reversion,
                grid=dict(rsi_buy=[5, 15], atr_stop=[1.5, 2.5], time_stop=[48, 96]),
                vwap=(False,), tfs=C.TIMEFRAMES),
}


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


def split(df):
    train_end = df.index[0] + pd.DateOffset(months=C.TRAIN_MONTHS)
    test_end = train_end + pd.DateOffset(months=C.TEST_MONTHS)
    return df[df.index < train_end], df[(df.index >= train_end) & (df.index < test_end)]


def extract_params(stats, param_names):
    estrat = None
    try:
        strat = stats["_strategy"]
    except Exception:
        strat = getattr(stats, "_strategy", None)
    best = {}
    for n in param_names:
        v = float("nan")
        if n in stats.index:
            v = num(stats[n])
        if (not np.isfinite(v)) and strat is not None:
            v = num(getattr(strat, n, np.nan))
        if not np.isfinite(v):
            raise RuntimeError(f"param '{n}' not found in optimize() result")
        best[n] = v
    return best


def buy_hold(test, tf):
    px = np.asarray(test["Close"], dtype=float)
    r = np.diff(np.log(px))
    per_year = 24 * 365 if tf == "1h" else 6 * 365
    sh = float(r.mean() / r.std() * np.sqrt(per_year)) if r.std() > 0 else float("nan")
    peak = np.maximum.accumulate(px)
    return {"Ret%": (px[-1] / px[0] - 1.0) * 100.0, "Sharpe": sh, "MaxDD%": float((px / peak - 1.0).min() * 100.0)}


def verdict_of(te, bh):
    bh_sh = bh["Sharpe"] if np.isfinite(bh["Sharpe"]) else -999.0
    if te["Ret%"] > 0 and te["Sharpe"] > 0.5 and te["Sharpe"] > bh_sh:
        return "ALIVE (preliminary)"
    if te["Ret%"] <= -3.0 or (np.isfinite(te["PF"]) and te["PF"] < 0.9):
        return "DEAD"
    return "MARGINAL"


def run_variant(tag, hyp, grid, cls, tf, train, test, use_vwap, summary):
    """Always run optimization against a THROWAWAY subclass so parameter mutation
    cannot leak between variants."""
    param_names = list(grid.keys())
    base_attrs = {"use_vwap": use_vwap, "_vwap": train["VWAP"].to_numpy()}
    base = type(f"{hyp}_{tf}_{'v' if use_vwap else 'p'}_train", (cls,), base_attrs)
    bt = Backtest(train, base, cash=C.CASH, commission=C.COMMISSION_PER_SIDE, exclusive_orders=True)
    try:
        best = bt.optimize(**grid, maximize="Sharpe Ratio")
    except Exception as e:
        print(f"[{hyp}] {tag}: optimize FAILED: {e}")
        return None
    params = extract_params(best, param_names)
    tr = row(best)

    test_attrs = {"_vwap": test["VWAP"].to_numpy(), **params}
    if use_vwap:
        test_attrs["use_vwap"] = True
    sub = type(f"{hyp}_{tf}_{'v' if use_vwap else 'p'}_test", (cls,), test_attrs)
    bt_test = Backtest(test, sub, cash=C.CASH, commission=C.COMMISSION_PER_SIDE, exclusive_orders=True)
    ts = bt_test.run()
    te = row(ts)
    bh = buy_hold(test, tf)
    verdict = verdict_of(te, bh)

    summary.append(dict(hyp=hyp, tag=tag, tf=tf, vwap=use_vwap, params=params,
                        train=tr, test=te, bh=bh, verdict=verdict))
    print(f"[{hyp}] {tag} params={params}")
    print(f"      TRAIN  {tr}")
    print(f"      TEST   {te}  B&H {bh}  -> {verdict}")


def run_hyp(hyp, cfg):
    summary = []
    for tf in cfg["tfs"]:
        path = os.path.join(ROOT, "data", f"{C.PAIR}_{tf}{C.DATA_SUFFIX}.csv")
        df = pd.read_csv(path, parse_dates=["Date"], index_col="Date").astype(float)
        df[["Open", "High", "Low", "Close"]] = df[["Open", "High", "Low", "Close"]] / C.PRICE_SCALE
        df["VWAP"] = vwap_daily(df)
        train, test = split(df)
        for uv in cfg["vwap"]:
            run_variant(f"{hyp}{'b' if uv else 'a'} {tf}", hyp, cfg["grid"], cfg["cls"],
                        tf, train, test, uv, summary)
    write_report(hyp, summary)
    return summary


def write_report(hyp, summary):
    lines = [f"# {hyp} Report Card", "",
             f"Data: Binance {C.PAIR} spot-style OHLC (prices scaled by 1e6, economics identical). "
             f"Costs: {C.COMMISSION_PER_SIDE * 100:.2f}% per side. Cash ${C.CASH:.0f}, risk {C.RISK_PCT * 100:.0f}%/trade.",
             f"Walk-forward: optimize first {C.TRAIN_MONTHS} months, test = final {C.TEST_MONTHS} months (untouched).", "",
             "| Variant | Train Ret% | Train Sharpe | TEST Ret% | TEST Sharpe | TEST MaxDD% | TEST PF | TEST Win% | TEST Trades | B&H Ret% | B&H DD% | Verdict |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in summary:
        p = s["params"]
        pd_s = "; ".join(f"{k}={v:g}" for k, v in sorted(p.items()))
        lines.append(
            f"| {s['tag']} (vwap={int(s['vwap'])}; {pd_s}) "
            f"| {fmt(s['train']['Ret%'])} | {fmt(s['train']['Sharpe'])} "
            f"| {fmt(s['test']['Ret%'])} | {fmt(s['test']['Sharpe'])} | {fmt(s['test']['MaxDD%'])} "
            f"| {fmt(s['test']['PF'])} | {fmt(s['test']['Win%'], 1)} | {s['test']['Trades']:.0f} "
            f"| {fmt(s['bh']['Ret%'])} | {fmt(s['bh']['MaxDD%'])} | {s['verdict']} |")
    lines += ["", "## Honest reading", "",
              "- TEST column is the only truth. Train numbers are what the optimizer wished into existence.",
              "- ALIVE (preliminary) = positive OOS return, Sharpe > 0.5, beats B&H risk-adjusted, vendeur survives next gauntlet steps (robustness nudge + 2y consistency + testnet), BEFORE any live money.",
              "- DEAD feeds the hypothesis log; a killed hypothesis for $0 of tuition is the desk working.", ""]
    path = os.path.join(OUT, f"{hyp}_report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[{hyp}] report written: {path}")


def main():
    os.makedirs(OUT, exist_ok=True)
    wanted = os.environ.get("HYP")  # optional single-hypothesis filter: e.g. HYP=H03
    all_summary = []
    for hyp, cfg in HYPOTHESES.items():
        if wanted and hyp != wanted:
            continue
        print(f"\n===== {hyp} =====")
        all_summary += run_hyp(hyp, cfg)
    # Combined session summary
    lines = ["# Session summary - hypothesis factory", "",
             "| Hyp | Variant | TEST Ret% | TEST Sharpe | TEST PF | TEST Win% | Trades | Verdict |", "|---|---|---|---|---|---|---|---|"]
    for s in all_summary:
        lines.append(f"| {s['hyp']} | {s['tag']} | {fmt(s['test']['Ret%'])} | {fmt(s['test']['Sharpe'])} "
                     f"| {fmt(s['test']['PF'])} | {fmt(s['test']['Win%'], 1)} | {s['test']['Trades']:.0f} | {s['verdict']} |")
    path = os.path.join(OUT, "session_summary.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n[factory] session summary written: {path}")


if __name__ == "__main__":
    main()
