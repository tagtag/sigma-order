#!/usr/bin/env python3
"""Batch 10: Section 4 -- #87 #89 #90 #91 #92 #93 #94 #95 #96.

  #87  The exchanged-label numbers are given three times.  Section 3.4
        states them; the two restatements in Section 4 go.
  #89  "already near the top of its own permutation set ... and stays
        there" gives no scale: the authored component is bounded above by
        +0.50, the span is a step of the grid, the TrendCapSpan-fold is a
        parameter count, and 1/n! = 1/24 is the grid width.
  #90  "The corresponding rank correlation establishes no trend" -- between
        what and what, and why n = 5 cannot settle it.
  #91  "and does not find it there either" -- say what was found: counted
        on the non-causal group the fraction goes down, not up.
  #92  "Why an autoregressive evaluator should find this easily" -- what
        "this" is; and "the one its context windows were built for", whose
        only use of "context window" is here.
  #93  The fourth statement that Delta does not exist for a masked
        evaluator, in a paragraph that needs none.
  #94  "The same observation applies at the other end" -- which end.
  #95  "across the generators" -- that these are the five corpora, and that
        the spread is across corpora rather than along the AR ladder.
  #96  "and Section 6.1's identity holds whatever produced the text" --
        the sentence is about the causal component of Delta; the identity
        is about sigma and does not bear on it.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b10.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #87 (a): Section 4 opening --------------------------------------
    ("main.tex",
     "which is a use of the labels; what it does not use is any claim that the\n"
     "label is right.  Computed on the other group instead it is $\\SwapAuthored$ rather than\n"
     "$\\SwapAuthoredOrig$ for \\texttt{\\SwapEval} (Section~\\ref{sec:decomp}), and\n"
     "the statements below survive the\nexchange:",
     "which is a use of the labels; what it does not use is any claim that the\n"
     "label is right.  Section~\\ref{sec:decomp} gives what the exchange does to\n"
     "the number; the statements below survive it:",
     "87a main:970"),

    # ---- #89 ---------------------------------------------------------------
    ("main.tex",
     "The authored arrangement is already near the top of its own permutation set at\n"
     "$\\ParamsGPTtwo$, and stays there: over the $\\TrendCapSpan$-fold span the\n"
     "whole range of the component is $\\AuthoredCompSpan$, which is\n"
     "\\AuthoredCompSpanSteps\\ step of the $1/n!$ grid.",
     "The authored component is bounded above by $+0.50$, the value a text would\n"
     "take if its authored arrangement were the strict maximum in every text of\n"
     "the group.  At $\\ParamsGPTtwo$ it is already $\\AuthoredGPTtwo$ of that, and\n"
     "over a $\\TrendCapSpan$-fold span of parameter count it ends at\n"
     "$\\AuthoredQwen$: the whole range of the component is $\\AuthoredCompSpan$,\n"
     "which is \\AuthoredCompSpanSteps\\ step of the $1/n! = 1/\\NPerms$ grid.",
     "89 main:996",
     "batch 29 (#232)"),

    # ---- #90 ---------------------------------------------------------------
    ("main.tex",
     "The corresponding rank\ncorrelation establishes no trend ($\\rho = \\TrendAuthoredRho$, $p =\n"
     "\\TrendAuthoredP$, exact rank null over \\TrendNEval\\ evaluators).",
     "Ranked against parameter count, the component\nestablishes no trend "
     "($\\rho = \\TrendAuthoredRho$, $p = \\TrendAuthoredP$,\n"
     "exact rank null over \\TrendNEval\\ evaluators; at that $n$ the smallest\n"
     "attainable two-sided $p$ is $\\TrendPFloor$, so no result on this AR ladder\n"
     "could have reached $0.05$ by a margin).",
     "90 main:999",
     "batch 29 (#246)"),

    # ---- #91 ---------------------------------------------------------------
    ("main.tex",
     "Section~\\ref{sec:window} looks for saturation in the count of texts that\n"
     "have reached the top, which is the statistic without this one's grid and\n"
     "bound, and does not find it there either.",
     "Section~\\ref{sec:window} looks for saturation in the count of texts whose\n"
     "authored arrangement is the strict maximum, which is the statistic without\n"
     "this one's grid and bound.  Counted on the non-causal group, that fraction\n"
     "falls rather than rises along the AR ladder, from $\\CeilNGPTtwo\\%$ to\n"
     "$\\CeilNQwen\\%$.",
     "91 main:1002",
     "batch 29 (cold read)"),

    # ---- #87 (b) -----------------------------------------------------------
    ("main.tex",
     "The component is the median midrank of the texts labelled\n"
     "\\emph{non}-causal, and under the exchange of labels \\texttt{\\SwapEval}'s is\n"
     "$\\SwapAuthored$ instead --- the same statement either way.  What it says is that an",
     "The component is the median midrank of the texts labelled\n"
     "\\emph{non}-causal.  What it says is that an",
     "87b main:1006"),

    # ---- #92 + #93 ---------------------------------------------------------
    ("main.tex",
     "Why an autoregressive evaluator should find this easily is not a\n"
     "measurement but an observation about how $\\Delta$ is built: the evaluator's\n"
     "factorisation runs in the order under test, so the authored arrangement is\n"
     "the one its context windows were built for.  We do not compare that against\n"
     "a masked evaluator, because $\\Delta$ does not exist for one\n"
     "(Section~\\ref{sec:scope}).",
     "Why an autoregressive evaluator should rank the authored arrangement above\n"
     "most rearrangements is not a measurement but an observation about how\n"
     "$\\Delta$ is built: the evaluator's factorisation runs in the order under\n"
     "test, so the authored arrangement is the one its conditionals condition on.",
     "92+93 main:1019"),

    # ---- #94 + #95 ---------------------------------------------------------
    ("main.tex",
     "The same observation applies at the other end.  Every passage in these corpora was emitted left to right",
     "The same applies to the model that produced the text, as against the one\n"
     "scoring it.  Every passage in these corpora was emitted left to right",
     "94 main:1026"),

    ("main.tex",
     "What the data can say is how far the component\n"
     "depends on which model did the emitting: across the \\AuthoredCorpNGen\\\n"
     "generators the authored component of a single evaluator spans\n"
     "\\AuthoredCorpSpreadSteps\\ steps of the $1/n!$ grid for the median\n"
     "evaluator, and \\AuthoredCorpSpreadMax\\ for the worst.",
     "What the data can say is how far the component\n"
     "depends on which model did the emitting.  Each of the \\AuthoredCorpNGen\\ corpora came\n"
     "from a different generator, so holding the evaluator fixed and reading\n"
     "across corpora varies the generator and nothing else; this is a spread\n"
     "across corpora and not a movement along the AR ladder, which is what\n"
     "Table~\\ref{tab:decomposition} reports.  The authored component of a single\n"
     "evaluator spans \\AuthoredCorpSpreadSteps\\ steps of the $1/n!$ grid for the\n"
     "median evaluator, and \\AuthoredCorpSpreadMax\\ for the worst.",
     "95 main:1035",
     "batch 29 (cold read)"),

    # ---- #96 ---------------------------------------------------------------
    ("main.tex",
     "This reaches the authored component and stops there.  The causal component\n"
     "is a difference between two groups produced the same way, so an effect\n"
     "common to both subtracts out of it, and\n"
     "Section~\\ref{sec:fbdef}'s identity holds whatever produced the text.",
     "This reaches the authored component and stops there.  The causal component\n"
     "is a difference between two groups produced the same way, so an effect\n"
     "common to both subtracts out of it.",
     "96 main:1044"),
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
            print(f"  skip  {label:<18} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                # A later batch rewrote this passage, so on a re-run neither
                # the old text nor this batch's own replacement is here.
                print(f"  pass  {label:<18} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<18} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<18} {name}")
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
    print("batch 10: Section 4")
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
