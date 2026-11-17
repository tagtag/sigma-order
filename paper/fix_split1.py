r"""Five long multi-claim sentences, split.  Sample batch.

34 sentences in the paper run over 40 words AND carry two or more clause
breaks with few numbers in them -- long because they hold several claims,
not because they list measurements.  These five are a sample, one each
from the abstract region, Section 2.1, Section 3.2, Section 5.4 and
Section 7, so the effect can be judged where the paper is most read.

THE RULE, and it is checkable in the diff: SPLIT, DO NOT REWRITE.  Every
clause that carries a claim keeps its words.  What changes is where the
sentence ends and the connective that joins the pieces.  Seven times in
the reading rounds a withdrawn claim came back, and every time it came
back inside a rewrite; a split that leaves the claim clauses untouched
cannot do that, and a reader can confirm it did not by looking at whether
any claim words moved.

  1. abstract region, 62 words.  Three claims: that sigma vanishes under a
     joint; that a masked model need not have one; what the value range
     carries in each case.
  2. Section 2.1, 80 words -- and I made it longer two days ago by adding
     the Table 3 pointer.  A report of two statistics with a parenthesis
     inside a colon inside a list.
  3. Section 3.2, 66 words.  An offer, a method, an aside about a third
     evaluator, and a conclusion, in one breath.
  4. Section 5.4, 70 words.  A measurement, then two things it is not.
  5. Section 7, 59 words.  One claim and two denials of what it is not.

Run:  python fix_split1.py <paper dir>
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


# ---------------------------------------------------------------- 1
rep("main.tex",
    r"""vanishes identically whenever the model's conditionals come from a joint ---
which a masked model's need not, since it supplies a distribution for each
unmasking order and no single one of them for all --- so wherever the
identity holds its value range carries no property of the text, and where it
fails what the range carries is the evaluator's incompatibility.""",
    r"""vanishes identically whenever the model's conditionals come from a joint.
A masked model's need not: it supplies a distribution for each unmasking
order and no single one of them for all.  Wherever the identity holds, the
value range of $\sigma$ carries no property of the text; where it fails,
what the range carries is the evaluator's incompatibility.""",
    "1: three claims, three sentences")

# ---------------------------------------------------------------- 2
rep("main.tex",
    r"""$\Dtok$ is reported in Table~\ref{tab:token}: its median is the larger of the
two in \NTokLarger\ of the \NTokCells\ evaluator--corpus cells, by a factor
of \SigTokRatioMin--\SigTokRatioMax (the denominators are the
\texttt{gpt2} rows of Table~\ref{tab:blkcells}, in the same corpus order),
and its causal/non-causal effect size $r$
--- the rank-biserial correlation of Eq.~\eqref{eq:rb}, defined in
Section~\ref{sec:blkord} and used throughout --- is \emph{negative}, the
non-causal texts scoring higher, in \NTokNegAR\ of \NTokNegARTot\ cells.""",
    r"""$\Dtok$ is reported in Table~\ref{tab:token}.  Its median is the larger of
the two in \NTokLarger\ of the \NTokCells\ evaluator--corpus cells, by a
factor of \SigTokRatioMin--\SigTokRatioMax; the denominators are the
\texttt{gpt2} rows of Table~\ref{tab:blkcells}, in the same corpus order.
Its causal/non-causal effect size $r$ --- the rank-biserial correlation of
Eq.~\eqref{eq:rb}, defined in Section~\ref{sec:blkord} and used throughout
--- is \emph{negative}, the non-causal texts scoring higher, in
\NTokNegAR\ of \NTokNegARTot\ cells.""",
    "2: the two statistics get a sentence each")

# ---------------------------------------------------------------- 3
rep("main.tex",
    r"""One may of course evaluate the \emph{shape} of Eq.~\eqref{eq:delta} on a
masked model by substituting some other number for $\log P$ --- a
pseudo-log-likelihood is the usual choice --- and we did exactly that, for
three masked evaluators --- the two this paper reports and
\texttt{bert-large}, which appears nowhere else because nothing it produced
is reported --- before concluding that the comparison with the
autoregressive readings means nothing.""",
    r"""One may of course evaluate the \emph{shape} of Eq.~\eqref{eq:delta} on a
masked model by substituting some other number for $\log P$; a
pseudo-log-likelihood is the usual choice.  We did exactly that, for three
masked evaluators --- the two this paper reports and \texttt{bert-large},
which appears nowhere else because nothing it produced is reported.  We
concluded that the comparison with the autoregressive readings means
nothing.""",
    "3: the offer, the run, and the conclusion are separated")

# ---------------------------------------------------------------- 4
rep("sec_decomp.tex",
    r"""On the causal texts the same fraction runs from $\CeilGPTtwo\%$ to
$\CeilQwen\%$ at $\rho = \TrendCeilRho$ ($p = \TrendCeilP$) --- but that is
a level read on the causal group alone, which references no
other group: it is neither the contrast of Section~\ref{sec:resolution},
which is a difference between the two groups, nor the saturation of a
component defined on the other one.""",
    r"""On the causal texts the same fraction runs from $\CeilGPTtwo\%$ to
$\CeilQwen\%$ at $\rho = \TrendCeilRho$ ($p = \TrendCeilP$).  That is a
level read on the causal group alone, which references no other group.  It
is neither the contrast of Section~\ref{sec:resolution}, which is a
difference between the two groups, nor the saturation of a component
defined on the other one.""",
    "4: the measurement, then what it is not")

# ---------------------------------------------------------------- 5
rep("main.tex",
    r"""These are three readings of
$\Delta$ --- as a reversal, as a quantity, and as a test --- and not a
restatement of the three consequences of Eq.~\eqref{eq:fbzero} that
Section~\ref{sec:introduction} draws, which are about $\sigma$ and about
what was computed in its place, nor of the three deficiencies of
Section~\ref{sec:capacity}, which are properties of $\Delta$ as a number.""",
    r"""These are three readings of $\Delta$: as a reversal, as a quantity, and as
a test.  They are not a restatement of the three consequences of
Eq.~\eqref{eq:fbzero} that Section~\ref{sec:introduction} draws, which are
about $\sigma$ and about what was computed in its place; nor of the three
deficiencies of Section~\ref{sec:capacity}, which are properties of
$\Delta$ as a number.""",
    "5: the claim, then the two denials")

print(f"done: {N} edits")
