r"""What a Japanese rendering of the abstract turned up, sentence by sentence.

The author cannot read the English well enough to check it, so the abstract
was rendered into Japanese one sentence at a time and read back.  Rendering
forces a referent for every pointer, a noun for every count and a unit for
every number, and seventeen places could not be rendered without asking a
question the English does not answer.  Three of those were wrong rather
than unclear:

  * Section 3.2 says the substitution was run "for three masked
    evaluators".  results_pll/ holds bert-base and bert-large, and gpt2
    for the autoregressive side.  LLaDA was never given the substitution.
    The number is two, and it is not checkable from the paper either way
    because bert-large appears in no table, so the count comes out.

  * "which is what the corpora of Ref. [1] contain" says the prose is of
    the same kind as Ref. [1]'s.  Section 1 says the experiment there
    "supplies this paper's corpora" and Section 5.1 calls them "its own
    corpora".  They are the same corpora, and saying it the long way
    invites a referee to ask whether the comparison used different texts.

  * "the measured distance" is the median midrank's distance from the
    0.50 null, defined in Section 3.4 and nowhere in the abstract, while
    the share quoted against it is in ceiling-free units.  A reader who
    takes the distance in midrank units pairs it with the wrong number.

The rest are pointers without referents (the question, the transfer, the
room above, more often than what), a term named before it is defined
(incompatibility), a definition given as an aside inside a dash, and the
line between what follows from the theorems and what the measurement adds,
which Section 1 draws and the abstract does not.

Run:  python fix_ar02.py <paper dir>
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


# ===================================================== wrong, not unclear

# ---- 1. the count the data does not support
rep("main.tex",
    r"""exactly that, for three masked evaluators, and concluded that the""",
    r"""exactly that, on masked evaluators, and concluded that the""",
    "1: the substitution was run on two, and neither count is checkable here")

# ---- 2. the corpora are Ref. [1]'s, not merely like them
rep("main.tex",
    r"""All of this is measured on prose
that language models produced, which is what the corpora of
Ref.~\cite{sagawa2026} contain;""",
    r"""All of this is measured on
Ref.~\cite{sagawa2026}'s own corpora, which are prose that language models
produced;""",
    "2: the same corpora, said as an identity")

# ---- 3. the distance, and the unit the share is in
rep("main.tex",
    r"""decomposition referred to that zero does use them, and taking them at face
value, across an autoregressive ladder from $\ParamsGPTtwo$ to $\ParamsQwen$
parameters, between $\ShareZMin\%$ and $\ShareZMax\%$ of the measured
distance is attributable to causal order and the rest to the arrangement
simply being the order the passage was produced in.""",
    r"""decomposition referred to that zero does use them.  Taking them at face
value --- granting that they record whether the sentences stand in a causal
sequence --- the decomposition runs across an autoregressive ladder of
\TrendNEval\ evaluators, from $\ParamsGPTtwo$ to $\ParamsQwen$ parameters.
Between $\ShareZMin\%$ and $\ShareZMax\%$ of the median midrank's distance
from the $0.50$ null is attributable to causal order, and the rest to the
arrangement simply being the order the passage was produced in.""",
    "3: what is assumed, what the distance is, and what the range runs over",
    marker="granting that they record whether the sentences stand")


# ============================================ pointers without a referent

# ---- 4. from where to where
rep("main.tex",
    r"""The expression
survives the transfer; the zero does not survive it.""",
    r"""The expression carries
over from an ensemble of trajectories to a fixed text; its zero does not
carry over.""",
    "4: the transfer, named")

# ---- 5. the question
rep("main.tex",
    r"""Neither quantity answers the question the thermodynamic reading poses, and
for different reasons.""",
    r"""The question the thermodynamic reading poses is whether a fixed text has an
entropy production: a number that is a property of the text and has a zero.
Neither quantity answers it, and for different reasons.""",
    "5: the question, stated rather than referred to")

# ---- 6. the room above
rep("main.tex",
    r"""over a \TrendCapSpan-fold range of parameters, and nothing we measure shows the
room above an authored arrangement closing.""",
    r"""over a \TrendCapSpan-fold range of parameters, and nothing we measure shows
the room above an authored arrangement --- the fraction of arrangements that
still score above it --- closing.""",
    "6: the room above, in one clause")

# ---- 7. more often than what
rep("main.tex",
    r"""authored arrangement is the most costly of all $n!$, the causal group
reaches it $\TailDiffGPTtwo$ to $\TailDiffQwen$ points more often as a
median over corpora.""",
    r"""authored arrangement is the most costly of all $n!$, the causal group
reaches it $\TailDiffGPTtwo$ to $\TailDiffQwen$ points more often than the
non-causal group, as a median over corpora and across the \TrendNEval\
evaluators.""",
    "7: than the non-causal group, over corpora, across evaluators")

# ---- 8. which cells
rep("main.tex",
    r"""part separates the two label groups in \ContrastNRejecting\ of the
\ContrastNCells\ (evaluator, corpus) cells at""",
    r"""part separates the two label groups in \ContrastNRejecting\ of the
