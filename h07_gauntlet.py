"""H07 GAUNTLET - daily regime/momentum as a REAL candidate (H00a identity).

Provenance: params n_sma=100, n_roc=30 are FROZEN from the Session-3 positive
control battery (H00a walk-forward train-optimize). Supplier note: H00a was a
CONTROL (a signature of the harness health), not a certified strategy; this
battery is what promotes or kills it. NO re-optimization.

Pre-registered gates (daily cadence amendments, rationale documented):
  P1d pooled realized NET OF FUNDING > 0 (funding drag = per-trade
      days-held x notional x 3bp/day while long)
  P2d pooled CLOSED trades >= 6  (cadence amendment: a daily regime system in
      a hostile year produces ~3-10 closed trades; the equity-era 20-trade bar
      is mechanically impossible at this cadence - same reasoning as the
      Session-2 4h amendment)
  P3d mean fold Sharpe > 0
  P4d >= 2/4 folds realized(net)-positive (regime systems skip quarters; 3/4
      would demand a bull-only edge, which contradicts the class)
  P5d >= 60% of the 9 documented-grid neighbors (n_sma 100/150/200 x
      n_roc 20/30/50) pooled-net-positive
  P6d ETHUSDT daily pooled realized > 0
  P7d |unrealized open@cutoff| <= 25% of |realized|
  ALL -> GAUNTLET-CERTIFIED; P1d fail -> DEAD; else MARGINAL.
FOLD WARMUP RULE (pre-registered): each fold run starts 150 calendar days
  before its window (an SMA(100) cannot warm up inside 3 months), trades
  counted ONLY if entered inside the fold window; per the Session-3 M2M quirk,
  residual $ = window M2M net - realized-in-window-$ is reported and the
  unrealized-purity gate uses it.
PEEK folds deliberately skipped: months 36-48 of the daily frame are the exact
  data H00a optimized on - the 9-neighbor stability battery already covers
  in-sample-ness. No PEEK theater.
Cost model: 7bp/side taker + 3bp/day funding haircut. Maker brackets banned
  as bolt-ons (Session 4)."""
import os

import numpy as np
import pandas as pd

from backtesting import Backtest

import config as C
import audit as A
from strategies import DailyMomentum

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")

PARAMS = dict(n_sma=100, n_roc=30)
COMM = 0.0007
FUND_BPS_DAY = 0.0003
WARMUP_DAYS = 150
FOLD_MONTHS = 3
N_FOLDS = 4
NEIGHBOR_SHARE = 0.60
UNREAL_SHARE_MAX = 0.25
GRID9 = dict(n_sma=[100, 150, 200], n_roc=[20, 30, 50])
TRADE_FLOOR = 6


def fold_frame(df, fold_start_month):
    """[warmup, fold_end) slice; folds are FOLD_MONTHS long, starting at
    `fold_start_month` offset from the series t0."""
    t0 = df.index[0]
    a = t0 + pd.DateOffset(months=fold_start_month) - pd.Timedelta(days=WARMUP_DAYS)
    bnd = t0 + pd.DateOffset(months=fold_start_month + FOLD_MONTHS)
    w = df[(df.index >= a) & (df.index < bnd)]
    return w


def fold_stats(w, fold_a, params, comm=COMM):
    st = Backtest(w, type("H07f", (DailyMomentum,), dict(params)),
                  cash=C.CASH, commission=comm, exclusive_orders=True).run()
    t = st["_trades"]
    if len(t):
        in_win = t["EntryTime"] >= fold_a
        tw = t[in_win]
        realized = float(tw["PnL"].sum())
        days = (tw["ExitBar"] - tw["EntryBar"]).astype(float)
        notional = tw["Size"].abs() * tw["EntryPrice"]
        drag = float((days * notional).sum()) * FUND_BPS_DAY
    else:
        realized, drag, tw = 0.0, 0.0, t
    final = float(st["_equity_curve"]["Equity"].iloc[-1])
    m2m = final - C.CASH
    residual = m2m - realized  # open@cutoff + warmup-region marks (pre-registered proxy)
    return dict(realized=realized, drag=drag, net=realized - drag, m2m=m2m,
                residual=residual, n=int(len(tw)), sh=A.num(st.get("Sharpe Ratio", np.nan)))


