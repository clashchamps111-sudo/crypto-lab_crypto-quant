# crypto-quant

Personal algo-trading research desk. Goal: validate crypto strategies honestly, automate them,
run them live with small capital, then scale.

## Golden rules (non-negotiable)
1. Nothing goes live before: walk-forward OOS backtest -> parameter robustness -> >=14 days Binance testnet.
2. Every backtest carries real costs (see `config.COMMISSION_PER_SIDE`).
3. Optimizer never sees the test window. TEST column = the only truth.
4. Kill rails (locked in `config.py`): strategy -15% drawdown = dead. Account -20% = stop everything.
5. Data: Binance public klines (UTC). Universe: BTC first, ETH second.

## How to run
```bat
cd crypto-quant
python -m pip install -r requirements.txt
python data.py            :: download/cache BTCUSDT + ETHUSDT, 1h + 4h (2 years)
python run_backtest.py    :: H01 walk-forward, writes out/H01_report.md
```

## Structure
- `config.py` - every knob in one place (costs, risk rails, walk-forward splits)
- `data.py` - downloader + cache (`data/*.csv`)
- `indicators.py` - EMA / Wilder RSI / ATR / session VWAP (lookahead-safe)
- `strategies.py` - Hypothesis 1: TrendPullback (EMA9/21 + RSI + EMA200, optional VWAP)
- `run_backtest.py` - walk-forward harness -> `out/H01_report.md`
- `JOURNAL.md` - what the agent did, decision log, hypothesis queue. Read this for reporting.

## Hypothesis queue
| ID | Idea | Status |
|---|---|---|
| H01a/b | Trend-pullback: EMA9/21 + RSI + EMA200 (+VWAP) | DEAD (all 4 variants lose OOS) |
| H02 | Mirrored short on perp 1x | DEAD: 4 market variants + **maker variant (H06b) DEAD** - churn ratchet forensics in JOURNAL |
| H03 | Donchian 20/10 breakout, ATR stop | 2y MARGINAL archived; **maker variant (H06a) MARGINAL** (fold-inconsistent, blended-cost floor fails) |
| H04 | RSI(2) mean reversion in bull regime | DEAD (both timeframes) |
| H00 | Audit positive controls (daily momentum / SMA regime) | BOTH GATES PASS -> harness certified green (H00a fully realized) |
| H05 | VWAP-band mean reversion (1h) | **DEAD** (train -99.3%/4387 trades churned; test -38.2% vs B&H -22.7%) |
| H06 | Maker-only limit-entry cost layer | **TESTED: bolt-on maker execution rejected by evidence**; signal-native passive design remains possible |
| H07 | Daily-bar funding-aware carry/momentum | **MARGINAL** (net +3.9% in hostile year, 67% neighbors positive, but 2 closed trades = statistically sterile at our scale) |
| U07 | Universe battery: H00a identity on 10-symbol basket | **MARGINAL** (pooled net +8.52 across 61 trades, 6/10 symbols positive; B3 fails 33% neighbors; SMA(100) family uniform-positive vs SMA(150)/200 uniform-NEGATIVE -> regime-speed finding) |
| CARRY | Funding-carry study (5y BTCUSDT) | Study-level CONFIRMED structural income (85.1% positive prints, mean +6.9%/yr; gated smoke +23.51 net/5y vs always-in +34.04 w/ unmodeled bear-regime risk); formal H09 gauntlet queued |
| H08 | Cross-sectional momentum on 10-symbol universe | **DEAD** (frozen winner r=30/K=2: train +198.09 then test realized -64.66, folds 0/4, all 10 LOO negative, triple-worse than B&H; class-level kill, not one-name luck) |
| RSPEED | Regime-speed confirmatory study (train 2022-24 -> judge 2025-26) | **TRANSFER FAILS** (2022-24 picked 150/30 by an $8.29 noise margin; it lost on judge; speed is epoch-dependent, not persistent) -> daily-bar alpha line SHELVED, pivot condition COMPLETE |
| CLOSE | Closure matrix (S10): dead families x {15m,1h,4h,weekly} x {bull/sideways/bear} | **CONFIRMED DEAD, all 5 families, all 18 cells** - cost x cadence law empirical (nets worsen monotonically toward faster bars; 15m cells lost 3x account); weekly empty; continuity: H05 1h reproduces S5 to 2dp |
| H09 | Formal funding-carry gauntlet (basis/slip, 2-leg, bear stress) | **GAUNTLET-CERTIFIED** (full-span 5y, basis truth via perp closes, QA 0.41bp vs marks: gated rule net +23.81 (+4.77%/yr), MDD -$0.31, 2 trips, all 6 gates PASS; always-in comparator +34.08 (+6.82%/yr)) -> **14d Binance testnet LOCKED before live money** |
| OILN | OI/liquidation forward collector (S10) | LIVE: BTC+ETH 5m OI accruing (latest-500 endpoint limitation discovered; 60d hypothesis hurdle ~2 months) |
| E3 | P1 funding-rotation harvest (S10.6) | **CLOSED honestly** (16-combo grid, one run): best gated rotation +3.80%/yr book failed its own value gate (margin +0.44pp < 0.50 required) -> static gated blend stays the funding deliverable. Comparator flag (non-binding): selected-always rotation +5.94%/yr book, positive every regime bucket, 49 cycles/yr - E3b candidate only via fresh pre-registration |
| P2 | Cross-coin stat-arb pairs (S10.6.1) | **CLOSED**: 22/45 pairs pass in-sample ADF/corr (screening illusion), 6 frozen winners judged OOS -> pooled **-64.99%/yr gross**, 273 trades, z-STOP exits dominate (spreads BREAK, not revert); funding trivial (no carry-disguise); negative every regime bucket; no flags spawned |
| P3 | Deep framework program: CRT / ICT / SMC / VP (S10.6.2) | **RATIFIED & SPLIT**: both layers (component+composite), full sub-hour from start (1m/5m streamed), both session anchors (UTC + EST-DST), unlimited new-scope revisions, DEAD ONLY IF ALL DIES closure. **CRT -> delegated to its own dedicated chat** (charter: crypto-quant/crt/CHARTER.md; own files; 3 user checkpoints: CP1 formalization, CP2 per-battery, CP3 pre-revision). ICT/SMC/VP -> THIS desk (critical path) |
| QUOTE | P1->P7 full-map program (S10.6) | RATIFIED: four-bar standard every line (A net>0, B >=4.77, C >=6.82, D >=20%/yr notional), paper-close-everything incl. grid/Elliott, sequential queue, ML late, options ENABLED (buildable), storage = stream-aggregate-discard |
| E | Funding breadth + COIN-M study (S10.5) | **PRODUCTS DELIVERED**: gated rule flips every alt positive (10-coin gated blend ~+3.66%/yr notional, worst simultaneous month -0.042%); COIN-M doubles per-capital yield (+3.47 vs +2.39%/yr gated, E1 gate PASS); E2 8%/yr gate FAILED honestly (1x funding is not 8%); majors correlate mean +0.59, BNB decouples; scale-up blueprint: COIN-M majors core + alt sleeves |

