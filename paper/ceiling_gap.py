#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""What is in the rise of the ceiling-fraction gap?

Section 5.4 offered the fraction of texts at the extreme arrangement as
evidence that the room above an authored arrangement is closing.  Measured
on the set Eq. (8) is defined on -- the non-causal texts -- that fraction
does not rise: 20, 15, 16, 16, 15 per cent along the ladder, rho = -0.53,
exact p = 0.47.  What rises is the fraction on the CAUSAL texts, 32 to 40,
and therefore the gap between the two groups, 12 to 25 points.

That gap is a causal/non-causal contrast, not a saturation effect, and it
sits awkwardly beside two claims the paper makes from a different statistic
of the same contrast: that the causal component is at the grid floor
(Section 5.3) and that it does not vary with capacity (Section 5.4).  Both
are read off the MEDIAN midrank.  The gap is read off the TAIL.

This script reports what the gap is made of, and nothing else.  It draws no
conclusion, because the point of running it is to find out whether there is
one.  Five questions, in order:

  1. per corpus -- is the rise in every generator or in one of them?
  2. leave-one-out -- does dropping any single evaluator or corpus change
     the sign of either trend?
  3. per evaluator -- is the causal/non-causal difference significant
     within an evaluator, by an exact test on the counts?
  4. threshold sweep -- the ceiling is "midrank is the strict maximum".
     Recomputing the same contrast at midrank thresholds below the top says
     whether the effect is a property of the tail alone or of the whole
     upper range.  If it exists only exactly at the ceiling it is a
     knife-edge artefact of that definition.
  5. tail against median -- the median midrank difference (the causal
     component) beside the tail difference, on the same evaluators, so the
     two statistics can be compared directly.

    python3 -I ceiling_gap.py ../order-intervention/results_blkord
