#!/usr/bin/env python3
"""Batch 40: #262 -- Section 6 says why it measures what Section 6.1 proves
is zero.

A reader who starts at Section 6 meets a section that proves sigma
vanishes for any evaluator with a joint and then spends three subsections
measuring it.  The obvious objection -- that the measurement confirms its
own prediction and adds nothing -- has two answers in this paper, and
neither is where that reader will look:

  - the identity fixes what a non-zero reading MEANS and not what it moves
    with, so the label contrast is not settled in advance
    (Section 6.1, two pages in);
  - sigma is the comparison Delta stands in for, so constructing it is what
    completes Section 2.2 rather than a separate result (Section 7, and the
    abstract's closing paragraph).

Both go into Section 6's opening, where the question is first asked.  The
content is not new; its placement is.  This is the same defect the rest of
this correction pass has been removing -- an answer that exists somewhere
other than where the reader needs it.

Idempotent.  Run from the directory holding sec_truesigma.tex.

    python3 -I fix_apply_b40.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("sec_truesigma.tex",
     "Section~\\ref{sec:notareversal} gave the reason it has no origin on the text\n"
     "it is read from.  This section measures a comparison that has one.\n",
     "Section~\\ref{sec:notareversal} gave the reason it has no origin on the text\n"
     "it is read from.  This section measures a comparison that has one.\n"
     "Two things make that worth doing, and the identity of\n"
     "Eq.~\\eqref{eq:fbzero} settles neither.  It fixes what a non-zero reading of\n"
     "$\\sigma$ means and not what that reading moves with, so whether $\\sigma$\n"
     "separates the two label groups has to be measured.  And $\\sigma$ is the\n"
     "comparison $\\Delta$ stands in for, so constructing it completes\n"
     "Section~\\ref{sec:notareversal}: the quantity that does have an origin on\n"
     "the text being read turns out to have nothing to say about that text.\n",
     "262 sec6 opening"),
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
    print("batch 40: why Section 6 measures it")
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
