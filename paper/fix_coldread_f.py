r"""Sixth batch: the second independent read of the built PDF.

The heaviest one is mine, from the fourth batch.

 1. "Nothing separates the groups below a midrank of \TailOnsetThr", in
    four places including the abstract.  \TailOnsetThr is the first
    threshold at which the MINIMUM over evaluators exceeds one point, so
    below it the minimum is small and individual evaluators need not be:
    the same page prints +2 and +3 for \texttt{gpt2}.  The macro supports
    the converse statement -- from that threshold up, EVERY evaluator
    separates them by more than a point -- and the largest contrast below
    it is now measured instead of asserted away.

 2. "the median midrank is \MedPctNoncausal on the non-causal texts and
    \MedPctCausal on the causal ones", in a paragraph about one evaluator.
    Both are medians across the ladder; the first happens to coincide with
    \texttt{gpt2}'s and the second does not, so the pair reads as one
    evaluator's and does not reconcile with Table 2.

 3. The Table 2 caption still says Eq. (9) is "computed without reference
    to the causal labels".  Section 3.4 and Section 4 now say the opposite
    in as many words: it uses them to select its reference set.

 4. Section 1 still says "writer-chosen", which Section 3.4 explicitly
    disowns ("'authored' names the order a text came in and not an act of
    authorship") and every other site has dropped.

 5. Section 3.2 says the withdrawn comparison ran on three masked
    evaluators and names \texttt{bert-large} as the third; Figure 2's
    caption names two.  Which two is not something the paper records, so
    the caption stops enumerating rather than guess.

 6. tab_saturation formats the parameter count with p//1000, giving 1B for
    \texttt{gpt2-xl} where every other table gives 1.6B.  params_str()
    exists for exactly this and was not used here.

 7. The comparison table says Eq. (10) is measured "at one step of the
    grid"; everywhere else it is one to two steps, and the generated range
    exists.

 9. The gap/room column takes four distinct values and three of five rows
    sit on an endpoint of their own interval.  The paper polices this kind
    of resolution everywhere else and said nothing here.

11. "the order of the two groups is stable" is drawn from counts of the
    causal group against the NULL.  One cell has the causal group above
    the non-causal, and the same subsection says so two paragraphs later.

12. "both are statistics of the labelled contrast": one of the two is the
    causal group's own ceiling fraction, which references no other group.

13. The self-test oracle and Appendix A's system are described in the same
    words and the text says they are not the same thing.

14. The > 0.95 sweep column is the strict-maximum column: for n = 4 the
    only attainable midrank above 0.95 is 23.5/24.  Section 5.3 presents
    them as two cuts.  The duplication is now stated and asserted.

15. Two of the five references to an earlier version are commentary on the
    revision rather than on the measurements, and go.
"""
import io
import os
import sys

os.chdir(sys.argv[1])
N = 0


def rep(path, a, b, label, marker=None):
    global N
    assert a not in b or marker, f"{label}: b contains a; pass a marker"
    s = io.open(path, encoding="utf-8").read()
    if marker is not None:
        if marker in s:
            print(f"  (already) {label}")
            return
    elif s.count(a) == 0 and s.count(b) >= 1:
        print(f"  (already) {label}")
        return
    assert s.count(a) == 1, f"{label}: {s.count(a)} in {path}"
    io.open(path, "w", encoding="utf-8").write(s.replace(a, b))
    print(f"  {label}")
    N += 1


# =================================================== the generator, first
# 1: what the onset threshold is, and what the sweep shows below it.
rep("make_tables.py",
    r"""    if first is not None:
        mac("TailOnsetThr", f"{first:.2f}")""",
    r"""    if first is not None:
        mac("TailOnsetThr", f"{first:.2f}")
        # The threshold is where the WORST evaluator passes one point, so
        # below it the worst is small and the others need not be.  Four
        # sentences read it as "no evaluator differs by a point below
        # here" while the table beside them printed +2 and +3.  The honest
        # companion is the largest contrast any evaluator shows below the
        # onset, measured over the same sweep.
        below = [sweep[m][j] for m in models
                 for j, t in enumerate(TAIL_THRESHOLDS)
                 if t < first and len(sweep[m]) > j]
        if below:
            mac("TailBelowOnsetMax", f"{100 * max(below):.0f}")""",
    "1a: the largest contrast below the onset is measured",
    marker="TailBelowOnsetMax")

rep("make_tables.py",
    r"""                "TailSweepNThr", "TailOnsetThr",""",
    r"""                "TailSweepNThr", "TailOnsetThr", "TailBelowOnsetMax",""",
    "1b: registered",
    marker='"TailOnsetThr", "TailBelowOnsetMax"')

