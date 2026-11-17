#!/usr/bin/env python3
"""Batch 42: #265 -- the prose that counted grid steps still counts them on
the old grid.

#253 doubled the step count: the causal component went from 1--2 steps of
1/n! to 2--4 steps of 1/2n!, and the authored component's span from 1 step
to 2.  The macros followed.  The sentences built on the old counts did not,
and several of them are now false rather than merely ungrammatical:

  Section 5.3  "The causal contribution is therefore at the instrument's
               resolution.  Its value is not a measured size but the
               smallest non-zero reading available" -- it is 2 to 4 times
               the smallest non-zero reading.  This is the load-bearing
               sentence of the section and it has to be restated, not
               reworded: the component is near the resolution, not at it.
  Section 5.3  "which is N grid steps --- the same grid step this section
               has just called the smallest" -- the span is 2 steps and the
               smallest is 1, so they are no longer the same thing.
  Section 5.4  "N step of the grid.  One step is the grid's own resolution"
               -- N is 2, so the apposition is wrong twice.
  Section 5.4  "constant to within one grid step" -- the component runs
               from 2 to 4 steps.
  Section 7    "one or two grid steps at each size we measured" -- 2 to 4.
  Figure 2     "N step of the $1/n!$ grid" -- the denominator #253 changed
               everywhere else, and the singular again.

What the restatement costs the paper is worth saying plainly: the argument
"the component is one step, so read no size off it" is gone, because the
component is not one step.  What replaces it is what the paper already does
elsewhere -- the component takes few distinct values, and the size the
paper quotes is the ceiling-free one.  That is weaker and it is true.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b42.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- Section 5.3: the movement paragraph ------------------------------
    ("sec_decomp.tex",
     "component is $\\AuthoredCompSpan$, which is \\AuthoredCompSpanSteps\\ grid\n"
     "steps --- the same grid step this section has just called the smallest\n"
     "non-zero reading available.  Section~\\ref{sec:window} returns to that where\n"
     "it reports the change, because a rise of one step is not evidence of a\n"
     "different kind from a component of one step.\n",
     "component is $\\AuthoredCompSpan$, which is \\AuthoredCompSpanSteps\\ grid\n"
     "steps --- no more than the causal component this section has just declined\n"
     "to read as a size.  Section~\\ref{sec:window} returns to that where\n"
     "it reports the change, because a rise of \\AuthoredCompSpanSteps\\ steps is\n"
     "not evidence of a different kind from a component of\n"
     "\\CausalCompStepsMin\\ to \\CausalCompStepsMax.\n",
     "265 sec5.3 movement"),

    # ---- Section 5.3: the claim the section rests on ----------------------
    ("sec_decomp.tex",
     "The causal contribution is therefore at the instrument's resolution.  Its\n"
     "value is not a measured size but the smallest non-zero reading available,\n"
     "and a difference between any two evaluators of one step is a difference between\n"
     "adjacent representable numbers.",
     "The causal contribution is therefore close to the instrument's resolution\n"
     "without being at it.  One step is $\\GridStep$ and the component is\n"
     "\\CausalCompStepsMin\\ to \\CausalCompStepsMax\\ of them, taking only\n"
     "\\CausalCompNDistinct\\ distinct values across the ladder, so a difference\n"
     "between two evaluators is a difference between adjacent representable\n"
     "numbers.",
     "265 sec5.3 resolution claim",
     "batch 43 (#266)"),

    # ---- Section 5.4: the ceiling gap -------------------------------------
    ("sec_decomp.tex",
     "\\AuthoredCompSpanSteps\\ step of the grid.  One step is the grid's own\n"
     "resolution, so a movement of that size puts no lower bound on how much\n"
     "the gap changed, and we read no size off it.",
     "\\AuthoredCompSpanSteps\\ steps of the grid.  That is within the\n"
     "\\CausalCompStepsMin--\\CausalCompStepsMax\\ steps this paper declines to\n"
     "read as a size, so a movement of it puts no lower bound on how much\n"
     "the gap changed, and we read no size off it.",
     "265 sec5.4 ceiling gap"),

    # ---- Section 5.4: the constancy claim ---------------------------------
    ("sec_decomp.tex",
     "causal contribution read on the median is constant to within one grid step\n",
     "causal contribution read on the median stays at\n"
     "\\CausalCompStepsMin--\\CausalCompStepsMax\\ grid steps\n",
     "265 sec5.4 constancy"),

    # ---- Section 5.4: the summary -----------------------------------------
    ("sec_decomp.tex",
     "$\\RoomQwen$, \\AuthoredCompSpanSteps\\ step of the same grid).",
     "$\\RoomQwen$, \\AuthoredCompSpanSteps\\ steps of the same grid).",
     "265 sec5.4 summary"),

    # ---- Figure 2's caption -----------------------------------------------
    ("main.tex",
     "\\AuthoredCompSpanSteps\\ step of the $1/n!$ grid.  The vertical separation",
     "\\AuthoredCompSpanSteps\\ steps of the $1/2n!$ grid.  The vertical separation",
     "265 fig2 grid"),

    ("main.tex",
     "which is \\AuthoredCompSpanSteps\\ step of the same grid, so it does not measurably close either",
     "which is \\AuthoredCompSpanSteps\\ steps of the same grid, so it does not measurably close either",
     "265 fig2 ceiling"),

    # ---- Section 8 --------------------------------------------------------
    ("main.tex",
     "about how the median share behaves beyond this range, only that it is one\n"
     "or two grid steps at each size we measured\n",
     "about how the median share behaves beyond this range, only that it is\n"
     "\\CausalCompStepsMin\\ to \\CausalCompStepsMax\\ grid steps at each size we\n"
     "measured\n",
     "265 sec8 no extrapolation"),

    # ---- three more $1/n!$ sites #253 missed -------------------------------
    ("main.tex",
     "component of a single evaluator spans \\AuthoredCorpSpreadSteps\\ steps of\n"
     "the $1/n!$ grid for the median evaluator",
     "component of a single evaluator spans \\AuthoredCorpSpreadSteps\\ steps of\n"
     "the $1/2n!$ grid for the median evaluator",
     "265 sec4.2 corpus spread"),

    ("main.tex",
     "\\CausalCompStepsMin--\\CausalCompStepsMax\\ steps of the\n"
     "$1/n!$ grid in every evaluator (Section~\\ref{sec:resolution}), which is the\n"
     "smallest non-zero value the statistic can return, so a difference between\n"
     "two evaluators is a difference between adjacent representable numbers.",
     "\\CausalCompStepsMin--\\CausalCompStepsMax\\ steps of the\n"
     "$1/2n!$ grid in every evaluator (Section~\\ref{sec:resolution}), taking\n"
     "\\CausalCompNDistinct\\ distinct values across the ladder, so a difference\n"
     "between two evaluators is a difference between adjacent representable\n"
     "numbers.",
     "265 sec7 size not resolved",
     "batch 43 (#266)"),

    ("sec_decomp.tex",
     "at \\CausalCompStepsMin--\\CausalCompStepsMax\\ steps of the $1/n!$ grid.",
     "at \\CausalCompStepsMin--\\CausalCompStepsMax\\ steps of the $1/2n!$ grid.",
     "265 sec5.4 ladder"),
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
    print("batch 42: the prose that counted steps on the old grid")
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
