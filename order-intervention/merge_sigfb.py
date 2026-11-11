#!/usr/bin/env python3
"""Merge block_sigma_fb.py output and lay the evaluators side by side.

For each text, every block arrangement p was scored with

    f(p) = [ log P_l2r(x_p) - log P_r2l(x_p) ] / L

and the WRITTEN arrangement's position among those n! values recorded.  The
column that decides the claim is `pct causal` against `pct noncausal`:

    0.50   the written order sits where an arbitrary arrangement would.  Under
           the hypothesis that it is just one arrangement among n!, its rank is
           uniform, so 0.50 is the null -- by exchangeability, not by any
           symmetry of f.
    != 0.50  the incompatibility this model shows on the text depends on how
           the text is arranged.

    r > 0   the written order ranks HIGHER for causal texts
    r < 0   it ranks LOWER for causal texts
    r ~ 0   arrangement affects both sets alike, so the reading carries no
            information about causal order

A rank exists at all only because the model is incompatible: f(p) = 0 for
every p when the conditionals come from a joint.  `degen` counts the texts
where the n! values did coincide; those are reported at the null and excluded
from the effect size, since they carry no ordering.

The decomposition uses the same rule as the autoregressive table, so the two
halves of the paper can be read against each other:

    authored = median(non-causal) - 0.50
    causal   = median(causal) - median(non-causal)
    share    = causal / (authored + causal)

    python3 -I merge_sigfb.py --dir results_sigfb
"""

import argparse
import collections
import glob
import json
import os
import sys

import numpy as np
from math import comb
from scipy.stats import mannwhitneyu, wilcoxon


def rb(a, b):
    """Rank-biserial correlation and its two-sided p-value."""
    if len(a) < 2 or len(b) < 2:
        return float("nan"), float("nan")
    st = mannwhitneyu(a, b, alternative="two-sided", method="asymptotic")
    return 2.0 * st.statistic / (len(a) * len(b)) - 1.0, float(st.pvalue)


def disp_p(vals):
    """Two-sided signed-rank p for `vals` against the 0.50 null.

    The effect size r compares the two sets with each other and is silent on
    whether either is displaced at all: both could sit at 0.50 and still
    differ, or both be far from it and not.  With the displacement here only
    about one grid step wide, this is the test that decides how much the
    sigma reading can carry.
    """
    v = np.asarray(vals, float) - 0.5
    if (v != 0).sum() < 6:
        return float("nan")
    try:
        return float(wilcoxon(v, alternative="two-sided").pvalue)
    except ValueError:
        return float("nan")


def fmt_p(p):
    return "--" if not np.isfinite(p) else f"{p:.2g}"


