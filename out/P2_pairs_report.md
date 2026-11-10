# P2 PAIRS REPORT (Session 10.6.1, pre-registered)

Data 2021-11-05 19:00:00 -> 2026-11-05 20:00:00 (1h); train [start -> 2025-11-05); judge [2025-11-05 -> end) ~ 1.00y.
Legs = USDT-M perps both sides; per $100 GROSS notional
(legs $50/$50; per-capital = /2 conservative, hedged-margin
advantage unmodeled). Costs: 28bp matched RT (7bp/side x4) +
3bp/day gross haircut + signed net funding per print on entry
notional (exit-bar print included). Realized-only verdicts.

## Pair screen (TRAIN-ONLY)

EG-ADF t on daily OLS-hedged train spread; qualify: t < -1.5 AND hourly-return corr >= 0.6; rank most-negative t.

| A | B | ADF t | corr | HL (d) | qual |
|---|---|---|---|---|---|
| LINKUSDT | TRXUSDT | -3.17 | +0.51 | 65.9 | - |
| ADAUSDT | TRXUSDT | -3.07 | +0.50 | 88.6 | - |
| SOLUSDT | LINKUSDT | -3.04 | +0.71 | 56.1 | YES |
| DOGEUSDT | TRXUSDT | -3.03 | +0.46 | 66.6 | - |
| ETHUSDT | SOLUSDT | -2.74 | +0.74 | 71.4 | YES |
| ETHUSDT | TRXUSDT | -2.73 | +0.52 | 86.9 | - |
| BTCUSDT | TRXUSDT | -2.66 | +0.51 | 62.8 | - |
| ETHUSDT | LINKUSDT | -2.61 | +0.79 | 73.0 | YES |
| DOGEUSDT | LINKUSDT | -2.58 | +0.69 | 74.8 | YES |
| ADAUSDT | AVAXUSDT | -2.51 | +0.73 | 85.1 | YES |
| XRPUSDT | TRXUSDT | -2.45 | +0.48 | 80.0 | - |
| ETHUSDT | BNBUSDT | -2.41 | +0.75 | 95.8 | YES |
| ADAUSDT | LINKUSDT | -2.37 | +0.76 | 97.5 | YES |
| BNBUSDT | TRXUSDT | -2.34 | +0.50 | 99.1 | - |
| ETHUSDT | XRPUSDT | -2.30 | +0.65 | 117.1 | YES |
| BTCUSDT | LINKUSDT | -2.27 | +0.72 | 111.2 | YES |
| SOLUSDT | TRXUSDT | -2.20 | +0.47 | 142.0 | - |
| BTCUSDT | DOGEUSDT | -2.18 | +0.68 | 111.9 | YES |
| ETHUSDT | DOGEUSDT | -2.14 | +0.70 | 115.5 | YES |
| SOLUSDT | DOGEUSDT | -2.13 | +0.64 | 115.7 | YES |
| BNBUSDT | DOGEUSDT | -2.13 | +0.65 | 90.3 | YES |
| AVAXUSDT | TRXUSDT | -2.13 | +0.48 | 155.1 | - |
| BTCUSDT | BNBUSDT | -1.98 | +0.73 | 128.6 | YES |
| DOGEUSDT | ADAUSDT | -1.93 | +0.69 | 135.3 | YES |
| XRPUSDT | DOGEUSDT | -1.83 | +0.62 | 133.7 | YES |
| LINKUSDT | AVAXUSDT | -1.78 | +0.75 | 146.7 | YES |
| BTCUSDT | ETHUSDT | -1.72 | +0.84 | 198.7 | YES |
| BTCUSDT | SOLUSDT | -1.70 | +0.72 | 191.8 | YES |
| BNBUSDT | XRPUSDT | -1.65 | +0.60 | 169.5 | YES |
| BTCUSDT | XRPUSDT | -1.55 | +0.63 | 211.3 | YES |
| ETHUSDT | ADAUSDT | -1.51 | +0.74 | 193.1 | YES |
| SOLUSDT | XRPUSDT | -1.46 | +0.60 | 285.8 | - |
| DOGEUSDT | AVAXUSDT | -1.43 | +0.66 | 215.0 | - |
| BNBUSDT | SOLUSDT | -1.40 | +0.68 | 183.1 | - |
| SOLUSDT | ADAUSDT | -1.31 | +0.70 | 301.9 | - |
| BNBUSDT | LINKUSDT | -1.28 | +0.71 | 199.3 | - |
| XRPUSDT | LINKUSDT | -1.26 | +0.65 | 253.4 | - |
| ETHUSDT | AVAXUSDT | -1.19 | +0.74 | 222.0 | - |
| XRPUSDT | ADAUSDT | -0.69 | +0.73 | 655.9 | - |
| BTCUSDT | ADAUSDT | -0.61 | +0.71 | 918.9 | - |
| BNBUSDT | ADAUSDT | -0.39 | +0.69 | 778.5 | - |
| XRPUSDT | AVAXUSDT | -0.24 | +0.62 | 1529.2 | - |
| SOLUSDT | AVAXUSDT | -0.24 | +0.74 | 1935.3 | - |
| BNBUSDT | AVAXUSDT | +0.25 | +0.69 | inf | - |
| BTCUSDT | AVAXUSDT | +0.41 | +0.71 | inf | - |

