#!/usr/bin/env python3
"""Where does the written sentence order rank, by forward/backward sigma?

The estimator, in one line.  For a text whose sentences are the blocks
b_1 ... b_n, and for each block arrangement p of the symmetric group:

    f(p) = [ log P_l2r(x_p) - log P_r2l(x_p) ] / L

where x_p is the token sequence of the text with its blocks in order p, and
log P_pi is the any-order chain rule under unmasking order pi.  Both terms
score THE SAME text; only the direction of assembly differs.  The reading is

    percentile_written = midrank of f(identity) among { f(p) }

and the question is whether that percentile differs between causally ordered
and non-causally ordered texts.

Why this is the right instrument for a masked model:

  * f(p) vanishes IDENTICALLY, for every p, when the model's conditionals
    come from a joint distribution -- both terms collapse to log P(x_p).  So
    a rank only exists at all because the model is incompatible.  What the
    percentile measures is how that incompatibility is distributed over
    arrangements, not how large it is.
  * the comparison is WITHIN one text: all n! arrangements have identical
    length, vocabulary, topic and style, so the confounds that separate the
    causal and non-causal text sets cannot act here.
  * the null is 0.50 by exchangeability, not by antisymmetry.  Under the
    hypothesis that the written order is just one arrangement among n!, its
    rank is uniform, so the midrank has expectation 0.50.  (The PLL block
    instrument got 0.50 from sigma(p) = -sigma(p o rev); f has no such
    symmetry, and does not need it.)

An autoregressive model CANNOT be run here: log P_r2l needs
P(x_1 | x_2..x_L), which conditions on the future.  For those evaluators use
block_order_pll.py with --kind causal, whose score is the exact
log-likelihood.

Cost: n! scores per text, each scored in BOTH directions, so 2 n! chain-rule
passes of L kernel evaluations.  For the four-sentence texts in this
repository that is 48 passes per text, twice what block_order_pll.py does.

    python3 -I block_sigma_fb.py --model bert-base-uncased \\
        --texts fixed_text_Fable5.json --out out.json

    python3 -I block_sigma_fb.py --model /path/to/LLaDA-8B-Base \\
        --texts fixed_text_Fable5.json --dtype bfloat16 --out out.json
"""

import argparse
import json
import os
import sys
import time

import numpy as np
from scipy.stats import mannwhitneyu

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aoar_core import aoar_logprob, make_order, split_into_blocks  # noqa: E402
from block_order_pll import permutation_set  # noqa: E402
from order_intervention import load_texts  # noqa: E402


def rank_biserial(a, b):
    """P(a > b) - P(b > a) and its two-sided p-value; ties count half."""
    if len(a) < 2 or len(b) < 2:
        return float("nan"), float("nan")
    st = mannwhitneyu(a, b, alternative="two-sided", method="asymptotic")
    return 2.0 * st.statistic / (len(a) * len(b)) - 1.0, float(st.pvalue)


def sigma_fb(token_ids, provider, chunk):
    """[ log P_l2r(x) - log P_r2l(x) ] / L for one token sequence."""
    L = len(token_ids)
    ll_f = aoar_logprob(token_ids, make_order("l2r", L), provider, chunk)
    ll_b = aoar_logprob(token_ids, make_order("r2l", L), provider, chunk)
    return (ll_f - ll_b) / float(L), ll_f, ll_b


