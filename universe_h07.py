"""UNIVERSE GAUNTLET - Session 6 primary line (pre-registered in JOURNAL).
Frozen H00a identity (DailyMomentum n_sma=100, n_roc=30) applied to the 10-symbol
basket: BTC, ETH + BNB, SOL, XRP, DOGE, ADA, LINK, AVAX, TRX (5y spot klines).
Shared ABSOLUTE test year (UTC 2025-11-05 -> 2026-11-04), 4x3m folds, 150d warmup
lead, trades counted only if entered in-window, 7bp/side + 3bp/day funding haircut.

Gates (pre-registered):
  B1 basket pooled NET > 0
  B2 >= 60% of the 10 symbols net-positive
  B3 >= 60% of the 9-neighbor documented grid pooled-net-positive (full basket)
  B4 mean per-symbol net > 0 (single-luck guard)
  B5 continuity: BTC must reproduce Session-5 pool (+3.90) and ETH (+3.35)
     within +-0.5 (absolute-date folds == Session-5 month-anchor folds)
Verdict: all of B1-B4 (and B5 within tolerance) -> GAUNTLET-CERTIFIED;
B1 fail -> DEAD; partial -> MARGINAL.
Standing rules: no maker bolt-ons; no re-optimization; realized net of haircut."""
import os

import numpy as np
import pandas as pd

from backtesting import Backtest

import audit as A
from strategies import DailyMomentum

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")

UNIVERSE = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
            "DOGEUSDT", "ADAUSDT", "LINKUSDT", "AVAXUSDT", "TRXUSDT"]
PARAMS = dict(n_sma=100, n_roc=30)
COMM = 0.0007
FUND_BPS_DAY = 0.0003
WARMUP_DAYS = 150
FOLD_T0 = pd.Timestamp("2025-11-05")
FOLD_MONTHS = 3
N_FOLDS = 4
CONT_TOL = 0.5
SESSION5 = {"BTCUSDT": 3.90, "ETHUSDT": 3.35}
GRID9 = dict(n_sma=[100, 150, 200], n_roc=[20, 30, 50])


def fold_daily(sym):
    df = A.daily_df(sym)
    per_sym = []
    for i in range(N_FOLDS):
        a = FOLD_T0 + pd.DateOffset(months=i * FOLD_MONTHS)
        bnd = FOLD_T0 + pd.DateOffset(months=(i + 1) * FOLD_MONTHS)
        w = df[(df.index >= a - pd.Timedelta(days=WARMUP_DAYS)) & (df.index < bnd)]
        per_sym.append((a, bnd, w))
    return per_sym


def fold_net(w, fold_a, params):
    st = Backtest(w, type("UF", (DailyMomentum,), dict(params)),
                  cash=100.0, commission=COMM, exclusive_orders=True).run()
    t = st["_trades"]
    if len(t):
        tw = t[t["EntryTime"] >= fold_a]
        realized = float(tw["PnL"].sum()) if len(tw) else 0.0
        days = (tw["ExitBar"] - tw["EntryBar"]).astype(float)
        notional = tw["Size"].abs() * tw["EntryPrice"]
        drag = float((days * notional).sum()) * FUND_BPS_DAY
    else:
        realized, drag, tw = 0.0, 0.0, t
    final = float(st["_equity_curve"]["Equity"].iloc[-1])
    residual = (final - 100.0) - realized
    return dict(realized=realized, drag=drag, net=realized - drag,
                n=int(len(tw)) if len(t) else 0, sh=A.num(st.get("Sharpe Ratio", np.nan)),
                residual=residual)


