#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Write synthetic order-intervention result files so that aggregate_orders.py can
be exercised end to end without any model weights.

Two regimes are planted so the aggregator's order-invariance report can be seen
to behave correctly:

  corpus MockInvariant : the causal/noncausal separation is the SAME for every
                         order  -> spread of r should be small
  corpus MockOrderDep  : the separation shrinks as the order moves away from
                         left-to-right -> spread of r should be large

This file generates data, it does not test the science.  Its only purpose is to
confirm that the aggregation and statistics layer runs and reports sensibly.

    python3 make_mock_results.py --out mock_results
    python3 aggregate_orders.py --glob 'mock_results/*.json'
"""

import argparse
import json
import os

import numpy as np

ORDERS = ["l2r", "r2l", "random:1", "random:2", "confidence"]
# effect size injected per order, in units of the noise scale
INVARIANT = {o: 0.9 for o in ORDERS}
ORDER_DEP = {"l2r": 0.9, "confidence": 0.7, "random:1": 0.25,
             "random:2": 0.2, "r2l": 0.0}


def make(corpus, shift_by_order, order, n=100, seed=0):
    rng = np.random.default_rng(seed)
    shift = shift_by_order[order]
    recs = []
    for cat in ("causal", "noncausal"):
        mu = 0.12 if cat == "causal" else 0.12 - 0.10 * shift
        for i in range(n):
            sb = rng.normal(mu, 0.10)
            st = rng.normal(3.0, 0.5)          # token level: no planted effect
            T = int(rng.integers(28, 42))
            recs.append({
                "T": T, "n_blocks": 4, "order_spec": order,
                "order_follows_text": False, "order": list(range(T)),
                "ll_fwd": 0.0, "ll_token_rev": 0.0, "ll_block_rev": 0.0,
                "sigma_token": st * T, "sigma_block": sb * T,
                "sigma_token_per_T": st, "sigma_block_per_T": sb,
                "category": cat, "index": i, "text": f"{cat} mock {i}",
            })
    return {"meta": {"model": "/mock/MockModel-8B", "mask_token_id": 126336,
                     "texts": f"mock/{corpus}.json", "corpus": corpus,
                     "order": order, "order_follows_text": False,
                     "dtype": "bfloat16", "n_records": len(recs),
                     "elapsed_sec": 0.0},
            "records": recs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="mock_results")
    ap.add_argument("--n", type=int, default=100)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    k = 0
    for corpus, table in (("MockInvariant", INVARIANT), ("MockOrderDep", ORDER_DEP)):
        for order in ORDERS:
            d = make(corpus, table, order, n=args.n, seed=k)
            k += 1
            p = os.path.join(args.out, f"{corpus}__{order.replace(':', '-')}.json")
            with open(p, "w") as f:
                json.dump(d, f)
            print(f"# wrote {p}")


if __name__ == "__main__":
    main()