- qualifiers: 22/45; selected top 6 by most-negative t.

## SOLUSDT / LINKUSDT  (t -3.04, corr +0.71, HL 56.1d)

| W | beta | z_in | train net $ | train trips |
|---|---|---|---|---|
| 30d | unit | 2.00 | -43.82 | 222 |
| 30d | unit | 2.50 | -35.84 | 200 |
| 30d | ols | 2.00 | -290.07 | 1835 |
| 30d | ols | 2.50 | -288.59 | 1831 |
| 90d | unit | 2.00 | -41.50 | 256 |
| 90d | unit | 2.50 | -37.90 | 247 |
| 90d | ols | 2.00 | -88.53 | 472 |
| 90d | ols | 2.50 | -83.47 | 467 |

- TRAIN PICK: W=30d beta=unit z_in=2.50 (train net -35.84$ on 200 trips)

**JUDGE 30d/unit/z2.50: trips 53 | net -12.33$ (-12.31%/yr gross) | PF 0.03 | avg/trade -0.233 | fund +0.45$ hair +3.98$ | MDD -12.33$ | exits {'z-out': 15, 'z-stop': 38}**

- Neighbors (informational): z2.25: 53 trips -12.02$ (MDD -12.02); z2.75: 52 trips -12.32$ (MDD -12.32)
- Regime split (mandatory lens): bull -5.21$ (30t); sideways -3.82$ (12t); bear -3.30$ (11t)

## ETHUSDT / SOLUSDT  (t -2.74, corr +0.74, HL 71.4d)

| W | beta | z_in | train net $ | train trips |
|---|---|---|---|---|
| 30d | unit | 2.00 | -40.15 | 240 |
| 30d | unit | 2.50 | -38.17 | 229 |
| 30d | ols | 2.00 | -263.95 | 1694 |
| 30d | ols | 2.50 | -261.07 | 1685 |
| 90d | unit | 2.00 | -47.05 | 269 |
| 90d | unit | 2.50 | -47.15 | 266 |
| 90d | ols | 2.00 | -80.62 | 503 |
| 90d | ols | 2.50 | -79.38 | 501 |

- TRAIN PICK: W=30d beta=unit z_in=2.50 (train net -38.17$ on 229 trips)

**JUDGE 30d/unit/z2.50: trips 54 | net -10.64$ (-10.62%/yr gross) | PF 0.05 | avg/trade -0.197 | fund -0.05$ hair +3.71$ | MDD -11.92$ | exits {'z-out': 13, 'z-stop': 41}**

- Neighbors (informational): z2.25: 55 trips -10.73$ (MDD -11.98); z2.75: 52 trips -10.44$ (MDD -11.76)
- Regime split (mandatory lens): bull -3.21$ (17t); sideways -3.64$ (20t); bear -3.78$ (17t)

## ETHUSDT / LINKUSDT  (t -2.61, corr +0.79, HL 73.0d)

| W | beta | z_in | train net $ | train trips |
|---|---|---|---|---|
| 30d | unit | 2.00 | -46.23 | 252 |
| 30d | unit | 2.50 | -44.84 | 235 |
| 30d | ols | 2.00 | -269.21 | 1707 |
| 30d | ols | 2.50 | -267.38 | 1705 |
| 90d | unit | 2.00 | -36.35 | 117 |
| 90d | unit | 2.50 | -32.73 | 109 |
| 90d | ols | 2.00 | -82.73 | 531 |
| 90d | ols | 2.50 | -80.35 | 528 |

- TRAIN PICK: W=90d beta=unit z_in=2.50 (train net -32.73$ on 109 trips)

**JUDGE 90d/unit/z2.50: trips 37 | net -11.36$ (-11.34%/yr gross) | PF 0.03 | avg/trade -0.307 | fund -0.12$ hair +2.50$ | MDD -13.00$ | exits {'z-out': 7, 'z-stop': 30}**

- Neighbors (informational): z2.25: 38 trips -12.03$ (MDD -13.66); z2.75: 36 trips -11.10$ (MDD -12.74)
- Regime split (mandatory lens): bull -5.47$ (19t); sideways -3.49$ (17t); bear -2.40$ (1t)

## DOGEUSDT / LINKUSDT  (t -2.58, corr +0.69, HL 74.8d)