# 6: one formatter for the parameter count, not two.
rep("make_tables.py",
    r"""        ps = "--" if not p else (f"{p}M" if p < 1000 else f"{p//1000}B")""",
    r"""        # params_str, not a second formatter: p//1000 printed 1B for
        # gpt2-xl in this table while every other one printed 1.6B, and
        # the 13-fold span quoted in Section 3.1 is 1.6B/124M.
        ps = "--" if not p else params_str(model)""",
    "6: the saturation table uses the same parameter formatter as the rest")

# 9: the gap/room column's own resolution, measured like every other.
rep("make_tables.py",
    r"""    # The span and the common overlap, so the prose never has to name which
    # evaluator sits at an extreme: a superlative typed by hand goes stale the
    # moment the measurements change, and two of them already had.""",
    r"""    # This column is a median of \\NCorp per-corpus ratios, so it can only
    # take one of those \\NCorp values and its bootstrap interval can only
    # have endpoints among them.  That is a grid, and this paper refuses
    # every other grid-bound number the status of a measured size, so the
    # same question is asked here and the answer is printed.
    if all_ratios:
        mac("RatioNDistinct", str(len({f"{r:.2f}" for r in all_ratios})))
        mac("RatioNEval", str(len(all_ratios)))
    if all_ci:
        ends = {f"{v:.2f}" for lo, hi in all_ci for v in (lo, hi)}
        mac("RatioNDistinctEnds", str(len(ends)))
        mac("RatioNAtEnd", str(sum(
            1 for r, (lo, hi) in zip(all_ratios, all_ci)
            if f"{r:.2f}" in (f"{lo:.2f}", f"{hi:.2f}"))))
    # The span and the common overlap, so the prose never has to name which
    # evaluator sits at an extreme: a superlative typed by hand goes stale the
    # moment the measurements change, and two of them already had.""",
    "9a: the gap/room column's resolution is measured",
    marker="RatioNDistinctEnds")

rep("make_tables.py",
    r"""                "CausalCompCapLo", "CausalCompCapHi",""",
    r"""                "CausalCompCapLo", "CausalCompCapHi",
                "RatioNDistinct", "RatioNEval", "RatioNDistinctEnds",
                "RatioNAtEnd",""",
    "9b: registered",
    marker='"RatioNDistinct", "RatioNEval"')

# 14: the top sweep column and the strict-max column are one cut.
rep("make_tables.py",
    r"""    sw = [r"% generated by make_tables.py -- do not edit",""",
    r"""    # Which sweep thresholds are the strict-maximum cut in disguise.  For
    # n = 4 the attainable midranks are (k + 0.5)/24, so the only one above
    # 0.95 is 23.5/24 and "> 0.95" IS "strict maximum" -- Section 5.3
    # offered the two as different cuts and the table printed each pair
    # equal in all five rows.  Dropping the column would strand its
    # retirement entries, so the duplication is measured and named instead.
    have = [m for m in models if m in per_model]
    dupthr = None
    for j, t in enumerate(TAIL_THRESHOLDS):
        if not have:
            break
        if all(len(sweep.get(m, [])) > j
               and abs(100 * sweep[m][j] - per_model[m][0]) < 0.5
               for m in have):
            dupthr = t
            break
    if dupthr is not None:
        mac("TailSweepDupThr", f"{dupthr:.2f}")

    sw = [r"% generated by make_tables.py -- do not edit",""",
    "14a: the redundant threshold is identified rather than presented as a cut",
    marker="TailSweepDupThr")

rep("make_tables.py",
    r"""                "TailSweepNThr", "TailOnsetThr", "TailBelowOnsetMax",""",
    r"""                "TailSweepNThr", "TailOnsetThr", "TailBelowOnsetMax",
                "TailSweepDupThr",""",
    "14b: registered",
    marker='"TailBelowOnsetMax",\n                "TailSweepDupThr"')

# ======================================================== 1: the four sites
rep("main.tex",
    r"""midrank of $\TailOnsetThr$; at the top of the range, where an authored""",
    r"""midrank of $\TailOnsetThr$, where no evaluator separates them by more than
$\TailBelowOnsetMax$ points; from there up every evaluator does, and at the
top of the range, where an authored""",
    "1c: the abstract says what the threshold measures")

rep("main.tex",
    r"""nothing separates the labelled groups below a midrank of $\TailOnsetThr$,""",
    r"""no evaluator separates the labelled groups by more than
$\TailBelowOnsetMax$ points below a midrank of $\TailOnsetThr$ and every one
of them does above it,""",
    "1d: the discussion")

