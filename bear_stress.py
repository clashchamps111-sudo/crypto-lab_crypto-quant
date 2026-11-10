"""SESSION 8 SIDE LINE - H09 BEAR-STRESS GROUNDWORK (pre-registered deliverable).

Question: how bad is negative-funding drawdown for the SHORT-perp leg of a
long-spot+short-perp carry (we PAY when prints go negative)? 2022 bear era =
stress epoch. From data/funding_BTCUSDT.csv (5,481 prints, in hand).

Deliverables (pre-registered):
- Per-year funding totals (2021-11 -> 2026-11), negative-print share/year.
- ALWAYS-IN stream: cumulative funding % of notional; its max drawdown (pp);
  worst calendar month; worst 90-print window; longest negative-print run.
- GATED rule (S6 smoke spec: trail-3 mean > +1bp/8h enter when flat;
  < -1bp/8h exit; fees 30bp round trip on $100): full-span replay (reproduce
  the S6 +23.51 reference within tolerance), plus 2022-slice stats.
- Formal-gauntlet design notes (basis/slip, mark-vs-index, spreads, rebal).
NOT a gauntlet, NOT certified: stress numbers only.
"""
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
CSV = os.path.join(ROOT, "data", "funding_BTCUSDT.csv")

FEE_RT = 0.003            # 30bp round trip (S6 smoke spec, $100 notional)
TRAIL_N = 3
ENTER_BP = 0.0001         # +1bp/8h
EXIT_BP = -0.0001


def load():
    df = pd.read_csv(CSV, parse_dates=["fundingTime"])
    df = df.sort_values("fundingTime").reset_index(drop=True)
    return df


def yearly_table(df, md):
    y = df.groupby(df["fundingTime"].dt.year)["fundingRate"].agg(["sum", "mean", "count"])
    neg = df.assign(neg=df["fundingRate"] < 0).groupby(df["fundingTime"].dt.year)["neg"].mean()
    md += ["## Yearly funding profile (short-perp holder PAYS when negative)", "",
           "| Year | Funding sum % | Mean annualized | Negative prints | Prints |",
           "|---|---|---|---|---|"]
    for yr, row in y.iterrows():
        md.append(f"| {yr} | {row['sum'] * 100:+.3f}% | {row['mean'] * 3 * 365:+.1%} | "
                  f"{neg[yr]:.1%} | {int(row['count'])} |")
    md.append("")
    return y


def always_in(df, md):
    r = df["fundingRate"].to_numpy()
    cum = np.cumsum(r) * 100.0           # % of notional
    peak = np.maximum.accumulate(cum)
    mdd = float((cum - peak).min())
    worst_idx = int(np.argmin(cum - peak))
    seen = cum - peak
    mdd_span = (df["fundingTime"].iloc[int(np.argmin(cum))], df["fundingTime"].iloc[int(np.argmax(peak[:np.argmin(cum) + 1]))]) if cum.size else None
    worst_month = df.groupby(df["fundingTime"].dt.to_period("M"))["fundingRate"].sum().min() * 100
    roll90 = pd.Series(r).rolling(90).sum()
    w90 = roll90.min() * 100
    neg = r < 0
    runs = []
    c = 0
    for x in neg:
        if x:
            c += 1
        else:
            if c:
                runs.append(c)
            c = 0
    if c:
        runs.append(c)
    longest = max(runs) if runs else 0
    md += ["## ALWAYS-IN carry stream (one trip, whole span, no fees)", "",
           f"- Final stream value: {cum[-1]:+.3f}% of notional over {len(df)} prints",
           f"- Stream MAX DRAWDOWN: {mdd:+.3f}pp of notional "
           f"(trough {df['fundingTime'].iloc[int(np.argmin(cum))].date()}, "
           f"peak {df['fundingTime'].iloc[int(np.argmax(peak[:int(np.argmin(cum)) + 1]))].date()})",
           f"- Worst calendar month: {worst_month:+.3f}% | Worst 90-print window: {w90:+.3f}% | "
           f"Longest consecutive negative-print run: {longest} prints "
           f"({longest / 3:.1f} days)", ""]
    return dict(mdd=mdd, worst_idx=worst_idx, mdd_span=mdd_span)


