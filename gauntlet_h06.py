"""H06 GAUNTLET - pre-registered battery for the two maker candidates.
Pre-registered gates (before any run; also frozen in JOURNAL.md Session 4):

PRIMARY OOS = deep test year (Nov25->Nov26) sliced 4 x 3m folds. Gates:
  P1 pooled primary REALIZED $ > 0
  P2 pooled primary CLOSED trades >= 20
  P3 mean primary-fold Sharpe > 0
  P4 >= 3 of 4 primary folds realized-positive
  P5 >= 60% of 27 neighbor param sets (fill_wait added as mechanism param)
     pooled-realized-positive at 2bp
  P6 ETHUSDT (frozen params) pooled realized > 0
  P7 |unrealized open@cutoff| <= 25% of |realized| (realized/unrealized split
     rule from the audit charter)
Verdicts: ALL P1..P7 -> GAUNTLET-CERTIFIED (testnet is next step).
P1 fails -> DEAD (maker thesis dead for this signal). Partial -> MARGINAL,
listing failed gates. NO metric besides these gates flips anything.

SECONDARY (PEEK-flagged, advisory): same folds over months 36-48 of the deep
series (inside the train window -> params saw that data once; measures
mechanism stability, NOT fresh alpha). Labeled PEEK in every table.

COST BRACKETS: 2bp/side = official (the audit's maker-flip criterion).
4.5bp/side = honest blended floor gates re-run for the winner (entries maker,
exits time/regime/SL takers in reality). Both reported; certification needs
P1-P7 at 2bp AND P1',P3' alive at 4.5bp (blended) for the strong stamp.
"""
import os

from itertools import product

import numpy as np
import pandas as pd

from backtesting import Backtest

import config as C
import audit as A
from strategies import DonchianMaker, MakerShortPullback

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")

# Winner params from the audit cost matrix - FROZEN, no re-optimization.
VARIANTS = {
    "H06a_DonchianMaker": dict(cls=DonchianMaker, tf="1h", suf="_deep",
                               params=dict(n_enter=20, n_exit=10, atr_stop=3.0),
                               neighbors=dict(n_enter=[15, 20, 25], n_exit=[7, 10, 13],
                                              fill_wait=[1, 2, 3])),
    "H06b_MakerShortPullback": dict(cls=MakerShortPullback, tf="1h", suf="_deep",
                                    params=dict(n_fast=9, atr_stop=2.5, use_vwap=True),
                                    neighbors=dict(n_fast=[7, 9, 11], atr_stop=[2.0, 2.5, 3.0],
                                                   fill_wait=[1, 2, 3])),
}

BP = dict(official=0.0002, blended=0.00045)
FOLD_MONTHS = 3
N_PRIMARY = 4      # test year => 4 folds
N_PEEK = 4         # last 4 quarters of the train window (PEEK)
GATE_POS_NEIGHBORS = 0.60
GATE_UNREAL_SHARE = 0.25


def load(sym):
    return A.load(sym, "1h", "_deep")


def fold_windows(df, start_month, n_folds):
    """(train_end_mos, i) -> [start, end) windows; start_month = offset months
    from the series start where folds begin; each fold = FOLD_MONTHS long."""
    t0 = df.index[0]
    out = []
    for i in range(n_folds):
        a = t0 + pd.DateOffset(months=start_month + i * FOLD_MONTHS)
        b = t0 + pd.DateOffset(months=start_month + (i + 1) * FOLD_MONTHS)
        w = df[(df.index >= a) & (df.index < b)]
        if len(w):
            out.append((i, w))
    return out


def run_fold(cls, params, window, comm, tag_cls):
    p = dict(params)
    if p.get("use_vwap"):
        w = window.copy()
        w["VWAP"] = A.vwap_daily(w)
        p["_vwap"] = w["VWAP"].to_numpy()
    cls2 = type(f"{tag_cls}_{int(comm * 10000)}bp", (cls,), p)
    st = Backtest(window, cls2, cash=C.CASH, commission=comm, exclusive_orders=True).run()
    t = st["_trades"]
    realized = float(t["PnL"].sum()) if len(t) else 0.0
    try:
        final = float(st["_equity_curve"]["Equity"].iloc[-1])
    except Exception:
        final = C.CASH
    unreal = final - C.CASH - realized
    trades = int(len(t))
    sharpe = A.num(st.get("Sharpe Ratio", np.nan))
    return dict(realized=realized, unreal=unreal, trades=trades, sharpe=sharpe)


def pool(fold_stats):
    r = [f["realized"] for f in fold_stats]
    pos = sum(1 for x in r if x > 0)
    sh = [A.num(f["sharpe"]) for f in fold_stats if np.isfinite(A.num(f["sharpe"]))]
    return dict(realized=float(sum(r)), unreal=float(sum(f["unreal"] for f in fold_stats)),
                trades=int(sum(f["trades"] for f in fold_stats)), folds_pos=pos,
                folds_n=len(r), mean_sharpe=float(np.mean(sh)) if sh else float("nan"))


