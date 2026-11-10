# H02 Report Card

Data: Binance BTCUSDT spot-style OHLC (prices scaled by 1e6, economics identical). Costs: 0.07% per side. Cash $100, risk 1%/trade.
Walk-forward: optimize first 18 months, test = final 6 months (untouched).

| Variant | Train Ret% | Train Sharpe | TEST Ret% | TEST Sharpe | TEST MaxDD% | TEST PF | TEST Win% | TEST Trades | B&H Ret% | B&H DD% | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| H02a 1h (vwap=0; atr_stop=2.5; n_fast=9) | -12.80 | -0.83 | -8.84 | -1.84 | -11.92 | 0.85 | 33.7 | 101 | 0.76 | -29.36 | DEAD |
| H02b 1h (vwap=1; atr_stop=2.5; n_fast=9) | -3.84 | -0.45 | -4.04 | -0.89 | -8.44 | 0.99 | 35.7 | 70 | 0.76 | -29.36 | DEAD |
| H02a 4h (vwap=0; atr_stop=1.5; n_fast=5) | 0.64 | 0.04 | -10.15 | -2.45 | -15.15 | 0.60 | 24.3 | 37 | 0.99 | -29.25 | DEAD |
| H02b 4h (vwap=1; atr_stop=1.5; n_fast=5) | 0.87 | 0.11 | -3.56 | -0.86 | -10.62 | 0.77 | 32.0 | 25 | 0.99 | -29.25 | DEAD |

## Honest reading

- TEST column is the only truth. Train numbers are what the optimizer wished into existence.
- ALIVE (preliminary) = positive OOS return, Sharpe > 0.5, beats B&H risk-adjusted, vendeur survives next gauntlet steps (robustness nudge + 2y consistency + testnet), BEFORE any live money.
- DEAD feeds the hypothesis log; a killed hypothesis for $0 of tuition is the desk working.
