#!/usr/bin/env python3
"""The forward/backward path entropy production of a fixed text.

For a text x = x_1 ... x_L, build it in two directions under one model:

    forward   log P_l2r(x) = log P(x_1) + log P(x_2|x_1) + ... + log P(x_L|x_1..x_{L-1})
    backward  log P_r2l(x) = log P(x_L) + log P(x_{L-1}|x_L) + ... + log P(x_1|x_2..x_L)

    sigma = [ log P_l2r(x) - log P_r2l(x) ] / L

Both are genuine normalised log-probabilities of the SAME text; only the
order of assembly differs.  This is the path-wise entropy production of
stochastic thermodynamics: the forward path against the reverse path, not a
comparison with some other text.

It is identically zero for any model whose conditionals come from a joint
distribution, because both products then collapse to log P(x).  An
autoregressive model has such a joint, so for it sigma = 0 -- and it cannot
be evaluated anyway, since P(x_1 | x_2..x_L) conditions on the future, which
causal attention cannot supply.  A masked model can supply it, and its
conditionals come from no joint, so sigma is not zero; what it measures is
that incompatibility, as exposed by this text.

This script reads runs already made by order_intervention.py: each (corpus,
order) file stores ll_fwd = log P_pi(x) per text, so the l2r file and the
r2l file of the same corpus give the two terms.

    python3 -I forward_backward_sigma.py
    python3 -I forward_backward_sigma.py --dir results_seeds_20261109

No model, no network.
"""

import argparse
import glob
import json
import os
import sys

import numpy as np


def rank_biserial(a, b):
    """P(a > b) - P(b > a); ties count half."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    allv = np.concatenate([a, b])
    order = np.argsort(allv, kind="mergesort")
    ranks = np.empty(len(allv), float)
    ranks[order] = np.arange(1, len(allv) + 1)
    srt = allv[order]
    i = 0
    while i < len(srt):
        j = i
        while j + 1 < len(srt) and srt[j + 1] == srt[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = ranks[order[i:j + 1]].mean()
        i = j + 1
    u = ranks[:len(a)].sum() - len(a) * (len(a) + 1) / 2.0
    return 2.0 * u / (len(a) * len(b)) - 1.0


def load(path):
    d = json.load(open(path))
    if "meta" not in d or "records" not in d:
        return None, None
    return d["meta"], d["records"]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(here,
                                                  "results_llada_20261109"))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    # A relative --dir is tried against the working directory first and then
    # against this script's own directory, so it works whether you run it
    # from inside order-intervention/ or from the directory above.
    tried = []
    chosen = None
    for cand in (args.dir, os.path.join(here, args.dir)):
        tried.append(os.path.abspath(cand))
        if glob.glob(os.path.join(cand, "*__l2r.json")):
            chosen = cand
            break
    if chosen is None:
        print("no *__l2r.json found.  Looked in:")
        for t in dict.fromkeys(tried):
            print(f"  {t}" + ("" if os.path.isdir(t) else "   (no such directory)"))
        print("\nDirectories beside this script that hold any such file:")
        found = sorted({os.path.dirname(f) for f in
                        glob.glob(os.path.join(here, "*", "*__l2r.json"))})
        for f in found:
            print(f"  {os.path.basename(f)}")
        if not found:
            print("  (none)")
        raise SystemExit(1)
    args.dir = chosen
    corpora = sorted({os.path.basename(f).split("__")[0]
                      for f in glob.glob(os.path.join(args.dir, "*__l2r.json"))})

    print("sigma = [ log P_l2r(x) - log P_r2l(x) ] / L,  the same text both ways")
    print("null: sigma = 0 identically for any model with a joint distribution")
    print("=" * 94)
    print(f"{'corpus':<14}{'n':>5}{'median all':>12}{'causal':>11}"
          f"{'non-causal':>12}{'frac>0':>9}{'r':>9}")
    print("-" * 94)

    out = {"dir": args.dir, "corpora": {}}
    for corpus in corpora:
        mf, rf = load(os.path.join(args.dir, f"{corpus}__l2r.json"))
        mb, rb = load(os.path.join(args.dir, f"{corpus}__r2l.json"))
        if rf is None or rb is None:
            continue
        key = lambda r: (r["category"], r["index"])
        bm = {key(r): r for r in rb}
        cs, ns, allv = [], [], []
        for r in rf:
            s = bm.get(key(r))
            if s is None:
                continue
            d = (r["ll_fwd"] - s["ll_fwd"]) / r["T"]
            allv.append(d)
            (cs if r["category"] == "causal" else ns).append(d)
        if not cs or not ns:
            continue
        frac_pos = float(np.mean(np.array(allv) > 0))
        r_rb = rank_biserial(cs, ns)
        name = corpus.replace("fixed_text_", "")
        print(f"{name:<14}{len(allv):>5}{np.median(allv):>12.4f}"
              f"{np.median(cs):>11.4f}{np.median(ns):>12.4f}"
              f"{frac_pos:>9.2f}{r_rb:>+9.3f}")
        out["corpora"][name] = {
            "n": len(allv), "model": (mf or {}).get("model"),
            "median_all": float(np.median(allv)),
            "median_causal": float(np.median(cs)),
            "median_noncausal": float(np.median(ns)),
            "frac_positive": frac_pos,
            "rank_biserial": float(r_rb),
        }

    print("=" * 94)
    cells = out["corpora"]
    if cells:
        rs = [c["rank_biserial"] for c in cells.values()]
        ms = [c["median_all"] for c in cells.values()]
        print(f"  every corpus has a positive median sigma "
              f"({min(ms):.4f} to {max(ms):.4f} per token): the model assembles")
        print(f"  text more probably forwards than backwards, which for a model")
        print(f"  with a joint would be exactly 0.")
        print(f"  the causal/non-causal effect size runs {min(rs):+.3f} to "
              f"{max(rs):+.3f};")
        print(f"  {sum(1 for r in rs if r < 0)} of {len(rs)} corpora have it "
              f"NEGATIVE -- the non-causal texts are the more forward-biased.")
        out["summary"] = {"median_min": min(ms), "median_max": max(ms),
                          "r_min": min(rs), "r_max": max(rs),
                          "n_corpora": len(rs),
                          "n_negative": sum(1 for r in rs if r < 0)}

    dest = args.out or os.path.join(here, "forward_backward_sigma.json")
    json.dump(out, open(dest, "w"), indent=1)
    print(f"\n# wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
