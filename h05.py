"""H05 Gauntlet - VWAP-band intraday mean reversion (1h), conventional market
execution (maker-as-bolt-on banned by H06 evidence; judged at 7bp/side only).

Pre-registered BEFORE any run:
STAGE 1 walk-forward: train = first 48 months of the 5y deep series; grid
  k_band {1.0, 1.5, 2.0} x atr_stop {1.5, 3.0} x time_stop {8, 24} = 12 combos
  (<=16 rule); optimize Sharpe on TRAIN; TEST = final 12 months run ONCE with
  frozen winner at 7bp/side. Verdict gates (factory standard):
  ALIVE iff TEST Ret>0 AND Sharpe>0.5 AND Sharpe beats B&H AND PF>=1.0;
  DEAD iff Ret<=-3 OR PF<0.9; else MARGINAL.
STAGE 2 (ONLY if ALIVE): fold battery = 4x3m folds over the test year at 7bp,
  the same 12 combos as the neighbor battery (>=60% pooled-realized-positive),
  ETH cross-check with frozen winner, realized/unrealized purity |open@cutoff|
  <= 25% of realized, pooled closed >= 60 (intraday cadence floor).
  ALL -> GAUNTLET-CERTIFIED; pooled-realized<=0 -> DEAD; else MARGINAL.
Standing rules applied: realized/unrealized split; cost snapshot (= 7bp, single
bracket; nothing flips on maker); no re-optimization after testing."""
import os

from itertools import product

import numpy as np
import pandas as pd

from backtesting import Backtest

import config as C
import audit as A
from indicators import vwap_band_arrays
from strategies import VwapBandReversion

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")

GRID = dict(k_band=[1.0, 1.5, 2.0], atr_stop=[1.5, 3.0], time_stop=[8, 24])
COMM = 0.0007  # 7bp/side official
FOLD_MONTHS = 3
N_FOLDS = 4
NEIGHBOR_SHARE = 0.60
TRADE_FLOOR = 60


def prepare(df):
    """Inject lookahead-safe vwap/sigma arrays on a sliced window."""
    w = df.copy()
    v, s = vwap_band_arrays(w, min_bars=3)
    w["_vwap_arr"] = v
    w["_sig_arr"] = s
    return w


def cls_with(P, w, name):
    attrs = dict(P, _vwap=w["_vwap_arr"].to_numpy(), _sig=w["_sig_arr"].to_numpy())
    return type(name, (VwapBandReversion,), attrs)


def run_window(cls2, window, comm=COMM):
    st = Backtest(window, cls2, cash=C.CASH, commission=comm, exclusive_orders=True).run()
    t = st["_trades"]
    realized = float(t["PnL"].sum()) if len(t) else 0.0
    final = float(st["_equity_curve"]["Equity"].iloc[-1]) if len(st["_equity_curve"]) else C.CASH
    unreal = final - C.CASH - realized
    trades = int(st["# Trades"])
    sharpe = A.num(st.get("Sharpe Ratio", np.nan))
    return dict(st=st, r=realized, u=unreal, n=trades, sh=sharpe)


def bh(window):
    px = np.asarray(window["Close"], float)
    r = np.diff(np.log(px))
    sh = float(r.mean() / r.std() * np.sqrt(24 * 365)) if r.std() > 0 else float("nan")
    peak = np.maximum.accumulate(px)
    return dict(Ret=float((px[-1] / px[0] - 1) * 100), Sharpe=sh,
                DD=float((px / peak - 1).min() * 100))


def stage1():
    """Train-window optimization -> frozen TEST judgment. Returns (verdict, P, bundles)."""
    df = A.load("BTCUSDT", "1h", "_deep")
    train_end = df.index[0] + pd.DateOffset(months=C.TRAIN_MONTHS)
    train = prepare(df[df.index < train_end])
    test = prepare(df[df.index >= train_end])
    bt = Backtest(train, type("H05opt", (VwapBandReversion,), {}),
                  cash=C.CASH, commission=COMM, exclusive_orders=True)
    best = bt.optimize(**GRID, maximize="Sharpe Ratio")
    strat = best["_strategy"]
    P = {g: float(getattr(strat, g)) for g in GRID}
    tr = run_window(cls_with(P, train, "H05tr"), train)
    te = run_window(cls_with(P, test, "H05te"), test)
    r = A.row(te["st"])
    b = bh(test)
    alive = (r["Ret%"] > 0 and r["Sharpe"] > 0.5 and r["Sharpe"] > b["Sharpe"]
             and r["PF"] >= 1.0)
    dead = (r["Ret%"] <= -3.0 or r["PF"] < 0.9)
    verdict = "ALIVE (preliminary)" if (alive and not dead) else ("DEAD" if dead else "MARGINAL")
    md = [f"### Stage 1 - frozen winner: {', '.join(f'{k}={v:g}' for k, v in P.items())}", "",
          f"- TRAIN (48m): Ret {A.num(tr['st']['Return [%]']):+.2f}%, "
          f"Sharpe {A.num(tr['st']['Sharpe Ratio']):.2f}, trades {tr['n']}, realized ${tr['r']:+.2f}",
          f"- TEST (12m judge, 7bp/side): Ret {r['Ret%']:+.2f}%, Sharpe {r['Sharpe']:.2f}, "
          f"MaxDD {r['MaxDD%']:.2f}%, PF {r['PF']:.2f}, trades {r['Trades']:.0f}, "
          f"Win {r['Win%']:.1f}%, realized ${te['r']:+.2f}, unreal ${te['u']:+.2f}",
          f"- B&H same window: Ret {b['Ret']:+.2f}%, Sharpe {b['Sharpe']:.2f}, DD {b['DD']:.2f}%",
          f"- **STAGE 1 VERDICT: {verdict}**", ""]
    return verdict, P, md


