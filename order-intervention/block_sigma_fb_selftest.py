#!/usr/bin/env python3
"""Self-test for block_sigma_fb.py, on a toy model with no network.

Four things are checked, each of which the real runs depend on:

  1. COMPATIBLE MODEL -> NO RANK.  When the conditionals come from a joint,
     f(p) = 0 for every arrangement p -- in exact arithmetic.  In floating
     point they differ by ~1e-16, so the runner must treat them as tied and
     report the midrank as exactly 0.50 rather than ranking rounding noise.
     This is the whole reason the instrument says something: a rank exists
     only because the model is incompatible.

  2. IDENTICAL BLOCKS -> NO RANK EITHER.  A text whose sentences are the same
     string has arrangements that are literally the same token sequence.
     Those must stay tied, whatever the model.

  3. INCOMPATIBLE MODEL -> A RANK, AND A CALIBRATED NULL.  Off the compatible
     manifold the n! values differ, so the written order has a position among
     them.  With texts in which no arrangement is privileged, that position
     must be uniform: the mean midrank over many texts has to sit at 0.50.  A
     biased null would manufacture an effect.

  4. THE ARITHMETIC, AND THE MISSING SYMMETRY.  percentile_written and
     z_written must agree with a direct recomputation; and f(p o rev) must
     NOT equal -f(p), since that antisymmetry is what the PLL block
     instrument had and this one does not (its null comes from
     exchangeability instead).

    python3 -I block_sigma_fb_selftest.py
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from block_sigma_fb import run_one_text  # noqa: E402

L, V = 6, 3            # six positions; ids 0,1 are words and 2 is a period
MASK = V               # the mask id is 3
PERIOD = 2
rng0 = np.random.default_rng(0)
states = np.array([[(s // V ** k) % V for k in range(L)] for s in range(V ** L)])
w = rng0.random(V ** L) ** 2
JOINT = w / w.sum()


class Oracle:
    """A perfectly consistent model: the exact conditionals of JOINT."""
    mask_id = MASK

    def encode(self, text):
        return [int(c) for c in text.split(",")]

    def decode_one(self, tid):
        return "." if int(tid) == PERIOD else "w"

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


class Inconsistent(Oracle):
    """The same conditionals, nudged off the compatible manifold."""

    def __init__(self, eps, seed):
        self.eps = eps
        self.r = np.random.default_rng(seed)
        self.cache = {}

    def batch_logprobs(self, rows):
        out = super().batch_logprobs(rows)
        for i, row in enumerate(rows):
            for k in range(L):
                key = (tuple(row), k)
                if key not in self.cache:
                    self.cache[key] = self.r.normal(0, self.eps, V)
                out[i, k] = out[i, k] + self.cache[key]
                out[i, k] -= np.log(np.exp(out[i, k]).sum())
        return out


def text_of(a, b, c):
    """Three blocks of two tokens: word, period, word, period, word, period."""
    return ",".join(str(v) for v in (a, PERIOD, b, PERIOD, c, PERIOD))


DISTINCT = [(a, b, c) for a in (0, 1) for b in (0, 1) for c in (0, 1)
            if len({a, b, c}) > 1]          # at least two blocks differ
SAME = [(0, 0, 0), (1, 1, 1)]               # all three blocks identical

fails = []


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}"
          + (f"   {detail}" if detail else ""))
    if not cond:
        fails.append(name)


def run(model, abc, seed=1):
    return run_one_text(text_of(*abc), model, 24, np.random.default_rng(seed),
                        64)[0]


def main():
    print("1. compatible model: every arrangement gives f(p) = 0")
    orc = Oracle()
    first = run(orc, DISTINCT[0])
    check("n_blocks == 3", first is not None and first["n_blocks"] == 3,
          "" if first is None else f"blocks={first['n_blocks']}")
    check("3! = 6 arrangements, enumerated exactly",
          first["n_perms"] == 6 and first["exact"])
    worst, pcts, degen = 0.0, [], 0
    for abc in DISTINCT:
        rec = run(orc, abc)
        vals = [d["sigma_fb"] for d in rec["perms"].values()]
        worst = max(worst, max(abs(v) for v in vals))
        pcts.append(rec["percentile_written"])
        degen += int(rec["degenerate"])
    check("all f(p) are zero to machine precision", worst < 1e-12,
          f"max |f| = {worst:.2e}")
    check("every text is flagged degenerate", degen == len(DISTINCT),
          f"{degen} of {len(DISTINCT)}")
    check("and ranks at exactly 0.50",
          all(p == 0.5 for p in pcts),
          f"midranks {min(pcts):.3f}..{max(pcts):.3f}")

    print()
    print("2. identical blocks: the arrangements are the same text")
    m = Inconsistent(0.3, seed=11)
    for abc in SAME:
        rec = run(m, abc)
        vals = np.array([d["sigma_fb"] for d in rec["perms"].values()])
        check(f"blocks {abc}: all 6 values identical",
              float(vals.max() - vals.min()) < 1e-15,
              f"spread {vals.max() - vals.min():.2e}")
        check(f"blocks {abc}: degenerate, midrank 0.50",
              rec["degenerate"] and rec["percentile_written"] == 0.5)

    print()
    print("3. incompatible model: a rank exists, and its null is 0.50")
    pcts, degen = [], 0
    for s, abc in enumerate(DISTINCT * 12):
        rec = run(Inconsistent(0.3, seed=100 + s), abc)
        pcts.append(rec["percentile_written"])
        degen += int(rec["degenerate"])
    pcts = np.array(pcts)
    se = pcts.std(ddof=1) / np.sqrt(len(pcts))
    check("no text with distinct blocks is degenerate", degen == 0,
          f"{degen} of {len(pcts)}")
    check("mean midrank is 0.50 within 3 standard errors",
          abs(pcts.mean() - 0.5) < 3 * se,
          f"mean {pcts.mean():.4f} +/- {se:.4f}  (n={len(pcts)})")

    print()
    print("4. the reported statistics match a direct recomputation")
    rec = run(Inconsistent(0.3, seed=7), DISTINCT[2])
    vals = np.array([d["sigma_fb"] for d in rec["perms"].values()])
    s_id = rec["perms"]["0,1,2"]["sigma_fb"]
    pct = ((vals < s_id).sum() + 0.5 * (vals == s_id).sum()) / len(vals)
    z = s_id / vals.std(ddof=1)
    check("sigma_fb_written is the identity arrangement",
          abs(rec["sigma_fb_written"] - s_id) < 1e-15)
    check("percentile_written recomputes",
          abs(rec["percentile_written"] - pct) < 1e-15,
          f"{rec['percentile_written']:.6f}")
    check("z_written recomputes", abs(rec["z_written"] - z) < 1e-12,
          f"{rec['z_written']:+.4f}")
    f_id = rec["perms"]["0,1,2"]["sigma_fb"]
    f_rev = rec["perms"]["2,1,0"]["sigma_fb"]
    check("f(p o rev) is NOT -f(p): no antisymmetry here",
          abs(f_rev + f_id) > 1e-6,
          f"f(id) = {f_id:+.4f}, f(rev) = {f_rev:+.4f}, "
          f"sum = {f_id + f_rev:+.4f}")

    print()
    if fails:
        print(f"FAILED: {len(fails)} check(s): {', '.join(fails)}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
