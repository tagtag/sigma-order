#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge block_order_pll.py output and lay the evaluators side by side.

The column that decides the paper's central claim is `pct causal` against
`pct noncausal`: the median position of the WRITTEN sentence order among all
24 orders of the same text.

    0.50   the model cannot distinguish the authored order from an arbitrary
           rearrangement of the same sentences
    1.00   the authored order is the most forward-costly arrangement there is

Because the comparison is within each text, length, vocabulary, style and
topic are identical across the permutations, so the between-set confounds
that qualify every causal-vs-noncausal effect size elsewhere in this project
do not apply.

    r > 0, p < 0.05   the authored order ranks higher for causal texts than for
                      non-causal ones: sigma responds to causal order
                      specifically
    r ~ 0             it ranks equally high in both: sigma responds to the
                      text being in its authored order -- coherence, anaphora,
                      topical flow -- and the causal/non-causal effect size is
                      not evidence that entropy production measures causality

Reported for a masked and a causal evaluator of matched size, so the same
table also answers whether any of this depends on the evaluator's training
direction.

    python3 merge_blkord.py --dir results_blkord
"""

import argparse
import glob
import json
import os
from collections import defaultdict

import numpy as np
from scipy.stats import mannwhitneyu, wilcoxon

KNOWN = {"bert-base-uncased": (110, "masked"),
         "bert-large-uncased": (340, "masked"),
         "gpt2": (117, "causal"),
         "Qwen/Qwen3-4B-Base": (4000, "causal"),
         "GSAI-ML/LLaDA-8B-Base": (8000, "masked")}


def rb(a, b):
    if len(a) < 2 or len(b) < 2:
        return float("nan"), float("nan")
    st = mannwhitneyu(a, b, alternative="two-sided", method="asymptotic")
    return 2.0 * st.statistic / (len(a) * len(b)) - 1.0, float(st.pvalue)


def vs_half(x):
    """Is the median percentile different from the 0.50 null?

    0.50 is where an order-blind score lands, so this says whether the authored
    order is distinguishable from an arbitrary one at all -- a separate
    question from whether causal and non-causal differ.
    """
    d = np.asarray(x, float) - 0.5
    if (d != 0).sum() < 10:
        return float("nan")
    return float(wilcoxon(d, alternative="two-sided").pvalue)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", default="blkord_comparison.json")
    args = ap.parse_args()

    bucket = defaultdict(dict)
    kinds = {}
    for f in sorted(glob.glob(os.path.join(args.dir, "blkord_*.json"))):
        if os.path.basename(f).startswith("blkord_comparison"):
            continue
        d = json.load(open(f))
        if "records" not in d:
            continue
        corpus = d["corpus"].replace("fixed_text_", "").replace(".json", "")
        kinds[d["model"]] = d["kind"]
        for r in d["records"]:
            bucket[(d["model"], corpus)][(r["category"], r["index"])] = r
    if not bucket:
        raise SystemExit(f"no blkord_*.json with records in {args.dir}")

    out = {"dir": args.dir, "cells": {}}
    for (model, corpus), recs in sorted(bucket.items()):
        rs = list(recs.values())
        pc = np.array([r["percentile_written"] for r in rs
                       if r["category"] == "causal"], float)
        pn = np.array([r["percentile_written"] for r in rs
                       if r["category"] == "noncausal"], float)
        zc = np.array([r["z_written"] for r in rs
                       if r["category"] == "causal"
                       and np.isfinite(r.get("z_written", np.nan))], float)
        zn = np.array([r["z_written"] for r in rs
                       if r["category"] == "noncausal"
                       and np.isfinite(r.get("z_written", np.nan))], float)
        r_rb, p = rb(pc, pn)
        out["cells"][f"{model}|{corpus}"] = {
            "model": model, "kind": kinds[model], "corpus": corpus,
            "n_causal": len(pc), "n_noncausal": len(pn),
            "median_pct_causal": float(np.median(pc)) if len(pc) else None,
            "median_pct_noncausal": float(np.median(pn)) if len(pn) else None,
            "p_causal_vs_half": vs_half(pc) if len(pc) else None,
            "p_noncausal_vs_half": vs_half(pn) if len(pn) else None,
            "median_z_causal": float(np.median(zc)) if len(zc) else None,
            "median_z_noncausal": float(np.median(zn)) if len(zn) else None,
            "frac_strict_max_causal": float(np.mean(
                [r["is_strict_max"] for r in rs if r["category"] == "causal"]))
                if len(pc) else None,
            "frac_strict_max_noncausal": float(np.mean(
                [r["is_strict_max"] for r in rs if r["category"] == "noncausal"]))
                if len(pn) else None,
            "rank_biserial": float(r_rb), "p": p,
            "n_perms_median": float(np.median([r["n_perms"] for r in rs])),
            "all_exact": bool(all(r["exact_enumeration"] for r in rs)),
        }

    rows = list(out["cells"].values())
    models = sorted({c["model"] for c in rows},
                    key=lambda m: KNOWN.get(m, (0, ""))[0])
    corpora = sorted({c["corpus"] for c in rows})

    print("=" * 108)
    print("Position of the WRITTEN sentence order among all orders of the "
          "same text")
    print("  0.50 = indistinguishable from an arbitrary order;  1.00 = the "
          "most forward-costly of them all")
    print("  r compares that position between causal and non-causal texts")
    print("=" * 108)
    print(f"{'evaluator':<20}{'dir':>8}{'corpus':>10}{'n':>6}"
          f"{'pct causal':>12}{'pct noncaus':>13}{'p vs 0.5 (C)':>14}"
          f"{'r':>9}{'p':>11}")
    for m in models:
        for c in corpora:
            cell = out["cells"].get(f"{m}|{c}")
            if cell is None:
                continue
            pch = cell["p_causal_vs_half"]
            pch_s = "n/a" if pch is None or np.isnan(pch) else f"{pch:.2e}"
            print(f"{m[:19]:<20}{cell['kind']:>8}{c:>10}"
                  f"{cell['n_causal'] + cell['n_noncausal']:>6}"
                  f"{cell['median_pct_causal']:>12.4f}"
                  f"{cell['median_pct_noncausal']:>13.4f}"
                  f"{pch_s:>14}{cell['rank_biserial']:>9.4f}{cell['p']:>11.2e}")

    print()
    print("=" * 108)
    print("Reading")
    print("=" * 108)
    for m in models:
        cells = [out["cells"][f"{m}|{c}"] for c in corpora
                 if f"{m}|{c}" in out["cells"]]
        if not cells:
            continue
        rr = np.array([c["rank_biserial"] for c in cells])
        pc = np.array([c["median_pct_causal"] for c in cells])
        pn = np.array([c["median_pct_noncausal"] for c in cells])
        sep = int((np.abs(rr) > 0.2).sum())
        print(f"  {m} ({kinds[m]}), {len(cells)} corpora")
        print(f"    authored order sits at {np.median(pc):.3f} (causal) and "
              f"{np.median(pn):.3f} (non-causal) of the permutation range")
        print(f"    causal vs non-causal |r| > 0.2 in {sep}/{len(cells)} corpora"
              f"  (median r = {np.median(rr):+.3f})")
        if np.median(pc) > 0.7 and np.median(pn) > 0.7 and sep == 0:
            print("    -> the authored order is special in BOTH groups and")
            print("       equally so.  With every between-set confound removed,")
            print("       sigma responds to the text being in its written")
            print("       order, not to causal structure.")
        elif sep == len(cells) and np.median(rr) > 0:
            print("    -> the authored order is more extreme for causal texts,")
            print("       within text, with length and vocabulary fixed.")
            print("       sigma does respond to causal order specifically.")
        elif np.median(pc) < 0.6 and np.median(pn) < 0.6:
            print("    -> the authored order is barely distinguishable from an")
            print("       arbitrary one for this evaluator.")
        else:
            print("    -> mixed; report corpus by corpus.")
        print()

    # ---------------- the decomposition ----------------
    # The distance of the authored order from the 0.50 null splits into a part
    # that any authored order earns -- measured by the NON-CAUSAL texts, whose
    # order is arbitrary but still the one a writer chose -- and a part that
    # only causal order earns.  Reporting the split per evaluator is what
    # separates a property of the text from a property of the evaluator.
    print()
    print("=" * 108)
    print("Decomposition: what the distance from the 0.50 null is made of")
    print("  authored = median(non-causal) - 0.50   any authored order earns this")
    print("  causal   = median(causal) - median(non-causal)   only causal order does")
    print("=" * 108)
    print("  A strong autoregressive evaluator SATURATES: its causal median can")
    print("  sit in the top permutation bin in every corpus, and the percentile")
    print("  grid is only 1/n! wide, so the percentile split understates the")
    print("  causal part there.  The same split is therefore also reported on")
    print("  z = sigma / sd(sigma over the permutations), which has no ceiling;")
    print("  its null is z = 0, because the permutation set is symmetric about")
    print("  zero by construction (see the antisymmetry of sigma).")
    print()
    print(f"{'evaluator':<22}{'dir':>8}{'authored':>10}{'causal':>9}{'share':>7}"
          f"{'auth z':>9}{'caus z':>9}{'share z':>9}{'at ceil':>9}")
    decomp = {}
    for m in models:
        cells = [out["cells"][f"{m}|{c}"] for c in corpora
                 if f"{m}|{c}" in out["cells"]]
        if not cells:
            continue
        auth = float(np.median([c["median_pct_noncausal"] - 0.5 for c in cells]))
        caus = float(np.median([c["median_pct_causal"] - c["median_pct_noncausal"]
                                for c in cells]))
        tot = auth + caus
        share = caus / tot if tot else float("nan")
        # paired within corpus, matching make_tables.py: median over corpora of
        # the per-corpus difference, not the difference of the two medians
        pairs = [(c["median_z_noncausal"], c["median_z_causal"]) for c in cells
                 if c.get("median_z_causal") is not None
                 and c.get("median_z_noncausal") is not None]
        if pairs:
            auth_z = float(np.median([a for a, _ in pairs]))
            caus_z = float(np.median([b - a for a, b in pairs]))
            tot_z = auth_z + caus_z
            share_z = caus_z / tot_z if tot_z else float("nan")
        else:
            auth_z = caus_z = share_z = float("nan")
        # how often the causal median sits in the top permutation bin, i.e.
        # the measure has no room left above it
        # the fraction of individual CAUSAL texts whose authored order is the
        # single most forward-costly arrangement.  Once a text is there the
        # measure has no room above it, so this is what bounds the protocol --
        # not whether the corpus MEDIAN happens to land in the top bin, which
        # is a much rarer event and was what this column reported before.
        ceil = float(np.median([c["frac_strict_max_causal"] for c in cells
                                if c.get("frac_strict_max_causal") is not None]
                               or [float("nan")]))
        decomp[m] = {"authored": auth, "causal": caus, "total": tot,
                     "causal_share": share, "authored_z": auth_z,
                     "causal_z": caus_z, "causal_share_z": share_z,
                     "frac_causal_at_ceiling": ceil, "n_corpora": len(cells)}
        zs = ("      n/a      n/a" if np.isnan(auth_z)
              else f"{auth_z:>+9.3f}{caus_z:>+9.3f}")
        ss = "      n/a" if np.isnan(share_z) else f"{share_z:>9.0%}"
        print(f"{m[:21]:<22}{kinds[m]:>8}{auth:>+10.3f}{caus:>+9.3f}"
              f"{share:>7.0%}{zs}{ss}{ceil:>9.0%}")
    out["decomposition"] = decomp
    if len(decomp) >= 2:
        print()
        # Read the authored component against CAPACITY first, not against model
        # class.  An earlier version of this verdict compared the two classes
        # and concluded that the component was an artefact of autoregressive
        # factorisation; an 8B masked model reaches the same level, so the
        # component is a capability effect and the class only sets how cheaply
        # it is obtained.
        series = sorted(
            (((KNOWN.get(m, (None,))[0]), kinds[m], m, decomp[m]) for m in decomp
             if (KNOWN.get(m, (None,))[0])), key=lambda r: r[0])
        if series:
            print("  Authored component against capacity:")
            for p, kind, m, d in series:
                ps = f"{p}M" if p < 1000 else f"{p//1000}B"
                print(f"    {m.split('/')[-1][:24]:<26}{ps:>6} {kind:>8}"
                      f"  authored {d['authored']:+.3f}"
                      f"  share {d['causal_share']:>4.0%}")
            masked = [(p, d) for p, k, _, d in series if k == "masked"]
            causal = [(p, d) for p, k, _, d in series if k == "causal"]
            if len(masked) >= 2:
                rising = all(masked[i][1]["authored"] <= masked[i+1][1]["authored"] + 1e-9
                             for i in range(len(masked) - 1))
                if rising:
                    print()
                    print("  Within the masked family the authored component "
                          "rises monotonically")
                    print("  with capacity, so it is not absent from that class "
                          "-- a small model")
                    print("  simply fails to detect it.  The share attributable "
                          "to the labelled")
                    print("  contrast falls correspondingly.")
            if masked and causal:
                big_m = masked[-1][1]["authored"]
                small_c = causal[0][1]["authored"]
                if abs(big_m - small_c) < 0.1:
                    pm, pc = masked[-1][0], causal[0][0]
                    print()
                    print(f"  The largest masked evaluator ({pm//1000 if pm>=1000 else pm}"
                          f"{'B' if pm>=1000 else 'M'}) and the smallest "
                          f"autoregressive one")
                    print(f"  ({pc}M) agree on this component to "
                          f"{abs(big_m - small_c):.3f}.  An autoregressive")
                    print(f"  factorisation therefore obtains it at roughly "
                          f"{pm/pc:.0f}x less capacity,")
                    print("  because it already runs in the order under test.")

    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
    print(f"\n# wrote {args.out}")


if __name__ == "__main__":
    main()