def main():
    os.makedirs(OUT, exist_ok=True)
    md = ["# UNIVERSE GAUNTLET - Session 6 (pre-registered in JOURNAL)", "",
          f"10-symbol basket, frozen H00a identity, absolute test year "
          f"{FOLD_T0.date()} + {N_FOLDS}x{FOLD_MONTHS}m, 150d warmup, "
          f"{COMM * 10000:.0f}bp/side + {FUND_BPS_DAY * 10000:.0f}bp/day haircut, "
          "in-window-entry accounting.", ""]
    sym_pools = {}
    table_rows = []
    for sym in UNIVERSE:
        folds = fold_daily(sym)
        fs = [fold_net(w, a, PARAMS) for a, _, w in folds]
        net = sum(f["net"] for f in fs)
        rea = sum(f["realized"] for f in fs)
        ntr = sum(f["n"] for f in fs)
        shs = [f["sh"] for f in fs if np.isfinite(f["sh"])]
        msh = float(np.mean(shs)) if shs else float("nan")
        fpos = sum(1 for f in fs if f["net"] > 0)
        sym_pools[sym] = dict(net=net, realized=rea, n=ntr, msh=msh,
                              fpos=fpos, folds=fs)
        table_rows.append((sym, rea, net, ntr, msh, fpos, fs))

    net_assets = [s for s in sym_pools if sym_pools[s]["net"] > 0]
    b1 = sum(p["net"] for p in sym_pools.values()) > 0
    b2 = len(net_assets) / len(UNIVERSE) >= 0.60
    b4 = float(np.mean([p["net"] for p in sym_pools.values()])) > 0

    # neighbor grid across the FULL basket
    combos, pos_n = [], 0
    for ns in GRID9["n_sma"]:
        for nr in GRID9["n_roc"]:
            pn = 0.0
            for sym in UNIVERSE:
                for a, _, w in fold_daily(sym):
                    pn += fold_net(w, a, dict(n_sma=ns, n_roc=nr))["net"]
            combos.append((dict(n_sma=ns, n_roc=nr), pn))
            pos_n += int(pn > 0)
    b3 = pos_n / len(combos) >= 0.60

    # continuity B5
    cont = {}
    for sym, target in SESSION5.items():
        got = sym_pools[sym]["net"]
        cont[sym] = (target, got, abs(got - target) <= CONT_TOL)
    b5_ok = all(c[2] for c in cont.values())

    gates = {
        "B1 basket pooled net >0": b1,
        "B2 >=60% symbols net-positive": b2,
        "B3 >=60% of 9 neighbors net-positive (basket)": b3,
        "B4 mean per-symbol net >0": b4,
        "B5 BTC/ETH continuity within +-0.5": b5_ok,
    }
    if all(gates.values()):
        verdict = "GAUNTLET-CERTIFIED"
    elif not gates["B1 basket pooled net >0"]:
        verdict = "DEAD"
    else:
        verdict = "MARGINAL (failed: " + "; ".join(k for k, ok in gates.items() if not ok) + ")"

    md += ["## Per-symbol fold pools", "",
           "| Symbol | Realized $ | Net $ | Trades | Mean fold Sharpe | Folds net-pos |",
           "|---|---|---|---|---|---|"]
    for sym, rea, net, ntr, msh, fpos, _ in table_rows:
        md.append(f"| {sym} | {rea:+.2f} | {net:+.2f} | {ntr} | {A.fmt(msh)} | {fpos}/{N_FOLDS} |")
    md += [f"- Basket pooled net: {sum(p['net'] for p in sym_pools.values()):+.2f} "
           f"across {sum(p['n'] for p in sym_pools.values())} closed trades",
           f"- Net-positive symbols: {len(net_assets)}/{len(UNIVERSE)} "
           f"({', '.join(net_assets) if net_assets else 'none'})",
           f"- Neighbors: {pos_n}/{len(combos)} basket-net-positive = {pos_n / len(combos):.0%}",
           "- Continuity: "
           + "; ".join(f"{s}: target {t:+.2f}, got {g:+.2f} ({'OK' if ok else 'OUT'})"
                       for s, (t, g, ok) in cont.items()), "",
           "**Gates:**"] + [f"- {k}: {'PASS' if ok else 'FAIL'}" for k, ok in gates.items()] \
          + [f"- **VERDICT: {verdict}**", "",
             "## Per-symbol fold detail", ""]
    for sym, _, _, _, _, _, fs in table_rows:
        md.append(f"### {sym}")
        md += ["| Fold | Realized | Drag | Net | Trades | Sharpe | Residual |",
               "|---|---|---|---|---|---|---|"]
        for i, f in enumerate(fs, 1):
            md.append(f"| {i} | {f['realized']:+.2f} | {f['drag']:+.2f} | {f['net']:+.2f} "
                      f"| {f['n']} | {A.fmt(f['sh'])} | {f['residual']:+.2f} |")
        md.append("")
    path = os.path.join(OUT, "universe_report.md")
    open(path, "w", encoding="utf-8").write("\n".join(md))
    print(f"[universe] verdict: {verdict}")
    print(f"[universe] written: {path}")
    for sym, rea, net, ntr, msh, fpos, _ in table_rows:
        print(f"  {sym:9s} net {net:+7.2f} trades {ntr:3d} folds+ {fpos}/4 sharp {A.fmt(msh)}")


if __name__ == "__main__":
    main()
