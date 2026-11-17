#!/usr/bin/env python3
"""Batch 12: Sections 5.1 and 5.3 -- #101 #102 #103 #104 #105 #107 #108
#109 #111 #112 #113 #115 #116 #117 #118.

  #101  "Two features of the corpus design might be read as validation" --
        only the first is a feature of the corpus design; the second is a
        feature of this paper's analysis.
  #102  "construct validity" is used without saying what it is.
  #103  "the causal component is CausalGPTtwo and CausalQwen" reads as a
        range; both ends are the same number.
  #104  "well clear of the grid" -- clear of what, and by how much.
  #105  "the two forms" -- name them, and keep the correlation out of the
        grounds, since n = 5 cannot settle it.
  #107  "rank-biserial effect size" / "rank-biserial correlation" -- one
        name, the one Eq.(rb) defines.
  #108  The range of r is a reservation; the median is not.  Separate them.
  #109  ContrastRejectByEval belongs beside the 18/25 it breaks down.
  #111  "since a count over an AR ladder says nothing about where on the AR
        ladder it falls" -- say it as the plain fact that a total does not
        give the breakdown.
  #112  "and only the z form can carry it" repeats the paragraph above it.
  #113  "which has neither a ceiling nor a grid: ... by a normalisation that
        cannot saturate" -- the grid is what decides whether the component
        is representable; the ceiling belongs to Section 5.4.
  #115  "which the table shows and this threshold does not" and "the
        difference opens" -- say what is shown and what opens.
  #116  "the strict maximum this section goes on to use" -- say what it is.
  #117  the grid of the tail reading needs its basis in the text.
  #118  "for the reason Section 6.3 gives about its own" -- say it here.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b12.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #101 + #102 -------------------------------------------------------
    ("main.tex",
     "Two features of the corpus design might be read as validation.  Neither\nis, and it is worth saying why.",
     "Two features might be read as validation --- one of the corpus design, one\n"
     "of our own analysis.  Neither is, and it is worth saying why.  What would\n"
     "be at stake is \\emph{construct validity}: whether the labels pick out a\n"
     "causal ordering of the sentences, rather than something else the two\n"
     "prompts induced along with it.",
     "101+102 main:1190"),

    ("main.tex",
     "Second, our within-text design removes the length,",
     "Second --- and this one is ours, not the corpus design's --- our\n"
     "within-text design removes the length,",
     "101b main:1202"),

    # ---- #103 -------------------------------------------------------------
    ("sec_decomp.tex",
     "$\\ParamsQwen$; the causal component is $\\CausalGPTtwo$ and $\\CausalQwen$.",
     "$\\ParamsQwen$; the causal component is $\\CausalGPTtwo$ at both ends and\n"
     "does not move between them.",
     "103 decomp:24",
     "batch 29 (cold read)"),

    # ---- #104 -------------------------------------------------------------
    ("sec_decomp.tex",
     "The authored component is a different size\n"
     "entirely: it sits \\AuthoredCompStepsMin\\ to \\AuthoredCompStepsMax\\ steps\n"
     "from the null, so the distance this paper decomposes is well clear of the\n"
     "grid even though the causal part of it is not.",
     "The authored component is a different size\n"
     "entirely: it sits \\AuthoredCompStepsMin\\ to \\AuthoredCompStepsMax\\ steps\n"
     "from the null, against the \\CausalCompStepsMin--\\CausalCompStepsMax\\ steps\n"
     "of the causal component.  The distance this paper decomposes is thus a\n"
     "measured size; the part of it attributable to the labels is not.",
     "104 decomp:55"),

    # ---- #113 + #105 ------------------------------------------------------
    ("sec_decomp.tex",
     "This is why Section~\\ref{sec:decomp}\n"
     "reports the same decomposition on\n"
     "$z = \\Delta(\\mathrm{id})/\\mathrm{sd}\\{\\Delta(\\pi)\\}$, which has neither a\n"
     "ceiling nor a grid: there the share runs $\\ShareZMin\\%$ to $\\ShareZMax\\%$ ---\n"
     "the same order of magnitude, by a normalisation that cannot saturate.  Per evaluator the two forms are not\n"
     "interchangeable: one evaluator's share differs between them by a factor of\n"
     "$\\ShareFormWorst$.  Whether they track each other across the\n"
     "$\\ShareFormNEval$ evaluators is not a question $\\ShareFormNEval$ points can\n"
     "settle either way ($\\rho = \\ShareFormRho$, $p = \\ShareFormP$); the factor is\n"
     "the measured part,",
     "This is why Section~\\ref{sec:decomp}\n"
     "reports the same decomposition on\n"
     "$z = \\Delta(\\mathrm{id})/\\mathrm{sd}\\{\\Delta(\\pi)\\}$, which lives on no\n"
     "grid at all, so that a component this small is representable in it: there\n"
     "the share runs $\\ShareZMin\\%$ to $\\ShareZMax\\%$, the same order of\n"
     "magnitude.  Per evaluator the midrank form and the $z$ form are not\n"
     "interchangeable: one evaluator's share differs between them by a factor of\n"
     "$\\ShareFormWorst$.  Whether the two forms track each other across the\n"
     "$\\ShareFormNEval$ evaluators is not a question $\\ShareFormNEval$ points can\n"
     "settle either way ($\\rho = \\ShareFormRho$, $p = \\ShareFormP$), and we rest\n"
     "nothing on it; the factor is the measured part,",
     "105+113 decomp:71"),

    # ---- #107 + #108 + #109 + #111 + #112 ---------------------------------
    ("sec_decomp.tex",
     "It does not separate them\n"
     "everywhere: the worst cell gives $p = \\ContrastPWorst$, and the\n"
     "rank-biserial effect size runs from $\\ContrastRMin$ to $\\ContrastRMax$ with\n"
     "a median of $\\ContrastRMedian$.  The cells that clear the threshold are not\n"
     "stacked on one rung of the AR ladder --- \\ContrastRejectByEval\\ --- and\n"
     "Table~\\ref{tab:blkcells} prints every cell, since a count over an AR ladder\n"
     "says nothing about where on the AR ladder it falls.  What is consistent is the direction, which\n"
     "is the same in \\ContrastNPositive\\ of the \\ContrastNCells\\ cells.  What is at resolution\n"
     "is the \\emph{size} of that separation once it is expressed as a share of the\n"
     "authored distance, and only the $z$ form can carry it.",
     "A total of \\ContrastNRejecting\\ does not say how those cells fall across\n"
     "the AR ladder, so the breakdown is given: \\ContrastRejectByEval, and\n"
     "Table~\\ref{tab:blkcells} prints every cell.  The separation is not\n"
     "everywhere: the worst cell gives $p = \\ContrastPWorst$, and the\n"
     "rank-biserial correlation of Eq.~\\eqref{eq:rb} runs from $\\ContrastRMin$ to\n"
     "$\\ContrastRMax$ across the cells, which is the reservation; its median is\n"
     "$\\ContrastRMedian$, which is not one.  What is consistent is the direction,\n"
     "which is the same in \\ContrastNPositive\\ of the \\ContrastNCells\\ cells.\n"
     "What is at resolution is the \\emph{size} of that separation once it is\n"
     "expressed as a share of the authored distance.",
     "107+108+109+111+112 decomp:83"),

    # ---- #115 + #116 ------------------------------------------------------
    ("sec_decomp.tex",
     "Single\nevaluators reach $\\TailBelowOnsetMax$ points below it, which the table shows\n"
     "and this threshold does not, and from there the difference opens for all of\nthem.",
     "Single\nevaluators reach $\\TailBelowOnsetMax$ points below it: Table~\\ref{tab:sweep}\n"
     "shows those cells, and $\\TailOnsetThr$, being the threshold at which the\n"
     "\\emph{worst} evaluator first passes a point, does not.  From\n"
     "$\\TailOnsetThr$ up, the difference between the two label groups is more\n"
     "than a point for every evaluator.",
     "115 decomp:127",
     "batch 29 (cold read)"),

    ("sec_decomp.tex",
     "The cut is not chosen to suit the argument: the separation is\n"
     "widest at $t = 0.90$ rather than at the strict maximum this section goes on\n"
     "to use, and the whole sweep is printed rather than the threshold that\n"
     "maximises it.",
     "The cut is not chosen to suit the argument.  The separation is\n"
     "widest at $t = 0.90$, not at the cut this section goes on to use, which is\n"
     "the strict maximum: the authored arrangement scoring above every one of the\n"
     "other $n! - 1$ arrangements of its own text.  The whole sweep is printed\n"
     "rather than the threshold that maximises it.",
     "116 decomp:133"),

    # ---- #117 + #118 ------------------------------------------------------
    ("sec_decomp.tex",
     "points, on a grid no coarser than $\\CeilResolution$, which is not a floor;",
     "points, on a grid no coarser than $\\CeilResolution$, which is not a floor.\n"
     "That grid is the fraction's own: it is taken over at least $\\CeilNTexts$\n"
     "causal texts in every cell, so one text moves it by no more than\n"
     "$\\CeilResolution$.",
     "117 decomp:166"),
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
            print(f"  skip  {label:<26} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                # A later batch rewrote this passage, so on a re-run neither
                # the old text nor this batch's own replacement is here.
                print(f"  pass  {label:<26} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<26} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<26} {name}")
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
    print("batch 12: Sections 5.1 and 5.3")
    print("-" * 60)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 60)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 60)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
