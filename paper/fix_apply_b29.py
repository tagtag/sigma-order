#!/usr/bin/env python3
"""Batch 29: the cold-read findings, #227-#247.

A reader who already knew the paper read it once through and reported the
places where knowing it was not enough to get past a sentence.  Everything
below was checked against the source before being written.  Seven of these
are defects the #69-#226 pass introduced; they are marked (mine).

  #227  The paper gives two different counts of its own negative result.
        Section 6.3: "The two negative results in this paper", one about
        Delta and one about sigma.  Section 7, which is the last thing read:
        "negative in three ways ... three readings of Delta", with sigma
        outside the count.  A reader who finishes the paper leaves with the
        count that excludes sigma.  Section 7 now states the two first and
        presents its three as a subdivision of the Delta one.
  #228  Abstract: "The decomposition referred to that zero" -- the nearest
        zero is the centre of the permutation set two sentences up; the
        0.50 null is meant.
  #229  Section 1.1 poses three questions and Section 1.2 draws three
        consequences, both numbered First/Second/Third, and the back
        references ("The third is a question about Delta", "the three
        questions above", "\\emph{The third.}") do not say which triple.
  #230  "at a block length of one" -- one what.
  #231  "A zero of a third kind" -- the two before it are not numbered.
  #232  (mine, #89) "bounded above by +0.50 ... it is already +0.354 of
        that" reads as a fraction of +0.50.  It is an absolute value.
  #233  (mine, #95) "this is a spread across corpora and not a movement
        along the AR ladder, which is what Table 2 reports" -- "which" can
        attach to either branch, and the two numbers that follow are not in
        Table 2.
  #234  (mine, #115) "Table 4 shows those cells, and 0.80, being the
        threshold ..., does not" -- the verb is elided and the subject is a
        number.
  #235  Section 6.4's heading says "this masked evaluator" with no
        antecedent inside it.
  #236  The Section 2.2 contrast table has a row "its zero comes from" with
        the Delta column filled, while the subtitle and Section 4.2 say
        Delta has no zero.  What that row gives is a reference point.
  #237  Table 1's caption says "in 5 cells of this table, every one of them
        gpt-2" -- every row of that table is gpt2, so the clause implies a
        contrast set that is not there.
  #238  "nowhere is it positive to any degree" is false: the same table
        prints +0.050 and +0.078.
  #239  Section 2.2 says Eq.(4) "makes sigma identically zero for every
        model whose conditionals come from a joint, while Delta for those
        same models is not identically zero" and four lines later "Neither
        quantity is evaluable on the other's class".  The first reads sigma
        on autoregressive models, which #144 settled it cannot be.
  #240  (mine, #103) "the causal component is +0.042 at both ends and does
        not move between them" -- Table 2 prints +0.083 at gpt2-medium.
  #241  Section 6.1 "The value range of sigma contains no property of the
        text" forbids the measurement Section 6.2 then makes.  What is
        meant is the magnitude, not where one arrangement falls among the
        rearrangements of one text.
  #242  Eq.(auth)'s "authored component" is defined in Section 3.4 under
        Delta and used in Section 6.3 under sigma without saying that the
        definition is of a midrank and so applies to either.
  #243  (mine, #191) Section 7 announces "three readings of Delta" and then
        gives the third a different subject.
  #244  (mine, #91) and #245 (mine, #125): "falls rather than rises along
        the AR ladder" asserts a direction for the quantity Section 5.4
        reports as establishing no trend, which is what Section 5.4's own
        rule forbids.
  #246  (mine, #90) "no result on this AR ladder could have reached 0.05 by
        a margin" -- what "by a margin" qualifies.
  #247  The median midranks 0.854 and 0.938 are given with no table
        reference; they are in Table 4.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b29.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #227 -------------------------------------------------------------
    ("main.tex",
     "Our conclusion is negative in three ways.  These are three readings of $\\Delta$: as a reversal, as a quantity, and as\n"
     "a test.  They are not a restatement of the three consequences of",
     "This paper's conclusion is negative in two ways, one for each quantity\n"
     "(Section~\\ref{sec:fbresult}).  Under $\\Delta$ the two label groups do\n"
     "separate, but these corpora cannot say what they are separated by; under\n"
     "$\\sigma$ a non-zero reading reports the masked evaluator's incompatibility\n"
     "and not the text.  The first of the two has three parts, and the rest of\n"
     "this section takes them in turn.  These are three readings of $\\Delta$: as a\n"
     "reversal, as a quantity, and as a test.  They are not a restatement of the\n"
     "three consequences of",
     "227 sec7 opening",
     "batch 31 (second cold read)"),

    ("main.tex",
     "The second and third conclusions rest on different things from the case\n"
     "about $\\sigma$, and the difference matters more than it looks.  Those two\n"
     "are empirical: a share that is small and unresolved, and sets with no\n"
     "criterion.  (The first is not, which is the point of putting it first.)",
     "The second and third readings rest on different things from the case\n"
     "about $\\sigma$, and the difference matters more than it looks.  Those two\n"
     "are empirical: a share that is small and unresolved, and sets with no\n"
     "criterion.  (The reading as a reversal is not, which is the point of\n"
     "putting it first.)",
     "227b sec7 later"),

    # ---- #228 -------------------------------------------------------------
    ("main.tex",
     "The\ndecomposition referred to that zero does use them.",
     "The\ndecomposition referred to that $0.50$ null does use them.",
     "228 abstract"),

    # ---- #229 -------------------------------------------------------------
    ("sec_intro.tex",
     "The third is a question about $\\Delta$, and a different measurement answers\nit in part without settling it.",
     "The third of the three, about $\\Delta$, is answered in part by a different\nmeasurement without being settled.",
     "229a intro:88"),

    ("sec_intro.tex",
     "The first and the third of the three questions above therefore have\nanswers, and they rest on different things.",
     "The first and the third of Ref.~\\cite{sagawa2026}'s three open points\n"
     "therefore have answers here, and they rest on different things.",
     "229b intro:181"),

    ("sec_intro.tex",
     "\\emph{The third.}  The separation \\emph{can} be carried out on $\\Delta$,",
     "\\emph{The open point about $\\Delta$.}  The separation \\emph{can} be carried\nout on $\\Delta$,",
     "229c intro:184"),

    # ---- #230 -------------------------------------------------------------
    ("main.tex",
     "at a\nblock length of one the backward measure is derived from the protocol",
     "when the blocks are single tokens the backward measure is derived from the\nprotocol",
     "230 main:456"),

    # ---- #231 -------------------------------------------------------------
    ("main.tex",
     "A zero of a third kind is available\nwithout either reversal doing the work.",
     "A third reference point is available without either reversal doing the\nwork.",
     "231 main:495"),

    # ---- #232 (mine) -------------------------------------------------------
    ("main.tex",
     "At $\\ParamsGPTtwo$ it is already $\\AuthoredGPTtwo$ of that, and\n"
     "over a $\\TrendCapSpan$-fold span of parameter count it ends at\n"
     "$\\AuthoredQwen$:",
     "At $\\ParamsGPTtwo$ it already stands at $\\AuthoredGPTtwo$, and\n"
     "over a $\\TrendCapSpan$-fold span of parameter count it ends at\n"
     "$\\AuthoredQwen$:",
     "232 main:999 (mine, #89)"),

    # ---- #233 (mine) + #247 ------------------------------------------------
    ("main.tex",
     "this is a spread\n"
     "across corpora and not a movement along the AR ladder, which is what\n"
     "Table~\\ref{tab:decomposition} reports.  The authored component of a single\n"
     "evaluator spans \\AuthoredCorpSpreadSteps\\ steps of the $1/n!$ grid for the\n"
     "median evaluator, and \\AuthoredCorpSpreadMax\\ for the worst.",
     "the spread\n"
     "read this way is across corpora, where Table~\\ref{tab:decomposition} reports\n"
     "movement along the AR ladder.  Taken over the corpora, the authored\n"
     "component of a single evaluator spans \\AuthoredCorpSpreadSteps\\ steps of\n"
     "the $1/n!$ grid for the median evaluator and \\AuthoredCorpSpreadMax\\ for\n"
     "the worst.",
     "233 main:1038 (mine, #95)",
     "batch 42 (#265)"),

    ("main.tex",
     "the median midrank is\n"
     "$\\MedPctNoncausal$ on the non-causal texts and $\\MedPctCausal$ on the causal\n"
     "ones, against a null of $0.50$;",
     "the median midrank is\n"
     "$\\MedPctNoncausal$ on the non-causal texts and $\\MedPctCausal$ on the causal\n"
     "ones, against a null of $0.50$;",
     "247 main:1019"),

    # ---- #234 (mine) -------------------------------------------------------
    ("sec_decomp.tex",
     "Table~\\ref{tab:sweep}\n"
     "shows those cells, and $\\TailOnsetThr$, being the threshold at which the\n"
     "\\emph{worst} evaluator first passes a point, does not.",
     "Table~\\ref{tab:sweep}\n"
     "shows those cells.  The threshold $\\TailOnsetThr$ does not show them,\n"
     "because it is the threshold at which the \\emph{worst} evaluator first\n"
     "passes a point.",
     "234 decomp:132 (mine, #115)"),

    # ---- #235 -------------------------------------------------------------
    ("sec_truesigma.tex",
     "\\subsection{The mask rate this masked evaluator was trained at}",
     "\\subsection{The mask rate \\texttt{bert-base} was trained at}",
     "235 true:352 heading"),

    # ---- #236 -------------------------------------------------------------
    ("main.tex",
     "its zero comes from & the permutation antisymmetry,",
     "its reference point & the permutation antisymmetry,",
     "236 contrast table"),

    # ---- #237 + #238 -------------------------------------------------------
    ("main.tex",
     "\\NTokNegARTot\\ cells of this table, every one of them \\textsc{gpt-2}, and\nnegligible in the rest.",
     "\\NTokNegARTot\\ cells of this table, and small and positive in the rest.",
     "237 tab:token caption"),

    ("main.tex",
     "is \\emph{negative}, the non-causal texts scoring higher, in\n"
     "\\NTokNegAR\\ of the \\NTokNegARTot\\ cells, and negligible in the rest:\n"
     "nowhere is it positive to any degree.",
     "is \\emph{negative}, the non-causal texts scoring higher, in\n"
     "\\NTokNegAR\\ of the \\NTokNegARTot\\ cells; in the other two it is positive\n"
     "but small, $+0.050$ and $+0.078$ (Table~\\ref{tab:token}).",
     "238 main:334"),

    # ---- #239 -------------------------------------------------------------
    ("main.tex",
     "Equation~\\eqref{eq:fbzero} of\n"
     "Section~\\ref{sec:fbdef} makes $\\sigma$ identically zero for every model\n"
     "whose conditionals come from a joint, while $\\Delta$ for those same models\n"
     "is not identically zero, taking a value that varies from text to text ---\n"
     "as sharp a separation as two quantities can have.",
     "Equation~\\eqref{eq:fbzero} of\n"
     "Section~\\ref{sec:fbdef} makes $\\sigma$ identically zero for a masked\n"
     "evaluator whose conditionals derive from one joint, while $\\Delta$ on an\n"
     "autoregressive evaluator, whose factorisation always supplies one, is not\n"
     "identically zero and takes a value that varies from text to text --- as\n"
     "sharp a separation as two quantities can have.",
     "239 main:595"),

    # ---- #240 (mine) -------------------------------------------------------
    ("sec_decomp.tex",
     "the causal component is $\\CausalGPTtwo$ at both ends and\ndoes not move between them.",
     "the causal component is $\\CausalGPTtwo$ at both ends; it is not monotone\n"
     "between them (Table~\\ref{tab:decomposition}).",
     "240 decomp:24 (mine, #103)"),

    # ---- #241 -------------------------------------------------------------
    ("sec_truesigma.tex",
     "The value range of $\\sigma$ contains no\nproperty of the text.",
     "The size of a non-zero $\\sigma$ is therefore\n"
     "not a property of the text.  Where one arrangement of a text falls among\n"
     "the rearrangements of that same text is a separate question, and\n"
     "Section~\\ref{sec:fbrank} is where it is asked.",
     "241 true:35"),

    # ---- #242 -------------------------------------------------------------
    ("sec_truesigma.tex",
     "Under \\texttt{LLaDA} the authored component of Eq.~\\eqref{eq:auth}, read\n"
     "under $\\sigma$, is $\\FbAuthoredLLaDA$:",
     "Equation~\\eqref{eq:auth} is defined on midranks and says nothing about\n"
     "which quantity produced them, so it reads under $\\sigma$ exactly as it does\n"
     "under $\\Delta$.  Under \\texttt{LLaDA} the authored component so read is\n"
     "$\\FbAuthoredLLaDA$:",
     "242 true:164"),

    # ---- #243 (mine) -------------------------------------------------------
    ("main.tex",
     "As a \\emph{test for causal structure}, these corpora cannot decide whether\n"
     "what $\\Delta$ separates is causal structure.  It does separate the two\n"
     "prompt-defined sets, in a fixed",
     "As a \\emph{test for causal structure}, $\\Delta$ cannot be read as one on\n"
     "these corpora, which cannot decide whether what it separates is causal\n"
     "structure.  It does separate the two prompt-defined sets, in a fixed",
     "243 main:1304 (mine, #191)",
     "batch 31 (second cold read)"),

    # ---- #244 (mine) -------------------------------------------------------
    ("main.tex",
     "Counted on the non-causal group, that fraction\nfalls rather than rises along the AR ladder, from $\\CeilNGPTtwo\\%$ to\n$\\CeilNQwen\\%$.",
     "Counted on the non-causal group, that fraction\n"
     "is $\\CeilNGPTtwo\\%$ at the bottom of the AR ladder and $\\CeilNQwen\\%$ at\n"
     "the top, and establishes no trend either way\n"
     "(Section~\\ref{sec:window}).",
     "244 main:1009 (mine, #91)"),

    # ---- #245 (mine) -------------------------------------------------------
    ("sec_decomp.tex",
     "measurement, and the measurement says it is not: counted on the group the\n"
     "component is defined on, the fraction at the maximum falls along the AR\n"
     "ladder rather than rising.",
     "measurement, and the measurement does not show it being approached:\n"
     "counted on the group the component is defined on, the fraction at the\n"
     "maximum is no higher at the top of the AR ladder than at the bottom.",
     "245 decomp:251 (mine, #125)"),

    # ---- #246 (mine) -------------------------------------------------------
    ("main.tex",
     "exact rank null over \\TrendNEval\\ evaluators; at that $n$ the smallest\n"
     "attainable two-sided $p$ is $\\TrendPFloor$, so no result on this AR ladder\n"
     "could have reached $0.05$ by a margin).",
     "exact rank null over \\TrendNEval\\ evaluators).  At that $n$ the smallest\n"
     "attainable two-sided $p$ is $\\TrendPFloor$, so the only $p$ this AR ladder\n"
     "can put below $0.05$ is $\\TrendPFloor$ itself: a result here either reaches\n"
     "that value or establishes nothing.",
     "246 main:1004 (mine, #90)"),
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
            print(f"  skip  {label:<30} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
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
    print("batch 29: the cold-read findings, #227-#247")
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
