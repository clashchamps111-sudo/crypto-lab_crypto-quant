# CLOSURE MATRIX REPORT (Session 10, pre-registered)

One execution per cell; four lenses (SOP / ladder / sweep / regime
split). Frozen param transfer. Judge = months [48,60) with per-TF
warmup lead, in-window entries, 7bp/side + 3bp/day haircut.
BTC primary; ETH cross-checks scoped out.

Family verdict (SOP lens + mandatory regime rule): CONFIRMED-DEAD
iff judge net <= 0 in every non-empty regime bucket of native AND
adjacent cells; any positive bucket -> bar/regime-locked candidate.

## H01 (frozen transfer: n_fast=13, n_slow=21, rsi_lo=35, rsi_hi=65, atr_stop=2.5, atr_tgt=3.0)

| TF | Ret% | Sharpe | PF | Trades | Net$ | Bull | Sideways | Bear |
|---|---|---|---|---|---|---|---|---|
| 15m | -43.84 | -6.35 | 0.54 | 291 | -91.33 | -5.99 | -50.57 | -34.76 |
| 1h | -10.07 | -1.10 | 0.72 | 85 | -20.01 | -0.24 | -20.17 | +0.41 |
| 4h | -6.29 | -1.50 | 0.49 | 25 | -7.46 | -1.05 | -4.48 | -1.93 |
| weekly | +0.25 | 0.18 | 1.31 | 0 | +0.00 | +0.00 | +0.00 | +0.00 |

- **SOP lens:** NOT closed (9 non-empty bucket×cells checked, all net<=0: False)
- **Ladder lens:** ladder would have stopped at native (1h)
- **Regime/locked flags:** 1h/bear +0.41
- **Sweep lens:** the table above is the full matrix view.


## H02b (frozen transfer: n_fast=9, rsi_lo=35, rsi_hi=60, atr_stop=2.5, atr_tgt=3.0)

| TF | Ret% | Sharpe | PF | Trades | Net$ | Bull | Sideways | Bear |
|---|---|---|---|---|---|---|---|---|
| 15m | -46.33 | -5.31 | 0.67 | 488 | -145.96 | -35.81 | -75.33 | -34.82 |
| 1h | -3.87 | -0.39 | 0.96 | 123 | -26.58 | -10.92 | -18.77 | +3.11 |
| 4h | -4.07 | -0.82 | 0.69 | 55 | -6.50 | -0.59 | -5.10 | -0.82 |

- **SOP lens:** NOT closed (9 non-empty bucket×cells checked, all net<=0: False)
- **Ladder lens:** ladder would have stopped at native (1h)
- **Regime/locked flags:** 1h/bear +3.11
- **Sweep lens:** the table above is the full matrix view.


## H03 (frozen transfer: n_enter=20, n_exit=10, atr_stop=3.0)

| TF | Ret% | Sharpe | PF | Trades | Net$ | Bull | Sideways | Bear |
|---|---|---|---|---|---|---|---|---|
| 15m | -53.12 | -4.65 | 0.62 | 423 | -213.30 | -33.53 | -106.63 | -73.14 |
| 1h | -5.22 | -0.31 | 0.83 | 98 | -38.85 | +2.77 | -30.22 | -11.40 |
| 4h | -0.50 | -0.08 | 0.72 | 31 | -5.09 | +2.24 | -9.23 | +1.91 |
| weekly | -0.35 | -1.00 | 0.00 | 1 | -0.16 | +0.00 | -0.16 | +0.00 |

- **SOP lens:** NOT closed (10 non-empty bucket×cells checked, all net<=0: False)
- **Ladder lens:** ladder would have stopped at native (1h)
- **Regime/locked flags:** 1h/bull +2.77; 4h/bull +2.24; 4h/bear +1.91
- **Sweep lens:** the table above is the full matrix view.


## H04 (frozen transfer: n_rsi=2, rsi_buy=10, n_ema_exit=9, atr_stop=2.0)

| TF | Ret% | Sharpe | PF | Trades | Net$ | Bull | Sideways | Bear |
|---|---|---|---|---|---|---|---|---|
| 15m | -67.53 | -14.62 | 0.37 | 734 | -96.38 | -19.58 | -50.19 | -26.62 |
| 1h | -29.19 | -4.54 | 0.48 | 163 | -39.11 | -9.19 | -22.80 | -7.12 |
| 4h | -2.23 | -0.49 | 0.91 | 36 | -3.71 | +1.27 | -3.64 | -1.34 |
| weekly | +0.65 | 0.99 | 3.37 | 0 | +0.00 | +0.00 | +0.00 | +0.00 |

- **SOP lens:** NOT closed (9 non-empty bucket×cells checked, all net<=0: False)
- **Ladder lens:** ladder would have stopped at native (1h)
- **Regime/locked flags:** 4h/bull +1.27
- **Sweep lens:** the table above is the full matrix view.


## H05 (frozen transfer: k_band=1.0, atr_stop=1.5)

| TF | Ret% | Sharpe | PF | Trades | Net$ | Bull | Sideways | Bear |
|---|---|---|---|---|---|---|---|---|
| 15m | -70.54 | -5.60 | 0.75 | 1128 | -326.98 | -57.40 | -137.41 | -132.18 |
| 1h | -38.19 | -2.12 | 0.85 | 651 | -114.17 | -13.06 | -49.93 | -51.18 |
| 4h | -28.47 | -2.63 | 0.74 | 413 | -38.60 | +0.63 | -21.61 | -17.63 |

- **SOP lens:** NOT closed (9 non-empty bucket×cells checked, all net<=0: False)
- **Ladder lens:** ladder would have stopped at native (1h)
- **Regime/locked flags:** 4h/bull +0.63
- **Sweep lens:** the table above is the full matrix view.

