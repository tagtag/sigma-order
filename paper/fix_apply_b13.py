#!/usr/bin/env python3
"""Batch 13: Section 5.4 -- #114 #120 #124 #125 #126(c) #127 #128 #129
#132 #133 #138 #139 #140 #141 #142 #143.

  #114  "A AR ladder" -> "An AR ladder".
  #120  "that quantity is measured below" -- name it.
  #124  the correlations are Spearman's and the section never says so
        before relying on the fact.
  #125  "the measurement says it is not" -- put its grounds in the sentence.
  #126(c) "the extreme arrangement" survives here.
  #127  "is not a detail" -> says what it is instead.
  #128  "over the TrendCapSpan-fold span of parameters covered here" and
        "runs from 20% to 15%" -- name the ends, and say that this is a
        fall and not a rise.
  #129  "the whole of that rho comes from the smallest evaluator, and the
        remaining four sit within one point of each other" is a claim about
        what survives removing that rung, so measure it.
  #132  "a stronger evaluator means one thing and is measured by one
        quantity" -- name both; and "stays at 1--2 steps of the grid" --
        say what is 1-2 steps.
  #133  "and the trend is offered as such" -- as what.
  #138  "the two differ by close to an order of magnitude" -- which two.
  #139  "the exact one is bounded below" -- give the bound and where it
        comes from.
  #140  say why the p is two-sided when the section argues one direction.
  #141  "so this is the second-smallest value available and not a small
        one" is a tautology as written.
  #142  "what the published model sizes afford" -- it is what this paper
        measured, and "model sizes" is parameter count.
  #143  "this AR ladder is able to establish a trend and is not able to
        establish the absence of one" -- state it as the general fact that
        failing to reject is not evidence of absence.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b13.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #132 + #120 -------------------------------------------------------
    ("sec_decomp.tex",
     "Throughout this paper a \\emph{stronger} evaluator means one thing and is\n"
     "measured by one quantity: how far it ranks a text's own arrangement above\n"
     "the rearrangements of the same sentences, which is the authored component of\n"
     "Eq.~\\eqref{eq:auth}.  It does not mean more sensitive to causal order;\n"
     "that quantity is measured below and stays at\n"
     "\\CausalCompStepsMin--\\CausalCompStepsMax\\ steps of the grid.",
     "Throughout this paper a \\emph{stronger} evaluator means one thing: one that\n"
     "ranks a text's own arrangement further above the rearrangements of the same\n"
     "sentences.  The quantity that measures it is the authored component of\n"
     "Eq.~\\eqref{eq:auth}.  It does not mean more sensitive to causal order.  That\n"
     "is the causal component of Eq.~\\eqref{eq:caus}, measured below, and it stays\n"
     "at \\CausalCompStepsMin--\\CausalCompStepsMax\\ steps of the $1/n!$ grid.",
     "132+120 decomp:228"),

    # ---- #124 -------------------------------------------------------------
    ("sec_decomp.tex",
     "(Section~\\ref{sec:limitations} says what that costs).  Because Spearman uses only ranks and the",
     "(Section~\\ref{sec:limitations} says what that costs).  Every $\\rho$ in this\n"
     "paper is Spearman's rank correlation.  Because it uses only ranks and the",
     "124 decomp:235"),

    # ---- #125 -------------------------------------------------------------
    ("sec_decomp.tex",
     "Whether that ceiling is being approached is a\nmeasurement, and the measurement says it is not.",
     "Whether that ceiling is being approached is a\n"
     "measurement, and the measurement says it is not: counted on the group the\n"
     "component is defined on, the fraction at the maximum falls along the AR\n"
     "ladder rather than rising.",
     "125 decomp:245",
     "batch 29 (cold read)"),

    # ---- #126(c) + #127 ----------------------------------------------------
    ("sec_decomp.tex",
     "The fraction of texts whose authored arrangement is already the extreme\n"
     "arrangement of its own permutation set is the natural statistic for it, and\n"
     "the group it is counted on is not a detail: the component it would be\n"
     "evidence about --- Eq.~\\eqref{eq:auth} --- is defined on the non-causal\n"
     "texts.",
     "The fraction of texts whose authored arrangement is already the strict\n"
     "maximum of its own permutation set is the natural statistic for it, and the\n"
     "group it is counted on decides what it is evidence about: the component in\n"
     "question --- Eq.~\\eqref{eq:auth} --- is defined on the non-causal texts.",
     "126c+127 decomp:249"),

    # ---- #128 + #129 -------------------------------------------------------
    ("sec_decomp.tex",
     "Counted there, over the \\TrendCapSpan$\\times$ span of parameters\n"
     "covered here, it runs from $\\CeilNGPTtwo\\%$ to $\\CeilNQwen\\%$ and\n"
     "establishes no trend, $\\rho = \\TrendCeilNRho$ ($p = \\TrendCeilNP$, exact\n"
     "rank null, $n = \\TrendNEval$); the whole of that $\\rho$ comes from the\n"
     "smallest evaluator, and the remaining four sit within one point of each\n"
     "other.",
     "Counted there, from \\texttt{gpt2} at $\\ParamsGPTtwo$ to\n"
     "\\texttt{Qwen3-4B-Base} at $\\ParamsQwen$, it goes from $\\CeilNGPTtwo\\%$ to\n"
     "$\\CeilNQwen\\%$ --- not up but down, at the levels measured --- and\n"
     "establishes no trend, $\\rho = \\TrendCeilNRho$ ($p = \\TrendCeilNP$, exact\n"
     "rank null, $n = \\TrendNEval$).  Dropping the smallest evaluator leaves\n"
     "$\\rho = \\TrendCeilNDropRho$ on the remaining \\TrendCeilNDropNEval\\ rungs\n"
     "($p = \\TrendCeilNDropP$), so what ordering there is rests on that one rung.",
     "128+129 decomp:253"),

    # ---- #138 + #139 + #140 + #141 ----------------------------------------
    ("sec_decomp.tex",
     "The $p$ is taken from it rather than from the usual asymptotic\n"
     "approximation because at $n = \\TrendNEval$ the two differ by close to an\n"
     "order of magnitude, and the exact one is bounded below: no such null on\n"
     "\\TrendNEval\\ points can return a two-sided $p$ smaller than $\\TrendPFloor$,\n"
     "so this is the second-smallest value available and not a small one.  A\n"
     "AR ladder of \\TrendNEval\\ is what the published model sizes afford, and the\n"
     "trend is offered as such.",
     "The $p$ is taken from it rather than from the usual asymptotic\n"
     "approximation because at $n = \\TrendNEval$ the exact $p$ and the asymptotic\n"
     "one differ by close to an order of magnitude.  The exact one is also bounded\n"
     "below: only $2$ of the $\\TrendNEval! = 120$ relabellings are as extreme as a\n"
     "perfect ordering, so the smallest two-sided $p$ it can return is\n"
     "$\\TrendPFloor$.  A $p$ at or near that bound therefore says that the\n"
     "ordering is as monotone as \\TrendNEval\\ points allow, and says nothing about\n"
     "how large the underlying change is.  The $p$ is two-sided throughout: this\n"
     "section argues about one direction, but the test is not told which, so\n"
     "nothing here is bought by assuming it.  An AR ladder of \\TrendNEval\\ rungs\n"
     "is what this paper measured, not the full range of published parameter\n"
     "counts, and any trend on it is offered as a trend over those\n"
     "\\TrendNEval\\ points.",
     "138+139+140+141+142+114+133 decomp:273"),

    # ---- #143 -------------------------------------------------------------
    ("sec_decomp.tex",
     "A null with\n$\\TrendNEval!$ points can only reject for a near-perfect monotone relation,\n"
     "so this AR ladder is able to establish a trend and is not able to establish the\n"
     "absence of one.",
     "A null with\n$\\TrendNEval!$ relabellings can only reject for a near-perfect monotone\n"
     "relation, so this AR ladder can establish a trend.  It cannot establish that\n"
     "there is none: failing to reject a null is not evidence that the null is\n"
     "true, and at this $n$ it is barely evidence at all.",
     "143 decomp:300"),
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
            print(f"  skip  {label:<34} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                # A later batch rewrote this passage, so on a re-run neither
                # the old text nor this batch's own replacement is here.
                print(f"  pass  {label:<34} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<34} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<34} {name}")
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
    print("batch 13: Section 5.4")
    print("-" * 64)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 64)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 64)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
