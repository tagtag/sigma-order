#!/usr/bin/env python3
"""Batch 8: Section 3.2 -- #71, #72, #73, #74, #75.

  #71  "sum_x P_pi(x) = 1" never says what x runs over.  It runs over the
        V^L sequences of the fixed length L.
  #72  The self-test sentence reads as a measurement on bert-base and
        LLaDA.  It is a test of the implementation of Eq.(aoar), run on a
        small exactly enumerable system, and "oracle" appears there for the
        first time without a definition.
  #73  "It supplies one for each pi" -- one what.  One P_pi of Eq.(aoar).
  #74  "report Delta only there" -- there is a framework, not a class of
        evaluator; say which evaluators.
  #75  Three passages describe a comparison this paper does not make and
        then withdraw it.  The withdrawal is itself the only trace of it
        left, so it goes; Section 4.2's closing sentence, which refers back
        to it, goes with it.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b8.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #75 (a): Section 3.1 ---------------------------------------------
    ("main.tex",
     "No evaluator appears in both sets, and none could.  A comparison of the\n"
     "two classes under $\\Delta$ was made in earlier work of ours and is\n"
     "withdrawn; Section~\\ref{sec:scope} says why, and the measurements remain in\n"
     "the repository.",
     "No evaluator appears in both sets, and none could: $\\Delta$ exists for the\n"
     "autoregressive evaluators and $\\sigma$ for the masked ones\n"
     "(Section~\\ref{sec:scope}).",
     "75a main:708"),

    # ---- #71 ---------------------------------------------------------------
    ("main.tex",
     "fixed the product telescopes over the tree of prefixes, so $\\sum_x\n"
     "P_\\pi(x) = 1$ provided only that each $p_\\theta(\\cdot \\mid \\text{prefix})$\n"
     "sums to one over the vocabulary.",
     "fixed the product telescopes over the tree of prefixes, so $\\sum_x\n"
     "P_\\pi(x) = 1$ --- the sum running over all $V^L$ sequences of the fixed\n"
     "length $L$ --- provided only that each\n"
     "$p_\\theta(\\cdot \\mid \\text{prefix})$ sums to one over the vocabulary.",
     "71 main:732"),

    # ---- #72 ---------------------------------------------------------------
    ("main.tex",
     "Consistency decides whether the different\n"
     "$\\pi$ agree, not whether each one normalises.  The accompanying self-test\n"
     "checks the implementation on both cases: $\\bigl|1 - \\sum_x P_\\pi(x)\\bigr|$\n"
     "is at most $\\AoarNormDev$ for a consistent oracle and $\\AoarNormDevInc$ for\n"
     "conditionals constructed to belong to no joint.",
     "Consistency decides whether the different\n"
     "$\\pi$ agree, not whether each one normalises.  The accompanying self-test\n"
     "checks our implementation of Eq.~\\eqref{eq:aoar}, not either masked\n"
     "evaluator: it runs on a system small enough to enumerate ($L = \\AoarL$\n"
     "sites, $V = \\AoarV$ symbols, $\\AoarStates$ sequences) and feeds it two sets\n"
     "of conditionals, an \\emph{oracle} --- conditionals read off a joint\n"
     "distribution written down in advance, so that they are consistent by\n"
     "construction --- and a set built to belong to no joint.  On both,\n"
     "$\\bigl|1 - \\sum_x P_\\pi(x)\\bigr|$ is at most $\\AoarNormDev$ and\n"
     "$\\AoarNormDevInc$ respectively.",
     "72 main:735"),

    # ---- #73 ---------------------------------------------------------------
    ("main.tex",
     "distribution.}  It supplies one for each $\\pi$, and $\\sigma$ is\n"
     "the measurement of how far two of them stand apart --- $\\sigma \\neq 0$ is\n"
     "exactly a certificate that they do not coincide.",
     "distribution.}  It supplies one $P_\\pi$ of Eq.~\\eqref{eq:aoar} for each\n"
     "unmasking order $\\pi$.  What $\\sigma$ measures is how far two of them stand\n"
     "apart: $\\sigma \\neq 0$ is exactly a certificate that they do not coincide.",
     "73 main:741"),

    # ---- #74 ---------------------------------------------------------------
    ("main.tex",
     "We therefore\nreport $\\Delta$ only there (Sections~\\ref{sec:authored}\n"
     "and~\\ref{sec:causal}), because a masked reading of it would be indexed by a",
     "We therefore\nreport $\\Delta$ only on autoregressive evaluators\n"
     "(Sections~\\ref{sec:authored} and~\\ref{sec:causal}), because a masked\n"
     "reading of it would be indexed by a",
     "74 main:753"),

    # ---- #75 (b): Section 3.2, the substitution paragraph -----------------
    ("main.tex",
     "One may of course evaluate the \\emph{shape} of Eq.~\\eqref{eq:delta} on a\n"
     "masked model by substituting some other number for $\\log P$.  We did\n"
     "exactly that, on masked evaluators, and concluded that the\n"
     "comparison with the autoregressive readings means nothing.  The construction of\n"
     "Section~\\ref{sec:blkord} does not notice the substitution, because it is\n"
     "score-agnostic: it asks only for a number per token sequence.",
     "One may of course evaluate the \\emph{shape} of Eq.~\\eqref{eq:delta} on a\n"
     "masked model by substituting some other number for $\\log P$.  The\n"
     "construction of Section~\\ref{sec:blkord} does not notice the substitution,\n"
     "because it is score-agnostic: it asks only for a number per token sequence.",
     "75b main:762"),

    ("main.tex",
     "The substitution also takes a quantity devised to\n"
     "work around the absence of a backward process and applies it to masked\n"
     "models, the only class for which a backward process exists.  Those\n"
     "measurements are retained in the repository and are not reported here.",
     "The substitution also takes a quantity devised to\n"
     "work around the absence of a backward process and applies it to masked\n"
     "models, the only class for which a backward process exists.",
     "75c main:769"),
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
            print(f"  skip  {label:<16} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                # A later batch rewrote this passage, so on a re-run neither
                # the old text nor this batch's own replacement is here.
                print(f"  pass  {label:<16} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<16} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<16} {name}")
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
    print("batch 8: Section 3.2 -- #71 #72 #73 #74 #75")
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
