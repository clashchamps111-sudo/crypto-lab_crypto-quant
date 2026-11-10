"""Diagnostic: why does H01 produce 0 trades?
1. Count raw entry-signal bars with default params (indicator math check).
2. Run a single fixed-param Backtest and log every buy attempt."""
import numpy as np
import pandas as pd
import config as C
from indicators import atr_w, ema, rsi_w
from strategies import TrendPullback
from backtesting import Backtest

df = pd.read_csv("data/BTCUSDT_1h.csv", parse_dates=["Date"], index_col="Date").astype(float)
df[["Open", "High", "Low", "Close"]] = df[["Open", "High", "Low", "Close"]] / C.PRICE_SCALE
train_end = df.index[0] + pd.DateOffset(months=C.TRAIN_MONTHS)
tr = df[df.index < train_end]

f = ema(tr.Close, 9).to_numpy()
s = ema(tr.Close, 21).to_numpy()
r200 = ema(tr.Close, 200).to_numpy()
rsi = rsi_w(tr.Close, 14).to_numpy()

above_reg = tr.Close.to_numpy() > r200
trend = f > s
touch = tr.Low.to_numpy() <= f
close_above = tr.Close.to_numpy() > f
rsi_ok = (rsi >= 35) & (rsi <= 65)
warmup = np.arange(len(tr)) >= 200

cond = above_reg & trend & touch & close_above & rsi_ok & warmup
print("bars:", len(tr))
print("above regime:", int(above_reg.sum()), "| trend:", int(trend.sum()),
      "| full entry signal:", int(cond.sum()))

# --- broker integration check: one fixed run, log order attempts ---
attempts = []

class TPDebug(TrendPullback):
    def next(self):
        i0_cond = None  # reuse parent logic but record attempts
        before = len(attempts)
        was_position = bool(self.position)
        super().next()
        if len(attempts) > before:
            pass  # recorded in buy override below

    def buy(self, *args, **kwargs):
        attempts.append((len(self.data.Close), float(self.data.Close[-1]), dict(kwargs)))
        return super().buy(*args, **kwargs)

bt = Backtest(tr, TPDebug, cash=C.CASH, commission=C.COMMISSION_PER_SIDE, exclusive_orders=True)
stats = bt.run()
print("fixed-default run: trades =", int(stats["# Trades"]), "| return % =", round(float(stats["Return [%]"]), 2))
print("buy attempts:", len(attempts))
for a in attempts[:5]:
    print("  attempt:", a)