def gated_rule(df):
    r = df["fundingRate"].to_numpy()
    t = df["fundingTime"].to_numpy()
    trail = pd.Series(r).rolling(TRAIL_N).mean().to_numpy()
    entries, exits = [], []
    inpos = False
    for i in range(TRAIL_N, len(r)):
        if not inpos and np.isfinite(trail[i]) and trail[i] > ENTER_BP:
            inpos = True
            entries.append(int(i + 1))     # accrue from the NEXT print (conservative)
        elif inpos and np.isfinite(trail[i]) and trail[i] < EXIT_BP:
            inpos = False
            exits.append(int(max(0, i - 1)))
    if len(exits) < len(entries):
        exits.append(int(len(r) - 1))
    held = np.zeros(len(r), dtype=bool)
    trips = []
    for e, x in zip(entries, exits):
        x2 = x if x >= e else len(r) - 1
        held[e:x2 + 1] = True
        trips.append((t[e], t[x2], float(r[e:x2 + 1].sum()) * 100))
    funding = float(df["fundingRate"][held].sum()) * 100.0
    fees = len(trips) * FEE_RT * 100
    net = funding - fees
    stream = np.cumsum(np.where(held, r, 0.0)) * 100.0
    peak = np.maximum.accumulate(stream)
    stream_mdd = float((stream - peak).min()) if len(stream) else 0.0
    return dict(trips=len(trips), trip_rows=trips, funding=funding, fees=fees,
                net=net, held=held, stream_mdd=stream_mdd)


def main():
    os.makedirs(OUT, exist_ok=True)
    df = load()
    print(f"[bear] {len(df)} prints: {df['fundingTime'].min()} -> {df['fundingTime'].max()}")
    md = ["# H09 BEAR-STRESS GROUNDWORK (Session 8, pre-registered deliverable)", "",
          "The carry leg SHORT-perp pays when funding prints negative; 2022",
          "bear era = stress epoch. Stress numbers only - NOT a gauntlet.", ""]
    yearly_table(df, md)
    ai = always_in(df, md)
    g = gated_rule(df)
    md += [f"## GATED rule (Session 6 smoke spec) - whole span", "",
           f"- Trips: {g['trips']} | funding collected: {g['funding']:+.2f}% of notional | "
           f"fees: {g['fees']:.2f} | NET: {g['net']:+.2f} on $100 "
           f"(S6 reference +23.51 - accounting tolerance check)",
           f"- Gated stream MDD (cumulative held funding, no-fees view): "
           f"{g['stream_mdd']:+.2f}pp", ""]
    held = g["held"]
    dd = df["fundingTime"].dt.year == 2022
    h22 = held & dd
    fund22 = float(df["fundingRate"][h22].sum()) * 100
    md += [f"## 2022 bear slice (the stress test)", "",
           f"- Prints in 2022: {int(dd.sum())} | prints HELD by the gate in 2022: "
           f"{int(h22.sum())} ({h22.sum() / max(dd.sum(), 1):.1%} exposure)",
           f"- Funding accrued by the held leg in 2022: {fund22:+.2f}% of notional",
           f"- Held prints negative in 2022: {(df['fundingRate'][h22] < 0).sum()}"
           f"/{int(h22.sum()) if h22.sum() else 1}"
           f" ({(df['fundingRate'][h22] < 0).mean() if h22.sum() else 0:.1%})",
           f"- Strictest negative stretch while held (worst 30-held-print sum): "
           f"{(pd.Series(df['fundingRate'][h22]).rolling(30).sum().min() * 100):+.2f}%", ""]
    md += ["## Formal gauntlet design notes (checklist for H09)", "",
           "- Basis/slip: model perp entry/exit at mark-vs-index drift; spot spread",
           "  ~1-2bp on majors; rebalancing monthly max (fee budget).",
           "- Funding accrual = realized prints already captured here (conservative).",
           "- Both-leg execution: spot 10bp/side + perp 5bp/side (current model)",
           "  -> stress at 1.5x costs in the gauntlet.",
           "- Kill rails: carry stack DD gates at strategy -10% of NAV (tighter than",
           "  the default -15% because carryincome ~7%/yr arithmetic), liquidate",
           "  both legs together; account -20% rail unchanged.", ""]
    path = os.path.join(OUT, "H09_bear_stress.md")
    open(path, "w", encoding="utf-8").write("\n".join(md))
    print(f"[bear] always-in stream MDD: {ai['mdd']:+.3f}pp")
    print(f"[bear] gated: trips {g['trips']}, net {g['net']:+.2f}, 2022 held prints "
          f"{int(h22.sum())}, 2022 funding {fund22:+.2f}%")
    print(f"[bear] written: {path}")


if __name__ == "__main__":
    main()
