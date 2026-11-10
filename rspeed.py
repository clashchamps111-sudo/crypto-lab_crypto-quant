"""SESSION 8 OPENER - REGIME-SPEED CONFIRMATORY STUDY (pre-registered).

Question: does regime speed selected on calendar 2022-2024 transfer to the
2025-11-05 -> 2026-11-05 judge year (already spent once as the S6 test)?

CONFIRMATORY ONLY - declared in JOURNAL before this file exists. Nothing
certifies; the study feeds exactly one decision: keep the daily-bar alpha line
on the shelf (licensed for re-certification on a FUTURE fresh window) or shelve
it permanently (pivot condition completes -> carry line primary / park; user
ratifies which branch).

Method:
- Selection epoch: 2022-01-01 -> 2024-12-31, COMMON START 2022-06-01 for ALL
  combos (pre-2022 warmup banks cover n_sma<=200 fully by ~2022-05-25; holding
  every combo to the common start removes the warmup bias against slow filters).
  Trades counted only if EntryTime >= 2022-06-01. Costs: 7bp/side +
  3bp/day haircut, entry-notional convention (S6 standard).
- Candidates: 9 documented combos n_sma{100,150,200} x n_roc{20,30,50}
  (DailyMomentum identity), 10-symbol universe, pooled realized net.
- Selection: max pooled net; tie-break higher realized, then lexicographic.
- Confirmation: EXACT REPLAY of the S6 judge battery via universe_h07 imports
  (fold_daily / fold_net) - deterministic continuity with the S6 neighbor table.
- Gates (pre-registered):
  T1: selected combo judge pooled NET > 0
  T2: selected n_sma family: >=2/3 members judge-positive AND train family
      mean NET > 0
  T3: slow-family monotone decay visible on TRAIN (mirrors the S6 judge
      structure) - reported, advisory.
Verdict mapping: T1+T2 -> CONFIRMED (shelf license for future window);
else -> FAILS (pivot condition completes with H08 dead).
"""
import os

import pandas as pd

from backtesting import Backtest

import audit as A
import config as C
from strategies import DailyMomentum
from universe_h07 import fold_daily, fold_net, GRID9, UNIVERSE, COMM, FUND_BPS_DAY

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")

TRAIN_A = pd.Timestamp("2022-06-01")   # common start (declared); pre-epoch warmup bank
TRAIN_B = pd.Timestamp("2024-12-31")


def train_pooled(params):
    """Pooled realized NET over 2022-06-01 -> 2024-12-31, all 10 symbols.
    Slice loads from series t0 so the pre-epoch warmup bank is real (the
    journal's declared convention: every filter fully warm by ~2022-05-25
    BEFORE the common start); entries counted only if EntryTime >= TRAIN_A."""
    pool_real = pool_drag = 0.0
    legs = 0
    per_sym = {}
    for sym in UNIVERSE:
        df = A.daily_df(sym)
        w = df[df.index <= TRAIN_B + pd.Timedelta(days=1)]
        st = Backtest(w, type("RS", (DailyMomentum,), dict(params)),
                      cash=C.CASH, commission=COMM, exclusive_orders=True).run()
        t = st["_trades"]
        if len(t):
            tw = t[t["EntryTime"] >= TRAIN_A]
            if len(tw):
                real = float(tw["PnL"].sum())
                days = (tw["ExitBar"] - tw["EntryBar"]).astype(float)
                notional = tw["Size"].abs() * tw["EntryPrice"]
                drag = float((days * notional).sum()) * FUND_BPS_DAY
                legs += int(len(tw))
            else:
                real, drag = 0.0, 0.0
        else:
            real, drag = 0.0, 0.0
        per_sym[sym] = real - drag
        pool_real += real
        pool_drag += drag
    return dict(net=pool_real - pool_drag, realized=pool_real, drag=pool_drag,
                legs=legs, per_sym=per_sym)


def judge_replay(params):
    """Exact S6 judge replay (fold machinery import)."""
    net = real = 0.0
    legs = 0
    per_sym = {}
    for sym in UNIVERSE:
        s_net = s_real = 0.0
        s_legs = 0
        for a, _, w in fold_daily(sym):
            f = fold_net(w, a, params)
            s_net += f["net"]
            s_real += f["realized"]
            s_legs += f["n"]
        per_sym[sym] = s_net
        net += s_net
        real += s_real
        legs += s_legs
    return dict(net=net, realized=real, legs=legs, per_sym=per_sym)


