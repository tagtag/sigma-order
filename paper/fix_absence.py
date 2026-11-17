r"""The absence sentence: open the subject instead of eliding the second head.

    "The absence is not of a number but of an independent number"

Both "of" phrases hang on "absence", which is correct English and still
makes the reader carry the head across the "but".  Supplying it again --
"but the absence of an independent number" -- breaks the parallel, since
"of X" and "the absence of Y" are not the same kind of phrase; and "but
that of an independent number" puts a pro-form back in, which is the habit
this whole pass is for.

Opening the subject removes the construction instead: "not of X but of Y"
becomes "not X but Y", with no head to carry and no pronoun.  It also puts
the contrast where the argument wants it -- on INDEPENDENT, not on
number.

Run:  python fix_absence.py <paper dir>
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


rep("sec_truesigma.tex",
    r"""about the text.  The
absence is not of a number but of an independent number: a""",
    r"""about the text.  What is
absent is not a number but an independent number: a""",
    "the subject is opened, so neither head has to be carried")

SUSPECT = re.compile(
    r"\b(?:the one|the ones|that kind|this kind|a kind|that form|this form|"
    r"of that|of this|the thing|in this sense|this reading|the other one|"
    r"such a|that of|need not\b(?!\s+\w)|does not\.|do not\.|cannot\.|"
    r"\bis of the\b|\bis of a\b)", re.I)
bad = [(lab, m.group(0)) for lab, b in WROTE for m in SUSPECT.finditer(b)]
if bad:
    print("\n  !! replacement text contains new pointing constructions:")
    for lab, hit in bad:
        print("     %-40s %r" % (lab, hit))
    raise SystemExit("fix the replacements before shipping this patch")
print(f"done: {N} edits (replacement text clean)")
