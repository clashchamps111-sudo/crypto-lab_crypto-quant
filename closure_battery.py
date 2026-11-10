"""SESSION 10 - CLOSURE MATRIX (one execution, four lenses; pre-registered).

Strategies (dead families): H01(H01 vwap flavor), H02b, H03, H04, H05.
Timeframes: 15m (new fetch), 1h (canonical), 4h (canonical), weekly (new
resampler). Cells EXCLUDED per pre-registration: H05 weekly (VWAP is
intraday-anchored), H02b weekly (not registered). Native cells re-run once
under the uniform lens for the regime-split layer; adjacent cells are NEW.

Conventions (all pre-registered):
- Frozen param transfer, no re-optimization: H01 audit set (n_fast=13,
  rsi_lo=35, atr_stop=2.5, atr_tgt=3.0, time_stop=24h); H02b mirror set
  (n_fast=9, rsi 35..60, atr_stop=2.5, use_vwap, time_stop=24h);
  H03 audit-flipped (n_enter=20, n_exit=10, atr_stop=3.0, time_stop=50h);
  H04 class defaults (RSI(2)<=10, ema_exit 9, atr 2.0, time 48h);
  H05 S5 frozen winner (k_band=1.0, atr_stop=1.5, time_stop=8h).
- Time-based params transfer in HOURS -> bars; lookbacks stay in bars.
- Weekly substitutions: regime EMA200 -> EMA40; VWAP dropped (H01/H02b);
  time_stop weekly = 3 bars (declared rounding floor).
- VWAP arrays: daily-anchored, bar-local (indicators.vwap_daily for
  TrendPullback/ShortTrendPullback; vwap_band_arrays for H05 with
  min_bars=3 on 15m/1h and min_bars=1 on 4h).
- Judge window: months [48,60) with warmup LEAD per TF (15m/1h: 60d,
  4h: 90d, weekly: 430d); trades counted ONLY if entered in-window
  (standing accounting). Costs 7bp/side. 3bp/day haircut on held notional.
- REGIME SPLIT (mandatory lens): calendar months classified by BTC's own
  trailing-30d return at month end: >= +10% bull, <= -10% bear, else
  sideways. Trades bucketed by entry month.
- Lenses: SOP (native+adjacent closure language), LADDER (stop at first
  dead TF), SWEEP (full matrix) - read off ONE executed matrix; plus the
  regime-split layer. No cell re-runs. Any positive bucket flags a
  bar/regime-locked candidate for possible NEW-line registration.
- BTC primary only (ETH cross-checks scoped out, declared).
"""
import os

import numpy as np
import pandas as pd

from backtesting import Backtest

import audit as A
import config as C
from indicators import vwap_band_arrays, vwap_daily
from strategies import (DonchianBreakout, Rsi2Reversion, ShortTrendPullback,
                        TrendPullback, VwapBandReversion)

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
COMM = 0.0007
HAIRCUT = 0.0003
JUDGE_START = pd.Timestamp("2025-11-05")   # absolute anchor (S6 precedent)

TFS = {
    "15m": dict(iv="15m", hours=0.25, lead=60),
    "1h": dict(iv="1h", hours=1.0, lead=60),
    "4h": dict(iv="4h", hours=4.0, lead=90),
    "weekly": dict(iv="1h", hours=168, lead=430),
}
FROZEN = dict(
    H01=dict(cls=TrendPullback, params=dict(n_fast=13, n_slow=21, rsi_lo=35,
                                            rsi_hi=65, atr_stop=2.5,
                                            atr_tgt=3.0), time_h=24, vwap=True),
    H02b=dict(cls=ShortTrendPullback, params=dict(n_fast=9, rsi_lo=35,
                                                  rsi_hi=60, atr_stop=2.5,
                                                  atr_tgt=3.0), time_h=24,
              vwap=True),
    H03=dict(cls=DonchianBreakout, params=dict(n_enter=20, n_exit=10,
                                               atr_stop=3.0), time_h=50,
             vwap=False),
    H04=dict(cls=Rsi2Reversion, params=dict(n_rsi=2, rsi_buy=10,
                                            n_ema_exit=9, atr_stop=2.0),
             time_h=48, vwap=False),
    H05=dict(cls=VwapBandReversion, params=dict(k_band=1.0, atr_stop=1.5),
             time_h=8, vwap=True),
)
CELLS = {
    "H01": ["15m", "1h", "4h", "weekly"],
    "H02b": ["15m", "1h", "4h"],
    "H03": ["15m", "1h", "4h", "weekly"],
    "H04": ["15m", "1h", "4h", "weekly"],
    "H05": ["15m", "1h", "4h"],
}
WEEKLY_EXCLUDE = {"H02b", "H05"}
WEEKLY_REGIME_SWAP = {"n_regime": 40}
WEEKLY_TIME_STOP = 3
WEEKLY_NO_VWAP = {"H01", "H02b"}


