r"""Six places that point at a table, a symbol or an evaluator that is not there.

Five of the eight the reader found this round are outside the paragraphs:
a figure caption, a reference to a table's column, a symbol used in one
section and not another, a small table's surroundings.  Seven reading
passes had all gone through paragraphs.

  1. "The last column of Table 5" is its median column.  The ceiling-free
     statistic is the LOWER BLOCK, which the table's own caption names.
     Table 5 was rebuilt from one column into two blocks and the sentence
     did not follow.  (Table 4's caption says "the last column" correctly
     of itself, which is probably where this came from.)

  2. "Appendix A measured that incompatibility as a Schnakenberg cycle
     affinity ... and Table 11 reads sigma on those same models: both
     quantities are non-zero".  Table 11 has no affinity column -- the
     affinity is Table 10's rms|A| -- so one of the two quantities is
     named in a form the cited table does not print.  Section 6.3 and
     Figure 2 both call it sigma_EP, which Table 11 does print.

  3. FIGURE 2'S CAPTION breaks the rule Section 5.4 states and the body
     keeps.  "it rises with capacity rather than falling" is a trend
     claim on rho = +0.90, p = 0.083; Section 5.4 says every rho that
     does not reach 0.05 is reported as no trend established and that
     nothing in the paper rests on one.  The appendix obeys this ("the
     endpoints are what this ratio compares", "not a trend test") and so
     does Section 6.3.  The caption did not get the fix.  It also carries
     "of this kind" with its antecedent inside the figure, and "that
     comparison" twice with no antecedent in the caption at all -- and a
     caption is read on its own.

  4. "under the exchange of labels it is +0.396 instead" drops the
     evaluator on the third telling, after two that carry it, so it reads
     as a statement about the ladder.  Four lines below, the midranks
     printed for that exchange give +0.438 for gpt2, not +0.396.  The
     neighbouring pointer is wrong in the same way: Section 3.4 gives the
     exchange for every evaluator as a SHARE, and the component for one.

  5. Section 6.2 writes permutations as $p$ where Section 3.3 writes
     $\pi$, and $p$ is this paper's symbol for a p-value in some dozens
     of places, with a $p$ column on the facing page.  One line is
     Eq. (antisym) restated, and in the other letter it reads as a second
     identity.

  6. "exact rank null" is first used in Section 4.1 and defined eight
     pages later under the words "Here and below", which is false of the
     uses above it; and it is introduced alongside "$n = 5$" two lines
     after "$1/n!$" with $n = 4$, a collision the definition untangles
     eight pages on.

Run:  python fix_reader3.py <paper dir>
"""
import io
import os
import re
import sys

os.chdir(sys.argv[1])
N = 0
WROTE = []


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
    WROTE.append((label, b))
    print(f"  {label}")
    N += 1


# ------------------------------------------------------ 1 which part of Table 5
rep("sec_decomp.tex",
    r"""bound and a contrast measured there might be an artefact of it.  The last
column of Table~\ref{tab:tail} answers it in units with no bound.""",
    r"""bound and a contrast measured there might be an artefact of it.  The lower
block of Table~\ref{tab:tail} answers it in units with no bound.""",
    "1: the lower block, which is what that table calls it")

# ------------------------------------------------------ 2 the named quantity
rep("sec_truesigma.tex",
    r"""Appendix~\ref{sec:toy} measured that incompatibility directly, as a
Schnakenberg cycle affinity on a system small enough to enumerate, and""",
    r"""Appendix~\ref{sec:toy} measured that incompatibility directly, as the
entropy production $\sigEP$ on a system small enough to enumerate, and""",
    "2: the quantity the cited table prints, and Section 6.3 names")

# ------------------------------------------------------ 3 Figure 2's caption
rep("main.tex",
    r"""whatever its accuracy; the masked values are the floor of that instrument, and
it rises with capacity rather than falling.  No masked readings of this kind are shown beside these.  What was measured
for the masked evaluators in that comparison is not $\Delta$
(Section~\ref{sec:scope}), so it is
withdrawn with the rest of that comparison and is not a $\Delta$ reading to
show.}""",
    r"""whatever its accuracy; the masked values are the floor of that instrument,
and its endpoints rise with capacity rather than falling.  No $\Delta$
readings for masked evaluators are shown beside these: what was measured
for them was not $\Delta$ (Section~\ref{sec:scope}), and it is withdrawn
with the comparison it belonged to.}""",
    "3: the caption keeps Section 5.4's rule and stands on its own")

# ------------------------------------------------------ 4 whose component
rep("main.tex",
    r"""\emph{non}-causal, and under the exchange of labels it is $\SwapAuthored$
instead --- the same statement either way.""",
    r"""\emph{non}-causal, and under the exchange of labels \texttt{\SwapEval}'s is
$\SwapAuthored$ instead --- the same statement either way.""",
    "4a: whose component it is, on the third telling as on the first two")

