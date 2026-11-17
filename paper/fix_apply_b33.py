#!/usr/bin/env python3
"""Batch 33: #252 -- the middle part of Section 7's summary, said in its own
terms.

The three-part summary now maps one to one onto the three readings, and a
reader recovers all three.  What the middle clause does not do is say
\\emph{why} a reading cannot be interpreted: "a reading on a fixed text
cannot be interpreted" is broad enough to cover the other two, so the
mapping rests on the order the readings are then taken rather than on the
content.  Naming the two deficiencies Section 4.2 establishes --- no stable
scale, no origin --- makes the middle clause as specific as the other two,
and the sentence splits so that nothing runs past the length budget.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b33.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("main.tex",
     "Under $\\Delta$ the comparison reverses the\n"
     "text and not the path, so no theorem places a zero on the text being read;\n"
     "a reading on a fixed text cannot be interpreted; and these corpora cannot\n"
     "decide whether what it separates is causal structure.",
     "Under $\\Delta$ the comparison reverses the\n"
     "text and not the path, so no theorem places a zero on the text being read.\n"
     "A reading on a fixed text has neither a stable scale nor an origin and so\n"
     "cannot be interpreted, and these corpora cannot decide whether what it\n"
     "separates is causal structure.",
     "252 sec7 opening"),
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
    print("batch 33: the middle part of Section 7's summary")
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
