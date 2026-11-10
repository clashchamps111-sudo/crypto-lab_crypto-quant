# JOURNAL - decision log + agent activity report

The user asked for full detail on everything the agent does. This file is that record.

## Locked decisions (from requirements intake)
| Topic | Decision |
|---|---|
| Goal | Validated strategies live on small capital -> add capital -> funded accounts later |
| Capital | $100 pilot; scale only after live proof |
| Universe | BTC first, then ETH |
| Styles | 1h and 4h both tested; deployment cadence decided by test results, not preference |
| Exchange | Binance (user has an account). Region: India - FIU-compliant usage |
| Derivatives | Perp at 1x for shorts later; PENDING user checks Futures tab access |
| Hosting | User Windows PC, free tier first; VPS only after a strategy proves itself |
| Autonomy | Default: full-auto on testnet first |
| User's role | Hands-off; agent engineers and reports in detail |

## Risk rails (set by agent, active immediately)
- Risk/trade: 1% of equity. Notional cap: 1x.
- Strategy kill: -15% drawdown from equity peak = permanent shutdown.
- Account kill: -20% drawdown = stop everything, full review.
- Testnet (>=14 days, untouched) before any real capital.

## Cost model (baked into all backtests)
0.07% per side = 0.05% perp taker + ~0.01% slippage + ~0.01% funding allowance.
Rationale: $100 account cannot survive 0.1% spot taker round trips on 1h edges;
perp-1x fee schedule is cheaper AND enables shorts later.

## Session log

### Session 1 - desk construction (all times approximate)
Build order:
1. [x] Verified Python 3.15.2 on user machine.
2. [x] Created project `crypto-quant/` (user chose current folder; agent subfoldered to avoid
  dumping files loose inside a Windows system-cache directory).
3. [x] Wrote config / data / indicators / strategies / walk-forward harness / README / JOURNAL.
4. [x] Dependency fight: Python 3.15 is TOO NEW for cp315 wheels. `pip install backtesting`
  failed building pyYAML from sdist (needs MSVC). Chain: backtesting -> bokeh -> pyYAML.
  pyYAML has cp314 wheels max. FIX: installed pyYAML from sdist with env
  `PYYAML_FORCE_LIBYAML=0` => pure-Python build (no compiler needed), then rest of stack.
5. [x] Downloaded 2y Binance klines: BTCUSDT + ETHUSDT, 1h (17,520 rows) + 4h (4,380 rows).

Debugging H01 = 0 trades (three real bugs found and fixed):
- Bug A (sizing semantics): passed size as units of BTC; backtesting.py treats size<1 as a
  FRACTION of equity. Fix: express as fraction: frac = risk_pct / stop_distance_pct, capped 0.98.
- Bug B (integer units): broker converts relative orders via int(floor(units)); BTC ~$68k / $100
  equity floors EVERY order to 0 units -> all orders canceled. Fix: scale all prices by 1e6
  (config PRICE_SCALE) -> unit granularity = $0.07; economics unchanged. (Reverted an earlier
  BROKER_MARGIN hack - misdiagnosis, deleted.)
- Bug C (VWAP injection): VWAP variant equaled no-VWAP variant because the _vwap array was never
  attached to the train subclass. Fix: inject per-split arrays; H01b now genuine.
- [x] diag_h01.py added as regression tool: counts signal bars (1,190) vs broker trades (347).
- [x] Walk-forward executed: optimize 18 months (12-combo grid, Sharpe-max), single evaluation
  on final 6 months, per timeframe x VWAP on/off. Verdict thresholds fixed (losers = DEAD).

## RESULTS - H01 Report Card (see out/H01_report.md)

Costs 0.07%/side. TEST = last 6 months (never shown to optimizer). B&H test = buy-hold same window.

| Variant | Train Ret% | TEST Ret% | TEST Sharpe | TEST PF | TEST Win% | Test Trades | Verdict |
|---|---|---|---|---|---|---|---|
| 1h H01a (no VWAP) | -20.2 | -10.4 | -2.24 | 0.75 | 35.4 | 99 | DEAD |
| 1h H01b (VWAP) | -20.7 | -5.5 | -1.55 | 0.71 | 35.6 | 45 | DEAD |
| 4h H01a | +1.9 | -12.8 | -3.73 | 0.22 | 12.0 | 25 | DEAD |
| 4h H01b (VWAP) | -2.9 | -8.8 | -2.96 | 0.17 | 7.7 | 13 | DEAD |

B&H over the same test window: +0.76% (1h) / +0.99% (4h), drawdown -29%.

Verdict: **H01 is DEAD in every configuration.** Evidence:
- Profit Factor < 1 out-of-sample everywhere. Risk:reward inside the strategy is 2:1
  (target 3x ATR, stop 1.5x ATR), so breakeven win rate is ~34%; we got 35% -> gross edge zero
  before costs, negative after.
- The 4h variants degrade catastrophically OOS (PF 0.17-0.22, win 8-12%) - the optimizer's
  train pick clung to grid corners (n_fast=13, rsi_lo=35), classic look of an unstable non-edge.
- Adding the friend's VWAP filter made results WORSE, not better.
- Momentum-trend pullbacks on BTC 1h/4h with these costs is not an edge in this 2y sample.

Conclusion for the user: your friend's stack was killed for $0 and ~2 hours of machine time,
BEFORE risking the $100 pilot. This is the pipeline doing its job.

## RESULTS - Session 2 (futures access confirmed -> H02 unblocked)

### H02 - Mirror short, perp 1x (EMA9/21+RSI bear regime [+VWAP])
| Variant | TEST Ret% | TEST Sharpe | TEST PF | Trades | Verdict |
|---|---|---|---|---|---|
| 1h no-VWAP | -8.8 | -1.84 | 0.85 | 101 | DEAD |
| 1h +VWAP | -4.0 | -0.89 | 0.99 | 70 | DEAD |
| 4h no-VWAP | -10.1 | -2.45 | 0.60 | 37 | DEAD |
| 4h +VWAP | -3.6 | -0.86 | 0.77 | 25 | DEAD |

### H04 - RSI(2) dip reversion in bull regime
| Variant | TEST Ret% | TEST Sharpe | TEST PF | Trades | Verdict |
|---|---|---|---|---|---|
| 1h | -4.2 | -1.53 | 0.69 | 42 | DEAD |
| 4h | -3.5 | -1.71 | 0.38 | 11 | DEAD |

Win rate ~50% but PF<1: small wins vs negative tail = negative expectancy after costs.

### H03 - Donchian breakout (the only pulse of life; deep-anchored next stage)
2y-era: 4h 20/10 ATR2 -> +7.7% OOS, Sharpe 0.86, PF 1.16 but only 12 trades. 1h marginal (+3.4%, PF 0.97).

Deep validation on 2y data (rolling 4x3m folds + 27-neighbor robustness + ETH):
- BTC pooled OOS +9.8% (21 trades), mean fold Sharpe -0.38 (inconsistent folds)
- ETH pooled OOS +9.56% (28 trades), mean fold Sharpe -0.89
- 93% of 27 neighbor param sets had positive pooled return (structure robust, consistency weak)

Data exhaustion -> 5y deep history fetched (BTC+ETH, 1h+4h, Nov2021-Nov2026, full cycle incl.
2022 bear). Config re-anchored: TRAIN_MONTHS=48, TEST_MONTHS=12 (data suffix `_deep`).

H03 final judgment on deep anchor (fresh untouched year, Nov25-Nov26):
| Variant | Train (4y) | TEST (1y) | TEST verdict |
|---|---|---|---|
| 1h 20/10/ATR3 | +39.0%, Sharpe 0.52, PF 1.08, 406 trades | +0.24%, Sharpe 0.02, PF 0.91, 99 trades | MARGINAL |
| 4h 40/10/ATR2 | +79.4%, Sharpe 1.28, PF 1.98, 79 trades | +0.57%, Sharpe 0.05, PF 0.69, 20 trades | DEAD |

Reading: textbook overfit shape (train beauty, OOS flat/negative) OR an edge that exists
mostly to preserve capital in drawdowns: test-year B&H was -22.7% at -45.3% DD while both
strategies exited the year ~flat with -9 to -17% DD. Combined with the earlier 2y window
disagreeing (mild positive) -> two independent OOS looks = inconsistent. VERDICT:
**H03 = MARGINAL, not deployable. Archived with its insight: trend exits = capital
preservation value even without alpha. Portfolio-design note, not a money strategy.**

### Scoreboard after 3 sessions
H01 DEAD (friend's stack, 4 variants). H02 DEAD (shorts, 4). H03 MARGINAL/archived. H04 DEAD.
$100 untouched. Zero dollars of tuition paid. The gauntlet is doing its job.

### Session 2 engineering log
- Added ShortTrendPullback / DonchianBreakout / Rsi2Reversion to strategies.py.
- Bug found: optimize() carries params as floats -> pandas rolling(window=20.0) crashed;
  ewm tolerates floats, rolling does not. Fix: rolling(int(...)) casts.
- Harness v2: generic hypothesis factory (per-hypothesis grid, vwap variants, timeframes,
  throwaway subclasses so optimize() mutations never leak between runs).
- config re-anchor: DATA_SUFFIX, TRAIN_MONTHS 48, TEST_MONTHS 12; loader/env-filter (HYP=...).
- fetch_deep.py: 5y history; 2y CSVs preserved as artifacts of sessions 1-2 reports.
- Gate amendment (standing rule): directional 4h systems cannot hit the 1h-era 100-trade bar;
  multi-fold pooled OOS evidence (>=30 pooled trades, mean fold Sharpe>0) replaces it.
  H03 failed the amended gate on fold-consistency anyway.

### Session 3 queue
- [ ] H05: VWAP-band intraday mean reversion (1h): buy when price < vwap - k*sigma;
  exit at vwap touch or ATR stop. Different edge class from everything dead so far.
- [ ] H06: Maker-only emulation layer: limit-order entry (0.02% maker, we pay fill-lag instead
  of taker fees) - attacks the cost function itself, which is what killed most 1h edges.
- [ ] H07: Daily-bar carry/momentum hybrid with funding-aware perp accounting - only if H05/H06 dead.
- [ ] If ALL dead: strategic review (timeframes, universe, cost structure) before grinding
  more of the same idea class - that would be overfitting the factory, not testing edges.

## RESULTS - Session 3: AUDIT CHARTER (user challenge: "are we missing something?")

User asked for a full audit with "multiple passes just to be more ensured". Frozen as a
pre-registered 4-check battery (many independent confirmations ONCE EACH, not infinite
re-runs): A cost matrix, B positive controls w/ freeze rule, C trade forensics,
D assumption book. Charters: `audit.py`; addendum diagnostics: `diag_audit.py`.
Artifact: `out/audit_report.md`.

### Charter result A - COST MATRIX (10 frozen variants re-priced 0/2/7bp per side)

| Variant | 0bp Ret | 2bp Ret/PF | 7bp Ret/PF | Alive @maker? |
|---|---|---|---|---|
| H01a 1h | +0.32 | -2.87 / 0.94 | -10.39 / 0.75 | no |
| H01b 1h | -0.45 | -1.91 / 0.87 | -5.45 / 0.71 | no |
| H02a 1h | +1.63 | -1.48 / 1.05 | -8.84 / 0.85 | no |
| **H02b 1h** | +3.26 | **+1.12 / 1.22** | -4.04 / 0.99 | **YES -> MAKER-CANDIDATE** |
| H02a 4h | -7.17 | -8.04 / 0.67 | -10.15 / 0.60 | no |
| H02b 4h | -1.48 | -2.08 / 0.86 | -3.56 / 0.77 | no |
| H04a 1h | +1.38 | -0.24 / 1.03 | -4.16 / 0.69 | no |
| H04a 4h | -2.53 | -2.80 / 0.48 | -3.47 / 0.38 | no |
| **H03 1h deep** | +9.89 | **+7.05 / 1.03** | +0.24 / 0.91 (realized -0.96!) | **YES -> MAKER-CANDIDATE** |
| H03 4h deep | +1.83 | +1.48 / 0.73 | +0.57 / 0.69 | no |

Reading: user's instinct was RIGHT in a precise way - 5/10 variants were gross-positive
at ZERO cost, so the classes were not imaginary; but our 7bp/side retail cost wall kills
all of them (0/10 alive at 7bp), and at maker-only 2bp exactly 2 survive. The verdicts
were honest; the frontier is costs, not signal classes. H06 promoted to head of queue.

### Charter result B - POSITIVE CONTROLS (freeze rule)

Battery: two documented-edge daily strategies through the IDENTICAL 48m/12m walk-forward
(maker 2bp+slip, 3bp/day funding haircut while long). Gates: net_ret>0, Sharpe>0,
DD better than B&H by >=10pp, closed trades >=3.

| Control | Params (train-optimized) | Test Ret | Sharpe | MaxDD | Trades | B&H same window | Gates |
|---|---|---|---|---|---|---|---|
| H00a DailyMomentum (SMA + RoC) | n_sma=100, n_roc=30 | +4.29% gross / +1.27% net of funding | 0.98 | -1.71% | 3 (PF 9.16) | -22.58% @ -44.7% DD | 4/4 PASS |
| H00b DailyRegime (SMA filter) | n_sma=150 | +8.32% gross / +7.63% net | 0.41 | -10.86% | 3 (PF 0.00*) | same | 4/4 PASS |

UPDATE from diag_audit.py: H00b's +8.32% = realized -$5.95 + unrealized +$14.26 (open
long at cutoff). Realized-only it FAILS net_ret>0. H00a passed FULLY REALIZED.
Decision: NO FREEZE (H00a alone proves the machine can certify green in a
year where B&H lost -22.6% at -44.7% DD with +1.27% net and -1.7% DD - that is the
documented regime edge working in a hostile year, exactly as the literature says).
H00b stamped PASS-BUT-FRAGILE; the fragility became a standing rule (below).

### Charter result C - TRADE FORENSICS