rep("main.tex",
    r"""$\SwapAuthoredOrig$ for \texttt{\SwapEval} (Section~\ref{sec:decomp} gives
the exchange for every evaluator), and the statements below survive the""",
    r"""$\SwapAuthoredOrig$ for \texttt{\SwapEval} (Section~\ref{sec:decomp}), and
the statements below survive the""",
    "4b: Section 3.4 gives the share for every evaluator, not the component")

# ------------------------------------------------------ 5 the permutation symbol
for _a, _b, _lab in (
    (r"""writing $x_p$ for the text with its blocks in order $p$, we score""",
     r"""writing $x_\pi$ for the text with its blocks in order $\pi$, we score""",
     "5a: the arrangement and its order"),
    (r"""f(p) \;=\; \sigma(x_p)""",
     r"""f(\pi) \;=\; \sigma(x_\pi)""",
     "5b: Eq. (fbperm)"),
    (r"""for every $p$, and record the midrank of $f(\mathrm{id})$,""",
     r"""for every $\pi$, and record the midrank of $f(\mathrm{id})$,""",
     "5c: every arrangement"),
    (r"""a centre, fixed at zero by the antisymmetry $\Delta(p) = -\Delta(p \circ""",
     r"""a centre, fixed at zero by the antisymmetry $\Delta(\pi) = -\Delta(\pi \circ""",
     "5d: and the restatement of Eq. (antisym), in its own letter"),
    (r"""so the set of $f(p)$ is not centred and supplies no origin of its own.""",
     r"""so the set of $f(\pi)$ is not centred and supplies no origin of its own.""",
     "5e: the set of values"),
    (r"""the null rather than ranked.  A compatible evaluator gives $f(p) = 0$ for
every $p$ by Eq.~\eqref{eq:fbzero};""",
     r"""the null rather than ranked.  A compatible evaluator gives $f(\pi) = 0$ for
every $\pi$ by Eq.~\eqref{eq:fbzero};""",
     "5f: and the compatible case"),
):
    rep("sec_truesigma.tex", _a, _b, _lab)

# ------------------------------------------------------ 6 exact rank null
rep("main.tex",
    r"""\TrendAuthoredP$, exact rank null, $n = \TrendNEval$).""",
    r"""\TrendAuthoredP$, exact rank null over \TrendNEval\ evaluators).""",
    "6a: not \"$n$\", which two lines up is the number of sentence blocks")

rep("sec_decomp.tex",
    r"""for it.  Here and below the \emph{exact rank null} means the distribution of the""",
    r"""for it.  Throughout, the \emph{exact rank null} means the distribution of the""",
    "6b: the term is used before this, so not \"here and below\"")


def _budget_shapes():
    try:
        src = io.open("check_paper.py", encoding="utf-8").read()
        m = re.search(r"ELLIPSIS_SHAPES = \{.*?\n\}", src, re.S)
        ns = {}
        exec(m.group(0), ns)
        return ns["ELLIPSIS_SHAPES"]
    except Exception as exc:
        print(f"  (no shape self-scan: {exc})")
        return {}


shaped = []
for _name, (_pat, _budget) in sorted(_budget_shapes().items()):
    for _lab, _b in WROTE:
        for _m in re.finditer(_pat, re.sub(r"\s+", " ", _b)):
            shaped.append((_name, _lab, _m.group(0)))
if shaped:
    print("\n  !! replacement text uses shapes the build budgets:")
    for _name, _lab, _hit in shaped:
        print("     %-34s %-30s %r" % (_name, _lab[:28], _hit))

SUSPECT = re.compile(
    r"\bthe ones?\s*(?=[.,;:]|\b(?:that|which|it|we|they|the|is|are)\b)|"
    r"\bof (?:that|this)\s*(?=[.,;:]|\b(?:is|are|was|were|and|or|we|it|they)\b)|"
    r"\b(?:that kind|this kind|a kind|that form|this form|"
    r"the thing|in this sense|this reading|the other one|"
    r"such a|that of|need not\b(?!\s+\w)|does not\.|do not\.|cannot\.|"
    r"\bis of the\b|\bis of a\b|\band not of\b|\bbut not of\b)", re.I)
bad = [(lab, m.group(0)) for lab, b in WROTE for m in SUSPECT.finditer(b)]
if bad:
    print("\n  !! replacement text contains new pointing constructions:")
    for lab, hit in bad:
        print("     %-40s %r" % (lab, hit))
    raise SystemExit("fix the replacements before shipping this patch")
print(f"done: {N} edits (replacement text clean)")
