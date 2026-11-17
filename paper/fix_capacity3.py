r"""The capacity/ladder split, finished.

The rest of the paper was converted and Section 5.4 was not, which is the
section that defines the variable.  Its opening says capacity "is the
variable every correlation below is taken against" and, in the same
sentence, that each rho reports monotonicity "along that ladder" -- the two
treated as one axis, which is exactly what Section 3.1 and the Limitations
say they are not.

Six sites: the subsection title, that opening, two procedural mentions, the
sentence that names the title, and Figure 1's caption.  Section 3.1's
definition, the Limitations' disclosure, and everything in Appendix A stay
as they are: the appendix sweeps a width at fixed objective, which is a real
capacity axis.

Two more:
 - The Limitations describe the confound and do not mention the one partial
   check that was run against it.
 - The family check's paragraph says "What IT does show", where "it" is the
   correlation the sentence before has just disqualified.  The claim rests
   on the ordering of four numbers, as the five-rung claim rests on the
   ordering of five, and has to say so in the same words.  The paragraph
   also does not say what the check costs: 13-fold instead of 32.
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


# ------------------------------------------------ 1: the title
rep("sec_decomp.tex",
    r"""\subsection{Capacity moves the tail and not the median}""",
    r"""\subsection{Along the ladder the tail moves and the median does not}""",
    "1: the subsection title, which the section's own summary quotes")

# ------------------------------- 2: the definition, the worst of the six
rep("sec_decomp.tex",
    r"""\emph{Capacity}, the variable every
correlation below is taken against, means the evaluator's parameter count
(the evaluator table of Section~\ref{sec:methods}); because Spearman uses
only ranks and the
\TrendNEval\ evaluators are already ordered by it, each $\rho$ reports
whether a component is monotone along that ladder and says nothing about""",
    r"""Every correlation below is taken against
\emph{position on the ladder}, which is the evaluators in order of parameter
count (the evaluator table of Section~\ref{sec:methods}).  That is not the
same variable as capacity: the top rung is a different family trained on a
different corpus, so the ladder orders size and model provenance together
(Section~\ref{sec:limitations} says what that costs).  Because Spearman uses only ranks and the
\TrendNEval\ evaluators are already in that order, each $\rho$ reports
whether a component is monotone along the ladder and says nothing about""",
    "2: the variable is named as what it is")

# ------------------------------------- 3, 4, 5: procedural mentions
rep("sec_decomp.tex",
    r"""either direction: against capacity the component gives $\rho =""",
    r"""either direction: along the ladder the component gives $\rho =""",
    "3: the component's own correlation")

rep("sec_decomp.tex",
    r"""Of the \TrendNTested\ components this section correlates against
capacity, \TrendNSignificant\ reach $0.05$,""",
    r"""Of the \TrendNTested\ components this section correlates against
position on the ladder, \TrendNSignificant\ reach $0.05$,""",
    "4: the family of correlations")

rep("sec_decomp.tex",
    r"""So the two statistics of one contrast answer the capacity question
differently, and the section's title is the summary:""",
    r"""So the two statistics of one contrast answer the ladder question
differently, and the section's title is the summary:""",
    "5: the sentence that names the title")

# ------------------------------------------------ 6: Figure 1's caption
rep("main.tex",
    r"""by
evaluator in order of capacity.""",
    r"""by
evaluator in ladder order.""",
    "6: Figure 1, whose own caption already says ladder twice")

# ---------------------------------- the Limitations name the partial check
rep("main.tex",
    r"""capacity is stated over the ladder as a whole and we do not separate the
two effects --- which bears hardest on the one trend this paper reports,
the tail contrast of Section~\ref{sec:window}, since the evaluator at the
top of that ladder is also the one that differs most in everything but
size.""",
    r"""capacity is stated over the ladder as a whole and we do not separate the
two effects --- which bears hardest on the one trend this paper reports,
the tail contrast of Section~\ref{sec:window}, since the evaluator at the
top of that ladder is also the one that differs most in everything but
size.  The partial answer is in Section~\ref{sec:window}: that contrast is
read again on the \TailZFamNEval\ rungs that are one family, where it keeps
the same ordering.  It covers $\TrendCapSpanFamily$-fold rather than
$\TrendCapSpan$ and cannot establish a trend at that $n$, so it narrows the
objection without settling it.""",
    "7: the Limitations point at the check that was run",
    marker="The partial answer is in Section")

# ----------------------------- the subject of the family check's claim
rep("sec_decomp.tex",
    r"""and we do not report it as one.  What it does show is that
the ordering is not produced by the single rung that differs in more than
size.""",
    r"""and we do not report it as one.  What the
\TailZFamNEval\ values show --- again as an ordering, and not as a $p$ ---
is that the ordering is not produced by the single rung that differs in more
than size.  It is also a narrower range, $\TrendCapSpanFamily$-fold rather
than $\TrendCapSpan$, which is what the check costs.""",
    "8: the claim rests on four numbers, not on a disqualified rho")

# ------------------------------------------- the Discussion's own hedge
rep("main.tex",
    r"""\TailZFamNEval\ rungs that share a family, where only size differs, it is
monotone as well (Section~\ref{sec:window}).""",
    r"""\TailZFamNEval\ rungs that share a family, where only size differs, it
keeps the same ordering (Section~\ref{sec:window}; at that $n$ no $p$ can
reach $0.05$, so this is an ordering and not a second trend).""",
    "9: the discussion discloses what the subset can and cannot carry")

print(f"done: {N} edits")