def run_one_text(text, provider, max_perms, rng, chunk, tie_tol=1e-12):
    """All block arrangements of one text, and where the written one ranks."""
    ids = provider.encode(text)
    blocks = split_into_blocks(ids, provider.decode_one)
    n = len(blocks)
    if n < 3 or len(ids) < 4:
        return None, {"n_blocks": n, "T": len(ids), "reason": "too few blocks"}

    perms, exact = permutation_set(n, max_perms, rng)
    ident = tuple(range(n))
    if ident not in perms:
        perms = sorted(set(perms) | {ident})

    vals, detail = {}, {}
    for p in perms:
        sids = [t for b in p for t in blocks[b]]
        s, lf, lb = sigma_fb(sids, provider, chunk)
        vals[p] = s
        detail[",".join(map(str, p))] = {"sigma_fb": s, "ll_l2r": lf,
                                         "ll_r2l": lb}

    arr = np.array([vals[p] for p in perms], dtype=np.float64)
    s_id = vals[ident]
    k = len(arr)
    sd = float(arr.std(ddof=1)) if k > 1 else 0.0

    # Values closer together than tie_tol are treated as tied.  Two cases
    # need this and both are real:
    #   * a model whose conditionals come from a joint gives f(p) = 0 for
    #     every p, but in floating point they differ by ~1e-16.  Ranking
    #     those would manufacture a percentile out of rounding noise.
    #   * a text whose blocks are identical has arrangements that are the
    #     same token sequence, so their f agree exactly and must stay tied.
    # Real readings are of order 1e-2 per token, so 1e-12 separates the two
    # situations by ten orders of magnitude.
    degenerate = bool(float(arr.max() - arr.min()) <= tie_tol)
    if degenerate:
        pct, z = 0.5, float("nan")       # no information: the null itself
    else:
        n_below = int((arr < s_id - tie_tol).sum())
        n_equal = int((np.abs(arr - s_id) <= tie_tol).sum())
        pct = (n_below + 0.5 * n_equal) / k
        z = float(s_id / sd) if sd > 0 else float("nan")

    rec = {
        "T": len(ids), "n_blocks": n, "n_perms": k, "exact": bool(exact),
        "sigma_fb_written": float(s_id),
        "sigma_fb_median": float(np.median(arr)),
        "sigma_fb_sd": sd,
        "spread": float(arr.max() - arr.min()),
        # 0.50 under exchangeability of the written order with the others
        "percentile_written": pct,
        "z_written": z,
        "degenerate": degenerate,
        "perms": detail,
    }
    return rec, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="local model directory")
    ap.add_argument("--texts", required=True, help="fixed-text corpus JSON")
    ap.add_argument("--max-perms", type=int, default=24,
                    help="24 enumerates 4! exactly; larger n is then sampled")
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--device", default=None)
    ap.add_argument("--max-batch", type=int, default=64)
    ap.add_argument("--chunk", type=int, default=64)
    ap.add_argument("--tie-tol", type=float, default=1e-12,
                    help="values this close are tied; guards against a\n                          percentile made out of rounding noise when the\n                          model is (nearly) compatible")
    ap.add_argument("--mask-token-id", type=int, default=None)
    ap.add_argument("--limit", type=int, default=None,
                    help="debug: only this many texts per category")
    ap.add_argument("--shard", default=None,
                    help="i/n: run only this shard of the texts")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from order_intervention import HFMaskedProvider
    prov = HFMaskedProvider(args.model, args.mask_token_id, args.dtype,
                            args.device, args.max_batch)
    rng = np.random.default_rng(args.seed)

    cats = load_texts(args.texts)
    corpus = os.path.basename(args.texts).replace(".json", "")
    print(f"# model={args.model}  mask_id={prov.mask_id}  "
          f"device={prov.device}  corpus={corpus}", flush=True)

    items = []
    for cat in ("causal", "noncausal"):
        texts = cats.get(cat, [])
        if args.limit:
            texts = texts[:args.limit]
        items += [(cat, i, t) for i, t in enumerate(texts)]
    if args.shard:
        i, n = (int(v) for v in args.shard.split("/"))
        items = [it for j, it in enumerate(items) if j % n == i]
        print(f"# shard {i}/{n}: {len(items)} texts", flush=True)

    t0 = time.time()
    records, skipped = [], []
    for j, (cat, idx, text) in enumerate(items):
        rec, skip = run_one_text(text, prov, args.max_perms, rng, args.chunk,
                                 args.tie_tol)
        if rec is None:
            skip.update({"category": cat, "index": idx})
            skipped.append(skip)
            continue
        rec.update({"category": cat, "index": idx, "text": text})
        records.append(rec)
        if (j + 1) % 20 == 0:
            print(f"#   {j + 1}/{len(items)}  "
                  f"{time.time() - t0:.0f}s", flush=True)
    elapsed = time.time() - t0

    pc = [r["percentile_written"] for r in records if r["category"] == "causal"]
    pn = [r["percentile_written"] for r in records
          if r["category"] == "noncausal"]
    r_rb, p_val = rank_biserial(pc, pn)
    n_degen = sum(1 for r in records if r["degenerate"])

    out = {
        "meta": {
            "script": "block_sigma_fb.py",
            "estimator": "f(p) = [log P_l2r(x_p) - log P_r2l(x_p)] / L; "
                         "percentile of the written order among all f(p)",
            "model": args.model, "corpus": corpus,
            "mask_token_id": prov.mask_id, "device": str(prov.device),
            "max_perms": args.max_perms, "seed": args.seed,
            "tie_tol": args.tie_tol,
            "shard": args.shard, "limit": args.limit,
            "n_texts": len(records), "n_skipped": len(skipped),
            "n_degenerate": n_degen,
            "elapsed_sec": elapsed,
        },
        "summary": {
            "median_percentile_causal": (float(np.median(pc)) if pc
                                         else float("nan")),
            "median_percentile_noncausal": (float(np.median(pn)) if pn
                                            else float("nan")),
            "rank_biserial": float(r_rb), "p_value": float(p_val),
            "n_causal": len(pc), "n_noncausal": len(pn),
        },
        "records": records,
        "skipped": skipped,
    }
    json.dump(out, open(args.out, "w"), indent=1)

    print(f"# {len(records)} texts, {len(skipped)} skipped, "
          f"{n_degen} degenerate, {elapsed:.0f}s")
    print(f"# median percentile  causal {np.median(pc) if pc else float('nan'):.4f}"
          f"   non-causal {np.median(pn) if pn else float('nan'):.4f}")
    print(f"# rank-biserial r = {r_rb:+.3f}   p = {p_val:.3g}")
    print(f"# wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