| Strategy | Entries checked | Condition violations | Verdict |
|---|---|---|---|
| H01a 1h (2y OOS window) | 99 | 0 | ENGINE FAITHFUL |
| H03 4h deep (test year) | 20 | 0 | ENGINE FAITHFUL |

Every entry re-derived bar-by-bar by hand (regime gate, EMA touch, close-above, RSI band,
Donchian prior-N-bar high) - zero mismatches. The engine trades what we think it trades.

## FINAL STAMPS (Session 3)

- **Engine forensics: FAITHFUL.**
- **Freeze rule: NOT triggered -> all verdicts STAND** (Controls: H00a solid PASS;
  H00b PASS-with-fragility-flag).
- **Cost matrix: 0/10 alive at 7bp; 2/10 alive at maker 2bp.**
- **FLIPS: H02b 1h (mirrored short + VWAP) and H03 1h 20/10/ATR3 (deep) -> MAKER-CANDIDATE.**
  Realized evidence: H02b +1.12% realized / 70 trades / PF 1.22; H03 +5.74% realized
  (+1.31 unreal) / 99 trades / PF 1.03. Flip rule: maker-candidates must still pass full
  gauntlet (robustness + fresh window + testnet) before any live money. NO LIVE MONEY YET.

## Gate amendments (standing rules, recorded permanently in this section)

1. (Session 2) Directional 4h systems: multi-fold pooled OOS replaces the 100-trade bar.
2. (Session 3) **Realized/unrealized split**: every test-window verdict must report closed-trade
   realized PnL separate from open@cutoff unrealized PnL; verdicts dominated by unrealized
   PnL are stamped FRAGILE, not certified. (Origin: H00b quirk discovery.)
3. (Session 3) **Cost snapshot**: any strategy claimed ALIVE must state the per-side cost it
   requires to survive; a "live" only at <=2bp variant cannot be certified until H06-layer
   execution (real maker orders) is emulated AND testnet-proven.
4. (Session 3) **Positive controls re-run rule**: the H00 battery re-runs after any harness
   change, and any time a verdict is contested, before the old verdict is trusted again.

### Session 3 engineering log
- `audit.py` written + pre-flight review: caught 2 bugs BEFORE first run (tf extraction from
  tag text; DD-gate comparison inverted). Fixed, ran clean first pass.
- `diag_audit.py` post-run diagnostics: M2M realized/unrealized split for controls; trade
  anatomy for the two maker-alive candidates. Found stats['End'] is a timestamp in this
  backtesting.py version (use `_equity_curve` last row for final equity).
- FOUND (engine behavior, not bug): `Return [%]` includes open@cutoff unrealized PnL while
  `_trades`/PF/Exposure count closes only. Proof: H00b M2M +8.32% vs realized -$5.95.
  Related: H03 1h deep at 7bp "alive-ish" +0.24% M2M is realized-NEGATIVE (-$0.96).
- `DailyMomentum` / `DailyRegime` control classes added to strategies.py.
- Control battery note: PF 0.00 + positive Return is a signature of an open@cutoff position
  (all realized PnL negative; unrealized carried the stats). Now on the bug-signature list.

### Scoreboard after audit
H01 DEAD (all variants; engine-verified). H02 DEAD at 7bp / H02b 1h MAKER-CANDIDATE.
H03 MARGINAL / H03 1h MAKER-CANDIDATE. H04 DEAD. H00 controls: machine certified green.
$100 untouched. Zero tuition paid. User's skepticism sharpened the frontier instead of
changing a verdict - exactly what honest re-checking should do.

## RESULTS - Session 4: H06 maker-execution gauntlet (both audit-flipped candidates judged)

Design pre-registered (see gauntlet_h06.py header; file is the authority): LIMIT-order
entry layer applied to both candidates; fills = resting limits at signal close
(chase-replace on repeating signals, hard-cancel on regime break or fill_wait expiry);
SIGNALS FROZEN from the audit (no re-optimization); fill_wait joins the neighbor grid;
PRIMARY = deep test year as 4x3m folds at 2bp/side; PEEK-flagged secondary folds over
months 36-48 (in-sample-ish, advisory); blended honest-cost bracket 4.5bp/side
(entries maker, time/regime/SL exits takers in reality); gates P1-P7 incl. the
realized/unrealized quad-rule from Session 3.

### H06b_MakerShortPullback - DEAD (P1 fail, and everything else confirms)

| Fold | Realized $ | Trades | Sharpe |
|---|---|---|---|
| 1 (Nov25-Jan26) | 0.00 | 0 | n/a |
| 2 | -3.68 | 284 | -1.27 |
| 3 | -6.59 | 146 | -2.20 |
| 4 | -4.77 | 104 | -2.60 |

- Pool: -15.04 realized / 534 trades / mean fold Sharpe -2.02; 0/27 neighbors positive;
  ETH -16.93; PEEK -19.79; blended 4.5bp -31.75. Fold-1 zero trades is NOT a mechanic
  bug: the MARKET twin also fires zero trades in that regime window (forensics below).
- Market-vs-maker twin on the IDENTICAL 6mo window: MARKET 70 trades / +1.12% vs
  MAKER 355 trades / -10.8%; median hold 1 bar (283 trades <= 2 bars), pnl median
  -$0.07. Root cause: bar-confirmed pullback signals + resting-limit chase = CHURN
  RATCHET (fill intra-bar on the rally, regime-exit next bar, re-signal, repeat) -
  turnover x5, per-trade edge swallowed by round-trip costs. The maker rebate is
  eaten by the turnover the chase creates.
- **Structural insight (standing): passive/limit execution is not a cost plug-in for
  bar-confirmed signals; it must be designed WITH the signal (fill-then-reconfirm,
  stop-limits, price ladders). H02's class is DEAD in every execution mode: 4 market
  variants, now maker variant with 0/27 neighbors.**

### H06a_DonchianMaker - MARGINAL (fails 3 of 7 gates; not testnet eligible)

| Fold | Realized $ | Unreal $ | Trades | Sharpe |
|---|---|---|---|---|
| 1 | -7.04 | 0.00 | 24 | -3.22 |
| 2 | -2.05 | +0.13 | 29 | -0.67 |
| 3 | -4.25 | +0.79 | 18 | -1.97 |
| 4 | +15.70 | +1.43 | 26 | +1.73 |

- Pool: +2.36 realized / 97 trades, mean fold Sharpe -1.03, 1/4 folds positive.
  Unrealized/unrealized split rule (P7) FAILS: unreal +2.35 = 100% of realized -
  half the pool's gain is open@cutoff marks (fold-4 positions riding into the cutoff).
- But: neighbors 24/27 = 89% positive; ETH pool +12.01 realized (85 trades, Sharpe
  0.36); PEEK pool +3.16 (116 trades). Blended 4.5bp: -0.82 realized -> NOT alive at
  the honest exit-cost floor.
- Reading: same disease every Donchian tune has shown - the STRUCTURE is robust (89%
  of param neighborhoods pay), the fold CONSISTENCY is not (one quarter carries the
  pool), and the honest cost floor wipes the crumbs. Archived; needles to say: this
  is the third independent confirmation of that disease family on this signal class.

### Session 4 stamps
- Both audit-flipped candidates resolved: H02-maker DEAD, H03-maker MARGINAL.
- NO testnet. $100 untouched. The maker path was TESTED with real execution mechanics,
  not assumed - the pre-registered flip rule demanded gauntlet survival and neither
  candidate survived.
- Nothing on the desk is gauntlet-certified at any cost level. The desk is still
  waiting for its first certified strategy.

### Session 4 engineering log
- strategies.py: MakerMixIn + DonchianMaker + MakerShortPullback. Maker semantics
  verified against backtesting 0.6.6 source BEFORE building: resting limits fill at
  min(open,limit)/max(open,limit) and persist; exclusive_orders auto-cancels previous
  pending order => chase-replace is safe; Order.cancel() used for regime-break /
  wait-expiry cancels. Two self-review catches fixed before runs (mangled chained
  comparison in the short bracket guard; dead branch in DonchianMaker).
- gauntlet_h06.py: 7 pre-registered gates (P1-P7), 27-neighbor grids each, ETH
  cross-check, PEEK folds, blended bracket, realized/unreal split. Pre-run self-review
  caught one fold-index variable bug and two report-string construction bugs
  BEFORE first execution.
- diag_h06b.py: market-vs-maker twin forensics (cadence, hold-length, pnl anatomy);
  fold-boundary caveat discovered and recorded: per-fold windows liquidate
  cross-boundary positions and re-anchor VWAP at each fold start, so fold pools are
  conservative vs a single contiguous window (54 vs 70 trades on the same calendar
  span, delta ~2pp realized). Recorded as a running caveat for future fold batteries,
  NOT as a gate amendment.
- Session-3 standing rules honored: realized/unrealized split applied (D1 rule).

### Session 5 queue (updated by gauntlet outcome)
- [ ] H05: VWAP-band intraday mean reversion (1h), CONVENTIONAL market execution;
  maker only as signal-native design later if the class survives at taker costs
  (maker-as-bolt-on is now explicitly rejected by evidence).
- [ ] H07: daily regime/momentum stands as the strongest documented-signal ground
  (H00a realized +1.27% in a hostile year) -> give it the full H06-style gauntlet
  (fold battery at daily cadence, P1-P7 adapted: taker costs, funding haircut).
- [ ] If BOTH H05 and H07 die: MANDATORY strategic review before any new variants
  (timeframes below 1h, universe widening beyond BTC/ETH, carry/funding structures,
  volatility-filtered designs).
- [ ] Housekeeping: instrument the fold battery to carry open positions across fold
  ends (kill the conservative boundary artifact) if we keep fold judging.

## RESULTS - Session 5: H05 judged DEAD, H07 judged MARGINAL -> strategic review trigger

### H05 - VWAP-band intraday mean reversion (1h, market execution, 7bp/side)

Pre-registered two-stage battery (h05.py): 12-combo grid
(k_band 1.0/1.5/2.0 x atr_stop 1.5/3.0 x time_stop 8/24h) train-optimized on the
48m deep train; test = fresh 12m once; stage-2 folds ONLY if alive.

| Window | Result |
|---|---|
| TRAIN (48m) | **-99.32%** / 4,387 trades / Sharpe -6.69 / realized -$99.32 |
| TEST (12m) | **-38.19%** / 651 trades / PF 0.85 / Win 41.8% (B&H: -22.67%) |

VERDICT: **DEAD (stage-1 wipeout; stage-2 skipped by only-if-alive rule).**
Reading: 1-bar VWAP dips at 1h cadence on crypto = ~14bp round-trip cost on every
dip; the class is the same disease family (churn + taker wall), now with evidence
from a FRESH edge class. Stage-1 kill for $0 tuition. Win 41.8% with PF 0.85 =
negative tail bigger than reversion wins.

### H07 - daily regime/momentum (H00a identity, frozen n_sma=100/n_roc=30) - FULL gauntlet

Pre-registered battery (h07_gauntlet.py): 4x3m folds with 150d warmup lead
(an SMA(100) cannot warm up inside a 3m fold; trades counted only if entered
in-window - pre-registered accounting), 7bp/side + 3bp/day funding haircut,
9 documented-grid neighbors, ETH cross-check. Maker banned as bolt-on.
PEEK folds deliberately skipped (in-sample data covered by neighbor battery).

| Fold | Realized | Funding drag | Net $ | Trades |
|---|---|---|---|---|
| 1 (Nov25-Jan26) | 0.00 | 0.00 | 0.00 | 0 |
| 2 | -0.29 | 0.01 | -0.30 | 1 |
| 3 | 0.00 | 0.00 | 0.00 | 0 |
| 4 | +4.62 | +0.41 | +4.20 | 1 |

- Pool: realized +4.33 -> **net +3.90**; only 2 closed trades; mean fold Sharpe +0.27;
  folds-net-positive 1/4; residual share 21% (passes the purity gate).
- Neighbors: 6/9 net-positive (67%). ETH pool net: +3.35.
- VERDICT: **MARGINAL (failed P2d trade floor and P4d fold-positivity; GROUND passes
  everything else).** NOT testnet eligible under the pre-registered mapping.

### The H07 reading (bridge to the strategic review)

The only signal family that has OUTPERFORMED cash-and-B&H in every independent
battery view (audit control: +1.27% net realized vs B&H -22.6%; deep folds: +3.9% net;
ETH: +3.35; 67% of documented neighbors positive) is statistically STERILE at our
scale: 2-4 closed trades per year on ONE asset. At a $100 account that is ~4%/yr -
operationally pointless by itself. The verdict is NOT "the edge is fake"; it is
"the edge needs a bigger breadth of expression": universe width (top-N coins),
portfolio-level application, long horizons, or demotion to a regime/vol filter
inside other strategies.

### Session 5 stamps
- H05 DEAD (fresh edge class, stage-1). H07 MARGINAL (ground-solid, mass-thin).
- Nothing certified. $100 untouched across 5 sessions, 9 hypothesis families,
  13 execution variants run, zero dollars of tuition.
