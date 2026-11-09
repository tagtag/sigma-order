#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Order intervention on the fixed-text entropy-production protocol of

  T. Sagawa, PRX Intelligence 1, 023013 (2026), arXiv:2604.07867
  code/data: https://github.com/taksagawa/Paper2026

For a masked (any-order) generative model, the unmasking order pi is a free
parameter.  This script computes, for every text in a corpus and one choice of
pi, the fixed-text entropy production

    sigma_token = log P_pi(forward) - log P_pi(token-reversed)
    sigma_block = log P_pi(forward) - log P_pi(block-reversed)

and writes one JSON per (corpus, order, evaluator).  `aggregate_orders.py` then
runs the causal-vs-noncausal statistics and reports whether the separation is
order invariant.

Why this is the experiment
--------------------------
Sagawa's Sec. VIII names the open problem: the block-level entropy production
mixes (i) genuine causal dependence, (ii) mere temporal ordering, and
(iii) conventions of discourse structure, and "disentangling these
contributions remains a highly nontrivial open problem."  An autoregressive
model cannot separate them because its generation order is forced to equal the
text order.  A masked model can: hold the text fixed and vary pi.

  * separation invariant under pi  -> the arrow is carried by the content
  * separation varies with pi      -> part of it is an artifact of the
                                      generation protocol

Running it (Kyoto ICR supercomputer, PBS Professional, APG queue)
-----------------------------------------------------------------
Compute nodes are assumed to have NO internet.  Fetch the weights on the login
node first (see README), then run with --model pointing at the local directory
and HF_HUB_OFFLINE=1.

    python3 order_intervention.py \
        --model  $HOME/models/LLaDA-8B-Base \
        --texts  $HOME/Paper2026/gpt2/text_sets2/fixed_text_Opus46.json \
        --order  l2r \
        --out    results/Opus46__l2r.json

Model notes
-----------
Any masked model exposing logits over the vocabulary at masked positions works.
Known mask token IDs: LLaDA-8B 126336, Dream-v0 151666.  The script tries
tokenizer.mask_token_id first and falls back to --mask-token-id.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aoar_core import sigma_for_text  # noqa: E402


class HFMaskedProvider:
    """Conditional provider backed by a Hugging Face masked model."""

    def __init__(self, model_dir, mask_token_id=None, dtype="bfloat16",
                 device=None, max_batch=64):
        import torch
        from transformers import AutoModel, AutoTokenizer

        self.torch = torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.max_batch = max_batch

        from transformers import AutoConfig

        self.tok = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
        td = {"bfloat16": torch.bfloat16, "float16": torch.float16,
              "float32": torch.float32}[dtype]

        # LLaDA is OLMo-derived and passes `device=config.init_device` to every
        # nn.Linear, which overrides any torch.device() context.  Left at its
        # default that means ~8e9 parameters are allocated on CPU and filled by
        # kaiming_uniform_ before from_pretrained overwrites them with the real
        # checkpoint: minutes of wasted work and up to 32 GB of host memory.
        # Building on the meta device and materialising straight from the
        # checkpoint avoids both.  Fall back if the config has no such field or
        # the path is unsupported.
        cfg = AutoConfig.from_pretrained(model_dir, trust_remote_code=True)
        model = None
        if hasattr(cfg, "init_device"):
            try:
                cfg.init_device = "meta"
                model = AutoModel.from_pretrained(
                    model_dir, config=cfg, trust_remote_code=True,
                    torch_dtype=td, low_cpu_mem_usage=True)
                print("# model built on meta and materialised from the checkpoint",
                      flush=True)
            except Exception as e:
                print(f"# meta-init path failed ({type(e).__name__}: {e}); "
                      f"falling back to the default load", flush=True)
                model = None
        if model is None:
            model = AutoModel.from_pretrained(
                model_dir, trust_remote_code=True, torch_dtype=td)
        self.model = model.to(self.device).eval()

        mid = mask_token_id
        if mid is None:
            mid = getattr(self.tok, "mask_token_id", None)
        if mid is None:
            raise SystemExit(
                "could not determine the mask token id; pass --mask-token-id "
                "(LLaDA-8B: 126336, Dream-v0: 151666)")
        self.mask_id = int(mid)

    # -- tokenisation -------------------------------------------------
    def encode(self, text):
        return self.tok(text, add_special_tokens=False)["input_ids"]

    def decode_one(self, tid):
        return self.tok.decode([int(tid)])

    # -- the one function the whole protocol needs ---------------------
    def batch_logprob_at(self, rows, positions, targets):
        """log p(target | row) at one position per row, gathered on device.

        Never materialises a (batch, length, vocab) tensor: the logits are
        sliced to the one position per row first, so peak memory is
        batch x vocab instead of batch x length x vocab.  With a 126k
        vocabulary that is the difference between fitting a 24 GB card and
        not.
        """
        torch = self.torch
        out = np.empty(len(rows), dtype=np.float64)
        for a in range(0, len(rows), self.max_batch):
            b = slice(a, min(a + self.max_batch, len(rows)))
            x = torch.tensor(rows[b], dtype=torch.long, device=self.device)
            pos = torch.tensor(positions[b], dtype=torch.long, device=self.device)
            tgt = torch.tensor(targets[b], dtype=torch.long, device=self.device)
            with torch.no_grad():
                o = self.model(x)
                logits = o.logits if hasattr(o, "logits") else o[0]
                # one row of logits per example, then log_softmax over vocab
                sel = logits[torch.arange(len(pos), device=self.device), pos]
                lp = torch.log_softmax(sel.float(), dim=-1)
                val = lp.gather(1, tgt.unsqueeze(1)).squeeze(1)
            out[b] = val.double().cpu().numpy()
        return out

    def batch_logprobs(self, rows):
        """Full (batch, length, vocab) log-probabilities.

        Only needed by the confidence order, which must compare positions.
        """
        torch = self.torch
        out = []
        for a in range(0, len(rows), self.max_batch):
            chunk = rows[a:a + self.max_batch]
            x = torch.tensor(chunk, dtype=torch.long, device=self.device)
            with torch.no_grad():
                o = self.model(x)
                logits = o.logits if hasattr(o, "logits") else o[0]
                lp = torch.log_softmax(logits.float(), dim=-1)
            out.append(lp.cpu().numpy().astype(np.float64))
        return np.concatenate(out, axis=0)


