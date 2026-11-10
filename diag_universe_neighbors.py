"""Forensics for universe B3 failure: per-neighbor basket pooled nets.
INSIGHT ONLY - no verdict changes (pre-registered verdict already stamped)."""
import numpy as np

from universe_h07 import GRID9, UNIVERSE, fold_daily, fold_net

for ns in GRID9["n_sma"]:
    for nr in GRID9["n_roc"]:
        pn = 0.0
        per = []
        for sym in UNIVERSE:
            s = 0.0
            for a, _, w in fold_daily(sym):
                s += fold_net(w, a, dict(n_sma=ns, n_roc=nr))["net"]
            per.append(f"{s:+.1f}")
            pn += s
        mark = " <- frozen" if (ns == 100 and nr == 30) else ""
        print(f"n_sma={ns:3d} n_roc={nr:2d}  basket {pn:+6.2f}  {'PASS' if pn > 0 else 'fail'}{mark}")
        print("   " + " ".join(per))
