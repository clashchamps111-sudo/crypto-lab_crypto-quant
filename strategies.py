"""Hypothesis #1: Trend Pullback - the friend's stack (EMA 9/21 + RSI [+VWAP])
implemented with proper regime filter, risk sizing, stops. Long-only."""
import numpy as np
import pandas as pd

from backtesting import Strategy

from indicators import atr_w, ema, rsi_w


class TrendPullback(Strategy):
    n_fast = 9        # EMA fast (pullback anchor)
    n_slow = 21       # EMA slow (trend check)
    n_regime = 200    # EMA regime filter: only long above it
    n_rsi = 14
    n_atr = 14
    rsi_lo = 40
    rsi_hi = 65
    atr_stop = 1.5    # stop distance in ATRs
    atr_tgt = 3.0     # target distance in ATRs
    risk_pct = 0.01   # fraction of equity risked per trade
    time_stop = 24    # exit after N bars if nothing happened
    use_vwap = False  # H01b adds a daily-VWAP confirmation
    _vwap = None      # per-split VWAP array injected by the runner (no lookahead)

    def init(self):
        self.ema_f = self.I(lambda x: ema(x, self.n_fast), self.data.Close, name=f"EMA{self.n_fast}")
        self.ema_s = self.I(lambda x: ema(x, self.n_slow), self.data.Close, name=f"EMA{self.n_slow}")
        self.ema_r = self.I(lambda x: ema(x, self.n_regime), self.data.Close, name=f"EMA{self.n_regime}")
        self.rsi = self.I(lambda x: rsi_w(x, self.n_rsi), self.data.Close, name="RSI")
        self.atr = self.I(
            lambda: atr_w(np.asarray(self.data.High), np.asarray(self.data.Low),
                          np.asarray(self.data.Close), self.n_atr),
            name="ATR",
        )
        self._entry_i = -1

    def next(self):
        c = float(self.data.Close[-1])
        if (np.isnan(self.ema_r[-1]) or np.isnan(self.rsi[-1]) or np.isnan(self.atr[-1])):
            return

        # Regime gate: out of a broken trend immediately.
        if c < float(self.ema_r[-1]) or float(self.ema_f[-1]) <= float(self.ema_s[-1]):
            if self.position:
                self.position.close()
            self._entry_i = -1
            return

        if self.position:
            if self._entry_i > 0 and (len(self.data.Close) - self._entry_i) >= self.time_stop:
                self.position.close()
                self._entry_i = -1
            return  # SL/TP manage the open trade

        pullback_touch = float(self.data.Low[-1]) <= float(self.ema_f[-1])
        close_above = c > float(self.ema_f[-1])
        rsi_ok = self.rsi_lo <= float(self.rsi[-1]) <= self.rsi_hi
        vwap_ok = True
        if self.use_vwap and self._vwap is not None:
            v = float(np.asarray(self._vwap, dtype=float)[-1])
            vwap_ok = np.isfinite(v) and c > v

        if pullback_touch and close_above and rsi_ok and vwap_ok:
            entry = c
            stop = entry - self.atr_stop * float(self.atr[-1])
            unit_risk = entry - stop
            if unit_risk <= 0:
                return
            # backtesting.py: size<1 = fraction of equity. notional_frac * stop_dist% = risk%.
            stop_dist_pct = unit_risk / entry
            frac = self.risk_pct / stop_dist_pct
            frac = min(frac, 0.98)  # hard 1x notional cap (max leverage)
            if frac <= 0:
                return
            self.buy(size=frac, sl=stop, tp=entry + self.atr_tgt * float(self.atr[-1]))
            self._entry_i = len(self.data.Close)


