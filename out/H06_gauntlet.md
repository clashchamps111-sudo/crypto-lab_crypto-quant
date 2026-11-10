# H06 GAUNTLET - maker-execution layer on both audit-flipped candidates

Pre-registered gates P1-P7 (see file header + JOURNAL). Signals frozen from
audit; no re-optimization; fill_wait is the only new parameter and it is
treated as a mechanism knob inside the neighbor grid.

## H06a_DonchianMaker (params frozen: n_enter=20, n_exit=10, atr_stop=3)

Primary = deep test year, 4 x 3m folds. Official cost 2.0bp/side.

| Fold | Realized $ | Unreal $ | Trades | Sharpe |
|---|---|---|---|---|
| 1 | -7.04 | +0.00 | 24 | -3.22 |
| 2 | -2.05 | +0.13 | 29 | -0.67 |
| 3 | -4.25 | +0.79 | 18 | -1.97 |
| 4 | +15.70 | +1.43 | 26 | 1.73 |

- **Primary pool: realized +2.36, trades 97, mean fold Sharpe -1.03, folds-positive 1/4**
- Unrealized/open@cutoff: +2.35 (share 100% of realized)
- Neighbors positive: 24/27 = 89%
- ETH pool: realized +12.01, trades 85, mean fold Sharpe 0.36
- PEEK pool (4 folds, months 36-48): realized +3.16, trades 116, mean fold Sharpe 0.02
- Blended bracket (4.5bp/side) primary: realized -0.82, trades 97, mean fold Sharpe -1.29, folds-positive 1/4

**Gates:**
- P1 pooled realized>0: PASS
- P2 pooled closed trades>=20: PASS
- P3 mean fold Sharpe>0: FAIL
- P4 >=3/4 folds positive: FAIL
- P5 neighbors>=60% positive: PASS
- P6 ETH pooled realized>0: PASS
- P7 unreal <=25% of realized: FAIL
- **VERDICT: MARGINAL (failed: P3 mean fold Sharpe>0; P4 >=3/4 folds positive; P7 unreal <=25% of realized)**

## H06b_MakerShortPullback (params frozen: n_fast=9, atr_stop=2.5, use_vwap=1)

Primary = deep test year, 4 x 3m folds. Official cost 2.0bp/side.

| Fold | Realized $ | Unreal $ | Trades | Sharpe |
|---|---|---|---|---|
| 1 | +0.00 | +0.00 | 0 | n/a |
| 2 | -3.68 | -0.00 | 284 | -1.27 |
| 3 | -6.59 | +0.00 | 146 | -2.20 |
| 4 | -4.77 | -0.00 | 104 | -2.60 |

- **Primary pool: realized -15.04, trades 534, mean fold Sharpe -2.02, folds-positive 0/4**
- Unrealized/open@cutoff: -0.00 (share 0% of realized)
- Neighbors positive: 0/27 = 0%
- ETH pool: realized -16.93, trades 465, mean fold Sharpe -3.39
- PEEK pool (4 folds, months 36-48): realized -19.79, trades 562, mean fold Sharpe -2.87
- Blended bracket (4.5bp/side) primary: realized -31.75, trades 534, mean fold Sharpe -4.78, folds-positive 0/4

**Gates:**
- P1 pooled realized>0: FAIL
- P2 pooled closed trades>=20: PASS
- P3 mean fold Sharpe>0: FAIL
- P4 >=3/4 folds positive: FAIL
- P5 neighbors>=60% positive: FAIL
- P6 ETH pooled realized>0: FAIL
- P7 unreal <=25% of realized: PASS
- **VERDICT: DEAD**

## Session verdict summary

| Variant | Verdict |
|---|---|
| H06a_DonchianMaker | MARGINAL (failed: P3 mean fold Sharpe>0; P4 >=3/4 folds positive; P7 unreal <=25% of realized) |
| H06b_MakerShortPullback | DEAD |