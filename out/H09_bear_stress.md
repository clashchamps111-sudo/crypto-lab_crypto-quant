# H09 BEAR-STRESS GROUNDWORK (Session 8, pre-registered deliverable)

The carry leg SHORT-perp pays when funding prints negative; 2022
bear era = stress epoch. Stress numbers only - NOT a gauntlet.

## Yearly funding profile (short-perp holder PAYS when negative)

| Year | Funding sum % | Mean annualized | Negative prints | Prints |
|---|---|---|---|---|
| 2021 | +2.459% | +16.0% | 1.2% | 168 |
| 2022 | +4.165% | +4.2% | 22.1% | 1095 |
| 2023 | +7.866% | +7.9% | 10.1% | 1095 |
| 2024 | +11.957% | +11.9% | 8.4% | 1098 |
| 2025 | +5.126% | +5.1% | 12.9% | 1095 |
| 2026 | +2.766% | +3.3% | 24.5% | 930 |

## ALWAYS-IN carry stream (one trip, whole span, no fees)

- Final stream value: +34.338% of notional over 5481 prints
- Stream MAX DRAWDOWN: -0.412pp of notional (trough 2021-11-06, peak 2021-11-06)
- Worst calendar month: -0.177% | Worst 90-print window: -0.297% | Longest consecutive negative-print run: 18 prints (6.0 days)

## GATED rule (Session 6 smoke spec) - whole span

- Trips: 2 | funding collected: +24.11% of notional | fees: 0.60 | NET: +23.51 on $100 (S6 reference +23.51 - accounting tolerance check)
- Gated stream MDD (cumulative held funding, no-fees view): -0.09pp

## 2022 bear slice (the stress test)

- Prints in 2022: 1095 | prints HELD by the gate in 2022: 175 (16.0% exposure)
- Funding accrued by the held leg in 2022: +0.75% of notional
- Held prints negative in 2022: 47/175 (26.9%)
- Strictest negative stretch while held (worst 30-held-print sum): -0.02%

## Formal gauntlet design notes (checklist for H09)

- Basis/slip: model perp entry/exit at mark-vs-index drift; spot spread
  ~1-2bp on majors; rebalancing monthly max (fee budget).
- Funding accrual = realized prints already captured here (conservative).
- Both-leg execution: spot 10bp/side + perp 5bp/side (current model)
  -> stress at 1.5x costs in the gauntlet.
- Kill rails: carry stack DD gates at strategy -10% of NAV (tighter than
  the default -15% because carryincome ~7%/yr arithmetic), liquidate
  both legs together; account -20% rail unchanged.
