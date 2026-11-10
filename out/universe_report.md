# UNIVERSE GAUNTLET - Session 6 (pre-registered in JOURNAL)

10-symbol basket, frozen H00a identity, absolute test year 2025-11-05 + 4x3m, 150d warmup, 7bp/side + 3bp/day haircut, in-window-entry accounting.

## Per-symbol fold pools

| Symbol | Realized $ | Net $ | Trades | Mean fold Sharpe | Folds net-pos |
|---|---|---|---|---|---|
| BTCUSDT | +4.33 | +3.90 | 2 | 0.27 | 1/4 |
| ETHUSDT | +3.72 | +3.35 | 9 | -0.64 | 1/4 |
| BNBUSDT | +3.10 | +2.48 | 5 | 0.12 | 1/4 |
| SOLUSDT | +5.54 | +5.14 | 4 | -0.48 | 1/4 |
| XRPUSDT | -2.06 | -2.29 | 8 | -1.22 | 0/4 |
| DOGEUSDT | -3.16 | -3.29 | 7 | -0.22 | 0/4 |
| ADAUSDT | -1.27 | -1.48 | 6 | -0.87 | 0/4 |
| LINKUSDT | +4.43 | +4.05 | 5 | -0.70 | 1/4 |
| AVAXUSDT | +2.99 | +2.74 | 4 | -0.14 | 1/4 |
| TRXUSDT | -5.37 | -6.08 | 11 | -0.24 | 0/4 |
- Basket pooled net: +8.52 across 61 closed trades
- Net-positive symbols: 6/10 (BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, LINKUSDT, AVAXUSDT)
- Neighbors: 3/9 basket-net-positive = 33%
- Continuity: BTCUSDT: target +3.90, got +3.90 (OK); ETHUSDT: target +3.35, got +3.35 (OK)

**Gates:**
- B1 basket pooled net >0: PASS
- B2 >=60% symbols net-positive: PASS
- B3 >=60% of 9 neighbors net-positive (basket): FAIL
- B4 mean per-symbol net >0: PASS
- B5 BTC/ETH continuity within +-0.5: PASS
- **VERDICT: MARGINAL (failed: B3 >=60% of 9 neighbors net-positive (basket))**

## Per-symbol fold detail

### BTCUSDT
| Fold | Realized | Drag | Net | Trades | Sharpe | Residual |
|---|---|---|---|---|---|---|
| 1 | +0.00 | +0.00 | +0.00 | 0 | -0.56 | -1.31 |
| 2 | -0.29 | +0.01 | -0.30 | 1 | 0.63 | +0.77 |
| 3 | +0.00 | +0.00 | +0.00 | 0 | -0.35 | -0.37 |
| 4 | +4.62 | +0.41 | +4.20 | 1 | 1.35 | +0.00 |

### ETHUSDT
| Fold | Realized | Drag | Net | Trades | Sharpe | Residual |
|---|---|---|---|---|---|---|
| 1 | -0.31 | +0.01 | -0.31 | 2 | -1.21 | -1.18 |
| 2 | -0.67 | +0.02 | -0.69 | 2 | -1.18 | -0.16 |
| 3 | +0.00 | +0.00 | +0.00 | 0 | -1.18 | -0.95 |
| 4 | +4.70 | +0.35 | +4.35 | 5 | 0.99 | +0.00 |

### BNBUSDT
| Fold | Realized | Drag | Net | Trades | Sharpe | Residual |
|---|---|---|---|---|---|---|
| 1 | +0.00 | +0.00 | +0.00 | 0 | -0.18 | -1.15 |
| 2 | +0.00 | +0.00 | +0.00 | 0 | n/a | +0.00 |
| 3 | -1.38 | +0.15 | -1.53 | 2 | -0.56 | -0.00 |
| 4 | +4.48 | +0.47 | +4.01 | 3 | 1.09 | +0.00 |

### SOLUSDT
| Fold | Realized | Drag | Net | Trades | Sharpe | Residual |
|---|---|---|---|---|---|---|
| 1 | +0.00 | +0.00 | +0.00 | 0 | -1.76 | -3.08 |
| 2 | +0.00 | +0.00 | +0.00 | 0 | n/a | +0.00 |
| 3 | -0.94 | +0.06 | -1.00 | 3 | -0.84 | -0.00 |
| 4 | +6.48 | +0.34 | +6.14 | 1 | 1.15 | -0.21 |

### XRPUSDT
| Fold | Realized | Drag | Net | Trades | Sharpe | Residual |
|---|---|---|---|---|---|---|
| 1 | -0.92 | +0.01 | -0.93 | 1 | -2.56 | -1.72 |
| 2 | +0.00 | +0.00 | +0.00 | 0 | -1.59 | -0.94 |
| 3 | -0.56 | +0.05 | -0.60 | 2 | -0.52 | -0.00 |
| 4 | -0.58 | +0.18 | -0.76 | 5 | -0.21 | -0.00 |

### DOGEUSDT
| Fold | Realized | Drag | Net | Trades | Sharpe | Residual |
|---|---|---|---|---|---|---|
| 1 | +0.00 | +0.00 | +0.00 | 0 | -1.30 | -2.01 |
| 2 | +0.00 | +0.00 | +0.00 | 0 | 2.21 | +1.46 |
| 3 | +0.00 | +0.00 | +0.00 | 0 | 0.02 | +0.03 |
| 4 | -3.16 | +0.13 | -3.29 | 7 | -1.83 | -0.00 |

### ADAUSDT
| Fold | Realized | Drag | Net | Trades | Sharpe | Residual |
|---|---|---|---|---|---|---|
| 1 | +0.00 | +0.00 | +0.00 | 0 | -1.14 | -0.83 |
| 2 | +0.00 | +0.00 | +0.00 | 0 | n/a | +0.00 |
| 3 | -1.10 | +0.03 | -1.13 | 2 | -1.39 | +0.00 |
| 4 | -0.18 | +0.17 | -0.34 | 4 | -0.07 | -0.00 |

### LINKUSDT
| Fold | Realized | Drag | Net | Trades | Sharpe | Residual |
|---|---|---|---|---|---|---|
| 1 | +0.00 | +0.00 | +0.00 | 0 | -1.62 | -1.01 |
| 2 | -0.23 | +0.00 | -0.24 | 1 | -1.37 | +0.00 |
| 3 | -0.70 | +0.08 | -0.78 | 3 | -0.65 | -0.23 |
| 4 | +5.37 | +0.30 | +5.07 | 1 | 0.84 | -0.74 |

### AVAXUSDT
| Fold | Realized | Drag | Net | Trades | Sharpe | Residual |
|---|---|---|---|---|---|---|
| 1 | +0.00 | +0.00 | +0.00 | 0 | -0.61 | -1.01 |
| 2 | +0.00 | +0.00 | +0.00 | 0 | n/a | +0.00 |
| 3 | -0.57 | +0.05 | -0.62 | 3 | -0.60 | -0.00 |
| 4 | +3.57 | +0.20 | +3.36 | 1 | 0.81 | +0.00 |

### TRXUSDT
| Fold | Realized | Drag | Net | Trades | Sharpe | Residual |
|---|---|---|---|---|---|---|
| 1 | -2.04 | +0.21 | -2.25 | 3 | -1.46 | -1.42 |
| 2 | -0.42 | +0.01 | -0.43 | 1 | 0.75 | +2.83 |
| 3 | +0.00 | +0.00 | +0.00 | 0 | 1.23 | +3.93 |
| 4 | -2.91 | +0.48 | -3.40 | 7 | -1.47 | +0.00 |