rep("sec_decomp.tex",
    r"""$t = \TailOnsetThr$ no evaluator shows a difference of even one point, and
from there the difference opens;""",
    r"""$t = \TailOnsetThr$ the worst evaluator shows no difference worth a point,
and $\TailOnsetThr$ is where the worst of them first passes one --- single
evaluators reach $\TailBelowOnsetMax$ points below it, which the table shows
and this threshold does not --- and from there the difference opens for all
of them;""",
    "1e: Section 5.3, where the table that contradicts it is printed")

rep("sec_decomp.tex",
    r"""$t$, median over the \NCorp\ corpora.  No evaluator differs by as much as one point below $t = \TailOnsetThr$.  The last column is the strict-maximum contrast of""",
    r"""$t$, median over the \NCorp\ corpora.  $\TailOnsetThr$ is the first
threshold at which \emph{every} evaluator separates the groups by more than
a point; below it single evaluators reach $\TailBelowOnsetMax$.  The
$>\TailSweepDupThr$ column is the strict-maximum column: the only midrank
above $\TailSweepDupThr$ that $n!$ arrangements admit is the largest one, so
the two cuts coincide by construction and not by measurement.  The last
column is the strict-maximum contrast of""",
    "1f + 14c: the caption states both the threshold and the duplication")

rep("sec_intro.tex",
    r"""groups below a midrank of $\TailOnsetThr$, and at the top of the range the""",
    r"""groups by more than $\TailBelowOnsetMax$ points below a midrank of
$\TailOnsetThr$ --- above it every evaluator does --- and at the top of the
range the""",
    "1g: the introduction")

# ------------------------------------------------------------------- 2
rep("main.tex",
    r"""--- the median midrank is $\MedPctNoncausal$ on the
non-causal texts and $\MedPctCausal$ on the causal ones, against a null of
$0.50$ ---""",
    r"""--- across the \TrendNEval\ autoregressive evaluators the median
midrank is $\MedPctNoncausal$ on the non-causal texts and $\MedPctCausal$ on
the causal ones, against a null of $0.50$; these are medians of medians and
their difference is not any evaluator's component ---""",
    "2: the pair is a ladder median and says so")

# ------------------------------------------------------------------- 3
rep("main.tex",
    r"""the part any authored arrangement contributes (Eq.~\ref{eq:auth}; computed without
reference to the causal labels) and the part attributable to causal order alone""",
    r"""the part any authored arrangement contributes (Eq.~\ref{eq:auth}; computed
on the texts labelled non-causal, which uses the labels to choose its
reference set and not to measure anything, in the sense
Section~\ref{sec:scope} sets out) and the part attributable to causal order
alone""",
    "3: the caption agrees with Section 3.4 about the labels")

# ------------------------------------------------------------------- 4
rep("sec_intro.tex",
    r"""decomposes the measured distance into two: the part any writer-chosen order earns, and the""",
    r"""decomposes the measured distance into two: the part the order a passage
came in earns on its own, and the""",
    "4: the last 'writer' in the paper")

# ------------------------------------------------------------------- 5
rep("main.tex",
    r"""What was measured
for \texttt{bert-base} and \texttt{bert-large} is a pseudo-log-likelihood""",
    r"""What was measured
for the masked evaluators in that comparison is a pseudo-log-likelihood""",
    "5: the caption stops naming a pair the paper does not record")

# ------------------------------------------------------------------- 7
rep("main.tex",
    r"""Section~\ref{sec:resolution} measures at one step of the grid.""",
    r"""Section~\ref{sec:resolution} measures at \CausalCompStepsMin\ to
\CausalCompStepsMax\ steps of the grid.""",
    "7: the generated range, where a hand-typed singular stood")

# ------------------------------------------------------------------- 9
rep("sec_decomp.tex",
    r"""above the non-causal median, with a $95\%$ interval from resampling texts
within each corpus and taking the median across the \NCorp\ corpora.  }""",
    r"""above the non-causal median, with a $95\%$ interval from resampling texts
within each corpus and taking the median across the \NCorp\ corpora.  That
median is one of \NCorp\ per-corpus ratios, so this column has a grid of its
own: it takes \RatioNDistinct\ distinct values over \RatioNEval\ evaluators
and its intervals have \RatioNDistinctEnds\ distinct endpoints, with
\RatioNAtEnd\ of the point estimates sitting on one.  We read its level and
not its width, for the reason Section~\ref{sec:resolution} gives about the
midrank.  It is also not the ratio of the two medians printed beside it;
those are medians of different per-corpus quantities.  }""",
    "9c: the new column is held to the same resolution rule as the rest")

# ------------------------------------------------------------------- 11
rep("sec_truesigma.tex",
    r"""under \texttt{LLaDA}: the \emph{order} of the two groups is stable.""",
    r"""under \texttt{LLaDA}: where the causal group sits \emph{relative to the
null} is the same under both.  That is not a statement about the two groups'
order, which does reverse in one cell below.""",
    "11: the counts are against the null, and the sentence says so")

