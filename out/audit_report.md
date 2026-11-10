# AUDIT REPORT (Session 3) - pre-registered

Data: BTCUSDT. Frozen variants from JOURNAL. Costs per side as labeled. Cash $100, risk 1%/trade.

## A. Cost matrix (frozen params, OOS windows only)

| Variant | 7bp Ret% | 7bp PF | 2bp Ret% | 2bp PF | 0bp Ret% | 0bp PF | Alive at 7bp? | Alive at maker? |
|---|---|---|---|---|---|---|---|---|
| H01a 1h | -10.39 | 0.75 | -2.87 | 0.94 | 0.32 | 1.03 | False | False |
| H01b 1h | -5.45 | 0.71 | -1.91 | 0.87 | -0.45 | 0.94 | False | False |
| H02a 1h | -8.84 | 0.85 | -1.48 | 1.05 | 1.63 | 1.14 | False | False |
| H02b 1h | -4.04 | 0.99 | 1.12 | 1.22 | 3.26 | 1.33 | False | True |
| H02a 4h | -10.15 | 0.60 | -8.04 | 0.67 | -7.17 | 0.70 | False | False |
| H02b 4h | -3.56 | 0.77 | -2.08 | 0.86 | -1.48 | 0.90 | False | False |
| H04a 1h | -4.16 | 0.69 | -0.24 | 1.03 | 1.38 | 1.20 | False | False |
| H04a 4h | -3.47 | 0.38 | -2.80 | 0.48 | -2.53 | 0.52 | False | False |
| H03 1h deep | 0.24 | 0.91 | 7.05 | 1.03 | 9.89 | 1.08 | False | True |
| H03 4h deep | 0.57 | 0.69 | 1.48 | 0.73 | 1.83 | 0.75 | False | False |

- Alive at 7bp: 0/10. Alive at maker 2bp: 2/10.
- Verdict rule: a dead strategy only flips to MAKER-CANDIDATE if it is alive at 2bp AND dead at 7bp.

## B. Positive control battery (freeze rule)

Documented-edge daily strategies, same walk-forward (48m train -> 12m judge Nov25-Nov26),
maker costs 2bp+slip per side, funding haircut 3bp/day while long.

### H00a_DailyMomentum (params: n_sma=100, n_roc=30)

- Test stats: Ret 4.29%, Sharpe 0.98, MaxDD -1.71%, trades 3, PF 9.16
- Funding haircut: -3.02% -> NET Ret 1.27%
- B&H same window: Ret -22.58% (net -33.50%), MaxDD -44.70%
- Gates: net_ret>0: PASS | Sharpe>0: PASS | DD better than B&H by >=10pp: PASS | trades>=3: PASS

### H00b_DailyRegime (params: n_sma=150)

- Test stats: Ret 8.32%, Sharpe 0.41, MaxDD -10.86%, trades 3, PF 0.00
- Funding haircut: -0.69% -> NET Ret 7.63%
- B&H same window: Ret -22.58% (net -33.50%), MaxDD -44.70%
- Gates: net_ret>0: PASS | Sharpe>0: PASS | DD better than B&H by >=10pp: PASS | trades>=3: PASS

**Freeze decision: BOTH PASS -> machine can certify green. Prior verdicts STAND.**

## C. Trade forensics

| Strategy | Entries checked | Condition violations | Verdict |
|---|---|---|---|
| H01a 1h | 99 | 0 | ENGINE FAITHFUL |
| H03 4h deep | 20 | 0 | ENGINE FAITHFUL |

## FINAL STAMPS

- Engine forensics: FAITHFUL -> verdicts stay valid.
- Controls: BOTH PASS -> machine can certify green. Prior verdicts STAND.
- Cost matrix: 2/10 variants were alive at maker-only costs (H06 limit-entry emulation confirmed as the frontier hypothesis if >0).

## D. ADDENDUM (post-run diagnostics, diag_audit.py)

### D1. Machine quirk found: Return vs. closed-trade ledger

- backtesting.py `Return [%]` includes unrealized PnL of a position still OPEN at the
  window cutoff (marked to market on the last bar), while `_trades`, `Profit Factor`
  and `Exposure Time [%]` count CLOSED trades only.
- H00b proof: M2M +8.32% = realized **-$5.95** (3 closed trades, all losses)
  + unrealized **+$14.26** (open long from Aug-Oct 2026 bounce).
  Under realized-only accounting H00b FAILS net_ret>0.
- Freeze outcome unchanged: H00a passed FULLY REALIZED (+$4.29 realized, $0 open),
  which alone proves the machine can certify green. H00b stamped PASS-but-fragile.
- **Standing rule (gate amendment): every future test-window verdict must split
  realized vs unrealized (open@cutoff) PnL. Return claims dominated by unrealized
  PnL are stamped FRAGILE, not certified.**

### D2. Maker-alive candidates anatomy (frozen params, 2bp vs 7bp per side)

| Variant | Costs | Ret% | Sharpe | PF | Trades | Win% | Realized $ | Unreal $ | Med hold |
|---|---|---|---|---|---|---|---|---|---|
| H02b 1h (short+VWAP) | 2bp | +1.12 | 0.23 | 1.22 | 70 | 36% | +1.12 | 0.00 | 8 bars |
| H02b 1h (short+VWAP) | 7bp | -4.04 | -0.89 | 0.99 | 70 | 36% | -4.04 | 0.00 | 8 bars |
| H03 1h deep (Donchian) | 2bp | +7.05 | 0.43 | 1.03 | 99 | 33% | +5.74 | +1.31 | 19 bars |
| H03 1h deep (Donchian) | 7bp | +0.24 | 0.02 | 0.91 | 99 | 33% | -0.96 | +1.20 | 19 bars |

- Both candidates' maker-alive status is REALIZED cash, not cutoff luck (unreal <= $1.31).
- H03 1h deep at 7bp: realized was actually NEGATIVE; the +0.24% M2M was cut-off flattered.
- Both flip to MAKER-CANDIDATE under the pre-registered rule; neither touches live money
  before robustness + fresh window + testnet.

### D3. Pre-flight bugs caught in audit.py BEFORE its first run (charter working as intended)

- Cost-matrix rows extracted timeframe from tag text (`tag.split()[-2]` -> "H01a" not
  "1h"): restructured MATRIX to explicit (tag, tf, suffix) tuples.
- DD-control gate was inverted (`<=` instead of `>=`): a strategy would have needed a
  drawdown WORSE than B&H by 10pp to pass. Fixed to `>= bhrs + 10`.
- diag_audit.py bug: this backtesting.py version's stats['End'] is a timestamp, not
  equity; final equity taken from `_equity_curve` last row instead.
