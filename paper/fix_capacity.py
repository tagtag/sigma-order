r"""Capacity and the ladder's span are two different numbers.

\TrendCapSpan is 32: the ratio of the parameter counts at the two ends of
the ladder, 124M to 4B.  Section 3.1 and the Limitations both say that the
top rung is a different family trained on a different corpus under a
different recipe, so a trend across the whole ladder is not attributable to
capacity alone -- and then four sentences say "across 32x in capacity",
which attributes exactly that.  \TrendCapSpanFamily is 13, the span of the
four rungs that do differ only in size.

The retreat: capacity means the 13-fold within-family span; 32 is the
ladder's parameter span and is called that.  The trend keeps all five
rungs, because that is where it was measured, and is said to run "along the
ladder" rather than "with capacity".

That leaves the obvious question unanswered -- does the trend survive on
the four rungs where only size differs? -- so this measures it rather than
leaving it to a caveat.  It is the same correlation on a subset, not a new
test, and it is not added to Section 5.4's family of \TrendNTested.
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


# =================================================== the generator first
rep("make_tables.py",
    r"""        mac("TailZTrendRho", f"{rho:+.2f}")
        mac("TailZTrendP", f"{p:.3f}")
        # Fold the two tail trends into Section 5.4's count, which""",
    r"""        mac("TailZTrendRho", f"{rho:+.2f}")
        mac("TailZTrendP", f"{p:.3f}")
        # The same correlation on the rungs that share a family, where only
        # size differs.  The Limitations say the family confound bears
        # hardest on this one trend; a caveat is the weaker answer when the
        # subset can simply be measured.  This is NOT a new member of
        # Section 5.4's family -- it is the same statistic on a subset of
        # the same points, and TrendNTested is deliberately not incremented
        # for it.  n = 4 floors at 2/4! = 0.083, which the prose states.
        fam = [m for m in models if m.startswith("gpt2") and PARAMS.get(m)
               and m in per_model]
        if len(fam) > 2:
            fz = [per_model[m][1] for m in fam]
            if all(np.isfinite(fz)):
                frho, fp, _ = spearman([PARAMS[m] for m in fam], fz)
                mac("TailZFamRho", f"{frho:+.2f}")
                mac("TailZFamP", f"{fp:.3f}")
                mac("TailZFamNEval", str(len(fam)))
                mac("TailZFamFloor", f"{exact_p_floor(len(fam)):.3f}")
        # Fold the two tail trends into Section 5.4's count, which""",
    "A: the trend restricted to the one family, measured",
    marker="TailZFamRho")

rep("make_tables.py",
    r"""                "TailZTrendRho", "TailZTrendP", "TailSignP",""",
    r"""                "TailZTrendRho", "TailZTrendP", "TailSignP",
                "TailZFamRho", "TailZFamP", "TailZFamNEval",
                "TailZFamFloor",""",
    "B: registered",
    marker='"TailZFamRho", "TailZFamP", "TailZFamNEval"')

# ============================================ capacity -> the ladder's span
rep("main.tex",
    r"""It stays there at every rung of the ladder,
across \TrendCapSpan$\times$ in capacity, and nothing we""",
    r"""It stays there at every rung of the ladder,
over a \TrendCapSpan-fold range of parameters, and nothing we""",
    "C: the abstract, where 32 is a parameter range and not a capacity")

rep("sec_intro.tex",
    r"""It is \CausalCompStepsMin\ to \CausalCompStepsMax\ steps at every size we
measured, across \TrendCapSpan$\times$ in capacity.""",
    r"""It is \CausalCompStepsMin\ to \CausalCompStepsMax\ steps at every size we
measured, over a \TrendCapSpan-fold range of parameters.""",
    "D: the introduction")

rep("sec_decomp.tex",
    r"""\TrendCapSpan$\times$ in capacity it never leaves the smallest non-zero""",
    r"""a \TrendCapSpan-fold range of parameters it never leaves the smallest
non-zero""",
    "E: Section 5.3")

rep("sec_decomp.tex",
    r"""across \TrendCapSpan$\times$ in capacity, while the same contrast read in""",
    r"""over a \TrendCapSpan-fold range of parameters, while the same contrast
read in""",
    "F: Section 5.4's summary")

rep("sec_decomp.tex",
    r"""% evaluators spanning \TrendCapSpan$\times$ in parameters, it does not.  What""",
    r"""% evaluators spanning \TrendCapSpan-fold in parameters -- of which the
% within-family capacity span is \TrendCapSpanFamily-fold -- it does not.  What""",
    "G: the design note keeps the two numbers apart too")

