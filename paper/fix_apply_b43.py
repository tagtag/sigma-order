#!/usr/bin/env python3
"""Batch 43: #266 -- the argument that rested on the resolution floor.

#253 made the grid 1/2n! and the causal component 2 to 4 steps of it rather
than one.  #265 corrected the sentences that counted steps.  What it did not
correct is the argument those counts were supporting, which survives in six
places and is now either a non sequitur or false:

  abstract      "...steps of the grid the statistic lives on, where one step
                is the smallest non-zero reading it can return, SO what the
                median establishes is that the groups differ and not by how
                much" -- the premise is true and no longer reaches the
                conclusion, because the component is not one step.
  Section 5.3   "a difference between two evaluators is a difference between
                adjacent representable numbers" -- the two values the
                component takes are 2 and 4 steps, which are not adjacent.
                This one #265 introduced.
  Section 5.3   "a component one grid step wide does not have a share that
                survives being renormalised."
  Section 5.3   "``The causal contrast is at the instrument's resolution''
                is a statement about the median difference and we keep it as
                one" -- the paper undertakes to keep a false statement.
  Section 5.4   "The median reading was at the resolution floor from the
                smallest evaluator onwards" -- false.
  Section 7     the same "adjacent representable numbers" as Section 5.3.

The conclusion does not change: the size this paper quotes is the
ceiling-free one, and the midrank component is not read as a size.  What
changes is the reason, from the grid to the ceiling, and the ceiling
argument is already in the paper and is untouched by #253 -- the midrank is
bounded above by 1 - 0.5/n!, and the authored component already stands 17 to
19 steps from the null, so the causal component is measured in the room that
is left.  That is why the paper reports the same decomposition on z, which
has no ceiling, and quotes the z share as the size.

This is weaker than "the component is one step, so read no size off it", and
it is true.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b43.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- the abstract's inference -----------------------------------------
    ("main.tex",
     "\\CausalCompStepsMin\\ to \\CausalCompStepsMax\\ steps of the $1/2n!$ grid the\n"
     "statistic lives on, where one step\n"
     "is the smallest non-zero reading it can return, so what the median\n"
     "establishes is that the two label groups differ and not by how much.",
     "\\CausalCompStepsMin\\ to \\CausalCompStepsMax\\ steps of the $1/2n!$ grid the\n"
     "statistic lives on, measured on a midrank that is bounded above and\n"
     "already near its ceiling, so what the median\n"
     "establishes is that the two label groups differ and not by how much.",
     "266 abstract inference"),

    # ---- Section 5.3: why the size is not read ----------------------------
    ("sec_decomp.tex",
     "The causal contribution is therefore close to the instrument's resolution\n"
     "without being at it.  One step is $\\GridStep$ and the component is\n"
     "\\CausalCompStepsMin\\ to \\CausalCompStepsMax\\ of them, taking only\n"
     "\\CausalCompNDistinct\\ distinct values across the ladder, so a difference\n"
     "between two evaluators is a difference between adjacent representable\n"
     "numbers.  This is why Section~\\ref{sec:decomp}\n",
     "The causal contribution is therefore a few steps of the grid: one step is\n"
     "$\\GridStep$ and the component is \\CausalCompStepsMin\\ to\n"
     "\\CausalCompStepsMax\\ of them, taking \\CausalCompNDistinct\\ distinct\n"
     "values across the \\TrendNEval\\ evaluators.  What keeps that from being\n"
     "read as a size is not the grid but the ceiling.  The midrank is bounded\n"
     "above by $1 - 0.5/n!$, and the authored component already stands\n"
     "\\AuthoredCompStepsMin\\ to \\AuthoredCompStepsMax\\ steps from the null, so\n"
     "the causal component is measured in the room that is left.\n"
     "This is why Section~\\ref{sec:decomp}\n",
     "266 sec5.3 why not a size"),

    # ---- Section 5.3: the renormalisation remark --------------------------
    ("sec_decomp.tex",
     "it is the same statement again: a component one grid\n"
     "step wide does not have a share that survives being renormalised.",
     "it is the same statement again: a component measured\n"
     "in the room left under the ceiling does not have a share that survives\n"
     "being renormalised.",
     "266 sec5.3 renormalisation"),

    # ---- Section 5.3: what the paper undertakes to keep -------------------
    ("sec_decomp.tex",
     "``The causal contrast is at the instrument's resolution'' is a statement\n"
     "about the median difference and we keep it as one.",
     "``The median contrast is too compressed to read a size from'' is a\n"
     "statement about the median difference and we keep it as one.",
     "266 sec5.3 what this changes"),

    # ---- Section 5.4 ------------------------------------------------------
    ("sec_decomp.tex",
     "the tail grows.  The median reading was at the resolution floor from the\n"
     "smallest evaluator onwards and stays there;",
     "the tail grows.  The median reading was already against the ceiling at the\n"
     "smallest evaluator and stays there;",
     "266 sec5.4 floor"),

    # ---- Section 7 --------------------------------------------------------
    ("main.tex",
     "\\CausalCompNDistinct\\ distinct values across the ladder, so a difference\n"
     "between two evaluators is a difference between adjacent representable\n"
     "numbers.  What\n"
     "the median establishes is that the sets differ and not by how much.",
     "\\CausalCompNDistinct\\ distinct values across the ladder, and it is\n"
     "measured in the room a saturating midrank leaves.  What\n"
     "the median establishes is that the sets differ and not by how much.",
     "266 sec7 size not resolved"),

    ("main.tex",
     "which is why Section~\\ref{sec:window} reports it; the resolution argument is\n"
     "about the median and we do not extend it past that.",
     "which is why Section~\\ref{sec:window} reports it; that argument is\n"
     "about the median and we do not extend it past that.",
     "266 sec7 the argument"),
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
    print("batch 43: the argument that rested on the resolution floor")
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