def load(dirpath):
    """{(model, corpus): [records]}, merging shards of the same cell."""
    cells = collections.defaultdict(list)
    meta = {}
    for f in sorted(glob.glob(os.path.join(dirpath, "*.json"))):
        try:
            d = json.load(open(f))
        except Exception as e:
            print(f"# unreadable, skipped: {os.path.basename(f)} ({e})")
            continue
        m = d.get("meta") or {}
        if m.get("script") != "block_sigma_fb.py" or "records" not in d:
            continue
        key = (m.get("model", "?"), m.get("corpus", "?"))
        cells[key] += d["records"]
        meta[key] = m
    return cells, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    dirpath = args.dir or os.path.join(here, "results_sigfb")
    if not os.path.isdir(dirpath):
        alt = os.path.join(here, os.path.basename(dirpath))
        dirpath = alt if os.path.isdir(alt) else dirpath

    cells, meta = load(dirpath)
    if not cells:
        raise SystemExit(f"no block_sigma_fb.py output in {dirpath}")

    print(f"# {dirpath}")
    print("f(p) = [ log P_l2r(x_p) - log P_r2l(x_p) ] / L ; "
          "position of the written arrangement")
    print("null = 0.50 by exchangeability")
    print("=" * 122)
    print(f"{'evaluator':<22}{'corpus':<12}{'n':>5}{'degen':>7}"
          f"{'pct causal':>12}{'p vs .5 (C)':>13}{'pct noncaus':>13}"
          f"{'p vs .5 (N)':>13}{'r':>9}{'p':>10}{'sigma_fb':>11}")
    print("-" * 122)

    out = {"dir": dirpath, "cells": {}, "by_model": {}}
    per_model = collections.defaultdict(lambda: {"a": [], "c": [], "r": []})

    for (model, corpus) in sorted(cells):
        recs = cells[(model, corpus)]
        live = [r for r in recs if not r.get("degenerate")]
        degen = len(recs) - len(live)
        pc = [r["percentile_written"] for r in live if r["category"] == "causal"]
        pn = [r["percentile_written"] for r in live
              if r["category"] == "noncausal"]
        if not pc or not pn:
            print(f"{model:<22}{corpus:<12}{len(recs):>5}{degen:>7}"
                  f"{'--':>12}{'--':>13}{'--':>9}{'--':>10}{'--':>11}")
            continue
        r_rb, p_val = rb(pc, pn)
        pc0, pn0 = disp_p(pc), disp_p(pn)
        sig = float(np.median([r["sigma_fb_written"] for r in live]))
        mc, mn = float(np.median(pc)), float(np.median(pn))
        name = model.split("/")[-1]
        short = corpus.replace("fixed_text_", "")
        print(f"{name:<22}{short:<12}{len(recs):>5}{degen:>7}"
              f"{mc:>12.4f}{fmt_p(pc0):>13}{mn:>13.4f}{fmt_p(pn0):>13}"
              f"{r_rb:>+9.3f}{p_val:>10.3g}{sig:>+11.4f}")
        out["cells"][f"{name}|{short}"] = {
            "n": len(recs), "n_degenerate": degen,
            "median_pct_causal": mc, "median_pct_noncausal": mn,
            "rank_biserial": float(r_rb), "p_value": float(p_val),
            "median_sigma_fb_written": sig,
            "p_causal_vs_null": pc0, "p_noncausal_vs_null": pn0,
            "elapsed_sec": meta[(model, corpus)].get("elapsed_sec"),
        }
        per_model[name]["a"].append(mn - 0.5)
        per_model[name]["c"].append(mc - mn)
        per_model[name]["r"].append(float(r_rb))

    print("=" * 122)

    # Each corpus on its own is a weak test -- n = 200 split two ways.  What
    # the corpora can say jointly is whether the SIGN is consistent, and that
    # is an exact binomial on the number of corpora, free of any assumption
    # about the effect's size.  Reported per evaluator, because agreement
    # between evaluators is a separate question again.
    print()
    print("consistency of sign across corpora (exact binomial, two-sided)")
    print("-" * 122)
    for name in sorted(per_model):
        rs = per_model[name]["r"]
        if len(rs) < 2:
            continue
        neg = sum(1 for v in rs if v < 0)
        k, n = max(neg, len(rs) - neg), len(rs)
        p_sign = min(1.0, 2.0 * sum(comb(n, i) for i in range(k, n + 1))
                     / 2.0 ** n)
        side = "negative" if neg > n - neg else "positive"
        print(f"  {name:<22} {neg}/{n} negative, median r = "
              f"{float(np.median(rs)):+.3f}, sign test p = {p_sign:.4f} "
              f"({side})")
        out.setdefault("sign_test", {})[name] = {
            "n_corpora": n, "n_negative": neg,
            "median_r": float(np.median(rs)), "p_sign": p_sign,
        }
    print()
    print("decomposition, same rule as the autoregressive table")
    print("=" * 122)
    print(f"{'evaluator':<22}{'corpora':>9}{'authored':>12}{'causal':>11}"
          f"{'total':>10}{'share':>9}")
    print("-" * 122)
    for name in sorted(per_model):
        a_, c_ = per_model[name]["a"], per_model[name]["c"]
        auth, caus = float(np.median(a_)), float(np.median(c_))
        tot = auth + caus
        # share = causal / total is only meaningful while the total is a
        # positive distance from the null, as it is in the autoregressive
        # table (+0.354, +0.042).  Let the causal component go negative
        # enough to drag the total below zero and the ratio flips sign twice,
        # printing a large POSITIVE share for a component that subtracts.
        # Report it only when the total is positive; otherwise the two
        # components have to be read on their own.
        share = caus / tot if tot > 0 else float("nan")
        print(f"{name:<22}{len(a_):>9}{auth:>+12.4f}{caus:>+11.4f}{tot:>+10.4f}"
              + (f"{100 * share:>8.0f}%" if np.isfinite(share)
                 else f"{'n/a':>9}"))
        out["by_model"][name] = {
            "n_corpora": len(a_), "authored": auth, "causal_component": caus,
            "total": tot, "causal_share": share,
            "n_causal_component_negative": sum(1 for v in c_ if v < 0),
        }
    print("=" * 122)

    dest = args.out or os.path.join(here, "merge_sigfb.json")
    json.dump(out, open(dest, "w"), indent=1)
    print(f"\n# wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
