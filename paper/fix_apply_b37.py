#!/usr/bin/env python3
"""Batch 37: #257 -- Table 5's caption names the test the lower block now
uses.

#256 replaced the lower block's Fisher exact test against a synthetic
expected row with the one-sample binomial test the question asks for.  The
caption still said "a two-sided Fisher exact test" and covered both blocks
with it, while going on to say that the lower block "is a one-sample
question and not the same test" -- which was true of the question and false
of the code, and is now true of both.  The caption names the two tests
separately.

The sentence also splits at its semicolon.  It was long before and the
replacement is no shorter, and the paper's budget for sentences over fifty
words is not something to spend on a caption.

Idempotent.  Run from the directory holding sec_decomp.tex.

    python3 -I fix_apply_b37.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("sec_decomp.tex",
     "$0.05/\\TailNCells = \\TailBonferroni$ on a two-sided Fisher exact test ---\n"
     "of the two groups' counts against each other in the upper block, and of the\n"
     "causal count against the $\\TailZNull\\%$ the cut defines in the lower, which\n"
     "is a one-sample question and not the same test; \\TailNRejecting\\ cells do in the\n"
     "upper block and \\TailZNRejecting\\ in the lower, against $0.05$ expected by\n"
     "chance.",
     "$0.05/\\TailNCells = \\TailBonferroni$: in the upper block a two-sided\n"
     "Fisher exact test of the two groups' counts against each other, and in the\n"
     "lower a two-sided binomial test of the causal count against the\n"
     "$\\TailZNull\\%$ the cut defines, which is a one-sample question and not the\n"
     "same test.  \\TailNRejecting\\ cells clear it in the\n"
     "upper block and \\TailZNRejecting\\ in the lower, against $0.05$ expected by\n"
     "chance.",
     "257 tab:tail caption"),
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
    print("batch 37: Table 5's caption names both tests")
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
