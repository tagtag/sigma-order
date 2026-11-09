#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Self-test for aoar_core.aoar_logprob, runnable WITHOUT any model weights.

The test exploits an exact property: if the conditional provider returns the
TRUE subset-marginal conditionals of some joint pi, then the any-order chain
rule gives the same answer for every unmasking order,

    sum_t log pi( x_{pi(t)} | x_{pi(1..t-1)} )  =  log pi(x)      for ALL pi,

because it is just the chain rule of pi written in a different order.  So
order-independence to machine precision validates the masking bookkeeping, the
order handling, and the indexing in aoar_logprob.

We build pi as a dense pairwise MRF on L=6 sites with alphabet V=4 (4096
states, fully enumerable) and implement an ORACLE provider that returns exact
subset-marginal conditionals by enumeration.  This is exactly the object a
masked diffusion model is trained to approximate: a conditional given a
partially revealed sequence, with the unrevealed positions marginalised out.

A second provider deliberately perturbs those conditionals.  Its log P_pi is
order-DEPENDENT, which shows the test has power rather than passing trivially.

    python3 aoar_selftest.py
"""

import itertools
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aoar_core import aoar_logprob, make_order  # noqa: E402

L, V = 6, 4
MASK = V
SEED = 0


def build_truth(rng, coupling=1.0):
    h = rng.normal(0.0, 0.5, size=(L, V))
    J = np.zeros((L, L, V, V))
    for k, l in itertools.combinations(range(L), 2):
        M = rng.normal(0.0, coupling / (1.0 + (l - k)), size=(V, V))
        J[k, l] = M
        J[l, k] = M.T
    return h, J


def joint(h, J):
    states = np.array(list(itertools.product(range(V), repeat=L)), dtype=np.int64)
    e = np.zeros(len(states))
    for k in range(L):
        e += h[k, states[:, k]]
    for k, l in itertools.combinations(range(L), 2):
        e += J[k, l, states[:, k], states[:, l]]
    e -= e.max()
    p = np.exp(e)
    return states, p / p.sum()


class OracleProvider:
    """Exact subset-marginal conditionals of the enumerated joint."""

    mask_id = MASK

    def __init__(self, states, pi):
        self.states = states
        self.pi = pi

    def batch_logprobs(self, rows):
        out = np.full((len(rows), L, V), -np.inf)
        for i, row in enumerate(rows):
            sel = np.ones(len(self.states), dtype=bool)
            for p, t in enumerate(row):
                if t != MASK:
                    sel &= self.states[:, p] == t
            w = self.pi[sel]
            st = self.states[sel]
            tot = w.sum()
            for k in range(L):
                acc = np.zeros(V)
                for v in range(V):
                    acc[v] = w[st[:, k] == v].sum()
                acc = np.maximum(acc / tot, 1e-300)
                out[i, k] = np.log(acc)
        return out


class PerturbedProvider(OracleProvider):
    """Oracle conditionals knocked off the compatible manifold."""

    def __init__(self, states, pi, eps, seed=1):
        super().__init__(states, pi)
        self.eps = eps
        self.rng = np.random.default_rng(seed)
        self._cache = {}

    def batch_logprobs(self, rows):
        out = super().batch_logprobs(rows)
        for i, row in enumerate(rows):
            # deterministic per-(row, site) perturbation
            for k in range(L):
                key = (tuple(row), k)
                if key not in self._cache:
                    self._cache[key] = np.random.default_rng(
                        abs(hash(key)) % (2**32)).normal(0, self.eps, size=V)
                z = out[i, k] + self._cache[key]
                z -= z.max()
                e = np.exp(z)
                out[i, k] = np.log(np.maximum(e / e.sum(), 1e-300))
        return out


def main():
    rng = np.random.default_rng(SEED)
    h, J = build_truth(rng)
    states, pi = joint(h, J)
    index = {tuple(s): i for i, s in enumerate(states)}

    orders = ["l2r", "r2l"] + [f"random:{s}" for s in range(1, 6)]
    test_x = [tuple(states[rng.choice(len(states), p=pi)]) for _ in range(5)]

    print(f"# L={L} V={V} states={V**L}")
    print(f"# joint entropy = {-np.sum(pi*np.log(pi)):.4f} nats\n")

    # ---------- 1. oracle: must be order independent -----------------
    oracle = OracleProvider(states, pi)
    print("=" * 94)
    print("1) ORACLE provider: log P_pi(x) must equal log pi(x) for EVERY order")
    print("=" * 94)
    print(f"{'x':<22}{'log pi(x)':>13}" + "".join(f"{o:>13}" for o in orders[:4]))
    worst = 0.0
    for x in test_x:
        target = float(np.log(pi[index[x]]))
        vals = []
        for o in orders:
            order = make_order(o, L)
            vals.append(aoar_logprob(list(x), order, oracle))
        worst = max(worst, max(abs(v - target) for v in vals))
        print(f"{str(x):<22}{target:>13.8f}"
              + "".join(f"{v:>13.8f}" for v in vals[:4]))
    print(f"\n  max |log P_pi(x) - log pi(x)| over "
          f"{len(test_x)} texts x {len(orders)} orders = {worst:.3e}")
    ok1 = worst < 1e-10
    print(f"  -> {'PASS' if ok1 else 'FAIL'} (threshold 1e-10)")

    # ---------- 2. perturbed: must be order dependent ----------------
    print()
    print("=" * 94)
    print("2) PERTURBED provider: log P_pi(x) must now DEPEND on the order")
    print("   (otherwise the test above would pass vacuously)")
    print("=" * 94)
    print(f"{'eps':>8}{'mean spread over orders':>28}{'max spread':>14}")
    spreads_ok = True
    for eps in (0.01, 0.1, 0.5):
        pert = PerturbedProvider(states, pi, eps)
        sp = []
        for x in test_x:
            vals = [aoar_logprob(list(x), make_order(o, L), pert) for o in orders]
            sp.append(max(vals) - min(vals))
        print(f"{eps:>8.2f}{np.mean(sp):>28.6f}{np.max(sp):>14.6f}")
        if np.mean(sp) <= 1e-8:
            spreads_ok = False
    ok2 = spreads_ok
    print(f"  -> {'PASS' if ok2 else 'FAIL'} (spread must be nonzero)")

    # ---------- 3. normalisation of the per-order joint ---------------
    print()
    print("=" * 94)
    print("3) For a FIXED order, P_pi must be a normalised distribution: "
          "sum_x P_pi(x) = 1")
    print("=" * 94)
    for o in ("l2r", "r2l", "random:3"):
        order = make_order(o, L)
        tot = 0.0
        for s in states:
            tot += np.exp(aoar_logprob(list(s), order, oracle))
        print(f"  order={o:<12} sum_x P_pi(x) = {tot:.12f}   "
              f"|1 - sum| = {abs(1-tot):.2e}")
    print("  (oracle is consistent, so each order reproduces pi exactly)")

    print()
    print("ALL TESTS PASS" if (ok1 and ok2) else "TESTS FAILED")
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    sys.exit(main())