class ShortTrendPullback(TrendPullback):
    """H02: exact mirror of H01 in bear regime, executed as a perp short at 1x.
    Bear regime: price below EMA200 AND EMA9 < EMA21. Rally pulls price UP to the
    fast EMA, bar closes back below it, RSI shows bearish momentum (mirrored band:
    35..60 - momentum present, not yet oversold). Same ATR brackets, time stop."""
    rsi_lo = 35   # mirrored band
    rsi_hi = 60

    def next(self):
        c = float(self.data.Close[-1])
        if np.isnan(self.ema_r[-1]) or np.isnan(self.rsi[-1]) or np.isnan(self.atr[-1]):
            return

        # Mirror regime gate: out when bull conditions return.
        if c > float(self.ema_r[-1]) or float(self.ema_f[-1]) >= float(self.ema_s[-1]):
            if self.position:
                self.position.close()
            self._entry_i = -1
            return

        if self.position:
            if self._entry_i > 0 and (len(self.data.Close) - self._entry_i) >= self.time_stop:
                self.position.close()
                self._entry_i = -1
            return  # SL/TP manage the open trade

        pullback_up = float(self.data.High[-1]) >= float(self.ema_f[-1])
        close_below = c < float(self.ema_f[-1])
        rsi_ok = self.rsi_lo <= float(self.rsi[-1]) <= self.rsi_hi
        vwap_ok = True
        if self.use_vwap and self._vwap is not None:
            v = float(np.asarray(self._vwap, dtype=float)[-1])
            vwap_ok = np.isfinite(v) and c < v

        if pullback_up and close_below and rsi_ok and vwap_ok:
            entry = c
            stop = entry + self.atr_stop * float(self.atr[-1])
            unit_risk = stop - entry
            if unit_risk <= 0:
                return
            stop_dist_pct = unit_risk / entry
            frac = min(self.risk_pct / stop_dist_pct, 0.98)
            if frac <= 0:
                return
            self.sell(size=frac, sl=stop, tp=entry - self.atr_tgt * float(self.atr[-1]))
            self._entry_i = len(self.data.Close)


class DonchianBreakout(Strategy):
    """H03: classic 20/10 Donchian breakout, long-only, bull-regime gated.
    Entry: close crosses ABOVE the max high of the previous n_enter bars.
    Exit: close falls BELOW the min low of the previous n_exit bars, ATR stop, or time stop.
    No profit target - this rides trends."""
    n_enter = 20
    n_exit = 10
    n_regime = 200
    n_atr = 14
    atr_stop = 2.5
    risk_pct = 0.01
    time_stop = 50

    def init(self):
        self.ema_r = self.I(lambda x: ema(x, self.n_regime), self.data.Close, name="EMAreg")
        self.atr = self.I(
            lambda: atr_w(np.asarray(self.data.High), np.asarray(self.data.Low),
                          np.asarray(self.data.Close), self.n_atr),
            name="ATR")
        self.hh = self.I(lambda x: pd.Series(x).rolling(int(self.n_enter)).max().shift(1),
                         self.data.High, name=f"HH{self.n_enter}")
        self.ll = self.I(lambda x: pd.Series(x).rolling(int(self.n_exit)).min().shift(1),
                         self.data.Low, name=f"LL{self.n_exit}")
        self._entry_i = -1

    def next(self):
        c = float(self.data.Close[-1])
        if np.isnan(self.atr[-1]) or np.isnan(self.ema_r[-1]) or np.isnan(self.hh[-1]) or np.isnan(self.ll[-1]):
            return
        if self.position:
            if c < float(self.ll[-1]):
                self.position.close()
                self._entry_i = -1
                return
            if self._entry_i > 0 and (len(self.data.Close) - self._entry_i) >= self.time_stop:
                self.position.close()
                self._entry_i = -1
            return
        if c > float(self.hh[-1]) and c > float(self.ema_r[-1]):
            stop = c - self.atr_stop * float(self.atr[-1])
            unit_risk = c - stop
            if unit_risk <= 0:
                return
            stop_dist_pct = unit_risk / c
            frac = min(self.risk_pct / stop_dist_pct, 0.98)
            if frac <= 0:
                return
            self.buy(size=frac, sl=stop)
            self._entry_i = len(self.data.Close)


