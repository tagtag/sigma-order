#!/usr/bin/env python3
"""The three rank correlations of the route control, and their exact p-values.

Appendix A quotes three Spearman correlations over the capacity sweep --
sigma_EP against width d, <|sigma|> against d, and the two against each
other -- together with the statement that none of them can be significant,
because with n widths the smallest two-sided p the exact rank null can
return is 2/n!.

This script recomputes all of it from bayes_route_control.json by
enumerating the n! permutations, so no SciPy approximation is involved and
every p is a count over the exact null.  It exists because 0.083 looks
surprisingly small next to the 0.017 floor; the enumeration shows it is the
second-smallest value the null can produce at n = 5 (10 of 120
permutations), not an error.

    python3 -I check_rank_pvalues.py
    python3 -I check_rank_pvalues.py --json bayes_route_control.json

Exit status 0 if every recomputed value matches the one the paper prints,
1 otherwise.  No model, no network.
"""

import argparse
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON = os.path.join(HERE, "bayes_route_control.json")

# What main.tex prints, via the macros make_tables.py writes.
EXPECTED = {
    "sigma_EP vs d":        (+0.90, 0.083),   # CtrlRhoEP,  CtrlPEP
    "<|sigma|> vs d":       (+0.10, 0.950),   # CtrlRhoSig, CtrlPSig
    "sigma_EP vs <|sigma|>": (+0.30, 0.683),  # CtrlRhoXS,  CtrlPXS
}
EXPECTED_FLOOR = 0.017                        # CtrlPFloor


def ranks(xs):
    """Midranks, so ties are handled the way a rank correlation must."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        shared = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = shared
        i = j + 1
    return out


def pearson(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = sum((x - ma) ** 2 for x in a) ** 0.5
    db = sum((y - mb) ** 2 for y in b) ** 0.5
    return num / (da * db) if da and db else 0.0


def spearman(a, b):
    return pearson(ranks(a), ranks(b))


def exact_two_sided_p(a, b):
    """Count permutations of b whose |rho| reaches the observed |rho|.

    The null is that the pairing carries no information, so every one of the
    n! pairings is equally likely.  n = 5 here, so 120 of them.
    """
    ra, rb = ranks(a), ranks(b)
    obs = abs(pearson(ra, rb))
    total = hits = 0
    for perm in itertools.permutations(rb):
        total += 1
        if abs(pearson(ra, list(perm))) >= obs - 1e-12:
            hits += 1
    return hits / total, hits, total


def null_floor(n):
    """The smallest two-sided p the exact rank null can return at this n."""
    ra = list(range(1, n + 1))
    best = None
    for perm in itertools.permutations(ra):
        p, _, _ = exact_two_sided_p(ra, list(perm))
        best = p if best is None else min(best, p)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=DEFAULT_JSON)
    args = ap.parse_args()

    with open(args.json, encoding="utf-8") as fh:
        doc = json.load(fh)
    rows = doc["rows"]

    d = [r["d"] for r in rows]
    sig_ep = [r["head"]["sigma"] for r in rows]
    sig_abs = [r["sigma_l2r_r2l"]["mean_abs"] for r in rows]
    n = len(rows)

    series = {
        "sigma_EP vs d": (sig_ep, d),
        "<|sigma|> vs d": (sig_abs, d),
        "sigma_EP vs <|sigma|>": (sig_ep, sig_abs),
    }

    print(f"{os.path.basename(args.json)}  n = {n} widths  "
          f"d = {', '.join(str(v) for v in d)}")
    print(f"exact rank null: {n}! = {len(list(itertools.permutations(range(n))))}"
          f" equally likely pairings")
    print("=" * 74)
    print(f"{'pair':<24}{'rho':>8}{'paper':>8}{'p':>10}{'paper':>8}"
          f"{'hits/n!':>12}  verdict")
    print("-" * 74)

    bad = 0
    for name, (a, b) in series.items():
        rho = spearman(a, b)
        p, hits, total = exact_two_sided_p(a, b)
        want_rho, want_p = EXPECTED[name]
        ok = (round(rho, 2) == want_rho) and (round(p, 3) == want_p)
        bad += not ok
        print(f"{name:<24}{rho:>+8.2f}{want_rho:>+8.2f}{p:>10.3f}"
              f"{want_p:>8.3f}{f'{hits}/{total}':>12}  "
              f"{'agree' if ok else 'DIFFER'}")

    floor = null_floor(n)
    ok = round(floor, 3) == EXPECTED_FLOOR
    bad += not ok
    print("-" * 74)
    print(f"{'smallest attainable p':<24}{'':>8}{'':>8}{floor:>10.3f}"
          f"{EXPECTED_FLOOR:>8.3f}{f'2/{len(list(itertools.permutations(range(n))))}':>12}"
          f"  {'agree' if ok else 'DIFFER'}")
    print("=" * 74)

    if bad:
        print(f"FAIL  {bad} value(s) do not match what the paper prints.")
        return 1
    print("PASS  all three rho, all three p, and the null floor reproduce.")
    print()
    print("On 0.083: it is not too small.  At n = 5 the exact null puts 2 of")
    print("120 pairings at |rho| = 1.00 and 8 more at |rho| = 0.90, so the two")
    print("smallest two-sided p it can return are 2/120 = 0.017 and")
    print("10/120 = 0.083.  The observed rho = +0.90 lands on the second of")
    print("them.  It is the closest to significance the sweep could come")
    print("without being a perfect ordering, and it still does not reach 0.05.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