# ====================================== the trend: along the ladder, and
#                                        within the family, measured
rep("main.tex",
    r"""In units with no
ceiling that separation grows monotonically with capacity, from
$\TailZGPTtwo\%$ to $\TailZQwen\%$ against a null of $\TailZNull\%$""",
    r"""In units with no
ceiling that separation grows monotonically along the ladder, from
$\TailZGPTtwo\%$ to $\TailZQwen\%$ against a null of $\TailZNull\%$""",
    "H: the abstract says along the ladder, which is where it was measured")

rep("main.tex",
    r"""in
ceiling-free units that separation grows monotonically with capacity ($\rho = \TailZTrendRho$, $p =
\TailZTrendP$).""",
    r"""in
ceiling-free units that separation grows monotonically along the ladder
($\rho = \TailZTrendRho$, $p = \TailZTrendP$), and on the
\TailZFamNEval\ rungs that share a family, where only size differs, it is
monotone as well ($\rho = \TailZFamRho$, $p = \TailZFamP$, which is the
floor for that many points).""",
    "I: the discussion answers the confound instead of only declaring it",
    # M rewrites what this produces, so the guard looks for what both leave
    marker="rungs that share a family, where only size differs")

rep("sec_intro.tex",
    r"""separation grows with capacity in units that have no ceiling.""",
    r"""separation grows along the ladder in units that have no ceiling.""",
    "J: the introduction")

rep("sec_decomp.tex",
    r"""\paragraph{The tail contrast does vary with capacity.}""",
    r"""\paragraph{The tail contrast does vary along the ladder.}""",
    "K: the paragraph heading")

print(f"done: {N} edits")

# The within-family result belongs in Section 5.4 first; the Discussion
# then refers to it rather than carrying the full statement.
rep("sec_decomp.tex",
    r"""That $p$ is $\TrendPFloor$ to within rounding: it is
the smallest value \TrendNEval\ points admit, so the relation is as
monotone as this ladder can show.""",
    r"""That $p$ is $\TrendPFloor$ to within rounding: it is
the smallest value \TrendNEval\ points admit, so the relation is as
monotone as this ladder can show.  The ladder's top rung differs from the
rest in more than size (Section~\ref{sec:limitations}), so we also read the
same quantity on the \TailZFamNEval\ rungs that are one family and differ in
size alone: there too it is monotone, $\rho = \TailZFamRho$ at $p =
\TailZFamP$, which is again the floor, $\TailZFamFloor$, for that many
points.  That is the same correlation on a subset of the same points and not
an additional test, so it does not enter the count below.""",
    "L: the within-family subset is measured where the trend is reported",
    marker="rungs that are one family and differ in")

rep("main.tex",
    r"""($\rho = \TailZTrendRho$, $p = \TailZTrendP$), and on the
\TailZFamNEval\ rungs that share a family, where only size differs, it is
monotone as well ($\rho = \TailZFamRho$, $p = \TailZFamP$, which is the
floor for that many points).""",
    r"""($\rho = \TailZTrendRho$, $p = \TailZTrendP$), and on the
\TailZFamNEval\ rungs that share a family, where only size differs, it is
monotone as well (Section~\ref{sec:window}).""",
    "M: the discussion points at it rather than repeating it")

# The last of the loose "with capacity": the whole ladder is meant.
rep("sec_decomp.tex",
    r"""``The causal contribution does not vary with capacity''
is therefore true of the median and false of the tail,""",
    r"""``The causal contribution does not vary along the ladder''
is therefore true of the median and false of the tail,""",
    "N: the counterfactual sentence in the paper's own vocabulary")

rep("sec_decomp.tex",
    r"""``The causal contribution shrinks with capacity'' would say the quantity""",
    r"""``The causal contribution shrinks along the ladder'' would say the quantity""",
    "O: the same, for the other counterfactual")

rep("sec_decomp.tex",
    r"""smallest evaluator onwards and stays there; what capacity moves is where in
the range the two groups differ, not how much the median of one exceeds the
median of the other.""",
    r"""smallest evaluator onwards and stays there; what moves along the ladder is
where in the range the two groups differ, not how much the median of one
exceeds the median of the other.""",
    "P: the claim, not the attribution")

rep("sec_decomp.tex",
    r"""and that the same contrast read in the tail both clears its floor and grows with capacity.""",
    r"""and that the same contrast read in the tail both clears its floor and grows along the ladder, within the one family as well as across the whole of it.""",
    "Q: the section's own summary of what it claims")

print(f"total: {N} edits")
