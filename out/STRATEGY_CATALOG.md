# STRATEGY CATALOG - crypto trading frameworks, complete desk map
(Section 10.6 reference artifact, Nov 10, 2026. Companion doc to JOURNAL;
this is the "test every single strategy" contract the user ratified.)

Each family: [core idea] | [typical TFs] | [instrument fit] | [data needed] |
[desk verdict / priority]. Verdicts cite the desk's own evidence where it
exists; "NEW DATA" families are honest about fetchability.

## GROUP A - PRICE-GEOMETRIC FAMILIES (the "reading the chart" world)
Desk evidence: ALL CONFIRMED DEAD at 7bp/side across {15m,1h,4h,weekly} x
{bull,sideways,bear} (S10 closure matrix). Minus-cadence math: faster = worse;
slower = empty. Re-testing frameworks in this group = re-running geometry
reframes of an already-closed family. Closure value only (cheap, data-ready),
not edge value.
1. Chart patterns (H&S, triangles, flags, wedges, cup-handle) | all TFs |
   VPA needed | dead-family geometry.
2. Candlestick patterns ( engulfing, pin bars, hammers) | intraday/1h/4h |
   dead-family geometry.
3. Trendlines/parallel channels | all TFs | subjective-formalization cost high.
4. Support/Resistance & range trading | all TFs | dead-family geometry.
5. Moving-average systems (golden/death crosses, ribbons) | all TFs | dead
   family (MA wrappers of S10 families).
6. Donchian/range breakouts (~Turtles) | 1h+.4h/d | TESTED (H03) dead at all
   adjacents.
7. Mean reversion orthodox (RSI, bollinger, K-D, z-score fades) | intraday+ |
   TESTED (H04/H05) dead.
8. Breakout+failed-breakout (bull/bear traps) | all TFs | dead family.
9. Wyckoff (accumulation/distribution phases, springs/PS) | H4+ | subjective
   formalization; mechanical proxies overlap 4/6/8.
10. Elliott waves / harmonic (Gartley etc.) | subjective, non-falsifiable
    mechanically without pattern-matching tolerances (tolerances kill OOS
    honesty); not recommended for mechanical discipline.
11. **CRT** (Candle Range Theory: range formed by the first candle(duration
    anchor), sweep of high/low = liquidity grab, then range reversal) |
    intraday 15m/5m + 1h/4h | pure OHLC geometry -> CAN mechanical-test cheap
    (formalization: range = first N-bar range; sweep = wick beyond + close
    back in). CLOSURE-VALUE (expect same death); user-named so registered.
12. **ICT concepts** (Fair Value Gaps = 3-candle imbalance; Order Blocks =
    last opposite candle before impulsive; liquidity sweeps; killzone
    session windows; market structure shifts) | 5m..4h | pure OHLC geometry
    -> mechanical battery possible (pre-register formalizations verbatim);
    expectation: same family death; session timing (killzones) is a NEW
    cadence axis (cheap add).
13. SMC (Smart Money Concepts; liquidity pools + OB confluence) | as 12.
14. **Volume Profile** (POC/VAH/VAL, R-threshold profiles, algorithm HVN/LVN)
    | intraday/1h | REAL VP needs intrabar distribution (tick/level-2):
    Binance klines only give OHLCV per bar -> VP must be APPROXIMATED from
    finer klines (1m aggregate) - declared approximation (APX level).
    New geometry axis (volume-weighted levels); honest novelty ABOVE other
    Group-A entries because volume weighting is a genuinely different input.
    Data: BTC 1m 5y = ~2.6M rows (fetchable, heavy-ish); test as P3.
15. Scalping as a class (entry/exit in minutes) | 1m-15m | cost-law dead
    unless maker-native (S4 evidence limits that); martingale/grid variants
    BANNED by risk rails (unbounded tail).
16. DCA/gridbots | any | negative-EV constructions vs drift+vol at our cost
    box; tails violate kill rails; excluded by standing rule.

## GROUP B - CARRY / INCOME FAMILIES (the desk's live currency)
17. Funding carry 1-asset (long spot + short perp) | 8h prints | **CERTIFIED
    (H09)**; closed-form income ~+4.77%/yr gated (per notional).
18. Funding breadth portfolio (10-coin gated rotation-free blend; alts gated
    flips by coin) | printed S10.5: ~+3.66%/yr blend; all-positive sleeves.
19. **Funding-rotation harvest (E3 - buildable NOW)**: weekly/monthly
    selection: direct carry sleeves at the highest-trailing-funding coins;
    expect LINK/DOGE-class yields; test whether rotation fees turnover
    beats static blend. Data IN HAND (10 x 5y prints). PRIORITY NOW.
20. COIN-M architecture (collateral = spot leg) | validated +3.47%/yr per
    capital (E1 PASS); majors only; scale-up core.
21. **Futures calendar basis / quarterly curve carry** (short expensive
    quarterly vs perp when curve steep; plus perp-quarterly flip at
    settlement) | instrument = quarterly contracts | NEW INSTRUMENT CLASS
    notwithstanding same repo-mechanics; data: fapi quarterly klines +
    funding-adjacent expectations; fetchable. Candidate (income).
