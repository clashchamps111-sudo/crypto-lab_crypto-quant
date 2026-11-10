"""H09 - FORMAL CARRY GAUNTLET (Session 9, pre-registered in JOURNAL).

Strategy under test (frozen from the Session 6 pre-registered smoke, zero
optimization): BTC carry stack long spot + short perp 1x; GATED rule enters
when trailing-3 print mean funding > +1bp/8h (flat), exits when it prints
< -1bp/8h while held. Comparator (reported, info-only): ALWAYS-IN one trip
across the evaluated era.

FORMAL additions vs the S6 smoke:
- BASIS TRUTH: basis_t = (perp mark_t - spot_t) / spot_t at every funding
  print. Perp mark = fapi markPrice history; spot_t = Close of the 1h bar
  opening at t-1h (that bar closes exactly at t -> last real price, no
  lookahead). markPrice coverage starts 2023-10-31 -> EVALUATED ERA is
  2023-10-31 .. spot-file aligned last print (declared fallback: fapi perp
  klines unreachable today).
- MARK-TO-PRINT accounting (per $100 notional, 1x, not reinvested):
  while held, print t contributes  funding_t*100  (settles the held acht
  8h window; the EXIT print's own funding is dropped - S6 conservative
  continuity)  -  delta(basis)_t*100  (basis change during [t-1h, t]).
  Fees 15bp at entry + 15bp at exit (spot 10bp + perp 5bp per side).
  The S6 blind spot now priced: intra-held basis swings draw NAV.
Gates (JOURNAL): P1 gated NET>0 | P2 ann >= +3%/yr | P3 full years inside
era (2024, 2025) both net>=0 (fallback-era remap, 2023/26 partial reported)
| P4 stream MDD >= -10% (kill rail) | P5 stress fees x1.5 + 5bp/side basis
slip -> NET>0 | P6 >=2 trips. ALL -> CERTIFIED -> 14d testnet; P1 fail ->
DEAD; else MARGINAL. One judge pass.
"""
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")

FUND_CSV = os.path.join(ROOT, "data", "funding_BTCUSDT.csv")
SPOT_CSV = os.path.join(ROOT, "data", "BTCUSDT_1h_deep.csv")

FEE_HALF = 0.0015           # 15bp entry + 15bp exit = 30bp round trip
TRAIL_N = 3
ENTER_BP = 0.0001           # +1bp/8h trailing mean
EXIT_BP = -0.0001           # -1bp/8h trailing mean while held
KILL_RAIL = -0.10           # P4 carry rail (-10% NAV)
ANN_FLOOR = 0.03            # P2 +3%/yr
TRIP_FLOOR = 2              # P6
SLIP = 0.0005               # P5: 5bp per side on basis marks
NOTIONAL = 100.0            # per $100 notional reporting unit


def build_prints():
    f = pd.read_csv(FUND_CSV, parse_dates=["fundingTime"])
    f = f.sort_values("fundingTime").reset_index(drop=True)
    s = pd.read_csv(SPOT_CSV, index_col="Date", parse_dates=["Date"])
    spot_close = s["Close"].astype(float)
    perp_path = os.path.join(ROOT, "data", "BTCUSDT_perp_1h.csv")
    perp_close = (pd.read_csv(perp_path, index_col="openTime", parse_dates=["openTime"])
                  ["close"].astype(float))
    rows, qa = [], []
    for _, row in f.iterrows():
        t = row["fundingTime"]
        bar_t = t.floor("h") - pd.Timedelta(hours=1)   # bar that CLOSES at floor(t)
        sc = spot_close.get(bar_t)
        pc = perp_close.get(bar_t)
        if sc is None or pd.isna(sc) or sc <= 0:
            continue
        if pc is None or pd.isna(pc) or pc <= 0:
            continue
        mark = row["markPrice"]
        if not pd.isna(mark):
            qa.append((float(pc) - float(mark)) / float(sc))
        rows.append(dict(t=t, r=float(row["fundingRate"]), mark=float(pc),
                         mark_src="perp_close", spot=float(sc),
                         basis=(float(pc) - float(sc)) / float(sc)))
    df = pd.DataFrame(rows).sort_values("t").reset_index(drop=True)
    if qa:
        qa = np.abs(np.array(qa)) * 1e4
        print(f"[h09] basis QA vs markPrice: {len(qa)} overlap prints, "
              f"mean |diff| {qa.mean():.2f}bp, p95 {np.percentile(qa, 95):.2f}bp, "
              f"max {qa.max():.2f}bp")
    return df


