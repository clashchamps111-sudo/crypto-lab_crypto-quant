# H04 Report Card

Data: Binance BTCUSDT spot-style OHLC (prices scaled by 1e6, economics identical). Costs: 0.07% per side. Cash $100, risk 1%/trade.
Walk-forward: optimize first 18 months, test = final 6 months (untouched).

| Variant | Train Ret% | Train Sharpe | TEST Ret% | TEST Sharpe | TEST MaxDD% | TEST PF | TEST Win% | TEST Trades | B&H Ret% | B&H DD% | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| H04a 1h (vwap=0; atr_stop=1.5; rsi_buy=5; time_stop=48) | -15.52 | -1.53 | -4.16 | -1.53 | -4.94 | 0.69 | 54.8 | 42 | 0.76 | -29.36 | DEAD |
| H04a 4h (vwap=0; atr_stop=1.5; rsi_buy=5; time_stop=48) | -5.92 | -1.15 | -3.47 | -1.71 | -4.27 | 0.38 | 45.5 | 11 | 0.99 | -29.25 | DEAD |

## Honest reading

- TEST column is the only truth. Train numbers are what the optimizer wished into existence.
- ALIVE (preliminary) = positive OOS return, Sharpe > 0.5, beats B&H risk-adjusted, vendeur survives next gauntlet steps (robustness nudge + 2y consistency + testnet), BEFORE any live money.
- DEAD feeds the hypothesis log; a killed hypothesis for $0 of tuition is the desk working.
