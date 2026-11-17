r"""The abstract's two load-bearing terms, glossed where a reader meets them.

An inventory of every term of art against its first occurrence in reading
order (audit_terms.py) puts five of this paper's terms in the abstract,
twelve occurrences between them, all defined only in Section 3:

    authored arrangement   4 in the abstract,  79 in the body, def. 3.4
    midrank                3                   87              def. 3.3
    permutation set        3                   20              def. 3.3
    authored component     1                   19              def. 3.4
    any-order chain rule   1                    8              def. 3.2

"permutation set" is glossed by the sentence after it ("Score a text's $n$
sentences in all $n!$ orders"), and the last two are single uses.  Two are
worth the words.

AUTHORED.  Section 3.4 says it plainly: "'authored' names the order a text
came in and not an act of authorship."  That is on page 12.  The abstract
uses the word four times before saying, two thirds of the way down, that
the prose was model-generated.  Until then a reader can take "authored" to
mean written by a person -- and the paper's central result is that the
authored arrangement is special, which under that reading is a different
and much more interesting claim than the one being made.  The sense has to
be fixed where the word first appears.

MIDRANK.  Eighty-seven uses in the body and no gloss until Eq. (midrank).
The abstract sentence says what it is LIKE -- unitless, bounded, 0.50 for
a blind score -- without saying it is a rank.  Four words fix that.

Run:  python fix_terms.py <paper dir>
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
    r"""set of values is centred at zero for any score whatever.  The midrank of the authored arrangement within its own set is then unitless, bounded, and exactly
$0.50$ for a score blind to sentence order; it uses no causal labels.""",
    r"""set of values is centred at zero for any score whatever.  A text's
\emph{authored arrangement} is the order it came in; every text here was
produced by a language model, so the word names an order and not an act of
authorship.  Its \emph{midrank} --- where its own $\Delta$ falls among the
$n!$ values --- is then unitless, bounded, and exactly $0.50$ for a score
blind to sentence order, and it uses no causal labels.""",
    "the abstract says what \"authored\" means, and what a midrank is")


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