| W | beta | z_in | train net $ | train trips |
|---|---|---|---|---|
| 30d | unit | 2.00 | -70.36 | 390 |
| 30d | unit | 2.50 | -64.58 | 370 |
| 30d | ols | 2.00 | -278.30 | 1723 |
| 30d | ols | 2.50 | -277.29 | 1717 |
| 90d | unit | 2.00 | -59.42 | 340 |
| 90d | unit | 2.50 | -52.56 | 329 |
| 90d | ols | 2.00 | -121.80 | 733 |
| 90d | ols | 2.50 | -114.12 | 727 |

- TRAIN PICK: W=90d beta=unit z_in=2.50 (train net -52.56$ on 329 trips)

**JUDGE 90d/unit/z2.50: trips 6 | net -6.01$ (-6.00%/yr gross) | PF 0.00 | avg/trade -1.001 | fund -0.02$ hair +4.10$ | MDD -6.01$ | exits {'z-out': 3, 'time-stop': 3}**

- Neighbors (informational): z2.25: 6 trips -5.34$ (MDD -5.34); z2.75: 4 trips -3.50$ (MDD -3.50)
- Regime split (mandatory lens): bull -1.59$ (2t); sideways -3.53$ (3t); bear -0.89$ (1t)

## ADAUSDT / AVAXUSDT  (t -2.51, corr +0.73, HL 85.1d)

| W | beta | z_in | train net $ | train trips |
|---|---|---|---|---|
| 30d | unit | 2.00 | -53.62 | 235 |
| 30d | unit | 2.50 | -44.89 | 209 |
| 30d | ols | 2.00 | -274.00 | 1717 |
| 30d | ols | 2.50 | -273.29 | 1714 |
| 90d | unit | 2.00 | -61.66 | 332 |
| 90d | unit | 2.50 | -56.82 | 323 |
| 90d | ols | 2.00 | -102.49 | 607 |
| 90d | ols | 2.50 | -99.13 | 603 |

- TRAIN PICK: W=30d beta=unit z_in=2.50 (train net -44.89$ on 209 trips)

**JUDGE 30d/unit/z2.50: trips 89 | net -17.04$ (-17.01%/yr gross) | PF 0.01 | avg/trade -0.191 | fund +0.02$ hair +3.80$ | MDD -17.04$ | exits {'z-out': 14, 'z-stop': 75}**

- Neighbors (informational): z2.25: 92 trips -18.12$ (MDD -18.43); z2.75: 85 trips -15.37$ (MDD -15.37)
- Regime split (mandatory lens): bull -0.95$ (2t); sideways -8.60$ (50t); bear -7.48$ (37t)

## ETHUSDT / BNBUSDT  (t -2.41, corr +0.75, HL 95.8d)

| W | beta | z_in | train net $ | train trips |
|---|---|---|---|---|
| 30d | unit | 2.00 | -48.68 | 217 |
| 30d | unit | 2.50 | -40.21 | 196 |
| 30d | ols | 2.00 | -267.50 | 1659 |
| 30d | ols | 2.50 | -265.82 | 1652 |
| 90d | unit | 2.00 | -21.05 | 81 |
| 90d | unit | 2.50 | -16.11 | 73 |
| 90d | ols | 2.00 | -107.29 | 625 |
| 90d | ols | 2.50 | -103.38 | 621 |

- TRAIN PICK: W=90d beta=unit z_in=2.50 (train net -16.11$ on 73 trips)

**JUDGE 90d/unit/z2.50: trips 34 | net -7.72$ (-7.71%/yr gross) | PF 0.06 | avg/trade -0.227 | fund -0.02$ hair +2.74$ | MDD -8.17$ | exits {'z-stop': 30, 'z-out': 2, 'time-stop': 2}**

- Neighbors (informational): z2.25: 34 trips -7.36$ (MDD -7.81); z2.75: 34 trips -8.18$ (MDD -8.65)
- Regime split (mandatory lens): bull -2.60$ (2t); sideways -0.59$ (1t); bear -4.53$ (31t)

## Verdict

- Frozen winners run: 6; ALIVE (net>0 AND >=8 judge trades): 0
- Pooled judge book: -65.10$ / 1.00y = -64.99%/yr gross (273 trades total)

### Four-bar table (per $100 GROSS notional; capital = /2)

| Bar | Definition | Best winner (DOGEUSDT/LINKUSDT) | Pooled six |
|---|---|---|---|
| A any-positive | net > 0 | FAIL (-6.00) | FAIL (-64.99) |
| B beats certified | >= 4.77%/yr | FAIL (-6.00) | FAIL (-64.99) |
| C beats always-in | >= 6.82%/yr | FAIL (-6.00) | FAIL (-64.99) |
| D double-digit capital | >= 20.0%/yr | FAIL (-6.00) | FAIL (-64.99) |

**P2 FAMILY VERDICT: CLOSED - no winner cleared (net>0 AND >=8 judge trades)**
