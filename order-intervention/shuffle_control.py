#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The decisive control: does sigma_block respond to CAUSAL ORDER, or to the text?

The hypothesis under test
-------------------------
sigma_block is read as a probe of causal structure because causally ordered
texts score higher than non-causal ones.  But the two groups were written from
different prompts and differ in more than causal order: our measurements found
their token counts differ significantly in 4 of 5 corpora, and non-causal
texts carry a substantial sigma_block in masked models (median 0.22-0.31)
where an autoregressive evaluator gives about zero.  If sigma_block mostly
reflects style, vocabulary or position rather than order, the group difference
would follow without any causal content.

The control
-----------
Compare each CAUSAL text with ITSELF, sentences shuffled:

    original   The glass slipped from her hand. It fell to the floor.
               It broke into many pieces. She swept them up carefully.
    shuffled   It broke into many pieces. She swept them up carefully.
               The glass slipped from her hand. It fell to the floor.

Same sentences, same tokens, same length, same topic, same style.  The ONLY
thing that changes is whether the sentence order is the causal one.  This is a
within-text, exactly matched comparison -- no confound survives it.

    sigma_block(original) >> sigma_block(shuffled)
        the forward order being the causal one is what costs; sigma_block does
        track causal order
    sigma_block(original) ~= sigma_block(shuffled)
        reversing an already-arbitrary order costs the same as reversing the
        causal one; sigma_block is not measuring causal order

The non-causal texts get the same treatment as a sanity check: their order is
arbitrary to begin with, so shuffling them should change nothing.

Statistics: the comparison is paired within text, so Wilcoxon signed-rank with
the matched-pairs rank-biserial correlation, not Mann-Whitney.  Several
shuffles per text are averaged so the result does not hinge on which
permutation was drawn.

    python3 shuffle_control.py --model GSAI-ML/LLaDA-8B-Base \\
        --mask-token-id 126336 \\
        --texts Paper2026/gpt2/text_sets2/fixed_text_Opus46.json \\
        --order l2r --shuffles 3 --out shuffle_control_Opus46.json
