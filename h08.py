"""H08 - CROSS-SECTIONAL MOMENTUM (10-symbol portfolio), pre-registered in JOURNAL.

Spec (JOURNAL, written before this file):
- Daily bars from 1h deep (audit.daily_df). Joined calendar = intersection of
  all 10 symbols (crypto trades ~every day -> joined index ~ calendar days).
- Signal: r-day rank return on the last daily bar of each ISO week (anchor).
- Execution: next joined day's open. Long-only, equal-weight 100/K targets;
  on membership change: exits sold fully, entrants bought at equity/K target
  from available cash, survivors untouched (declared reading of the journal's
  'no intra-membership re-weighing'); leftover cash stays idle.
- Costs: 7bp/side; funding haircut 3bp/day of ENTRY notional while held
  (consistent with the H07 convention).
- Train-opt grid r{30,60} x K{2,3} on months [0,48) (selection metric: money
  view = realized + open-forced-close, declared); judge year 2025-11-05 ->
  2026-11-04 ONCE with the frozen winner; folds 4x3m absolute-calendar for P3.
- VERDICT ACCOUNTING (standing rules): realized-only verdicts (closed in-window
  legs, net of haircut); unrealized/residual = M2M - realized reported; P4
  guards the |residual|/|realized| share. Sims for test/fold/LOO windows start
  with 150d warmup lead so M2M is anchored to the window (S6 accounting).
- Gates: P1 realized NET>0; P2 >=20 closed legs; P3 >=2/4 folds net+;
  P4 |residual|<=25% |realized|; P5 realized NET > equal-weight 10-coin B&H
  net (B&H pays NO funding haircut - spot passive - conservative for us);
  P6 stability: N1 (>=3/4 of the 4 grid combos net+ on test year), N2 (all 10
  LOO pools realized net+), N3 (realized NET>0 at 10bp/side), N4 (best symbol
  <=60% of pool realized).
ALL -> CERTIFIED; P1 fail -> DEAD; else MARGINAL. One pass, no re-opt.
"""
import os

import numpy as np
import pandas as pd

import audit as A
import config as C

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")

UNIVERSE = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
            "DOGEUSDT", "ADAUSDT", "LINKUSDT", "AVAXUSDT", "TRXUSDT"]
COMM = 0.0007
FUND_BPS_DAY = 0.0003
GRID = [(r, k) for r in (30, 60) for k in (2, 3)]  # 4 combos (<16 rule)
FOLD_T0 = pd.Timestamp("2025-11-05")
FOLD_MONTHS = 3
N_FOLDS = 4
WARMUP = 150
TRADE_FLOOR = 20
UNREAL_MAX = 0.25
ATTR_CAP = 0.60

# ---------------- data layer (cached) ----------------
_CACHE = {}


def load_universe(sym_filter=None):
    key = tuple(sym_filter) if sym_filter is not None else None
    if key in _CACHE:
        return _CACHE[key]
    syms = [s for s in UNIVERSE if sym_filter is None or s in sym_filter]
    frames = {s: A.daily_df(s) for s in syms}
    idx = None
    for s in syms:
        i = frames[s].index
        idx = i if idx is None else idx.intersection(i)
    idx = idx.sort_values()
    joined = {s: frames[s].reindex(idx) for s in syms}
    _CACHE[key] = (syms, joined, idx)
    return _CACHE[key]


def slice_frames(joined, idx, a, warm=WARMUP, b=None):
    """[a - warm, b) window slice honoring the S6 warmup rule."""
    a_i = int(idx.searchsorted(a - pd.Timedelta(days=warm)))
    b_i = len(idx) if b is None else int(idx.searchsorted(b))
    sub_idx = idx[a_i:b_i]
    return {s: joined[s].iloc[a_i:b_i].copy() for s in joined}, sub_idx


