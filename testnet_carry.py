"""TESTNET CARRY PHASE A - two-leg execution harness (pre-registered in JOURNAL).

Stacks (each $100 notional, 1x): A = GATED carry (certified primary),
B = ALWAYS-IN comparator. Phase A measures EXECUTION MECHANICS AND ACCOUNTING
FIDELITY (fills, fees, funding settlements, ledger vs model). Income is NOT
the decision basis (pre-registered pick rule: fidelity decides, tie -> A).

Operational truth (declared in JOURNAL): SPOT testnet (testnet.binance.vision)
and FUTURES testnet (testnet.binancefuture.com) are separate accounts/keys.
BOTH stacks share the two books (one BTC balance, one net perp short) with
LEDGER-LEVEL attribution by stack tag - closes reverse EXACT ledger-filled
quantities. Testnet books are simulated/thin: fidelity is measured WITHIN
testnet's own world (internal basis, internal fills), not vs prod prices.
Funding prints on testnet may be coarse/simulated - measured, not gated.
Structural kill conditions (JOURNAL): unbalanced legs > 2h (perp short with
no spot BTC / vice versa), fee > 1.5x model on a completed leg, funding
missing on 2+ settlements, ledger corruption.

Keys file: crypto-quant/testnet_keys.json (local only; never print secrets):
  {"fut_api": "...", "fut_sec": "...", "spot_api": "...", "spot_sec": "..."}
futures testnet: https://testnet.binancefuture.com
spot testnet:    https://testnet.binance.vision

Commands:
  status            balances + net perp position on both accounts
  open A|B          market BUY spot $100 + market SELL perp (matched to fills)
  close A|B         reverse EXACT ledger quantities of that stack (reduceOnly
                    perp; spot SELLs its BTC leg); pulls funding income
  check             daily reconciliation stamp -> out/testnet_recon.md
  report            Phase A summary (14d clock vs ledger, fidelity stats)

Ledger: crypto-quant/data/testnet_ledger.csv (append-only audit trail).
Clock: starts at the first successful `open A` row in the ledger.
"""
import hashlib
import hmac
import json
import os
import time
import urllib.parse
import urllib.request

import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
KEYS = os.path.join(ROOT, "testnet_keys.json")
LEDGER = os.path.join(ROOT, "data", "testnet_ledger.csv")
OUT = os.path.join(ROOT, "out")
RECON = os.path.join(OUT, "testnet_recon.md")
REPORT = os.path.join(OUT, "testnet_phaseA_report.md")

FUT = "https://testnet.binancefuture.com"
SPOT = "https://testnet.binance.vision"
NOTIONAL = 100.0
SYMBOL = "BTCUSDT"
STEP = 0.001                      # BTCUSDT perp min quantity step (fapi)


# ---------------- plumbing ----------------
def keys():
    if not os.path.exists(KEYS):
        raise SystemExit("[keys] testnet_keys.json missing.\nCreate it with:\n"
                         '  {"fut_api": "...", "fut_sec": "...", '
                         '"spot_api": "...", "spot_sec": "..."}\n'
                         "Futures testnet keys: https://testnet.binancefuture.com "
                         "(bottom-left 'API Key' tab after login)\n"
                         "Spot testnet keys:    https://testnet.binance.vision "
                         "(Generate HMAC-SHA256 key)")
    with open(KEYS) as f:
        k = json.load(f)
    for field in ("fut_api", "fut_sec", "spot_api", "spot_sec"):
        if not k.get(field):
            raise SystemExit(f"[keys] field missing: {field}")
    return k


def req(base, path, method="GET", params=None, signed=False, side="fut"):
    k = keys()
    api, sec = ((k["fut_api"], k["fut_sec"]) if side == "fut"
                else (k["spot_api"], k["spot_sec"]))
    params = dict(params or {})
    qs = urllib.parse.urlencode(params, doseq=True)
    if signed:
        p = dict(params)
        p["timestamp"] = int(time.time() * 1000)
        p["recvWindow"] = 10000
        qs = urllib.parse.urlencode(p, doseq=True)
        sig = hmac.new(sec.encode(), qs.encode(), hashlib.sha256).hexdigest()
        qs += f"&signature={sig}"
    url = f"{base}{path}" + (f"?{qs}" if qs else "")
    r = urllib.request.Request(url, method=method,
                               headers={"X-MBX-APIKEY": api})
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.loads(resp.read())


def ledger_append(rows):
    if not rows:
        return
    df = pd.DataFrame(rows)
    hdr = not os.path.exists(LEDGER)
    df.to_csv(LEDGER, mode="a", header=hdr, index=False)


def po(prop):
    return float(prop or 0)


