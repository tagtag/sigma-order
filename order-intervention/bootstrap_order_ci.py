#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paired bootstrap test for order dependence of the block-level effect size.

Why this replaces the synthetic "null band"
-------------------------------------------
An earlier calibration on synthetic data gave a spread of 0.17 in the
rank-biserial correlation with no order dependence planted, and that number
was used as a rough threshold.  It is the wrong reference for two reasons:

  1. It came from data with a different effect size and noise structure.
  2. It treated the orders as independent samples.  They are not: every order
     scores THE SAME 200 texts, so the per-text values are paired and highly
     correlated across orders.  Independent resampling overstates the noise.

The orders are also not replicates of one quantity -- each fixed unmasking
order defines its own joint distribution and therefore its own entropy
production -- so there is no "true r" whose sampling spread could be
simulated.  The well-posed question is narrower and is the one tested here:

    Is the difference in effect size between two orders larger than the
    uncertainty in estimating those effect sizes from 200 texts?

Method
------
For each corpus, texts are aligned across orders by (category, index).  Text
indices are resampled with replacement, stratified within category, and the
SAME resampled indices are used for every order, which preserves the pairing.
For each pair of orders the bootstrap distribution of r_A - r_B gives a
percentile confidence interval and a two-sided bootstrap p-value.  Holm
correction is applied across the pairs within each corpus; the total number of
comparisons is reported so the reader can judge the multiplicity.

A CI excluding zero means those two orders genuinely differ in effect size.
If no pair differs, the effect size is order invariant for that corpus.

    python3 bootstrap_order_ci.py --dir res --out bootstrap_order_ci.json
