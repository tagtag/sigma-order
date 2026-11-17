#!/usr/bin/env python3
"""Batch 44: #268 -- the rest of the resolution-floor language.

#266 corrected the six places that stated the argument outright.  A sweep
for every line containing floor, smallest, representable or resolution finds
seven more that assert the same thing in other words, and they are false for
the same reason: the causal component is 2 to 4 steps of the 1/2n! grid, not
one, so it does not sit at the statistic's resolution and does not occupy
the smallest non-zero reading.

  Section 2.2   "the size sits at the resolution of the statistic"
  Table 2       "a quantity sitting at the resolution of its statistic does
                not have a share that survives renormalisation"
  Section 5.3   "What is at resolution is the SIZE of that separation"
  Section 5.4   "The causal component is at the grid floor at every rung ...
                it never leaves the smallest non-zero reading the statistic
                can return"
  Section 5.4   "the top of the midrank range, where it is not at the grid
                floor"
  Section 7     "Read in the tail it leaves the grid floor"
  Section 6.4   "it sits at the grid's resolution"

All seven take the replacement #266 settled on: the midrank saturates, the
causal component is measured in the room the ceiling leaves, and it takes
few distinct values.  That is why the paper quotes the ceiling-free share as
the size.

Section 5.4's heading "In the tail it is not at the grid floor" is left
alone: that paragraph is about the tail statistic's own grid of
\\CeilResolution points, and says so in its next sentence.  The three floors
check_paper's check_bare_floor distinguishes are still three.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b44.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("main.tex",
     "supported in \\ContrastNPositive\\ of \\ContrastNCells\\ cells, and the size\n"
     "sits at the resolution of the\n"
     "statistic.",
     "supported in \\ContrastNPositive\\ of \\ContrastNCells\\ cells, and the size\n"
     "is measured in the room a saturating midrank\n"
     "leaves.",
     "268 sec2.2 size"),

    ("main.tex",
     "nothing either way at that $n$.  Section~\\ref{sec:resolution} is where that\n"
     "belongs: a quantity sitting at the resolution of its statistic does not have\n"
     "a share that survives renormalisation.}",
     "nothing either way at that $n$.  Section~\\ref{sec:resolution} is where that\n"
     "belongs: a quantity measured in the room a bounded statistic leaves does not\n"
     "have a share that survives renormalisation.}",
     "268 tab2 caption"),

    ("sec_decomp.tex",
     "What is at resolution is the \\emph{size} of that separation once it is\n"
     "expressed as a share of the authored distance.",
     "What the ceiling compresses is the \\emph{size} of that separation once it is\n"
     "expressed as a share of the authored distance.",
     "268 sec5.3 what is at resolution"),

    ("sec_decomp.tex",
     "The causal component is at the grid floor at every rung.  It is\n"
     "\\CausalCompStepsMin\\ to \\CausalCompStepsMax\\ steps across the\n"
     "\\TrendNEval\\ evaluators (Section~\\ref{sec:resolution}), so across\n"
     "a \\TrendCapSpan-fold range of parameters it never leaves the smallest\n"
     "non-zero\n"
     "reading the statistic can return.",
     "The causal component stays within a few steps of the grid at every rung.\n"
     "It is \\CausalCompStepsMin\\ to \\CausalCompStepsMax\\ steps across the\n"
     "\\TrendNEval\\ evaluators (Section~\\ref{sec:resolution}), so across\n"
     "a \\TrendCapSpan-fold range of parameters it takes\n"
     "\\CausalCompNDistinct\\ distinct\n"
     "values in all.",
     "268 sec5.4 grid floor"),

    ("sec_decomp.tex",
     "Section~\\ref{sec:resolution} measured the same label contrast at the top of\n"
     "the midrank range, where it is not at the grid floor.",
     "Section~\\ref{sec:resolution} measured the same label contrast at the top of\n"
     "the midrank range, where the ceiling does not compress it.",
     "268 sec5.4 tail contrast"),

    ("main.tex",
     "(Section~\\ref{sec:window}).  Read in the tail it leaves the\n"
     "grid floor and moves along the AR ladder.",
     "(Section~\\ref{sec:window}).  Read in the tail it is no longer compressed\n"
     "and moves along the AR ladder.",
     "268 sec7 tail"),

    ("sec_truesigma.tex",
     "read off is the size of the part attributable to the causal label: it sits at\n"
     "the grid's resolution, and the groups have no criterion distinguishing them",
     "read off is the size of the part attributable to the causal label: it is\n"
     "measured in the room a saturating midrank leaves, and the groups have no\n"
     "criterion distinguishing them",
     "268 sec6.4 what cannot be read"),
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
    print("batch 44: the rest of the resolution-floor language")
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
