r"""Section 7 had not caught up with the vocabulary Section 2.2 introduced.

Naming the two readings scoped Sections 1 and 2.2 correctly and left the
Discussion saying what it said before, about "the quantity of Ref. [1]"
with no setting attached.  Two of those are now wrong rather than merely
loose, because the paper has since asserted that one of the two readings
is anchored.

  "Its central quantity is unanchored"  (Section 7, last paragraph)

      Half false.  In the ensemble reading Eq. (ensembleread) anchors the
      average at zero.  Unanchored is a property of the fixed-text
      reading.  This is the most quoted sentence of the paper and makes
      an unqualified claim about the framework's central quantity.

  "No identity is available for it and none is claimed"  (Section 7)

      The ensemble reading HAS an identity: the integral fluctuation
      theorem, Ref. [1]'s Eq. (34), which Section 2.2 cites itself.  The
      clause that follows recovers the intended sense, but a reader two
      pages past a passage that named two readings asks which one.

  "Every objection below is to the fixed-text reading"  (abstract)

      The labelling objection is not.  Section 1 says so in its own
      words: "The labelling is a question about the corpora rather than
      about the quantity."  "Every" invites the check, so the sentence
      has to survive it.

AND THE NAMES, where the argument is summarised.  Section 7's first
conclusion is correctly scoped already -- "where the sequences are drawn
from the model itself... about an average, not about one text" -- and
Section 2.2's handover paragraph draws the same distinction in the same
old words.  Introducing names and then not using them at the two places a
reader goes for the summary wastes most of what they were for.

Run:  python fix_scope.py <paper dir>
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


# ------------------------------------------------- 1 unanchored, which one
rep("main.tex",
    r"""empirical claim survives our re-measurement.  Its central quantity is
unanchored, and the quantity it was standing in for is identically zero""",
    r"""empirical claim survives our re-measurement.  Its central quantity is
unanchored in the fixed-text reading, and the quantity it was standing in
for is identically zero""",
    "1: unanchored is a property of one of the two readings")

# ------------------------------------------------- 2 no identity, where
rep("main.tex",
    r"""(The first is not, which is the point of putting it first.)  No identity
is available for it and none is claimed: $\Delta$ is a log-ratio between a""",
    r"""(The first is not, which is the point of putting it first.)  No identity
is available for it on a fixed text, and none is claimed: $\Delta$ is a
log-ratio between a""",
    "2: the ensemble reading has one, so this names where there is none")

# ------------------------------------------------- 3 every objection to what
rep("main.tex",
    r"""non-negative; nothing here disputes it.  Every objection below is to the
\emph{fixed-text reading}, on texts prepared by other models, which is the
setting applied to the corpora re-measured here.""",
    r"""non-negative; nothing here disputes it.  Every objection below to the
quantity is to the \emph{fixed-text reading}, on texts prepared by other
models, which is the setting applied to the corpora re-measured here.  What
the labels record is a separate question, about the corpora rather than
about the quantity, and Section~\ref{sec:construct} weighs it on its own.""",
    "3: the labelling objection is about the corpora, not the quantity")

# ------------------------------------------------- 4 the names, in Section 7
rep("main.tex",
    r"""that holds on the text being read (Section~\ref{sec:notareversal}).  Where
the sequences are drawn from the model itself, Ref.~\cite{sagawa2026}
supplies a zero and a sign by a theorem --- about an average, not about one
text --- and nothing here disputes that.""",
    r"""that holds on the text being read (Section~\ref{sec:notareversal}).  In the
ensemble reading, where the sequences are drawn from the model itself,
Ref.~\cite{sagawa2026} supplies a zero and a sign by a theorem, about an
average and not about one text, and nothing here disputes that.""",
    "4a: Section 7's first conclusion uses the name")

rep("main.tex",
    r"""label, found afterwards, is not: where the theorems reach, the quantity has
that meaning already, and where they do not, no correlation with a label
restores it.""",
    r"""label, found afterwards, is not: in the ensemble reading the quantity has
that meaning already, and in the fixed-text reading no correlation with a
label restores it.""",
    "4b: Section 2.2's handover uses the names")


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
