#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Is the fixed-text entropy production a property of the TEXT or of the
AUTOREGRESSIVE FACTORISATION?

The question
------------
Sagawa (PRX Intelligence 1, 023013, 2026) measures, for a fixed text x,

    sigma = [ log P(x) - log P(x~) ] / L          x~ = x reversed

with an autoregressive evaluator, and reads sigma > 0 as entropy production:
an arrow of time carried by the text.  But an autoregressive model is trained
in ONE direction only, so the reversed text is out of its training
distribution.  Two explanations of sigma > 0 cannot be separated by such a
model:

    (i)  the text carries a causal arrow,
    (ii) the EVALUATOR was only ever trained to run forward.

Replacing the evaluator with a masked (bidirectional) language model removes
(ii) by construction.  Its score for position k,

    log p_theta(x_k | x_{-k}),

uses context on both sides, so for x and for x~ every prediction sees the SAME
multiset of context tokens -- only their arrangement differs.  Neither
direction is privileged by the factorisation.  Therefore:

    sigma_masked ~ 0        sigma was a property of the autoregressive
                            factorisation, not of the text
    sigma_masked > 0        the asymmetry survives a direction-neutral
                            evaluator

What this script does NOT claim
-------------------------------
The masked score used here is the PSEUDO-log-likelihood
PLL(x) = sum_k log p_theta(x_k | x_{-k}), which is what BERT is trained to
approximate.  It is NOT the log-probability of any joint distribution: a
masked model's conditionals are in general incompatible with every joint
(arXiv:2605.16378).  So PLL(x) - PLL(x~) is a well-defined score difference
but it is NOT a Kullback-Leibler divergence, and the identification
sigma = D_KL(P_forward || P_backward) does not hold for it.  That is a
feature here, not a defect: the object under test is the EVALUATOR'S
directional bias, and for that a direction-neutral scorer is exactly the right
instrument.  (The any-order chain rule in aoar_core.py is the other route,
which does give a genuine log-probability, at the cost of a free order pi.)

The scale confound, and how it is controlled
--------------------------------------------
The reproduction found GPT-2 (117M) unable to separate causal from non-causal
texts at block level in 3 of 5 corpora, while Qwen3-4B-Base separates in 5 of
5.  So a null result from BERT-base (110M) would be ambiguous between "because
it is bidirectional" and "because it is small".  Two controls:

  1. SCALE-MATCHED PAIR.  BERT-base (110M, masked) against GPT-2 (117M,
     causal): same era, near-identical size, comparable training corpora.  A
     difference between these two is a difference of directionality, not of
     scale.  Run both with this script so the tokenisation, block splitting
     and statistics are identical.

  2. LARGE BIDIRECTIONAL.  LLaDA-8B-Base scored by PLL, against Qwen3-4B-Base
     scored autoregressively.  Removes any residual doubt about scale.

Both reversals are measured separately and they answer different questions:

  * TOKEN reversal destroys grammar, so every model scores it far worse.  The
    resulting sigma is dominated by syntax and says little about causality.
  * BLOCK reversal keeps each sentence intact and permutes sentence order
    only, so what remains is discourse order.  Sagawa's headline result is at
    block level, and so is the comparison that matters here.

    python3 pll_sigma.py --model bert-base-uncased --kind masked \\
        --texts Paper2026/gpt2/text_sets2/fixed_text_Opus46.json \\
        --out pll_bert-base_Opus46.json
    python3 pll_sigma.py --model gpt2 --kind causal \\
        --texts Paper2026/gpt2/text_sets2/fixed_text_Opus46.json \\
        --out pll_gpt2_Opus46.json