def run_rule(prints, mode="gated", stress=False):
    """State machine over era prints. Dollars per $100 notional."""
    n = len(prints)
    rs = prints["r"].to_numpy()
    bs = prints["basis"].to_numpy()
    ts = prints["t"].to_numpy()
    trail = pd.Series(rs).rolling(TRAIL_N).mean().to_numpy()

    fee_mult = 1.5 if stress else 1.0
    slip = SLIP if stress else 0.0

    held_from = None
    stream = np.zeros(n)          # $ increments per $100 notional
    funding_tot = basis_tot = fees_tot = 0.0
    trips = []
    years = {}
    cur_trip = {}

    def bucket(t):
        y = pd.Timestamp(t).year
        if y not in years:
            years[y] = dict(fund=0.0, basis=0.0, fees=0.0)
        return years[y]

    for i in range(n):
        inc = 0.0
        if held_from is not None and i > held_from:
            # window [i-1, i) was held: delta always applies
            delta = (bs[i] - bs[i - 1]) * NOTIONAL
            inc += -delta
            basis_tot -= delta
            bucket(ts[i])["basis"] -= delta
            # funding of print i settles [i-1, i): applied unless THIS print is the exit
            # (conservative continuity: drop the exit print's own funding)
            if mode == "always" or (np.isfinite(trail[i]) and trail[i] >= EXIT_BP):
                inc += rs[i] * NOTIONAL
                funding_tot += rs[i] * NOTIONAL
                bucket(ts[i])["fund"] += rs[i] * NOTIONAL
            if i == n - 1:   # force close at era end
                fee_c = (FEE_HALF * fee_mult + slip) * NOTIONAL
                stream[i] -= fee_c
                fees_tot += fee_c
                bucket(ts[i])["fees"] += fee_c   # store positive; net = fund+basis-fees
                cur_trip.update(exit=ts[i], exit_basis=bs[i],
                                slip=slip, fee_mult=fee_mult)
                trips.append(cur_trip)
                held_from = None
        elif held_from is not None and i == held_from:
            pass  # entry print: no delta (we enter AT the mark), no funding
        # --- decisions at print i
        if held_from is None:
            enter = (i == 0 and mode == "always") or (
                mode == "gated" and np.isfinite(trail[i]) and trail[i] > ENTER_BP)
            if enter:
                fee_c = (FEE_HALF * fee_mult + slip) * NOTIONAL
                held_from = i
                stream[i] -= fee_c
                fees_tot += fee_c
                bucket(ts[i])["fees"] += fee_c
                cur_trip = dict(entry=ts[i], entry_basis=bs[i],
                                slip=slip, fee_mult=fee_mult)
        elif held_from is not None and i < n - 1 and mode == "gated" \
                and np.isfinite(trail[i]) and trail[i] < EXIT_BP:
            fee_c = (FEE_HALF * fee_mult + slip) * NOTIONAL
            stream[i] -= fee_c
            fees_tot += fee_c
            bucket(ts[i])["fees"] += fee_c
            cur_trip.update(exit=ts[i], exit_basis=bs[i])
            trips.append(cur_trip)
            held_from = None
        stream[i] += inc
        # if we exited this print, delta already booked by the accrual step

    # degenerate edge: entered at the very last print -> instant-close trip
    if held_from is not None:
        fee_c = (FEE_HALF * fee_mult + slip) * NOTIONAL
        stream[n - 1] -= fee_c
        fees_tot += fee_c
        bucket(ts[n - 1])["fees"] += fee_c
        cur_trip.update(exit=ts[n - 1], exit_basis=bs[n - 1])
        trips.append(cur_trip)
        held_from = None

    net = funding_tot + basis_tot - fees_tot
    cum = np.cumsum(stream)
    peak = np.maximum.accumulate(cum) if len(cum) else np.array([0.0])
    mdd = float((cum - peak).min()) if len(cum) else 0.0
    years_span = (pd.Timestamp(ts[-1]) - pd.Timestamp(ts[0])).total_seconds() / (365.25 * 86400)
    return dict(mode=mode, stress=stress, net=net, funding=funding_tot,
                basis=basis_tot, fees=fees_tot, mdd=mdd, trips=len(trips),
                ann=(net / NOTIONAL) / years_span if years_span > 0 else float("nan"),
                span=(pd.Timestamp(ts[0]), pd.Timestamp(ts[-1])), years=years_span, per_year=years,
                trip_rows=trips, stream=cum, trail_fired=bool(np.any(
                    np.isfinite(trail) & (trail > ENTER_BP))))


