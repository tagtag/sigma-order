#!/usr/bin/env python3
"""Batch 35: #254 -- a rank survives a positive affine rescaling, not any
strictly monotone one.

Section 3.1 says the midrank disposes of the unit "because a rank is
unchanged by any strictly monotone rescaling of the score".  That is true of
the ranks of a score.  What is ranked here is not a score but the difference

    Delta_S(pi) = [ S(x_pi) - S(x_{pi o rev}) ] / L ,

and a non-linear monotone map of S does not preserve the order of those
differences: f(a) - f(b) > f(c) - f(d) does not follow from a - b > c - d.
Only a positive affine map S -> aS + b carries Delta_S to a Delta_S and so
leaves the ranks alone.

The claim the sentence is making still holds, because a change of unit is
affine: nats to bits is a = 1/ln 2.  So the correction narrows the class and
keeps the argument, and says why the narrower class is the right one.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b35.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("main.tex",
     "because a rank is unchanged by any strictly monotone rescaling of\n"
     "the score.  Stopping after the first stage would leave the scale exactly\n"
     "where it was.",
     "because a rank is unchanged by any positive affine rescaling of\n"
     "the score.  Affine and not merely monotone: $\\Delta_S$ is a\n"
     "\\emph{difference} of scores, and a non-linear monotone map of $S$\n"
     "reorders those differences.  A change of unit is affine, which is what\n"
     "this stage has to absorb.  Stopping after the first stage would leave the\n"
     "scale exactly where it was.",
     "254 affine not monotone"),
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
    print("batch 35: affine, not monotone")
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