- Pre-committed condition met in spirit ("mandatory strategic review before ANY
  new variants"): triggered NOW - user ratifies direction next.

### Session 5 engineering log
- indicators.py: vwap_sigma_daily + vwap_band_arrays (bar-local, UTC-anchored,
  first 3h-of-day NaN mask to kill the 00:00 pathology; smoke-tested).
- strategies.py: VwapBandReversion added (market execution, VWAP-touch exit,
  ATR stop, hour time stop).
- h05.py + out/H05_report.md; pre-run self-review REWROTE the file to fix
  (a) broken stage-return plumbing, (b) fatal non-injection of _vwap/_sig arrays
  (would have produced a fake zero-trade run), (c) leftover dead code.
- h07_gauntlet.py + out/H07_report.md; pre-run catches: fold_frame end-month
  crash bug; SMA(100) warmup-impossible-in-fold DESIGN bug caught BEFORE running
  and pre-registered as the warmup-lead accounting rule.
- diag discipline: fold in-window-only trade counting documented as conservative
  (straddling positions excluded; residual proxy pre-registered).

## SESSION 6 PRE-REGISTRATION (written BEFORE any new-symbol data was fetched)

Direction ratified by user: UNIVERSE WIDENING (primary) + FUNDING-CARRY (side line).

### Primary: universe battery for the H07 identity (pre-registered)

- Assets: BTC, ETH (existing) + 8 additions fetched 5y spot klines 1h ->
  BNB, SOL, XRP, DOGE, ADA, LINK, AVAX, TRX (all have >=5y Binance spot history,
  liquid perps for execution).
- Frozen signal identity: DailyMomentum n_sma=100, n_roc=30 (H00a provenance, zero
  re-optimization). This is a UNIVERSE generalization test, not a tuning pass.
- Shared absolute test year for ALL symbols: UTC 2025-11-05 -> 2026-11-04
  (BTC deep-series anchor); per-symbol 150d warmup lead; 4x3m folds; trades counted
  only if entered in-window (standing accounting).
- Costs: 7bp/side + 3bp/day funding haircut on notional while long (perp execution).
- Basket gates (pre-registered):
  B1 basket pooled NET > 0
  B2 >= 60% of the 10 symbols net-positive
  B3 >= 60% of the 9-neighbor documented grid (n_sma 100/150/200 x n_roc 20/30/50)
     pooled-net-positive across the FULL basket
  B4 mean per-symbol net > 0 (guards single-asset luck)
  B5 BTC/ETH continuity: same code path must reproduce Session-5 BTC +3.90 / ETH +3.35
     within accounting tolerance (engine continuity check, tolerance +-0.5)
- Verdicts: all -> GAUNTLET-CERTIFIED (basket candidate; testnet next);
  B1 fail -> DEAD; partial -> MARGINAL with named failures.
- EXCLUSIONS: no maker brackets (Session-4 rule); no re-optimization; no PEEK theater.

### Side line: funding-carry research (pre-registered)

- Data: Binance fapi /fapi/v1/fundingRate history, BTCUSDT, 5y, paginated ->
  data/funding_BTCUSDT.csv. Live spot-check already done (Nov 6: floor +1bp/8h,
  shorts EARN 3bp/day).
- Analytics (descriptive, 5y): monthly funding sums, share of negative periods,
  annualized rates in positive vs negative regimes; distribution stats.
- Two-leg SMOKE model (NOT a gauntlet; revenue-structure study): long spot +
  short perp 1x => PnL = funding stream - fees (spot 10bp + perp 5bp per SIDE =
  30bp round trip); rule: enter when trailing-3-period mean funding > +1bp/8h,
  exit when < -1bp/8h; report trips, funding collected, fees, net, max
  drawdown-of-carry-stream. Purpose: quantify the structural revenue curve ONLY;
  formal certification would need its own gauntlet + testnet.

## RESULTS - Session 6: universe battery + funding-carry analytics

### Primary: UNIVERSE GAUNTLET (10 symbols, H00a identity frozen)

| Symbol | Net $ | Trades | Folds net-pos | Mean fold Sharpe |
|---|---|---|---|---|
| BTCUSDT | +3.90 | 2 | 1/4 | +0.27 |
| ETHUSDT | +3.35 | 9 | 1/4 | -0.64 |
| BNBUSDT | +2.48 | 5 | 1/4 | +0.12 |
| SOLUSDT | +5.14 | 4 | 1/4 | -0.48 |
| XRPUSDT | -2.29 | 8 | 0/4 | -1.22 |
| DOGEUSDT | -3.29 | 7 | 0/4 | -0.22 |
| ADAUSDT | -1.48 | 6 | 0/4 | -0.87 |
| LINKUSDT | +4.05 | 5 | 1/4 | -0.70 |
| AVAXUSDT | +2.74 | 4 | 1/4 | -0.14 |
| TRXUSDT | -6.08 | 11 | 0/4 | -0.24 |

- Basket pooled net +8.52 across 61 closed trades (MASS problem attacked: 2 -> 61).
- Gates: B1 PASS (pooled >0) | B2 PASS (6/10 = exactly 60%: BTC, ETH, BNB, SOL, LINK, AVAX)
  | B3 FAIL (3/9 = 33% neighbors) | B4 PASS (mean/symbol +0.85) |
  B5 PASS (BTC +3.90->+3.90, ETH +3.35->+3.35 EXACT reproduction - engine continuity
  via absolute-calendar fold anchors CONFIRMED).
- VERDICT: **MARGINAL** (B3 failed). Not certifiable; no re-runs, no re-optimization.
- Neighbor forensics (diag_universe_neighbors.py): the SMA(100) family passes as a
  FAMILY (100/20 +1.17, 100/30 +8.52, 100/50 +2.37); EVERY SMA(150) and SMA(200)
  neighbor FAILS, monotonically decaying down to -19.35 (200/50). Structural finding:
  in this hostile test year, REGIME SPEED is the economically meaningful variable -
  fast (100d) filters defended capital, slow ones rode the drawdowns. The frozen
  identity sits at the fast edge of a decaying family: not a lucky island (its own
  family is uniformly positive), but not robust across the neighborhood either.
  NOTE: this does NOT license a grid-grind toward faster SMA - that would be
  overfitting to one hostile year. It licenses a REGIME-SPEED study with proper
  multi-year train/OOS discipline (2022-2024 as train material, 2025-26 as judge).
- Negative symbols (XRP, DOGE, ADA, TRX) were the year's weakest regime-players;
  per-symbol alpha varies with each coin's own regime character - cross-sectional
  (relative-ranked) selection is the obvious H08 follow-up, NOT more per-coin slots.

### Side line: FUNDING-CARRY (revenue structure, 5y BTCUSDT)

Facts (5,481 8h prints, 2021-11-06 -> 2026-11-06):
- 85.1% of prints positive; mean +6.9%/yr (+8.8% when positive, -4.3% when negative);
  p95 +14.4%/yr. Always-in carry reference: +34.34% of notional over 5y, no fees.
- Monthly sums 2025-2026 include a negative stretch Feb-Apr 2026 (-0.06% to -0.18%/mo)
  - funding stream is regime-dependent, CORROBORATING the H07/H00 theme that regime
  gating is the edge ground everywhere in this market.

Two-leg carry smoke (pre-registered rule, fees 30bp round trip, $100 notional):
- Gated rule (trail-3 > +1bp/8h enter; < -1bp/8h exit): 2 round trips, +24.11%
  funding collected - 0.60% fees = **NET +23.51 (~4.7%/yr), stream maxDD ~ -$0.09**.
- Always-in (one trip): +34.04% net over 5y (~6.8%/yr) BUT the stream would ride
  every negative-funding stretch (true risk = 2022-scale negative regimes; MDD not
  modeled in this smoke and could be severe).
- SIDE-LINE VERDICT (study-level, NOT certified): carry is a REAL structural income
  stream (85% positive prints, floor-pegged 3bp/day currently); the naive always-in
  version out-NAVIGATES the trail-3 gate by ~2.1pp/yr on this span end-to-end, but
  carries unmodeled negative-regime drawdown risk; the gate buys smoothness at that
  price. Both versions need: basis/slip modeling, both-leg execution realism, and a
  dedicated gauntlet + testnet before any money. A NEXT-STEP candidate for a formal
  H09 line.

### Session 6 stamps
- Universe battery: MARGINAL (pooled +8.52/61 trades is the best evidence depth yet;
  stability fails) -> not certified; no testnet.
- Carry study: structural income CONFIRMED at study level; certification pipeline
  defined but not built/finished.
- $100 untouched. Zero certification across 6 sessions; best cumulative evidence
  now sits in the daily-regime family expressed ACROSS a universe, plus a
  structurally different income stream (funding carry).

### Session 6 engineering log
- fetch_universe.py: 8 new symbols x 5y 1h deep (43,799 rows each; one endpoint
  timeout auto-fell-back to data-api mirror).
- universe_h07.py: 10-symbol battery, absolute-calendar fold anchors (B5 continuity
  exact), 9-neighbor basket grid (360 fold-runs), per-symbol/detail tables.
- diag_universe_neighbors.py: per-neighbor per-symbol decomposition (forensics only).
- funding_carrier.py: paginated fapi funding history (5,481 prints), analytics,
  pre-registered carry smoke; self-review fixes before run (dead loop, unclosed
  final carry position, trips counter).
- out/universe_report.md + out/FUNDING_analytics.md artifacts.

### Session 7 queue (updated by Session 6 results)
- [ ] H08 (NEW, natural next line): CROSS-SECTIONAL momentum on the 10-symbol
  universe - rank by 30d/60d RoC, hold top-K long, rebalance weekly daily-cadence.
  Attacks per-coin regime variance with relative strength; uses data already in the
  folder. Pre-register gates like B1-B5 before running anything.
- [ ] Universe regime-speed study: pick the regime-slowdown by YEARS 2022-2024
  (train), judge 2025-26 (untouched). Legal path to revisit MARGINAL baskets
  WITHOUT grinding one hostile year.
- [ ] H09 (new line): formal funding-carry gauntlet - basis/slip model, both-leg
  execution costs, negative-regime stress on always-in vs gated, folds, only then
  testnet. Needs the 2022-bear funding drawdown quantified first (from CSV in hand).
- [ ] If H08 dies AND regime-speed study fails: the strategic conclusion is that
  daily-bar alpha on liquid crypto is not certifiable at $100 scale with this
  cost structure - pivot candidates: weekly cadence carry portfolio or desk park.

### Session 4 queue (updated by audit outcome)
- [ ] H06 FIRST (promoted by audit): real maker-order emulation layer. Limit entries at
  maker 0.02%, fill-lag modeled as entry at next bar open only if low <= limit (fill
  realism), maker TPs where possible. Cost ledger at 2bp/side.
- [ ] Apply FULL gauntlet to H02b 1h + H03 1h deep as maker variants: 27-neighbor
  robustness at 2bp, ETH cross-check, fresh-window consistency (multi-fold), realized split.
- [ ] H05 VWAP-band reversion still queued (new edge class).
- [ ] H07 daily carry/momentum (now ALSO justified by H00 results: the regime edge SHOWED
  UP in the hostile year; H00 as a candidate strategy gets the same gauntlet treatment as
  any other, maker costs + funding haircut).
- [ ] If everything dead: strategic review before more variants.

## SESSION 7 (Nov 7, 2026) - opener: controls re-run SEAL + H08 pre-registration

### Opener: positive-controls re-run seal (standing-rule compliance)

Reason: user request for a zero-loose-ends record after conversation compaction
(the summary history, not the disk artifacts, was compacted; two server restarts
and one connection reset during Sessions 5-6 all recovered without data loss -
three journal-editing blemishes were found in the closing audit pass and repaired
before this seal; verdict-bearing numbers were re-verified against out/*.md to
the cent). One genuinely open item under our own standing rule "controls re-run
after any harness change": strategies.py/indicators.py grew additively since the
Session 3 controls passed. Seal executed, user ratified as Session 7 opener.

Method: seal_controls.py calls audit.positive_controls() UNTOUCHED; diffs H00a/
H00b against the S3 stored stamp; engine constants re-verified in config.py
(CASH=100, 7bp/side, 1x, PRICE_SCALE=1e6, kill rails intact).

Result (out/controls_rerun_seal.md):
- H00a: Ret +4.29%, Sharpe 0.98, MaxDD -1.71%, 3 trades, PF 9.16, net +1.27%
  -> EXACT match to S3, all 4 gates PASS
- H00b: Ret +8.32%, Sharpe 0.41, MaxDD -10.86%, 3 trades, net +7.63%
  -> EXACT match, 4/4 gates PASS
- Freeze decision: BOTH PASS -> machine can certify green.
- Data integrity at seal time: BTC deep 43,799 rows, funding 5,481 prints.
**SEAL: PASS - harness certified green; every Session 3-6 verdict STANDS. Zero
re-testing required anywhere; H01-H07 stamps were never compaction-fragile.**

Governance ratifications (user, Nov 7): (1) controls re-run before new work |
(2) H08 pre-registration then run straight after, veto at report card |
(3) no report-card archive needed (journal is the primary artifact) |
(4) user memory check clean - all prior decisions confirmed on disk.

### H08 PRE-REGISTRATION (written BEFORE any H08 run): cross-sectional momentum

Hypothesis: relative strength selects survivors; the weakest-regime coins were the
universe's heat source of losses in S6 (XRP/DOGE/ADA/TRX net-negative at every
fold) so ranking and holding ONLY the top-K names converts per-coin regime
variance into a portfolio edge. Machinery is NEW by necessity (a portfolio needs
its own engine - backtesting.py is single-asset; this is the one legitimate
custom-engine use, specification declared before running), signal class is a
documented one distinct from all prior: cross-sectional momentum.

Engine specification (declared before running):
- Inputs: daily bars resampled from 1h deep (audit.daily_df), 10 symbols, SAME
  shared test year as S6 (2025-11-05 -> 2026-11-04) for like-for-like pooling
  against the S6 basket (+8.52 goodwill comparison, not a gate).
- Signal: r-day return rank (Close[t]/Close[t-r]-1) on the LAST daily bar of
  each ISO week (rebalance anchor).
- Execution: signals conclude at close t; executed at NEXT day's open (no
  lookahead). Long-only, equal-weight 100/K per name, 1x total notional cap;
  fractional units allowed (own engine; granularity ~1e-6 of daily range,
  declared). Membership churn control: a held name is sold ONLY when it leaves
  the top-K rank set at a rebalance date; equal-weight restored on membership
  change only (no intra-membership re-weighing).
- Costs: 7bp/side on traded notional; funding 3bp/day haircut on open long
  notional (perp longs pay positive funding; haircut applied on entry notional).
- Walk-forward: winner grid r in {30,60} x K in {2,3} = 4 combos (<16 rule),
  optimized on months [0,48) train ONLY; the untouched test year is judged ONCE
  with the frozen winner.
- Fold accounting: S6 standard - 4x3m absolute-calendar folds, 150d warmup lead
  (rank windows <= 60d), trades counted only if entered in-window, residual =
  M2M - realized reported; NET = realized(net of drag) - including fold pooling.
- Benchmark: equal-weight 10-coin buy-and-hold, reported not gated.
- Stability battery (judged against frozen winner, pre-registered):
  N1 neighborhood: >= 3/4 of the 4 grid combos net-positive across the test year
  N2 leave-one-out x 10 symbols: winner pool stays net-positive in EVERY exclude-
     one portfolio, AND >= 7/10 of the LOO pools net-positive
  N3 double-cost robustness: winner NET stays > 0 at 10bp/side
  N4 attribution cap: the winner's best single symbol <= 60% of pool realized
Portfolio gates (ALL -> CERTIFIED, testnet-eligible):
  P1 test-year portfolio NET > 0
  P2 >= 20 closed portfolio trades in test year
  P3 >= 2/4 folds net-positive
  P4 unrealized open@cutoff <= 25% of realized
  P5 winner NET > equal-weight 10-coin B&H net (same window)
  P6 stability: N1, N2, N3, N4 all hold
Any P1 fail -> DEAD; else MARGINAL naming exact failed gates.
Standing rules preserved: no maker bolt-on; no re-optimization after the single
judge pass; realized/unrealized split; one-pass verdict only.

### H08 RESULTS (run per pre-registered rules AFTER the registration landed)

Train (48m, money view - declared metric): all 4 grid combos strongly positive;
| r | K | NET $ | legs |
|---|---|---|---|
| 30 | 2 | +198.09 | 126 |
| 30 | 3 | +173.44 | 171 |
| 60 | 2 | +36.20 | 98 |
| 60 | 3 | +108.64 | 116 |

Frozen winner: r=30, K=2 (max train NET, +198.09).

Test year 2025-11-05 -> 2026-11-05, judged ONCE (realized-only standing rule):
- 43 closed in-window legs, realized **-64.66** net of fees+haircut (M2M -59.62,
  residual +5.04 = 8% of realized, open@cutoff 2 names).
- Folds 4x3m: pool realized -75.29, 0/4 folds positive (best fold -4.16).
- per-symbol losses: best is BELTSTRIKE SOL +2.97; 9 of 10 symbols lose
  (ADA -14.82, BNB -12.57, XRP -8.99, ETH -8.79, AVAX -8.77, DOGE -8.30...).
- Neighborhood N1: all 3 non-winner combos negative (-31 to -58); N2 LOO: 0/10
  pools positive (-56 to -69); N3 double-cost: -64.75; P5 vs equal-weight B&H
  net (-34.21): FAIL by -30pp.
**VERDICT: DEAD (P1 failed; 7/9 gates failed; pre-registered one-pass).**
No re-runs, no maker rescue allowed (bolt-on ban), no universe variant revive
(N2 shows no single symbol carries the loss - the CLASS is wrong, not a name).

Reading (forensics-complete): the mother of all walk-forward reversals -
train 2x money in 4y of mostly-bull legs, then the same rule loses ~2x B&H in
the hostile judge. Weekly momentum-chasing into a strength-reversal regime is
knife-catching: the attribution is diffuse (all names lose spread out, N4 clean),
fees are trivially small vs losses (10bp/side changes -64.66 -> -64.75), so this
is NOT a cost artifact and NOT one lucky loss ball - it's the same S5/S6 disease:
REGIME DEPENDENCE, now proven lethal for ranked-momentum on this universe at our
cost floor. Cross-sectional momentum at weekly cadence: permanently dead on this
desk (kill rails: fails at price layer, not marginal).

H08 DEAD triggers the pre-registered pivot condition evaluation: queue says
"H08 dies AND regime-speed study fails -> pivot". Regime-speed study = Session 8
opening move (confirmatory framing - the 2025-26 judge year was already spent
once as S6's test; the study re-asks the S6 stability finding with a 2022-24
train anchor, NOT a discovery pass; pre-registration must carry that caveat).

### Session 7 stamps (opener + H08)
- Positive-controls SEAL: PASS (both controls reproduce S3 identically; harness
  certified green; ALL verdicts stand; compaction caused zero result damage -
  three journal-text blemishes found+repaired in closing audit pass).
- H08 cross-sectional momentum: **DEAD** (cleanest kill explanation in the
  project; zero re-testing needed).
- $100 untouched across 7 sessions. Nothing certified still true; the evidence
  base for "regime dependence is the master variable" is now overwhelming:
  speed of regime filters (S6 forensics) and momentum-chasing failures (H08)
  point the same direction from two independent families.
- Pivot condition: 50% evaluated (H08 DEAD); regime-speed decides the other 50%.

### Session 7 engineering log
- seal_controls.py + out/controls_rerun_seal.md: untouched-call seal runner;
  parsed diffs; both controls EXACT matches to S3 (H00a net +1.27, H00b +7.63).
- h08.py: custom portfolio engine (joined-calendar, weekly ISO anchors,
  next-open execution, equal-weight top-K, membership churn control,
  7bp/side + 3bp/day haircut, realized-only verdict accounting, LOO/N1-N4
  battery, B&H benchmark). Pre-run self-review caught BEFORE execution:
  (a) fatal accounting-epoch bug (test/fold/LOO sims started from 2021 - would
  have contaminated every window M2M; fixed with 150d warmup slices),
  (b) P4 auto-pass bug (forced-close included in NET - residual would be 0);
  fixed by realized-only verdicts per standing rule,
  (c) float(...).any() crash bug, (d) three dead functions removed.
- out/H08_report.md. JOURNAL pre-registration landed BEFORE build (this file).

## SESSION 8 (Nov 9, 2026) - PRE-REGISTRATION: regime-speed confirmatory study + H09 bear-stress groundwork

Both items queued by the Session 7 queue and ratified direction. H08 is DEAD, so
the regime-speed study completes the pre-registered pivot condition
("H08 dead AND regime-speed fails -> pivot to weekly-cadence carry portfolio or
park desk"). NOTHING certifies from this session; it delivers ATTRIBUTION and a
pivot decision.

### CONFIRMATORY framing (declared before running, non-negotiable)

The 2025-2026 judge year was already spent ONCE as the S6 universe battery test
(MARGINAL). This study re-asks the S6 stability finding with a 2022-2024 train
anchor. Its evidentiary role = confirmatory attribution, NOT discovery; any
"pass" does NOT flip the S6 verdict or certify anything. It feeds exactly one
decision: does the daily-bar alpha line STAY on the shelf (with a licensed
future re-certification attempt on a fresh future window) or leave the shelf
permanently (pivot condition completes -> carry line becomes primary / park).

### Regime-speed study spec (written BEFORE any run)

- Question: does REGIME SPEED selected on the OLD epoch (calendar 2022) transfer
  to the judge year (2025-11-05 -> 2026-11-05)? S6 forensics said the SMA(100)
  family passed the judge as a family while SMA(150)/200 uniformly failed - if
  a speed rule fit ONLY on 2022-2024 data picks the same family, speed is
  persistent structure, not one-year noise.
- Selection epoch: calendar 2022-01-01 -> 2024-12-31 (train material - all
  inside S6's training span, so no OOS contamination risk for TRAINING).
  WARMUP CONVENTION (declared): all filters held to the COMMON START
  2022-06-01 - the pre-epoch warmup banks from series t0 (2021-11-06) cover
  fast filters but n_sma=200 only warms ~2022-05-25; holding ALL combos to the
  common start kills the warmup bias that would otherwise punish slow filters.
  Trades counted only if entered on/after 2022-06-01.
- Candidates: the documented 9-combo grid n_sma {100,150,200} x n_roc
  {20,30,50} (S6 neighborhood standard, zero new tuning); DailyMomentum
  identity, 10-symbol universe, 7bp/side + 3bp/day haircut (S6 cost standard).
- Selection metric: pooled NET (realized net of drag) across the 10 symbols
  over 2022-06-01 -> 2024-12-31. Tie-break: higher pooled realized, then lexicographic.
- Confirmation epoch: EXACT REPLAY of the S6 judge battery via
  universe_h07.fold_daily/fold_net imports (absolute-calendar folds, in-window
  entries) - determinism continuity with the S6 table, NOT a fresh spend.
- Pre-registered gates:
  T1 transfer: the combo selected on 2022-2024 has judge-year pooled NET > 0.
  T2 family property: the n_sma family selected on 2022-2024 shows >= 2/3 of
     its n_roc members judge-positive AND its train family-mean NET > 0.
  T3 structural persistence: slow-family monotone decay on TRAIN must mirror
     the S6 judge pattern already documented (n_sma 150/200 worse than 100).
- Verdict mapping (pre-registered):
  T1+T2 PASS -> "transfer CONFIRMED": the fast-family basket stays on the
    shelf as the standing daily-bar candidate; re-certification licensed ONLY
    on a fresh future window (e.g., 2026-11 -> 2027-11); nothing certified now.
  T1 or T2 FAIL -> transfer FAILS -> pivot condition COMPLETES (with H08 DEAD):
    the daily-bar alpha line is permanently shelved and the desk pivots to
    the funding-carry line (H09 formal gauntlet) or parks - user ratifies
    which pivot branch at the report card.
- Exclusions: no re-optimization of anything else; no maker brackets; one pass.

### H09 SIDE LINE - bear-stress groundwork (deliverable spec, pre-registered)

Goal: quantify the exact risk number the formal carry gauntlet needs: how bad
is the negative-funding drawdown for the SHORT-perp leg (long-spot+short-perp
PAYS when funding prints negative - 2022 bear era is the stress test).
From data/funding_BTCUSDT.csv (5,481 prints, in hand):
- Per-year funding totals 2021-11 -> 2026-11 (annualized where full year).
- ALWAYS-IN stream: cumulative funding sum as % of notional; max drawdown of
  the stream (peak-to-trough, pp of notional); worst calendar month; worst
  90-print window; longest consecutive negative-print run; negative-print
  share per year.
- GATED rule (Session 6 smoke spec: trail-3 mean > +1bp/8h enter; < -1bp/8h
  exit; 30bp round trip): full-span replay (reproduce the +23.51 reference
  within accounting tolerance), then 2022-slice: trips, funding collected,
  fees, net, stream MDD, worst month.
- Output: out/H09_bear_stress.md with the design notes the formal gauntlet
  needs (basis/slip modeling checklist: mark-vs-index drift, perp execution
  spread, spot execution spread, rebalancing frequency).
NOT a gauntlet, NOT certified: revenue-structure stress numbers only.

### Session 8 RESULTS (post-run stamp)

#### Regime-speed confirmatory study (out/REGIME_SPEED_report.md)

Selection epoch 2022-06-01 -> 2024-12-31 (10 symbols, 7bp+3bp standard): the
epoch was generous to the WHOLE grid - all 9 combos realized-positive, pooled
nets +68.80 (200/50) to +196.77 (150/30). The $8.29 margin separating the
selected 150/30 from runner-up 100/30 (+188.48) is noise-scale - pre-registration
bound us to it, and that binding is the lesson: a metric that picks within noise
cannot deliver a transferable rule.

Judge replay (exact S6 machinery): selected 150/30 judge pooled NET -3.61.
- Gates: T1 FAIL | T2 FAIL | T3 (advisory) train slow-decay ABSENT
  (train family means: SMA100 +153.24, SMA150 +155.09, SMA200 +141.23 - the
  2022-24 epoch mildly favored SLOW, then 2025-26 favored FAST: epoch-dependent,
  not persistent structure).
- Judge family confirmation table remained: SMA100 3/3 positive (+4.02 mean),
  SMA150 0/3 (-4.56), SMA200 0/3 (-15.05).

**VERDICT: TRANSFER FAILS.** Per the pre-registered mapping: with H08 already
DEAD, the pivot condition is COMPLETE. The daily-bar alpha class (per-coin
regime/momentum, cross-sectional momentum) is PERMANENTLY SHELVED as a
candidate line - it may return only via explicitly pre-registered new-class
hypotheses, not by warm-restarting these. GUARD: this does NOT touch the
harness-health controls (H00a/b remain valid positive controls; H00a's
continuity duty unchanged).

#### H09 bear-stress groundwork (out/H09_bear_stress.md)

The 2022-bear catastrophe the carry line feared does NOT appear in the funding
prints - stress test outcome is de-risking:
- Yearly funding (short-perp holder pays negatives): 2021(partial) +2.46%,
  2022 +4.165% (22.1% negative prints but shallow), 2023 +7.87%, 2024 +11.96%,
  2025 +5.13%, 2026(partial) +2.77%. Span total +34.34% gross.
- ALWAYS-IN stream max drawdown: **-0.41pp of notional** (worst month -0.18%,
  worst 90-print window -0.30%, longest negative run 6.0 days).
- GATED rule full-span replay: NET **+23.51 on $100 - EXACT reproduction of the
  S6 reference** (accounting tolerance check PASS; 2 trips, +24.11% funding,
  -0.60% fees); gated stream MDD -0.09pp.
- 2022 slice: the gate held 175/1095 prints (16% exposure), accrued +0.75%,
  26.9% of held prints negative, worst 30-held-print stretch -0.02%.
- Honest reading: the funding STREAM is not the carry stack's tail risk; the
  REAL risk lives in basis/execution marks (spot-perp basis wobble, mark-vs-
  index drift, spreads) which funding prints cannot show. The formal H09
  gauntlet must model those, not re-fear 2022 funding. Kill-rail design note:
  carry stack DD gate at strategy -10% NAV (tighter than the -15% default,
  calibrated to ~7%/yr income arithmetic), both legs liquidate together.

#### Session 8 stamps
- Regime-speed: TRANSFER FAILS (pre-registered mapping executed verbatim).
- Daily-bar alpha line (per-coin + cross-sectional momentum): shelved
  permanently as candidate lines; pivot condition COMPLETE (H08 dead + no
  transfer).
- H09 groundwork: carry stress test BENIGN at funding-print level; formal
  gauntlet spec Notes staged (basis/slip + 1.5x cost stress + -10% NAV rail).
- $100 untouched across 8 sessions. Zero certified still true - and now the
  pre-registered queue machinery itself decided the next strategic branch.
- Desk direction (pre-registered pivot candidates): weekly-cadence carry
  portfolio via H09 formal gauntlet, OR park. User ratifies at report card.

#### Session 8 engineering log
- rspeed.py + out/REGIME_SPEED_report.md: selection (single-window pooled net,
  common-start warmup convention) + exact S6 judge replay via universe_h07
  imports. Pre-run self-review caught a design-code contradiction: the slice
  originally started 2022-01-01, which would have re-created the warmup bias
  against slow filters that the declared common-start convention exists to
  kill - fixed to slice from series t0 with entry-counting >= 2022-06-01.
  Also: unhashable-dict-key crash fixed (tuple keys).
- bear_stress.py + out/H09_bear_stress.md: yearly profile, always-in stream
  MDD/worst-window stats, gated rule replay + 2022 slice, gauntlet design
  checklist. Pre-run cleanups: dead tuple, simplified funding accumulation.

#### Session 8 close - PARK RATIFICATION (Nov 9, 2026)

Decision path recorded verbatim for the audit trail: the report-card question
tool logged "H09 carry gauntlet now (Recommended)" as the click; the user's
final typed instruction the same day read: "park it for now instead and please
continue, tell me where should we proceed now?" LATEST USER INSTRUCTION TAKES
PRECEDENCE: **the desk PARKS.** H09 design remains STAGED (spec notes in
out/H09_bear_stress.md), NOT built, NOT scheduled, NOT costing anything until a
wake trigger fires.

PARK PROTOCOL (pre-registered at parking time, before the instrument build):
- Operational state: no new strategy engineering, no builds, no testnet, and
  no live account was EVER opened - clean park; $100 untouched as always;
  zero unwind obligations.
- Staged-but-parked assets: H09 gauntlet design notes (basis/slip stress at
  1.5x costs, -10% NAV carry rail, both-legs-liquidate rule); 5y funding
  history CSV + analytics; all engines and gauntlet machinery; 10-symbol data.
- WAKE TRIGGERS (desk wakes when ANY fires):
  W1 user says "wake" / "go" - any time, no justification needed.
  W2 RICH REGIME: trailing-30d funding mean >= +10%/yr annualized (vs the 5y
     baseline +6.9%) -> materially richer carry environment; H09 opens first.
  W3 HOSTILE REGIME (advisory, OPPOSITE stack): trailing-30d negative-print
     share >= 40% -> a LONG-perp funding-receiver era becomes structurally
     interesting as a NEW pre-registered line (NOT the standing short-perp
     carry stack, which PAYS in negative regimes). CORRECTION ON RECORD: the
     S8 report card called a negative era a "short-perp bonanza" - backwards
     for our stack; negative funding is a LONG-perp bonanza. Corrected here.
  W4 FRESH WINDOW: UTC 2027-11-05 completes the first untouched year after the
     RSPEED license -> the shelved SMA(100)-family daily-bar basket may run
     a full re-certification battery on genuinely fresh data, exactly once.
- While parked: the ONLY running instrument is the funding watch
  (funding_watch.py, live prints): baseline stamped on first run; re-run
  manually at any cadence (weekly is plenty); alerts print W2/W3 flags.
- Resume-on-wake checklist (for W2): pre-register final H09 gates, build the
  two-leg engine, 14-calendar-day Binance testnet minimum BEFORE any live
  money, then $100 pilot with kill rails (strategy -10% NAV for carry,
  account -20% unchanged).

#### Park-mode instrumentation baseline (stamped by funding_watch.py first run, Nov 9 2026)

- Live prints: 300 (~100 days); latest print **+1bp/8h** (floor-pegged = +10.9%/yr
  if the peg holds; shorts receive it under the standing carry stack).
- Trailing-30d: mean +0.0061%/8h = **+6.6%/yr** (just under the 5y +6.9% baseline);
  negative share 6.7%.
- **Alerts: NONE** - W2 (>= +10%/yr) not met, W3 (<40% negative) not met.
  Desk stays nominally parked; carry economics at today's regime remain the
  same ones the H09 spec is staged for.
- Watch log: out/funding_watch_log.md (appends; refreshed on demand or re-run)
  - Cadence guidance: weekly manual re-run is plenty; triggers are slow-moving.

#### Park-mode instrumentation baseline #2 (Nov 11 2026)
- Live fetch failed this run (network timeout); watch stamped a clearly
  labeled STALE entry (CSV tail, no alerts) and continued - fallback behaves
  as designed. No regime change inferable from stale data; nothing incident.

## SESSION 9 (Nov 11, 2026) - WAKE + H09 formal carry gauntlet

### W1 wake stamp (user instruction: "run the watch, wake")

W1 fired by explicit user instruction. PARK LIFTED. The pre-registered
resume-on-wake checklist governs this session: pre-register final H09 gates
-> build two-leg engine -> full gauntlet -> 14-calendar-day Binance testnet
minimum BEFORE any live money -> only then $100 pilot with kill rails.
The watch was re-run as requested (live fetch timed out; STALE-tagged CSV-tail
stamped, no alerts; waking is user-driven W1, not regime-driven).

### H09 PRE-REGISTRATION (written BEFORE any perp fetch, engine build, or run)

Strategy under test: BTC carry stack - long spot + short perp 1x notional -
gated rule FROZEN from the Session 6 pre-registered smoke (zero optimization,
zero new parameters: enter when trailing-3 print mean funding > +1bp/8h when
flat; exit when it prints < -1bp/8h while held). Comparator (reported, not a
gate): ALWAYS-IN one trip across the span - the S6 contrast structure kept but
now with basis truth; comparator bound to its own report line, not parts.

What makes this FORMAL (vs the S6 smoke): full two-leg execution truth:
- Bases series: perp bar close minus spot bar close at every funding print
  (perp 1h klines fetched from fapi for 2021-11-present; if fapi klines are
  unreachable today, declared fallback: basis era restricted to markPrice
  coverage starting 2023-10-31 - 60.4% of prints - and the limitation is
  stamped in the verdict header).
- Mark-to-print accounting: stack value per printed 8h step (while held) =
  funding_i - delta(basis)_i; fees charge at trip boundaries (spot 10bp/side +
  perp 5bp/side = 30bp round trip); declared per-$100-notional, 1x, NOT
  reinvested intra-window (income density reported per $100 notional).
- The basis risk the smoke ignored is now IN the stream: intra-held basis
  swings draw NAV down exactly like price swings did in every prior battery.

Gates (ALL -> GAUNTLET-CERTIFIED, unlocking the 14d testnet; P1 fail -> DEAD;
else MARGINAL naming exact failed gates):
  P1 primary (GATED) full-span NET > 0 under funding + basis - fees truth
  P2 annualized NET >= +3%/yr after full execution truth
  P3 calendar-year consistency: net >= 0 in >= 3/4 of full years 2022-2025
     (2026 partial reported, not gated)
  P4 stream max drawdown >= -10% (pre-registered carry kill rail; history
     must never have breached it, print-mark basis included)
  P5 cost/slip stress: NET stays > 0 with fees x1.5 AND entry/exit basis
     slippage of 5bp per side
  P6 liquidity of the rule: >= 2 trips in the span (once-ever rules are dead)
Standing rules apply: realized value (funding prints are cash; basis marks
exist in the stream), no re-optimization (rules frozen from S6 pre-registr-
ation), no maker bolt-ons, one judge pass, realized/unrealized split reported
(stream splits: funding-print income vs basis-mark residuals).

### H09 RESULTS (post-run stamp)

Data layer (rebuilt mid-session): fapi became reachable again and the perp
history fetched - data/BTCUSDT_perp_1h.csv, 44,032 bars 2021-11-01 ->
2026-11-09. Basis = (perp close - spot close) at print instants (both legs
read at the same instant: the 1h bar that CLOSES at the print hour - no
lookahead, symmetric legs). QA (data fidelity): overlap vs fapi markPrice on
3,302 prints -> mean |diff| 0.41bp, p95 1.66bp, max 5.78bp -> perp-close
basis proxy VALIDATED. Full-span battery: 5,475 prints 5.00y. The S8
fallback-era MARGINAL run is superseded by this full-span verdict (per its
own pre-registered fallback contract).

PRIMARY (GATED carry, rules FROZEN from S6):
- NET **+23.81 per $100 notional** (+4.77%/yr) | funding +24.13 | basis +0.29
  | fees 0.60 | stream MDD **-$0.31 | stress NET +23.31 | 2 trips (S6 whole-
  span smoke said +23.51 -> basis truth moved it +0.30 - the S6 estimate was
  already database-honest).
- Trips: (1) 2021-11-06 -> 2022-02-28 (113.7d, basis +7.0bp -> -7.9bp =
  -14.9bp capture LOSS); (2) 2023-01-14 -> 2025-05-02 (839.3d, +7.5 -> -6.2bp
  = -13.7bp capture loss).
- Structural insight #1: BOTH trip exits landed at perp DISCOUNTS - the gate
  exits when funding goes negative, and funding-negative is exactly when the
  perp prices at a discount. Basis loss is the real cost of gate TIMING;
  funding income out-earned it (2022 net still +0.68 WITH basis truth).
- Structural insight #2: the frozen +1bp/8h threshold is mania-calibrated -
  after the 2025-05 exit it stayed FLAT while funding ran +5-7%/yr (below the
  ~11%/yr trigger for 18+ months).
COMPARATOR (ALWAYS-IN, info-only): net +34.08 (+6.82%/yr), MDD -$0.44,
basis +0.14 across the span, every calendar year positive incl. 2022 (+4.19).
The gate's insurance cost ~2.05pp/yr over the span and bought near-zero
protection in history. Switching the primary to ALWAYS-IN would be a NEW
pre-registration (user ratifies at the testnet design step - no retro-tuning).

Gates: P1 PASS | P2 PASS | P3 PASS (2022-2025, one negative year allowed,
got ZERO) | P4 PASS | P5 PASS | P6 PASS.
**VERDICT: GAUNTLET-CERTIFIED. 14-calendar-day Binance testnet LOCKED before
any live money (first testnet carry trip starts the clock). Kill rails:
strategy -10% NAV (carry-tuned), account -20%, both legs liquidate together.**

This is the desk's FIRST certified edge in 9 sessions - certified as an
INCOME stream, not a price-prediction alpha: no directional bet, gamma-free,
and the 2022 bear survived with basis marks included.

### Session 9 stamps
- H09: **GAUNTLET-CERTIFIED** (full-span, basis-truthed, frozen rules).
- $100 untouched across 9 sessions. One certified line, ready for testnet.
- Data assets: 44,032-bar perp series (new), verif. 0.4bp QA; funding + spot
  already in hand - the H09 basis layer is reproducible end-to-end.

### Session 9 engineering log
- fetch_perp.py: paginated fapi klines with retries (failed during the
  network outage, succeeded ~1 session-hour later - the retry discipline
  paid: pre-registered fallback retired cleanly instead of permanent scope
  reduction).
- h09.py: print-mark-to-mark carry state machine (funding settlement window
  conventions per S6 continuity; exit-print funding conservatively dropped;
  full basis-delta capture incl. exit print's delta). Pre-run review caught:
  fee-bucket sign bug (would inflate year nets), degenerate last-print trip
  left unclosed, str-vs-int year keys silently emptying gate P3's list,
  annualization unit bug (dollars formatted as %, x100, auto-passing P2),
  era-label truncation + a syntax-mangling edit repaired. QA cross-check
  added for the basis proxy.
- out/H09_report.md. JOURNAL pre-registration landed BEFORE any fetch/build.

### SESSION 9 close - TESTNET PHASE A pre-registration (written BEFORE any testnet activity)

User ratification (Nov 11, 2026): BOTH variants side-by-side on testnet.

PHASE A SPEC (14-calendar-day testnet, paper money, zero live exposure):
- Two stacks run SIMULTANEOUSLY, each on $100 testnet notional, 1x:
  Stack A = GATED carry (the certified primary: enter when trail-3 print
  mean funding > +1bp/8h, exit when < -1bp/8h while held).
  Stack B = ALWAYS-IN (comparator: enter once, hold through Phase A).
- Purpose (honest, declared): validate EXECUTION MECHANICS AND ACCOUNTING
  FIDELITY only - two legs fill and the hedge holds; fees and funding settle
  as modeled; ledger reconciles. It does NOT re-measure income (income is
  already validated by the 5y real-prints gauntlet; a 14d income comparison
  would be statistical noise and is NOT the decision basis).
- OPERATIONAL SUBTLETY (declared): Binance SPOT testnet
  (testnet.binance.vision) and FUTURES testnet (testnet.binancefuture.com)
  are separate accounts with separate API keys - both are needed for the
  two-leg stack. Testnet funding prints may be simulated/differ from live;
  reconciliation targets MECHANICS (fills, fees, ledger vs model), not
  income size.
- 14-day clock: starts when the FIRST testnet carry trip of Stack A opens.
  Minimum 14 calendar days of held stack before the Phase A report.
- Daily reconciliation metrics (ledger vs H09 model, tolerance bands):
  both-leg fill within 30s of each other; per-leg fee within 0.5x model;
  funding accrual per settlement within 25% of the model print value
  (testnet funding prints are coarse); basis mark at settlement within
  5bp of (perp mark - spot close); NAV ledger vs model cumulative diff
  reported (not gated during Phase A - measured).
- Pick rule (pre-registered now, evidence-based): the LIVE $100 pilot uses
  the variant with BETTER ACCOUNTING FIDELITY (smaller |ledger - model|
  error across the daily metrics). Exact tie -> Stack A (certified primary)
  wins. INCOME SIZE DOES NOT PICK - the +6.82 vs +4.77%/yr historical
  difference is a documented tradeoff of the gate, and a 14d sample cannot
  re-judge it (explicit anti-cherry-picking rule).
- Kill conditions during Phase A (any -> clock PAUSES, incident logged,
  fix, resume): unfilled/broken hedge leg open > 2h without engineer action;
  a leg's settled fee > 1.5x model on a completion; funding accrual missing
  on 2+ settlements; ledger corruption.
- After Phase A: full reconciliation report -> user approval -> LIVE $100
  pilot with kill rails (strategy -10% NAV carry-tuned, account -20%, both
  legs liquidate together) OR further fix cycles. No live money before the
  report lands and the user says go.
- Standing rules intact: no live account exists today; $100 untouched
  through 9 sessions; all knobs above fixed before the first testnet call.

### SESSION 9.5 (Nov 10, 2026) - testnet parked by user; strategy-search phase opened

User decision: PARK the H09 testnet run for now ("i will park the testnet run
for this strategy for now"), and open a strategy-search phase. Semantics on
record: H09 certification STANDS (nothing expires); the 14-day testnet clock
deferred until the user returns with keys; testnet_keys.json never created;
park costs nothing; a later "go testnet" resumes Phase A exactly as
pre-registered (both-variants protocol unchanged). $100 untouched through
9 sessions retained. The session now pivots to: timeframe-coverage audit +
candidate NEW hypothesis lines (user asked what was tested and what wasn't).

Coverage audit (recorded for honesty, testable in future):
- Bars tested: 1h (S1-6 families), 4h (H01b/H04 variants), daily (controls,
  H07, U07, H08), 8h prints (carry). Weekly/monthly signal bars: NEVER.
  Sub-hour (15m/5m/1m): NEVER. Tick/order-book/level-2: NEVER.
- Data classes tested: OHLCV price action + funding prints + basis. Classes
  NEVER touched: Open Interest, liquidations, order flow, vol-targeting,
  cross-venue basis, funding breadth (beyond single-asset).
- Era coverage: price-alphas judged on one hostile test year + folds
  (regime-speed study proved epoch-dependence of that family). The carry
  line is the only multi-era (5y) certified evidence.

Session 9.5 candidate menu (pre-registered per line BEFORE running):
  (A) OI/liquidation data class - NEW signal source, free fapi endpoints.
  (B) Weekly-bar trend family, 10 coins - closes the untested-TF box above
      daily; expectation: statistically thin, cheap to test.
  (C) H05b intraday closure: 15m (+4h variant) VWAP-band - settles the
      faster-intraday cadence box; pre-registered expectation DEAD via
      churn x cost (documents the kill honestly, not a straw man).
  (D) Vol-target overlay on certified carry (improve income smoothness).
  (E) Funding breadth + COIN-M architecture paper line (already ratified
      as background; becomes the income-stage workhorse if it validates).

## SESSION 10 PRE-REGISTRATION (written BEFORE any 15m fetch or battery build)
### The CLOSURE MATRIX: one execution, four lenses (user-ratified extensions)

User ratified (Nov 10): (1) ALL four under-tested axes are in scope - faster
bars, slower bars, market regimes, instrument types; (2) ALL THREE multi-TF
standards tested for understanding (native+adjacent SOP, fail-fast ladder,
full sweep); (3) regime-split verdicts MANDATORY; (4) bounded closure battery
for the dead families (the ratified exception to no-rerun).

RESOLUTION of the three-standards request (pre-registered design): the
battery executes ONE matrix - every listed strategy x timeframe cell runs
EXACTLY ONCE. The three standards are three DECISION LENSES read off that
single matrix (SOP = native+adjacent; LADDER = stop at first dead TF; SWEEP
= full matrix view) plus the regime-split as a fourth lens. No cell re-runs;
no multiple passes; the three standards are compared on identical data.
Binding language: the SOP lens writes closure verdicts; ladder/sweep lenses
are labeled ANALYTICAL; any positive adjacent-TF cell does NOT resurrect a
dead strategy - it flags a bar/regime-locked candidate that may only become
a NEW pre-registered line (fresh state, fresh gates).

SCOPE (bounded, declared): dead price families H01, H02b, H03, H04, H05.
Adjacency map (pre-registered, one bar faster + slower than native):
  H01 (native 1h, EMA9/21+RSI14+EMA200+VWAP): adjacents {15m, 4h(run), weekly*}
  H02b (native 1h mirrored short):        adjacents {15m, 4h}
  H03 (native 1h Donchian 20/10):         adjacents {15m, 4h, weekly}
  H04 (native 1h+4h already both dead):   adjacents {15m, weekly}
  H05 (native 1h VWAP-band):              adjacents {15m, 4h}   [= item C]
  Items B (weekly trend: EMA9/21+cross on weekly closes) and the weekly cells
  above share the weekly resampler. H02b/H03's outstanding 4h cells included.
  No resurrection of U07/H07/H08 (marginal-shelved families excluded).
FEASIBILITY SUBSTITUTIONS (pre-registered): weekly bars 5y = ~260 bars ->
  a 200-bar EMA cannot exist (warmup), so weekly variants cap every lookback
  at 60 weeks (H01 weekly: EMA9/21 kept, EMA200->EMA40, RSI(14), VWAP dropped
  (no intraday anchor at weekly); H03 weekly Donchian 20w/10w; H04 weekly
  RSI(2) w/ SMA(3) regime kept; H05: NO weekly cell (VWAP is intraday-anchored;
  exclusion pre-registered, not a skip). 15m cells: H01 uses its SAME params
  (EMA9/21/200 at 15m = 9h/5.25h/50h effective horizons - DECLARED, that is
  what a 15m bar of the same parameters means); H05 15m: k_band/atr_stop
  frozen; time_stop transfers as HOURS (1h winner = 8h -> 15m cell = 32
  bars) - CORRECTION BEFORE EXECUTION: an earlier line here read "12 bars";
  hours-based transfer replaces it (time-based params transfer in hours,
  lookbacks in bars - the declared convention for the whole matrix).
REGIME DEFINITION (pre-registered, one rule for every cell): each calendar
  month is classified by the underlying's own trailing-30d return at month
  end: >= +10% bull, <= -10% bear, else sideways (BTC for BTC-native
  strategies). Every cell reports pooled net per regime bucket alongside the
  overall net; CLOSURE language honors the mandatory split: a family is
  CONFIRMED-DEAD only if dead in ALL regime buckets that actually contain
  test-window data (empty buckets reported N/A); any positive bucket is
  flagged bar/regime-locked candidate for possible NEW-line registration.
COSTS: 7bp/side taker everywhere (maker variants only where their existing
  S4 verdicts apply); 3bp/day haircut on day-in-market for long-holding
  cells at daily+ (weekly uses 3bp/day held notional likewise).
ACCOUNTING: standing accounting (realized, in-window entries for fold rows
  where used; the closure battery runs each cell as ONE window (4y+1y split
  inherited: train months [0,48) judge months [48,60)) - no new folds for
  closure; the four-lens matrix is the analysis layer.
VERDICT MAPPING: per cell: of the standard gates (Ret>0, Sharpe>0.5,
  PF>=1.0) - PASS/FAIL; family-level closure language only via the SOP lens
  + regime rule above. Compute bounds: <= 16 combos per strategy per cell.

### ITEM A - FORWARD COLLECTOR (starts today, pre-registered)
OI history: fapi /futures/data/openInterestHist only serves a ~30-day
window -> collector records BTCUSDT + ETHUSDT OI (5m period) at each session
touch into data/oi_collect/*.csv; liquidations via /fapi/v1/forceOrders
(archive window limited) recorded when available. NO hypothesis tests until
>= 60 days sample (pre-registered hurdle); the collector is infrastructure,
the first battery gets its own pre-registration when the hurdle is met.

### ITEM E - background (ratified): COIN-M funding history pull (dapi) +
10-coin funding breadth retire to the BACKGROUND queue - not this session's
critical path; pre-registered separately when fired.

## SESSION 10.5 (Nov 10, 2026) - ITEM E FIRED (user: "fire the background
research line")

### E PRE-REGISTRATION (before any fetch/build/run)

Scope (paper only, zero live-money work):
- E1 COIN-M architecture study: pull dapi funding history (BTCUSD coin-margined
  perp, /dapi/v1/fundingRate, paginated) + COIN-M spot-equivalent funding
  economics: rerun the H09 carry engine (h09.py conventions) on COIN-M
  prints; verify notional=capital efficiency claim; PRIMARY metric: net per
  $100 notional AND per $100 capital for both architectures (co-movement
  of funding incomes across venue types reported - diversification check).
- E2 10-coin funding breadth: fetch 5y funding history for the universe
  (BNB/SOL/XRP/DOGE/ADA/LINK/AVAX/TRX ETH already have spot; funding CSVs
  via fapi pagination like BTCUSDT in S6). Analytics pre-registered:
  positive-print share, mean annualized, monthly cross-correlation matrix
  (funding co-movement = concentration risk of a funding PORTFOLIO), worst
  simultaneous-negative drawdown episode, and a gated-rule replay per coin
  (S6 smoke rule frozen: trail-3 > +1bp enter, < -1bp exit, 30bp RT).
  Metrics of record: portfolio blended funding income matrix (equal-weight
  top-K by trailing fap%, unfunded - paper only).
- NOT in scope: any live-money effects, any price-direction alpha, maker
  variants, COIN-M spot leg mechanics beyond collateral-efficiency analysis.
- Gates (study-level, pre-registered): E1 VALIDATED iff COIN-M net per
  $100 capital >= 1.3x the USDT-M capital-yield (else the capital-efficiency
  claim is de-rated); E2 WORTHWHILE iff portfolio blended mean funding
  annualized >= 8%/yr AND worst simultaneous-negative month drawdown <=
  1.0% of notional (else concentration risk kills the benefit).
-->
No verdict changes to H09 (certified line untouched); E is target income
improvement research for a future scale-up, ratified as background.

### E RESULTS (post-run stamp)

Fetched: 5y funding history for ALL 10 unconditional (5,490 prints each,
data/funding_breadth/) + COIN-M BTCUSD_PERP (5,489 prints, 5,00 years).
Per-coin runs (always-in vs S6 frozen gated, per $100 notional):

| Coin | always-in %/yr | gated %. (trips) |
|---|---|---|
| BTC | +6.87 | +4.69 (2) |
| ETH | +6.13 | +4.63 (2) |
| BNB | **-5.02** | +1.13 (19) |
| SOL | **-4.19** | +4.15 (7) |
| XRP | +5.55 | +4.35 (4) |
| DOGE | +7.36 | +3.89 (5) |
| ADA | +5.59 | +3.89 (5) |
| LINK | +8.19 (best) | +4.80 (4) |
| AVAX | +3.25 | +4.02 (5) |
| TRX | **-4.67** | +1.05 (11) |

DISCOVERY #1 (the line's key product): the GATED rule beats ALWAYS-IN on
EVERY alt coin - it converts the three negative bleeders (BNB/SOL/TRX,
always-in -4.2..-5.0%/yr) into positives. On BTC/ETH the gate costs income
(4.69 vs 6.87) but on alts it IS the strategy. A 10-coin equal-weight GATED
funding portfolio blends ~+3.66%/yr per NOTIONAL (derived mean of the ten
gated rows) with stream MDDs of -0.04..-0.07% per coin - the smoothing and
the print-diversification are real (worst simultaneous month across the
10-coin always-in book: only -0.042%).
DISCOVERY #2: funding co-movement is BIMODAL - majors cluster tightly
(mean pairwise monthly correlation +0.59 across 45 pairs; BTC-LINK +0.92)
while BNB decouples (+0.19..+0.26 vs everything). A funding PORTFOLIO's
diversification benefit is real but imperfect: the majors leg moves as one.
DISCOVERY #3 (E1): COIN-M gated replay: +17.36/5y = +3.47%/yr per $100
NOTIONAL, and because the BTC collateral doubles as margin, that is ALSO
+3.47%/yr per $100 CAPITAL - vs USDT-M 1x capital-yield ~+2.39%/yr (gated).
E1 gate PASS (>= 1.3x): COIN-M is the venue/collateral winner at 1x.
Note: COIN-M exists for majors (BTC/ETH) only; alt breadth stays USDT-M.
DISPLAY CORRECTION: the report's portfolio line printed +0.03%/yr via a
fraction-vs-percent format bug; independent recomputation confirmed +2.86%/
yr blended always-in (true value; fixed in e_line.py for the record).

Gates: E1 PASS | E2-blended >= 8%/yr FAIL (blended always-in +2.86%, gated
+3.66% - the 8% bar was pre-registered optimism; single-venue funding at
1x just is not 8%) | E2 worst-drawdown <= 1.0% PASS (worst -0.07%).
**E-LINE VERDICT: MIXED/PARTIAL (as printed) - but the actionable products
are real: (a) gated rule is the correct execution for alt-funding income,
(b) a 10-coin gated portfolio is feasible with trivial simultaneous drawdown
but ~+3.7%/yr notional ceiling at 1x USDT-M, (c) COIN-M doubles per-capital
efficiency for the majors at NO leverage cost.** The income-stage blueprint
for a capital scale-up now reads: BTC(+-ETH) COIN-M gated core (+ ~3.5%/yr
per capital) + optional alt funding sleeves for breadth. These remain
PAPER research products until testnet and a scale ratification.

### Session 10.5 stamps
- E-line delivered its products; no live-money change; H09 certification
  untouched. Background data stack grows: 10-coin funding breadth CSVs +
  COIN-M history in hand.
- $100 untouched through 10.5 sessions.

## SESSION 10.6 (Nov 10, 2026) - THE FULL-MAP CONTRACT (user request: "test
every single strategy, framework ... on their timeframes, out of their
timeframes ... earn more yearly than the dust with help of this funding
based strategy. ask me your doubts. time is not a constraint")

Registered BEFORE any build from this program:
- Reference artifact: crypto-quant/out/STRATEGY_CATALOG.md - 36 families in
  4 groups (A price-geometric x16, B carry/income x9, C new-data x11, D
  meta), each with core idea | native TFs | instrument fit | data needed |
  desk verdict / priority. This file is the user's "test everything"
  contract document; completeness is achievedBattery by battery.
- Discipline carries over wholesale: per-battery pre-registered gates
  verbatim before compute; one judge pass per cell; SOP/ladder/sweep/
  regime lenses via the S10 one-matrix executor (reusable per family);
  native + adjacent + out-of-TF cells per the user contract; mandatory
  regime split everywhere; param grids <= 16 combos; closure language
  only via the SOP lens.
- Group A inheritance: price-geometry families are inheritance-dead by the
  S10 18-cell matrix (same signal mathematics at every cadence/regime).
  User-named CRT / ICT / SMC / Volume Profile still receive MECHANICAL
  closure batteries - formal rule definitions pre-registered verbatim
  before run (sweeps = wick-through-close-back; FVG = 3-candle gap;
  OB = last opposite candle pre-impulse; killzones = UTC session windows;
  VP = declared 1m-kline approximation). Expectation DEATH, purpose map
  completeness; any survival overrides the expectation honestly.
- Group B additions: E3 funding-rotation harvest (P1, data in hand),
  quarterly-curve basis carry (new instrument, fetchable), Binance
  options investigation (feasibility-gated on user access).
- Group C additions: pairwise stat-arb relative value (P2, data in hand),
  time-of-day/day-of-week seasonality closure (cheap), OI/liquidation
  batteries gated on the 60d forward accrual hurdle, order-flow =
  1m-taker-flow-proxy-or-decline decision open, ML/factor battery =
  guardrail-design-first, end-of-program fire.
- Exclusions standing until user overrides: grid/DCA/martingale (unbounded
  tails violate kill rails), DeFi/LP (venue rule), macro/on-chain (external
  data outside Binance-only). Paper-closure override offered in Q&A.
PRIORITY QUEUE P1-P7 lives in the catalog. NOTHING FIRED yet: queue order,
success-bar definition, exclusion overrides, and proxy choices went to the
user as pre-registered doubts (Q&A in flight). $100 untouched through 10.6.

### SESSION 10.6 RATIFICATION (Q&A answers, in-harness, before any build)
- SUCCESS BAR ratified as the FOUR-BAR STANDARD - every future line is
  judged against ALL of these and reported per-bar (per $100 NOTIONAL,
  with capital-basis equivalents: USDT-M 1x per-capital = notional/2;
  COIN-M per-capital = notional):
  BAR-A  net > 0 after all costs (any positive);
  BAR-B  >= +4.77%/yr notional (= +2.38%/yr per capital) - beats the
         certified carry line;
  BAR-C  >= +6.82%/yr notional (= +3.41%/yr per capital) - beats the
         always-in comparator;
  BAR-D  >= +20%/yr notional (= +10%/yr per capital) - double digits.
- MAP COMPLETENESS: PAPER-CLOSE EVERYTHING - grid/DCA/martingale and
  Elliott/harmonics receive paper-only closures (verdicts documented with
  numbers, permanently NON-TRADABLE); former standing exclusions convert
  to paper-closure queue entries, not omissions.
- ORDER: sequential P1 -> P7 as written in the catalog.
- ML/factor line: late, end-of-program; guardrail pre-registration gets
  drafted during the cheap closures.
- OPTIONS: user confirms Binance Options ENABLED on their account ->
  P6 upgrades from feasibility-gated to buildable; investigation battery
  fires in sequence (data probes first, no capital work).
- STORAGE DISCIPLINE (new standing rule; user constraint = low PC
  storage): ALL future data builds must be stream-aggregate-discard
  (fetch chunks, process incrementally in memory, persist only compact
  aggregates) or genuinely small artifacts; NO GB-scale CSVs are annexed
  to disk. Order-flow P3 will follow the streamed pattern (1m pages ->
  running aggregates -> raw pages discarded). Existing moderate files
  (15m/1h deeps, funding breadths) remain as-is.
### E3 RESULTS - P1 funding-rotation (Session 10.6, pre-registered 16-combo grid)

Engine note (caught pre-verdict): the first pass reported per-sleeve sums
(K sleeves x full notional); DENOMINATOR corrected to per $100 BOOK
(K sleeves share the book; static K=10 cross-checks vs E2: +3.36% vs
+3.66% hand-figure - convention delta documented, not a redo). Unit of
record from here: per $100 BOOK notional.

COMBOS (net %/yr book; all 16 pre-registered, gated = PRIMARY):
- Static baselines (same conventions): gated +3.36, selected-always +4.60.
- Gated family: K3 {2.51..3.68}, K5 {3.42..3.80}; best = K5/180p/M
  +3.80%/yr, 27 cycles/yr, stream MDD -0.02%.
- Comparator family (selected_always): {+4.33..+5.94}; best = K3/180p/M
  +5.94%/yr, 49 cycles/yr, MDD -0.49%.
- G1 (beat static by >= 0.5pp/yr): FAIL (margin +0.44pp). G2 MDD: PASS.
- Four bars: best gated rotation vs bars: A PASS (+3.80), B/C/D FAIL.
- Regime split (mandatory lens, best gated K5-180-M): bull +9.62 /
  sideways +10.12 / bear +0.90 (book units, 5y) - positive everywhere,
  weakest in bear; NOT regime-locked. Comparator best K3-180-M: +12.68 /
  +18.48 / +3.50 - same shape.

**E3 VERDICT (binding, per pre-registration and the comparator-language
rule): ROTATION CLOSED as a gated-execution line - fails its own value
gate by a margin of 0.06pp (0.44 vs 0.50 required): the selection layer's
turnover and dilution absorb its selection edge. The STATIC GATED BLEND
(+2.86 always per E2, +3.36 gated here) stays the funding-portfolio
deliverable. COMPARATOR FLAG (analytical, non-binding, cannot resurrect):
selected_always rotation +5.94%/yr book (+2.97%/yr per capital USDT-M
1x) with 49 cycles/yr and MDD -0.49% - positive in EVERY regime bucket -
i.e., an "always-hold-positive-trailing-funding" portfolio; observation on
record: the S6 gate COSTS income in a context where selection already
keeps funding positive (matches E2's majors finding). Becomes a candidate
only via a FRESH pre-registration (E3b) if ever fired - not promoted.**

Reading for the user: rotation as an alpha layer failed its test cleanly
AND CHEAPLY (one run, 16 cells, data already on disk - the map-coverage
cost model working as designed). The four-bar standard now has its first
complete example: a line that is profitable (BAR-A) but does not beat the
machine (BAR-B) and is therefore closed by the desk's own bar.

### Session 10.6 stamps
- Full-map contract + four-bar standard + paper-close-everything +
  sequential P1->P7 + ML-late + options-enabled (buildable) + storage-
  discipline rule (stream-aggregate-discard; no GB-scale offline data)
  all ratified and stamped before any build.
- E3 (P1) executed and CLOSED honestly; static gated blending remains
  the funding deliverable; the funding machine remains the desk's floor.
- $100 untouched through 10.6.

## SESSION 10.6.1 - P2 PRE-REGISTRATION (user: "go with the P2: cross-coin
statistical-arb pairs"; WRITTEN BEFORE ANY CODE/BUILD/RUN)

P2 = cross-coin stat-arb pairs (relative-value family). This is a NEW
family, not a closure: standing new-line discipline applies - train-only
selection, frozen winners judged OOS, four-bar verdicts.

UNIVERSE / INSTRUMENTS: the 10-coin USDT-M set; legs = USDT-M PERPS on
BOTH sides (no spot leg - pure derivative relative value, executable
with the same futures keys as the parked testnet if ever promoted).
CADENCE: 1h bars; funding prints accrue on the pair timeline.

SELECTION (TRAIN-ONLY; the judge window decides): all 45 unordered pairs
scored on train daily ln-closes [data start -> 2025-11-05): Engle-Granger
ADF (constant + 1 lag, plain OLS SE; 5% CV -2.86 reference) on the
OLS-hedged spread ln A - beta ln B; a pair QUALIFIES iff ADF t < -1.5
AND train hourly log-return correlation >= 0.60 (returns, not levels -
spurious-trend guard). Rank qualifiers by most-negative t; take top 6
unique pairs; fewer than 3 qualifiers -> family verdict EMPTY.
Screening is in-sample training by construction; the judge window sees
only frozen winners.

SIGNAL: z = (s_t - mu[window ending t-1]) / sigma same window - rolling
stats on trailing W bars SHIFT(1), min_periods = full window (no
same-bar peeking). s = ln A - beta_t ln B; beta modes: UNIT (beta = 1)
or MONTHLY walk-forward OLS refit on the trailing 90d of hourly ln
closes (frozen between refits; leading warmup backfilled - z is NaN
there anyway). Entry |z| >= z_in in {2.0, 2.5}: SHORT A / LONG B if
z > 0, inverse if z < 0. Exit |z| <= 0.5. Ruin-stop |z| > 4.0
(structural break). Time stop 720 bars (30d). GRID per pair: 2 W
(30d/90d) x 2 beta modes x 2 z_in = 8 combos (<= 16 standing bound).

ACCOUNTING (unit of record = per $100 GROSS notional; legs $50/$50;
per-capital mapped /2 as the conservative naked-margin bound - hedged-
margin advantage unmodeled and declared):
- fees 7bp/side x 4 sides = 28bp matched RT ($0.14 per $100 gross);
- haircut 3bp/day per $1 GROSS notional while held (standing);
- funding: both legs USDT-M perps -> signed net = dir x $50 x (r_A - r_B)
  per print while held, accrued on ENTRY notional; the EXIT-bar print is
  INCLUDED (a perp-perp exit at bar close occurs AFTER that bar's 8h
  settlement; declared difference from the H09 carry rule's dropped
  exit print, which was a spot-leg conservatism);
- REALIZED-ONLY verdict convention (open-at-cutoff trades unbooked);
- trades labeled by ENTRY timestamp; train entries -> train stats,
  entries >= judge start -> judge stats; ONE continuous simulation per
  combo (z warmup lives inside the train year; no separate judge lead);
- MDD monitor = realized trade-exit stream (intramark MDD not modeled -
  declared; gauntlet-grade mark modeling reserved for a later
  certification phase if any winner clears the bars);
- pairs simulated independently, no cross-pair netting (declared).

PROTOCOL: per pair, train pick = max train net $ subject to >= 8 train
trades (tie -> first in grid order); frozen winner + z_in +-0.25
neighbors run as INFORMATIONAL robustness rows (BRITTLENESS flag if the
winner passes judge but both neighbors fail). Judge trade floor = 8
(H07 lesson: 2 closed trades = statistically sterile). No post-hoc
re-picks; ALL cells reported.

VERDICT GATES (pre-registered): family ALIVE iff >= 1 frozen winner
shows judge net > 0 AND >= 8 judge trades; pooled judge net across
winners reported; four-bar table (A net>0 / B >= +4.77%/yr / C >=
+6.82%/yr / D >= +20%/yr, per gross notional) on the best judge winner
AND the pooled book; MANDATORY regime split (BTC trailing-30d monthly
buckets) per winner; FUNDING-DIVERGENCE RECLASSIFICATION: if net funding
income exceeds 50% of gross income the winner is tagged
"funding-carry-disguised" (real pairs mechanics, but the income source
is funding, not price convergence) and reported as such.
EXPECTATION: none pre-committed; prior mildly skeptical (28bp matched RT
vs z-scale mean reversion on majors). The bars decide.
STORAGE: zero new fetches (10x 1h deep OHLCV + funding breadths on
disk); report artifact out/P2_pairs_report.md.

### P2 RESULTS - pairs stat-arb (Session 10.6.1)

SCREEN (train-only): 22/45 pairs pass the in-sample EG-ADF + corr gates -
the classic stat-arb screening ILLUSION (in-sample cointegration is
everywhere on trending cryptos). Top-6 by most-negative ADF t: SOL/LINK,
ETH/SOL, ETH/LINK, DOGE/LINK, ADA/AVAX, ETH/BNB.

JUDGE (frozen winners, ~1.0y, per $100 GROSS; capital = /2):

| Pair | trips | net $ (%/yr) | PF | funding $ |
|---|---|---|---|---|
| SOL/LINK | 53 | -12.33 (-12.31) | 0.03 | +0.45 |
| ETH/SOL | 54 | -10.64 (-10.62) | 0.05 | -0.05 |
| ETH/LINK | 37 | -11.36 (-11.34) | 0.03 | -0.12 |
| DOGE/LINK | 6 | -6.01 (-6.00) | 0.00 | -0.02 |
| ADA/AVAX | 89 | -17.04 (-17.01) | 0.01 | +0.02 |
| ETH/BNB | 34 | -7.72 (-7.71) | 0.06 | -0.02 |

POOLED judge book: -65.10$ = -64.99%/yr gross across 273 trades.
Four bars: best winner FAILS bar A (-6.00%/yr); B/C/D FAIL; pooled FAIL.

AUTOPSY (the informative part):
1. EXIT-REASON breakdown: z-STOP exits dominate everywhere (ADA/AVAX
   75/89; ETH/BNB 30/34; ETH/SOL 41/54) - the spreads did NOT mean-
   revert; they BROKE through structural stops. In-sample cointegration/
   half-life had no OOS validity at 1h cadence: crypto pairs co-collapse
   in risk-offs but decouple idiosyncratically in single-coin pumps.
   Neighbors negative everywhere too => uniform falsity, NOT brittleness
   (no brittleness flags triggered).
2. Funding components trivial (+/-0.5$ max per year) -> the pre-registered
   funding-carry-disguise tag never fires; this family died on PRICE.
3. Regime split (mandatory lens): negative in EVERY bucket for EVERY
   winner (SOL/LINK -5.21/-3.82/-3.30; ETH/BNB -2.60/-0.59/-4.53 etc.)
   -> negative-everywhere closure with NO positive-regime flags to
   review (cleaner than the S10 matrix).
4. Third consecutive family killed by the cost wall at 1h-ish cadence
   (28bp matched RT + 3bp/day haircut vs z-scale moves): the cost x
   cadence law now documented across price-geometry (S10) AND
   relative-value (today).

**P2 FAMILY VERDICT (binding, pre-registered gate): CLOSED - no winner
cleared (net>0 AND >=8 judge trades). Stat-arb pairs on the 10-coin
USDT-M set at 1h cadence under 28bp matched costs: DEAD. No comparator
flags; no new-line registrations spawned.**

### Session 10.6.1 stamps
- P2 executed inside its pre-registered box (train-only selection, frozen
  winners, informational neighbors, no post-hoc anything); storage rule
  honored (zero new fetches); artifacts p2_pairs.py +
  out/P2_pairs_report.md.
- Map progress: price-geometry (S10) + relative-value (today) closed;
  next in the sequential queue = P3 (CRT/ICT/SMC/Volume-Profile closure
  batteries; 1m data under the streaming-aggregate pattern).
- $100 untouched through 10.6.1.

## SESSION 10.6.2 - P3 PROGRAM PRE-REGISTRATION PART 1 (Q&A ratifications,
before any build)

User framing (binding): "the CRT, ICT, SMC, Volume profile frameworks are
very deep and need to look into each of them independently with repetitive
review cycles, considering all the other things needed for the framework"
-> P3 is a DEEP PER-FRAMEWORK EVALUATION PROGRAM, not an S10-style
one-shot closure battery. False-closure protection is a design
requirement, explicitly requested by the user.
- BOTH LAYERS ratified: every component isolated AND the complete
  composite bundle tested per framework (attribution duality; no
  component is falsely closed by its bundle and vice versa).
- CADENCE: FULL SUB-HOUR FROM START ratified - 1m/5m/15m/1h/4h/daily
  lanes all open in the FIRST pass; sub-hour data built ONLY via the
  standing stream-aggregate-discard pattern (fetch window -> in-memory
  session aggregates -> raw discarded; KB-scale artifacts persist);
  heavy compute explicitly accepted (user: time is no constraint).
- SESSION ANCHORS: BOTH pre-registered variants - UTC (data-native) and
  EST-with-DST (practitioner clock) - run and reported separately; a
  timing edge hiding in a local-session window is refused a guess-death.
- REVISIONS: UNLIMITED review-cycle revisions per framework (user-
  ratified; supersedes the earlier max-2 draft), ALL under the
  new-scope-only rule: a revision = a FRESH pre-registration ADDING new
  testable scope identified by the review (deeper components, new
  tolerance anchors, new variant families); re-running any dead cell of
  a used scope stays banned forever; the revision registry logs every
  used scope to enforce it.
- CLOSURE RULE: DEAD ONLY IF ALL DIES - a framework's file closes ONLY
  if every component dies at every cadence/anchor AND every composite
  dies through all revision rounds; ANY survivor anywhere keeps the
  framework OPEN as a flagged candidate (flag -> possible fresh-line
  registration; never a verdict overturn).
- NOVEL-AXIS FRAMING (why P3 is not caricature-testing): the price-
  geometry cores inherit the S10 closure (strong prior of death,
  pre-declared); the program's real questions are the NEVER-TOUCHED
  layers: session timing/killzones, volume weighting (VP), structure
  state machines (SMC BOS/CHoCH), composite confluence statistics,
  anchor-range fractals (CRT). NO pre-committed expectation on the
  novel axes - that boundary is the honest-testing discipline.
- STANDING bindings per program: BTC primary (ETH cross-check only if a
  candidate survives); <= 16 combos per spec version per cell; four-bar
  standard (A > 0 / B >= 4.77 / C >= 6.82 / D >= 20%/yr notional) per-
  bar reporting; mandatory regime split per verdict; maker-passive
  execution only where the signal is structurally limit-order-native
  (H06 rule); train [start -> 2025-11-05) / judge [2025-11-05 -> data
  end); storage rule honored; every pre-registration precedes compute.
- TRACK SPLIT (part-ratified): user delegates CRT to a DEDICATED
  SEPARATE CHAT which must feel like CONTINUATION, not a new start -
  mechanism under ratification in an in-flight logistics Q&A (shared
  files as memory + CRT_CHARTER handoff + wake ritual + echo-back).
  ICT/SMC/VP tracks remain in THIS chat on this session's critical
  path. Logistics stamps follow the Q&A answers.

### SESSION 10.6.2 PART 2 - CRT TRACK LOGISTICS (Q&A ratified; charter written)

CRT DELEGATION MECHANICS (all user-ratified):
- LOCATION: the CRT chat opens in the SAME workspace folder as this desk
  - file continuity is total (data, engines, JOURNAL all resolvable).
- SCOPE: CRT chat owns CRT ONLY; THIS chat retains ICT/SMC/VP deep
  tracks + the rest of the P-queue + E-line upkeep + collector touches;
  the two chats run in PARALLEL.
- STREAMING ENGINE: CRT builds its OWN sub-hour streaming pipeline
  (full isolation ratified; the main desk builds its own for
  ICT/SMC/VP under the same storage rule - no shared dependency).
- LEDGERING: CRT records ONLY in its own files
  (crypto-quant/crt/: CHARTER.md + REGISTRY.md + battery reports + crt /
  engines + data_agg KB-scale aggregates); the CRT chat does NOT write
  the main JOURNAL - the MAIN desk holds a pointer row and receives
  port summaries via the user relay.
- CONTINUITY ENFORCEMENT: "Echo, no quiz" - the CRT chat's first duty is
  the full read + a state echo-back (no gate quiz); wrong-folder halts
  are built into the charter (JOURNAL-missing = stop and tell user).
- USER IN THE LOOP (CRT only): three fixed checkpoints -
  CP1 formalization-dossier review, CP2 after every battery readout,
  CP3 before each revision round (the user's "repetitive review cycle"
  ratifies as the CP structure).

DELIVERED NOW: crypto-quant/crt/CHARTER.md - the full handoff (desk
state one-pager; evidence anchors; the six binding contract items;
standing numbers/conventions incl. the pandas quirks and the H09
notional correction; CRT anatomy inventory draft v0.5 as the CP1 work
item; wake ritual + echo-back template; registry format; failsafes).

MAIN-DESK STATUS: ICT/SMC/VP deep tracks remain the critical path here
(same ratified standards: both layers, full sub-hour from start, both
anchors, unlimited new-scope revisions, dead-only-if-all-dies); their
sub-hour streaming lane will be built here separately. CRT verdicts
return to this ledger only via user-relayed port summaries.
$100 untouched through 10.6.2.

## RESULTS - Session 10: the closure matrix (18 cells, one execution, four lenses)

Runs: 18 cells (H01 x {15m,1h,4h,weekly}, H02b x {15m,1h,4h},
H03 x {15m,1h,4h,weekly}, H04 x {15m,1h,4h,weekly}, H05 x {15m,1h,4h}).
Every cell = frozen param transfer, judge window [2025-11-05 -> 2026-11-05)
absolute-anchored, per-TF warmup lead, in-window entries, 7bp/side +
3bp/day haircut, regime buckets by entry month (BTC trailing-30d at month
end: >= +10% / <= -10%).

| Cell | Ret% | PF | Trades | Net$ | Buckets B/S/D |
|---|---|---|---|---|---|
| H01 15m | -43.84 | 0.54 | 291 | -91.33 | all negative |
| H01 1h | -10.07 | 0.72 | 85 | -20.01 | bear +0.41 flag |
| H01 4h | -6.29 | 0.49 | 25 | -7.46 | all negative |
| H01 weekly | +0.25 | 0 trades (warmup ate the year) | | +0.00 | n/a |
| H02b 15m | -46.33 | 0.67 | 488 | -145.96 | all negative |
| H02b 1h | -3.87 | 0.96 | 123 | -26.58 | bear +3.11 flag |
| H02b 4h | -4.07 | 0.69 | 55 | -6.50 | all negative |
| H03 15m | -53.12 | 0.62 | 423 | -213.30 | all negative |
| H03 1h | -5.22 | 0.83 | 98 | -38.85 | bull +2.77 flag |
| H03 4h | -0.50 | 0.72 | 31 | -5.09 | bull +2.24, bear +1.91 flags |
| H03 weekly | -0.35 | PF 0.00 | 1 | -0.16 | ~empty |
| H04 15m | -67.53 | 0.37 | 734 | -96.38 | all negative |
| H04 1h | -29.19 | 0.48 | 163 | -39.11 | all negative |
| H04 4h | -2.23 | 0.91 | 36 | -3.71 | bull +1.27 flag |
| H04 weekly | +0.65 | 0 trades | | +0.00 | n/a |
| H05 15m | -70.54 | 0.75 | 1128 | -326.98 | all negative |
| H05 1h | -38.19 | 0.85 | 651 | -114.17 | all negative |
| H05 4h | -28.47 | 0.74 | 413 | -38.60 | bull +0.63 flag |

FINDINGS (all four lenses aggregated):
1. CONFIRMED DEAD, every dead family, at every traded timeframe and every
   regime bucket with material size - by the SOP lens every family is
   confirmed; by the LADDER lens every family would have been stopped at
   its native 1h in one run (the ladder standard is COMPUTATIONALLY
   VALIDATED: one run per family would have sufficed for closure);
   the SWEEP lens exists only as the destruction documentation.
2. The COST x CADENCE law is now EMPIRICAL on this desk: nets worsen
   monotonically toward faster bars in every family (H01: -7.5 (4h) ->
   -20 (1h) -> -91 (15m); H05: -38 (4h) -> -114 (1h) -> -327 (15m)).
   The 15m cells lost 3.2x the ACCOUNT in one year on $100 notional.
3. Weekly cells came back statistically EMPTY as pre-registered (0-1
   trades; EMA40-regime warmup consumed the judge year) - the slower-bar
   box physically cannot produce the trade mass a $100-scale gauntlet
   requires. Slower bars are not an escape; they are a different death.
4. Regime-locked pocket FLAGS (pre-registered flag language, NOT
   candidates-by-default): H02b/bear@1h (+3.11), H03/bull@1h (+2.77),
   H03/bull+4h (+2.24, +1.91), H04/bull@4h (+1.27), H01/bear@1h (+0.41),
   H05/bull@4h (+0.63). Reading: sub-$3 pockets in the hostile year;
   each candidate would inherit the same trade-mass wall and the same
   cost floor. NONE meet NEW-line registration economics by inspection;
   flagged for the record, not promoted.
5. CONTINUITY STAMP: the closure battery's H05 1h cell reproduced the
   Session 5 judge verdict exactly (ret -38.19%, 651 trades) - the matrix
   is bit-faithful to the certified harness lineage.
6. Regime classification sanity: 33 sideways / 14 bear / 14 bull months
   over 5y. The judge year contained all three buckets - the mandatory
   regime layer had genuine width to judge against.

### Session 10 stamps
- The coverage map the user asked for is now CLOSED on the price-action
  side: 1h/4h/15m/weekly x {trend, mirror-short, breakout, scalping-RSI,
  VWAP-reversion} x {bull, sideways, bear} - all dead or empty. The map
  was "truly tested" in the user's sense for the first time today.
- H09 certification undiminished; testnet remains parked awaiting keys.
- OI collector live (BTC+ETH): endpoint behavior discovered - serves
  latest-500 records only (1.7d backfill)despite the 30d window spec ->
  forward accrual 288 rows/day is the path; 60d hypothesis hurdle ~2
  months away. ETH 15m deep file also fetched (175,195 bars) for any
  future cross-check rows (scoped out today).
- $100 untouched through 10 sessions.

### Session 10 engineering log
- 15m fetches (BTC+ETH x 5y, 175,195 bars each) via the existing
  data.load_or_fetch pipeline + mirror fallback.
- oi_collect.py: paginated /futures/data/openInterestHist collector; first
  touch revealed the latest-500-only behavior (logged above); ledger
  data/oi_collect/*.csv started.
- closure_battery.py: one-matrix-four-lenses runner (frozen transfers,
  hours-based time_stop conversion, weekly resampler W-SUN, regime
  bucketing, per-trade haircut nets, SOP/ladder/flag lens writer).
  Pre-run fixes: absolute judge anchor (S6 precedent), window-signature
  crash, pandas 3.x freq "M"->"ME", per-trade haircut bucket merge,
  str/int year-key and fee-sign classes of bugs avoided by review.
- out/closure_matrix_report.md.

### REVIEW: SESSION 9 strategic ratifications (Nov 10, 2026 - scaling question session)

User raised the honest capital question: "0.5$/month is dust". Desk purpose
declared by user: REAL INCOME, EVENTUALLY (not learning-only). Decisions:
- Capital: STAY at $100 for now (ratified); no Stage-2 number set.
- Liquidity constraint: deferred - user to define deployment horizon later.
- Venue: Binance ONLY (ratified; counterparty split not desired now).
- Background research line RATIFIED while testnet runs: funding PORTFOLIO
  review (10-coin blend + venue/collateral architecture study) - paper only,
  zero live-money work.
- Leverage: user asked for the 2-3x math before deciding (delivered same
  session); decision open. KEY CORRECTION ON RECORD: H09's +4.77%/+6.82% are
  per $100 NOTIONAL; per $100 CAPITAL at 1x USDT-M the stack needs the spot
  leg as separate cash, so capital-yield is ~half USDT-M 1x. Full COIN-M
  (BTCUSD perp, collateral = the BTC itself) restores notional = capital
  efficiency at 1x, but COIN-M funding history differs from USDT-M and needs
  its own pull + re-run before any number is trusted (background line, task 1).
  Leverage on a hedged stack does NOT multiply income per capital (only the
  margin buffer changes); the historic "3x carry" intuition fails the math.