\ContrastNCells\ (evaluator, corpus) cells --- \ContrastNEval\ evaluators by
\ContrastNCorpora\ corpora --- at""",
    "8: the cell count printed as the product it is")


# ====================================== scope, naming, and what is aside

# ---- 9. the resolution argument is about the median (Section 8 says so)
rep("main.tex",
    r"""is the smallest non-zero reading it can return, so what is established is
that the two label groups differ and not by how much.""",
    r"""is the smallest non-zero reading it can return, so what the median
establishes is that the two label groups differ and not by how much.""",
    "9a: the median, in the abstract")

rep("sec_intro.tex",
    r"""on, one step being the smallest non-zero reading available: what the
measurement establishes is that the two label groups differ, not by how
much.""",
    r"""on, one step being the smallest non-zero reading available: what the median
establishes is that the two label groups differ, not by how much.""",
    "9b: and in Section 2.1, where the same sentence stands")

# ---- 10. the two axes do not share a phrase
rep("main.tex",
    r"""room above an authored arrangement --- the fraction of arrangements that
still score above it --- closing.  The same contrast read higher
up the range behaves differently.""",
    r"""room above an authored arrangement --- the fraction of arrangements that
still score above it --- closing.  The same contrast read at higher midranks
behaves differently.""",
    "10: higher up the RANGE and higher up the LADDER were one phrase apart")

# ---- 11. the statistic, out of the dash
rep("main.tex",
    r"""Read in that ceiling-free normalisation --- a
different statistic from the share above: the percentage of causal texts
above the non-causal group's own $\TailZQ$th percentile --- the separation
grows monotonically along the ladder, from""",
    r"""A second statistic reads the same contrast in the ceiling-free form.  Take
the non-causal group's own $\TailZQ$th percentile, and count the share of
causal texts above it.  Read that way the separation grows monotonically
along the ladder, from""",
    "11: the definition as a step, not as an aside",
    marker="A second statistic reads the same contrast")

# ---- 12. the size quoted, and why the other unit is given
rep("main.tex",
    r"""saturate.  Quote that normalisation if a size is to be quoted; in midrank
units the figure is $\ShareEvalMin\%$ to $\ShareEvalMax\%$.""",
    r"""saturate.  The figure this paper quotes for a size is that one.  In midrank
units the same share is $\ShareEvalMin\%$ to $\ShareEvalMax\%$, which is the
form the grid argument below is read in.""",
    "12: the paper's own practice, and why both units appear")

# ---- 13. where the definition ends and the measurement begins
rep("main.tex",
    r"""$\sigma = [\log P_{\mathrm{l2r}}(x) - \log P_{\mathrm{r2l}}(x)]/L$.  This
vanishes identically whenever the model's conditionals come from a joint.""",
    r"""$\sigma = [\log P_{\mathrm{l2r}}(x) - \log P_{\mathrm{r2l}}(x)]/L$.  That
defines $\sigma$ for the class; what this paper measures is $\sigma$ on two
masked evaluators.  It vanishes identically whenever the model's
conditionals come from a joint.""",
    "13: a class definition and a measurement, in separate sentences")

# ---- 14. incompatibility, named where it arises
rep("main.tex",
    r"""orders.  Where that identity holds, $\sigma$ is the same number, zero,
whatever the text; where it fails,
what the range carries is the evaluator's incompatibility.""",
    r"""orders.  That failure to come from one joint is what we call the
evaluator's \emph{incompatibility}.  Where the identity holds, $\sigma$ is
the same number, zero, whatever the text; where it fails, what the range
carries is that incompatibility.""",
    "14: the term defined at the sentence that produces it")

# ---- 15. what needs the data and what does not
rep("main.tex",
    r"""$\Delta$ reverses the text, which moves to another point
of the same law and leaves a fixed text without an origin; what it does
separate is mostly the order the passage was produced in.""",
    r"""$\Delta$ reverses the text, which moves to another point
of the same law and leaves a fixed text without an origin.  That much
follows from the structure of the theorems and needs no measurement.  What
the measurement adds is that what $\Delta$ does separate is mostly the order
the passage was produced in.""",
    "15a: the Delta side is structural, and the abstract did not say so")

rep("main.tex",
    r"""held fixed --- and Eq.~\eqref{eq:fbzero} gives that an origin, so its value
reports the evaluator's incompatibility rather than the text.""",
    r"""held fixed --- and Eq.~\eqref{eq:fbzero} gives that an origin, so its value
reports the evaluator's incompatibility rather than the text; that too
follows from the identity, before anything is measured.""",
    "15b: and so is the sigma side")


# ============================================================== self-scan
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
        print("     %-30s %-28s %r" % (_name, _lab[:26], _hit))

LONG = [(lab, len(s.split())) for lab, b in WROTE
        for s in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", b))
        if len(s.split()) > 50]
if LONG:
    print("\n  !! replacement text has sentences over 50 words:")
    for lab, n in LONG:
        print(f"     {lab[:40]:42s} {n} words")

print(f"done: {N} edits")