"""
import glob
import itertools
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np

CORPUS_ORDER = ["Opus46", "GPT54", "GPT56", "Gemini31", "Fable5"]
EVAL_ORDER = ["gpt2", "gpt2-medium", "gpt2-large", "gpt2-xl",
              "Qwen/Qwen3-4B-Base"]
PARAMS = {"gpt2": 124, "gpt2-medium": 355, "gpt2-large": 774,
          "gpt2-xl": 1558, "Qwen/Qwen3-4B-Base": 4000}


def load(dirpath):
    bucket, kinds = defaultdict(dict), {}
    for f in sorted(glob.glob(os.path.join(dirpath, "blkord_*.json"))):
        if os.path.basename(f).startswith("blkord_comparison"):
            continue
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if "records" not in d or "model" not in d:
            continue
        corpus = d["corpus"].replace("fixed_text_", "").replace(".json", "")
        kinds[d["model"]] = d["kind"]
        for r in d["records"]:
            bucket[(d["model"], corpus)][(r["category"], r["index"])] = r
    return bucket, kinds


def spearman(x, y):
    """rho and an EXACT two-sided p, as make_tables.spearman does."""
    from scipy.stats import rankdata
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x)
    rx = rankdata(x) - np.mean(rankdata(x))
    ry = rankdata(y) - np.mean(rankdata(y))
    den = math.sqrt(float((rx ** 2).sum()) * float((ry ** 2).sum()))
    if den == 0:
        return float("nan"), 1.0
    rho = float((rx * ry).sum() / den)
    if n > 8:
        from scipy.stats import spearmanr
        return rho, float(spearmanr(x, y).pvalue)
    perms = np.array(list(itertools.permutations(range(n))))
    rhos = (rx * ry[perms]).sum(axis=1) / den
    return rho, float(np.mean(np.abs(rhos) >= abs(rho) - 1e-12))


def frac(recs, cat, key):
    v = [r[key] for k, r in recs.items() if k[0] == cat and key in r]
    return (float(np.mean(v)), len(v)) if v else (float("nan"), 0)


def above(recs, cat, thr):
    v = [r["percentile_written"] for k, r in recs.items() if k[0] == cat]
    return (float(np.mean([q > thr for q in v])), len(v)) if v \
        else (float("nan"), 0)


def main(dirpath):
    blk, kinds = load(dirpath)
    if not blk:
        print(f"no blkord_*.json under {dirpath}")
        return 1
    models = [m for m in EVAL_ORDER if kinds.get(m) == "causal"
              and any(k[0] == m for k in blk)]
    corpora = [c for c in CORPUS_ORDER if any(k[1] == c for k in blk)]
    par = [PARAMS[m] for m in models]
    short = [m.split("/")[-1] for m in models]

    # ---------------------------------------------------------------- 1
    print("=" * 78)
    print("1) the ceiling fraction per corpus     (c = causal, "
          "nc = non-causal, %)")
    print("=" * 78)
    per = {}
    for cat, tag in (("noncausal", "nc"), ("causal", "c")):
        print(f"\n  {tag}:")
        print(" " * 20 + "".join(f"{c:>12}" for c in corpora)
              + f"{'median':>12}")
        for m, s in zip(models, short):
            row = [100 * frac(blk.get((m, c), {}), cat, "is_strict_max")[0]
                   for c in corpora]
            per[(tag, m)] = row
            print(f"  {s:<18}" + "".join(f"{v:>12.0f}" for v in row)
                  + f"{np.median(row):>12.0f}")

    print("\n  per-corpus trend of the gap (c - nc) against capacity:")
    for ci, c in enumerate(corpora):
        g = [per[("c", m)][ci] - per[("nc", m)][ci] for m in models]
        rho, p = spearman(par, g)
        print(f"  {c:<12} {str([round(v) for v in g]):<26} "
              f"rho={rho:+.2f}  p={p:.3f}  ends {g[0]:+.0f} -> {g[-1]:+.0f}")

    # ---------------------------------------------------------------- 2
    print()
    print("=" * 78)
    print("2) leave-one-out, on the medians over corpora")
    print("=" * 78)
    med = {t: [float(np.median(per[(t, m)])) for m in models]
           for t in ("nc", "c")}
    med["gap"] = [a - b for a, b in zip(med["c"], med["nc"])]
    for t, name in (("nc", "ceiling nc"), ("c", "ceiling c"),
                    ("gap", "gap")):
        rho, p = spearman(par, med[t])
        print(f"\n  {name}  full: rho={rho:+.3f} p={p:.3f}   "
              f"{[round(v) for v in med[t]]}")
        for i, s in enumerate(short):
            xs = [v for j, v in enumerate(par) if j != i]
            ys = [v for j, v in enumerate(med[t]) if j != i]
            r2, p2 = spearman(xs, ys)
            print(f"      drop {s:<16} rho={r2:+.3f} p={p2:.3f}")
    print("\n  dropping a corpus instead (medians recomputed over the rest):")
    for ci, c in enumerate(corpora):
        g = [float(np.median([per[("c", m)][k] - per[("nc", m)][k]
                              for k in range(len(corpora)) if k != ci]))
             for m in models]
        rho, p = spearman(par, g)
        print(f"      drop {c:<12} gap rho={rho:+.3f} p={p:.3f}  "
              f"{[round(v) for v in g]}")

    # ---------------------------------------------------------------- 3
    print()
    print("=" * 78)
    print("3) within an evaluator: is the ceiling difference significant?")
    print("    counts pooled over corpora, Fisher exact, two-sided")
    print("=" * 78)
    from scipy.stats import fisher_exact
    for m, s in zip(models, short):
        cc = nn = ct = nt = 0
        for c in corpora:
            recs = blk.get((m, c), {})
            f1, n1 = frac(recs, "causal", "is_strict_max")
            f0, n0 = frac(recs, "noncausal", "is_strict_max")
            if n1:
                cc += round(f1 * n1); ct += n1
            if n0:
                nn += round(f0 * n0); nt += n0
        if ct and nt:
            _, p = fisher_exact([[cc, ct - cc], [nn, nt - nn]])
            print(f"  {s:<18} causal {cc:>4}/{ct:<5} "
                  f"non-causal {nn:>4}/{nt:<5} p={p:.2e}")

    # ---------------------------------------------------------------- 4
    print()
    print("=" * 78)
    print("4) the same contrast at midrank thresholds below the ceiling")
    print("    'fraction of texts with midrank above t', c - nc, in points")
    print("=" * 78)
    thrs = [0.50, 0.60, 0.70, 0.80, 0.90, 0.95]
    print(" " * 20 + "".join(f"{('>' + format(t, '.2f')):>10}" for t in thrs)
          + f"{'strictmax':>11}")
    rows = {}
    for m, s in zip(models, short):
        row = []
        for t in thrs:
            g = float(np.median(
                [100 * (above(blk.get((m, c), {}), "causal", t)[0]
                        - above(blk.get((m, c), {}), "noncausal", t)[0])
                 for c in corpora]))
            row.append(g)
        g = float(np.median([per[("c", m)][i] - per[("nc", m)][i]
                             for i in range(len(corpora))]))
        row.append(g)
        rows[m] = row
        print(f"  {s:<18}" + "".join(f"{v:>10.1f}" for v in row))
    print("\n  trend of each column against capacity:")
    for j, label in enumerate([f">{t:.2f}" for t in thrs] + ["strictmax"]):
        col = [rows[m][j] for m in models]
        rho, p = spearman(par, col)
        print(f"      {label:<11} rho={rho:+.3f}  p={p:.3f}  "
              f"ends {col[0]:+.1f} -> {col[-1]:+.1f}")

    # ---------------------------------------------------------------- 5
    print()
    print("=" * 78)
    print("5) the tail contrast beside the median contrast")
    print("=" * 78)
    comp = []
    for m in models:
        c_ = []
        for c in corpora:
            recs = blk.get((m, c), {})
            pc = [r["percentile_written"] for k, r in recs.items()
                  if k[0] == "causal"]
            pn = [r["percentile_written"] for k, r in recs.items()
                  if k[0] == "noncausal"]
            if pc and pn:
                c_.append(float(np.median(pc)) - float(np.median(pn)))
        comp.append(float(np.median(c_)))
    k = max(r["n_perms"] for recs in blk.values() for r in recs.values()
            if "n_perms" in r)
    print(f"  grid = 1/{k} = {1.0/k:.4f};  ceiling fraction step = "
          f"1/100 = 0.01")
    print(f"\n  {'evaluator':<18}{'median diff':>14}{'in steps':>10}"
          f"{'tail diff (pts)':>18}{'in steps':>10}")
    for s, a, b in zip(short, comp, [rows[m][-1] for m in models]):
        print(f"  {s:<18}{a:>14.4f}{a*k:>10.1f}{b:>18.1f}{b:>10.1f}")
    rho, p = spearman(par, comp)
    print(f"\n  median diff vs capacity: rho={rho:+.3f} p={p:.3f}")
    rho, p = spearman(par, [rows[m][-1] for m in models])
    print(f"  tail   diff vs capacity: rho={rho:+.3f} p={p:.3f}")
    rho, p = spearman(comp, [rows[m][-1] for m in models])
    print(f"  the two against each other: rho={rho:+.3f} p={p:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1
                  else "../order-intervention/results_blkord"))