"""

import argparse
import glob
import json
import os
from collections import defaultdict

import numpy as np
from scipy.stats import mannwhitneyu

COL = "sigma_block_per_T"


def rank_biserial(c, n):
    """r = 2U/(n1 n2) - 1 = 2 P(causal > noncausal) - 1."""
    U = mannwhitneyu(c, n, alternative="two-sided", method="asymptotic").statistic
    return 2.0 * U / (len(c) * len(n)) - 1.0


def load(dirpath):
    """corpus -> order -> {(category, index): value}, excluding the ft arm."""
    data = defaultdict(dict)
    for f in sorted(glob.glob(os.path.join(dirpath, "*.json"))):
        if os.path.basename(f).startswith("order_intervention_summary"):
            continue
        d = json.load(open(f))
        meta = d.get("meta", {})
        if meta.get("order_follows_text"):
            continue
        corpus = meta["corpus"].replace("fixed_text_", "").replace(".json", "")
        vals = {(r["category"], r["index"]): r[COL] for r in d["records"]}
        data[corpus][meta["order"]] = vals
    return data


def holm(pvals):
    """Holm-Bonferroni adjusted p-values, order preserved."""
    m = len(pvals)
    idx = np.argsort(pvals)
    adj = np.empty(m)
    run = 0.0
    for k, i in enumerate(idx):
        run = max(run, (m - k) * pvals[i])
        adj[i] = min(run, 1.0)
    return adj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="directory of result JSONs")
    ap.add_argument("--B", type=int, default=10000, help="bootstrap resamples")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="bootstrap_order_ci.json")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    data = load(args.dir)
    if not data:
        raise SystemExit(f"no usable result files in {args.dir}")

    out = {"B": args.B, "seed": args.seed, "column": COL, "corpora": {}}
    all_pairs = 0

    for corpus in sorted(data):
        orders = sorted(data[corpus])
        # align texts across orders
        keys = set(data[corpus][orders[0]])
        for o in orders[1:]:
            keys &= set(data[corpus][o])
        keys = sorted(keys)
        cidx = [k for k in keys if k[0] == "causal"]
        nidx = [k for k in keys if k[0] == "noncausal"]
        M = {o: np.array([data[corpus][o][k] for k in keys]) for o in orders}
        pos_c = np.array([keys.index(k) for k in cidx])
        pos_n = np.array([keys.index(k) for k in nidx])

        r_obs = {o: rank_biserial(M[o][pos_c], M[o][pos_n]) for o in orders}

        # paired bootstrap: one resample of text indices, reused for every order
        boot = {o: np.empty(args.B) for o in orders}
        for b in range(args.B):
            bc = rng.choice(pos_c, size=len(pos_c), replace=True)
            bn = rng.choice(pos_n, size=len(pos_n), replace=True)
            for o in orders:
                boot[o][b] = rank_biserial(M[o][bc], M[o][bn])

        per_order = {}
        for o in orders:
            lo, hi = np.percentile(boot[o], [2.5, 97.5])
            per_order[o] = {"r": float(r_obs[o]), "ci95": [float(lo), float(hi)],
                            "se": float(boot[o].std(ddof=1))}

        pairs, pv = [], []
        for i in range(len(orders)):
            for j in range(i + 1, len(orders)):
                a, b_ = orders[i], orders[j]
                d = boot[a] - boot[b_]
                lo, hi = np.percentile(d, [2.5, 97.5])
                # two-sided bootstrap p: how far the distribution sits from 0
                frac = min((d <= 0).mean(), (d >= 0).mean())
                p = min(1.0, 2.0 * frac)
                pairs.append({"a": a, "b": b_,
                              "diff": float(r_obs[a] - r_obs[b_]),
                              "ci95": [float(lo), float(hi)],
                              "p_boot": float(p)})
                pv.append(p)
        adj = holm(np.array(pv))
        for k, pr in enumerate(pairs):
            pr["p_holm"] = float(adj[k])
            pr["excludes_zero"] = bool(pr["ci95"][0] > 0 or pr["ci95"][1] < 0)
        all_pairs += len(pairs)

        rs = np.array([r_obs[o] for o in orders])
        out["corpora"][corpus] = {
            "n_causal": len(pos_c), "n_noncausal": len(pos_n),
            "orders": orders, "per_order": per_order, "pairs": pairs,
            "observed_spread": float(rs.max() - rs.min()),
            "any_pair_differs": any(p["excludes_zero"] for p in pairs),
            "any_pair_differs_holm": any(p["p_holm"] < 0.05 for p in pairs),
        }

    out["total_pairwise_comparisons"] = all_pairs

    # ---------------- report ----------------
    print("=" * 96)
    print(f"Per-order effect size with paired bootstrap 95% CI  (B={args.B})")
    print("=" * 96)
    print(f"{'corpus':<12}{'order':<12}{'r':>9}{'CI low':>10}{'CI high':>10}{'SE':>9}")
    for corpus, c in out["corpora"].items():
        for o in c["orders"]:
            p = c["per_order"][o]
            print(f"{corpus:<12}{o:<12}{p['r']:>9.4f}"
                  f"{p['ci95'][0]:>10.4f}{p['ci95'][1]:>10.4f}{p['se']:>9.4f}")

    print()
    print("=" * 96)
    print("Pairwise differences between orders (paired bootstrap)")
    print("  CI excluding zero => those two orders really differ")
    print("=" * 96)
    print(f"{'corpus':<12}{'pair':<24}{'diff':>9}{'CI low':>10}{'CI high':>10}"
          f"{'p_boot':>10}{'p_holm':>9}{'':>4}")
    for corpus, c in out["corpora"].items():
        for pr in c["pairs"]:
            mark = "  *" if pr["excludes_zero"] else ""
            print(f"{corpus:<12}{pr['a']+' vs '+pr['b']:<24}{pr['diff']:>9.4f}"
                  f"{pr['ci95'][0]:>10.4f}{pr['ci95'][1]:>10.4f}"
                  f"{pr['p_boot']:>10.4f}{pr['p_holm']:>9.4f}{mark}")

    print()
    print("=" * 96)
    print("Verdict per corpus")
    print("=" * 96)
    print(f"{'corpus':<12}{'spread':>9}{'any pair differs':>19}{'after Holm':>13}")
    for corpus, c in out["corpora"].items():
        print(f"{corpus:<12}{c['observed_spread']:>9.4f}"
              f"{str(c['any_pair_differs']):>19}"
              f"{str(c['any_pair_differs_holm']):>13}")
    print(f"\n# {all_pairs} pairwise comparisons in total; Holm is applied "
          f"within each corpus, not across all of them.")

    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
    print(f"# wrote {args.out}")


if __name__ == "__main__":
    main()