class Rsi2Reversion(Strategy):
    """H04: Connors-style RSI(2) dip-buying inside a bull regime.
    Entry: RSI(n_rsi) collapses <= rsi_buy while price is above the EMA200 regime.
    Exit: close back above the n_ema_exit EMA, ATR stop, or time stop."""
    n_rsi = 2
    rsi_buy = 10
    n_regime = 200
    n_ema_exit = 9
    n_atr = 14
    atr_stop = 2.0
    risk_pct = 0.01
    time_stop = 48

    def init(self):
        self.ema_r = self.I(lambda x: ema(x, self.n_regime), self.data.Close, name="EMAreg")
        self.ema_x = self.I(lambda x: ema(x, self.n_ema_exit), self.data.Close, name="EMAexit")
        self.atr = self.I(
            lambda: atr_w(np.asarray(self.data.High), np.asarray(self.data.Low),
                          np.asarray(self.data.Close), self.n_atr),
            name="ATR")
        self.rsi = self.I(lambda x: rsi_w(x, self.n_rsi), self.data.Close, name="RSI2")
        self._entry_i = -1

    def next(self):
        c = float(self.data.Close[-1])
        if np.isnan(self.atr[-1]) or np.isnan(self.ema_r[-1]) or np.isnan(self.rsi[-1]) or np.isnan(self.ema_x[-1]):
            return
        if self.position:
            if c > float(self.ema_x[-1]):
                self.position.close()
                self._entry_i = -1
                return
            if self._entry_i > 0 and (len(self.data.Close) - self._entry_i) >= self.time_stop:
                self.position.close()
                self._entry_i = -1
            return  # SL handles disaster bars; otherwise hold for reversion
        if float(self.rsi[-1]) <= self.rsi_buy and c > float(self.ema_r[-1]):
            stop = c - self.atr_stop * float(self.atr[-1])
            unit_risk = c - stop
            if unit_risk <= 0:
                return
            stop_dist_pct = unit_risk / c
            frac = min(self.risk_pct / stop_dist_pct, 0.98)
            if frac <= 0:
                return
            self.buy(size=frac, sl=stop)
            self._entry_i = len(self.data.Close)


class DailyMomentum(Strategy):
    """AUDIT CONTROL H00a: daily time-series momentum, documented edge class in
    BTC literature. Long only while: close > SMA(n_sma) AND n_roc-day return > 0.
    ATR stop as disaster brake, regime exit otherwise."""
    n_sma = 100
    n_roc = 30
    n_atr = 14
    atr_stop = 2.0
    risk_pct = 0.01

    def init(self):
        self.sma = self.I(lambda x: pd.Series(x).rolling(int(self.n_sma)).mean(),
                          self.data.Close, name=f"SMA{self.n_sma}")
        self.ro = self.I(lambda x: pd.Series(x).pct_change(int(self.n_roc)),
                         self.data.Close, name=f"RoC{self.n_roc}")
        self.atrv = self.I(
            lambda: atr_w(np.asarray(self.data.High), np.asarray(self.data.Low),
                          np.asarray(self.data.Close), self.n_atr),
            name="ATR")

    def next(self):
        c = float(self.data.Close[-1])
        if np.isnan(self.sma[-1]) or np.isnan(self.ro[-1]) or np.isnan(self.atrv[-1]):
            return
        in_regime = c > float(self.sma[-1]) and float(self.ro[-1]) > 0
        if self.position:
            if not in_regime:
                self.position.close()
            return
        if not in_regime:
            return
        stop = c - self.atr_stop * float(self.atrv[-1])
        stop_dist_pct = (c - stop) / c
        if stop_dist_pct <= 0:
            return
        frac = min(self.risk_pct / stop_dist_pct, 0.98)
        self.buy(size=frac, sl=stop)


