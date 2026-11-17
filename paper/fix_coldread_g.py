r"""Seventh batch: the third read.  Four defects and four refinements.

1. The abstract kept the old sentence in front of the new one: "Nothing
   separates the groups below 0.80, where no evaluator separates them by
   more than 3 points".  The three body sites were rewritten and this was
   prepended to rather than replaced.

2. Limitations still says Section 4 "is constructed to be independent of
   the labels".  Section 4's own first paragraph says it uses them to pick
   its reference set and does not use any claim that they are right, and
   Section 3.4 and the Table 2 caption now say so too.  What is true of
   Section 4 is invariance under exchanging the labels.

3. The comparison table's "what was measured" row still says one step of
   the grid, split over two lines, which is why the previous pass missed
   it.

4. Two section references, both mine from the last batch:
   - Section 5.4 cites itself for the cell tests, which are Section 5.3's,
     in a sentence that contrasts the two.
   - The Table 2 caption cites Section 3.2 for the select/measure
     distinction, which Section 3.4 draws.

a. "+13 to +22 points" in the abstract and the discussion is a median over
   corpora; per cell the range runs much wider and Section 5.3 says so.

b. The abstract quotes p = 0.017 unqualified while Section 5.4 explains at
   length that this family is uncorrected and that 0.017 is the floor.
   The qualifier belongs where the number is first shown.

c. The tab_saturation caption calls the causal ceiling fraction "the
   contrast of Section 5.3".  It is a level on one group; Section 5.4 was
   corrected on exactly this point last round.

d. The tab_token caption says "autoregressive cells", which everywhere
   else in the paper means 25.
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


# --------------------------------------------- 1: the abstract's two halves
rep("main.tex",
    r"""Nothing separates the groups below a
midrank of $\TailOnsetThr$, where no evaluator separates them by more than
$\TailBelowOnsetMax$ points; from there up every evaluator does, and at the
top of the range, where an authored
arrangement is the most costly of all $n!$, the causal group reaches it
$\TailDiffGPTtwo$ to $\TailDiffQwen$ points more often.""",
    r"""No evaluator separates the groups by more
than $\TailBelowOnsetMax$ points below a midrank of $\TailOnsetThr$, and
from there up every one of them does; at the top of the range, where an
authored arrangement is the most costly of all $n!$, the causal group
reaches it $\TailDiffGPTtwo$ to $\TailDiffQwen$ points more often as a
median over corpora.""",
    "1 + a: one claim, and the range is named as a median")

# --------------------------------------------------- 2: the Limitations
rep("main.tex",
    r"""Section~\ref{sec:authored} is constructed to be independent of the
labels;""",
    r"""Section~\ref{sec:authored} uses them to choose which texts it
reads and nothing beyond that, so what it says is unchanged when the two
labels are exchanged;""",
    "2: invariance under exchange, not independence of the labels")

# ------------------------------------------------ 3: the comparison table
rep("main.tex",
    r"""what was measured   & significant in \ContrastNRejecting\ of
                      \ContrastNCells\ cells, one
                    & the same sign in \FbNNegative\ of \\
                    & \quad step of the grid""",
    r"""what was measured   & significant in \ContrastNRejecting\ of
                      \ContrastNCells\ cells,
                    & the same sign in \FbNNegative\ of \\
                    & \quad \CausalCompStepsMin--\CausalCompStepsMax\ steps
                      of the grid""",
    "3: the generated range, in the row that split it over two lines")

# ------------------------------------------------- 4: two cross-references
rep("sec_decomp.tex",
    r"""the cell tests of
Section~\ref{sec:window} are corrected over \TailNCells\ and the""",
    r"""the cell tests of
Section~\ref{sec:resolution} are corrected over \TailNCells\ and the""",
    "4a: the cell tests are the previous section's, not this one's")

rep("main.tex",
    r"""reference set and not to measure anything, in the sense
Section~\ref{sec:scope} sets out)""",
    r"""reference set and not to measure anything, in the sense
Section~\ref{sec:decomp} sets out)""",
    "4b: the select/measure distinction is drawn in Section 3.4")

# ------------------------------------------------------ a: the discussion
rep("main.tex",
    r"""and at the top of the range the causal group reaches the most costly
arrangement $\TailDiffGPTtwo$ to $\TailDiffQwen$ points more often;""",
    r"""and at the top of the range the causal group reaches the most costly
arrangement $\TailDiffGPTtwo$ to $\TailDiffQwen$ points more often, as a
median over corpora;""",
    "a2: the discussion names the same range as a median")

# ----------------------------------------------- b: the abstract's p-value
rep("main.tex",
    r"""$\TailZGPTtwo\%$ to $\TailZQwen\%$ against a null of $\TailZNull\%$
($\rho = \TailZTrendRho$, $p = \TailZTrendP$).""",
    r"""$\TailZGPTtwo\%$ to $\TailZQwen\%$ against a null of $\TailZNull\%$
($\rho = \TailZTrendRho$ over \TrendNEval\ evaluators; $p = \TailZTrendP$,
which is the smallest two-sided value that many points admit, and is not
corrected for the other correlations the same section runs).""",
    "b: the floor and the multiplicity travel with the number")

# ------------------------------------------- c: a level is not a contrast
rep("sec_decomp.tex",
    r"""The causal column
rises, and that is the contrast of Section~\ref{sec:resolution}, not a
property of the component.""",
    r"""The causal column
rises; that is a level read on the causal group alone, which
Section~\ref{sec:window} separates from the contrast of
Section~\ref{sec:resolution}, and it is not a property of the component.""",
    "c: the ceiling fraction references no second group")

# ------------------------------------------------------ d: whose cells
rep("main.tex",
    r"""non-causal texts scoring higher --- in \NTokNegAR\ of \NTokNegARTot\
autoregressive cells, which a measure of causal order should not do.""",
    r"""non-causal texts scoring higher --- in \NTokNegAR\ of the
\NTokNegARTot\ autoregressive cells of this table, which a measure of
causal order should not do.""",
    "d: the count is of this table's cells, not the paper's usual 25")

print(f"done: {N} edits")
