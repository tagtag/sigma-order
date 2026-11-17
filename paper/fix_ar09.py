r"""The budget caught the patch that tightened it.

fix_ar06 put BARE_NOUN_BUDGET["quantity"] back to 16.  fix_ar08 then wrote

    What the quantity means is settled there and in Section~\ref{sec:truesigma}

into Section 5's opening, which is a bare "the quantity" in a paper that
calls three different things a quantity, and the build failed at 17.

That is the rule working.  Had fix_ar05's 21 still been in place the
sentence would have gone in unnoticed, and a reader of Section 5 would
have met "the quantity" with $\Delta$, $\sigma$ and $\sigma_{EP}$ all in
scope and no way to tell which.  The budget is worth what it costs only
when it is the number the paper actually has.

The quantity meant there is $\Delta$: Section 2.2 is about what
Ref. [1]'s own measurement means, and Ref. [1]'s measurement is
Eq. (1).  Naming it costs one word.

The other edit is the 51-word sentence fix_ar08's self-scan flagged.  The
flag was not a rise -- the original said "the same measurement" where the
replacement says "a different measurement", three words for three, so the
sentence was 51 words before the patch as well and the over-50 count did
not move.  It is still too long to read in one pass, and the colon in it
is already doing the work a full stop would do.  Splitting takes the count
from 43 to 42.

A note for the patches after this one: the self-scan in fix_ar02 and
fix_ar08 reports a long sentence in replacement text without checking
whether the sentence it replaced was long too, so it cannot tell a new
problem from an inherited one.  It also says nothing about bare ambiguous
nouns, which is what actually broke this build.  Both are added below and
should be carried forward.

Run:  python fix_ar09.py <paper dir>
"""
import io
import os
import re
import sys

os.chdir(sys.argv[1])
N = 0
WROTE = []


def rep(path, a, b, label):
    global N
    assert a not in b, f"{label}: b contains a"
    s = io.open(path, encoding="utf-8").read()
    if s.count(a) == 0 and s.count(b) >= 1:
        print(f"  (already) {label}")
        return
    assert s.count(a) == 1, f"{label}: found {s.count(a)} in {path}"
    io.open(path, "w", encoding="utf-8").write(s.replace(a, b))
    WROTE.append((label, a, b))
    print(f"  {label}")
    N += 1


rep("main.tex",
    r"""step.  What the quantity means is settled there and in""",
    r"""step.  What $\Delta$ means is settled there and in""",
    "1: the quantity is Delta, and Section 5 now says so")

rep("sec_intro.tex",
    r"""it in part without settling it: the distance $\Delta$ reports can be""",
    r"""it in part without settling it.  The distance $\Delta$ reports can be""",
    "2: 51 words split in two; over-50 count 43 -> 42")

print(f"done: {N} edits")


# --------------------------------------------------------- self-scan, mk2
def _nouns():
    try:
        src = io.open("check_paper.py", encoding="utf-8").read()
        ns = {}
        exec(re.search(r"AMBIGUOUS_NOUNS = \(.*?\)", src, re.S).group(0), ns)
        exec(re.search(r"NOUN_QUALIFIERS = \(.*?\)", src, re.S).group(0), ns)
        return ns["AMBIGUOUS_NOUNS"], ns["NOUN_QUALIFIERS"]
    except Exception as exc:
        print(f"  (no noun self-scan: {exc})")
        return (), ()


AMB, QUAL = _nouns()
bad = []
for lab, a, b in WROTE:
    for noun in AMB:
        pat = r"\bthe %s\b(?!\s+(?:%s))" % (noun, "|".join(QUAL))
        before = len(re.findall(pat, re.sub(r"\s+", " ", a)))
        after = len(re.findall(pat, re.sub(r"\s+", " ", b)))
        if after > before:
            bad.append((lab, noun, after - before))
if bad:
    print("\n  !! this patch ADDS bare ambiguous nouns -- the build will fail:")
    for lab, noun, n in bad:
        print('     %-40s +%d bare "the %s"' % (lab[:40], n, noun))

grew = []
for lab, a, b in WROTE:
    def longest(t):
        ss = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", t))
        return max((len(s.split()) for s in ss), default=0)
    if longest(b) > 50 and longest(b) > longest(a):
        grew.append((lab, longest(a), longest(b)))
if grew:
    print("\n  !! replacement text LENGTHENS a sentence past 50 words:")
    for lab, x, y in grew:
        print(f"     {lab[:40]:42s} {x} -> {y} words")
