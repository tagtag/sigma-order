#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Synthetic pll_sigma.py output, to check merge_pll.py before the cluster run.

Two things need checking and neither needs a GPU or any weights:

  1. SHARD MERGING.  pll_sigma.py writes one file per (model, corpus, shard).
     If merge_pll.py double-counted a text -- say because a shard was re-run
     after a timeout -- every n would be inflated and every median subtly
     wrong, with nothing in the output to show it.  Here each cell is written
     as two shards AND one of them is written twice, so a correct merge still
     reports exactly 200 texts.

  2. THE VERDICT BRANCHES.  merge_pll.py ends with a plain-language reading,
     and a reading that fires on the wrong branch is worse than none.  Both
     scenarios are generated and the expected branch stated, so the printed
     verdict can be compared against what it should be.

        scenario A  masked sigma ~ 0, causal sigma > 0 with separation
                    -> "the entropy production largely disappears"
        scenario B  both evaluators separate
                    -> "the separation survives ... at matched scale"

    python3 make_mock_pll.py --outdir /tmp/mock_pll_A --scenario A
    python3 merge_pll.py --dir /tmp/mock_pll_A
"""

import argparse
import json
import os

import numpy as np

CORPORA = ["Opus46", "GPT54"]
N_PER_CAT = 100


def cell(rng, model, kind, corpus, shard, mu_c, mu_n, sd, tok_scale):
    """One (model, corpus, shard) file's worth of records."""
    i_shard, n_shard = (int(v) for v in shard.split("/"))
    recs = []
    for cat, mu in (("causal", mu_c), ("noncausal", mu_n)):
        for i in range(N_PER_CAT):
            if i % n_shard != i_shard:
                continue
            T = int(rng.integers(30, 50))
            s_blk = float(rng.normal(mu, sd))
            s_tok = float(rng.normal(mu * tok_scale + 1.5, sd * 2))
            recs.append({
                "category": cat, "index": i, "T": T,
                "n_blocks": 4, "n_blocks_split": 4,
                "score_forward": -T * 3.0,
                "score_token_reversed": -T * 3.0 - s_tok * T,
                "score_block_reversed": -T * 3.0 - s_blk * T,
                "sigma_token_per_T": s_tok,
                "sigma_block_per_T": s_blk,
            })
    return {"model": model, "kind": kind, "corpus": f"fixed_text_{corpus}.json",
            "dtype": "float32", "shard": shard, "n_records": len(recs),
            "elapsed_sec": 1.0, "stats": {}, "records": recs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--scenario", choices=("A", "B"), default="A")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    os.makedirs(args.outdir, exist_ok=True)

    if args.scenario == "A":
        # masked evaluator finds nothing; causal evaluator separates strongly
        spec = [("bert-base-uncased", "masked", 0.01, 0.00, 0.12, 8.0),
                ("gpt2", "causal", 0.38, 0.02, 0.15, 5.0)]
        expect = "the entropy production largely DISAPPEARS"
    else:
        # both separate, masked slightly less
        spec = [("bert-base-uncased", "masked", 0.31, 0.05, 0.14, 6.0),
                ("gpt2", "causal", 0.38, 0.02, 0.15, 5.0)]
        expect = "the separation survives a direction-neutral evaluator"

    written = 0
    for model, kind, mu_c, mu_n, sd, tks in spec:
        tag = model.replace("/", "_")
        for corpus in CORPORA:
            for shard in ("0/2", "1/2"):
                d = cell(rng, model, kind, corpus, shard, mu_c, mu_n, sd, tks)
                p = os.path.join(
                    args.outdir,
                    f"pll_{tag}__{corpus}__{shard.replace('/', '-')}.json")
                with open(p, "w") as f:
                    json.dump(d, f)
                written += 1
            # a deliberate duplicate of shard 0/2 under a different file name,
            # as a re-run after a timeout would leave behind.  A correct merge
            # keys on (category, index) and still reports n = 200.
            d = cell(rng, model, kind, corpus, "0/2", mu_c, mu_n, sd, tks)
            p = os.path.join(
                args.outdir, f"pll_{tag}__{corpus}__0-2__rerun.json")
            with open(p, "w") as f:
                json.dump(d, f)
            written += 1

    print(f"# scenario {args.scenario}: wrote {written} files to {args.outdir}")
    print(f"# each (model, corpus) cell must merge to exactly "
          f"{2 * N_PER_CAT} texts despite the duplicate shard")
    print(f"# expected verdict to contain: {expect!r}")


if __name__ == "__main__":
    main()