def main():
    os.makedirs(OUT, exist_ok=True)
    md = ["# REGIME-SPEED CONFIRMATORY STUDY (Session 8, pre-registered)", "",
          "CONFIRMATORY ONLY: the judge year was already spent once (S6 test).",
          "Selection on calendar 2022-2024 (common start 2022-06-01 for all",
          "combos - warmup-bias control), confirmation = EXACT S6 judge replay.",
          "Nothing certifies here; output feeds the pre-registered pivot", "condition.", ""]
    print("[rspeed] selection epoch: 2022-06-01 -> 2024-12-31 (9 combos x 10 symbols)")
    train = {}
    for ns in GRID9["n_sma"]:
        for nr in GRID9["n_roc"]:
            params = dict(n_sma=ns, n_roc=nr)
            train[(ns, nr)] = train_pooled(params)
            print(f"[train] n_sma={ns:3d} n_roc={nr:2d} net {train[(ns, nr)]['net']:+8.2f} "
                  f"legs {train[(ns, nr)]['legs']:3d}")

    order = sorted(train, key=lambda c: (-train[c]["net"], -train[c]["realized"], c[1], c[0]))
    winner = dict(n_sma=order[0][0], n_roc=order[0][1])
    fam_train = {}
    for ns in GRID9["n_sma"]:
        fam_train[ns] = sum(train[c]["net"] for c in train if c[0] == ns) / 3
    # T3 advisory: monotone decay check (fast >= mid >= slow family means on train)
    dec = [fam_train[m] for m in (100, 150, 200)]
    t3 = dec[0] > dec[1] > dec[2]

    print(f"[rspeed] selected: {winner}")
    print("[rspeed] judge replay (S6-continuous fold machinery):")
    judge = judge_replay(winner)
    fam_judge = {ns: [] for ns in GRID9["n_sma"]}
    for ns in GRID9["n_sma"]:
        for nr in GRID9["n_roc"]:
            jf = judge_replay(dict(n_sma=ns, n_roc=nr))
            fam_judge[ns].append(jf)
    t1 = judge["net"] > 0
    t2 = (sum(1 for j in fam_judge[winner["n_sma"]] if j["net"] > 0) >= 2
          and fam_train[winner["n_sma"]] > 0)

    md += ["## Selection epoch (2022-06-01 -> 2024-12-31, pooled net)", "",
           "| n_sma | n_roc | Realized $ | Funding drag $ | NET $ | Legs |",
           "|---|---|---|---|---|---|"]
    for c in order:
        v = train[c]
        mark = " **<- selected**" if c == order[0] else ""
        md.append(f"| {c[0]} | {c[1]} | {v['realized']:+.2f} | "
                  f"{v['drag']:+.2f} | {v['net']:+.2f} | {v['legs']}{mark} |")
    md += ["- Train family means:",
           ", ".join(f"SMA({ns}): {fam_train[ns]:+.2f}" for ns in (100, 150, 200)),
           f"- T3 slow-decay on train: {dec[0]:+.2f} vs {dec[1]:+.2f} vs {dec[2]:+.2f} "
           f"-> {'MONOTONE (mirrors judge structure)' if t3 else 'NOT monotone'}", ""]

    md += [f"## Confirmation (judge replay, selected combo n_sma={winner['n_sma']}, "
           f"n_roc={winner['n_roc']})", "",
           f"- Judge pooled NET: {judge['net']:+.2f} across {judge['legs']} legs "
           "(absolute-calendar 4x3m folds, in-window entries - S6 machinery)",
           f"- Judge pooled realized: {judge['realized']:+.2f}", "",
           "| Family (n_sma) | Judge members net-positive | Family mean judge NET $ |",
           "|---|---|---|"]
    for ns in (100, 150, 200):
        js = fam_judge[ns]
        pos = sum(1 for j in js if j["net"] > 0)
        mean_net = sum(j["net"] for j in js) / len(js) if js else float("nan")
        md.append(f"| {ns} | {pos}/3 | {mean_net:+.2f} |")
    md += ["", "**Gates:**",
           f"- T1 selected combo judge NET > 0: {judge['net']:+.2f} -> "
           f"{'PASS' if t1 else 'FAIL'}",
           f"- T2 family property (train family mean {fam_train[winner['n_sma']]:+.2f} > 0, "
           f"judge members >=2/3 positive) -> {'PASS' if t2 else 'FAIL'}",
           f"- T3 (advisory) train slow-decay mirror -> "
           f"{'PATTERN PRESENT' if t3 else 'ABSENT'}", ""]

    if t1 and t2:
        verdict = ("TRANSFER CONFIRMED - fast-family basket stays on the shelf as the "
                   "standing daily-bar candidate; re-certification licensed ONLY on a "
                   "fresh future window (2026-11 -> 2027-11); nothing certified now; "
                   "attribution: S6 MARGINAL stability failure = slow-family drag, "
                   "speed is persistent structure.")
    else:
        verdict = ("TRANSFER FAILS - pivot condition COMPLETES (H08 dead + speed "
                   "selection does not transfer): daily-bar alpha line shelved "
                   "permanently; desk pivots to funding-carry (H09 gauntlet) or parks; "
                   "user ratifies branch at the report card.")
    md += [f"**STUDY VERDICT: {verdict}**", ""]
    path = os.path.join(OUT, "REGIME_SPEED_report.md")
    open(path, "w", encoding="utf-8").write("\n".join(md))
    print(f"[rspeed] verdict: {verdict}")
    print(f"[rspeed] written: {path}")


if __name__ == "__main__":
    main()