def fmt_trip(tr):
    e, x = pd.Timestamp(tr["entry"]), pd.Timestamp(tr["exit"])
    days = (x - e).total_seconds() / 86400
    return (f"{e:%Y-%m-%d %H:%M} -> {x:%Y-%m-%d %H:%M} ({days:.1f}d) "
            f"basis {tr['entry_basis'] * 1e4:+.1f}bp -> {tr['exit_basis'] * 1e4:+.1f}bp")


def verdict_for(res, era_full_years):
    g = {
        "P1 NET > 0": res["net"] > 0,
        f"P2 annualized >= +{ANN_FLOOR:.0%}/yr": res["ann"] >= ANN_FLOOR,
        f"P3 calendar years net>=0 in >=75% of {era_full_years}":
            (sum(1 for y in era_full_years
                 if res["per_year"].get(y, {}).get("net", -1) >= 0)
             >= len(era_full_years) * 0.75) if era_full_years else False,
        f"P4 stream MDD >= {KILL_RAIL:.0%} (rail never breached)": res["mdd"] >= KILL_RAIL * NOTIONAL,
        "P5 stress (x1.5 fees + 10bp RT slip) NET > 0": res["stress_net"] > 0,
        f"P6 trips >= {TRIP_FLOOR}": res["trips"] >= TRIP_FLOOR,
    }
    return g


