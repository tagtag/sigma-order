#!/usr/bin/env python3
"""Batch 23: Section 8 -- #198 #200 #201 #202 #203 #204 #205(b) #207(b).

  #198  The item is headed "The authored component is not decomposed" but
        its body is about the authored arrangement.  The component is what
        is not decomposed, and the item holds for either model class
        because it is a fact about the corpora.
  #200  "The masked floor" is undefined, and the word "floor" is already
        doing three other jobs in this paper.  What is meant is the part of
        sigma common to every arrangement of one text, which the within-text
        rank cancels.
  #201  An addition the author asked for: say that the two controls were
        not computed, and why.
  #202  "the sampled set must be closed under reversal for Eq.(antisym) to
        hold" -- say what that requires and what is lost without it.
  #203  "A masked model supplies no single joint" holds when its
        conditionals are incompatible, not unconditionally; and "come from
        one joint P" is ambiguous between the value and the distribution.
  #204  "a free unmasking order with no counterpart in the physics" is too
        strong and contradicts Appendix A, which builds a Markov chain from
        masked conditionals and measures its reversibility.
  #205(b) The labelling caveat is Ref.~[1]'s own; the missing human-written
        control is not, and is not credited to it.
  #207(b) "Capacity and family are not fully separated" -- parameter count.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b23.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #205(b) -----------------------------------------------------------
    ("main.tex",
     "\\emph{The labels.}  Treated in Section~\\ref{sec:construct} rather than here,\n"
     "because it is not a caveat on the result but a limit on what the result can be\n"
     "about.",
     "\\emph{The labels.}  Treated in Section~\\ref{sec:construct} rather than here,\n"
     "because it is not a caveat on the result but a limit on what the result can be\n"
     "about.  Ref.~\\cite{sagawa2026} raises it for its own corpora first: the\n"
     "labels are fixed by the generation prompt rather than by a formal criterion,\n"
     "and it claims no general quantitative measure of causal structure on that\n"
     "basis~\\cite[Sec.~V~B]{sagawa2026}.",
     "205b sec8 labels"),

    # ---- #198 --------------------------------------------------------------
    ("main.tex",
     "\\emph{The authored component is not decomposed.}  The non-causal passages are\n"
     "coherent discourse, so what we call authored arrangement mixes topical\n"
     "continuity, backward pronoun resolution and the placement of new\n"
     "information.  Separating these would need text\nsets built for the purpose.",
     "\\emph{The authored component is not decomposed.}  The non-causal passages are\n"
     "coherent discourse, so what the authored component picks up mixes topical\n"
     "continuity, backward pronoun resolution and the placement of new\n"
     "information.  Separating these would need text sets built for the purpose.\n"
     "This is a fact about the corpora and not about either quantity: it holds for\n"
     "the component read under $\\Delta$ and for the one read under $\\sigma$\n"
     "alike.",
     "198 sec8 decomposition"),

    # ---- #200 + #201 -------------------------------------------------------
    ("main.tex",
     "\\emph{The masked floor is characterised only in the exactly solvable system.}\n"
     "It is the part of $\\sigma$ that no ordering of the content can explain, and\n"
     "Appendix~\\ref{sec:toy} is where it is measured.  Two controls on text remain: a corpus of sentences drawn from unrelated\n"
     "documents, which removes topical continuity, and a word-shuffled corpus, which\n"
     "removes syntax as well.  Their $\\sigma$ would bound it.",
     "\\emph{The text-independent part of $\\sigma$ is characterised only in the\n"
     "exactly solvable system.}  A masked evaluator returns a non-zero $\\sigma$\n"
     "because its conditionals derive from no single joint, and that is a property\n"
     "of the evaluator rather than of the text.  Part of what it contributes is\n"
     "therefore common to every arrangement of one text, and a rank taken within\n"
     "that text cancels it --- which is why the text results here are reported as\n"
     "midranks and not as magnitudes.  How large that common part is, is measured\n"
     "only in the exactly solvable system of Appendix~\\ref{sec:toy}, where the\n"
     "conditionals can be enumerated.  Two controls on text would bound it: a\n"
     "corpus of sentences drawn from unrelated documents, which removes topical\n"
     "continuity, and a word-shuffled corpus, which removes syntax as well.  We\n"
     "have not computed them: it is not obvious how to build controls whose\n"
     "$\\sigma$ bounds it in a meaningful way.",
     "200+201 sec8 masked floor"),

    # ---- #202 --------------------------------------------------------------
    ("main.tex",
     "Longer texts require sampling the permutation\n"
     "set, and the sampled set must be closed under reversal for\n"
     "Eq.~\\eqref{eq:antisym} to hold.",
     "Longer texts require sampling the permutation\n"
     "set, and the sample must be closed under reversal: if $\\pi$ is drawn then\n"
     "$\\pi\\circ\\mathrm{rev}$ has to be drawn too.  Otherwise the sampled values\n"
     "no longer come in the pairs $\\{d, -d\\}$ of Eq.~\\eqref{eq:antisym}, the set\n"
     "is not symmetric about zero, and the origin the construction exists to\n"
     "supply is lost.",
     "202 sec8 enumeration"),

    # ---- #203 + #204 -------------------------------------------------------
    ("main.tex",
     "\\emph{A masked model supplies no single joint}\n"
     "(Section~\\ref{sec:scope}), so $\\Delta$ has no masked counterpart and none is\n"
     "reported here.  The any-order chain rule does give a log-probability, at the\n"
     "price of a free unmasking order with no counterpart in the physics; that is\n"
     "the instrument of Section~\\ref{sec:fbdef}, and it answers a different\nquestion.",
     "\\emph{When its conditionals are incompatible, a masked model has no single\n"
     "joint accounting for all unmasking orders} (Section~\\ref{sec:scope}).\n"
     "Equation~\\eqref{eq:delta} requires its two terms to be $\\log P(x)$ and\n"
     "$\\log P(\\tilde{x})$ under one and the same joint $P$ --- a different $P$ for\n"
     "a different text is no obstacle, but two values read off two different\n"
     "distributions are not a $\\Delta$.  A masked model offers one $P_\\pi$ per\n"
     "unmasking order and does not single out which, so $\\Delta$ has no masked\n"
     "counterpart and none is reported here.  The any-order chain rule does give a\n"
     "log-probability, at the price of an unmasking order that the framework does\n"
     "not fix; that is the instrument of Section~\\ref{sec:fbdef}, and it answers a\n"
     "different question.",
     "203+204 sec8 no single joint",
     "batch 28 (glossary)"),

    # ---- #207(b) -----------------------------------------------------------
    ("main.tex",
     "\\emph{Capacity and family are not fully separated.}",
     "\\emph{Parameter count and family are not fully separated.}",
     "207b sec8 heading"),
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
    print("batch 23: Section 8")
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
