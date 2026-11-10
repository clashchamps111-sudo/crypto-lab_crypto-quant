# H07 REPORT - daily regime/momentum, H00a identity, FULL gauntlet

Pre-registered gates in header. Frozen params (no re-optimization).
Realized/unrealized split standing rule. Maker banned as bolt-on.

## H07 - frozen params n_sma=100, n_roc=30 (from H00a)

Primary = deep test year, 4 x 3m folds. 7bp/side + 3bp/day-in-market funding haircut. 150d warmup lead; trades counted if entered in-window.

| Fold | Realized $ | Funding drag $ | Net $ | Trades | Sharpe | Residual $ |
|---|---|---|---|---|---|---|
| 1 | +0.00 | +0.00 | +0.00 | 0 | -0.56 | -1.31 |
| 2 | -0.29 | +0.01 | -0.30 | 1 | 0.63 | +0.77 |
| 3 | +0.00 | +0.00 | +0.00 | 0 | -0.35 | -0.37 |
| 4 | +4.62 | +0.41 | +4.20 | 1 | 1.35 | +0.00 |
- **Pool: realized +4.33 -> net +3.90; trades 2; mean fold Sharpe 0.27; folds-net-positive 1/4; residual share 21%**
- Neighbors: 6/9 net-positive = 67%
- ETH pool net: +3.35
**Gates:**
- P1d pooled realized net-of-funding >0: PASS
- P2d pooled closed trades >= 6: FAIL
- P3d mean fold Sharpe >0: PASS
- P4d >=2/4 folds net-positive: FAIL
- P5d >=60% of 9 neighbors net-positive: PASS
- P6d ETH pooled net >0: PASS
- P7d residual <=25% of realized: PASS
- **VERDICT: MARGINAL (failed: P2d pooled closed trades >= 6; P4d >=2/4 folds net-positive)**