# ---------------- portfolio engine ----------------
def _sim(r, k, joined, idx, sym_titles=None, comm=COMM):
    """One warmup->window portfolio run. Returns legs (closed), realized,
    m2m, open_realized (open@last close forced-close, informational), per_sym."""
    syms = [s for s in (sym_titles or UNIVERSE) if s in joined]
    closes = pd.DataFrame({s: joined[s]["Close"] for s in syms})
    opens = pd.DataFrame({s: joined[s]["Open"] for s in syms})
    dlist = list(idx)
    weeks = [(d.isocalendar()[0], d.isocalendar()[1]) for d in dlist]
    anchors = {i for i in range(len(dlist) - 1) if weeks[i] != weeks[i + 1]}

    cash = C.CASH
    pos = {}
    legs = []
    m2m = 0.0
    for i in range(WARMUP, len(dlist)):
        d = dlist[i]
        ai = i - 1
        if ai in anchors and i >= r + 1:
            ca = {s: float(closes[s].iloc[ai]) for s in syms}
            hist_ok = [s for s in syms
                       if np.isfinite(ca[s]) and np.isfinite(float(closes[s].iloc[ai - r]))
                       and float(closes[s].iloc[ai - r]) > 0]
            if len(hist_ok) >= k:
                mom = {s: ca[s] / float(closes[s].iloc[ai - r]) - 1 for s in hist_ok}
                topk = sorted(mom, key=mom.get, reverse=True)[:k]
                current = set(pos)
                for s in sorted(current - set(topk)):
                    p = pos.pop(s)
                    px = float(opens[s].iloc[i])
                    gross = p["units"] * px
                    fee = gross * comm
                    days = i - p["entry_i"]
                    haircut = p["entry_notional"] * FUND_BPS_DAY * days
                    legs.append(dict(sym=s, entry_date=p["entry_date"], exit_date=d,
                                     entry_notional=p["entry_notional"],
                                     fees=p["buy_fee"] + fee, haircut=haircut,
                                     realized=gross - fee - haircut - p["cost_basis"]))
                    cash += gross - fee
                mv = 0.0
                for s, p in pos.items():
                    c = ca.get(s, np.nan)
                    mv += p["units"] * (c if np.isfinite(c) else p["entry_px"])
                    # survivor marks use the anchor close (decision-time equity);
                    # survivor notional deliberately NOT trimmed (declared)
                total_eq = cash + mv
                target = total_eq / k
                for s in sorted(set(topk) - current):
                    if cash <= 1e-9:
                        break
                    px = float(opens[s].iloc[i])
                    if not np.isfinite(px) or px <= 0:
                        continue
                    spend = min(target, cash)
                    fee = spend * comm
                    units = (spend - fee) / px
                    entry_notional = spend - fee
                    cash -= spend
                    pos[s] = dict(units=units, entry_px=px,
                                  entry_notional=entry_notional, entry_i=i,
                                  buy_fee=fee, cost_basis=entry_notional,
                                  entry_date=d)
        mv = 0.0
        for s, p in pos.items():
            c = float(closes[s].iloc[i])
            if np.isnan(c):
                c = p["entry_px"]
            mv += p["units"] * c
        m2m = cash + mv - C.CASH

    fi = len(dlist) - 1
    open_realized = 0.0
    n_open = 0
    for s, p in pos.items():
        px = float(closes[s].iloc[fi])
        gross = p["units"] * px
        fee = gross * comm
        days = fi - p["entry_i"]
        haircut = p["entry_notional"] * FUND_BPS_DAY * days
        open_realized += gross - fee - haircut - p["cost_basis"]
        n_open += 1
    realized = float(sum(l["realized"] for l in legs))
    per_sym = {}
    for l in legs:
        per_sym[l["sym"]] = per_sym.get(l["sym"], 0.0) + l["realized"]
    return dict(legs=legs, realized=realized, m2m=m2m,
                open_realized=open_realized, n_open=n_open, per_sym=per_sym)


def window_net(res, a):
    """In-window-entry legs only; realized-only + realized-only money splits."""
    lw = [l for l in res["legs"] if l["entry_date"] >= a]
    realized = float(sum(l["realized"] for l in lw))
    unreal = res["m2m"] - realized
    psym = {}
    for l in lw:
        psym[l["sym"]] = psym.get(l["sym"], 0.0) + l["realized"]
    return dict(realized=realized, unreal=unreal, legs=lw, n=len(lw), per_sym=psym)


def bh_net(frames, a, b, comm=COMM):
    """Equal-weight 10-coin B&H over [a,b), net of one 7bp round trip on book."""
    rets = []
    for s, df in frames.items():
        px = df["Close"].loc[a:b]
        if len(px) < 2:
            continue
        rets.append(float(px.iloc[-1] / px.iloc[0] - 1))
    if not rets:
        return float("nan")
    return (float(np.mean(rets)) - 2 * comm) * 100


