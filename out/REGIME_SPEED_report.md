# REGIME-SPEED CONFIRMATORY STUDY (Session 8, pre-registered)

CONFIRMATORY ONLY: the judge year was already spent once (S6 test).
Selection on calendar 2022-2024 (common start 2022-06-01 for all
combos - warmup-bias control), confirmation = EXACT S6 judge replay.
Nothing certifies here; output feeds the pre-registered pivot
condition.

## Selection epoch (2022-06-01 -> 2024-12-31, pooled net)

| n_sma | n_roc | Realized $ | Funding drag $ | NET $ | Legs |
|---|---|---|---|---|---|
| 150 | 30 | +210.35 | +13.59 | +196.77 | 269 **<- selected** |
| 150 | 20 | +204.10 | +13.18 | +190.92 | 347 |
| 100 | 30 | +202.32 | +13.84 | +188.48 | 276 |
| 100 | 20 | +199.96 | +13.52 | +186.44 | 365 |
| 200 | 30 | +191.59 | +12.68 | +178.91 | 259 |
| 200 | 20 | +188.50 | +12.53 | +175.97 | 326 |
| 100 | 50 | +98.88 | +14.08 | +84.81 | 257 |
| 150 | 50 | +91.15 | +13.56 | +77.60 | 247 |
| 200 | 50 | +81.58 | +12.78 | +68.80 | 233 |
- Train family means:
SMA(100): +153.24, SMA(150): +155.09, SMA(200): +141.23
- T3 slow-decay on train: +153.24 vs +155.09 vs +141.23 -> NOT monotone

## Confirmation (judge replay, selected combo n_sma=150, n_roc=30)

- Judge pooled NET: -3.61 across 58 legs (absolute-calendar 4x3m folds, in-window entries - S6 machinery)
- Judge pooled realized: -0.24

| Family (n_sma) | Judge members net-positive | Family mean judge NET $ |
|---|---|---|
| 100 | 3/3 | +4.02 |
| 150 | 0/3 | -4.56 |
| 200 | 0/3 | -15.05 |

**Gates:**
- T1 selected combo judge NET > 0: -3.61 -> FAIL
- T2 family property (train family mean +155.09 > 0, judge members >=2/3 positive) -> FAIL
- T3 (advisory) train slow-decay mirror -> ABSENT

**STUDY VERDICT: TRANSFER FAILS - pivot condition COMPLETES (H08 dead + speed selection does not transfer): daily-bar alpha line shelved permanently; desk pivots to funding-carry (H09 gauntlet) or parks; user ratifies branch at the report card.**
