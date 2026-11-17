#!/usr/bin/env python3
"""Batch 31: the second cold read of Section 7 -- #248, #249, #250.

All three are defects in sentences batch 29 and batch 22 introduced.

  #248  The opening now says the conclusion is negative in two ways and
        that the Delta one has three parts, but the clause summarising the
        Delta side --- "these corpora cannot say what they are separated
        by" --- is only the third of those parts.  The first two are
        structural and hold whatever the corpora are, which Section 7 says
        itself a page later.  A reader is told to expect three parts and
        given a summary that covers one.  The summary now covers all three.
  #249  "Delta cannot be read as one on these corpora, which cannot decide
        whether what it separates is causal structure" says the same thing
        twice in one sentence.  The sentences that follow already give the
        reason, so the second half goes.
  #250  "Three things." opens a fourth triple two paragraphs after Section 7
        has distinguished three of them from one another.  The count is
        right and costs more than it is worth; the list closes on "And" by
        itself.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b31.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #248 -------------------------------------------------------------
    ("main.tex",
     "Under $\\Delta$ the two label groups do\n"
     "separate, but these corpora cannot say what they are separated by; under\n"
     "$\\sigma$ a non-zero reading reports the masked evaluator's incompatibility\n"
     "and not the text.",
     "Under $\\Delta$ a reading on a fixed text\n"
     "cannot be interpreted, and these corpora cannot decide whether what it\n"
     "separates is causal structure; under $\\sigma$ a non-zero reading reports\n"
     "the masked evaluator's incompatibility and not the text.",
     "248 sec7 opening"),

    # ---- #249 -------------------------------------------------------------
    ("main.tex",
     "As a \\emph{test for causal structure}, $\\Delta$ cannot be read as one on\n"
     "these corpora, which cannot decide whether what it separates is causal\n"
     "structure.  It does separate the two prompt-defined sets, in a fixed",
     "As a \\emph{test for causal structure}, $\\Delta$ cannot be read as one\n"
     "here.  It does separate the two prompt-defined sets, in a fixed",
     "249 sec7 third reading"),

    # ---- #250 -------------------------------------------------------------
    ("main.tex",
     "not separate the two label groups.  Three things.  That a non-zero $\\sigma$",
     "not separate the two label groups.  That a non-zero $\\sigma$",
     "250 sec7 closing"),
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
    print("batch 31: the second cold read of Section 7")
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