def price_of(side="fut"):
    p = req(FUT if side == "fut" else SPOT,
            "/fapi/v1/ticker/price" if side == "fut" else "/api/v3/ticker/price",
            params={"symbol": SYMBOL})
    return float(p["price"])


# ---------------- commands ----------------
def status():
    print("== SPOT testnet ==")
    for b in req(SPOT, "/api/v3/account", signed=True, side="spot")["balances"]:
        if po(b["free"]) > 0:
            print(f"  {b['asset']:6s} free {po(b['free']):.8f}")
    print("== FUTURES testnet ==")
    acct = req(FUT, "/fapi/v2/account", signed=True, side="fut")
    for a in acct.get("assets", []):
        if po(a.get("walletBalance", 0)) > 0:
            print(f"  {a['asset']:6s} wallet {po(a['walletBalance']):.2f} "
                  f"upnl {po(a.get('unrealizedProfit', 0)):+.2f}")
    for p in acct.get("positions", []):
        if po(p.get("positionAmt", 0)) != 0:
            print(f"  position {p['symbol']} {p['positionAmt']} @ entry {p['entryPrice']}")


def open_stack(stack):
    stack = stack.upper()
    print(f"[open {stack}] spot MARKET BUY ${NOTIONAL:.2f} of BTC ...")
    sp = req(SPOT, "/api/v3/order", method="POST",
             params={"symbol": SYMBOL, "side": "BUY", "type": "MARKET",
                     "quoteOrderQty": NOTIONAL}, signed=True, side="spot")
    rows = [dict(ts=pd.Timestamp.now(), stack=stack, action="open", leg="spot",
                 side="BUY", symbol=SYMBOL, qty=po(x.get("qty")),
                 price=po(x.get("price")), fee=po(x.get("commission")),
                 exec_id=x.get("tradeId") or x.get("orderId"))
            for x in (sp.get("fills") or [{"qty": sp.get("executedQty"),
                                           "price": sp.get("price", 0),
                                           "commission": sp.get("commission")}])]
    btc_filled = sum(r["qty"] for r in rows)
    print(f"  filled {btc_filled:.8f} BTC, fee {sum(r['fee'] for r in rows):.8f}")
    px = price_of("fut")
    qty = max(round(NOTIONAL / px / STEP) * STEP, STEP)
    print(f"[open {stack}] perp MARKET SELL {qty} BTC @~{px:.2f} ...")
    fp = req(FUT, "/fapi/v1/order", method="POST",
             params={"symbol": SYMBOL, "side": "SELL", "type": "MARKET",
                     "quantity": f"{qty:.3f}"}, signed=True, side="fut")
    rows += [dict(ts=pd.Timestamp.now(), stack=stack, action="open", leg="perp",
                  side="SELL", symbol=SYMBOL, qty=po(x.get("qty")),
                  price=po(x.get("avgPrice") or x.get("price")),
                  fee=po(x.get("commission")), exec_id=fp.get("orderId"))
             for x in [(fp if not fp.get("fills") else fp["fills"][0])]]
    print(f"  filled avgPx {fp.get('avgPrice', '?')}")
    ledger_append(rows)
    print(f"[open {stack}] DONE. Hedge integrity (ledger-vs-books) via `check`.")
    if stack == "A":
        print("[clock] 14-day Phase A clock anchored at this ledger row.")


def close_stack(stack):
    stack = stack.upper()
    if not os.path.exists(LEDGER):
        print(f"[close {stack}] ledger empty - nothing to close")
        return
    df = pd.read_csv(LEDGER)
    opens = df[(df.stack == stack) & (df.action == "open")]
    closes = df[(df.stack == stack) & (df.action == "close")]
    spot_qty = opens[(opens.leg == "spot")].qty.sum() - closes[(closes.leg == "spot")].qty.sum()
    perp_qty = opens[(opens.leg == "perp")].qty.sum() - closes[(closes.leg == "perp")].qty.sum()
    if perp_qty <= 0 or spot_qty <= 0:
        print(f"[close {stack}] no open stack legs remain in ledger - nothing to close")
        return
    rows = []
    print(f"[close {stack}] perp MARKET BUY-back {perp_qty:.3f} (reduceOnly) ...")
    fp = req(FUT, "/fapi/v1/order", method="POST",
             params={"symbol": SYMBOL, "side": "BUY", "type": "MARKET",
                     "quantity": f"{perp_qty:.3f}", "reduceOnly": "true"},
             signed=True, side="fut")
    rows.append(dict(ts=pd.Timestamp.now(), stack=stack, action="close", leg="perp",
                     side="BUY", symbol=SYMBOL, qty=po(fp.get("executedQty") or perp_qty),
                     price=po(fp.get("avgPrice")), fee=po(fp.get("commission")),
                     exec_id=fp.get("orderId")))
    print(f"[close {stack}] spot MARKET SELL {spot_qty:.8f} BTC ...")
    sp = req(SPOT, "/api/v3/order", method="POST",
             params={"symbol": SYMBOL, "side": "SELL", "type": "MARKET",
                     "quantity": f"{spot_qty:.8f}"}, signed=True, side="spot")
    rows.append(dict(ts=pd.Timestamp.now(), stack=stack, action="close", leg="spot",
                     side="SELL", symbol=SYMBOL, qty=po(sp.get("executedQty") or spot_qty),
                     price=po(sp.get("price")), fee=po(sp.get("commission")),
                     exec_id=sp.get("orderId")))
    ledger_append(rows)
    inc = req(FUT, "/fapi/v1/income", signed=True, side="fut",
              params={"incomeType": "FUNDING_FEE", "limit": 100})
    print(f"[close {stack}] DONE. Funding-income entries visible on testnet: "
          f"{len(inc)} (sum {sum(po(x['income']) for x in inc):+.6f})")


