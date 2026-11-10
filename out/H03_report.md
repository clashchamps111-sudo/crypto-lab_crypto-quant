# H03 Report Card

Data: Binance BTCUSDT spot-style OHLC (prices scaled by 1e6, economics identical). Costs: 0.07% per side. Cash $100, risk 1%/trade.
Walk-forward: optimize first 48 months, test = final 12 months (untouched).

| Variant | Train Ret% | Train Sharpe | TEST Ret% | TEST Sharpe | TEST MaxDD% | TEST PF | TEST Win% | TEST Trades | B&H Ret% | B&H DD% | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| H03a 1h (vwap=0; atr_stop=3; n_enter=20; n_exit=10) | 38.95 | 0.52 | 0.24 | 0.02 | -16.85 | 0.91 | 33.3 | 99 | -22.67 | -45.35 | MARGINAL |
| H03a 4h (vwap=0; atr_stop=2; n_enter=40; n_exit=10) | 79.42 | 1.28 | 0.57 | 0.05 | -10.81 | 0.69 | 25.0 | 20 | -22.61 | -45.16 | DEAD |

## Honest reading

- TEST column is the only truth. Train numbers are what the optimizer wished into existence.
- ALIVE (preliminary) = positive OOS return, Sharpe > 0.5, beats B&H risk-adjusted, vendeur survives next gauntlet steps (robustness nudge + 2y consistency + testnet), BEFORE any live money.
- DEAD feeds the hypothesis log; a killed hypothesis for $0 of tuition is the desk working.
