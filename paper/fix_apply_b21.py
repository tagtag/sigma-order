#!/usr/bin/env python3
"""Batch 21: Section 7 -- #152(b) #160(c) #186 #188 #190 #191 #192 #193
#194 #195 #196.

  #152(b) "what that reports is the evaluator rather than the text" and
        "the evaluator, not the text" -- a property of the masked
        evaluator.
  #160(c) "the quantity it was standing in for is identically zero wherever
        the conditionals derive from a joint --- which is the case the
        thermodynamic reading is written for.  Where that fails it is
        defined and non-zero" is the claim #144 withdrew: for an
        autoregressive evaluator sigma is not evaluable, so it is not a
        case of Eq.(4) either way.
  #186  "the causal part" and "the bare fact that the passage came in some
        order" rename the two components of Eqs. (caus) and (auth).
  #188  Section 7 has both quantities in view, so every bare "evaluator"
        that means the Delta side says so.
  #190  "without reference to any judgement about causality" -- what it is
        independent of is what the labels represent.
  #191  "Delta is not evaluable on these corpora at all" borrows Section
        6.1's word for a different situation.  Delta is computable and does
        separate the groups; what these corpora cannot decide is whether
        what it separates is causal structure.
  #192  "a referent for the difference" -- name it.
  #193  "A value of Delta should not be quoted for a text, or compared
        between models" -- quoting and comparing are both possible; what is
        not available is the interpretation.
  #194  "that lower end" -- of what.
  #195  "we found no upper end to check" -- what upper end, and why one was
        expected.
  #196  "The framework these measurements belong to is built for
        autoregressive models" reads as though this paper's apparatus were,
        which the midrank is not: Section 6.2 applies it to masked
        evaluators.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b21.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #186 + #188 -------------------------------------------------------
    ("main.tex",
     "$\\ShareEvalMax\\%$ in midrank units), and the rest to the bare fact that the\n"
     "passage came in some order.  Read on the median, the causal part sits at\n"
     "\\CausalCompStepsMin--\\CausalCompStepsMax\\ steps of the grid at every rung\n"
     "of the AR ladder and does not move\nalong it (Section~\\ref{sec:window}).",
     "$\\ShareEvalMax\\%$ in midrank units), and the rest to the authored component\n"
     "of Eq.~\\eqref{eq:auth} --- the bare fact that the passage came in some\n"
     "order.  Read on the median, the causal component of Eq.~\\eqref{eq:caus}\n"
     "sits at \\CausalCompStepsMin--\\CausalCompStepsMax\\ steps of the grid at\n"
     "every rung of the AR ladder and does not move along it\n"
     "(Section~\\ref{sec:window}).",
     "186 main:1277"),

    ("main.tex",
     "Read in the tail it leaves the\ngrid floor and moves along the AR ladder.  No evaluator separates the labelled\n"
     "groups by more than\n$\\TailBelowOnsetMax$ points below a midrank of $\\TailOnsetThr$, and every\n"
     "one of them does above it.",
     "Read in the tail it leaves the\n"
     "grid floor and moves along the AR ladder.  No autoregressive evaluator\n"
     "separates the labelled groups by more than\n"
     "$\\TailBelowOnsetMax$ points below a midrank of $\\TailOnsetThr$, and every\n"
     "one of them does above it.",
     "188a main:1281",
     "batch 44 (#268)"),

    # ---- #190 -------------------------------------------------------------
    ("main.tex",
     "All of this is established without reference to any\njudgement about causality.",
     "All of this is established regardless of what the causal and non-causal\n"
     "labels actually represent.",
     "190 main:1296"),

    # ---- #191 -------------------------------------------------------------
    ("main.tex",
     "As a \\emph{test for causal structure}, $\\Delta$ is not evaluable on these\n"
     "corpora at all.  It does separate the two prompt-defined sets, in a fixed",
     "As a \\emph{test for causal structure}, these corpora cannot decide whether\n"
     "what $\\Delta$ separates is causal structure.  It does separate the two\n"
     "prompt-defined sets, in a fixed",
     "191 main:1299",
     "batch 29 (cold read)"),

    # ---- #192 -------------------------------------------------------------
    ("main.tex",
     "What neither statistic\nsupplies is a referent for the difference.",
     "What neither statistic\n"
     "supplies is an answer to what the difference is a difference in: whether\n"
     "what it separates is causal structure at all.",
     "192 main:1313"),

    # ---- #193 + #194 + #195 + #188(b) -------------------------------------
    ("main.tex",
     "The practical consequences are narrow and concrete.  A value of $\\Delta$ should\n"
     "not be quoted for a text, or compared between models.  Where a reference is\n"
     "needed, the permutation set of the text itself supplies one, and the midrank\n"
     "within it is unitless, at a cost of $n!$ scores rather\n"
     "than two.  An evaluator should be large enough that the authored arrangement is not\n"
     "at the null, and that lower end should be checked rather than assumed;\n"
     "we found no upper end to check, the fraction of non-causal texts at the\n"
     "strict maximum establishing no trend across the AR ladder\n"
     "(Section~\\ref{sec:window}).",
     "The practical consequences are narrow and concrete.  A bare value of\n"
     "$\\Delta$ should not be reported as an interpretable measurement of a text,\n"
     "nor compared between evaluators: on a fixed text it has neither an origin\n"
     "nor a stable scale (Section~\\ref{sec:capacity}).  Both are of course\n"
     "computable; what is missing is what they would mean.  Where a reference is\n"
     "needed, the permutation set of the text itself supplies one, and the midrank\n"
     "within it is unitless, at a cost of $n!$ scores rather than two.  An\n"
     "autoregressive evaluator should have parameters enough that the authored\n"
     "arrangement is not at the null, and that lower end --- the parameter count at\n"
     "which its midrank first clears $0.50$ --- should be checked rather than\n"
     "assumed.  We looked for an upper end as well, since the midrank is bounded\n"
     "by $1.00$ and a parameter count at which most authored arrangements are\n"
     "already the strict maximum would leave it nowhere to go; we found none, the\n"
     "fraction of non-causal texts at the strict maximum establishing no trend\n"
     "across the AR ladder (Section~\\ref{sec:window}).",
     "193+194+195+188b main:1332"),

    # ---- #196 + #152(b) + #160(c) ------------------------------------------
    ("main.tex",
     "Finally, on scope.  The framework these measurements belong to is built for\n"
     "autoregressive models, and the quantity it defines requires a single joint,\n"
     "which an autoregressive factorisation supplies and a masked model leaves to a\n"
     "choice of unmasking order.  That is not a gap to be filled with\n"
     "a substitute score: what a masked model supplies instead is a comparison\n"
     "with a zero on the text it is read from (Section~\\ref{sec:fbdef}), and what\n"
     "that reports is the\n"
     "evaluator rather than the text (Section~\\ref{sec:fbresult}).  The framework's\n"
     "empirical claim survives our re-measurement.  Its central quantity is\n"
     "unanchored in the fixed-text reading, and the quantity it was standing in\n"
     "for is identically zero\n"
     "wherever the conditionals derive from a joint --- which is the case the\n"
     "thermodynamic reading is written for.  Where that fails it is defined and\n"
     "non-zero, and Section~\\ref{sec:fbresult} measures what it reports there:\n"
     "the evaluator, not the text.",
     "Finally, on scope.  The framework under re-examination here --- the\n"
     "stochastic-thermodynamic framework of Ref.~\\cite{sagawa2026} --- is built\n"
     "for autoregressive models, and the quantity it defines requires a single\n"
     "joint, which an autoregressive factorisation supplies and a masked model\n"
     "leaves to a choice of unmasking order.  The apparatus of this paper is not\n"
     "so restricted: the permutation set and the midrank apply to any score, and\n"
     "Section~\\ref{sec:fbrank} uses them on masked evaluators.  That is not a gap\n"
     "to be filled with a substitute score: what a masked model supplies instead is\n"
     "a comparison with a zero on the text it is read from\n"
     "(Section~\\ref{sec:fbdef}), and what that reports is a property of the masked\n"
     "evaluator rather than of the text (Section~\\ref{sec:fbresult}).  The\n"
     "framework's empirical claim survives our re-measurement.  Its central\n"
     "quantity is unanchored in the fixed-text reading, and the quantity it was\n"
     "standing in for is not evaluable on an autoregressive evaluator at all\n"
     "(Section~\\ref{sec:truesigma}): an autoregressive evaluator cannot supply\n"
     "the conditionals Eq.~\\eqref{eq:aoar} asks for, so it is not a case of\n"
     "Eq.~\\eqref{eq:fbzero} either way.  On a masked evaluator the quantity is\n"
     "defined, and Section~\\ref{sec:fbresult} measures what it reports there: a\n"
     "property of the masked evaluator, not of the text.",
     "196+152b+160c main:1343",
     "batch 29 (cold read)"),
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
    print("batch 21: Section 7")
    print("-" * 56)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 56)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 56)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
