r"""Section 5 and 5.1 brought onto the spine the introduction now states.

Nothing here is false -- that was checked separately.  What is wrong is
that these were written before the introduction was, and the introduction
has since become the careful statement of the same three things.

  1. THE DEPENDENCE.  "everything after depends on what it records" is
     stronger than the design allows and undoes the reason for the design.
     Every causal-order measurement is made WITHIN a text, where length,
     vocabulary, topic and style are identical by construction; the labels
     enter only as a grouping of the resulting ranks.  The introduction's
     word is "conditional".  A reader who takes "depends" at face value
     has been told the within-text construction buys nothing.

  2. TWO FACTS THE INTRODUCTION HAS AND 5.1 DOES NOT.  5.1 is the section
     that owns the question "what do the labels record, and what do they
     not", and the sharpest statement of the second half is in the
     introduction instead: the non-causal passages are coherent discourse
     whose order is not causal.  So is the asymmetry of the grouping --
     the decomposition is defined against the non-causal group and its
     share changes sign if the groups are exchanged -- which is a
     consequence of USING the labels and belongs where the labels are
     discussed.

     The introduction writes the first as "not incoherent".  5.1 says it
     positively: what the label records is an arrangement, not a defect in
     the writing.  A litotes in the one sentence that tells a reader these
     passages are ordinary prose is the wrong place for one.

  3. WHO RAISED IT.  Ref. [1] raises this about its own corpora in
     Sec. V B, before we do.  The introduction says so and 5.1 does not,
     which leaves the section that makes the criticism looking as though
     it originated it.

Run:  python fix_sec5.py <paper dir>
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


# --------------------------------------------------------- 1 dependence
rep("main.tex",
    r"""re-measured, across a ladder of \TrendNEval\ evaluators.  The labelling comes
first, because everything after depends on what it records.""",
    r"""re-measured, across a ladder of \TrendNEval\ evaluators.  The labelling comes
first, because the labels enter every measurement below only as a grouping
of ranks, and every figure derived from that grouping is reported as
conditional on it.""",
    "1: conditional on the labelling, which is what the design bought")

# ------------------------------------------------------- 3 who raised it
rep("main.tex",
    r"""\label{sec:construct}
The labels record that a language model, given a prompt asking for a short""",
    r"""\label{sec:construct}
What the labels record is a question Ref.~\cite{sagawa2026} raises about its
own corpora before we do~\cite[Sec.~V~B]{sagawa2026}.

The labels record that a language model, given a prompt asking for a short""",
    "3: the original raises it first, and says so")

# ------------------------------------------------ 2a what is NOT recorded
rep("main.tex",
    r"""against any specified causal structure.  ``Causal'' here is the name of a
prompt, not the result of a measurement.""",
    r"""against any specified causal structure.  ``Causal'' here is the name of a
prompt, not the result of a measurement.

What the non-causal label records is an arrangement, and not a defect in the
writing.  Those passages are coherent discourse: their topic continues,
their pronouns resolve backwards, their connectives are in place.  Their
sentence order is simply not causal.  The lengths of the two sets are not
controlled either.""",
    "2a: the second half of this subsection's own title",
    marker="What the non-causal label records")

# ----------------------------------------------- 2b the grouping is a use
rep("main.tex",
    r"""as a contrast between prompt-defined sets and nowhere describe it as a
measurement of causality.""",
    r"""as a contrast between prompt-defined sets and nowhere describe it as a
measurement of causality.

The labels are used asymmetrically as well.  The decomposition of
Section~\ref{sec:decomp} is defined against the non-causal group, and its
share changes sign if the two groups are exchanged.  Every figure derived
from it is therefore conditional on the labelling and not on the texts
alone.""",
    "2b: using the labels as a grouping is still using them",
    marker="The labels are used asymmetrically as well")

SUSPECT = re.compile(
    r"\bthe ones?\s*(?=[.,;:]|\b(?:that|which|it|we|they|the|is|are)\b)|"
    r"\b(?:that kind|this kind|a kind|that form|this form|"
    r"of that|of this|the thing|in this sense|this reading|the other one|"
    r"such a|that of|need not\b(?!\s+\w)|does not\.|do not\.|cannot\.|"
    r"\bis of the\b|\bis of a\b|\band not of\b|\bbut not of\b)", re.I)
bad = [(lab, m.group(0)) for lab, b in WROTE for m in SUSPECT.finditer(b)]
if bad:
    print("\n  !! replacement text contains new pointing constructions:")
    for lab, hit in bad:
        print("     %-40s %r" % (lab, hit))
    raise SystemExit("fix the replacements before shipping this patch")
print(f"done: {N} edits (replacement text clean)")
