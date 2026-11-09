#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Where does the WRITTEN sentence order rank among ALL sentence orders?

Why this is the decisive test
-----------------------------
Every result so far compares the causal text set against the non-causal text
set, and those two sets differ in more than causal order: their token counts
differ significantly in 4 of 5 corpora, they came from different generation
prompts, and the non-causal texts are still coherent discourse -- topic
continues, pronouns resolve backwards, connectives appear.  So an effect size
r > 0 is equally consistent with sigma responding to "the text is in the order
it was written in" as with sigma responding to causal structure.  No
between-set comparison can separate those.

This test is WITHIN each text.  Concatenate the same sentences in each of the
n! possible orders and ask where the written order ranks:

    sigma(pi) = [ S(x_pi) - S(x_{pi o rev}) ] / L

for a score S.  Length, vocabulary, style and topic are identical across the
permutations by construction, so nothing is left to confound.

    rank 24/24  the written order is the single most forward-costly
                arrangement of these sentences
    rank 12/24  it is unremarkable among arbitrary arrangements

and then, the point:

    causal ranks high, non-causal ranks mid    sigma tracks causal order
    both rank equally high                    sigma tracks the text being in
                                              its written order -- coherence,
                                              anaphora, topical flow -- not
                                              causal structure

Why no any-order chain rule is needed
-------------------------------------
block_order_test.py computes sigma(pi) from the any-order log-probability,
which needs a model trained across all masking rates (LLaDA-8B, hence a GPU).
But the statistic here is a RANK among rearrangements of one token multiset,
and for that any comparable score will do -- the antisymmetry

    sigma(pi) = - sigma(pi o rev)

is purely formal and holds for any S whatsoever.  So the pseudo-log-likelihood
works, which puts this test on the CPU and, more importantly, on the
SCALE-MATCHED PAIR:

    bert-base-uncased  110M  masked  (direction neutral)
    gpt2               117M  causal  (one direction)

Running the decisive test on both is stronger than running it on LLaDA alone,
because it answers the directionality question and the causality question with
the same statistic.

Note the symmetry is a property of the DESIGN, not a finding: the 24 sigma
values come in +/- pairs and sum to zero by construction.  That is exactly why
shuffle_control.py was uninformative -- it compared the written order against
the CENTRE of this symmetric set, which is zero whatever the model does.  The
rank is not forced, and is what is reported here.

Cost: 24 scores per text instead of 3.  bert-base took about 6 min per corpus
in pll_sigma.py, so about 48 min per corpus here; gpt2 is seconds either way.
Two corpora on the scale-matched pair is roughly 1.7 h -- inside SMALL.

    python3 block_order_pll.py --model bert-base-uncased --kind masked \\
        --texts Paper2026/gpt2/text_sets2/fixed_text_Opus46.json \\
        --out blkord_bert-base_Opus46.json
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
from aoar_core import split_into_blocks  # noqa: E402
from order_intervention import load_texts  # noqa: E402
from pll_sigma import CausalScorer, MaskedScorer  # noqa: E402


