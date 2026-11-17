r"""The budget ratchet, and a word the build's own diagnostic contradicts.

THE RATCHET.  The build reported 44 sentences over 50 words against a
budget of 54.  The budget comes down to 44.

"FLAT".  ceiling_resolution.py prints a verdict on every build:

    WRONG SIGN.  On the set Eq. (8) is defined on the ceiling fraction
    FALLS by 5.0 of its own steps across the ladder.  That is not a
    question of resolution -- the move is resolved -- it is the opposite
    of what Section 5.4 claims.

The series is 20.0, 15.0, 16.0, 16.0, 15.0 percent.  Section 5.4's body
describes it exactly right -- "the whole of that rho comes from the
smallest evaluator, and the remaining four sit within one point of each
other" -- and then three one-word summaries elsewhere call the series
FLAT.  It is not flat.  It drops five of its own steps at the first rung
and is flat after that, and five steps is a move this paper calls
resolved everywhere else.

The word is also the wrong carrier for the withdrawal.  The saturation
claim is withdrawn because no trend is established, not because the
series is level; "flat" asserts a shape the measurement does not have and
is not needed for the argument.  All three sites take the fact instead.

A referee reading 20, 15, 16, 16, 15 under the word "flat" has been handed
a free objection, and the build has been printing the contradiction all
along with nothing to consume it.

THE CHECK.  "flat" is permitted only in the negative -- "not flat", "nor
flat".  A negated use says a series fails to be level, which is a weak
claim and safe.  A positive use asserts a shape, and a shape is a
measurement: it has to be stated as one.  The paper's two surviving uses
are both negated, so the allow-list costs nothing and the next positive
one has to argue for itself.

Run:  python fix_flat.py <paper dir>
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


# ------------------------------------------------------------- 1 ratchet
rep("check_paper.py",
    "SENTENCE_BUDGET = 54",
    "SENTENCE_BUDGET = 44   # reported by the build after fix_split3",
    "1: the budget comes down to the reported count")

# --------------------------------------------------------------- 2 prose
rep("sec_decomp.tex",
    r"""evaluator so a reader can see the flat series rather than take our word
for it.""",
    r"""evaluator so a reader can see the two series rather than take our word
for it.""",
    "2a: the table shows the series; the prose need not characterise it")

rep("sec_decomp.tex",
    r"""latter, and it is the non-causal column that bears on saturation: it is
flat, which is why this section withdraws that claim.""",
    r"""latter, and it is the non-causal column that bears on saturation: it does
not rise, which is why this section withdraws that claim.""",
    "2b: the caption gives the reason the withdrawal actually rests on")

rep("main.tex",
    r"""we found no upper end to check, the fraction of non-causal texts at the
extreme arrangement being flat across the ladder""",
    r"""we found no upper end to check, the fraction of non-causal texts at the
extreme arrangement establishing no trend across the ladder""",
    "2c: Section 7 says what was measured, not what it looked like")

# --------------------------------------------------------------- 3 check
CHECK = '''FLAT_NEGATED = re.compile(r"\\b(?:not|nor|never|hardly)\\b[^.;:]{0,24}$",
                          re.I)


def check_flat_sense(src):
    """"flat" is permitted only in the negative.

    Three sites called a series flat that runs 20.0, 15.0, 16.0, 16.0,
    15.0 -- a drop of five of its own steps at the first rung, which this
    paper calls resolved everywhere else, and which ceiling_resolution.py
    has been printing as WRONG SIGN on every build.  The body text had it
    right and the summaries did not, which is the shape this file keeps
    finding: the careful statement is made once and a loose one is made
    three times.

    A negated use -- "neither at the floor nor flat", "it is not flat" --
    says a series FAILS to be level.  That is weak and safe.  A positive
    use asserts a shape, and a shape is a measurement: it belongs in the
    sentence as one, with the span and the trend that back it.

    Raising this is a one-line decision with a reason, like any other
    allow-list here.  What it stops is the word going back in as a
    summary of a series someone has not re-read.
    """
    body = re.sub(r"(?<!\\\\)%.*", " ", src)
    flat = re.sub(r"\\s+", " ", body)
    for m in re.finditer(r"\\bflat\\b", flat):
        before = flat[max(0, m.start() - 40):m.start()]
        if not FLAT_NEGATED.search(before):
            fail("flat",
                 "\\"flat\\" asserted of a series: ..." + before[-40:]
                 + "flat... -- say the span and the trend instead, or "
                 "negate it; a series called flat has to be level, and "
                 "the one this rule was written for falls five of its "
                 "own steps")


def check_percentile_sense(src):'''

rep("check_paper.py",
    "def check_percentile_sense(src):",
    CHECK,
    "3a: the check",
    marker="def check_flat_sense")

rep("check_paper.py",
    "    check_percentile_sense(src)",
    "    check_percentile_sense(src)\n    check_flat_sense(src)",
    "3b: invoked",
    marker="\n    check_flat_sense(src)")

SELFTEST = '''

def check_flat_rule():
    """"flat" only in the negative."""
    import check_paper as C
    ok = [r"the contrast is neither at the floor nor flat",
          r"read there it is not flat along the ladder",
          r"it is never flat on this set"]
    bad = [r"a reader can see the flat series",
           r"the non-causal column is flat",
           r"the fraction at the extreme arrangement being flat"]
    for s in ok:
        del C.FAIL[:]
        C.check_flat_sense(s)
        assert not C.FAIL, (s, [m for _, m in C.FAIL])
    for s in bad:
        del C.FAIL[:]
        C.check_flat_sense(s)
        assert C.FAIL, s
    del C.FAIL[:]
    del C.WARN[:]
    print("  catch: a series called flat without the measurement")


check_flat_rule()


check_between_sign_rule()'''

rep("check_paper_selftest.py",
    "\n\n\ncheck_between_sign_rule()",
    SELFTEST,
    "4: its selftest",
    marker="def check_flat_rule")

SUSPECT = re.compile(
    r"\bthe ones?\s*(?=[.,;:]|\b(?:that|which|it|we|they|the|is|are)\b)|"
    r"\b(?:that kind|this kind|a kind|that form|this form|"
    r"of that|of this|the thing|in this sense|this reading|the other one|"
    r"such a|that of|need not\b(?!\s+\w)|does not\.|do not\.|cannot\.|"
    r"\bis of the\b|\bis of a\b|\band not of\b|\bbut not of\b)", re.I)
bad = [(lab, m.group(0)) for lab, b in WROTE
       if lab.startswith("2") for m in SUSPECT.finditer(b)]
if bad:
    print("\n  !! replacement text contains new pointing constructions:")
    for lab, hit in bad:
        print("     %-40s %r" % (lab, hit))
    raise SystemExit("fix the replacements before shipping this patch")
print(f"done: {N} edits (replacement text clean)")
