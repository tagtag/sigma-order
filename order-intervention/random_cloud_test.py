#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the structured unmasking orders against the cloud of random ones.

The question
------------
The first run found the block-level effect size varying with the order in 2 of
5 corpora.  Two readings were left open: the order matters structurally, or any
particular permutation adds idiosyncratic variation that two random draws were
too few to measure.  All-pairs testing cannot settle it -- with twelve orders
that is 66 comparisons per corpus and no power after correction.

The design instead uses the random seeds as an EMPIRICAL NULL.  Each random
permutation is one draw of "an arbitrary order", so the spread of r among them
is permutation idiosyncrasy, measured rather than assumed.  The structured
orders, left-to-right and right-to-left, are then asked whether they sit inside
that cloud.

  inside  -> the variation is idiosyncrasy; the effect size is order invariant
             in any meaningful sense
  outside -> the structured orders really do carry different information

Two readings are reported for each structured order:

  * a z-score against the random cloud's mean and standard deviation, and the
    rank of its r within the cloud, with a two-sided permutation-style p-value
    (how extreme its rank is).  The rank p-value is the honest one: with ten
    seeds the finest two-sided p is 2/11, so a single corpus cannot reach 0.05
    on rank alone -- agreement across corpora is what carries weight.
  * a paired bootstrap CI for (structured r) - (mean of random r), which uses
    the per-text pairing and is not limited by the number of seeds.

Also reported: the spread among random seeds alone, which is the number the
earlier crude threshold of 0.17 was guessing at.

    python3 random_cloud_test.py --dir results_seeds