def window_with_lead(source, tf):
    """[judge_start - lead, judge_end) slice; trades counted only if entered
    at/after JUDGE_START (standing accounting)."""
    spec = TFS[tf]
    a = JUDGE_START - pd.Timedelta(days=spec["lead"])
    w = source[(source.index >= a) & (source.index < JUDGE_START + pd.DateOffset(months=12))]
    return w, JUDGE_START


def resample_weekly(df):
    agg = df.resample("W-SUN", label="left", closed="left").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last",
         "Volume": "sum"}).dropna()
    return agg


def haircut_and_realized(st, judge_start):
    t = st["_trades"]
    if not len(t):
        return 0.0, 0.0, 0, t
    tw = t[t["EntryTime"] >= judge_start]
    if len(tw):
        days = (tw["ExitBar"] - tw["EntryBar"]).astype(float)
        notional = tw["Size"].abs() * tw["EntryPrice"]
        tw = tw.copy()
        tw["net"] = tw["PnL"] - (days * notional) * HAIRCUT
        realized = float(tw["net"].sum())
        drag = float(((days * notional) * HAIRCUT).sum())
    else:
        realized, drag = 0.0, 0.0
    return realized, drag, int(len(tw)), tw


def regime_buckets():
    d = A.daily_df("BTCUSDT")
    ret30 = d["Close"].pct_change(30)
    month_end = d.groupby(pd.Grouper(freq="ME"))["Close"].last().dropna()
    labels = {}
    for m, _px in month_end.items():
        r = float(ret30.asof(m))
        labels[pd.Timestamp(m).to_period("M")] = ("bull" if r >= 0.10 else
                                                  "bear" if r <= -0.10 else
                                                  "sideways")
    return labels


def run_cell(strategy_id, tf, source, regime_map):
    p = dict(FROZEN[strategy_id]["params"])
    cls = FROZEN[strategy_id]["cls"]
    weekly = tf == "weekly"
    if weekly:
        p.update(WEEKLY_REGIME_SWAP)
        p["time_stop"] = WEEKLY_TIME_STOP
        vwap_mode = False
    else:
        p["time_stop"] = max(1, int(round(FROZEN[strategy_id]["time_h"] /
                                          TFS[tf]["hours"])))
        vwap_mode = FROZEN[strategy_id]["vwap"]

    w, judge_start = window_with_lead(source, tf)
    if cls is VwapBandReversion:
        min_bars = 1 if tf == "4h" else 3
        v, s = vwap_band_arrays(w, min_bars=min_bars)
        attrs = dict(p, _vwap=v, _sig=s)
        bt = Backtest(w, type("CX", (cls,), attrs), cash=C.CASH,
                      commission=COMM, exclusive_orders=True)
    else:
        if vwap_mode and tf in ("15m", "1h", "4h"):
            attrs = dict(p, use_vwap=True, _vwap=np.asarray(vwap_daily(w)))
        else:
            attrs = dict(p, use_vwap=False, _vwap=None)
        bt = Backtest(w, type("CX", (cls,), attrs), cash=C.CASH,
                      commission=COMM, exclusive_orders=True)
    st = bt.run()
    net, drag, ntr, tw = haircut_and_realized(st, judge_start)
    # regime buckets by entry month (judge entries only)
    buck = {"bull": 0.0, "bear": 0.0, "sideways": 0.0, "n": 0}
    if len(tw):
        for m, pnl in tw.groupby(tw["EntryTime"].dt.to_period("M"))["net"].sum().items():
            buck[regime_map.get(m, "sideways")] += float(pnl)
        buck["n"] = int(len(tw))
    # net-of-haircut already realized-based; gross for reporting
    r = A.row(st)
    return dict(tf=tf, ret=r["Ret%"], sharpe=r["Sharpe"], pf=r["PF"],
                trades=ntr, net=net, drag=drag, maxdd=r["MaxDD%"],
                raw_ret=r["Ret%"], buckets=buck, r=r)