def permutation_set(n, max_perms, rng):
    """Block orders to score: closed under reversal, containing the identity.

    Closure is required because sigma(pi) needs the score at pi o rev as well.
    For n <= 4 the whole symmetric group fits in 24 and the test is exact
    rather than sampled.
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


def rank_biserial(a, b):
    if len(a) < 2 or len(b) < 2:
        return float("nan"), float("nan")
    st = mannwhitneyu(a, b, alternative="two-sided", method="asymptotic")
    return 2.0 * st.statistic / (len(a) * len(b)) - 1.0, float(st.pvalue)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--kind", choices=("masked", "causal"), required=True)
    ap.add_argument("--texts", required=True)
    ap.add_argument("--max-perms", type=int, default=24,
                    help="24 enumerates 4! exactly; larger n is then sampled")
    ap.add_argument("--dtype", default="float32")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--max-batch", type=int, default=64)
    ap.add_argument("--mask-token-id", type=int, default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    import torch
    if args.threads:
        torch.set_num_threads(args.threads)
    shard_i, shard_n = (int(v) for v in args.shard.split("/"))

    t0 = time.time()
    rng = np.random.default_rng(args.seed)
    Scorer = MaskedScorer if args.kind == "masked" else CausalScorer
    sc = Scorer(args.model, args.dtype, args.device, args.max_batch,
                mask_token_id=args.mask_token_id)
    corpus = os.path.basename(args.texts)
    print(f"# model={args.model} ({args.kind})  corpus={corpus}  "
          f"max_perms={args.max_perms}  shard={shard_i}/{shard_n}", flush=True)

    cats = load_texts(args.texts)
    records = []
    for cat, texts in cats.items():
        if args.limit:
            texts = texts[: args.limit]
        for i, text in enumerate(texts):
            if i % shard_n != shard_i:
                continue
            ids = sc.encode(text)
            blocks = split_into_blocks(ids, sc.decode_one)
            n = len(blocks)
            if n < 3 or len(ids) < 4:
                continue

            perms, exact = permutation_set(n, args.max_perms, rng)
            score = {}
            for p in perms:
                sids = [t for b in p for t in blocks[b]]
                score[p] = sc.score(sids)

            L = float(len(ids))
            ident = tuple(range(n))
            sig = {p: (score[p] - score[tuple(reversed(p))]) / L for p in perms}
            vals = np.array([sig[p] for p in perms], dtype=float)
            s_id = sig[ident]
            k = len(vals)
            # MIDRANK, not a "<=" count.  A score blind to block order makes
            # every sigma exactly zero, and counting vals <= s_id would then
            # put the written order at k/k = 1.00 -- reading as "the most
            # forward-costly arrangement" when in fact the model cannot tell
            # the arrangements apart.  Splitting ties puts that case at
            # exactly 0.50, which is the null this test reads against.
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
            if (i + 1) % 10 == 0:
                print(f"#   {cat} {i+1}/{len(texts)}  ({time.time()-t0:.0f}s)",
                      flush=True)
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
    for key in ("percentile_written", "z_written", "sigma_written"):
        a = np.array([r[key] for r in c], float)
        b = np.array([r[key] for r in nn], float)
        r_rb, p = rank_biserial(a, b)
        between[key] = {"r": float(r_rb), "p": p,
                        "median_causal": float(np.median(a)) if len(a) else None,
                        "median_noncausal": float(np.median(b)) if len(b) else None}

    out = {"model": args.model, "kind": args.kind, "corpus": corpus,
           "max_perms": args.max_perms, "shard": args.shard,
           "n_records": len(records), "elapsed_sec": time.time() - t0,
           "summary": summary, "between": between, "records": records}
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)

    nex = sum(r["exact_enumeration"] for r in records)
    print()
    print("=" * 92)
    print(f"Written block order among all block orders: {args.model} "
          f"({args.kind}), {corpus}")
    print(f"  {nex}/{len(records)} texts enumerated exactly")
    print("  percentile: 0.50 = indistinguishable from an arbitrary order, "
          "1.00 = the most forward-costly of them all")
    print("=" * 92)
    print(f"{'group':<11}{'n':>5}{'med pct':>10}{'mean pct':>10}{'med z':>9}"
          f"{'strict max':>12}{'med sigma':>11}{'med max':>10}")
    for cat, s in summary.items():
        print(f"{cat:<11}{s['n']:>5}{s['median_percentile']:>10.4f}"
              f"{s['mean_percentile']:>10.4f}{s['median_z']:>9.3f}"
              f"{s['frac_strict_max']:>12.1%}{s['median_sigma_written']:>11.5f}"
              f"{s['median_sigma_max']:>10.5f}")

    print()
    print(f"{'measure':<20}{'med causal':>13}{'med noncaus':>13}{'r':>9}{'p':>12}")
    for key, v in between.items():
        if v["median_causal"] is None:
            continue
        print(f"{key:<20}{v['median_causal']:>13.4f}{v['median_noncausal']:>13.4f}"
              f"{v['r']:>9.4f}{v['p']:>12.3e}")

    print()
    print("=" * 92)
    print("Reading")
    print("=" * 92)
    pc = between.get("percentile_written")
    if pc and pc["median_causal"] is not None:
        if pc["p"] < 0.05 and pc["r"] > 0.2:
            print("  The written order ranks HIGHER among arbitrary block")
            print("  orders for causal texts than for non-causal ones.  Within")
            print("  a text, with length and vocabulary held fixed, sigma")
            print("  responds to causal order specifically.")
        elif pc["p"] >= 0.05 or abs(pc["r"]) <= 0.2:
            print("  The written order ranks EQUALLY HIGH in both groups.")
            print("  With every between-set confound removed, what sigma")
            print("  responds to is the text being in its written order, not")
            print("  its causal structure.  The causal/non-causal effect size")
            print("  is then not evidence that entropy production measures")
            print("  causality.")
        else:
            print("  Non-causal texts rank HIGHER, which fits neither reading")
            print("  and must be explained before anything is claimed.")
    print(f"\n# wrote {args.out}  ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
