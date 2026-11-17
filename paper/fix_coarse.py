r"""Two pointings in one clause, in the sentence that fixes the grain.

    "--- the coarse-graining the published analysis adopts, and the one
     every number below is read on."

"the published analysis" is Ref. [1], which this paper names by citation
everywhere else; a reader has to decide whether it means Ref. [1] or prior
work in general, and the sentence gives no way to tell.  "the one" then
elides "coarse-graining" a second time.

The clause is also carrying two separate facts on one dash: that the grain
is not ours to choose, and that everything below sits on it.  They become
two sentences.

Run:  python fix_coarse.py <paper dir>
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
    r"""sentence blocks rather than the tokens --- the coarse-graining the published
analysis
adopts, and the one every number below is read on.""",
    r"""sentence blocks rather than the tokens.  That is the coarse-graining
Ref.~\cite{sagawa2026} adopts, and every number below is read on it.""",
    "the reference is named and the head noun is supplied once")

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