"""

import argparse
import glob
import json
import os
import re
from collections import defaultdict

import numpy as np
from scipy.stats import mannwhitneyu

COL = "sigma_block_per_T"
STRUCTURED = ("l2r", "r2l")


def rank_biserial(c, n):
    U = mannwhitneyu(c, n, alternative="two-sided", method="asymptotic").statistic
    return 2.0 * U / (len(c) * len(n)) - 1.0


def load(dirpath):
    data = defaultdict(dict)
    for f in sorted(glob.glob(os.path.join(dirpath, "*.json"))):
        if os.path.basename(f).startswith(("order_intervention_summary",
                                           "random_cloud", "bootstrap_order")):
            continue
        d = json.load(open(f))
        meta = d.get("meta", {})
        if meta.get("order_follows_text"):
            continue
        corpus = meta["corpus"].replace("fixed_text_", "").replace(".json", "")
        data[corpus][meta["order"]] = {
            (r["category"], r["index"]): r[COL] for r in d["records"]}
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--B", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="random_cloud_test.json")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    data = load(args.dir)
    if not data:
        raise SystemExit(f"no usable result files in {args.dir}")

    out = {"B": args.B, "seed": args.seed, "column": COL, "corpora": {}}

    for corpus in sorted(data):
        orders = sorted(data[corpus])
        rnd = sorted([o for o in orders if o.startswith("random:")],
                     key=lambda s: int(re.sub(r"\D", "", s)))
        struct = [o for o in STRUCTURED if o in orders]
        if len(rnd) < 3:
            print(f"# {corpus}: only {len(rnd)} random orders, skipping "
                  f"(the cloud needs at least 3)")
            continue

        keys = set.intersection(*(set(data[corpus][o]) for o in orders))
        keys = sorted(keys)
        M = {o: np.array([data[corpus][o][k] for k in keys]) for o in orders}
        pc = np.array([i for i, k in enumerate(keys) if k[0] == "causal"])
        pn = np.array([i for i, k in enumerate(keys) if k[0] == "noncausal"])

        r_obs = {o: rank_biserial(M[o][pc], M[o][pn]) for o in orders}
        cloud = np.array([r_obs[o] for o in rnd])

        boot = {o: np.empty(args.B) for o in orders}
        for b in range(args.B):
            bc = rng.choice(pc, size=len(pc), replace=True)
            bn = rng.choice(pn, size=len(pn), replace=True)
            for o in orders:
                boot[o][b] = rank_biserial(M[o][bc], M[o][bn])
        cloud_boot = np.mean([boot[o] for o in rnd], axis=0)

        res = {"n_random": len(rnd), "random_orders": rnd,
               "random_r": cloud.tolist(),
               "cloud_mean": float(cloud.mean()),
               "cloud_sd": float(cloud.std(ddof=1)),
               "cloud_spread": float(cloud.max() - cloud.min()),
               "structured": {}}

        for o in struct:
            r = r_obs[o]
            z = (r - cloud.mean()) / cloud.std(ddof=1)
            # rank of r among the cloud plus itself
            allv = np.append(cloud, r)
            rank = int((allv <= r).sum())
            k = len(allv)
            p_rank = min(1.0, 2.0 * min(rank, k - rank + 1) / k)
            d = boot[o] - cloud_boot
            lo, hi = np.percentile(d, [2.5, 97.5])
            res["structured"][o] = {
                "r": float(r), "z_vs_cloud": float(z),
                "rank_in_cloud": rank, "cloud_size_with_self": k,
                "p_rank": float(p_rank),
                "diff_vs_cloud_mean": float(r - cloud.mean()),
                "ci95": [float(lo), float(hi)],
                "outside_cloud_range": bool(r < cloud.min() or r > cloud.max()),
                "ci_excludes_zero": bool(lo > 0 or hi < 0),
            }
        out["corpora"][corpus] = res

    # ---------------- report ----------------
    print("=" * 100)
    print("The random cloud: effect size across random unmasking orders")
    print("=" * 100)
    print(f"{'corpus':<12}{'n':>4}{'mean r':>9}{'sd':>8}{'spread':>9}"
          f"{'min':>8}{'max':>8}")
    for c, v in out["corpora"].items():
        print(f"{c:<12}{v['n_random']:>4}{v['cloud_mean']:>9.4f}"
              f"{v['cloud_sd']:>8.4f}{v['cloud_spread']:>9.4f}"
              f"{min(v['random_r']):>8.4f}{max(v['random_r']):>8.4f}")

    print()
    print("=" * 100)
    print("Structured orders against that cloud")
    print("  'outside' = r beyond the cloud's observed range")
    print("  CI is the paired bootstrap of (structured r) - (cloud mean r)")
    print("=" * 100)
    print(f"{'corpus':<12}{'order':<6}{'r':>9}{'z':>8}{'rank':>7}{'p_rank':>9}"
          f"{'diff':>9}{'CI low':>9}{'CI high':>9}{'outside':>9}{'CI>0':>7}")
    for c, v in out["corpora"].items():
        for o, s in v["structured"].items():
            print(f"{c:<12}{o:<6}{s['r']:>9.4f}{s['z_vs_cloud']:>8.2f}"
                  f"{str(s['rank_in_cloud'])+'/'+str(s['cloud_size_with_self']):>7}"
                  f"{s['p_rank']:>9.4f}{s['diff_vs_cloud_mean']:>9.4f}"
                  f"{s['ci95'][0]:>9.4f}{s['ci95'][1]:>9.4f}"
                  f"{str(s['outside_cloud_range']):>9}"
                  f"{str(s['ci_excludes_zero']):>7}")

    print()
    print("=" * 100)
    print("Reading")
    print("=" * 100)
    for c, v in out["corpora"].items():
        any_out = any(s["outside_cloud_range"] for s in v["structured"].values())
        any_ci = any(s["ci_excludes_zero"] for s in v["structured"].values())
        if any_out or any_ci:
            verdict = ("a structured order sits apart from the cloud: "
                       "the order carries information")
        else:
            verdict = ("both structured orders sit inside the cloud: "
                       "the variation is permutation idiosyncrasy")
        print(f"  {c:<12} {verdict}")
    print("\n  With ten seeds the finest two-sided rank p is 2/11 = 0.18, so no")
    print("  single corpus settles this on rank alone; the bootstrap CI and")
    print("  agreement across corpora are what carry the weight.")

    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
    print(f"\n# wrote {args.out}")


if __name__ == "__main__":
    main()
