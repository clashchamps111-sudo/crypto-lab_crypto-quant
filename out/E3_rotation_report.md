# E3 FUNDING-ROTATION HARVEST (Session 10.6, pre-registered)

Selection = richest trailing funding coins each rebalance;
S6 frozen per-coin gates (primary) or selected-always comparator;
conservative accrual (entry/exit/boundary prints not earned);
30bp RT per cycle; funding-only stream MDD; 16 combos at once,
gated family = primary. Baselines re-run under identical
conventions (K=10). UNIT OF RECORD: per $100 BOOK notional -
each open sleeve carries book/K weight (E2 blend comparable).

| K | lookback | reb | exec | net % | net %/yr | trips | cycl/yr | swap/yr | MDD % |
|---|---|---|---|---|---|---|---|---|---|
| 10 | n/a | n/a | gated STATIC BASELINE | +16.85 | +3.36 | 47 | 9.4 | - | -0.02 |
| 10 | n/a | n/a | selected_always STATIC | +23.03 | +4.60 | 97 | 19.4 | - | -0.17 |
| 3 | 90p | W | gated | +12.58 | +2.51 | 51 | 10.2 | 8.8 | -0.03 |
| 5 | 90p | W | gated | +17.14 | +3.42 | 46 | 9.2 | 7.0 | -0.03 |
| 3 | 180p | W | gated | +16.22 | +3.24 | 32 | 6.4 | 5.0 | -0.02 |
| 5 | 180p | W | gated | +18.49 | +3.69 | 31 | 6.2 | 3.6 | -0.02 |
| 3 | 90p | M | gated | +16.26 | +3.25 | 32 | 6.4 | 4.8 | -0.02 |
| 5 | 90p | M | gated | +18.01 | +3.59 | 36 | 7.2 | 4.6 | -0.02 |
| 3 | 180p | M | gated | +18.44 | +3.68 | 21 | 4.2 | 3.2 | -0.01 |
| 5 | 180p | M | gated | +19.03 | +3.80 | 27 | 5.4 | 2.8 | -0.02 |
| 3 | 90p | W | always | +21.71 | +4.33 | 149 | 29.7 | 27.5 | -0.35 |
| 5 | 90p | W | always | +26.53 | +5.30 | 140 | 27.9 | 22.4 | -0.31 |
| 3 | 180p | W | always | +27.89 | +5.57 | 83 | 16.6 | 15.8 | -0.42 |
| 5 | 180p | W | always | +28.63 | +5.71 | 82 | 16.4 | 13.4 | -0.64 |
| 3 | 90p | M | always | +26.78 | +5.35 | 79 | 15.8 | 12.8 | -0.41 |
| 5 | 90p | M | always | +28.05 | +5.60 | 87 | 17.4 | 10.8 | -0.32 |
| 3 | 180p | M | always | +29.75 | +5.94 | 49 | 9.8 | 8.8 | -0.49 |
| 5 | 180p | M | always | +28.19 | +5.63 | 54 | 10.8 | 7.2 | -0.55 |

## Verdict gates (pre-registered)

- Best gated combo: K=5, lookback=180p, rebalance=M -> +3.80%/yr notional
- Static gated baseline: +3.36%/yr
- G1 rotation beats static by >= 0.5pp/yr: FAIL (margin +0.44pp)
- G2 funding-stream MDD >= -1.0%: PASS (-0.02%)

## Four-bar table (per $100 notional; capital = /2 USDT-M 1x)

| Bar | Definition | Best rotation | Static gate baseline |
|---|---|---|---|
| A any-positive | net > 0 | PASS (+3.80/yr) | PASS (+3.36/yr) |
| B beats certified | >= 4.77%/yr notional | FAIL (+3.80/yr) | FAIL (+3.36/yr) |
| C beats always-in | >= 6.82%/yr notional | FAIL (+3.80/yr) | FAIL (+3.36/yr) |
| D double-digit capital | >= 20.0%/yr notional | FAIL (+3.80/yr) | FAIL (+3.36/yr) |

Winner capital-basis note: USDT-M 1x per-capital = +1.90%/yr; COIN-M-class per-capital = notional yield (not applicable here - universal set).

## Best-rotation funding stream by year ($/notional, pre-fees)

| Year | stream |
|---|---|
| 2021 | +0.00 |
| 2022 | +0.00 |
| 2023 | +30.53 |
| 2024 | +65.38 |
| 2025 | +5.77 |
| 2026 | +1.58 |

Best-rotation earned-funding share by coin (>= 3% shown): XRP 20%, DOGE 19%, LINK 13%, AVAX 13%, SOL 11%, ADA 10%, ETH 10%

**E3 VERDICT: ROTATION CLOSED - complexity without benefit; the STATIC GATED BLEND stays the funding-portfolio deliverable**
