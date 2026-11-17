r"""Ref. [1] has two readings of its quantity, and three sentences name one.

Section 2.2 is careful about this and says so at length: Ref. [1]'s
Section V A measures the entropy production of trajectories the model
actually ran, the theorem applies there, "nothing here disputes it"; its
Section V B reads the same expression on externally prepared fixed texts,
and Ref. [1] itself states that the averages are not guaranteed to be
non-negative in that case.  Everything this paper measures concerns the
second reading.

Three sentences elsewhere refer to "the quantity of Ref. [1]" with a
definite article and no marker that there are two readings.  The worst is
in Section 2.2 itself:

    "The quantity of Ref. [1] has no zero that holds on the text being
     read."

Unqualified, that is false of the Section V A reading, which has a zero by
the theorem -- as the same section grants three paragraphs earlier.  The
sentence that follows does supply the qualification, but a reader (or a
referee, or the author of Ref. [1]) meets the overstatement first.

The other two are milder and have the same shape: "the quantity Ref. [1]
defines", where Ref. [1] defines the trajectory quantity and EVALUATES the
fixed-text one; and "what the entropy production of Ref. [1] means",
where the question being posed is about the fixed-text reading.

This is the defect this paper exists to avoid committing.  Its whole case
against Ref. [1] is "each statement there is its own and we take none of
them further than it does; what is not there is their sum" -- and then it
takes a statement about one reading further than that reading.

Run:  python fix_whichquantity.py <paper dir>
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


# ------------------------------------------------- the overstatement
rep("main.tex",
    r"""not the zero.  The quantity of Ref.~\cite{sagawa2026} has no zero that
holds on the text being read.""",
    r"""not the zero.  Read on a text the evaluator did not produce, the quantity
of Ref.~\cite{sagawa2026} has no zero that holds on the text being read.""",
    "1: which reading of it has no zero on the text",
    marker="has no zero that holds on the text being read")

# ------------------------------------------------- defines vs evaluates
rep("sec_truesigma.tex",
    r"""Everything so far measures $\Delta$, the quantity Ref.~\cite{sagawa2026}
defines: a text scored against a rearrangement of itself.""",
    r"""Everything so far measures $\Delta$: a text scored against a rearrangement
of itself, which is what Ref.~\cite{sagawa2026} evaluates on externally
prepared texts~\cite[Sec.~V~B]{sagawa2026}.""",
    "2: evaluated on fixed texts, which is not where the theorem is proved",
    marker="measures $\\Delta$: a text scored against a rearrangement")

# ------------------------------------------------- which question is asked
rep("sec_intro.tex",
    r"""answer can mean, and Section~\ref{sec:construct} weighs it separately.  The first is a question about what the entropy
production of Ref.~\cite{sagawa2026} means, and answering it for a fixed
text needs a comparison whose zero
holds on that text --- which the model class Ref.~\cite{sagawa2026} uses
cannot supply.""",
    r"""answer can mean, and Section~\ref{sec:construct} weighs it separately.  The
first is a question about what the entropy production of
Ref.~\cite{sagawa2026} means once it is read on a text the evaluator did
not produce, and answering it needs a comparison whose zero holds on that
text --- which the model class Ref.~\cite{sagawa2026} uses cannot supply.""",
    "3: the question is about the fixed-text reading, and says so",
    marker="a question about what the entropy production of")

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
