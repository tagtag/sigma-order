#!/usr/bin/env python3
"""How much sigma depends on the unmasking order, for a masked diffusion model.

A masked language model's conditionals need not come from any joint, so its
pseudo-log-likelihood is not the logarithm of anything (Section 3.2 of the
paper).  A masked DIFFUSION model escapes that: fix an unmasking order pi and
the any-order chain rule

    log P_pi(x) = sum_t log p_theta( x_{pi(t)} | the positions revealed before t )

is a genuine log-probability, normalised over sequences, so

    sigma_pi = [ log P_pi(x) - log P_pi(x~) ] / L

is a genuine log-ratio rather than a score difference.  The price is pi: the
physics has no such parameter, and a real model is not consistent, so the
answer moves when pi does.

The paper states that price qualitatively.  This measures it, from runs that
were already made and are in this repository: LLaDA-8B-Base scored under 12
unmasking orders on two corpora, and under 4 orders on five corpora.

    python3 -I order_dependence.py

No model, no network: it reads the stored JSON.
"""

import collections
import glob
import json
import os
import sys

import numpy as np


def load(dirpath):
    """{(corpus, order): [records]} from one results directory."""
    out = {}
    for f in sorted(glob.glob(os.path.join(dirpath, "*.json"))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if "meta" not in d or "records" not in d:
            continue          # the aggregate summary file
        m = d["meta"]
        out[(m.get("corpus"), m.get("order"))] = d["records"]
    return out


def rank_biserial(a, b):
    """P(a > b) - P(b > a), computed from the rank sum; ties count half."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    allv = np.concatenate([a, b])
    order = np.argsort(allv, kind="mergesort")
    ranks = np.empty(len(allv), float)
    ranks[order] = np.arange(1, len(allv) + 1)
    # average ranks over ties
    i = 0
    srt = allv[order]
    while i < len(srt):
        j = i
        while j + 1 < len(srt) and srt[j + 1] == srt[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = ranks[order[i:j + 1]].mean()
        i = j + 1
    u = ranks[:len(a)].sum() - len(a) * (len(a) + 1) / 2.0
    return 2.0 * u / (len(a) * len(b)) - 1.0


def report(name, dirpath):
    recs = load(dirpath)
    if not recs:
        print(f"{name}: no records in {dirpath}")
        return {}
    by_corpus = collections.defaultdict(dict)
    for (corpus, order), rs in recs.items():
        cat = collections.defaultdict(list)
        for r in rs:
            cat[r["category"]].append(r)
        if not cat["causal"] or not cat["noncausal"]:
            raise SystemExit(f"{corpus}/{order}: records carry no usable labels")
        a = [r["sigma_block_per_T"] for r in cat["causal"]]
        b = [r["sigma_block_per_T"] for r in cat["noncausal"]]
        by_corpus[corpus][order] = {
            "r": rank_biserial(a, b),
            "median_all": float(np.median(a + b)),
        }

    print(f"\n{name}")
    print("=" * 78)
    out = {}
    for corpus in sorted(by_corpus):
        cells = by_corpus[corpus]
        rs = np.array([c["r"] for c in cells.values()], float)
        ms = np.array([c["median_all"] for c in cells.values()], float)
        rs = rs[np.isfinite(rs)]
        print(f"  {corpus}  ({len(cells)} unmasking orders)")
        print(f"    effect size r     min {rs.min():+.3f}  max {rs.max():+.3f}"
              f"  spread {rs.max() - rs.min():.3f}  sd {rs.std(ddof=1):.3f}")
        print(f"    median sigma/T    min {ms.min():.4f}  max {ms.max():.4f}"
              f"  ratio {ms.max() / ms.min():.2f}" if ms.min() > 0 else "")
        out[corpus] = {
            "n_orders": len(cells),
            "r_min": float(rs.min()), "r_max": float(rs.max()),
            "r_spread": float(rs.max() - rs.min()),
            "r_sd": float(rs.std(ddof=1)),
            "orders": {o: c["r"] for o, c in sorted(cells.items())},
        }
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    res = {}
    res["seeds"] = report("12 unmasking orders, 2 corpora",
                          os.path.join(here, "results_seeds_20261109"))
    res["llada"] = report("4 unmasking orders, 5 corpora",
                          os.path.join(here, "results_llada_20261109"))

    spreads = [c["r_spread"] for g in res.values() for c in g.values()]
    if spreads:
        print()
        print("=" * 78)
        print(f"  across every corpus measured, changing only the unmasking")
        print(f"  order moves the effect size by {min(spreads):.3f} to "
              f"{max(spreads):.3f}")
        res["summary"] = {"spread_min": float(min(spreads)),
                          "spread_max": float(max(spreads)),
                          "n_cells": len(spreads)}
    out = os.path.join(here, "order_dependence.json")
    json.dump(res, open(out, "w"), indent=1)
    print(f"\n# wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
