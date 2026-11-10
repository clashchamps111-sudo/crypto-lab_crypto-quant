# H01 Report Card - Trend Pullback (EMA9/21 + RSI + regime [+VWAP])

Data: Binance BTCUSDT spot, UTC. Costs: 0.07% per side (taker + slippage + funding allowance). Cash: $100. Risk: 1%/trade. Long-only.
Walk-forward: train = first 18 months, test = last 6 months (optimizer never saw the test window).

| Variant | TF | VWAP | Params | Train Ret% | Train Sharpe | TEST Ret% | TEST Sharpe | TEST MaxDD% | TEST Trades | TEST PF | TEST Win% | B&H Ret% | B&H Sharpe | B&H DD% | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT 1h H01a | 1h | 0 | atr_stop=2.5; n_fast=13; rsi_lo=35 | -20.21 | -1.44 | -10.39 | -2.24 | -13.73 | 99 | 0.75 | 35.4 | 0.76 | 0.04 | -29.36 | MARGINAL |
| BTCUSDT 1h H01b | 1h | 1 | atr_stop=2.5; n_fast=13; rsi_lo=35 | -20.73 | -1.64 | -5.45 | -1.55 | -8.98 | 45 | 0.71 | 35.6 | 0.76 | 0.04 | -29.36 | MARGINAL |
| BTCUSDT 4h H01a | 4h | 0 | atr_stop=1.5; n_fast=13; rsi_lo=35 | 1.92 | 0.15 | -12.76 | -3.73 | -12.76 | 25 | 0.22 | 12.0 | 0.99 | 0.05 | -29.25 | MARGINAL |
| BTCUSDT 4h H01b | 4h | 1 | atr_stop=1.5; n_fast=13; rsi_lo=35 | -2.92 | -0.26 | -8.79 | -2.96 | -8.79 | 13 | 0.17 | 7.7 | 0.99 | 0.05 | -29.25 | MARGINAL |

## Gauntlet status (v0 gate)
- [x] Realistic costs modelled (taker + slippage + funding allowance)
- [x] Walk-forward: optimizer never saw the test window
- [x] Grid kept small (12 combos < 16 cap)
- [ ] Parameter robustness: nudge every arg +-25% (next session - required before testnet)
- [ ] >=100 trades over the full 2y sample (next session)
- [ ] 2-4 weeks Binance testnet forward test (only for ALIVE variants)

## Interpreting this honestly
- TEST column is the only truth. TRAIN numbers are what the optimizer wanted to believe.
- If TEST < B&H on risk-adjusted terms, holding BTC dumbly was the better trade: strategy NOT worth automating.
- MARGINAL/DEAD is data, not failure. It goes in the hypothesis log and we move to H02.

## Hypothesis queue (next)
- H02: mirrored SHORT version on perp 1x (needs futures-access confirmation from user).
- H03: Donchian 20/10 breakout, ATR stop (classic trend follower).
- H04: RSI(2) mean reversion inside bull regime (buy strength dips).
- H05: VWAP band intraday reversion (only if 1h survives costs).
