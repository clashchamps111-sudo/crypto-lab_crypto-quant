"""SESSION 10.6 - P1: E3 FUNDING-ROTATION HARVEST (pre-registered).

Idea: direct carry sleeves at the coins with the richest TRAILING funding.
Selection layer on top of per-coin gated execution (S6 frozen rule) and a
"selected-always" comparator. All data in hand (10 x 5y funding prints).

PRE-REGISTERED (verbatim, before any run):
- Universe: the 10-coin funding breadth set (E2 data, 2021-11-06 ->
  2026-11-09, ~5,490 prints each, aligned on the outer-join timeline).
- Grid (16 combos, ALL registered at once, all reported): K in {3,5},
  lookback in {90 prints (30d), 180 prints (60d)}, rebalance in {weekly,
  monthly}, execution in {gated, selected_always}. PRIMARY family =
  gated rows; selected_always rows are comparators.
- Selection rule: at each rebalance boundary, candidate pool = coins whose
  trailing-mean funding (lookback, skipna) is FINITE and > 0; rank pool by
  trailing mean DESC; top K become the selected set for the segment. Pool
  smaller than K -> fewer sleeves (no forced negative-funding holds: a
  carry sleeve long-spot/short-perp PAYS while funding is negative).
- Gated execution (primary): within selected set, per-coin S6 frozen rule
  on trail-3 print mean: enter when > +1bp, exit when < -1bp; plus forced
  exit at segment boundary if the coin drops out of the selected set.
- Selected_always (comparator): hold while selected AND trailing lookback
  > 0 at every print; forced exit at boundary drop or trailing <= 0.
- ACCRUAL / FEES (conservative, desk lineage): entry print NOT earned
  (hold starts after the entry settlement); exit print NOT earned (exit
  closes before its settlement); boundary-drop exits likewise skip the
  boundary print. Fees: 30bp RT per open->close cycle; forced rotation
  closes count as trips. Turnover = cycles/yr.
- Baselines computed here under IDENTICAL conventions: static equal-weight
  gated blend (K=10 pool rule) and static selected_always.
- VERDICT (pre-registered): rotation VALIDATED iff best GATED combo beats
  the static gated baseline by >= +0.5pp/yr notional AND funding-only
  stream MDD (per $100 notional) >= -1.0%. Else rotation closed as
  complexity-without-benefit and the static blend stays the deliverable.
- Reporting: all 16 combos; four-bar table (BAR-A/B/C/D) for best gated
  combo AND static baseline; winner per-year buckets; net share by coin.
"""
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
DIR = os.path.join(ROOT, "data", "funding_breadth")
COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
         "DOGEUSDT", "ADAUSDT", "LINKUSDT", "AVAXUSDT", "TRXUSDT"]
FEE_RT = 0.003
ENTER = 0.0001          # trail-3 > +1bp
EXIT = -0.0001          # trail-3 < -1bp
MARGIN_PP = 0.5
MDD_FLOOR = -1.0


def load_wide():
    frames = {}
    for s in COINS:
        d = pd.read_csv(os.path.join(DIR, f"usdt_{s}.csv"),
                        parse_dates=["fundingTime"]).sort_values("fundingTime")
        frames[s] = d.set_index("fundingTime")["r"]
    return pd.DataFrame(frames).sort_index()


