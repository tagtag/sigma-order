r"""The two readings, written so that one functional is visibly one functional.

Three corrections to the display, two of them substantive.

THE MEASURE.  Ref. [1]'s Eq. (33) writes the integral fluctuation theorem
under $P_\to$ for FIXED-length blocks, where $R$ is a bijection of
$\mathcal{Y}^T$.  This paper uses sentence blocks, which are variable
length, and Ref. [1] treats that case separately: "We then replace $P$
with the conditional distribution $P_c$, which leaves $\sigma'$
unchanged", giving Eq. (34), $\mathbb{E}_{P_c}[e^{-\sigma'}] = 1$.  The
display was quoting the fixed-length statement for the variable-length
setting.  $P_c$ is the forward measure conditioned on the sequence ending
at a block boundary, which is the terminal-delimiter condition Section 2.2
already invokes two paragraphs earlier and never defines.  Both are fixed
here, since the definition is what makes $P_c$ readable.

THE FUNCTIONAL.  The prose says "the functional is the same in both
readings" and "the brackets carry the difference", and the two lines then
differed in more than brackets: $\log P(x)/P(Rx)$ against $\Delta(x)$,
which carries a $1/L$ and is defined in Eq. (delta) with $\tilde{x}$
rather than $Rx$.  A reader cannot see the claim the paragraph is making.
Both lines now carry the same expression, and the connection to $\Delta$
is stated as what it is: $\log P(x)/P(Rx) = L\,\Dblock(x)$.

Dropping the $1/L$ is right and not a liberty: Ref. [1]'s Eq. (32) defines
$\sigma'$ without it, and the per-length form appears only where its
figures report $\sigma_{\mathrm{block}}/T'$.

THE CRITERION.  "for one $x$ that $P_\to$ did not produce" defines the
fixed-text reading by provenance.  That is not this paper's criterion and
contradicts what it took several passes to establish: "Nothing forbids
evaluating $\log P(x)$ there: every sequence is in the model's support",
and "it holds whether or not the text came from the model".  What makes a
reading fixed-text is that no average is taken.  Provenance matters for
the next point -- that the ensemble statement does not reach these corpora
-- and the paragraph after the display is where it already lives.

Run:  python fix_display.py <paper dir>
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


# ------------------------------------------- 1 the condition gets a definition
rep("main.tex",
    r"""terminal-delimiter condition that makes $R$ a bijection also makes it an
involution on the space it carves out, so the process that realises
$P_\leftarrow$ can be written in one line: sample a sequence from the model,
then reverse the order of its blocks.""",
    r"""terminal-delimiter condition --- that the sequence end at a block boundary,
so that the reversed sequence segments uniquely --- makes $R$ a bijection,
and also an involution on the space it carves out.  The process that
realises $P_\leftarrow$ can therefore be written in one line: sample a
sequence from the model, then reverse the order of its blocks.""",
    "1: the condition the argument rests on is stated, not named")

# ------------------------------------------- 2 the display
rep("main.tex",
    r"""\textit{the ensemble reading:}\quad
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
    r"""\textit{the ensemble reading:}\quad
  &\mathbb{E}_{P_c}\!\left[\log \frac{P(x)}{P(Rx)}\right] \;\ge\; 0 ,
  \label{eq:ensembleread}\\[2pt]
\textit{the fixed-text reading:}\quad
  &\log \frac{P(x)}{P(Rx)} \quad \text{for a single } x ,
   \text{ with no average taken.}
  \label{eq:fixedtextread}
\end{align}
Equation~\eqref{eq:ensembleread} is Ref.~\cite{sagawa2026}'s Section~V~A
--- the non-negativity just cited --- and nothing in this paper disputes
it.  Here $P_c$ is the forward measure conditioned on the terminal-delimiter
condition above, which is the form the theorem takes when the blocks are of
variable length~\cite[Eq.~(34)]{sagawa2026}, as sentence blocks are.
Equation~\eqref{eq:fixedtextread} is its Section~V~B and is where every
objection below to the quantity lies.  It is $L\,\Dblock(x)$, the quantity
of Eq.~\eqref{eq:delta} before the per-token normalisation, and
Ref.~\cite{sagawa2026} likewise defines it without that
normalisation~\cite[Eq.~(32)]{sagawa2026}.  The functional is the same in both
readings; what differs is the measure, and whether an average is taken at
all.  The brackets carry the difference, and dropping them is how a
measured value comes to be read as a theorem: $\mathbb{E}_{P_c}$ is a
statement about a distribution, and the bare log-ratio is a number read off
one text.""",
    "2: one measure corrected, one functional made visible, one criterion fixed",
    marker=r"\mathbb{E}_{P_c}")


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
