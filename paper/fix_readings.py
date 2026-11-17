r"""One functional, two settings, and a name for each.

Ref. [1] reads its entropy production in two settings.  On trajectories the
model itself generated (its Sec. V A), where the fluctuation theorem
applies and the average is non-negative.  And on externally prepared fixed
texts (its Sec. V B), where there is no ensemble, and where Ref. [1] itself
says the averages are not guaranteed non-negative.  Everything this paper
measures, and every objection it makes, concerns the second.

Section 2.2 establishes all of that, carefully, in prose.  What it never
does is NAME the two, and the cost shows up everywhere else: three later
sentences said "the quantity of Ref. [1]" with a definite article, one of
them asserting of it something true only of the second setting; a patch
then repaired those three with three different paraphrases, because there
was no name to use.  A reader reaching page 8 still cannot tell whether
the paper is against the framework or against one application of it.

So:

  (a) a display putting the two settings side by side, with the brackets
      doing the work.  One is an average under $P_\to$ and the other is a
      number read off one text, and writing both as "> 0" is how a
      measurement comes to look like a theorem.  It is also why
      $\Delta(\mathrm{id}) > 0$ and $\langle\sigma\rangle \ge 0$ were
      being read as the same claim: different measure, different bracket,
      different status.

  (b) the names: \emph{ensemble reading} and \emph{fixed-text reading}.
      The three repaired sites take the names, so one phrase does the work
      of three paraphrases.

  (c) the scope, in the abstract.  "Nothing here disputes the ensemble
      reading" is currently a half-sentence in the middle of Section 2.2.
      A referee -- and the author of Ref. [1] -- should not have to reach
      page 8 for it.

NOT written with $\sigma$.  This paper reserves that letter for Eq. (fb),
its own quantity with a zero, and the reservation is an argument
(Section 2.1).  The ensemble statement is written as the unnormalised
log-ratio instead, which also avoids claiming $\mathbb{E}[\Delta] \ge 0$
for the per-token form: dividing by a text-dependent $L$ does not carry a
Jensen bound through.

Apply fix_whichquantity.py first; (b) rewrites the three sites that patch
repaired.

Run:  python fix_readings.py <paper dir>
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


# ---------------------------------------------------- (a) and (b): the display
rep("main.tex",
    r"""derives~\cite[Eqs.~(14),~(19) and~(33)]{sagawa2026} are statements about
the distribution those trajectories are drawn from.""",
    r"""derives~\cite[Eqs.~(14),~(19) and~(33)]{sagawa2026} are statements about
the distribution those trajectories are drawn from.

One functional, read in two settings, and this paper names them apart:
\begin{align}
\textit{the ensemble reading:}\quad
  &\mathbb{E}_{P_\to}\!\left[\log \frac{P(x)}{P(Rx)}\right] \;\ge\; 0 ,
  \label{eq:ensembleread}\\[2pt]
\textit{the fixed-text reading:}\quad
  &\Delta(x)\ \text{for one } x \text{ that } P_\to \text{ did not
    produce.}
  \label{eq:fixedtextread}
\end{align}
Equation~\eqref{eq:ensembleread} is Ref.~\cite{sagawa2026}'s Section~V~A
--- the non-negativity just cited --- and nothing in this paper disputes
it.  Equation~\eqref{eq:fixedtextread} is
its Section~V~B and is where every objection below lies.  The functional is
the same in both readings; what differs is the measure, and whether an
average is taken at all.  The brackets carry the difference, and dropping
them is how
a measured value comes to be read as a theorem: $\mathbb{E}_{P_\to}$ is a
statement about a distribution, and $\Delta(x)$ is a number read off one
text.""",
    "a, b: the two readings, side by side and named",
    marker=r"\textit{the ensemble reading:}")

# ---------------------------------------------------- (b) the three sites
rep("main.tex",
    r"""not the zero.  Read on a text the evaluator did not produce, the quantity
of Ref.~\cite{sagawa2026} has no zero that holds on the text being read.""",
    r"""not the zero.  In the fixed-text reading, the quantity of
Ref.~\cite{sagawa2026} has no zero that holds on the text being read.""",
    "b: Section 2.2 uses the name")

rep("sec_truesigma.tex",
    r"""Everything so far measures $\Delta$: a text scored against a rearrangement
of itself, which is what Ref.~\cite{sagawa2026} evaluates on externally
prepared texts~\cite[Sec.~V~B]{sagawa2026}.""",
    r"""Everything so far measures $\Delta$: a text scored against a rearrangement
of itself, which is the fixed-text reading of
Ref.~\cite{sagawa2026}~\cite[Sec.~V~B]{sagawa2026}.""",
    "b: Section 6 uses the name")

rep("sec_intro.tex",
    r"""first is a question about what the entropy production of
Ref.~\cite{sagawa2026} means once it is read on a text the evaluator did
not produce, and answering it needs a comparison whose zero holds on that
text --- which the model class Ref.~\cite{sagawa2026} uses cannot supply.""",
    r"""first is a question about what the entropy production of
Ref.~\cite{sagawa2026} means in its fixed-text reading, and answering it
needs a comparison whose zero holds on that text --- which the model class
Ref.~\cite{sagawa2026} uses cannot supply.""",
    "b: Section 1 uses the name",
    marker="means in its fixed-text reading")

# ---------------------------------------------------- (c) the scope, up front
rep("main.tex",
    r"""the evaluator (Section~\ref{sec:notareversal}).  No theorem
fixes where the zero of a quantity evaluated on a fixed text lies.  The expression
survives the transfer; the zero does not survive it.""",
    r"""the evaluator (Section~\ref{sec:notareversal}).  No theorem
fixes where the zero of a quantity evaluated on a fixed text lies.  The expression
survives the transfer; the zero does not survive it.
Ref.~\cite{sagawa2026} reads its quantity in two settings, and this paper
disputes one of them.  In the \emph{ensemble reading}, on trajectories the
model itself generated, the fluctuation theorem applies and the average is
non-negative; nothing here disputes it.  Every objection below is to the
\emph{fixed-text reading}, on texts prepared by other models, which is the
setting applied to the corpora re-measured here.""",
    "c: the abstract says which reading is disputed",
    marker="reads its quantity in two settings")

# The patch now scans its own replacement text with the SAME shape list the
# build enforces, not only with the hand-written SUSPECT below.  Four patches
# today introduced a shape they were written to remove -- "come from one",
# "both quantities", and in this one an ordinal standing for a reading, in
# the abstract.  SUSPECT only knows what someone thought to add to it;
# ELLIPSIS_SHAPES is the list the build fails on.
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
        print("     %-34s %-40s %r" % (_name, _lab[:38], _hit))
    print("     (a legitimate use is fine -- the budget then has to move,")
    print("      with a reason, in ELLIPSIS_SHAPES.  An accidental one is")
    print("      what this scan is for.)")

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
