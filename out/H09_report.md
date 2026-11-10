# H09 REPORT - formal carry gauntlet (Session 9)

**FULL SPAN**: perp klines fetched this session (44,032 bars). Basis
= (perp close - spot close) at print instants; printed span 2021-11-06 -> 2026-11-04 (5.00y, 5475 prints). QA: perp-close basis
cross-checked against fapi markPrice overlap (2023-10-31+), diffs in bp
printed at build time. The S8 fallback-era MARGINAL is superseded by
this full-span verdict.

Costs: 30bp RT fees (15+15). Basis marked every print. Per $100
notional, 1x, not reinvested. Rules FROZEN from S6 pre-registration.

## Primary: GATED carry (frozen rule)

- Trips: 2 | funding collected: +24.13 | basis P&L: +0.29 | fees: 0.60
- **NET: +23.81 per $100** (+4.77%/yr annualized)
- Stream MDD: -0.31 (rail -10%) | stress NET: +23.31

| Trip | Entry -> exit |
|---|---|
| carry | 2021-11-06 16:00 -> 2022-02-28 08:00 (113.7d) basis +7.0bp -> -7.9bp |
| carry | 2023-01-14 08:00 -> 2025-05-02 16:00 (839.3d) basis +7.5bp -> -6.2bp |

| Year | Funding $ | Basis $ | Fees & slip $ | Net $ |
|---|---|---|---|---|
| 2021  (partial) | +2.32 | +0.07 | -0.15 | +2.24 |
| 2022 | +0.75 | +0.08 | -0.15 | +0.68 |
| 2023 | +7.60 | -0.00 | -0.15 | +7.45 |
| 2024 | +11.96 | +0.10 | -0.00 | +12.06 |
| 2025 | +1.49 | +0.04 | -0.15 | +1.38 |

## Comparator: ALWAYS-IN (era-restricted, info-only)

- Trips: 1 | funding +34.24 | basis +0.14 | fees 0.30 | **NET +34.08** (+6.82%/yr) | MDD -0.44 | stress NET +33.83

| Year | Funding $ | Basis $ | Fees & slip $ | Net $ |
|---|---|---|---|---|
| 2021  (partial) | +2.41 | +0.11 | -0.15 | +2.37 |
| 2022 | +4.16 | +0.02 | -0.00 | +4.19 |
| 2023 | +7.87 | -0.10 | -0.00 | +7.76 |
| 2024 | +11.96 | +0.10 | -0.00 | +12.06 |
| 2025 | +5.13 | +0.03 | -0.00 | +5.15 |
| 2026  (partial) | +2.72 | -0.02 | -0.15 | +2.54 |

## Gates (primary = GATED, per JOURNAL pre-registration)

- P1 NET > 0: PASS
- P2 annualized >= +3%/yr: PASS
- P3 calendar years net>=0 in >=75% of [2022, 2023, 2024, 2025]: PASS
- P4 stream MDD >= -10% (rail never breached): PASS
- P5 stress (x1.5 fees + 10bp RT slip) NET > 0: PASS
- P6 trips >= 2: PASS
- **VERDICT: GAUNTLET-CERTIFIED -> 14-calendar-day Binance testnet is locked before any live money; kill rails: -10% NAV strategy, -20% account.**