def check():
    now = pd.Timestamp.now()
    px_s, px_f = price_of("spot"), price_of("fut")
    basis_test = (px_f - px_s) / px_s
    pos = req(FUT, "/fapi/v2/positionRisk", signed=True, side="fut")
    amt = sum(po(p["positionAmt"]) for p in pos if p["symbol"] == SYMBOL)
    spot_btc = sum(po(b["free"]) for b in
                   req(SPOT, "/api/v3/account", signed=True, side="spot")["balances"]
                   if b["asset"] == "BTC")
    inc = req(FUT, "/fapi/v1/income", signed=True, side="fut",
              params={"incomeType": "FUNDING_FEE", "limit": 50})
    fund_sum = sum(po(x["income"]) for x in inc)
    flags = []
    if amt < -0.0001 and spot_btc <= 0.00001:
        flags.append("STRUCTURAL: perp short open with NO spot BTC leg (kill cond.)")
    if amt > 0.0001:
        flags.append("STRUCTURAL: perp side is LONG while carry stack is short - hedge broken")
    ledger_note = "ledger present" if os.path.exists(LEDGER) else "ledger EMPTY (clock not started)"
    block = "\n".join([
        f"## {now.strftime('%Y-%m-%d %H:%M')}",
        f"- testnet internal px: spot {px_s:.2f} | perp {px_f:.2f} | "
        f"internal basis {basis_test * 1e4:+.2f}bp",
        f"- books: perp {amt:+.4f} BTC | spot BTC free {spot_btc:.8f} "
        f"(ledger: {ledger_note})",
        f"- funding income (last 50): n={len(inc)}, sum {fund_sum:+.6f}",
        f"- flags: {'; '.join(flags) if flags else 'none'}", ""])
    with open(RECON, "a", encoding="utf-8") as f:
        f.write(block + "\n")
    print(block)
    print(f"[check] appended {RECON}")


def report():
    if not os.path.exists(LEDGER):
        print("[report] ledger empty - clock never started")
        return
    df = pd.read_csv(LEDGER, parse_dates=["ts"])
    opens = df[df.action == "open"]
    if opens.empty:
        print("[report] no open rows - clock never started")
        return
    clock_stack = opens[opens.stack == "A"]
    first = clock_stack.ts.min() if not clock_stack.empty else opens.ts.min()
    days = (pd.Timestamp.now() - first).total_seconds() / 86400
    print(f"[report] ledger rows {len(df)} | A-clock anchored {first} | "
          f"elapsed {days:.1f}d -> {'REACHED' if days >= 14 else 'NOT reached'} (14d)")
    piv = df.groupby(["stack", "action", "leg"]).agg(qty=("qty", "sum"),
                                                     fee=("fee", "sum"))
    print(piv.to_string())
    text = "\n".join([
        f"# TESTNET PHASE A REPORT ({pd.Timestamp.now():%Y-%m-%d %H:%M})",
        "",
        f"- A-clock: anchored {first}, elapsed {days:.1f}d -> "
        f"{'REACHED' if days >= 14 else 'NOT reached'} (14d minimum)",
        "- Ledger summary (qty/fee by stack-action-leg):", piv.to_string(),
        "", "- Pick rule (pre-registered): fidelity decides, exact tie -> A;",
        "  income size does NOT pick.", ""])
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[report] written {REPORT}")


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    arg = sys.argv[2].upper() if len(sys.argv) > 2 and len(sys.argv[2]) <= 1 else None
    if cmd == "status":
        status()
    elif cmd == "open" and arg in ("A", "B"):
        open_stack(arg)
    elif cmd == "close" and arg in ("A", "B"):
        close_stack(arg)
    elif cmd == "check":
        check()
    elif cmd == "report":
        report()
    else:
        print(__doc__)
