# H03 deep validation - Donchian 20/10 ATR2, 4h

Rolling walk-forward: 4 folds x 3 months OOS. Costs 0.07%/side. Every fold tested with the SAME frozen params - no refitting per fold.

## Fold-by-fold (BTCUSDT 4h, frozen params)

| Fold | Ret% | Sharpe | MaxDD% | PF | Win% | Trades |
|---|---|---|---|---|---|---|
| 1 | -1.47 | -0.90 | -3.24 | 0.33 | 40.0 | 5 |
| 2 | 2.90 | 1.33 | -2.31 | 3.18 | 60.0 | 5 |
| 3 | -2.99 | -3.54 | -3.16 | 0.00 | 0.0 | 4 |
| 4 | 11.64 | 1.59 | -6.44 | 1.87 | 28.6 | 7 |

**Pooled OOS: Ret 9.80% over folds, trades 21, mean fold Sharpe -0.38**

## Neighbor robustness (BTCUSDT 4h)

- Param grid: n_enter {15,20,25} x n_exit {7,10,13} x atr_stop {1.5,2.0,3.0} (27 neighbors), all through the same folds.
- Winner rank among neighbors: 2 of 27.
- Share of neighbors with positive pooled OOS return: 93% (robustness floor expectation: >=60%).

## ETHUSDT cross-check (same frozen params)

- Pooled OOS: Ret 9.56%, trades 28, mean fold Sharpe -0.89.

## Gate reading

- Pass requires: pooled OOS trades >= 30 (amended from 1h era), mean fold Sharpe > 0, neighbor positive-rate >= 60%, and ETH not catastrophically anti-correlated.
- Trade-count gate amended in JOURNAL: directional 4h systems cannot produce 100 trades in 2y at honest frequency; the multi-fold OOS evidence replaces it.