def gauntlet_variant(name, v, md):
    cls, tf, suf, params = v["cls"], v["tf"], v["suf"], v["params"]
    nb_grid = v["neighbors"]
    tag_cls = name.split("_")[0]
    df = load("BTCUSDT")
    df_eth = load("ETHUSDT")
    test_start = C.TRAIN_MONTHS
    peek_start = C.TRAIN_MONTHS - N_PEEK * FOLD_MONTHS

    # ---- primary: winner params, 4 folds, 2bp official
    ov = BP["official"]
    folds = fold_windows(df, test_start, N_PRIMARY)
    fs = [run_fold(cls, {**params}, w, ov, f"{tag_cls}f{i}") for i, (_, w) in enumerate(folds)]
    p = pool(fs)

    # ---- neighbors (2bp, primary folds)
    combos = list(product(*nb_grid.values()))
    nb_pos = 0
    for combo in combos:
        pars = {**params, **dict(zip(nb_grid.keys(), combo))}
        nb_fs = [run_fold(cls, pars, w, ov, f"{tag_cls}nb") for _, w in folds]
        nb_pool = pool(nb_fs)
        nb_pos += int(nb_pool["realized"] > 0)
    nb_share = nb_pos / len(combos)

    # ---- ETH cross-check (winner, 2bp, primary folds)
    eth_fs = [run_fold(cls, {**params}, w, ov, f"{tag_cls}eth") for _, w in
              fold_windows(df_eth, test_start, N_PRIMARY)]
    eth_p = pool(eth_fs)

    # ---- PEEK folds (2bp, winner)
    pk_fs = [run_fold(cls, {**params}, w, ov, f"{tag_cls}pk") for _, w in
             fold_windows(df, peek_start, N_PEEK)]
    pk_p = pool(pk_fs)

    # ---- blended-cost bracket (4.5bp): winner primary + PEEK + ETH
    bv = BP["blended"]
    b_fs = [run_fold(cls, {**params}, w, bv, f"{tag_cls}b") for _, w in folds]
    b_p = pool(b_fs)

    # ---- gates
    unreal_share = (abs(p["unreal"]) / abs(p["realized"])) if p["realized"] else float("inf")
    gates = {
        "P1 pooled realized>0": p["realized"] > 0,
        "P2 pooled closed trades>=20": p["trades"] >= 20,
        "P3 mean fold Sharpe>0": p["mean_sharpe"] > 0,
        "P4 >=3/4 folds positive": p["folds_pos"] >= 3,
        f"P5 neighbors>=60% positive": nb_share >= GATE_POS_NEIGHBORS,
        "P6 ETH pooled realized>0": eth_p["realized"] > 0,
        f"P7 unreal <=25% of realized": unreal_share <= GATE_UNREAL_SHARE,
    }
    n_pass = sum(gates.values())
    if all(gates.values()):
        verdict = "GAUNTLET-CERTIFIED" if b_p["realized"] > 0 and b_p["mean_sharpe"] > 0 else "CERTIFIED @2bp (blended fails)"
    elif not gates["P1 pooled realized>0"]:
        verdict = "DEAD"
    else:
        failed = [k for k, ok in gates.items() if not ok]
        verdict = f"MARGINAL (failed: {'; '.join(failed)})"

    md += [f"## {name} (params frozen: {', '.join(f'{k}={val:g}' if isinstance(val, (int, float)) else f'{k}={val}' for k, val in params.items())})", "",
           f"Primary = deep test year, 4 x {FOLD_MONTHS}m folds. Official cost {ov * 10000:.1f}bp/side.", "",
           "| Fold | Realized $ | Unreal $ | Trades | Sharpe |", "|---|---|---|---|---|"]
    for (i, w), f in zip(folds, fs):
        md.append(f"| {i + 1} | {f['realized']:+.2f} | {f['unreal']:+.2f} | {f['trades']} | {A.fmt(f['sharpe'])} |")
    md += ["", f"- **Primary pool: realized {p['realized']:+.2f}, trades {p['trades']}, "
           f"mean fold Sharpe {A.fmt(p['mean_sharpe'])}, folds-positive {p['folds_pos']}/{p['folds_n']}**",
           f"- Unrealized/open@cutoff: {p['unreal']:+.2f} (share {unreal_share:.0%} of realized)",
           f"- Neighbors positive: {nb_pos}/{len(combos)} = {nb_share:.0%}",
           f"- ETH pool: realized {eth_p['realized']:+.2f}, trades {eth_p['trades']}, "
           f"mean fold Sharpe {A.fmt(eth_p['mean_sharpe'])}",
           f"- PEEK pool ({N_PEEK} folds, months {peek_start}-{C.TRAIN_MONTHS}): "
           f"realized {pk_p['realized']:+.2f}, trades {pk_p['trades']}, "
           f"mean fold Sharpe {A.fmt(pk_p['mean_sharpe'])}",
           f"- Blended bracket ({bv * 10000:.1f}bp/side) primary: realized {b_p['realized']:+.2f}, "
           f"trades {b_p['trades']}, mean fold Sharpe {A.fmt(b_p['mean_sharpe'])}, "
           f"folds-positive {b_p['folds_pos']}/{b_p['folds_n']}", "",
           "**Gates:**"] + [f"- {k}: {'PASS' if ok else 'FAIL'}" for k, ok in gates.items()] \
          + [f"- **VERDICT: {verdict}**", ""]
    return verdict


def main():
    os.makedirs(OUT, exist_ok=True)
    md = ["# H06 GAUNTLET - maker-execution layer on both audit-flipped candidates", "",
          "Pre-registered gates P1-P7 (see file header + JOURNAL). Signals frozen from",
          "audit; no re-optimization; fill_wait is the only new parameter and it is",
          "treated as a mechanism knob inside the neighbor grid.", ""]
    verdicts = {}
    for name, v in VARIANTS.items():
        print(f"===== {name} =====")
        verdicts[name] = gauntlet_variant(name, v, md)
        print(f"[{name}] -> {verdicts[name]}")
    md += ["## Session verdict summary", "",
           "| Variant | Verdict |", "|---|---|"] + \
          [f"| {n} | {verdicts[n]} |" for n in verdicts]
    path = os.path.join(OUT, "H06_gauntlet.md")
    open(path, "w", encoding="utf-8").write("\n".join(md))
    print(f"[gauntlet] written: {path}")


if __name__ == "__main__":
    main()
