#!/usr/bin/env python3
"""Batch 39: #261 -- the abstract still introduced sigma as the quantity the
thermodynamic reading names.

"The thermodynamic reading names a quantity of a different kind, and for a
fixed text it can be constructed and measured" is the sentence that brings
sigma into the abstract.  It was written when the paper called Eq.(fb) an
entropy production.  #255 withdrew that: what the thermodynamic reading
names is a path against its time reverse, which is Appendix A's sigma_EP
and not sigma.  Left as it stood, the abstract hands sigma a parentage
Section 2.2 takes away from it a few pages later --- "Section 6.1 does
something weaker and sufficient".

The replacement says what Sections 1.1 and 2.2 already say sigma is for: a
comparison whose zero holds on the text being read, which is the one thing
Delta does not supply.  That is the reason sigma is in the paper, and it
never depended on sigma being an entropy production.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b39.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("main.tex",
     "The thermodynamic reading names a quantity of a different kind, and for a\n"
     "fixed text it can be constructed and measured.\n",
     "The question the thermodynamic reading poses needs a comparison whose zero\n"
     "holds on the text being read, and for a fixed text one can be constructed\n"
     "and measured.\n",
     "261 abstract sigma lead-in"),
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
    print("batch 39: the abstract's lead-in to sigma")
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
