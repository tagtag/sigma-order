#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kolmogorov cycle affinity of the single-site Glauber dynamics induced by a
masked language model (BERT), with an autoregressive (GPT-2) control.

Background
----------
Iterative masked-token resampling on an MLM defines a Markov chain on token
sequences (Glauber dynamics).  For a transition that changes exactly one site
k, the single-site Glauber rate is

    P(x -> y) = (1/n) * p_k(y_k | x_{-k}),

where p_k(. | x_{-k}) is the MLM conditional obtained by masking site k.

Consider two sites i < j and two candidate tokens at each,
(a, a') at i and (b, b') at j, with the rest of the sentence held fixed.
The four states {a,a'} x {b,b'} form a 4-cycle.  Its Kolmogorov cycle
affinity is

    A = log [ P(a->a'|b) P(b->b'|a') P(a'->a|b') P(b'->b|a) ]
      - log [ P(b->b'|a) P(a->a'|b') P(b'->b|a') P(a'->a|b) ]

The 1/n factors cancel.  Writing the log-odds

    D_i(u) = log p_i(a'|u) - log p_i(a|u)       (site i, with site j = u)
    D_j(v) = log p_j(b'|v) - log p_j(b|v)       (site j, with site i = v)

the affinity collapses to a difference of two couplings:

    C_i = D_i(b') - D_i(b)     # effect of j's value on i's log-odds
    C_j = D_j(a') - D_j(a)     # effect of i's value on j's log-odds
    A   = C_j - C_i

Kolmogorov's criterion: the chain admits a compatible stationary distribution
and satisfies detailed balance w.r.t. it iff A = 0 on every cycle.  For any
model defining a consistent joint pi(x), both C_i and C_j equal the mixed
second difference log[pi(a',b') pi(a,b) / (pi(a,b') pi(a',b))], so A == 0
identically.  A != 0 therefore measures the asymmetry of the learned pairwise
coupling: how much site j moves site i, versus how much site i moves site j.

This is the quantitative closure of the binary "rectangle test" of
arXiv:2605.16378, and is the per-cycle ingredient of the Schnakenberg
decomposition of the entropy production rate, sigma = sum_c A_c J_c.
(The cycle fluxes J_c require the stationary measure and are NOT computed
here; this script reports the affinity spectrum only.)

Controls
--------
  * GPT-2: an autoregressive model defines a consistent joint, so A must be
    0 to floating-point precision.  This validates the estimator and the code.
  * Distant / unrelated site pairs under BERT: coupling ~ 0, so A ~ 0.

Usage
-----
    python3 cycle_affinity.py            # full run, writes results.json
    python3 cycle_affinity.py --quick    # fewer sentences
"""

import argparse
import itertools
import json
import math
import os
import random
import sys

import torch
import torch.nn.functional as F

SEED = 0
MLM_NAME = "bert-base-uncased"
AR_NAME = "gpt2"

# Sentences used to build cycles.  Mixture of general sentences and
# relational "A is B" style sentences (the reversal-curse setting).
SENTENCES = [
    "the doctor finished her shift and drove home in the rain .",
    "the company reported a sharp decline in quarterly revenue .",
    "he opened the window because the room was far too warm .",
    "scientists discovered a new species of frog in the forest .",
    "the old bridge collapsed after the heavy storm last night .",
    "she poured the hot coffee into a ceramic mug carefully .",
    "the government announced a new policy on carbon emissions .",
    "my brother works as an engineer at a small startup .",
    "the cat jumped onto the table and knocked over the glass .",
    "tokyo is the capital city of japan and a major port .",
    "marie curie was the physicist who discovered the element radium .",
    "the chef prepared a simple dinner of rice and grilled fish .",
]


def log_softmax_at(model, tokenizer, ids, pos, device):
    """Return log p(. | context) at a masked position `pos` of `ids`."""
    x = ids.clone()
    x[0, pos] = tokenizer.mask_token_id
    with torch.no_grad():
        logits = model(x.to(device)).logits
    return F.log_softmax(logits[0, pos].float(), dim=-1).cpu()


def mlm_affinity(model, tokenizer, ids, i, j, a, ap, b, bp, device):
    """Cycle affinity for sites (i, j) with token pairs (a, ap), (b, bp)."""
    # site i conditionals, with site j held at b and at bp
    x = ids.clone()
    x[0, j] = b
    lp_i_b = log_softmax_at(model, tokenizer, x, i, device)
    x[0, j] = bp
    lp_i_bp = log_softmax_at(model, tokenizer, x, i, device)

    # site j conditionals, with site i held at a and at ap
    x = ids.clone()
    x[0, i] = a
    lp_j_a = log_softmax_at(model, tokenizer, x, j, device)
    x[0, i] = ap
    lp_j_ap = log_softmax_at(model, tokenizer, x, j, device)

    D_i_b = (lp_i_b[ap] - lp_i_b[a]).item()
    D_i_bp = (lp_i_bp[ap] - lp_i_bp[a]).item()
    D_j_a = (lp_j_a[bp] - lp_j_a[b]).item()
    D_j_ap = (lp_j_ap[bp] - lp_j_ap[b]).item()

    C_i = D_i_bp - D_i_b
    C_j = D_j_ap - D_j_a
    return C_j - C_i, C_i, C_j


def ar_seq_logprob(model, ids, device):
    """Total log p(x) under an autoregressive model."""
    with torch.no_grad():
        logits = model(ids.to(device)).logits.float()
    lp = F.log_softmax(logits[0, :-1], dim=-1).cpu()
    tgt = ids[0, 1:]
    return lp.gather(-1, tgt.unsqueeze(-1)).sum().item()


def ar_affinity(model, ids, i, j, a, ap, b, bp, device):
    """Same cycle affinity for an AR model. Must be ~0 by construction."""
    def lp(ti, tj):
        x = ids.clone()
        x[0, i] = ti
        x[0, j] = tj
        return ar_seq_logprob(model, x, device)

    l_ab, l_apb = lp(a, b), lp(ap, b)
    l_abp, l_apbp = lp(a, bp), lp(ap, bp)
    C_i = (l_apbp - l_abp) - (l_apb - l_ab)
    C_j = (l_apbp - l_apb) - (l_abp - l_ab)
    return C_j - C_i, C_i, C_j


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--quick", action="store_true")
    ap_.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json"))
    args = ap_.parse_args()

    random.seed(SEED)
    torch.manual_seed(SEED)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"# device: {device}", flush=True)

    from transformers import (AutoModelForCausalLM, AutoModelForMaskedLM,
                              AutoTokenizer)

    print(f"# loading {MLM_NAME}", flush=True)
    mtok = AutoTokenizer.from_pretrained(MLM_NAME)
    mlm = AutoModelForMaskedLM.from_pretrained(MLM_NAME).to(device).eval()

    sentences = SENTENCES[:4] if args.quick else SENTENCES

    records = []
    for s in sentences:
        enc = mtok(s, return_tensors="pt")
        ids = enc["input_ids"]
        n = ids.shape[1]
        # content positions only (skip [CLS]/[SEP] and punctuation)
        positions = [
            p for p in range(1, n - 1)
            if mtok.convert_ids_to_tokens([ids[0, p].item()])[0].isalpha()
        ]
        if len(positions) < 2:
            continue

        # candidate token pair at each position: top-2 under masking
        cands = {}
        for p in positions:
            lp = log_softmax_at(mlm, mtok, ids, p, device)
            top = torch.topk(lp, 2).indices.tolist()
            orig = ids[0, p].item()
            alt = top[0] if top[0] != orig else top[1]
            cands[p] = (orig, alt)

        for i, j in itertools.combinations(positions, 2):
            a, apk = cands[i]
            b, bpk = cands[j]
            A, C_i, C_j = mlm_affinity(mlm, mtok, ids, i, j, a, apk, b, bpk, device)
            records.append({
                "sentence": s,
                "i": i, "j": j, "gap": j - i,
                "tok_i": mtok.convert_ids_to_tokens([a, apk]),
                "tok_j": mtok.convert_ids_to_tokens([b, bpk]),
                "C_i": C_i, "C_j": C_j, "A": A,
            })
        print(f"# done: {s[:50]}...  cycles so far: {len(records)}", flush=True)

    del mlm
    if device == "cuda":
        torch.cuda.empty_cache()

    # ---- AR control -------------------------------------------------
    print(f"# loading {AR_NAME} (control)", flush=True)
    gtok = AutoTokenizer.from_pretrained(AR_NAME)
    gpt = AutoModelForCausalLM.from_pretrained(AR_NAME).to(device).eval()

    ctrl = []
    for s in sentences[: (2 if args.quick else 4)]:
        ids = gtok(s, return_tensors="pt")["input_ids"]
        n = ids.shape[1]
        positions = [p for p in range(n) if gtok.decode([ids[0, p].item()]).strip().isalpha()]
        if len(positions) < 2:
            continue
        cands = {}
        for p in positions:
            orig = ids[0, p].item()
            # alternative: a different frequent token
            alt = random.choice([t for t in positions if ids[0, t].item() != orig])
            cands[p] = (orig, ids[0, alt].item())
        for i, j in itertools.combinations(positions, 2):
            a, apk = cands[i]
            b, bpk = cands[j]
            if a == apk or b == bpk:
                continue
            A, C_i, C_j = ar_affinity(gpt, ids, i, j, a, apk, b, bpk, device)
            ctrl.append({"sentence": s, "i": i, "j": j, "C_i": C_i, "C_j": C_j, "A": A})
        print(f"# control done: {s[:50]}...  cycles: {len(ctrl)}", flush=True)

    # ---- report -----------------------------------------------------
    def stats(xs):
        xs = sorted(xs)
        k = len(xs)
        if k == 0:
            return {}
        mean = sum(xs) / k
        var = sum((v - mean) ** 2 for v in xs) / max(k - 1, 1)
        absx = sorted(abs(v) for v in xs)
        return {
            "n": k,
            "mean": mean,
            "sd": math.sqrt(var),
            "median_abs": absx[k // 2],
            "p90_abs": absx[int(0.9 * (k - 1))],
            "max_abs": absx[-1],
        }

    A_mlm = [r["A"] for r in records]
    A_ar = [r["A"] for r in ctrl]

    out = {
        "mlm_model": MLM_NAME,
        "ar_model": AR_NAME,
        "n_sentences": len(sentences),
        "mlm_affinity_stats": stats(A_mlm),
        "ar_affinity_stats": stats(A_ar),
        "mlm_by_gap": {},
        "records": records,
        "control_records": ctrl,
    }
    by_gap = {}
    for r in records:
        by_gap.setdefault(r["gap"], []).append(abs(r["A"]))
    for g in sorted(by_gap):
        v = sorted(by_gap[g])
        out["mlm_by_gap"][str(g)] = {"n": len(v), "median_abs_A": v[len(v) // 2]}

    print()
    print("=" * 62)
    print("BERT (bert-base-uncased) single-site Glauber cycle affinity")
    print("=" * 62)
    for k, v in out["mlm_affinity_stats"].items():
        print(f"  {k:12s} {v:.6g}")
    print()
    print(f"GPT-2 control (consistent joint => A must be ~0)")
    for k, v in out["ar_affinity_stats"].items():
        print(f"  {k:12s} {v:.6g}")
    print()
    print("median |A| by site separation (BERT):")
    for g in sorted(by_gap, key=int):
        v = out["mlm_by_gap"][str(g)]
        print(f"  gap={g:3d}  n={v['n']:4d}  median|A|={v['median_abs_A']:.4f}")

    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
    print(f"\n# wrote {args.out}")


if __name__ == "__main__":
    main()
