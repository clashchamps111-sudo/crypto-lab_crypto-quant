# POSITIVE-CONTROLS RE-RUN SEAL (Session 7 opener)

Provenance: standing rule 'controls re-run after any harness change'.
Triggers since S3: strategies.py/indicators.py grew (additive only),
5 new runners added; engine constants untouched (verified in header).
Method: audit.positive_controls() called EXACTLY as in S3; zero edits
to audit.py, strategies.py control classes, indicators core, config.

Expected S3 stamp: H00a Ret +4.29% (net +1.27%) 4/4 gates; H00b Ret +8.32% (net +7.63%) 4/4 gates; BOTH PASS.

## Data integrity

- BTCUSDT_1h_deep: 43799 rows, 2021-11-05 19:00:00 -> 2026-11-04 18:00:00
- funding_BTCUSDT.csv: 5481 prints

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

## Comparison vs Session 3 stamp

- H00a: S3: Ret +4.29 net +1.27 | re-run: Ret +4.29 net +1.27, gates: net_ret>0: PASS | Sharpe>0: PASS | DD better than B&H by >=10pp: PASS | trades>=3: PASS

### H00b_DailyRegime (params: n_sma=150)

- Test stats: Ret 8.32%, Sharpe 0.41, MaxDD -10.86%, trades 3, PF 0.00
- Funding haircut: -0.69% -> NET Ret 7.63%
- B&H same window: Ret -22.58% (net -33.50%), MaxDD -44.70%
- Gates: net_ret>0: PASS | Sharpe>0: PASS | DD better than B&H by >=10pp: PASS | trades>=3: PASS

**Freeze decision: BOTH PASS -> machine can certify green. Prior verdicts STAND.**

- H00b: S3: Ret +8.32 net +7.63 | re-run: Ret +8.32 net +7.63, gates: net_ret>0: PASS | Sharpe>0: PASS | DD better than B&H by >=10pp: PASS | trades>=3: PASS

**Freeze decision: BOTH PASS -> machine can certify green. Prior verdicts STAND.**

- Freeze decision (re-run): BOTH PASS -> machine can certify green. Prior verdicts STAND.
- H00a identity match (params/Ret/NET all within 0.005): YES

**SEAL: PASS - harness certified green; all Session 3-6 verdicts STAND.**

Integrity: BTC deep 43799 rows, funding 5481 prints.
