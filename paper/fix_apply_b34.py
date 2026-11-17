#!/usr/bin/env python3
"""Batch 34: #253 -- the midrank grid is 1/2n!, not 1/n!.

Equation (midrank) is

    pct = [ #{Delta < Delta_id} + (1/2) #{Delta = Delta_id} ] / n!

and the authored arrangement is always tied with itself, so the half term
always contributes: 2 n! pct = 2a + t, where a is the count strictly below
and t >= 1 the number of tied arrangements.  That is an integer, and it is
odd whenever t is -- which is the ordinary case, t = 1.  So the midrank
lives on a grid of width 1/2n! and not 1/n!, and the smallest non-zero
reading it can return is 1/2n!.  (The degenerate texts, all n! values
tied, have t = n! and sit at exactly 0.50; they are on the grid too, and
the paper already reports them at the null.)

The claim is about one reading.  A median over an even number of texts is a
mean of two values on the grid and need not be on it -- a corpus with
degenerate texts at exactly 0.50 mixed among ordinary ones puts the median
halfway between grid points -- so the components, which are medians, are
quoted in grid units to a tenth of a step rather than rounded to whole
ones.  That rounding is what hid the error: the causal component printed as
"1 to 2 steps" of 1/n! while the authored component, printed unrounded,
read 8.5 and 9.5.

The paper's own generated numbers already show this and the prose did not:
\\AuthoredCompStepsMin is 8.5 and \\AuthoredCompStepsMax is 9.5, which are
17/48 and 19/48 and not multiples of 1/24.  The causal component was printed
as 1 to 2 steps only because make_tables.py rounded it; on the correct grid
it is 2 to 4.  fix_apply_grid.py makes \\GridStep and \\GridK right at the
source, so every macro-driven site follows; this batch fixes the four places
that spell the grid out in prose, and the one place that says how large the
causal component is in steps without a macro.

main.tex:1002 also stops using \\NPerms for the grid denominator.  \\NPerms
is n! and stays 24; the grid denominator is now \\GridK = 48, and the two
are no longer the same number.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b34.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- abstract ---------------------------------------------------------
    ("main.tex",
     "steps of the $1/n!$ grid the\nstatistic lives on",
     "steps of the $1/2n!$ grid the\nstatistic lives on",
     "253 abstract grid"),

    # ---- Section 4.2, the saturation argument -----------------------------
    ("main.tex",
     "Because the midrank is confined to a grid of width $1/n!$ and bounded above,",
     "Because the midrank is confined to a grid of width $1/2n!$ and bounded above,",
     "253 sec4.2 grid"),

    # ---- Section 4.2, the authored component's span -----------------------
    ("main.tex",
     "which is \\AuthoredCompSpanSteps\\ step of the $1/n! = 1/\\NPerms$ grid.",
     "which is \\AuthoredCompSpanSteps\\ steps of the $1/2n! = 1/\\GridK$ grid.",
     "253 sec4.2 span"),

    # ---- Section 5.3, where the grid is stated and explained --------------
    ("sec_decomp.tex",
     "express.  The midrank over $n!$ arrangements lives on a grid of width\n"
     "$1/n! = \\GridStep$.  A causal component of $\\CausalGPTtwo$ is one grid step.\n",
     "express.  The midrank of Eq.~\\eqref{eq:midrank} counts ties as halves and\n"
     "the authored arrangement is always tied with itself, so $2\\,n!$ times the\n"
     "midrank is an integer, and an odd one whenever the number of tied\n"
     "arrangements is odd.  The grid a single reading lives on is therefore\n"
     "$1/2n! = \\GridStep$ wide and not $1/n!$, which\n"
     "\\fn{check_grid_resolution.py} verifies on the measurements.  The\n"
     "components below are medians over texts, so they are quoted in those\n"
     "units to a tenth of a step rather than rounded to whole ones.\n",
     "253 sec5.3 grid"),

    # ---- the floor check's own account of which floors exist --------------
    ("check_paper.py",
     "This paper calls three things a floor: the resolution of the $1/n!$",
     "This paper calls three things a floor: the resolution of the $1/2n!$",
     "253 check_paper docstring"),
]

FILES = sorted({e[0] for e in EDITS})


def apply_edits(root, dry_run=False):
    cache = {}
    for name in FILES:
        with open(os.path.join(root, name), encoding="utf-8") as fh:
            cache[name] = fh.read()
    made = skipped = passed = 0
    for edit in EDITS:
        name, old, new, label = edit[:4]
        later = edit[4] if len(edit) > 4 else None
        text = cache[name]
        done = (new in text) if old in new else (old not in text and new in text)
        if done:
            print(f"  skip  {label:<28} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                print(f"  pass  {label:<28} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<28} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<28} {name}")
        made += 1
    if not dry_run:
        for name, text in cache.items():
            with open(os.path.join(root, name), "w", encoding="utf-8") as fh:
                fh.write(text)
    return made, skipped, passed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    print("batch 34: the midrank grid is 1/2n!")
    print("-" * 52)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 52)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 52)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
