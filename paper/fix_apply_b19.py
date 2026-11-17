#!/usr/bin/env python3
"""Batch 19: the end of Section 6.3 -- #167 #169 #170 #176 #177 #178 #179
#180 #181 #182.

  #176  "The two negative results in this paper" -- name them, and do not
        say Delta fails to separate the groups: it separates them in
        ContrastNRejecting of ContrastNCells cells.
  #177  "and nothing here needs to" -- what needs nothing.
  #178  "Nor does the sweep of Appendix A show the defect going away" --
        say what going away would look like and what it would be going
        away with.
  #179  "and the supporting statement has to be about sigma rather than
        about sigEP" -- say first why sigEP is in the sentence at all.
  #180  "The two are different functionals of one failure" treats the
        failure as an argument of the two quantities; what each takes as
        input is the evaluator's conditionals.
  #181  "What sigma itself does over the sweep is stay put" contradicts the
        sentence three lines later, which says a sweep of five points
        cannot establish that a quantity is constant.
  #167  The closing paragraph restates six numbers that Sections 4.2, 5.3
        and 5.4 have already given, and one point Section 5.1 makes.  The
        work it does is in its last sentence.
  #169  "they would survive being wrong about sigma entirely" -- wrong
        about what.
  #170  "On the authored arrangement they agree to the printed precision"
        -- what agrees.
  #182  "share no code beyond the chain rule itself" is false:
        block_sigma_fb.py imports load_texts and HFMaskedProvider from
        order_intervention.py.  And the agreement was checked only for
        LLaDA, because no direct bert-base run exists.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b19.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #176 -------------------------------------------------------------
    ("sec_truesigma.tex",
     "The two negative results in this paper are not of the same kind, and the\n"
     "distinction decides what either of them licenses.",
     "The two negative results in this paper are not of the same kind, and the\n"
     "distinction decides what either of them licenses.  Under $\\Delta$\n"
     "(Sections~\\ref{sec:authored} and~\\ref{sec:causal}) the two label groups do\n"
     "separate, in \\ContrastNRejecting\\ of \\ContrastNCells\\ cells.  What cannot be\n"
     "read off is the size of the part attributable to the causal label: it sits at\n"
     "the grid's resolution, and the groups have no criterion distinguishing them\n"
     "beyond the prompts that produced them.  Under $\\sigma$\n"
     "(this section) what a non-zero reading reports is the masked evaluator's\n"
     "incompatibility, by the identity, and not causal order.  The $\\Delta$\n"
     "result is empirical; the $\\sigma$ one follows from the identity.",
     "176 true:289"),

    # ---- #177 -------------------------------------------------------------
    ("sec_truesigma.tex",
     "We do not account for\nthat difference, and nothing here needs to ---",
     "We do not account for\nthat difference, and no claim in this paper needs to ---",
     "177 true:297"),

    # ---- #178 + #179 + #180 + #181 ----------------------------------------
    ("sec_truesigma.tex",
     "Nor does the sweep of Appendix~\\ref{sec:toy} show the defect going away,\n"
     "and the supporting statement has to be about $\\sigma$ rather than about\n"
     "$\\sigEP$.  The two are different functionals of one failure, and the sweep does not\n"
     "show them moving together: ranked against each other they give $\\rho =\n"
     "\\CtrlRhoXS$ at $p = \\CtrlPXS$, which establishes nothing either way at\n"
     "$n = \\CtrlNWidths$ --- the appendix says so in those terms, and what it\n"
     "does establish is the factor by which each changes; $\\sigEP$'s behaviour there licenses nothing about $\\sigma$.  What\n"
     "$\\sigma$ itself does over the sweep is stay put: $\\langle|\\sigma|\\rangle$\n"
     "runs between $\\CtrlSigAbsMin$ and $\\CtrlSigAbsMax$ across all\n"
     "$\\CtrlNWidths$ widths, so it is nowhere near zero at any of them.",
     "Nor does the sweep of Appendix~\\ref{sec:toy} show $\\sigma$ heading towards\n"
     "zero as the transformer width $d$ grows from $\\CtrlDMin$ to $\\CtrlDMax$.\n"
     "The appendix reports two quantities on that one sweep, $\\sigEP$ and\n"
     "$\\sigma$, which is why both are in view here; the statement that bears on\n"
     "this section has to be the one about $\\sigma$.  They are separate\n"
     "quantities, each computed from the evaluator's own conditionals, and what\n"
     "makes each of them non-zero is the same incompatibility --- but the\n"
     "behaviour of one does not follow from the behaviour of the other, and the\n"
     "sweep does not show them moving together: ranked against each other they\n"
     "give $\\rho = \\CtrlRhoXS$ at $p = \\CtrlPXS$, which establishes nothing\n"
     "either way at $n = \\CtrlNWidths$.  What $\\sigma$ does over the sweep is\n"
     "not approach zero: $\\langle|\\sigma|\\rangle$ runs between $\\CtrlSigAbsMin$\n"
     "and $\\CtrlSigAbsMax$ across all $\\CtrlNWidths$ widths.",
     "178+179+180+181 true:302",
     "batch 29 (cold read)"),

    # ---- #167 + #169 -------------------------------------------------------
    ("sec_truesigma.tex",
     "Measured, its magnitude grows rather than shrinks --- by a\n"
     "factor of $\\CapRatioMedian$ between the ends of the AR ladder,\n"
     "larger at the top in $\\CapNUp$ of $\\CapNCorpora$ corpora, with the sign of\n"
     "$\\Delta$ itself differing between the two ends in $\\CapNSign$\n"
     "(Section~\\ref{sec:capacity}).  The\n"
     "grounds for declining to read $\\Delta$ as a measurement of causal order are\n"
     "the ones given there and in Section~\\ref{sec:construct}: the share\n"
     "attributable to the labels is $\\ShareZMin\\%$ to $\\ShareZMax\\%$ in units\n"
     "with no ceiling, $\\ShareEvalMin\\%$ to $\\ShareEvalMax\\%$ on the midrank\n"
     "where it sits at one step of the grid, and the two label groups have no criterion\n"
     "distinguishing them beyond the prompts that produced them.  Those are\n"
     "empirical and they would survive being wrong about $\\sigma$ entirely.",
     "Measured, its magnitude grows rather than shrinks along the AR ladder\n"
     "(Section~\\ref{sec:capacity}).  The grounds for declining to read $\\Delta$ as\n"
     "a measurement of causal order are the ones given there, in\n"
     "Section~\\ref{sec:resolution} and in Section~\\ref{sec:construct}, and they\n"
     "are empirical: they would stand even if everything this section says about\n"
     "$\\sigma$ were wrong.",
     "167+169 true:318"),

    # ---- #170 + #182 -------------------------------------------------------
    ("sec_truesigma.tex",
     "These two constructions are implemented separately, in\n"
     "\\fn{order_intervention.py} and \\fn{block_sigma_fb.py}, and share\n"
     "no code beyond the chain rule itself.  On the authored arrangement they agree\n"
     "to the printed precision in all \\FbNCorpora\\ corpora, which is the\n"
     "check that the rank construction measures what the direct one does.",
     "The within-text reading and the unrearranged reading are computed by\n"
     "separate programs, \\fn{block_sigma_fb.py} and\n"
     "\\fn{order_intervention.py}.  They are not independent implementations: the\n"
     "first imports the text loader and the masked-model provider from the second,\n"
     "so what they share is the input path and the model interface, and what\n"
     "differs is the construction of $\\sigma$ itself.  On the authored\n"
     "arrangement the median $\\sigma$ they return agrees to the printed precision\n"
     "in all \\FbNCorpora\\ corpora, which is the check that the rank construction\n"
     "measures what the direct one does (\\fn{check_two_constructions.py}).  That\n"
     "check covers \\texttt{LLaDA} only: no direct run exists for\n"
     "\\texttt{bert-base}.",
     "170+182 true:334"),
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
            print(f"  skip  {label:<30} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                # A later batch rewrote this passage, so on a re-run neither
                # the old text nor this batch's own replacement is here.
                print(f"  pass  {label:<30} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<30} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<30} {name}")
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
    print("batch 19: the end of Section 6.3")
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