def gauntlet(md):
    df = A.daily_df("BTCUSDT")
    dfe = A.daily_df("ETHUSDT")
    t0 = df.index[0]
    fold_stats_btc = []
    fold_rows = []
    for i in range(N_FOLDS):
        fs_m = C.TRAIN_MONTHS + i * FOLD_MONTHS
        a = t0 + pd.DateOffset(months=fs_m)
        w = fold_frame(df, fs_m)
        s = fold_stats(w, a, PARAMS)
        fold_stats_btc.append(s)
        fold_rows.append(s)
    net_pool = sum(f["net"] for f in fold_stats_btc)
    rea_pool = sum(f["realized"] for f in fold_stats_btc)
    n_pool = sum(f["n"] for f in fold_stats_btc)
    shs = [f["sh"] for f in fold_stats_btc if np.isfinite(f["sh"])]
    mean_sh = float(np.mean(shs)) if shs else float("nan")
    folds_pos = sum(1 for f in fold_stats_btc if f["net"] > 0)
    un_share = abs(sum(f["residual"] for f in fold_stats_btc)) / abs(rea_pool) if rea_pool else float("inf")

    # 9 documented-grid neighbors
    combos, pos_n = [], 0
    for ns in GRID9["n_sma"]:
        for nr in GRID9["n_roc"]:
            pn = 0.0
            for i in range(N_FOLDS):
                fs_m = C.TRAIN_MONTHS + i * FOLD_MONTHS
                a = t0 + pd.DateOffset(months=fs_m)
                s = fold_stats(fold_frame(df, fs_m), a, dict(n_sma=ns, n_roc=nr))
                pn += s["net"]
            combos.append((dict(n_sma=ns, n_roc=nr), pn))
            pos_n += int(pn > 0)
    nb_share = pos_n / len(combos)

    # ETH cross-check
    eth_net = 0.0
    t0e = dfe.index[0]
    for i in range(N_FOLDS):
        fs_m = C.TRAIN_MONTHS + i * FOLD_MONTHS
        a = t0e + pd.DateOffset(months=fs_m)
        eth_net += fold_stats(fold_frame(dfe, fs_m), a, PARAMS)["net"]

    gates = {
        "P1d pooled realized net-of-funding >0": net_pool > 0,
        f"P2d pooled closed trades >= {TRADE_FLOOR}": n_pool >= TRADE_FLOOR,
        "P3d mean fold Sharpe >0": mean_sh > 0,
        "P4d >=2/4 folds net-positive": folds_pos >= 2,
        "P5d >=60% of 9 neighbors net-positive": nb_share >= NEIGHBOR_SHARE,
        "P6d ETH pooled net >0": eth_net > 0,
        f"P7d residual <=25% of realized": un_share <= UNREAL_SHARE_MAX,
    }
    if all(gates.values()):
        verdict = "GAUNTLET-CERTIFIED"
    elif not gates["P1d pooled realized net-of-funding >0"]:
        verdict = "DEAD"
    else:
        verdict = "MARGINAL (failed: " + "; ".join(k for k, ok in gates.items() if not ok) + ")"

    md += [f"## H07 - frozen params n_sma={PARAMS['n_sma']}, n_roc={PARAMS['n_roc']} (from H00a)", "",
           f"Primary = deep test year, {N_FOLDS} x {FOLD_MONTHS}m folds. "
           f"{COMM * 10000:.0f}bp/side + {FUND_BPS_DAY * 10000:.0f}bp/day-in-market funding haircut. "
           f"{WARMUP_DAYS}d warmup lead; trades counted if entered in-window.", "",
           "| Fold | Realized $ | Funding drag $ | Net $ | Trades | Sharpe | Residual $ |",
           "|---|---|---|---|---|---|---|"]
    for i, f in enumerate(fold_rows, 1):
        md.append(f"| {i} | {f['realized']:+.2f} | {f['drag']:+.2f} | {f['net']:+.2f} "
                  f"| {f['n']} | {A.fmt(f['sh'])} | {f['residual']:+.2f} |")
    md += [f"- **Pool: realized {rea_pool:+.2f} -> net {net_pool:+.2f}; trades {n_pool}; "
           f"mean fold Sharpe {mean_sh:.2f}; folds-net-positive {folds_pos}/{N_FOLDS}; "
           f"residual share {un_share:.0%}**",
           f"- Neighbors: {pos_n}/{len(combos)} net-positive = {nb_share:.0%}",
           f"- ETH pool net: {eth_net:+.2f}",
           "**Gates:**"] + [f"- {k}: {'PASS' if ok else 'FAIL'}" for k, ok in gates.items()] \
          + [f"- **VERDICT: {verdict}**", ""]
    return verdict


def main():
    os.makedirs(OUT, exist_ok=True)
    md = ["# H07 REPORT - daily regime/momentum, H00a identity, FULL gauntlet", "",
          "Pre-registered gates in header. Frozen params (no re-optimization).",
          "Realized/unrealized split standing rule. Maker banned as bolt-on.", ""]
    verdict = gauntlet(md)
    path = os.path.join(OUT, "H07_report.md")
    open(path, "w", encoding="utf-8").write("\n".join(md))
    print(f"[H07] verdict: {verdict}")
    print(f"[H07] written: {path}")


if __name__ == "__main__":
    main()
