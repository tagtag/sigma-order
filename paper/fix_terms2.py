r"""Two more names the abstract uses before it says what they are.

EVALUATOR.  Six uses in the abstract and no gloss anywhere in it.  That is
not a convenience: this paper's sharpest reservation is that the model
which PRODUCED a text and the model which SCORES it are different models
(Section 4.1), and the word for the second one is "evaluator".  The
abstract's own sentence "All of this is measured on prose that language
models produced" is about the producers, and nothing ties it to the
evaluators.  A reader who takes "evaluator" loosely has the paper's
central caveat in front of them and cannot see it.

The gloss goes at the first use, which is the contrastive one -- "produced
by other models, not by the evaluator" -- where four words finish the
contrast the sentence is already making.

PERMUTATION SET.  Named with a definite article in the abstract, and
constructed in the sentence AFTER it ("Score a text's $n$ sentences in all
$n!$ orders").  The construction is where the name belongs; the two swap
places and the name costs nothing.

Left alone: "the authored component", which the reader marked as
recommended rather than required.  Its abstract sentence is already at the
length budget, which has no headroom, and naming it there means splitting
a sentence to make room for a four-word apposition.  It is named and
defined in Section 3.4.

Run:  python fix_terms2.py <paper dir>
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


rep("main.tex",
    r"""distribution, and the texts at issue were produced by other models, not by
the evaluator (Section~\ref{sec:notareversal}).""",
    r"""distribution, and the texts at issue were produced by other models, not by
the \emph{evaluator}, the model that scores
them (Section~\ref{sec:notareversal}).""",
    "evaluator: the model that scores, which is not the model that produced")

rep("main.tex",
    r"""We supply a zero from an exact antisymmetry of the permutation set
instead.  Score a text's $n$
sentences in all $n!$ orders.""",
    r"""We supply a zero from an exact antisymmetry instead.  Score a text's $n$
sentences in all $n!$ orders: those values are the text's
\emph{permutation set}.""",
    "permutation set: named where it is built, not one sentence earlier")


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