def window_folds(df, sym=False, t0=None):
    """Fold windows over the test year: months [48, 60) in FOLD_MONTHS slices."""
    t0 = t0 if t0 is not None else df.index[0]
    te_start = t0 + pd.DateOffset(months=C.TRAIN_MONTHS)
    out = []
    for i in range(N_FOLDS):
        a = te_start + pd.DateOffset(months=i * FOLD_MONTHS)
        bnd = te_start + pd.DateOffset(months=(i + 1) * FOLD_MONTHS)
        w = df[(df.index >= a) & (df.index < bnd)]
        if len(w):
            out.append((i, prepare(w)))
    return out


def stage2(P):
    df = A.load("BTCUSDT", "1h", "_deep")
    dfe = A.load("ETHUSDT", "1h", "_deep")
    folds = window_folds(df)
    fs = [run_window(cls_with(P, w, f"H05f{i}"), w) for i, w in folds]
    pool_r = sum(f["r"] for f in fs)
    pool_tr = sum(f["n"] for f in fs)
    pool_u = sum(f["u"] for f in fs)
    shs = [f["sh"] for f in fs if np.isfinite(f["sh"])]
    mean_sh = float(np.mean(shs)) if shs else float("nan")
    folds_pos = sum(1 for f in fs if f["r"] > 0)

    combos, pos_n = [], 0
    for kb, at, ts in product(GRID["k_band"], GRID["atr_stop"], GRID["time_stop"]):
        pars = dict(k_band=kb, atr_stop=at, time_stop=ts)
        pr = 0.0
        for i, w in folds:
            pr += run_window(cls_with(pars, w, "H05nb"), w)["r"]
        combos.append((pars, pr))
        pos_n += int(pr > 0)
    nb_share = pos_n / len(combos)

    eth_r = sum(run_window(cls_with(P, w, "H05eth"), w)["r"] for i, w in window_folds(dfe))

    unreal_share = abs(pool_u) / abs(pool_r) if pool_r else float("inf")
    gates = {
        "G1 pooled realized>0": pool_r > 0,
        "G2 mean fold Sharpe>0": mean_sh > 0,
        "G3 >=3/4 folds realized-positive": folds_pos >= 3,
        "G4 >=60% of 12 neighbors positive": nb_share >= NEIGHBOR_SHARE,
        "G5 ETH pooled realized>0": eth_r > 0,
        "G6 unreal <=25% of realized": unreal_share <= 0.25,
        "G7 pooled closed >=60": pool_tr >= TRADE_FLOOR,
    }
    if all(gates.values()):
        verdict = "GAUNTLET-CERTIFIED"
    elif not gates["G1 pooled realized>0"]:
        verdict = "DEAD"
    else:
        verdict = "MARGINAL (failed: " + "; ".join(k for k, ok in gates.items() if not ok) + ")"

    md = [f"### Stage 2 - fold gauntlet (only-if-alive rule) | {N_FOLDS} x {FOLD_MONTHS}m folds, 7bp/side", "",
          "| Fold | Realized $ | Unreal $ | Trades | Sharpe |", "|---|---|---|---|---|"]
    for (i, _), f in zip(folds, fs):
        md.append(f"| {i + 1} | {f['r']:+.2f} | {f['u']:+.2f} | {f['n']} | {A.fmt(f['sh'])} |")
    md += [f"- **Pool: realized {pool_r:+.2f}, trades {pool_tr}, mean fold Sharpe {mean_sh:.2f}, "
           f"folds-positive {folds_pos}/{N_FOLDS}, unreal share {unreal_share:.0%}**",
           f"- Neighbors: {pos_n}/{len(combos)} pooled-positive = {nb_share:.0%}",
           f"- ETH pool: realized {eth_r:+.2f}",
           "**Gates:**"] + [f"- {k}: {'PASS' if ok else 'FAIL'}" for k, ok in gates.items()] \
          + [f"- **STAGE 2 VERDICT: {verdict}**", ""]
    return verdict, md


def main():
    os.makedirs(OUT, exist_ok=True)
    md = ["# H05 REPORT - VWAP-band intraday reversion (1h)", "",
          "Pre-registered two-stage battery (header). Costs 7bp/side everywhere.",
          "Realized/unrealized split per standing rule. VWAP arrays bar-local,",
          "UTC-day anchored, first 3h of each day masked.", ""]
    verdict, P, md1 = stage1()
    md += md1
    if verdict == "ALIVE (preliminary)":
        _, md2 = stage2(P)
        md += md2
    else:
        md += ["### Stage 2 skipped (only-if-alive rule)", "",
               f"Stage 1 said {verdict} - the fold gauntlet does not run unless the",
               "walk-forward judge clears. One-pass discipline preserved.", ""]
    path = os.path.join(OUT, "H05_report.md")
    open(path, "w", encoding="utf-8").write("\n".join(md))
    print(f"[H05] winner params: {P}")
    print(f"[H05] final verdict: {verdict}")
    print(f"[H05] written: {path}")


if __name__ == "__main__":
    main()
