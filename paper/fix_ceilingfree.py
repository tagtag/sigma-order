r"""A coinage used fourteen lines before anything says what it means.

"ceiling-free" appears first in the abstract-facing part of Section 1:

    That figure is in the ceiling-free normalisation of Section 5.3,
    which is the one to quote if a size is to be quoted

and is then used eleven more times.  Nothing between the coinage and
Section 5.3 says what the ceiling is.  A reader has to carry the word
"bounded", two sentences earlier, across to "ceiling-free" and work out
that the bound IS the ceiling -- and the statistic that has no ceiling is
named nowhere until Section 5.3.

The gloss is one clause: z is the distance in standard deviations of the
permutation set, so it has no upper bound and cannot saturate.  Put at
first use it costs a reader nothing and saves the other eleven.

The same sentence also says "the one to quote", eliding "normalisation".
Both are the same defect -- the sentence points instead of naming -- and
both go.

AND THE ABSTRACT NAMES IT TWICE, DIFFERENTLY.  Twenty lines later the same
abstract says "In units with no ceiling", and Section 5.4 says "the
ceiling-free form" for that same reading.  Three names for one idea, one
of them inside the abstract that coined the first.  Worse, "units with no
ceiling" is not accurate: the number reported there is a percentage of
texts, which is bounded at 100.  What has no ceiling is the z scale the
percentile is taken on.  Reusing the glossed name says that and costs no
words.

NOT CHECKABLE.  A coinage used before it is glossed has no shape a regex
can find: "ceiling-free" reads like self-explanatory English, which is
exactly why it passed every reading until someone asked.  This one stays
on the reader.

Run:  python fix_ceilingfree.py <paper dir>
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
    r"""That figure is in the
ceiling-free
normalisation of Section~\ref{sec:resolution}, which is the one to quote
if a size is to be quoted; in midrank units it is $\ShareEvalMin\%$ to
$\ShareEvalMax\%$.""",
    r"""That figure is in the
ceiling-free
normalisation of Section~\ref{sec:resolution}: the distance in standard
deviations of the permutation set, which has no upper bound and so cannot
saturate.  Quote that normalisation if a size is to be quoted; in midrank
units the figure is $\ShareEvalMin\%$ to $\ShareEvalMax\%$.""",
    "1: the coinage is glossed where it is coined")

rep("main.tex",
    r"""median over corpora.  In units with no ceiling --- a
different statistic from the share above: the percentage of causal texts
above the non-causal group's own $\TailZQ$th percentile --- that separation
grows monotonically along the ladder, from""",
    r"""median over corpora.  Read in that ceiling-free normalisation --- a
different statistic from the share above: the percentage of causal texts
above the non-causal group's own $\TailZQ$th percentile --- the separation
grows monotonically along the ladder, from""",
    "2: one name for it, and the name that was just glossed")

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
