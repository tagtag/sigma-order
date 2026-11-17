r""""a correlation" three times, with neither side of it named.

    "The theorems that place a quantity's zero and its sign are what say
     what it is a quantity of; a correlation found afterwards is not;
     where those theorems reach, it has that meaning, and where they do
     not, a correlation cannot restore it.  What a correlation does
     establish is that the quantity varies with whatever the label marks"

A correlation between what and what?  The relata only arrive in the fourth
clause, as "the quantity varies with whatever the label marks", by which
point the reader has met the bare word three times.  The sentence also
carries three claims at once, and its "it has that meaning" has no
antecedent closer than "a quantity" two clauses back.

The relata are named once, at the first use, and the later uses point back
at that.  The generality is kept: the claim is about any quantity and any
label, not about Delta and the causal labels in particular, which is why
it sits here and not in Section 5.

Run:  python fix_correlation.py <paper dir>
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


rep("main.tex",
    r"""The theorems that place a quantity's zero and its sign are what
say what it is a quantity of; a correlation found afterwards is not; where those theorems reach, it has that meaning, and where
they do not, a correlation cannot restore it.  What a correlation does
establish is that the quantity varies with whatever the label marks, and how
much of it does is a measurable question.""",
    r"""The theorems that place a quantity's zero and its sign are what
say what it is a quantity of.  A correlation between that quantity and a
label, found afterwards, is not: where the theorems reach, the quantity has
that meaning already, and where they do not, no correlation with a label
restores it.  What such a correlation does establish is that the quantity
varies with whatever the label marks, and how much of it does is a
measurable question.""",
    "the two sides of the correlation are named at its first use")

print(f"done: {N} edits")
