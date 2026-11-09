#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Where does the WRITTEN block order sit among all block orders?

Why this replaces shuffle_control.py
------------------------------------
shuffle_control.py compared sigma_block(original) against sigma_block(shuffled)
and found the shuffled value collapses to about zero.  That comparison cannot
discriminate anything, because the collapse is forced:

    writing x_pi for the blocks concatenated in order pi, block reversal of
    x_pi is exactly x_{pi o rev}, so

        sigma(pi) = [log P(x_pi) - log P(x_{pi o rev})] / L = - sigma(pi o rev)

    identically.  The map pi -> pi o rev is a measure-preserving involution on
    the symmetric group, so the distribution of sigma over a uniformly drawn pi
    is EXACTLY symmetric about zero -- independently of the model, the text, or
    any causal content.

So "original exceeds shuffled in 96% of texts" only restates
sigma_block(original) > 0, which was already measured.  (The small NEGATIVE
shuffled medians observed, -0.011 to -0.027, are themselves the signature of
this mechanism: the script excluded the identity permutation but not its
reversal, removing the +sigma(id) member of that one pair, a bias of about
sigma(id)/(n!-1) ~ 0.018 for n=4.)

The test that is not forced
---------------------------
Ask instead where the written order ranks among ALL block orders of the same
text.  With four blocks there are 4! = 24 orders, so this is exact rather than
sampled.  For each permutation pi the measure is

    sigma(pi) = [log P(x_pi) - log P(x_{pi o rev})] / L

The set of 24 values is symmetric about zero by the identity above, which is
fine: the question is not whether the distribution is centred, it is whether
sigma(identity) sits at the TOP of it.

    rank 24/24  the written order is the single most forward-costly
                arrangement of these sentences
    rank 12/24  the written order is unremarkable among arbitrary arrangements

The discriminator
-----------------
Compare those ranks between the two groups.

    causal ranks high, non-causal ranks mid    sigma_block responds to causal
                                               order specifically
    both groups rank equally high              sigma_block responds to "being
                                               the order the text was written
                                               in" -- discourse coherence,
                                               anaphora, topical flow -- and
                                               not to causal structure

The second outcome is the one that matters for the paper's central claim: it
would mean the causal/non-causal effect size is not evidence that entropy
production measures causality.

Cost: 24 any-order log-probabilities per text instead of 2, i.e. about three
times shuffle_control.py -- roughly 18 min for Opus46 and 10 min for GPT54 on
a 4090.

    python3 block_order_test.py --model GSAI-ML/LLaDA-8B-Base \\
        --mask-token-id 126336 \\
        --texts Paper2026/gpt2/text_sets2/fixed_text_Opus46.json \\
        --order l2r --out block_order_Opus46.json
