r"""The long-sentence tail, batch 2: the three longest, 299 words between them.

  1. Section 7, 118 words -- the longest sentence in the paper.  Four
     measurements joined by a colon, two commas and a semicolon: that the
     contrast leaves the floor, where it does so, what the causal group
     reaches at the top of the range, and how that grows along the ladder.

  2. Section 5.4, 110 words.  A promise ("we claim only what the ladder
     supports") followed by four claims in a "that ..., that ..., and
     that ..." list.  The list becomes sentences, so each claim can be
     checked on its own.

  3. Section 5.4, 71 words.  A measurement, then why this form is the one
     the paper leads with.  A semicolon becomes a full stop.

Split, not rewritten: every claim clause keeps its words, and the diff
shows only sentence boundaries, capitalisation and connectives changing.

AND the build now prints the long-sentence count on every run.  The budget
was a ratchet with no gauge: the only way to learn the current number was
to set the budget too low and read it off the failure.  The number joins
the summary line, and the budget comes down to it in the next patch --
lowered to what the build reports, not to what this script estimates.

One refinement to the self-scan, written down because it was nearly a
false fix: "the one rung differing in more than size" is the numeral with
its noun present, carried through unchanged from the source, and not the
pro-form the scan is looking for.

Run:  python fix_split3.py <paper dir>
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


# ------------------------------------------------------------------ 1
rep("main.tex",
    r"""Read in the upper tail it leaves the
floor and moves along the ladder:
no evaluator separates the labelled groups by more than
$\TailBelowOnsetMax$ points below a midrank of $\TailOnsetThr$ and every one
of them does above it,
and at the top of the range the causal group reaches the most costly
arrangement $\TailDiffGPTtwo$ to $\TailDiffQwen$ points more often, as a
median over corpora; in
ceiling-free units that separation grows monotonically along the ladder
($\rho = \TailZTrendRho$, $p = \TailZTrendP$), and on the
\TailZFamNEval\ rungs that share a family, where only size differs, it
keeps the same ordering""",
    r"""Read in the upper tail it leaves the
floor and moves along the ladder.  No evaluator separates the labelled
groups by more than
$\TailBelowOnsetMax$ points below a midrank of $\TailOnsetThr$, and every
one of them does above it.
At the top of the range the causal group reaches the most costly
arrangement $\TailDiffGPTtwo$ to $\TailDiffQwen$ points more often, as a
median over corpora.  In
ceiling-free units that separation grows monotonically along the ladder
($\rho = \TailZTrendRho$, $p = \TailZTrendP$).  On the
\TailZFamNEval\ rungs that share a family, where only size differs, it
keeps the same ordering""",
    "1: the longest sentence in the paper, 118 words, becomes five")

# ------------------------------------------------------------------ 2
rep("sec_decomp.tex",
    r"""We therefore do not extrapolate past $\ParamsQwen$, and we claim only what
the ladder supports: $\ShareZMin\%$ to $\ShareZMax\%$ of what $\Delta$
measures is attributable to causal order in ceiling-free units
($\ShareEvalMin\%$ to $\ShareEvalMax\%$ on the midrank), that the midrank
component sits at \CausalCompStepsMin--\CausalCompStepsMax\ steps of the
grid at every size we measured, that the room above an authored arrangement does not measurably close ($\RoomGPTtwo$ to $\RoomQwen$, \AuthoredCompSpanSteps\ step of the same grid), and that the same contrast read in the tail both clears its floor and grows along the ladder, an ordering that does not depend on the one rung differing in more than size.""",
    r"""We therefore do not extrapolate past $\ParamsQwen$, and we claim only what
the ladder supports.  $\ShareZMin\%$ to $\ShareZMax\%$ of what $\Delta$
measures is attributable to causal order in ceiling-free units
($\ShareEvalMin\%$ to $\ShareEvalMax\%$ on the midrank).  The midrank
component sits at \CausalCompStepsMin--\CausalCompStepsMax\ steps of the
grid at every size we measured.  The room above an authored arrangement
does not measurably close ($\RoomGPTtwo$ to $\RoomQwen$,
\AuthoredCompSpanSteps\ step of the same grid).  And the same contrast read
in the tail both clears its floor and grows along the ladder, an ordering
that does not depend on the one rung differing in more than size.""",
    "2: four claims after a colon become four sentences")

# ------------------------------------------------------------------ 3
rep("sec_decomp.tex",
    r"""\TailTrendRho$ ($p = \TailTrendP$), which by the rule above establishes
nothing either way; we lead with the ceiling-free form because its null
is fixed by construction and it has no bound to saturate against, not
because it gives the smaller $p$.""",
    r"""\TailTrendRho$ ($p = \TailTrendP$), which by the rule above establishes
nothing either way.  We lead with the ceiling-free form because its null
is fixed by construction and it has no bound to saturate against, not
because it gives the smaller $p$.""",
    "3: the measurement, then the reason for leading with it")

# ------------------------------------------------------------------ 4
# The budget is a ratchet, but nothing reports the current count unless it
# FAILS, so the only way to lower it was to break the build on purpose.
# The count joins the summary line, and the budget comes down with it.
rep("check_paper.py",
    '''    long = [s for s in prose_sentences(src) if len(s.split()) > SENTENCE_WORDS]
    if len(long) > SENTENCE_BUDGET:''',
    '''    long = [s for s in prose_sentences(src) if len(s.split()) > SENTENCE_WORDS]
    globals()["NLONG"] = len(long)   # reported in the summary line
    if len(long) > SENTENCE_BUDGET:''',
    "4a: the count is kept",
    marker='globals()["NLONG"]')

rep("check_paper.py",
    "SENTENCE_WORDS = 50\nSENTENCE_BUDGET = 54",
    "SENTENCE_WORDS = 50\n"
    "# The budget is lowered to the number the build reports, never to a\n"
    "# number guessed here: a guess that is one too low fails a build for a\n"
    "# reason that has nothing to do with the paper.\n"
    "SENTENCE_BUDGET = 54\nNLONG = 0",
    "4b: the ratchet runs on the reported number, not an estimate",
    marker="never to a\n")

rep("check_paper.py",
    '''          f"{ntrd} non-significant trend(s), {nsep} appendix-only macro(s)")''',
    '''          f"{ntrd} non-significant trend(s), {nsep} appendix-only macro(s), "
          f"{NLONG} sentence(s) over {SENTENCE_WORDS} words (budget "
          f"{SENTENCE_BUDGET})")''',
    "4c: reported on every build",
    marker="sentence(s) over {SENTENCE_WORDS}")


# The self-scan, with one refinement.  "the one" as a PRO-FORM is the
# defect ("the one that has a reverse process"); "the one rung differing in
# more than size" is the numeral with its noun present, and is carried
# through this patch unchanged from the source.  Require the pro-form
# reading: punctuation or a function word after it, not a noun.
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
