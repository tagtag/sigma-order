r"""The other half of the abstract's ellipsis.

fix_abs_ellipsis.py supplied the head noun on the first arm and left the
second:

    "is A REVERSAL OF the text's sentence blocks and not OF its tokens"

"not of its tokens" elides "a reversal" exactly as the first arm did
before it was fixed.  Half a fix is what happens when the repair is made
where the reader stopped rather than over the whole construction.

The noun construction is the thing to drop.  As a verb there is no head to
elide on either arm, and the sentence loses a word:

    "The reported separation is obtained by reversing the text's sentence
     blocks, not its tokens:"

Run:  python fix_abs_reversal.py <paper dir>
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
    r"""sentence order is arbitrary.  The reversal that carries the reported
separation is a reversal of the text's sentence blocks and not of its
tokens:""",
    r"""sentence order is arbitrary.  The reported separation is obtained by
reversing the text's sentence blocks, not its tokens:""",
    "the noun construction goes, and with it both elided heads")

SUSPECT = re.compile(
    r"\b(?:the one|the ones|that kind|this kind|a kind|that form|this form|"
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
