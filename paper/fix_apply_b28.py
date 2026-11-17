#!/usr/bin/env python3
"""Batch 28: the glossary violation batch 23 introduced.

glossary.txt reserves "different sequence" for the contrast between an
arrangement and its reversal, and refuses "different text".  The sentence
#203 added to Section 8 used the refused phrase for a different purpose --
that Eq. (delta) allows each text its own joint and only forbids reading its
two terms off two distributions.  Saying "each text" carries that without
the reserved wording.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b28.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("main.tex",
     "$\\log P(\\tilde{x})$ under one and the same joint $P$ --- a different $P$ for\n"
     "a different text is no obstacle, but two values read off two different\n"
     "distributions are not a $\\Delta$.",
     "$\\log P(\\tilde{x})$ under one and the same joint $P$ --- a different $P$ for\n"
     "each text is no obstacle, but two values read off two different\n"
     "distributions are not a $\\Delta$.",
     "glossary main:1449"),
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
            print(f"  skip  {label:<22} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                print(f"  pass  {label:<22} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<22} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<22} {name}")
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
    print("batch 28: the glossary violation from #203")
    print("-" * 48)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 48)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 48)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