# ------------------------------------------------------------------- 12
rep("sec_decomp.tex",
    r"""\TrendNSignificant\ reach $0.05$, and both are statistics of the
labelled contrast rather than of the authored distance: the fraction of
\emph{causal} texts at the extreme arrangement, and the ceiling-free tail
contrast above.""",
    r"""\TrendNSignificant\ reach $0.05$, and both are read on the
\emph{causal} group rather than on the authored distance: the fraction of
causal texts at the extreme arrangement, which references no other group,
and the ceiling-free tail contrast above, which is measured against the
non-causal group's own percentile.""",
    "12: one of the two is a level and not a contrast")

# ------------------------------------------------------------------- 13
rep("main.tex",
    r"""enumerated, which is not the system of Appendix~\ref{sec:toy}.  There""",
    r"""enumerated.  It has the same shape as the system of
Appendix~\ref{sec:toy} and is not it: this oracle returns the exact subset
marginals of its own joint, which is what the test needs and what the
appendix's measurement would have nothing to measure on.  There""",
    "13: what distinguishes the two systems is stated, not asserted")

# ------------------------------------------------------------------- 15
rep("main.tex",
    r"""arrangement closing, and say so where an earlier reading of these data said
the opposite.""",
    r"""arrangement closing.""",
    "15a: the discussion reports the measurement, not the revision")

print(f"done: {N} edits")

# ================================================== 10: the multiplicity
# Section 5.4 runs \TrendNTested correlations against capacity and corrects
# none of them, while the cell tests are corrected over 25 and the distance
# tests over 20.  0.05/8 is below the exact floor 2/5!, so this ladder
# cannot carry a corrected trend at all -- which is a fact about the ladder
# and has to be stated rather than left for a referee to find.  The two
# correlations stand as they are measured; what changes is that the reader
# is told they are uncorrected and why no correction is available.
rep("make_tables.py",
    r"""        if "TrendNTested" in MACROS:
            MACROS["TrendNTested"] = str(int(MACROS["TrendNTested"]) + 2)
            MACROS["TrendNSignificant"] = str(
                int(MACROS["TrendNSignificant"]) + extra)""",
    r"""        if "TrendNTested" in MACROS:
            MACROS["TrendNTested"] = str(int(MACROS["TrendNTested"]) + 2)
            MACROS["TrendNSignificant"] = str(
                int(MACROS["TrendNSignificant"]) + extra)
            # HERE, not where TrendNTested is first set: the tail trends are
            # folded in afterwards, so a threshold computed from the earlier
            # count would be 0.05/6 printed beside a family of 8.  The
            # threshold these correlations WOULD be judged against if this
            # section corrected them the way its cell tests are corrected;
            # the prose states that it lies below the exact floor rather
            # than quietly not correcting.
            MACROS["TrendBonferroni"] = (
                f"{0.05 / int(MACROS['TrendNTested']):.4f}")""",
    "10a: the corrected threshold, computed from the final family size",
    marker="TrendBonferroni")

rep("make_tables.py",
    r"""                "TrendNTested",""",
    r"""                "TrendNTested", "TrendBonferroni",""",
    "10b: registered",
    marker='"TrendNTested", "TrendBonferroni",')

rep("sec_decomp.tex",
    r"""No component of the authored distance reaches it.  The
count is generated rather than asserted, so a sentence calling one of them
the only one cannot outlive the measurement --- which is what an earlier
version of this sentence did.""",
    r"""No component of the authored distance reaches it.  The
count is generated rather than asserted, so a sentence calling one of them
the only one cannot outlive the measurement.

Neither of the two is corrected for the \TrendNTested\ correlations this
section runs, and we say so rather than leave it implicit: the cell tests of
Section~\ref{sec:window} are corrected over \TailNCells\ and the
distance-from-null tests of Section~\ref{sec:fbresult} over
\FbNTestsDisp, and this family is not.  It cannot be.  A Bonferroni
threshold here would be $0.05/\TrendNTested = \TrendBonferroni$, and the
smallest two-sided $p$ that \TrendNEval\ points admit at all is
$\TrendPFloor$, so no correlation measured on this ladder could clear it
whatever the data did.  Both correlations are therefore reported
uncorrected, and the direction rather than the threshold is what we lean
on: the ceiling-free tail fraction is larger at every rung than at the one
below, which is a statement about the ordering of \TrendNEval\ numbers and
not about a $p$.  A ladder with more rungs is what would settle it, and
Section~\ref{sec:limitations} says so.""",
    "10c + 15b: the family is named, the floor is stated, the remark goes")

print(f"total: {N} edits")
