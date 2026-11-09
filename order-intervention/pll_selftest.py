#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify pll_sigma.py's bookkeeping without downloading any weights.

What has to be right before this goes on a cluster
--------------------------------------------------
1. Each CONTENT position is masked exactly once, and no special token
   ([CLS]/[SEP]) is ever masked or scored.  An off-by-one here would silently
   score the wrong tokens and the whole comparison would be meaningless.
2. The reversals are involutions, so "forward" and "reversed" really are the
   same multiset of tokens in a different arrangement, and nothing is lost or
   duplicated.
3. A model with NO directional preference gives sigma exactly 0.  This is the
   null the real experiment is testing against: if a uniform scorer did not
   give 0, a measured sigma ~ 0 would prove nothing.
4. The causal scorer scores exactly T tokens, each once.

Stubs replace the network: a module returning all-zero logits makes every
token equiprobable, so the scores are analytically -T log V and every
discrepancy is a bookkeeping bug rather than a numerical one.

    python3 pll_selftest.py
"""

import math
import os
import sys

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aoar_core import block_reverse, split_into_blocks, token_reverse  # noqa: E402
from pll_sigma import CausalScorer, MaskedScorer  # noqa: E402

V = 50
MASK = 7
PREFIX = [101]
SUFFIX = [102]
FAIL = []


def check(name, ok, detail=""):
    print(f"  [{'ok ' if ok else 'FAIL'}] {name}" + (f"   {detail}" if detail else ""))
    if not ok:
        FAIL.append(name)


class ZeroLogits(torch.nn.Module):
    """Every token equiprobable; records every row it is shown."""

    def __init__(self):
        super().__init__()
        self.seen = []

    def forward(self, x):
        self.seen.extend(x.tolist())
        return type("O", (), {"logits": torch.zeros(x.shape[0], x.shape[1], V)})()


def make_masked():
    s = MaskedScorer.__new__(MaskedScorer)
    s.model = ZeroLogits()
    s.device = "cpu"
    s.max_batch = 3          # deliberately smaller than T, to exercise chunking
    s.mask_id = MASK
    s.prefix = list(PREFIX)
    s.suffix = list(SUFFIX)
    s.tok = None
    return s


def make_causal():
    s = CausalScorer.__new__(CausalScorer)
    s.model = ZeroLogits()
    s.device = "cpu"
    s.bos = 99
    s.tok = None
    return s


def main():
    print("=" * 74)
    print("pll_sigma.py self-test (no weights needed)")
    print("=" * 74)

    ids = [11, 12, 13, 14, 15, 16, 17]
    T = len(ids)

    # ---- 1. masking bookkeeping -------------------------------------
    print("\n1. masked scorer: which positions get masked")
    s = make_masked()
    total = s.score(ids)
    rows = s.model.seen
    check("one forward row per content token", len(rows) == T,
          f"{len(rows)} rows for T={T}")
    masked_at = []
    for r in rows:
        at = [j for j, v in enumerate(r) if v == MASK]
        masked_at.append(at)
    check("exactly one mask per row", all(len(a) == 1 for a in masked_at))
    flat = sorted(a[0] for a in masked_at)
    want = list(range(len(PREFIX), len(PREFIX) + T))
    check("each content position masked exactly once", flat == want,
          f"{flat} vs {want}")
    specials_intact = all(r[0] == PREFIX[0] and r[-1] == SUFFIX[0] for r in rows)
    check("special tokens never masked", specials_intact)
    unmasked_ok = all(
        [v for j, v in enumerate(r[len(PREFIX):len(PREFIX) + T]) if j != a[0] - len(PREFIX)]
        == [v for j, v in enumerate(ids) if j != a[0] - len(PREFIX)]
        for r, a in zip(rows, masked_at))
    check("all other content tokens left in place", unmasked_ok)

    # ---- 2. analytic value ------------------------------------------
    print("\n2. masked scorer: value under a uniform model")
    want_total = -T * math.log(V)
    # the stub emits float32 logits, so log_softmax over V=50 followed by a sum
    # carries ~1e-6 of rounding.  A bookkeeping error would be off by at least
    # one token's worth, log V = 3.9, so 1e-4 separates the two cleanly.
    TOL = 1e-4
    check("PLL == -T log V", abs(total - want_total) < TOL,
          f"{total:.10f} vs {want_total:.10f}")

    # ---- 3. causal scorer -------------------------------------------
    print("\n3. causal scorer")
    cs = make_causal()
    tc = cs.score(ids)
    check("log P == -T log V", abs(tc - want_total) < TOL,
          f"{tc:.10f} vs {want_total:.10f}")
    check("one row, length T+1 (BOS prepended)",
          len(cs.model.seen) == 1 and len(cs.model.seen[0]) == T + 1)
    check("BOS is first and content follows unchanged",
          cs.model.seen[0] == [cs.bos] + ids)

    # ---- 4. reversals are involutions -------------------------------
    print("\n4. reversals")
    check("token_reverse is an involution",
          token_reverse(token_reverse(ids)) == list(ids))
    check("token_reverse preserves the multiset",
          sorted(token_reverse(ids)) == sorted(ids))

    # a sequence with real sentence punctuation, so blocks are well defined
    vocab = {1: "The", 2: " glass", 3: " fell", 4: ".", 5: " It",
             6: " broke", 7: ".", 8: " She", 9: " swept", 10: "."}
    seq = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    def dec(t):
        return vocab[t]

    blocks = split_into_blocks(seq, dec)
    check("blocks split at sentence enders", len(blocks) == 3,
          f"{[[dec(t) for t in b] for b in blocks]}")
    rb, nb = block_reverse(seq, dec)
    check("block_reverse keeps the multiset", sorted(rb) == sorted(seq))
    check("block_reverse preserves length", len(rb) == len(seq))
    rb2, _ = block_reverse(rb, dec)
    check("block_reverse is an involution", list(rb2) == list(seq),
          f"{[dec(t) for t in rb]} -> {[dec(t) for t in rb2]}")
    check("blocks themselves are intact, only their order changed",
          [sorted(b) for b in split_into_blocks(rb, dec)][::-1]
          == [sorted(b) for b in blocks])

    # ---- 5. the null the experiment tests against -------------------
    print("\n5. sigma under a direction-neutral model")
    s2 = make_masked()
    f = s2.score(seq)
    t_ = s2.score(token_reverse(seq))
    b_ = s2.score(block_reverse(seq, dec)[0])
    check("sigma_token == 0 exactly", abs(f - t_) < 1e-12, f"{f - t_:.3e}")
    check("sigma_block == 0 exactly", abs(f - b_) < 1e-12, f"{f - b_:.3e}")
    cs2 = make_causal()
    f2 = cs2.score(seq)
    b2 = cs2.score(block_reverse(seq, dec)[0])
    check("causal sigma_block == 0 exactly", abs(f2 - b2) < 1e-12,
          f"{f2 - b2:.3e}")

    print()
    print("=" * 74)
    if FAIL:
        print(f"{len(FAIL)} CHECK(S) FAILED: {', '.join(FAIL)}")
        sys.exit(1)
    print("ALL CHECKS PASS -- the bookkeeping is right; only the weights are")
    print("missing, so this is safe to submit to the cluster.")
    print("=" * 74)


if __name__ == "__main__":
    main()
