# H08 REPORT - cross-sectional momentum portfolio

Pre-registered in JOURNAL BEFORE build (gates P1-P6, N1-N4).
r-day momentum rank, top-K equal weight, weekly anchors, next-open
execution, 7bp/side + 3bp/day haircut. One judge pass.

## Train (48m) - grid selection (money view, declared)

| r | K | Realized $ | Open@cutoff $ | NET $ | Closed legs |
|---|---|---|---|---|---|
| 30 | 2 | +225.78 | -27.70 | +198.09 | 126 |
| 30 | 3 | +203.47 | -30.03 | +173.44 | 171 |
| 60 | 2 | +53.85 | -17.64 | +36.20 | 98 |
| 60 | 3 | +160.38 | -51.74 | +108.64 | 116 |
- **Frozen winner: r=30, K=2 (max train NET)**

## Test year 2025-11-05 -> 2026-11-05 (frozen r=30, K=2)

- Closed in-window legs: 43 | realized $-64.66 (net of fees + haircut)
- Continuous-run M2M: -59.62 | residual/unrealized $+5.04 (8% of realized) | open@cutoff 2 names (forced-close value -0.53, informational)
- **P1 realized NET: -64.66 on $100**

| Symbol | Realized $ |
|---|---|
| SOLUSDT | +2.97 |
| LINKUSDT | -0.34 |
| BTCUSDT | -0.53 |
| TRXUSDT | -4.53 |
| DOGEUSDT | -8.30 |
| AVAXUSDT | -8.77 |
| ETHUSDT | -8.79 |
| XRPUSDT | -8.99 |
| BNBUSDT | -12.57 |
| ADAUSDT | -14.82 |

## Folds (4x3m absolute-calendar, 150d warmup, in-window entries)

| Fold | Realized $ | Unreal $ | Legs |
|---|---|---|---|
| 1 | -30.16 | -7.02 | 11 |
| 2 | -4.16 | +3.43 | 9 |
| 3 | -28.43 | +0.76 | 9 |
| 4 | -12.53 | +1.00 | 12 |
- Pool realized -75.29, unreal -1.82, folds-positive 0/4

## Stability battery

| Non-winner combo | Test realized $ |
|---|---|
| r=30 K=3 | -57.72 |
| r=60 K=2 | -34.11 |
| r=60 K=3 | -31.01 |
| LOO excluded | Test realized $ |
|---|---|
| BTCUSDT | -66.38 |
| ETHUSDT | -62.64 |
| BNBUSDT | -58.16 |
| SOLUSDT | -67.31 |
| XRPUSDT | -63.02 |
| DOGEUSDT | -61.05 |
| ADAUSDT | -56.33 |
| LINKUSDT | -58.53 |
| AVAXUSDT | -63.66 |
| TRXUSDT | -69.38 |
- N1 neighborhood: 0/3 non-winner combos positive (winner + >=2 => >=3/4) -> FAIL
- N2 leave-one-out: 0/10 pools realized-positive -> FAIL
- N3 double-cost 10bp/side: realized -64.75 -> FAIL
- N4 attribution: best symbol +2.97 = 5% of realized -> FAIL
- P5 benchmark: realized -64.66 vs B&H-net -34.21 -> FAIL

**Gates:**
- P1 test-year realized NET > 0: FAIL
- P2 closed legs >= 20: PASS
- P3 >= 2/4 folds realized-positive: FAIL
- P4 |residual| <= 25% of realized: PASS
- P5 realized NET > equal-weight B&H net: FAIL
- P6-N1 neighborhood >= 3/4 positive: FAIL
- P6-N2 all 10 LOO pools positive: FAIL
- P6-N3 NET > 0 at 10bp/side: FAIL
- P6-N4 best symbol <= 60% realized: FAIL
**VERDICT: DEAD**
