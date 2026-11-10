# H05 REPORT - VWAP-band intraday reversion (1h)

Pre-registered two-stage battery (header). Costs 7bp/side everywhere.
Realized/unrealized split per standing rule. VWAP arrays bar-local,
UTC-day anchored, first 3h of each day masked.

### Stage 1 - frozen winner: k_band=1, atr_stop=1.5, time_stop=8

- TRAIN (48m): Ret -99.32%, Sharpe -6.69, trades 4387, realized $-99.32
- TEST (12m judge, 7bp/side): Ret -38.19%, Sharpe -2.37, MaxDD -46.77%, PF 0.85, trades 651, Win 41.8%, realized $-38.19, unreal $+0.00
- B&H same window: Ret -22.67%, Sharpe -0.60, DD -45.35%
- **STAGE 1 VERDICT: DEAD**

### Stage 2 skipped (only-if-alive rule)

Stage 1 said DEAD - the fold gauntlet does not run unless the
walk-forward judge clears. One-pass discipline preserved.
