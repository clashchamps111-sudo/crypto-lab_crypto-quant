"""Central knobs. The backtest harness reads these. Change carefully."""

PAIR = "BTCUSDT"              # Binance symbol. BTC first, then ETH (decision locked)
TIMEFRAMES = ("1h", "4h")     # both styles get tested; the survivor decides cadence
CASH = 100.0                  # pilot capital in USDT
DATA_SUFFIX = "_deep"         # file suffix: 5y Binance history; 2y originals stay archived
# Costs per side, baked into every backtest so nothing flatters us:
#   0.05% Binance USDT-M perp taker fee
#   + ~0.01% slippage allowance on liquid BTC
#   + ~0.01% funding allowance (approx, for typical 1-3 day holds)
COMMISSION_PER_SIDE = 0.0007

# ---- Risk rails (locked by the agent until the user overrides in writing) ----
RISK_PCT = 0.01               # risk 1% of equity per trade
MAX_NOTIONAL_MULT = 1.0       # sizing never exceeds this x equity (1x discipline)
# Price scaling: backtesting.py counts units as INTEGERS; raw BTC prices (~$68k)
# would floor every $100-account order to 0 units. Dividing all prices by
# PRICE_SCALE gives unit granularity of (price / 1e6) real dollars while
# returns, equity, risk and costs stay economically identical. Reverting the
# earlier BROKER_MARGIN hack - the true root cause was integer quantization.
PRICE_SCALE = 1_000_000
KILL_DD_STRATEGY = 15.0       # % drawdown from a strategy's equity peak -> permanent death
KILL_DD_ACCOUNT = 20.0        # % drawdown on total account -> stop all, full review
TESTNET_MIN_DAYS = 14         # untouched forward-test days before a cent goes live
OPT_GRID_MAX = 16             # hard cap on parameter combos per optimization pass
TRAIN_MONTHS = 48             # walk-forward train window on the 5y deep series
TEST_MONTHS = 12              # untouched final year - the judge
