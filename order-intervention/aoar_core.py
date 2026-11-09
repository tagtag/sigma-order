#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Any-order autoregressive (AO-AR) log-likelihood for masked generative models,
and the sequence reversals used by Sagawa's fixed-text entropy-production
protocol.

Background
----------
Sagawa (PRX Intelligence 1, 023013 (2026); arXiv:2604.07867) defines, for a
fixed text, the stochastic entropy production under protocol reversal

    sigma = log P(forward token sequence) - log P(reversed sequence)

with BOTH terms evaluated by the SAME model.  For an autoregressive model
log P(x) is given by the chain rule in left-to-right order, so the generation
order is forced to coincide with the text order.

For a masked (any-order) generative model the two decouple.  Given an
unmasking order pi (a permutation of positions), the model defines a proper
normalised joint by the any-order chain rule

    log P_pi(x) = sum_{t=1}^{L} log p_theta( x_{pi(t)} | x_{pi(1..t-1)}, rest masked )

At step t the positions pi(1..t-1) hold their true tokens, every other position
(including pi(t) itself) holds [MASK], and we read the model's distribution at
position pi(t).

Two consequences matter here:

  * For each FIXED pi, a masked diffusion model is an autoregressive model in
    Sagawa's class: the partially filled sequence is a deterministic internal
    state and p_theta is an explicit emission kernel.  His framework therefore
    applies verbatim, with sigma_pi exactly computable.  What is new is that pi
    is a free parameter -- an AR model has pi = identity forced on it.
  * The order-averaged object log E_pi[P_pi(x)] is NOT a per-order joint; the
    usual masked-diffusion training objective bounds it from below.  We stay
    with fixed pi so that every quantity is a genuine log-probability.

Order vs reversal -- do not conflate
------------------------------------
  * REVERSAL decides WHICH sequence is scored (forward / token-reversed /
    block-reversed).  This is Sagawa's protocol reversal.
  * ORDER decides HOW the log-probability of that sequence is computed.

The faithful transplant keeps pi fixed in POSITION space and reverses the text,
mirroring the AR case where the generation order stays left-to-right while the
text is reversed.  `order_follows_text=True` reverses the order along with the
text instead; that variant is closer in spirit to Bayesian retrodiction and is
provided as a diagnostic, not as the default.

Reversal conventions follow the reference implementation
(gpt2/text_sets/gpt2_input_text.py in github.com/taksagawa/Paper2026):
  * token reversal: reverse the whole token-ID sequence;
  * block reversal: split at tokens whose decoded text ends with sentence-final
    punctuation (. ! ?), reverse the BLOCK order, preserve intra-block order.
