r"""One word, from the tenth read's own correction.

The preamble written in fix_coldread_j.py says "Section 2.2 ended at
Ref. [1]'s own first step".  Section 2.2 does not end there: the handoff
paragraph sits about two thirds in, and eight paragraphs and the comparison
table follow it.  Section 6's preamble shows the form that carries no claim
about position -- "Section 2.2 GAVE THE REASON it has no origin" -- verb and
object, no location.  "named" does the same work here.

Run:  python fix_coldread_k.py <paper dir>
"""
import io
import os
import sys

os.chdir(sys.argv[1])
N = 0


def rep(path, a, b, label, marker=None):
    """marker: text unique to the result, required when b still contains a."""
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


rep("main.tex",
    r"""Section~\ref{sec:notareversal} ended at Ref.~\cite{sagawa2026}'s own first""",
    r"""Section~\ref{sec:notareversal} named Ref.~\cite{sagawa2026}'s own first""",
    "the preamble claims a handoff, not a position")

print(f"done: {N} edits")