class DailyRegime(Strategy):
    """AUDIT CONTROL H00b: pure SMA-regime filter (documented robust behavior:
    long above SMA, cash below), no momentum term."""
    n_sma = 100
    risk_pct = 0.01

    def init(self):
        self.sma = self.I(lambda x: pd.Series(x).rolling(int(self.n_sma)).mean(),
                          self.data.Close, name=f"SMA{self.n_sma}")

    def next(self):
        c = float(self.data.Close[-1])
        if np.isnan(self.sma[-1]):
            return
        in_regime = c > float(self.sma[-1])
        if self.position and not in_regime:
            self.position.close()
            return
        if self.position or not in_regime:
            return
        self.buy(size=0.95)  # all-equity regime holding; no stop, exit is the filter


class MakerMixIn:
    """H06 mechanics shared by both maker variants (source-verified in
    backtesting 0.6.6): a limit order rests until the market returns to it
    (buy fills when bar.low <= limit at min(open, limit); sell fills when
    bar.high >= limit at max(open, limit)), and with exclusive_orders=True a
    fresh signal auto-cancels the previous pending order, so re-placing the
    limit each repeating signal IS a cancel-and-replace chase. We additionally
    hard-cancel on regime break or after fill_wait bars without a fill."""
    fill_wait = 2  # bars a resting limit survives without a fill
    _ord = None
    _ord_i = -1

    def _cancel_pending(self):
        if self._ord is not None and self._ord in self.orders:
            self._ord.cancel()
        self._ord = None

    def _age_ok(self):
        return (len(self.data.Close) - self._ord_i) <= self.fill_wait


class DonchianMaker(DonchianBreakout, MakerMixIn):
    """H06a: H03 Donchian with a PASSIVE maker entry. Signals frozen from the
    audit-flipped params (1h deep: n_enter=20, n_exit=10, atr_stop=3.0).
    Entry: LIMIT buy resting at the signal close (chase/re-place while the
    breakout+regime signal repeats; cancel on regime break or fill_wait expiry).
    A runaway breakout that never returns = deliberately missed fill (the
    fill-miss premium passive entries pay). Exits unchanged: LL-break close,
    time stop, SL bracket - realized as takers in reality, so the honest cost
    bracket for this variant is 2bp entry + 7bp exit ~= 4.5bp/side blended."""
    # entry cheaply re-derived: place limit, not market
    def next(self):  # replaces DonchianBreakout.next entirely
        c = float(self.data.Close[-1])
        if np.isnan(self.atr[-1]) or np.isnan(self.ema_r[-1]) or np.isnan(self.hh[-1]) or np.isnan(self.ll[-1]):
            return

        if self.position:
            if c < float(self.ll[-1]):
                self.position.close()
                self._entry_i = -1
                return
            if self._entry_i > 0 and (len(self.data.Close) - self._entry_i) >= self.time_stop:
                self.position.close()
                self._entry_i = -1
                return
            self._ord = None  # pending got filled somewhere earlier
            return

        # not in position: if regime broke or wait expired -> cancel resting limit
        if self._ord is not None:
            if c < float(self.ema_r[-1]) or not self._age_ok():
                self._cancel_pending()

        signal = c > float(self.hh[-1]) and c > float(self.ema_r[-1])
        if signal:
            stop = c - self.atr_stop * float(self.atr[-1])
            if stop >= c:
                return
            stop_dist_pct = (c - stop) / c
            frac = min(self.risk_pct / stop_dist_pct, 0.98)
            if frac <= 0:
                return
            self._ord = self.buy(size=frac, limit=c, sl=stop)
            self._ord_i = len(self.data.Close)