Audit (Session 3): engine forensics FAITHFUL (119 entries bar-verified, 0 violations) ->
verdicts stand. Standing rules: realized/unrealized split on every window verdict;
cost-at-which-alive must be stated; controls re-run after any harness change.
Gauntlet (Session 4): both audit-flipped maker-candidates judged - H02-maker DEAD,
H03-maker MARGINAL (not certified). No testnet; nothing gauntlet-certified yet.
Session 5: H05 DEAD (intraday reversion churn+costs), H07 MARGINAL (daily-regime
ground works but 2-4 trades/yr = statistically sterile at $100 scale).
Session 6: strategic review ratified -> universe widening (primary) + carry (side).
Universe battery MARGINAL (pooled +8.52/61 trades; neighbor stability fails;
regime-speed is the variable), carry study confirms structural income (~6.8%/yr
always-in pre-bear-risk). Session 7 queued: H08 cross-sectional momentum first.
Session 7: controls re-run SEAL PASS (harness certified green post-compaction;
all verdicts stand). H08 cross-sectional momentum DEAD (train +198 -> test -64.66,
folds 0/4, diffuse losses, class-level kill). Pivot condition 50% evaluated;
Session 8 = regime-speed study (confirmatory) which decides the pivot.
Session 8: regime-speed TRANSFER FAILS (daily-bar alpha line shelved; pivot
condition COMPLETE). Bear-stress groundwork de-risks carry (funding stream MDD
-0.41pp always-in; risk migrates to basis/execution).

**DESK PARKED (Nov 9, 2026) - WOKEN Nov 11, 2026**
W1 wake ("run the watch, wake"); H09 formal carry gauntlet ->
**GAUNTLET-CERTIFIED** (full-span 5y basis truth, QA 0.41bp vs marks; gated
rule +23.81 net per $100 notional, +4.77%/yr, MDD -$0.31, 2 trips, survived
2022 with basis marks; always-in comparator +34.08/+6.82%). Testnet Phase A
pre-registered (both variants, fidelity-pick rule) but PARKED by user Nov 10
before keys - clock resumes on "go testnet". Leverage math delivered:
per-$100-notional corrected to per-capital (~half at 1x USDT-M); COIN-M
capital-efficiency queued as background study.

**SESSION 10 (Nov 10): the user's coverage question fully executed.**
Timeframes audited (1h/4h/daily/8h tested - 15m/weekly/tick never) ->
closure matrix: 18 cells (H01/H02b/H03/H04/H05 x 15m/1h/4h/weekly,
regime-split lens, frozen transfers) -> **ALL dead families CONFIRMED DEAD
at every timeframe and every regime bucket**; cost x cadence law empirical
(15m cells lost up to 3x the account in a year); weekly cells statistically
empty; H05 1h cell reproduces the S5 verdict to 2dp (harness continuity).
OI forward-collector live (BTC+ETH; 60d hypothesis hurdle ~2 months out).
ETH 15m deep (175k bars) cached for any future cross-check rows.
$100 untouched through 10 sessions.

**SESSION 10.6 (Nov 10): FULL-MAP PROGRAM RATIFIED + P1 EXECUTED.**
User contract = test every framework (STRATEGY_CATALOG.md: 36 families,
P1-P7 queue) under the four-bar standard (A/B/C/D), paper-close-everything
(incl. grid/martingale/Elliott as never-tradable closures), mandatory
regime split, sequential queue, ML late, options ENABLED per user, new
STORAGE RULE (stream-aggregate-discard; no GB-scale data on this PC).
P1 E3 funding-rotation: CLOSED honestly (best gated +3.80%/yr book vs
static +3.36% - below the +0.5pp/yr complexity bar; comparator
selected-always +5.94% flagged non-binding, every-regime-positive).
P2 cross-coin stat-arb pairs: CLOSED (train screen passed 22/45 pairs -
in-sample illusion; frozen winners pooled -64.99%/yr gross OOS; z-stop
breakouts dominate; negative every regime bucket).
$100 untouched through 10.6.