"""

import argparse
import itertools
import json
import os
import sys
import time

import numpy as np
from scipy.stats import mannwhitneyu

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aoar_core import aoar_logprob, make_order, split_into_blocks  # noqa: E402
from order_intervention import HFMaskedProvider, load_texts  # noqa: E402


def permutation_set(n, max_perms, rng):
    """Block orders to evaluate, closed under reversal and containing identity.

    Closure matters: sigma(pi) needs log P at both pi and pi o rev, so both
    must be in the set.  For n <= 4 the full symmetric group fits and the test
    is exact.
    """
    ident = tuple(range(n))
    allp = list(itertools.permutations(range(n)))
    if len(allp) <= max_perms:
        return allp, True
    chosen = {ident, tuple(reversed(ident))}
    while len(chosen) < max_perms:
        p = tuple(int(v) for v in rng.permutation(n))
        chosen.add(p)
        chosen.add(tuple(reversed(p)))
    return sorted(chosen), False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--texts", required=True)
    ap.add_argument("--order", default="l2r",
                    help="unmasking order, held fixed across block orders")
    ap.add_argument("--max-perms", type=int, default=24,
                    help="block orders per text; 24 enumerates 4! exactly")
    ap.add_argument("--mask-token-id", type=int, default=None)
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--max-batch", type=int, default=32)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    t0 = time.time()
    rng = np.random.default_rng(args.seed)
    prov = HFMaskedProvider(args.model, args.mask_token_id, args.dtype,
                            max_batch=args.max_batch)
    corpus = os.path.basename(args.texts)
    print(f"# model={args.model}  corpus={corpus}  order={args.order}  "
          f"max_perms={args.max_perms}", flush=True)

    cats = load_texts(args.texts)
    records = []
    for cat, texts in cats.items():
        if args.limit:
            texts = texts[: args.limit]
        for i, text in enumerate(texts):
            ids = prov.encode(text)
            blocks = split_into_blocks(ids, prov.decode_one)
            n = len(blocks)
            if n < 3 or len(ids) < 4:
                continue

            perms, exact = permutation_set(n, args.max_perms, rng)
            lp = {}
            for p in perms:
                sids = [t for b in p for t in blocks[b]]
                if len(sids) != len(ids):      # cannot happen, but be sure
                    lp = None
                    break
                order = make_order(args.order, len(sids), prov, sids)
                lp[p] = aoar_logprob(sids, order, prov, args.max_batch)
            if not lp:
                continue

            L = float(len(ids))
            ident = tuple(range(n))
            sig = {p: (lp[p] - lp[tuple(reversed(p))]) / L for p in perms}
            vals = np.array([sig[p] for p in perms], dtype=float)
            s_id = sig[ident]

            # MIDRANK, not a "<=" count: a score blind to block order makes
            # every sigma exactly zero, and a "<=" count would then report
            # k/k = 1.00 for a model that cannot tell the arrangements apart.
            # Splitting ties puts that case at 0.50, the true null.
            k = len(vals)
            n_below = int((vals < s_id).sum())
            n_equal = int((vals == s_id).sum())
            sd = float(vals.std(ddof=1))
            records.append({
                "category": cat, "index": i, "T": int(len(ids)), "n_blocks": n,
                "exact_enumeration": bool(exact),
                "sigma_written": float(s_id),
                "sigma_max": float(vals.max()),
                "sigma_sd": sd,
                "n_below": n_below, "n_equal": n_equal, "n_perms": k,
                "percentile_written": (n_below + 0.5 * n_equal) / k,
                "z_written": float(s_id / sd) if sd > 0 else float("nan"),
                "is_strict_max": bool(n_below == k - 1 and n_equal == 1),
            })
            if (i + 1) % 25 == 0:
                print(f"#   {cat} {i+1}/{len(texts)}", flush=True)
        print(f"# done {cat}: {sum(r['category'] == cat for r in records)} texts",
              flush=True)

    # ---------------- analysis ----------------
    summary = {}
    for cat in ("causal", "noncausal"):
        rs = [r for r in records if r["category"] == cat]
        if not rs:
            continue
        summary[cat] = {
            "n": len(rs),
            "median_percentile": float(np.median([r["percentile_written"] for r in rs])),
            "mean_percentile": float(np.mean([r["percentile_written"] for r in rs])),
            "median_z": float(np.median([r["z_written"] for r in rs])),
            "frac_strict_max": float(np.mean([r["is_strict_max"] for r in rs])),
            "median_sigma_written": float(np.median([r["sigma_written"] for r in rs])),
            "median_sigma_max": float(np.median([r["sigma_max"] for r in rs])),
        }

    between = {}
    c = [r for r in records if r["category"] == "causal"]
    nn = [r for r in records if r["category"] == "noncausal"]
    if len(c) >= 10 and len(nn) >= 10:
        for key in ("percentile_written", "z_written", "sigma_written"):
            a = np.array([r[key] for r in c], float)
            b = np.array([r[key] for r in nn], float)
            st = mannwhitneyu(a, b, alternative="two-sided", method="asymptotic")
            r_rb = 2.0 * st.statistic / (len(a) * len(b)) - 1.0
            between[key] = {"r": float(r_rb), "p": float(st.pvalue),
                            "median_causal": float(np.median(a)),
                            "median_noncausal": float(np.median(b))}

    out = {"model": args.model, "corpus": corpus, "order": args.order,
           "max_perms": args.max_perms, "n_records": len(records),
           "elapsed_sec": time.time() - t0,
           "summary": summary, "between": between, "records": records}
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)

    nex = sum(r["exact_enumeration"] for r in records)
    print()
    print("=" * 92)
    print(f"Block-order position: {corpus}, unmasking order {args.order}")
    print(f"  {nex}/{len(records)} texts enumerated exactly (all block orders)")
    print("  percentile = where the WRITTEN order sits among all block orders")
    print("  1.00 means the written order is the most forward-costly of them all")
    print("=" * 92)
    print(f"{'group':<11}{'n':>5}{'med pct':>10}{'mean pct':>10}{'med z':>9}"
          f"{'strict max':>12}{'med sigma':>11}{'med max':>10}")
    for cat, s in summary.items():
        print(f"{cat:<11}{s['n']:>5}{s['median_percentile']:>10.4f}"
              f"{s['mean_percentile']:>10.4f}{s['median_z']:>9.3f}"
              f"{s['frac_strict_max']:>12.1%}{s['median_sigma_written']:>11.5f}"
              f"{s['median_sigma_max']:>10.5f}")

    print()
    print("=" * 92)
    print("Causal vs non-causal on each measure")
    print("=" * 92)
    print(f"{'measure':<20}{'med causal':>13}{'med noncaus':>13}{'r':>9}{'p':>12}")
    for key, v in between.items():
        print(f"{key:<20}{v['median_causal']:>13.4f}{v['median_noncausal']:>13.4f}"
              f"{v['r']:>9.4f}{v['p']:>12.3e}")

    print()
    print("=" * 92)
    print("Reading")
    print("=" * 92)
    pc = between.get("percentile_written")
    if pc:
        if pc["p"] < 0.05 and pc["r"] > 0.2:
            print("  The written order ranks HIGHER among arbitrary block orders")
            print("  for causal texts than for non-causal ones.  sigma_block")
            print("  responds to causal order specifically, beyond coherence.")
        elif pc["p"] >= 0.05 or abs(pc["r"]) <= 0.2:
            print("  The written order ranks EQUALLY HIGH in both groups.")
            print("  What sigma_block responds to is the text being in the order")
            print("  it was written in -- discourse coherence, anaphora, topical")
            print("  flow -- not causal structure.  The causal/non-causal effect")
            print("  size is then not evidence that entropy production measures")
            print("  causality.")
        else:
            print("  Non-causal texts rank HIGHER, which fits neither reading")
            print("  and needs explaining before anything is claimed.")
    print(f"\n# wrote {args.out}  ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