"""

import argparse
import json
import os
import sys
import time

import numpy as np
from scipy.stats import wilcoxon

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aoar_core import (aoar_logprob, block_reverse, make_order,  # noqa: E402
                       split_into_blocks)
from order_intervention import HFMaskedProvider, load_texts  # noqa: E402


def sigma_block_of(ids, order_spec, prov, chunk):
    """sigma_block for one token sequence under one unmasking order."""
    order = make_order(order_spec, len(ids), prov, ids)
    fwd = aoar_logprob(ids, order, prov, chunk)
    rev, nblk = block_reverse(ids, prov.decode_one)
    # the reversal may retokenise to a different length only if blocks were
    # split oddly; guard so the order stays a valid permutation
    if len(rev) != len(ids):
        return None, nblk
    order_r = make_order(order_spec, len(rev), prov, rev)
    return (fwd - aoar_logprob(rev, order_r, prov, chunk)) / len(ids), nblk


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--texts", required=True)
    ap.add_argument("--order", default="l2r")
    ap.add_argument("--shuffles", type=int, default=3,
                    help="shuffled variants per text, averaged")
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
          f"shuffles={args.shuffles}", flush=True)

    cats = load_texts(args.texts)
    records = []
    for cat, texts in cats.items():
        if args.limit:
            texts = texts[: args.limit]
        for i, text in enumerate(texts):
            ids = prov.encode(text)
            blocks = split_into_blocks(ids, prov.decode_one)
            if len(blocks) < 3 or len(ids) < 4:
                continue  # need enough blocks for shuffling to mean anything

            s_orig, nblk = sigma_block_of(ids, args.order, prov, args.max_batch)
            if s_orig is None:
                continue

            s_shuf = []
            for s in range(args.shuffles):
                perm = rng.permutation(len(blocks))
                # a permutation that leaves the order unchanged teaches nothing
                tries = 0
                while np.array_equal(perm, np.arange(len(blocks))) and tries < 10:
                    perm = rng.permutation(len(blocks))
                    tries += 1
                sids = [t for b in perm for t in blocks[b]]
                v, _ = sigma_block_of(sids, args.order, prov, args.max_batch)
                if v is not None:
                    s_shuf.append(v)
            if not s_shuf:
                continue

            records.append({
                "category": cat, "index": i, "T": len(ids), "n_blocks": nblk,
                "sigma_block_per_T_original": s_orig,
                "sigma_block_per_T_shuffled_mean": float(np.mean(s_shuf)),
                "sigma_block_per_T_shuffled_all": [float(v) for v in s_shuf],
            })
            if (i + 1) % 25 == 0:
                print(f"#   {cat} {i+1}/{len(texts)}", flush=True)
        print(f"# done {cat}: {sum(r['category']==cat for r in records)} texts",
              flush=True)

    # ---------------- analysis ----------------
    summary = {}
    for cat in ("causal", "noncausal"):
        rs = [r for r in records if r["category"] == cat]
        if not rs:
            continue
        a = np.array([r["sigma_block_per_T_original"] for r in rs])
        b = np.array([r["sigma_block_per_T_shuffled_mean"] for r in rs])
        d = a - b
        nz = d[d != 0]
        if len(nz) >= 10:
            st = wilcoxon(a, b, alternative="two-sided",
                          zero_method="wilcox")
            # matched-pairs rank-biserial: (W+ - W-) / (W+ + W-)
            from scipy.stats import rankdata
            rk = rankdata(np.abs(nz))
            wp, wm = rk[nz > 0].sum(), rk[nz < 0].sum()
            rrb = float((wp - wm) / (wp + wm))
            p = float(st.pvalue)
        else:
            rrb, p = float("nan"), float("nan")
        summary[cat] = {
            "n": len(rs),
            "median_original": float(np.median(a)),
            "median_shuffled": float(np.median(b)),
            "median_difference": float(np.median(d)),
            "mean_difference": float(d.mean()),
            "frac_original_larger": float((d > 0).mean()),
            "rank_biserial_paired": rrb,
            "p_wilcoxon": p,
        }

    out = {"model": args.model, "corpus": corpus, "order": args.order,
           "shuffles": args.shuffles, "n_records": len(records),
           "elapsed_sec": time.time() - t0,
           "summary": summary, "records": records}
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)

    print()
    print("=" * 86)
    print(f"Shuffle control: {corpus}, order {args.order}")
    print("  original = sentences in their given order")
    print("  shuffled = the SAME sentences, order permuted")
    print("=" * 86)
    print(f"{'group':<11}{'n':>5}{'median orig':>13}{'median shuf':>13}"
          f"{'median diff':>13}{'orig>shuf':>11}{'r_paired':>10}{'p':>12}")
    for cat, s in summary.items():
        print(f"{cat:<11}{s['n']:>5}{s['median_original']:>13.5f}"
              f"{s['median_shuffled']:>13.5f}{s['median_difference']:>13.5f}"
              f"{s['frac_original_larger']:>11.2%}{s['rank_biserial_paired']:>10.4f}"
              f"{s['p_wilcoxon']:>12.3e}")

    print()
    print("=" * 86)
    print("Reading")
    print("=" * 86)
    c = summary.get("causal")
    if c:
        if c["p_wilcoxon"] < 0.05 and c["median_difference"] > 0:
            print("  CAUSAL texts lose sigma_block when their sentences are")
            print("  shuffled: the forward order being the causal one is part of")
            print("  what the measure responds to.")
        elif c["p_wilcoxon"] >= 0.05:
            print("  CAUSAL texts keep their sigma_block after shuffling:")
            print("  reversing an already-arbitrary order costs as much as")
            print("  reversing the causal one.  sigma_block is then not")
            print("  measuring causal order.")
        else:
            print("  CAUSAL texts GAIN sigma_block when shuffled, which fits")
            print("  neither reading cleanly and needs explaining.")
    n = summary.get("noncausal")
    if n:
        print(f"  Non-causal texts shift by {n['median_difference']:+.5f} "
              f"(p={n['p_wilcoxon']:.3g}); their order was arbitrary already,")
        print("  so a large shift here would mean the shuffle itself, not the")
        print("  loss of causal order, is doing the work.")
    print(f"\n# wrote {args.out}  ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
