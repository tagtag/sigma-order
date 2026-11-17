#!/usr/bin/env python3
"""Batch 36: #255 -- Eq.(fb) compares two assembly orders; it is not a path
against its time reverse.

A reader's objection, and it is right.  Both evaluations of Eq.(aoar) run
from the empty sequence to the same completed text: left-to-right fills
positions 1, 2, ..., L and right-to-left fills L, L-1, ..., 1, and for two
tokens those are the paths

    {} -> (x1) -> (x1,x2)      and      {} -> (x2) -> (x1,x2) .

They share an initial state and a final state, so neither is the time
reverse of the other -- the time reverse of the first empties the sequence
rather than filling it.  Calling Eq.(fb) "the forward path against its
reverse" and "an entropy production in the sense of Jarzynski, Crooks and
Seifert" claims a correspondence that is not there, and claims it in a paper
whose subject is a correspondence that is not there.  E[L sigma] = D_KL is
then an identity between two generation orders and not a fluctuation
theorem.

Nothing in the paper's argument needs the reading.  Eq.(fbzero) -- sigma
vanishes whenever the conditionals come from a joint -- follows from the
any-order chain rule alone, and the conclusion it supports, that a non-zero
sigma reports the evaluator's incompatibility rather than the text, is if
anything stronger once sigma is not an entropy production at all.  The
quantity in this paper that is one is Appendix A's sigma_EP, whose Glauber
chain has a defined time reversal.

So the thermodynamic identification goes, in the five places that make it,
and the subtitle stops calling sigma an entropy production.  The main title
is untouched: "reversing the text is not reversing the path" is a claim
about Delta, it is true, and Appendix A is where the path is reversed.
Section 7's wording already said "the order in which a model assembles" and
needed no change.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b36.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- the title ---------------------------------------------------------
    ("main.tex",
     "% and not between a path and its reverse -- and the subtitle carries what\n"
     "% each of the two quantities lacks.  Section 1's own note explains why that\n"
     "% section still builds to the claim rather than opening with it.\n",
     "% and not between a path and its reverse -- and the subtitle carries what\n"
     "% each of the two quantities lacks.  Section 1's own note explains why that\n"
     "% section still builds to the claim rather than opening with it.\n"
     "%\n"
     "% The subtitle read \"an entropy production that is identically zero\" until\n"
     "% a reader objected that both orders of Eq.(fb) run from the empty sequence\n"
     "% to the same text, so neither is the time reverse of the other.  The\n"
     "% objection is right.  The identity does not depend on the reading, and the\n"
     "% quantity here that is an entropy production is Appendix A's sigma_EP.\n"
     "% The main title is a claim about Delta and is unaffected.\n",
     "255 title note"),

    ("main.tex",
     "\\large a fixed-text measure without a zero, and an entropy production\n"
     "that is identically zero}",
     "\\large a fixed-text measure without a zero, and an order comparison\n"
     "that vanishes identically}",
     "255 subtitle",
     "batch 38 (#260)"),

    # ---- the notation key at the head of main.tex --------------------------
    ("main.tex",
     "%   \\sigma        Eq.~(5): the SAME text assembled in two directions.  This\n"
     "%                 is the entropy production, it is identically zero for any\n"
     "%                 model with a joint, and only a masked model can evaluate\n"
     "%                 it (Section~\\ref{sec:fbdef}).\n",
     "%   \\sigma        Eq.~(5): the SAME text assembled in two directions.  Both\n"
     "%                 orders run from the empty sequence to the same text, so it\n"
     "%                 is NOT a path against its reverse and the paper does not\n"
     "%                 call it an entropy production.  It is identically zero for\n"
     "%                 any model with a joint, and only a masked model can\n"
     "%                 evaluate it (Section~\\ref{sec:fbdef}).\n",
     "255 notation key"),

    # ---- abstract ----------------------------------------------------------
    ("main.tex",
     "text gives the forward path against its reverse,\n",
     "text gives two assembly orders of one text,\n",
     "255 abstract fb"),

    ("main.tex",
     "$\\sigma$ reverses\nthe path --- the order in which the model assembles the text, with the text\n"
     "held fixed --- and",
     "$\\sigma$ reverses\nthe order in which the model assembles the text, with the text\n"
     "held fixed, and",
     "255 abstract reverses"),

    # ---- Section 1.2, where the identification is made ---------------------
    ("sec_intro.tex",
     "the left-to-right and then the right-to-left order of one text gives the\n"
     "forward path and its reverse under a single model:",
     "the left-to-right and then the right-to-left order of one text gives the\n"
     "two assembly orders of that text under a single model:",
     "255 intro aoar"),

    ("sec_intro.tex",
     "This is an entropy production in the sense\n"
     "of~\\cite{jarzynski1997, crooks1999, seifert2012}: one trajectory\n"
     "weighed against its own reversal under the dynamics that produced it.",
     "This is not a trajectory weighed against its own reversal in the sense\n"
     "of~\\cite{jarzynski1997, crooks1999, seifert2012}.  Both orders run from\n"
     "the empty sequence to the same completed text, so neither is the time\n"
     "reverse of the other, and we do not claim Eq.~\\eqref{eq:fb} as an entropy\n"
     "production.  Nothing below needs it to be one: Eq.~\\eqref{eq:fbzero}\n"
     "follows from the any-order chain rule alone.  The quantity here that is an\n"
     "entropy production is $\\sigEP$ of Appendix~\\ref{sec:toy}, whose chain has\n"
     "a time reversal.",
     "255 intro not an EP"),

    # The paragraph that followed opened "Equation (fb) is that comparison",
    # pointing back at the path-against-its-reverse the paragraph above now
    # says it is not, and then repeated the identification in its own
    # apposition.
    ("sec_intro.tex",
     "Equation~\\eqref{eq:fb} is that comparison, constructed for a fixed text:\n"
     "one text assembled under a schedule and under its reverse, with a zero\n"
     "that holds on that text,\n"
     "which is what a masked evaluator makes possible and an autoregressive one\n"
     "does not (Section~\\ref{sec:notareversal}).",
     "Equation~\\eqref{eq:fb} is the comparison this paper does make,\n"
     "constructed for a fixed text: one text assembled under a schedule and\n"
     "under the opposite schedule, with a zero that holds on that text.\n"
     "That is what a masked evaluator makes possible and an autoregressive one\n"
     "does not (Section~\\ref{sec:notareversal}).",
     "255 intro that comparison"),

    # ---- Section 2.2, where the framework is said to apply -----------------
    ("main.tex",
     "an actual forward path against its reverse --- the same framework is what\n"
     "Appendix~\\ref{sec:toy} and Section~\\ref{sec:fbdef} use, and what turns the\n"
     "question into an identity.",
     "an actual forward path against its reverse --- the same framework is what\n"
     "Appendix~\\ref{sec:toy} uses.  Section~\\ref{sec:fbdef} does something\n"
     "weaker and sufficient: it compares two assembly orders of one text, which\n"
     "turns the question into an identity without a time reversal.",
     "255 sec2.2 framework"),

    ("main.tex",
     "reserve $\\sigma$ for the entropy production of Eq.~\\eqref{eq:fb} --- the",
     "reserve $\\sigma$ for the forward/backward quantity of Eq.~\\eqref{eq:fb} --- the",
     "255 sec2.2 reserve",
     "batch 38 (#260)"),

    # The paper no longer gives sigma that name, so "the name" had nothing
    # left to point at.
    ("main.tex",
     "reports is a separate question, and the answer is not what the name\n"
     "\\emph{entropy production} promises: Section~\\ref{sec:fbresult} measures it",
     "reports is a separate question, and the answer is not what a thermodynamic\n"
     "reading would promise: Section~\\ref{sec:fbresult} measures it",
     "255 sec2.2 promise"),

    # ---- Section 6.1, where the estimator is introduced --------------------
    ("sec_truesigma.tex",
     "backward, one token at a time from the right.  That is the forward path\n"
     "against its reverse, which is what the stochastic-thermodynamic definition\n"
     "asks for.",
     "backward, one token at a time from the right.  Both run from the empty\n"
     "sequence to the same completed text, so this is a comparison of assembly\n"
     "orders and not the path against its reverse that the\n"
     "stochastic-thermodynamic definition asks for.  The identity below does not\n"
     "need it to be one.",
     "255 sec6.1 estimator"),

    # ---- the two captions that name it an entropy production ---------------
    ("sec_truesigma.tex",
     "% The forward/backward entropy production, measured on masked evaluators.",
     "% The forward/backward quantity of Eq.(fb), measured on masked evaluators.",
     "255 sec6 header",
     "batch 38 (#260)"),

    ("sec_truesigma.tex",
     "\\caption{The forward/backward entropy production of\n"
     "Eq.~\\eqref{eq:fb}, read as the midrank",
     "\\caption{The forward/backward quantity of\n"
     "Eq.~\\eqref{eq:fb}, read as the midrank",
     "255 tab:fbrank caption",
     "batch 38 (#260)"),
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
    print("batch 36: Eq.(fb) is not a path against its reverse")
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
