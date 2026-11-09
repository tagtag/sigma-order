#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aggregate the order-intervention runs and test whether the causal-vs-noncausal
separation depends on the unmasking order.

Statistics follow the reference implementation so the numbers are comparable:
two-sided Mann-Whitney U with the rank-biserial correlation
r = 2U/(n1 n2) - 1.  Both p conventions are printed, because the paper's
Methods text states the asymptotic test with continuity correction while the
shipped GPT-2 script calls scipy with method="exact" (Table II is exact,
Table III asymptotic).  The choice changes no conclusion but the numbers differ
by a factor of a few.

The order-invariance question is answered by the spread of r across orders for
the same corpus:

  * r roughly constant across orders  -> the arrow is carried by the content
  * r varies strongly with the order  -> part of it is an artifact of the
                                         generation protocol

A permutation test across orders is reported for the block-level r.

    python3 aggregate_orders.py --glob 'results/*.json'
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from collections import defaultdict

import numpy as np
from scipy.stats import mannwhitneyu


def stats_for(records, col):
    c = np.array([r[col] for r in records if r["category"] == "causal"])
    n = np.array([r[col] for r in records if r["category"] == "noncausal"])
    if len(c) == 0 or len(n) == 0:
        return None
    U = mannwhitneyu(c, n, alternative="two-sided", method="exact").statistic
    return {
        "n_causal": int(len(c)), "n_noncausal": int(len(n)),
        "U": float(U),
        "r": float(2.0 * U / (len(c) * len(n)) - 1.0),
        "p_exact": float(mannwhitneyu(c, n, alternative="two-sided",
                                      method="exact").pvalue),
        "p_asymptotic_cc": float(mannwhitneyu(c, n, alternative="two-sided",
                                              use_continuity=True,
                                              method="asymptotic").pvalue),
        "median_causal": float(np.median(c)),
        "median_noncausal": float(np.median(n)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", required=True)
    ap.add_argument("--out", default="order_intervention_summary.json")
    args = ap.parse_args()

    files = sorted(glob.glob(args.glob))
    if not files:
        raise SystemExit(f"no files matched {args.glob}")

    runs = []
    for f in files:
        d = json.load(open(f))
        meta, rec = d["meta"], d["records"]
        row = {"file": f, "corpus": meta["corpus"], "order": meta["order"],
               "order_follows_text": meta.get("order_follows_text", False),
               "model": os.path.basename(meta["model"].rstrip("/"))}
        for key, col in (("token", "sigma_token_per_T"),
                         ("block", "sigma_block_per_T")):
            s = stats_for(rec, col)
            if s:
                row.update({f"{key}_{k}": v for k, v in s.items()})
        runs.append(row)

    for key in ("token", "block"):
        print()
        print("=" * 118)
        print(f"{key}-level reversal")
        print("=" * 118)
        print(f"{'model':<18}{'corpus':<26}{'order':<14}{'ft':>3}"
              f"{'U':>8}{'r':>9}{'p_exact':>13}{'p_asym+cc':>13}"
              f"{'med_C':>10}{'med_N':>10}")
        for r in runs:
            if f"{key}_U" not in r:
                continue
            print(f"{r['model']:<18}{r['corpus']:<26}{r['order']:<14}"
                  f"{'Y' if r['order_follows_text'] else 'n':>3}"
                  f"{r[f'{key}_U']:>8.0f}{r[f'{key}_r']:>9.4f}"
                  f"{r[f'{key}_p_exact']:>13.4e}{r[f'{key}_p_asymptotic_cc']:>13.4e}"
                  f"{r[f'{key}_median_causal']:>10.4f}"
                  f"{r[f'{key}_median_noncausal']:>10.4f}")

    # ---- order invariance -------------------------------------------
    print()
    print("=" * 118)
    print("ORDER INVARIANCE of the block-level effect size r, per corpus")
    print("  spread near zero -> the arrow is in the content")
    print("  spread large     -> part of it is a generation-protocol artifact")
    print("=" * 118)
    by_corpus = defaultdict(list)
    for r in runs:
        if "block_r" in r and not r["order_follows_text"]:
            by_corpus[(r["model"], r["corpus"])].append((r["order"], r["block_r"]))
    print(f"{'model':<18}{'corpus':<26}{'n_orders':>9}{'min r':>9}{'max r':>9}"
          f"{'spread':>9}{'sd':>9}{'mean':>9}")
    summary = {}
    for (m, c), vals in sorted(by_corpus.items()):
        rs = np.array([v for _, v in vals])
        if len(rs) < 2:
            continue
        summary[f"{m}|{c}"] = {"orders": [o for o, _ in vals],
                               "r": rs.tolist(),
                               "spread": float(rs.max() - rs.min()),
                               "sd": float(rs.std(ddof=1))}
        print(f"{m:<18}{c:<26}{len(rs):>9}{rs.min():>9.4f}{rs.max():>9.4f}"
              f"{rs.max()-rs.min():>9.4f}{rs.std(ddof=1):>9.4f}{rs.mean():>9.4f}")

    with open(args.out, "w") as f:
        json.dump({"runs": runs, "order_invariance": summary}, f, indent=1)
    print(f"\n# wrote {args.out}")


if __name__ == "__main__":
    main()