def load_texts(path):
    d = json.load(open(path))
    if "causal_texts" in d:
        return {"causal": d["causal_texts"], "noncausal": d["noncausal_texts"]}
    raise SystemExit(f"unexpected text JSON schema in {path}: keys={list(d)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="local model directory")
    ap.add_argument("--texts", required=True, nargs="+",
                    help="one or more fixed-text corpus JSONs")
    ap.add_argument("--order", required=True,
                    help="comma separated: l2r,r2l,random:1,confidence")
    ap.add_argument("--out", help="output JSON (single corpus x single order)")
    ap.add_argument("--outdir", help="output directory; one JSON per "
                                    "(corpus, order). Use this for a grid.")
    ap.add_argument("--mask-token-id", type=int, default=None)
    ap.add_argument("--dtype", default="bfloat16",
                    choices=["bfloat16", "float16", "float32"])
    ap.add_argument("--max-batch", type=int, default=64)
    ap.add_argument("--order-follows-text", action="store_true",
                    help="diagnostic: mirror the order with the text "
                         "(closer to Bayesian retrodiction) instead of "
                         "keeping it fixed in position space")
    ap.add_argument("--limit", type=int, default=0,
                    help="debug: only this many texts per category")
    args = ap.parse_args()

    orders = [o.strip() for o in args.order.split(",") if o.strip()]
    if not args.out and not args.outdir:
        raise SystemExit("pass --out (single run) or --outdir (grid)")
    if args.out and (len(orders) > 1 or len(args.texts) > 1):
        raise SystemExit("--out is for one corpus and one order; use --outdir")
    if args.outdir:
        os.makedirs(args.outdir, exist_ok=True)
    else:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".",
                    exist_ok=True)

    t0 = time.time()
    # The model is loaded ONCE and reused across the whole grid.  With ~15 GB of
    # weights on Lustre and only minutes of compute per (corpus, order), loading
    # per task would cost more than the computation itself -- and under GPU
    # contention one allocation beats N queue waits.
    prov = HFMaskedProvider(args.model, args.mask_token_id, args.dtype,
                            max_batch=args.max_batch)
    print(f"# model={args.model}  mask_id={prov.mask_id}  device={prov.device}",
          flush=True)
    print(f"# grid: {len(args.texts)} corpora x {len(orders)} orders "
          f"= {len(args.texts)*len(orders)} tasks  "
          f"[model load {time.time()-t0:.1f}s]", flush=True)

    # Tokenise each corpus once; the token IDs do not depend on the order.
    corpora = []
    for path in args.texts:
        cats = load_texts(path)
        enc = {}
        for cat, texts in cats.items():
            if args.limit:
                texts = texts[: args.limit]
            enc[cat] = [(i, t, prov.encode(t)) for i, t in enumerate(texts)]
        corpora.append((path, enc))

    written = []
    for path, enc in corpora:
        corpus = os.path.basename(path)
        for order_spec in orders:
            t1 = time.time()
            records = []
            for cat, items in enc.items():
                for i, text, ids in items:
                    if len(ids) < 2:
                        continue
                    rec = sigma_for_text(
                        ids, order_spec, prov, prov.decode_one,
                        order_follows_text=args.order_follows_text,
                        chunk=args.max_batch)
                    rec.update({"category": cat, "index": i, "text": text})
                    records.append(rec)
            meta = {
                "model": args.model, "mask_token_id": prov.mask_id,
                "texts": path, "corpus": corpus, "order": order_spec,
                "order_follows_text": bool(args.order_follows_text),
                "dtype": args.dtype, "n_records": len(records),
                "elapsed_sec": time.time() - t1,
            }
            if args.outdir:
                tag = (corpus.replace(".json", "") + "__"
                       + order_spec.replace(":", "-")
                       + ("__follow" if args.order_follows_text else ""))
                out = os.path.join(args.outdir, tag + ".json")
            else:
                out = args.out
            with open(out, "w") as f:
                json.dump({"meta": meta, "records": records}, f, indent=1)
            written.append(out)

            med = {c: np.median([r["sigma_block_per_T"] for r in records
                                 if r["category"] == c] or [np.nan])
                   for c in ("causal", "noncausal")}
            print(f"# {corpus:<28} {order_spec:<12} n={len(records):>4}  "
                  f"median sigma_block/T  C={med['causal']:+.5f} "
                  f"N={med['noncausal']:+.5f}  "
                  f"[{time.time()-t1:.0f}s]  -> {os.path.basename(out)}",
                  flush=True)

    print(f"# {len(written)} files written in {time.time()-t0:.1f}s total")


if __name__ == "__main__":
    main()
