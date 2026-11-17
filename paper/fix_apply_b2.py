#!/usr/bin/env python3
"""Batch 2: "the room above" opened out, and the sentences around it.

  #130  "the room above an authored arrangement" names a quantity by a
        metaphor.  It is the gap between the authored arrangement's midrank
        and the ceiling of 1.00 -- equivalently the fraction of
        arrangements still scoring above it -- and what is or is not
        happening to it is happening as the autoregressive evaluator's
        parameter count grows.  Six sites: main.tex:228 (abstract), :1075
        (Figure 1 caption), :1270 (Section 7), sec_decomp.tex:252, :285,
        :414.
  #131  "and we withdraw the claim that it is" -- the present version never
        makes that claim, so there is nothing to withdraw.  Dropped.
  #134  "The room itself is no better: it goes from X to Y" -- the sentence
        before it has already given the gap.  Dropped.
  #135  "not a size this paper reads anywhere else" -- say why it is not
        read: one step is the grid's own resolution, so it bounds nothing.
  #136  "gives both fractions" -- name them.
  #137  "rather than take our word for it" -- plain wording.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b2.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #130 (a) abstract ----------------------------------------------
    ("main.tex",
     "over a \\TrendCapSpan-fold range of parameters, and nothing we measure shows\n"
     "the room above an authored arrangement --- the fraction of arrangements that\n"
     "still score above it --- closing.",
     "over a \\TrendCapSpan-fold range of parameters.  Nothing we measure shows\n"
     "the gap between an authored arrangement's midrank and the ceiling of $1.00$\n"
     "--- the fraction of arrangements that still score above it --- narrowing as\n"
     "that parameter count grows.",
     "130a abstract"),

    # ---- #130 (b) Figure 1 caption ---------------------------------------
    ("main.tex",
     "The room above the non-causal series goes from $\\RoomGPTtwo$ to $\\RoomQwen$,",
     "The gap between the non-causal series and the ceiling of $1.00$ goes from "
     "$\\RoomGPTtwo$ to $\\RoomQwen$,",
     "130b fig1 caption"),

    # ---- #130 (c) Section 7 ----------------------------------------------
    ("main.tex",
     "We found nothing that shows the room above an authored\narrangement closing.",
     "We found nothing that shows the gap between an authored arrangement's\n"
     "midrank and the ceiling of $1.00$ narrowing as the autoregressive\n"
     "evaluator's parameter count grows.",
     "130c sec7"),

    # ---- #130 (d) + #131 + #134 + #135 -----------------------------------
    ("sec_decomp.tex",
     "\\textbf{Nothing measured here shows the room above an\n"
     "authored arrangement closing}, and we withdraw the claim that it is.  The\n"
     "room itself is no better: it goes from $\\RoomGPTtwo$ to $\\RoomQwen$, which\n"
     "is \\AuthoredCompSpanSteps\\ step of the grid and not a size this paper reads\n"
     "anywhere else.",
     "\\textbf{Nothing measured here shows the gap between an authored\n"
     "arrangement's midrank and the ceiling of $1.00$ narrowing as parameter\n"
     "count grows}: it goes from $\\RoomGPTtwo$ to $\\RoomQwen$, which is\n"
     "\\AuthoredCompSpanSteps\\ step of the grid.  One step is the grid's own\n"
     "resolution, so a movement of that size puts no lower bound on how much\n"
     "the gap changed, and we read no size off it.",
     "130d+131+134+135 decomp:252"),

    # ---- #136 + #137 ------------------------------------------------------
    ("sec_decomp.tex",
     "Table~\\ref{tab:saturation} gives both fractions for every\n"
     "evaluator so a reader can see the two series rather than take our word\n"
     "for it.",
     "Table~\\ref{tab:saturation} gives, for every evaluator, the fraction of\n"
     "causal texts and the fraction of non-causal texts whose authored\n"
     "arrangement is the strict maximum, so both series can be checked\n"
     "directly.",
     "136+137 decomp:256"),

    # ---- #130 (e) the ratio's denominator ---------------------------------
    ("sec_decomp.tex",
     "the last column is that gap as a fraction of the room remaining\nabove the non-causal median,",
     "the last column is that gap as a fraction of the distance remaining\n"
     "between the non-causal median and the ceiling of $1.00$,",
     "130e decomp:285"),

    # ---- #130 (f) Section 5.4 summary -------------------------------------
    ("sec_decomp.tex",
     "The room above an authored arrangement\ndoes not measurably close ($\\RoomGPTtwo$ to $\\RoomQwen$,\n"
     "\\AuthoredCompSpanSteps\\ step of the same grid).",
     "The gap between an authored arrangement's midrank\nand the ceiling of $1.00$ does not measurably narrow "
     "($\\RoomGPTtwo$ to\n$\\RoomQwen$, \\AuthoredCompSpanSteps\\ step of the same grid).",
     "130f decomp:414"),
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
        # Which test means "already applied" depends on how the two
        # strings nest.  If old is a substring of new (an insertion), old
        # survives the edit, so only the presence of new can decide; if new
        # is a substring of old (a deletion), new is there before the edit,
        # so old has to be looked for first.
        done = (new in text) if old in new else (old not in text and new in text)
        if done:
            print(f"  skip  {label:<28} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                # A later batch rewrote this passage, so on a re-run neither
                # the old text nor this batch's own replacement is here.
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
    print("batch 2: the room above (#130), and #131 #134 #135 #136 #137")
    print("-" * 70)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 70)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 70)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
