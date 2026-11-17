#!/usr/bin/env python3
"""Batch 32: #251 -- the third part of Section 7's opening summary.

Batch 31 widened the Delta summary from one of the three readings to two.
The reading "as a reversal" is still only named and not summarised: what
the paragraph says about it is that it needs no measurement, which is its
character and not what it denies.  A reader told to expect three parts and
given two stops in the same place as before.

The summary now runs in the order the readings are then taken: the
comparison reverses the text and not the path, so no theorem places a zero
on the text being read; a reading on a fixed text cannot be interpreted;
and these corpora cannot decide whether what it separates is causal
structure.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b32.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("main.tex",
     "Under $\\Delta$ a reading on a fixed text\n"
     "cannot be interpreted, and these corpora cannot decide whether what it\n"
     "separates is causal structure; under $\\sigma$ a non-zero reading reports\n"
     "the masked evaluator's incompatibility and not the text.",
     "Under $\\Delta$ the comparison reverses the\n"
     "text and not the path, so no theorem places a zero on the text being read;\n"
     "a reading on a fixed text cannot be interpreted; and these corpora cannot\n"
     "decide whether what it separates is causal structure.  Under $\\sigma$ a\n"
     "non-zero reading reports the masked evaluator's incompatibility and not\n"
     "the text.",
     "251 sec7 opening",
     "batch 33 (#252)"),
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
    print("batch 32: the third part of Section 7's opening summary")
    print("-" * 58)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 58)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 58)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