def sweep(wide, k, lookback, cad, exec_mode):
    idx = wide.index
    R = np.nan_to_num(wide.to_numpy(), nan=0.0)
    n, nc = R.shape
    trail = wide.rolling(lookback, min_periods=max(2, lookback // 2)) \
        .mean().to_numpy()
    trail3 = wide.rolling(3, min_periods=3).mean().to_numpy()
    labels = (np.asarray((idx - idx[0]) // pd.Timedelta(days=7),
                         dtype=np.int64) if cad == "W" else
              np.asarray(idx.to_period("M").astype(np.int64)))
    starts = np.flatnonzero(np.r_[True, labels[1:] != labels[:-1]])
    start_set = set(starts.tolist())

    pos = np.zeros(nc, dtype=bool)
    sel = np.zeros(nc, dtype=bool)
    earned = np.zeros(nc)
    trips = 0
    swaps = 0
    stream = np.zeros(n)
    winner_periods = []

    for i in range(n):
        if i in start_set:
            tr = trail[i]
            pool = [c for c in range(nc) if np.isfinite(tr[c]) and tr[c] > 0]
            pool.sort(key=lambda c: -tr[c])
            sel = np.zeros(nc, dtype=bool)
            for c in pool[:k]:
                sel[c] = True
            dropped = np.flatnonzero(pos & ~sel)
            if len(dropped):
                pos[dropped] = False          # boundary exit BEFORE settlement
                trips += len(dropped)
                swaps += len(dropped)
        if exec_mode == "gated":
            ex = np.flatnonzero(pos & np.isfinite(trail3[i]) &
                                (trail3[i] < EXIT))
        else:
            ex = np.flatnonzero(pos & ((~np.isfinite(trail[i])) |
                                       (trail[i] <= 0)))
        if len(ex):
            pos[ex] = False                   # gate exit BEFORE settlement
            trips += len(ex)
        stream[i] = R[i][pos].sum()
        earned += np.where(pos, R[i], 0.0)
        if exec_mode == "gated":
            can = sel & ~pos & np.isfinite(trail3[i]) & (trail3[i] > ENTER)
        else:
            can = sel & ~pos & np.isfinite(trail[i]) & (trail[i] > 0)
        pos |= can

    years = (idx[-1] - idx[0]).total_seconds() / (365.25 * 86400)
    # DENOMINATOR FIX (per $100 BOOK notional): each open sleeve carries
    # book/K weight; fees likewise 30bp of sleeve notional per cycle.
    wgt = 1.0 / k
    fund_book = earned.sum() * 100 * wgt
    net_book = fund_book - trips * FEE_RT * 100 * wgt
    cum = stream.cumsum() * 100 * wgt
    peak = np.maximum.accumulate(cum)
    mdd = float((cum - peak).min())
    share = pd.Series(earned, index=wide.columns)
    share = share / max(share.sum(), 1e-12)
    return dict(net=float(net_book), fund=float(fund_book), years=years,
                ann=float(net_book) / years, trips=int(trips),
                turnover=float(trips) / years, mdd=mdd, share=share,
                stream=stream, cad=cad, k=k, lookback=lookback,
                exec_mode=exec_mode, swaps=swaps)


def yearly_stream(idx, stream):
    s = pd.DataFrame({"y": idx.year, "v": stream.cumsum() * 100})
    yearly = s.groupby("y")["v"].last().diff()
    first = s.groupby("y")["v"].first()
    yearly.iloc[0] = first.iloc[0]
    return yearly


def main():
    os.makedirs(OUT, exist_ok=True)
    wide = load_wide()
    idx = wide.index
    md = ["# E3 FUNDING-ROTATION HARVEST (Session 10.6, pre-registered)", "",
          "Selection = richest trailing funding coins each rebalance;",
          "S6 frozen per-coin gates (primary) or selected-always comparator;",
          "conservative accrual (entry/exit/boundary prints not earned);",
          "30bp RT per cycle; funding-only stream MDD; 16 combos at once,",
          "gated family = primary. Baselines re-run under identical",
          "conventions (K=10). UNIT OF RECORD: per $100 BOOK notional -",
          "each open sleeve carries book/K weight (E2 blend comparable).", "",
          "| K | lookback | reb | exec | net % | net %/yr | trips | cycl/yr | swap/yr | MDD % |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    static_g = sweep(wide, k=10, lookback=90, cad="W", exec_mode="gated")
    static_a = sweep(wide, k=10, lookback=90, cad="W",
                     exec_mode="selected_always")
    md += ["| 10 | n/a | n/a | gated STATIC BASELINE | "
           f"{static_g['net']:+.2f} | {static_g['ann']:+.2f} | "
           f"{static_g['trips']} | {static_g['turnover']:.1f} | - | "
           f"{static_g['mdd']:+.2f} |",
           "| 10 | n/a | n/a | selected_always STATIC | "
           f"{static_a['net']:+.2f} | {static_a['ann']:+.2f} | "
           f"{static_a['trips']} | {static_a['turnover']:.1f} | - | "
           f"{static_a['mdd']:+.2f} |"]
    print(f"[baseline] gated-static {static_g['ann']:+.2f}%/yr | "
          f"always-static {static_a['ann']:+.2f}%/yr")
    rows = []
    for exec_mode in ("gated", "selected_always"):
        for cad in ("W", "M"):
            for lookback in (90, 180):
                for k in (3, 5):
                    r = sweep(wide, k, lookback, cad, exec_mode)
                    rows.append(r)
                    md.append(f"| {r['k']} | {r['lookback']}p | {r['cad']} | "
                              f"{'gated' if r['exec_mode'] == 'gated' else 'always'} | "
                              f"{r['net']:+.2f} | {r['ann']:+.2f} | "
                              f"{r['trips']} | {r['turnover']:.1f} | "
                              f"{r['swaps'] / r['years']:.1f} | {r['mdd']:+.2f} |")
                    print(f"[combo] K{k} {lookback}p {cad} {exec_mode}: "
                          f"ann {r['ann']:+.2f}%/yr trips {r['trips']} "
                          f"MDD {r['mdd']:+.2f}")
    gated = [r for r in rows if r["exec_mode"] == "gated"]
    best = max(gated, key=lambda r: r["ann"])
    gate1 = best["ann"] >= static_g["ann"] + MARGIN_PP
    gate2 = best["mdd"] >= MDD_FLOOR
    md += ["", "## Verdict gates (pre-registered)", "",
           f"- Best gated combo: K={best['k']}, lookback={best['lookback']}p, "
           f"rebalance={best['cad']} -> {best['ann']:+.2f}%/yr notional",
           f"- Static gated baseline: {static_g['ann']:+.2f}%/yr",
           f"- G1 rotation beats static by >= {MARGIN_PP}pp/yr: "
           f"{'PASS' if gate1 else 'FAIL'} "
           f"(margin {best['ann'] - static_g['ann']:+.2f}pp)",
           f"- G2 funding-stream MDD >= {MDD_FLOOR}%: "
           f"{'PASS' if gate2 else 'FAIL'} ({best['mdd']:+.2f}%)"]
    md += ["", "## Four-bar table (per $100 notional; capital = /2 USDT-M 1x)",
           "", "| Bar | Definition | Best rotation | Static gate baseline |",
           "|---|---|---|---|"]
    for name, thr in (("A any-positive", None), ("B beats certified", 4.77),
                      ("C beats always-in", 6.82),
                      ("D double-digit capital", 20.0)):
        def bar(v):
            return ("PASS" if v > 0 else "FAIL") if thr is None else \
                ("PASS" if v >= thr else "FAIL")
        lab = "net > 0" if thr is None else f">= {thr}%/yr notional"
        md.append(f"| {name} | {lab} | {bar(best['ann'])} "
                  f"({best['ann']:+.2f}/yr) | {bar(static_g['ann'])} "
                  f"({static_g['ann']:+.2f}/yr) |")
    md += ["", f"Winner capital-basis note: USDT-M 1x per-capital = "
           f"{best['ann'] / 2:+.2f}%/yr; COIN-M-class per-capital = notional "
           "yield (not applicable here - universal set)."]
    ys = yearly_stream(idx, best["stream"])
    md += ["", "## Best-rotation funding stream by year ($/notional, pre-fees)",
           "", "| Year | stream |", "|---|---|"]
    for y, v in ys.items():
        md.append(f"| {y} | {v:+.2f} |")
    sh = best["share"].sort_values(ascending=False)
    md += ["", "Best-rotation earned-funding share by coin (>= 3% shown): "
           + ", ".join(f"{c.replace('USDT', '')} {v * 100:.0f}%"
                       for c, v in sh.items() if v >= 0.03), ""]
    ver = ("ROTATION VALIDATED" if (gate1 and gate2) else
           "ROTATION CLOSED - complexity without benefit; the STATIC GATED "
           "BLEND stays the funding-portfolio deliverable")
    md += [f"**E3 VERDICT: {ver}**", ""]
    path = os.path.join(OUT, "E3_rotation_report.md")
    open(path, "w", encoding="utf-8").write("\n".join(md))
    print(f"[E3] G1 {'PASS' if gate1 else 'FAIL'} | G2 "
          f"{'PASS' if gate2 else 'FAIL'} -> {ver}")
    print(f"[E3] written {path}")


if __name__ == "__main__":
    main()