class MakerShortPullback(ShortTrendPullback, MakerMixIn):
    """H06b: H02b (mirror short + VWAP) with a PASSIVE maker entry. Signals frozen
    from audit params (1h: n_fast=9, atr_stop=2.5, rsi 35..60, use_vwap=True).
    Entry: LIMIT sell resting at the signal close (chase while the pullback-up
    signal repeats; cancel on regime break or fill_wait expiry). Exits: TP as
    limit (maker-eligible), SL / time stop / regime break as takers -> blended
    bracket reported. Time-stop counter set at FILL, not at signal."""
    def next(self):
        c = float(self.data.Close[-1])
        if np.isnan(self.ema_r[-1]) or np.isnan(self.rsi[-1]) or np.isnan(self.atr[-1]):
            return

        if self.position:
            # fill detection: time-stop counter starts at fill bar (approx one
            # bar granularity - next() runs after the broker filled the order)
            if self._entry_i < 0:
                self._entry_i = len(self.data.Close)
            self._ord = None
            if c > float(self.ema_r[-1]) or float(self.ema_f[-1]) >= float(self.ema_s[-1]):
                self.position.close()
                self._entry_i = -1
                return
            if self._entry_i > 0 and (len(self.data.Close) - self._entry_i) >= self.time_stop:
                self.position.close()
                self._entry_i = -1
                return
            return  # SL/TP manage the open trade

        if self._ord is not None:
            broken = c > float(self.ema_r[-1]) or float(self.ema_f[-1]) >= float(self.ema_s[-1])
            if broken or not self._age_ok():
                self._cancel_pending()

        pullback_up = float(self.data.High[-1]) >= float(self.ema_f[-1])
        close_below = c < float(self.ema_f[-1])
        rsi_ok = self.rsi_lo <= float(self.rsi[-1]) <= self.rsi_hi
        vwap_ok = True
        if self.use_vwap and self._vwap is not None:
            v = float(np.asarray(self._vwap, dtype=float)[-1])
            vwap_ok = np.isfinite(v) and c < v

        if pullback_up and close_below and rsi_ok and vwap_ok:
            stop = c + self.atr_stop * float(self.atr[-1])
            tp = c - self.atr_tgt * float(self.atr[-1])
            if tp >= c or stop <= c:  # degenerate brackets
                return
            stop_dist_pct = (stop - c) / c
            frac = min(self.risk_pct / stop_dist_pct, 0.98)
            if frac <= 0:
                return
            self._ord = self.sell(size=frac, limit=c, sl=stop, tp=tp)
            self._ord_i = len(self.data.Close)


class VwapBandReversion(Strategy):
    """H05: VWAP-band intraday mean reversion, 1h bars, LONG only,
    conventional market execution (maker-as-bolt-on is banned by H06 evidence).
    Entry: close drops below the daily VWAP minus k_band * daily volume-weighted
    sigma (first min_bars hours of each UTC day masked NaN by the runner).
    Exit: close back at/above VWAP (reversion complete), ATR stop, or time stop.
    No profit target - the anchor touch IS the target."""
    k_band = 1.5
    n_atr = 14
    atr_stop = 2.0
    risk_pct = 0.01
    time_stop = 12        # hours; reversion windows are short
    _vwap = None          # injected by the runner (lookahead-safe arrays)
    _sig = None

    def init(self):
        self.atr = self.I(
            lambda: atr_w(np.asarray(self.data.High), np.asarray(self.data.Low),
                          np.asarray(self.data.Close), self.n_atr),
            name="ATR")
        self._entry_i = -1

    def next(self):
        c = float(self.data.Close[-1])
        if np.isnan(self.atr[-1]):
            return
        v = float(np.asarray(self._vwap, dtype=float)[-1]) if self._vwap is not None else np.nan
        s = float(np.asarray(self._sig, dtype=float)[-1]) if self._sig is not None else np.nan

        if self.position:
            if np.isfinite(v) and c >= v:
                self.position.close()
                self._entry_i = -1
                return
            if self._entry_i > 0 and (len(self.data.Close) - self._entry_i) >= self.time_stop:
                self.position.close()
                self._entry_i = -1
                return
            return  # SL manages disaster bars

        if np.isfinite(v) and np.isfinite(s) and s > 0 and c < v - self.k_band * s:
            stop = c - self.atr_stop * float(self.atr[-1])
            if stop >= c:
                return
            stop_dist_pct = (c - stop) / c
            frac = min(self.risk_pct / stop_dist_pct, 0.98)
            if frac <= 0:
                return
            self.buy(size=frac, sl=stop)
            self._entry_i = len(self.data.Close)
