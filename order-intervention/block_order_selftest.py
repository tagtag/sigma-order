#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify block_order_pll.py's statistic without weights.

What has to be right
--------------------
1. The permutation set is CLOSED UNDER REVERSAL and contains the identity.
   sigma(pi) reads the score at pi o rev, so a set missing that element would
   raise a KeyError on real data, after the model is loaded and minutes of
   compute are spent.
2. The 24 sigma values sum to zero and come in +/- pairs.  This is the
   antisymmetry that made shuffle_control.py uninformative; here it is
   expected, and if it did NOT hold the permutation bookkeeping would be
   wrong.
3. The RANK of the identity is not forced by that symmetry -- it must be able
   to take any value from 1 to n!.  If the rank were pinned the test would be
   as empty as the shuffle control was.
4. A score that is blind to order puts the identity exactly mid-rank, which is
   the null this test reads against.
5. A score that rewards the authored order puts the identity at the top.

    python3 block_order_selftest.py
"""

import itertools
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FAIL = []


def check(name, ok, detail=""):
    print(f"  [{'ok ' if ok else 'FAIL'}] {name}" + (f"   {detail}" if detail else ""))
    if not ok:
        FAIL.append(name)


def pct(vals, s):
    """Midrank percentile, identical to block_order_pll.py's."""
    import numpy as _np
    v = _np.asarray(vals, dtype=float)
    return (float((v < s).sum()) + 0.5 * float((v == s).sum())) / len(v)


def sigmas(n, score_of_perm, perms):
    return {p: score_of_perm(p) - score_of_perm(tuple(reversed(p))) for p in perms}


def main():
    # import here so a syntax error in the module is reported as such
    from block_order_pll import permutation_set

    print("=" * 74)
    print("block_order_pll.py self-test (no weights needed)")
    print("=" * 74)
    rng = np.random.default_rng(0)

    # ---- 1. the permutation set ------------------------------------
    print("\n1. permutation set")
    for n, want_exact in ((3, True), (4, True), (6, False)):
        perms, exact = permutation_set(n, 24, rng)
        ident = tuple(range(n))
        closed = all(tuple(reversed(p)) in set(perms) for p in perms)
        check(f"n={n}: identity present", ident in perms)
        check(f"n={n}: closed under reversal", closed)
        check(f"n={n}: exact flag correct ({exact})", exact == want_exact,
              f"{len(perms)} perms")
        if n == 4:
            check("n=4: all 24 orders enumerated", len(perms) == 24)

    # ---- 2. antisymmetry -------------------------------------------
    print("\n2. antisymmetry of sigma over the permutation set")
    n = 4
    perms, _ = permutation_set(n, 24, rng)
    sc = {p: float(rng.normal()) for p in perms}
    sig = sigmas(n, lambda p: sc[p], perms)
    v = np.array([sig[p] for p in perms])
    check("values sum to zero", abs(float(v.sum())) < 1e-12,
          f"{float(v.sum()):.3e}")
    check("set closed under negation",
          sorted(np.round(v, 12)) == sorted(np.round(-v, 12)))

    # ---- 3. the rank is NOT pinned by that symmetry ----------------
    print("\n3. rank of the authored order is free to move")
    pcts = []
    for trial in range(400):
        sc = {p: float(rng.normal()) for p in perms}
        sig = sigmas(n, lambda p: sc[p], perms)
        v = np.array([sig[p] for p in perms])
        pcts.append(pct(v, sig[tuple(range(n))]))
    pcts = np.array(pcts)
    check("percentile takes many distinct values under random scores",
          len(set(np.round(pcts, 6))) >= 10,
          f"{len(set(np.round(pcts, 6)))} distinct values, range "
          f"{pcts.min():.4f}..{pcts.max():.4f}")
    check("can reach the top of the range", pcts.max() > 0.95,
          f"max {pcts.max():.4f}")
    check("can reach the bottom of the range", pcts.min() < 0.05,
          f"min {pcts.min():.4f}")
    # under a score unrelated to the authored order the percentile is uniform,
    # so its mean is 0.5: that is the reference the real measurement moves away
    # from, and it is a property of the statistic, not of any model
    check("mean percentile is 0.5 under random scores",
          abs(pcts.mean() - 0.5) < 0.03, f"mean {pcts.mean():.4f}")

    # ---- 4. an order-blind score sits mid-rank ---------------------
    print("\n4. a score that ignores order")
    # depends only on the multiset of tokens, so every permutation scores alike
    sig = sigmas(n, lambda p: 0.0, perms)
    v = np.array([sig[p] for p in perms])
    s_id = sig[tuple(range(n))]
    check("every sigma is exactly zero", bool(np.all(v == 0.0)))
    # A "<=" count would report k/k = 1.00 here, i.e. "the authored order is
    # the most forward-costly arrangement", for a model that cannot tell the
    # arrangements apart at all.  The midrank splits the ties and lands on the
    # true null.
    check("midrank percentile is exactly 0.50 for an order-blind score",
          abs(pct(v, s_id) - 0.5) < 1e-12, f"{pct(v, s_id):.6f}")
    check("an unadjusted <= count would have said 1.00 (why midrank is used)",
          abs(float((v <= s_id).sum()) / len(v) - 1.0) < 1e-12)

    # ---- 5. a score that rewards the authored order -----------------
    print("\n5. a score that rewards the authored order")

    def ordered_score(p):
        # rewards adjacent pairs that appear in ascending authored order, the
        # way a language model rewards sentences that follow their antecedents
        return float(sum(1 for a, b in zip(p, p[1:]) if b == a + 1))

    sig = sigmas(n, ordered_score, perms)
    v = np.array([sig[p] for p in perms])
    s_id = sig[tuple(range(n))]
    check("identity is the strict maximum", s_id > np.sort(v)[-2],
          f"sigma_written={s_id:.3f}, next={np.sort(v)[-2]:.3f}")
    check("midrank percentile is near 1.00", pct(v, s_id) > 0.95,
          f"{pct(v, s_id):.4f}")

    print()
    print("=" * 74)
    if FAIL:
        print(f"{len(FAIL)} CHECK(S) FAILED: {', '.join(FAIL)}")
        sys.exit(1)
    print("ALL CHECKS PASS -- the permutation bookkeeping is right and the")
    print("rank statistic is free to move, so the test is not degenerate the")
    print("way shuffle_control.py was.")
    print("=" * 74)


if __name__ == "__main__":
    main()