def main():
    os.makedirs(OUT, exist_ok=True)
    src = {}
    for tf, spec in TFS.items():
        if tf == "weekly":
            src[tf] = resample_weekly(A.load("BTCUSDT", "1h", "_deep"))
        else:
            src[tf] = A.load("BTCUSDT", spec["iv"], "_deep")
        print(f"[cell-data] {tf}: {len(src[tf])} bars")
    regime_map = regime_buckets()
    print(f"[regime] months classified: "
          f"{pd.Series(list(regime_map.values())).value_counts().to_dict()}")

    md = ["# CLOSURE MATRIX REPORT (Session 10, pre-registered)", "",
          "One execution per cell; four lenses (SOP / ladder / sweep / regime",
          "split). Frozen param transfer. Judge = months [48,60) with per-TF",
          "warmup lead, in-window entries, 7bp/side + 3bp/day haircut.",
          "BTC primary; ETH cross-checks scoped out.", "",
          "Family verdict (SOP lens + mandatory regime rule): CONFIRMED-DEAD",
          "iff judge net <= 0 in every non-empty regime bucket of native AND",
          "adjacent cells; any positive bucket -> bar/regime-locked candidate.", ""]
    matrix = {}
    for sid in CELLS:
        rows = []
        for tf in CELLS[sid]:
            res = run_cell(sid, tf, src[tf], regime_map)
            matrix[(sid, tf)] = res
            rows.append(res)
            print(f"[{sid} {tf}] ret {res['ret']:+.2f}% sh {res['sharpe']:.2f} "
                  f"pf {res['pf']:.2f} trades {res['trades']} net {res['net']:+.2f} "
                  f"bull {res['buckets']['bull']:+.2f} sideways {res['buckets']['sideways']:+.2f} "
                  f"bear {res['buckets']['bear']:+.2f}")
        md += [f"## {sid} (frozen transfer: "
               f"{', '.join(f'{k}={v}' for k, v in FROZEN[sid]['params'].items())})",
               "", "| TF | Ret% | Sharpe | PF | Trades | Net$ | Bull | Sideways | Bear |",
               "|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            md.append(f"| {r['tf']} | {r['ret']:+.2f} | {r['sharpe']:.2f} | "
                      f"{r['pf']:.2f} | {r['trades']} | {r['net']:+.2f} | "
                      f"{r['buckets']['bull']:+.2f} | {r['buckets']['sideways']:+.2f} | "
                      f"{r['buckets']['bear']:+.2f} |")
        # ---- four lenses (read off the single executed matrix) ----
        order = ["1h"] + [tf for tf in CELLS[sid] if tf != "1h"]
        nonempty = [(tf, b, matrix[(sid, tf)]["buckets"][b])
                    for tf in CELLS[sid] for b in ("bull", "sideways", "bear")
                    if abs(matrix[(sid, tf)]["buckets"][b]) > 1e-9]
        sop_dead = all(v <= 0 for _, _, v in nonempty) if nonempty else False
        flags = [(tf, b, v) for tf, b, v in nonempty if v > 0]
        ladder = None
        for tf in order:
            if matrix[(sid, tf)]["net"] <= 0:
                ladder = tf
                break
        ladder_line = (f"ladder would have stopped at native ({ladder})"
                       if ladder == "1h" and ladder else
                       (f"ladder stops at {ladder}" if ladder else
                        "ladder: no dead cell found"))
        md += ["",
               f"- **SOP lens:** {'CONFIRMED-DEAD' if sop_dead else 'NOT closed'} "
               f"({len(nonempty)} non-empty bucket×cells checked, all net<=0: "
               f"{sop_dead})",
               f"- **Ladder lens:** {ladder_line}",
               f"- **Regime/locked flags:** "
               + ("; ".join(f"{tf}/{b} {v:+.2f}" for tf, b, v in flags)
                  if flags else "none - no positive bucket anywhere"),
               "- **Sweep lens:** the table above is the full matrix view.", ""]
        md.append("")

    path = os.path.join(OUT, "closure_matrix_report.md")
    open(path, "w", encoding="utf-8").write("\n".join(md))
    print(f"[battery] written {path}")


if __name__ == "__main__":
    main()
