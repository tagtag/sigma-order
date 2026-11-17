r"""Section 1 claims a sign consistency the measurement does not have.

"Both constructions place the causal contribution on the same side of zero
... The sign is consistent" reads, next to Table 7, as a claim about cells.
One cell reverses: \texttt{LLaDA}/\textsc{Opus46} gives $r = +0.107$, and
Section 6.3 says so itself -- "the same in \FbNNegative\ of \FbNCells\
cells", "which does reverse in one cell below".  The abstract and the
comparison table on p.9 both already quote the count; Section 1 was the one
place left unqualified.

What is true without qualification is the per-construction aggregate: the
median causal component is negative for every evaluator under both
constructions.  So the aggregate claim is scoped to the median, and the
cell-level statement becomes the count that is already generated -- which is
this paper's own practice everywhere else, and is stronger than "almost"
because it names the exception's size.

Run:  python fix_sign.py <paper dir>
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


rep("sec_intro.tex",
    r"""Both constructions place the causal contribution on the same side of zero,
and it is the side that subtracts: a causal text exposes \emph{less} of the
evaluator's incompatibility, not more.  The sign is consistent and the
magnitude does not reach significance, and in any case a contrast that did""",
    r"""Both constructions place the \emph{median} causal contribution on the same
side of zero, and it is the side that subtracts: a causal text exposes
\emph{less} of the evaluator's incompatibility, not more.  Cell by cell the
sign holds in \FbNNegative\ of the \FbNCells\ evaluator--corpus cells rather
than in all of them, the magnitude does not reach significance, and in any
case a contrast that did""",
    "the aggregate is scoped to the median, the cells are counted")

print(f"done: {N} edits")
