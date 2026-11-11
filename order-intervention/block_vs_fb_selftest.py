#!/usr/bin/env python3
"""Block-reversal sigma is not the forward/backward sigma.  A self-test.

Two quantities in this repository are both written as a difference divided by
the token count, and they are easy to confuse:

  forward/backward   sigma_fb(x)    = [ log P_l2r(x) - log P_r2l(x) ] / L
                     the SAME text, assembled in two directions

  block reversal     sigma_blk(x)   = [ log P_pi(x) - log P_pi(x~) ] / L
                     TWO DIFFERENT texts (x and its block reversal x~),
                     assembled in ONE direction pi

They are not the same, and the difference is not a matter of degree:

  * sigma_fb vanishes IDENTICALLY for any model whose conditionals come from
    a joint, because both terms collapse to log P(x).
  * sigma_blk does NOT vanish for such a model, because x and x~ are
    different sequences with different probabilities.

That is why the block instrument yields a non-zero reading on gpt2 (whose
score IS an exact log-likelihood) while the forward/backward instrument
cannot: if the two were equivalent, the autoregressive half of the paper
would be measuring exactly zero.

This test builds an exactly consistent model -- the true conditionals of a
known joint -- and checks both statements.

    python3 -I block_vs_fb_selftest.py

No model, no network; a few hundred milliseconds.
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aoar_core import aoar_logprob, make_order  # noqa: E402

L, V = 6, 2            # six positions, two symbols: 64 sequences
MASK = V
BLOCK = 2              # two tokens per "sentence" -> three blocks
rng = np.random.default_rng(0)
states = np.array([[(s >> k) & 1 for k in range(L)] for s in range(V ** L)])
w = rng.random(V ** L) ** 2
JOINT = w / w.sum()


class Oracle:
    """A perfectly consistent model: the exact conditionals of JOINT."""
    mask_id = MASK

    def batch_logprobs(self, rows):
        out = np.full((len(rows), L, V), -np.inf)
        for i, row in enumerate(rows):
            sel = np.ones(len(states), bool)
            for p, t in enumerate(row):
                if t != MASK:
                    sel &= states[:, p] == t
            ww, st = JOINT[sel], states[sel]
            for k in range(L):
                acc = np.array([ww[st[:, k] == v].sum() for v in range(V)])
                out[i, k] = np.log(np.maximum(acc / ww.sum(), 1e-300))
        return out


def blocks_of(seq):
    return [list(seq[i:i + BLOCK]) for i in range(0, len(seq), BLOCK)]


def block_reverse(seq):
    """Reverse the ORDER of the blocks; each block stays forward inside."""
    return [t for b in reversed(blocks_of(seq)) for t in b]


def main():
    orc = Oracle()
    l2r, r2l = make_order("l2r", L), make_order("r2l", L)

    print(f"L = {L}, {L // BLOCK} blocks of {BLOCK} tokens, "
          f"{V ** L} sequences; model = exact conditionals of a known joint")
    print()
    print("sigma_fb  = [ log P_l2r(x)  - log P_r2l(x) ] / L     same text, "
          "two directions")
    print("sigma_blk = [ log P_l2r(x)  - log P_l2r(x~) ] / L    two texts, "
          "one direction")
    print("=" * 78)
    print(f"{'x':>10}{'x~':>10}{'log P(x)':>12}{'log P(x~)':>12}"
          f"{'sigma_fb':>13}{'sigma_blk':>12}")
    print("-" * 78)

    fb, blk = [], []
    for s in states[:8]:
        x = list(s)
        xt = block_reverse(x)
        lp_f = aoar_logprob(x, l2r, orc)
        lp_b = aoar_logprob(x, r2l, orc)
        lp_t = aoar_logprob(xt, l2r, orc)
        s_fb = (lp_f - lp_b) / L
        s_blk = (lp_f - lp_t) / L
        fb.append(s_fb)
        blk.append(s_blk)
        print(f"{''.join(map(str, x)):>10}{''.join(map(str, xt)):>10}"
              f"{lp_f:>12.6f}{lp_t:>12.6f}{s_fb:>13.2e}{s_blk:>+12.4f}")

    # the full check, over every sequence
    fb_all, blk_all = [], []
    for s in states:
        x = list(s)
        lp_f = aoar_logprob(x, l2r, orc)
        fb_all.append((lp_f - aoar_logprob(x, r2l, orc)) / L)
        blk_all.append((lp_f - aoar_logprob(block_reverse(x), l2r, orc)) / L)
    fb_all, blk_all = np.array(fb_all), np.array(blk_all)

    print("=" * 78)
    print(f"over all {len(states)} sequences:")
    print(f"  max |sigma_fb|  = {np.abs(fb_all).max():.3e}   "
          f"<- zero to machine precision, as the identity requires")
    print(f"  max |sigma_blk| = {np.abs(blk_all).max():.4f}        "
          f"<- not zero, and not close to it")
    print(f"  rms  sigma_blk  = {np.sqrt((blk_all ** 2).mean()):.4f}")

    ok = np.abs(fb_all).max() < 1e-12 and np.abs(blk_all).max() > 1e-3
    print()
    if ok:
        print("PASS  the two sigmas are different quantities.  block reversal")
        print("      changes WHICH text is scored; it does not reverse the")
        print("      direction of assembly, and it does not reduce to l2r-r2l.")
    else:
        print("FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