No BOS is prepended: that is a GPT-2 specific detail with no analogue for a
masked model, where every position is scored from a masked context.
"""

from __future__ import annotations

import numpy as np

SENT_END = (".", "!", "?")


# ----------------------------------------------------------------------
# Reversals
# ----------------------------------------------------------------------
def split_into_blocks(token_ids, decode_one):
    """Split token IDs into sentence blocks.

    `decode_one(tid) -> str` decodes a single token.  A block ends at a token
    whose decoded text, right-stripped, ends with '.', '!' or '?'.
    """
    blocks, cur = [], []
    for tid in token_ids:
        cur.append(tid)
        piece = decode_one(tid).rstrip()
        if piece.endswith(SENT_END):
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    return blocks


def token_reverse(token_ids):
    return list(reversed(list(token_ids)))


def block_reverse(token_ids, decode_one):
    blocks = split_into_blocks(token_ids, decode_one)
    out = []
    for b in reversed(blocks):
        out.extend(b)
    return out, len(blocks)


# ----------------------------------------------------------------------
# Unmasking orders
# ----------------------------------------------------------------------
def make_order(spec, L, provider=None, seq_ids=None):
    """Return a permutation of range(L).

    spec:
      'l2r'            identity (left to right) -- the AR-equivalent control
      'r2l'            right to left
      'random:<seed>'  a fixed random permutation
      'confidence'     greedy: at each step reveal the masked position where
                       the model is currently most confident about the TRUE
                       token (requires provider and seq_ids); this is the order
                       a confidence-based sampler would actually follow
    """
    if spec == "l2r":
        return list(range(L))
    if spec == "r2l":
        return list(range(L - 1, -1, -1))
    if spec.startswith("random:"):
        rng = np.random.default_rng(int(spec.split(":", 1)[1]))
        return list(rng.permutation(L))
    if spec == "confidence":
        if provider is None or seq_ids is None:
            raise ValueError("confidence order needs provider and seq_ids")
        return _confidence_order(provider, seq_ids, L)
    raise ValueError(f"unknown order spec: {spec}")


def _confidence_order(provider, seq_ids, L):
    revealed, order = set(), []
    for _ in range(L):
        row = [provider.mask_id] * L
        for p in revealed:
            row[p] = seq_ids[p]
        lp = provider.batch_logprobs([row])[0]          # (L, V)
        best_pos, best_val = None, -np.inf
        for p in range(L):
            if p in revealed:
                continue
            v = lp[p, seq_ids[p]]
            if v > best_val:
                best_pos, best_val = p, v
        order.append(best_pos)
        revealed.add(best_pos)
    return order


# ----------------------------------------------------------------------
# AO-AR log-likelihood
# ----------------------------------------------------------------------
def aoar_logprob(seq_ids, order, provider, chunk=64, return_per_step=False):
    """log P_pi(seq_ids) under unmasking order `order`.

    Builds the L partially-masked inputs, scores them in batches, and sums the
    log-probability of the true token at the position revealed at each step.
    Exactly L kernel evaluations, independent of the vocabulary size.
    """
    seq_ids = list(seq_ids)
    L = len(seq_ids)
    if sorted(order) != list(range(L)):
        raise ValueError("order must be a permutation of range(len(seq_ids))")

    rows = []
    for t in range(L):
        row = [provider.mask_id] * L
        for s in range(t):
            pos = order[s]
            row[pos] = seq_ids[pos]
        rows.append(row)

    per_step = np.empty(L, dtype=np.float64)
    positions = [order[t] for t in range(L)]
    targets = [seq_ids[p] for p in positions]

    # Only one number per row is ever used: the log-probability of the true
    # token at the position revealed at that step.  A provider that can gather
    # it on the device avoids materialising a (batch, length, vocab) tensor,
    # which for a 126k vocabulary is gigabytes per batch and is what decides
    # whether the model fits on a 24 GB card.  Providers without the targeted
    # method (the self-test oracle) fall back to the full array.
    targeted = getattr(provider, "batch_logprob_at", None)
    for a in range(0, L, chunk):
        sl = slice(a, min(a + chunk, L))
        if targeted is not None:
            per_step[sl] = targeted(rows[sl], positions[sl], targets[sl])
        else:
            lp = provider.batch_logprobs(rows[sl])           # (b, L, V)
            for i in range(lp.shape[0]):
                t = a + i
                per_step[t] = lp[i, positions[t], targets[t]]

    total = float(per_step.sum())
    return (total, per_step) if return_per_step else total


# ----------------------------------------------------------------------
# One text -> entropy production under one order
# ----------------------------------------------------------------------
def sigma_for_text(token_ids, order_spec, provider, decode_one,
                   order_follows_text=False, chunk=64):
    """Return sigma_token and sigma_block for one text under one order.

    sigma_* = log P_pi(forward) - log P_pi(reversed)
    """
    L = len(token_ids)
    order = make_order(order_spec, L, provider, token_ids)

    ll_fwd = aoar_logprob(token_ids, order, provider, chunk)

    tok_rev = token_reverse(token_ids)
    blk_rev, n_blocks = block_reverse(token_ids, decode_one)

    def order_for(_seq):
        # Protocol reversal: the order stays fixed in position space.
        # order_follows_text=True instead mirrors the order with the text.
        return list(reversed(order)) if order_follows_text else order

    ll_tok_rev = aoar_logprob(tok_rev, order_for(tok_rev), provider, chunk)
    ll_blk_rev = aoar_logprob(blk_rev, order_for(blk_rev), provider, chunk)

    return {
        "T": L,
        "n_blocks": n_blocks,
        "order_spec": order_spec,
        "order_follows_text": bool(order_follows_text),
        "order": [int(p) for p in order],
        "ll_fwd": ll_fwd,
        "ll_token_rev": ll_tok_rev,
        "ll_block_rev": ll_blk_rev,
        "sigma_token": ll_fwd - ll_tok_rev,
        "sigma_block": ll_fwd - ll_blk_rev,
        "sigma_token_per_T": (ll_fwd - ll_tok_rev) / L,
        "sigma_block_per_T": (ll_fwd - ll_blk_rev) / L,
    }