def main():
    os.makedirs(OUT, exist_ok=True)
    md = ["# H08 REPORT - cross-sectional momentum portfolio", "",
          "Pre-registered in JOURNAL BEFORE build (gates P1-P6, N1-N4).",
          "r-day momentum rank, top-K equal weight, weekly anchors, next-open",
          "execution, 7bp/side + 3bp/day haircut. One judge pass.", ""]
    syms_full, joined_full, idx_full = load_universe(None)
    t0 = idx_full[0]
    test_start = FOLD_T0
    test_end = test_start + pd.DateOffset(months=C.TEST_MONTHS)
    train_end = t0 + pd.DateOffset(months=C.TRAIN_MONTHS)

    # ---- TRAIN: months [0, 48m) - sim runs from t0, slice at train_end
    tr_joined, tr_idx = slice_frames(joined_full, idx_full, t0, warm=0, b=train_end)
    # NOTE warm=0: slice starts at t0, engine applies WARMUP internally
    train_res = {}
    for r, k in GRID:
        res = _sim(r, k, tr_joined, tr_idx, syms_full, COMM)
        net = res["realized"] + res["open_realized"]  # money view (declared)
        train_res[(r, k)] = dict(res=res, net=net, legs=len(res["legs"]))
        print(f"[train] r={r:2d} K={k}: realized {res['realized']:+7.2f} "
              f"open {res['open_realized']:+7.2f} net {net:+7.2f} legs {len(res['legs'])}")
    winner = max(train_res, key=lambda c: train_res[c]["net"])
    r, k = winner
    md += ["## Train (48m) - grid selection (money view, declared)", "",
           "| r | K | Realized $ | Open@cutoff $ | NET $ | Closed legs |",
           "|---|---|---|---|---|---|"]
    for (rr, kk), v in train_res.items():
        md.append(f"| {rr} | {kk} | {v['res']['realized']:+.2f} | "
                  f"{v['res']['open_realized']:+.2f} | {v['net']:+.2f} | {v['legs']} |")
    md += [f"- **Frozen winner: r={r}, K={k} (max train NET)**", ""]

    # ---- TEST YEAR single continuous judge (window-anchored accounting)
    te_frames, te_idx = slice_frames(joined_full, idx_full, test_start, WARMUP, test_end)
    res = _sim(r, k, te_frames, te_idx, syms_full, COMM)
    w = window_net(res, test_start)
    realized, unreal = w["realized"], w["unreal"]
    n_legs = w["n"]
    p1 = realized > 0
    p2 = n_legs >= TRADE_FLOOR
    unreal_share = abs(unreal) / max(abs(realized), 1e-9)
    p4 = unreal_share <= UNREAL_MAX
    best_sym = max(w["per_sym"].values()) if w["per_sym"] else 0.0
    n4_ok = realized > 0 and best_sym <= ATTR_CAP * abs(realized)
    md += [f"## Test year {test_start.date()} -> {test_end.date()} "
           f"(frozen r={r}, K={k})", "",
           f"- Closed in-window legs: {n_legs} | realized ${realized:+.2f} "
           f"(net of fees + haircut)",
           f"- Continuous-run M2M: {res['m2m']:+.2f} | residual/unrealized ${unreal:+.2f} "
           f"({unreal_share:.0%} of realized) | open@cutoff {res['n_open']} names "
           f"(forced-close value {res['open_realized']:+.2f}, informational)",
           f"- **P1 realized NET: {realized:+.2f} on $100**", ""]
    md += ["| Symbol | Realized $ |", "|---|---|"]
    for s, v in sorted(w["per_sym"].items(), key=lambda kv: -kv[1]):
        md.append(f"| {s} | {v:+.2f} |")
    md += [""]

    # ---- folds for P3 (each fold: [a-150d, b) fresh cash=100 sim)
    fold_rows, fold_pos = [], 0
    pool_r = pool_u = 0.0
    for i in range(N_FOLDS):
        a2 = test_start + pd.DateOffset(months=i * FOLD_MONTHS)
        b2 = test_start + pd.DateOffset(months=(i + 1) * FOLD_MONTHS)
        f_frames, f_idx = slice_frames(joined_full, idx_full, a2, WARMUP, b2)
        rf = _sim(r, k, f_frames, f_idx, syms_full, COMM)
        wf = window_net(rf, a2)
        fold_rows.append((i, wf["realized"], wf["unreal"], wf["n"]))
        pool_r += wf["realized"]
        pool_u += wf["unreal"]
        fold_pos += int(wf["realized"] > 0)
    p3 = fold_pos >= 2
    md += [f"## Folds (4x{FOLD_MONTHS}m absolute-calendar, 150d warmup, "
           "in-window entries)", "",
           "| Fold | Realized $ | Unreal $ | Legs |", "|---|---|---|---|"]
    for i, lr, ru, nl in fold_rows:
        md.append(f"| {i + 1} | {lr:+.2f} | {ru:+.2f} | {nl} |")
    md += [f"- Pool realized {pool_r:+.2f}, unreal {pool_u:+.2f}, "
           f"folds-positive {fold_pos}/{N_FOLDS}", ""]

    # ---- P5 benchmark
    bhn = bh_net(joined_full, test_start, test_end)
    p5 = realized > bhn

    # ---- N1: 4-combo neighborhood on the test year
    nb = {}
    for (rr, kk) in GRID:
        if (rr, kk) == winner:
            continue
        rn = _sim(rr, kk, te_frames, te_idx, syms_full, COMM)
        wn = window_net(rn, test_start)
        nb[(rr, kk)] = wn["realized"]
    others_pos = sum(1 for v in nb.values() if v > 0)
    n1_ok = others_pos >= 2  # winner + 2/3 others => >=3/4 of 4
    md += ["## Stability battery", "",
           "| Non-winner combo | Test realized $ |", "|---|---|"]
    for c, v in nb.items():
        md.append(f"| r={c[0]} K={c[1]} | {v:+.2f} |")

    # ---- N2: leave-one-out x 10 (winner combo, window-anchored)
    loo_rows, loo_pos = [], 0
    for s in UNIVERSE:
        keep = [x for x in UNIVERSE if x != s]
        _, j2, ix2 = load_universe(keep)
        lf_frames, lf_idx = slice_frames(j2, ix2, test_start, WARMUP, test_end)
        rs = _sim(r, k, lf_frames, lf_idx, keep, COMM)
        ws2 = window_net(rs, test_start)
        loo_rows.append((s, ws2["realized"]))
        loo_pos += int(ws2["realized"] > 0)
    n2_ok = loo_pos == len(UNIVERSE)
    md += ["| LOO excluded | Test realized $ |", "|---|---|"]
    for s, v in loo_rows:
        md.append(f"| {s} | {v:+.2f} |")

    # ---- N3: double cost
    rc = _sim(r, k, te_frames, te_idx, syms_full, 0.0010)
    net_10bp = window_net(rc, test_start)["realized"]
    n3_ok = net_10bp > 0

    md += [f"- N1 neighborhood: {others_pos}/3 non-winner combos positive "
           f"(winner + >=2 => >=3/4) -> {'PASS' if n1_ok else 'FAIL'}",
           f"- N2 leave-one-out: {loo_pos}/10 pools realized-positive "
           f"-> {'PASS' if n2_ok else 'FAIL'}",
           f"- N3 double-cost 10bp/side: realized {net_10bp:+.2f} "
           f"-> {'PASS' if n3_ok else 'FAIL'}",
           f"- N4 attribution: best symbol {best_sym:+.2f} = "
           f"{best_sym / max(abs(realized), 1e-9):.0%} of realized -> "
           f"{'PASS' if n4_ok else 'FAIL'}",
           f"- P5 benchmark: realized {realized:+.2f} vs B&H-net {bhn:+.2f} "
           f"-> {'PASS' if p5 else 'FAIL'}", ""]

    gates = {
        "P1 test-year realized NET > 0": p1,
        f"P2 closed legs >= {TRADE_FLOOR}": p2,
        "P3 >= 2/4 folds realized-positive": p3,
        "P4 |residual| <= 25% of realized": p4,
        "P5 realized NET > equal-weight B&H net": p5,
        "P6-N1 neighborhood >= 3/4 positive": n1_ok,
        "P6-N2 all 10 LOO pools positive": n2_ok,
        "P6-N3 NET > 0 at 10bp/side": n3_ok,
        "P6-N4 best symbol <= 60% realized": n4_ok,
    }
    if all(gates.values()):
        verdict = "GAUNTLET-CERTIFIED"
    elif not p1:
        verdict = "DEAD"
    else:
        verdict = "MARGINAL (failed: " + "; ".join(kk for kk, ok in gates.items() if not ok) + ")"
    md += ["**Gates:**"] + [f"- {kk}: {'PASS' if ok else 'FAIL'}" for kk, ok in gates.items()] \
        + [f"**VERDICT: {verdict}**", ""]
    path = os.path.join(OUT, "H08_report.md")
    open(path, "w", encoding="utf-8").write("\n".join(md))
    print(f"[H08] winner: r={r} K={k}")
    print(f"[H08] test realized {realized:+.2f} legs {n_legs} unreal {unreal:+.2f} "
          f"B&H-net {bhn:+.2f}")
    print(f"[H08] verdict: {verdict}")
    print(f"[H08] written: {path}")


if __name__ == "__main__":
    main()