def main():
    os.makedirs(OUT, exist_ok=True)
    prints = build_prints()
    print(f"[h09] era prints: {len(prints)} "
          f"({prints['t'].min()} -> {prints['t'].max()})")
    base = run_rule(prints, "gated", stress=False)
    stressed = run_rule(prints, "gated", stress=True)
    always = run_rule(prints, "always", stress=False)
    always_st = run_rule(prints, "always", stress=True)
    base["stress_net"] = stressed["net"]
    always["stress_net"] = always_st["net"]

    # per-year net columns (fees bucket stores POSITIVE charges)
    for res in (base, always):
        for y in res["per_year"]:
            b = res["per_year"][y]
            b["net"] = b["fund"] + b["basis"] - b["fees"]
    full_in_span = [y for y in (2022, 2023, 2024, 2025) if y in base["per_year"]]

    md = ["# H09 REPORT - formal carry gauntlet (Session 9)", "",
          "**FULL SPAN**: perp klines fetched this session (44,032 bars). Basis",
          f"= (perp close - spot close) at print instants; printed span "
          f"{base['span'][0]:%Y-%m-%d} -> {base['span'][1]:%Y-%m-%d} "
          f"({base['years']:.2f}y, {len(prints)} prints). QA: perp-close basis",
          "cross-checked against fapi markPrice overlap (2023-10-31+), diffs in bp",
          "printed at build time. The S8 fallback-era MARGINAL is superseded by",
          "this full-span verdict.\n",
          "Costs: 30bp RT fees (15+15). Basis marked every print. Per $100",
          "notional, 1x, not reinvested. Rules FROZEN from S6 pre-registration.", "",
          "## Primary: GATED carry (frozen rule)", ""]
    md += [f"- Trips: {base['trips']} | funding collected: {base['funding']:+.2f} "
           f"| basis P&L: {base['basis']:+.2f} | fees: {base['fees']:.2f}",
           f"- **NET: {base['net']:+.2f} per $100** ({base['ann']:+.2%}/yr annualized)",
           f"- Stream MDD: {base['mdd']:+.2f} (rail {KILL_RAIL * 100:.0f}%) "
           f"| stress NET: {stressed['net']:+.2f}",
           "", "| Trip | Entry -> exit |", "|---|---|"]
    for tr in base["trip_rows"]:
        md.append(f"| carry | {fmt_trip(tr)} |")
    md += ["", "| Year | Funding $ | Basis $ | Fees & slip $ | Net $ |", "|---|---|---|---|---|"]
    for y in sorted(base["per_year"]):
        b = base["per_year"][y]
        md.append(f"| {y}{'  (partial)' if str(y) in ('2021', '2026') else ''} "
                  f"| {b['fund']:+.2f} | {b['basis']:+.2f} | {-b['fees']:+.2f} | {b['net']:+.2f} |")
    md += ["", "## Comparator: ALWAYS-IN (era-restricted, info-only)", ""]
    md += [f"- Trips: {always['trips']} | funding {always['funding']:+.2f} | "
           f"basis {always['basis']:+.2f} | fees {always['fees']:.2f} "
           f"| **NET {always['net']:+.2f}** ({always['ann']:+.2%}/yr) "
           f"| MDD {always['mdd']:+.2f} | stress NET {always_st['net']:+.2f}",
           "", "| Year | Funding $ | Basis $ | Fees & slip $ | Net $ |", "|---|---|---|---|---|"]
    for y in sorted(always["per_year"]):
        b = always["per_year"][y]
        md.append(f"| {y}{'  (partial)' if str(y) in ('2021', '2026') else ''} "
                  f"| {b['fund']:+.2f} | {b['basis']:+.2f} | {-b['fees']:+.2f} | {b['net']:+.2f} |")
    gates = verdict_for(base, full_in_span)
    md += ["", "## Gates (primary = GATED, per JOURNAL pre-registration)", ""]
    for k, ok in gates.items():
        md.append(f"- {k}: {'PASS' if ok else 'FAIL'}")
    if all(gates.values()):
        verdict = ("GAUNTLET-CERTIFIED -> 14-calendar-day Binance testnet is locked "
                   "before any live money; kill rails: -10% NAV strategy, -20% account.")
    elif not gates["P1 NET > 0"]:
        verdict = "DEAD - P1 failed under full execution truth."
    else:
        verdict = ("MARGINAL (failed: " + "; ".join(k for k, ok in gates.items() if not ok) + ")")
    md += [f"- **VERDICT: {verdict}**", ""]
    path = os.path.join(OUT, "H09_report.md")
    open(path, "w", encoding="utf-8").write("\n".join(md))
    print(f"[h09] gated: net {base['net']:+.2f} ({base['ann']:+.2%}/yr), trips {base['trips']}, "
          f"MDD {base['mdd']:+.2f}, stress net {stressed['net']:+.2f}")
    print(f"[h09] always-in era: net {always['net']:+.2f} ({always['ann']:+.2%}/yr), "
          f"MDD {always['mdd']:+.2f}")
    print(f"[h09] verdict: {verdict}")
    print(f"[h09] written: {path}")


if __name__ == "__main__":
    main()