22. Spot-perp basis beyond funding (dislocation arb at print times) | study
    level from existing basis series; microstructure thin ($100 book) but
    measurable. Medium.
23. Staking/on-chain yields on majors (Simple Earn) | spot | passive BTC ---
    yields ~0.5-2%/yr; stackable additive but immaterial vs funding;
    venue-products change over time; low priority.
24. DeFi/AMM-LP yields | out-of-venue (user: Binance only) + gas/mev risk;
    excluded by venue rule unless user revisits.
25. Options income (covered calls, cash-secured puts, vol selling) |
    NEW instrument class IF Binance options available to the user (India
    access/liquidity constraints unknown -> investigation required before
    any build). Long-dated options vols on Binance are thin; prior work
    needed. Registered as investigation line (not a battery).

## GROUP C - NEW-DATA FAMILIES (signal sources beyond price+candle)
26. Open Interest dynamics (OI change/price-divergence, OI-weighted
    squeezes) | fapi/futures/data/openInterestHist forward-collected (60d
    hurdle accruing; latest-500 limitation known); FORWARD-ONLY study.
27. Liquidation cascades (available/forceOrders + stream) | same window
    limitation; collector planned post-keys testnet usage; FORWARD ONLY.
28. Order flow / level-2 imbalance, CVD | genuinely new signal but data is
    heavy (aggTrades historical TBs) -> DECLINED for now unless manually
    incurred; partial proxy: 1m-candle taker-flow approximation possible;
    medium-priority data build.
29. Premium-index dislocation snapshots (fapi /premiumIndex) | free +
    instant; forward collection candidate alongside OI (premium basis
    extremes as funding-rotation inputs). Cheap add to OI collector.
30. Funding-rate-as-signal families (momentum/acceleration/rotation) |
    data IN HAND; overlaps E3 (19) with rotation; part of E3.
31. Cross-coin statistical arbitrage (cointegrated relative-value pairs,
    z-scored spreads; BTC-ETH is canonical) | daily/4h cadence; genuine NEW
    STRUCTURE (relative value, market-neutral-ish) different from
    cross-sectional momentum (trend-based; H08 dead-family). Data IN HAND
    (10 x 5y OHLCV). PRIORITY CANDIDATE - pairs-spreading has documented
    literature and cadence-friendliness (moderate trade counts); regime
    split applies. Top pick for "new signal mathematics" not-yet-closed.
32. Calendar/seasonality (time-of-day, day-of-week, month-of-year patterns)
    | all TFs | genuinely untested cadence axis; data in hand; statistical
    thinness risk high but cheap to close (median-hours incomes battery).
33. Macro-driven regimes (DXY, rates, equity flows) | external data; outside
    Binance-only desk; deferred until user asks.
34. On-chain metrics (SOPR, exchange flows, MVRV) | external data sources
    (paid), not fetchable from Binance; deferred.
35. ML/factor models (classifiers on feature bundles, Deep approaches)
    | high overfitting surface; needs strict pre-registered feature/is/CV
    guardrails; CLOSURE-NOT-STARTED; registered as a later phase after the
    cheap closures; the honest defense = tiny feature count + long OOS.
36. Portfolio overlays (vol-target sizing, Kelly caps, regime overlays)
    | E-line adjunct; queued (D) for AFTER a positive income stack.

## GROUP D - META
- Every battery: pre-registered gates verbatim before any compute; one judge
  pass; the 4-lens matrix (SOP/ladder/sweep/regime) reads negated families;
  no-resurrection rule: any positive adjacent-bucket -> NEW-line registration.
- Standing text: H09 certification is the desk's STRUCTURAL income floor;
  everything above is about (i) closing the map, (ii) finding additional
  income streams to stack with carry, (iii) finding the %improvement that
  makes a SCALE-UP worthwhile when the user ratifies capital.

PRIORITY QUEUE (proposal, pending user ratification) - STATUS after S10.6:
  P1 E3 funding-rotation harvest -> EXECUTED + CLOSED (gated fails its
     value gate by 0.06pp; comparator selected-always flagged, non-binding).
  P2 cross-coin stat-arb pairs -> EXECUTED + CLOSED (frozen winners pooled
     -64.99%/yr gross OOS; z-stop breakouts dominate; no flags spawned).
  P3 CRT/ICT/SMC/VP deep program -> RATIFIED as a deep per-framework
     evaluation (both layers, full sub-hour, both anchors, unlimited
     new-scope revisions, dead-only-if-all-dies). CRT DELEGATED to a
     dedicated parallel chat (crypto-quant/crt/CHARTER.md owns the
     handoff: read-first map, contract, anatomy inventory, wake ritual).
     ICT/SMC/VP remain on THIS desk's critical path.  <- ACTIVE HERE
  P4 quarterly-curve carry study (income instrument; fetchable).
  P5 time-of-day/seasonality closure (cheap).
  P6 options investigation (user confirms access ENABLED -> buildable).
  P7 OI battery (hurdle ~2 months out).
