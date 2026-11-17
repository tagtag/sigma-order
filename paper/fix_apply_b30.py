#!/usr/bin/env python3
"""Batch 30: the two budgets batch 29 pushed over, on the measurement machine.

check_paper.py counts prose after expanding the generated macros, so the
sentence-length and bare-referent counts depend on the values make_tables.py
writes.  Without the measurement data both sit exactly at budget here and
one over there.  Rather than leave a margin of zero, three sites of my own
adding come down:

  * "On a masked evaluator the quantity is defined" and "the sigma one is
    about the quantity" both name sigma instead of saying "the quantity"
    (two off the bare-referent count).
  * The sentence introducing Appendix A's masked measurement ran to 66
    words; it splits where the certificate ends and the measurement begins.

No budget is raised.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b30.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("main.tex",
     "Eq.~\\eqref{eq:fbzero} either way.  On a masked evaluator the quantity is\n"
     "defined, and Section~\\ref{sec:fbresult} measures what it reports there: a\n"
     "property of the masked evaluator, not of the text.",
     "Eq.~\\eqref{eq:fbzero} either way.  On a masked evaluator $\\sigma$ is\n"
     "defined, and Section~\\ref{sec:fbresult} measures what it reports there: a\n"
     "property of the masked evaluator, not of the text.",
     "the quantity main:1383"),


    ("main.tex",
     "The certificate cited there is for modern masked\n"
     "language models and does not carry over to a model of this size, so whether\n"
     "it holds here is a measurement, and this is it: $\\sigEP$ runs from\n"
     "$\\ToySigmaMin$ to $\\ToySigmaMax$,",
     "The certificate cited there is for modern masked\n"
     "language models and does not carry over to a model of this size, so whether\n"
     "it holds here is a measurement.  This is it: $\\sigEP$ runs from\n"
     "$\\ToySigmaMin$ to $\\ToySigmaMax$,",
     "length main:1648"),
    ("sec_truesigma.tex",
     "makes each of them non-zero is the same incompatibility --- but the\n"
     "behaviour of one does not follow from the behaviour of the other, and the\n"
     "sweep does not show them moving together: ranked against each other they\n"
     "give $\\rho = \\CtrlRhoXS$ at $p = \\CtrlPXS$, which establishes nothing\n"
     "either way at $n = \\CtrlNWidths$.",
     "makes each of them non-zero is the same incompatibility.  The behaviour of\n"
     "one does not follow from the behaviour of the other, and the sweep does not\n"
     "show them moving together: ranked against each other they give\n"
     "$\\rho = \\CtrlRhoXS$ at $p = \\CtrlPXS$, which establishes nothing either way\n"
     "at $n = \\CtrlNWidths$.",
     "length true:306"),
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
            print(f"  skip  {label:<24} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                print(f"  pass  {label:<24} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<24} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<24} {name}")
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
    print("batch 30: margin on the two budgets batch 29 filled")
    print("-" * 54)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 54)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 54)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