"""

import argparse
import json
import os
import sys
import time

import numpy as np
import torch
import transformers
from scipy.stats import mannwhitneyu
from transformers import AutoConfig, AutoModelForCausalLM, AutoModelForMaskedLM, AutoTokenizer

# `torch_dtype` was renamed to `dtype` around transformers 4.56 and the old
# name deprecated; the Kyoto ICR pytorch/2.4.1 module ships 4.45.2, where only
# `torch_dtype` exists and `dtype` would be forwarded into the config instead
# of selecting a precision.  Pick the name this installation actually accepts
# rather than assuming either one.
_TV = tuple(int(x) for x in transformers.__version__.split(".")[:2])
DTYPE_KW = "dtype" if _TV >= (4, 56) else "torch_dtype"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aoar_core import block_reverse, split_into_blocks, token_reverse  # noqa: E402
from order_intervention import load_texts  # noqa: E402


# --------------------------------------------------------------------------
# scorers
# --------------------------------------------------------------------------
class MaskedScorer:
    """Pseudo-log-likelihood from a masked language model.

    PLL(x) = sum_k log p_theta(x_k | x_{-k}), one forward pass per masked
    position, batched.  Special tokens ([CLS]/[SEP]) wrap the content but are
    never scored and never reversed -- reversing them would change the input
    format rather than the text.
    """

    kind = "masked"

    def __init__(self, name, dtype="float32", device="cpu", max_batch=64,
                 mask_token_id=None):
        self.tok = AutoTokenizer.from_pretrained(name, trust_remote_code=True)
        td = getattr(torch, dtype)
        cfg = AutoConfig.from_pretrained(name, trust_remote_code=True)
        model = None
        if hasattr(cfg, "init_device"):
            # LLaDA hands config.init_device to every nn.Linear, so building on
            # meta is the only way to avoid initialising 8B parameters on the
            # CPU before the checkpoint overwrites them.
            try:
                cfg.init_device = "meta"
                model = AutoModelForMaskedLM.from_pretrained(
                    name, config=cfg, trust_remote_code=True,
                    low_cpu_mem_usage=True, **{DTYPE_KW: td})
            except Exception:
                model = None
        if model is None:
            try:
                model = AutoModelForMaskedLM.from_pretrained(
                    name, trust_remote_code=True, **{DTYPE_KW: td})
            except Exception:
                from transformers import AutoModel
                model = AutoModel.from_pretrained(
                    name, trust_remote_code=True, **{DTYPE_KW: td})
        self.model = model.to(device).eval()
        self.device = device
        self.max_batch = max_batch
        mid = mask_token_id if mask_token_id is not None else self.tok.mask_token_id
        if mid is None:
            raise SystemExit(
                f"{name} has no mask token; pass --mask-token-id explicitly")
        self.mask_id = int(mid)
        # the wrapper that the model expects around content tokens
        probe = self.tok("x", add_special_tokens=True)["input_ids"]
        inner = self.tok("x", add_special_tokens=False)["input_ids"]
        j = probe.index(inner[0])
        self.prefix = probe[:j]
        self.suffix = probe[j + len(inner):]

    def encode(self, text):
        return self.tok(text, add_special_tokens=False)["input_ids"]

    def decode_one(self, tid):
        return self.tok.decode([tid])

    def score(self, ids):
        """PLL of a content-token sequence."""
        full = self.prefix + list(ids) + self.suffix
        off = len(self.prefix)
        n = len(ids)
        rows = []
        for k in range(n):
            r = list(full)
            r[off + k] = self.mask_id
            rows.append(r)
        total = 0.0
        for a in range(0, n, self.max_batch):
            b = slice(a, min(a + self.max_batch, n))
            x = torch.tensor(rows[b], dtype=torch.long, device=self.device)
            pos = torch.arange(a, min(a + self.max_batch, n)) + off
            pos = pos.to(self.device)
            tgt = torch.tensor([ids[k] for k in range(a, min(a + self.max_batch, n))],
                               dtype=torch.long, device=self.device)
            with torch.no_grad():
                o = self.model(x)
                logits = o.logits if hasattr(o, "logits") else o[0]
                sel = logits[torch.arange(len(pos), device=self.device), pos]
                lp = torch.log_softmax(sel.float(), dim=-1)
                total += float(lp.gather(1, tgt.unsqueeze(1)).sum())
        return total


class CausalScorer:
    """Exact log P(x) from an autoregressive model, the original protocol.

    The first content token needs a conditioning token to be scored at all, so
    one BOS (or EOS used as BOS, for GPT-2) is prepended.  Every content token
    is then scored exactly once, as in sum_k log p(x_k | x_{<k}).
    """

    kind = "causal"

    def __init__(self, name, dtype="float32", device="cpu", max_batch=64, **_):
        self.tok = AutoTokenizer.from_pretrained(name, trust_remote_code=True)
        td = getattr(torch, dtype)
        self.model = AutoModelForCausalLM.from_pretrained(
            name, trust_remote_code=True,
            **{DTYPE_KW: td}).to(device).eval()
        self.device = device
        bos = self.tok.bos_token_id
        if bos is None:
            bos = self.tok.eos_token_id
        if bos is None:
            raise SystemExit(f"{name} has neither BOS nor EOS to condition on")
        self.bos = int(bos)

    def encode(self, text):
        return self.tok(text, add_special_tokens=False)["input_ids"]

    def decode_one(self, tid):
        return self.tok.decode([tid])

    def score(self, ids):
        x = torch.tensor([[self.bos] + list(ids)], dtype=torch.long,
                         device=self.device)
        with torch.no_grad():
            logits = self.model(x).logits[0].float()
        lp = torch.log_softmax(logits[:-1], dim=-1)
        tgt = torch.tensor(list(ids), dtype=torch.long, device=self.device)
        return float(lp.gather(1, tgt.unsqueeze(1)).sum())


# --------------------------------------------------------------------------
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
    ap.add_argument("--dtype", default="float32")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--max-batch", type=int, default=64)
    ap.add_argument("--mask-token-id", type=int, default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--threads", type=int, default=0,
                    help="torch CPU threads; 0 leaves the default")
    ap.add_argument("--shard", default="0/1",
                    help="i/n: take every n-th text starting at i, within each "
                         "category.  Lets a long run be split across several "
                         "12-hour SMALL-queue jobs; merge with merge_pll.py")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    shard_i, shard_n = (int(v) for v in args.shard.split("/"))
    if not (0 <= shard_i < shard_n):
        raise SystemExit(f"bad --shard {args.shard}")

    if args.threads:
        torch.set_num_threads(args.threads)
    t0 = time.time()
    Scorer = MaskedScorer if args.kind == "masked" else CausalScorer
    sc = Scorer(args.model, args.dtype, args.device, args.max_batch,
                mask_token_id=args.mask_token_id)
    corpus = os.path.basename(args.texts)
    print(f"# model={args.model} ({args.kind})  corpus={corpus}  "
          f"device={args.device}  threads={torch.get_num_threads()}  "
          f"shard={shard_i}/{shard_n}", flush=True)

    cats = load_texts(args.texts)
    records = []
    for cat, texts in cats.items():
        if args.limit:
            texts = texts[: args.limit]
        for i, text in enumerate(texts):
            if i % shard_n != shard_i:
                continue
            ids = sc.encode(text)
            if len(ids) < 4:
                continue
            blocks = split_into_blocks(ids, sc.decode_one)
            rev_t = token_reverse(ids)
            rev_b, nblk = block_reverse(ids, sc.decode_one)
            L = float(len(ids))
            s_f = sc.score(ids)
            s_t = sc.score(rev_t)
            s_b = sc.score(rev_b)
            records.append({
                "category": cat, "index": i, "T": int(len(ids)),
                "n_blocks": int(nblk), "n_blocks_split": len(blocks),
                "score_forward": s_f,
                "score_token_reversed": s_t,
                "score_block_reversed": s_b,
                "sigma_token_per_T": (s_f - s_t) / L,
                "sigma_block_per_T": (s_f - s_b) / L,
            })
            if (i + 1) % 25 == 0:
                print(f"#   {cat} {i+1}/{len(texts)}  "
                      f"({time.time()-t0:.0f}s)", flush=True)
        print(f"# done {cat}: {sum(r['category'] == cat for r in records)} texts",
              flush=True)

    stats = {}
    c = [r for r in records if r["category"] == "causal"]
    n = [r for r in records if r["category"] == "noncausal"]
    for key in ("sigma_block_per_T", "sigma_token_per_T"):
        a = np.array([r[key] for r in c], float)
        b = np.array([r[key] for r in n], float)
        r_rb, p = rank_biserial(a, b)
        stats[key] = {
            "n_causal": len(a), "n_noncausal": len(b),
            "median_causal": float(np.median(a)) if len(a) else None,
            "median_noncausal": float(np.median(b)) if len(b) else None,
            "mean_causal": float(a.mean()) if len(a) else None,
            "mean_noncausal": float(b.mean()) if len(b) else None,
            "median_all": float(np.median(np.concatenate([a, b]))),
            "rank_biserial": float(r_rb), "p": p,
        }

    out = {"model": args.model, "kind": args.kind, "corpus": corpus,
           "dtype": args.dtype, "shard": args.shard, "n_records": len(records),
           "elapsed_sec": time.time() - t0,
           "stats": stats, "records": records}
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)

    print()
    print("=" * 92)
    print(f"{args.model} ({args.kind})  on  {corpus}")
    print("  sigma > 0 means the forward text scores higher than the reversed one")
    print("=" * 92)
    print(f"{'reversal':<14}{'med all':>11}{'med causal':>12}{'med noncaus':>13}"
          f"{'r':>9}{'p':>12}")
    for key, s in stats.items():
        lab = "block" if "block" in key else "token"
        print(f"{lab:<14}{s['median_all']:>11.5f}{s['median_causal']:>12.5f}"
              f"{s['median_noncausal']:>13.5f}{s['rank_biserial']:>9.4f}"
              f"{s['p']:>12.3e}")
    print(f"\n# wrote {args.out}  ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
