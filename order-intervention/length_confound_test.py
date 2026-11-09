#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Is the causal / non-causal separation explained by text length?

The concern
-----------
The two text groups were produced by different generation prompts, so they can
differ in more than causal structure.  Checking the measured records:

  * token count T differs significantly between the groups in 4 of 5 corpora
    (Opus46 p=8.8e-17, GPT56 p=1.9e-13, Gemini31 p=9.7e-03, Fable5 p=3.1e-03;
    only GPT54 does not, p=0.45),
  * and sigma_block/T is negatively correlated with T, most strongly in
    Opus46 (-0.392), the corpus with the largest effect size.

In Opus46 the causal texts are the SHORTER ones (median 40 vs 45) and shorter
texts carry larger sigma_block/T, so some of that corpus's r = 0.708 could be
a length effect rather than a causal-structure effect.  Block count is 4 for
every text, so it is not a confound.

Two controls, neither needing a GPU
-----------------------------------
1. RESIDUALISED: regress sigma_block/T on T (ordinary least squares, pooled
   over both groups so the fit cannot absorb the group difference), then
   recompute the effect size on the residuals.  What survives is the part of
   the separation that length does not explain.

2. LENGTH-MATCHED: build the largest subsample in which the two groups have
   the same T distribution, by greedily pairing each causal text with an
   unused non-causal text of identical T, and recompute the effect size on
   those pairs only.  This makes no functional assumption about how sigma
   depends on T, at the cost of discarding unmatched texts.

Both report a paired bootstrap confidence interval, so the residualised and
matched effect sizes can be compared with the raw one on equal footing.

    python3 length_confound_test.py --dir results_llada_20261109
"""

import argparse
import glob
import json
import os
from collections import defaultdict

import numpy as np
from scipy.stats import mannwhitneyu

COL = "sigma_block_per_T"


def rb(c, n):
    if len(c) == 0 or len(n) == 0:
        return np.nan
    U = mannwhitneyu(c, n, alternative="two-sided", method="asymptotic").statistic
    return 2.0 * U / (len(c) * len(n)) - 1.0


def residualise(y, T):
    """Remove the pooled linear trend of y on T."""
    A = np.vstack([T, np.ones_like(T)]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    return y - A @ coef, float(coef[0])


def match_on_T(Tc, Tn):
    """Greedy exact-T pairing; returns index arrays into each group."""
    pool = defaultdict(list)
    for j, t in enumerate(Tn):
        pool[t].append(j)
    ic, jn = [], []
    for i, t in enumerate(Tc):
        if pool[t]:
            jn.append(pool[t].pop())
            ic.append(i)
    return np.array(ic, dtype=int), np.array(jn, dtype=int)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--order", default="l2r")
    ap.add_argument("--B", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="length_confound_test.json")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    out = {"order": args.order, "B": args.B, "corpora": {}}

    print("=" * 104)
    print(f"Length confound, order = {args.order}")
    print("  raw        : effect size as measured")
    print("  residual   : after removing the pooled linear trend of sigma on T")
    print("  matched    : on the exact-T matched subsample")
    print("=" * 104)
    print(f"{'corpus':<11}{'r_raw':>8}{'CI_raw':>17}{'r_resid':>9}{'CI_resid':>17}"
          f"{'r_match':>9}{'n_pair':>7}{'slope':>9}")

    for f in sorted(glob.glob(os.path.join(args.dir, f"*__{args.order}.json"))):
        d = json.load(open(f))
        if d["meta"].get("order_follows_text"):
            continue
        tag = (os.path.basename(f).replace("fixed_text_", "")
               .replace(f"__{args.order}.json", ""))
        rec = d["records"]
        y = np.array([r[COL] for r in rec], float)
        T = np.array([r["T"] for r in rec], float)
        isc = np.array([r["category"] == "causal" for r in rec])

        r_raw = rb(y[isc], y[~isc])
        res, slope = residualise(y, T)
        r_res = rb(res[isc], res[~isc])

        ic, jn = match_on_T(T[isc], T[~isc])
        yc, yn = y[isc], y[~isc]
        r_mat = rb(yc[ic], yn[jn]) if len(ic) >= 10 else np.nan

        # paired bootstrap over texts, within category
        pc = np.flatnonzero(isc)
        pn = np.flatnonzero(~isc)
        braw = np.empty(args.B)
        bres = np.empty(args.B)
        for b in range(args.B):
            bc = rng.choice(pc, size=len(pc), replace=True)
            bn = rng.choice(pn, size=len(pn), replace=True)
            braw[b] = rb(y[bc], y[bn])
            bres[b] = rb(res[bc], res[bn])
        ci_raw = np.percentile(braw, [2.5, 97.5])
        ci_res = np.percentile(bres, [2.5, 97.5])

        out["corpora"][tag] = {
            "r_raw": float(r_raw), "ci_raw": ci_raw.tolist(),
            "r_residual": float(r_res), "ci_residual": ci_res.tolist(),
            "r_matched": None if np.isnan(r_mat) else float(r_mat),
            "n_matched_pairs": int(len(ic)),
            "slope_sigma_on_T": slope,
            "median_T_causal": float(np.median(T[isc])),
            "median_T_noncausal": float(np.median(T[~isc])),
            "residual_ci_excludes_zero": bool(ci_res[0] > 0 or ci_res[1] < 0),
        }
        mstr = "   n/a" if np.isnan(r_mat) else f"{r_mat:>9.4f}"
        print(f"{tag:<11}{r_raw:>8.4f}"
              f"{'['+format(ci_raw[0],'.3f')+','+format(ci_raw[1],'.3f')+']':>17}"
              f"{r_res:>9.4f}"
              f"{'['+format(ci_res[0],'.3f')+','+format(ci_res[1],'.3f')+']':>17}"
              f"{mstr}{len(ic):>7}{slope:>9.5f}")

    print()
    print("=" * 104)
    print("Reading")
    print("=" * 104)
    for tag, v in out["corpora"].items():
        keep = v["r_residual"] / v["r_raw"] if v["r_raw"] else float("nan")
        mark = "survives" if v["residual_ci_excludes_zero"] else "COLLAPSES"
        print(f"  {tag:<11} residual keeps {keep*100:5.1f}% of the raw effect"
              f"   -> {mark}")

    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
    print(f"\n# wrote {args.out}")


if __name__ == "__main__":
    main()
