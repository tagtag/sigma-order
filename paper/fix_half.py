r"""Three repairs that reached one branch of their construction, and two rules.

The pattern the reader named: a fix is made where someone stopped reading,
not over the construction they stopped in.  Seven of these in two days.

  1. SECTION 7 CONTRADICTS SECTION 8.  "the midrank within it is unitless
     and model-independent" -- and Section 8 spends a whole Limitations
     item saying it is not: "it does not make the measurement independent
     of the evaluator.  It is not", with the numbers.  Dropping the two
     words leaves the recommendation standing on what is true, that the
     midrank removes the unit.

  2. THE BIJECTION.  "makes $R$ a bijection, and also an involution on the
     space it carves out" puts the restriction on the second branch only.
     Ref. [1] restricts the first: "$R_S$ is a bijection on the restricted
     space conditioned on this terminal constraint."  Unrestricted it is
     false.  One comma moves the phrase onto both.

  3. $P_c$ REACHED THE DISPLAY AND NOT THE PROSE.  The display was
     corrected to $\mathbb{E}_{P_c}$ and the same two theorems are then
     restated twice more under $P_\to$.  The remaining $P_\to$ -- in
     $P_\leftarrow = P_\to \circ R$ -- is right and stays: that is the
     backward measure built from the forward one, before any conditioning.

AND TWO RULES, both of the allow-list shape that has worked here before.

  THE BARE FLOOR.  Not every "floor" is ambiguous: "grid floor", "exact
  floor", "masked floor", "its floor", "a floor", "that floor" all carry
  their own antecedent, and banning the word would fail four true
  sentences to catch none.  What is ambiguous is the bare definite "the
  floor" with nothing attached.  Two are left, both in the appendix; they
  take the name the appendix already uses, $\sigEP$.

  THE FLOAT DISTANCE.  Table 3 is cited on page 15 and printed on page 20,
  and that is the right answer rather than a defect: the 25-row table has
  to sit beside Section 5.3, which reads it row by row, and Section 4.2
  cites it for a range.  The distance is the cost of a placement that is
  correct.  An accepted distance is recorded per float, so the expected
  case is silent and a change in it is loud -- and the record says what
  the next person must not do, which is delete the Section 4.2 citation to
  close the gap.

Run:  python fix_half.py <paper dir>
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


# ------------------------------------------------ 1 Section 7 vs Section 8
rep("main.tex",
    r"""within it is unitless and model-independent, at a cost of $n!$ scores rather
than two.""",
    r"""within it is unitless, at a cost of $n!$ scores rather
than two.""",
    "1: Section 8 denies model-independence in a Limitations item of its own")

# ------------------------------------------------------- 2 the bijection
rep("main.tex",
    r"""so that the reversed sequence segments uniquely --- makes $R$ a bijection,
and also an involution on the space it carves out.""",
    r"""so that the reversed sequence segments uniquely --- makes $R$ a bijection,
and also an involution, on the space it carves out.""",
    "2: the restriction is on both, as Ref. [1] puts it on the bijection")

# --------------------------------------------------- 3 the prose restatements
rep("main.tex",
    r"""statements about an average under $P_\to$, and a corpus is an empirical
measure that is not $P_\to$;""",
    r"""statements about an average under $P_c$, and a corpus is an empirical
measure that is not $P_c$;""",
    "3a: the theorem under the measure it is stated for")

rep("main.tex",
    r"""non-negativity is a statement about an average under $P_\to$, with
equality when the law is invariant under $R$.""",
    r"""non-negativity is a statement about an average under $P_c$, with
equality when the law is invariant under $R$.""",
    "3b: and the second restatement")

# --------------------------------------------- 4 the form of the twin fix
rep("main.tex",
    r"""(The first is not, which is the point of putting it first.)  No identity
is available for it on a fixed text, and none is claimed:""",
    r"""(The first is not, which is the point of putting it first.)  On a fixed
text no identity is available for it, and none is claimed:""",
    "4: one form for the family, matching Section 6.3")

# --------------------------------------------------- 5 the two bare floors
rep("main.tex",
    r"""by this, and it is worth saying so where the floor is introduced.""",
    r"""by this, and it is worth saying so where the $\sigEP$ floor is introduced.""",
    "5a: the appendix names the floor it is introducing")

rep("main.tex",
    r"""it here only so that the floor is not mistaken for an unexplained artefact.""",
    r"""it here only so that the $\sigEP$ floor is not mistaken for an unexplained
artefact.""",
    "5b: and the one that refers back to it")

# ----------------------------------------------------------- 6 the two rules
FLOORCHECK = '''def check_bare_floor(src):
    """"the floor", with nothing attached to say which floor.

    This paper calls three things a floor: the resolution of the $1/n!$
    grid, the attainable minimum of an exact $p$, and the part of $\\\\sigma$
    that no ordering explains.  Banning the word would fail four true
    sentences -- "its floor", "a floor", "that floor", "the floor of that
    instrument" all carry their own antecedent -- to catch none.  What
    carries no antecedent is the bare definite article with nothing after
    it, which asks a reader to supply a unique referent where there are
    three.

    A qualifier before the noun needs no rule: "the grid floor" does not
    match this pattern at all.
    """
    body = strip_comments(src)
    flat = re.sub(r"\\s+", " ", body)
    for m in re.finditer(r"\\bthe floor\\b(?!\\s+(?:of|imposed|that|which|in)\\b)",
                         flat, re.I):
        fail("floor",
             "bare \\"the floor\\": ...%s... --- this paper has a grid floor, "
             "an exact floor and a masked floor, so say which, or attach a "
             "phrase that does (\\"the floor of ...\\", \\"its floor\\")"
             % flat[max(0, m.start() - 70):m.end() + 70])


def check_flat_sense(src):'''

rep("check_paper.py",
    "def check_flat_sense(src):",
    FLOORCHECK,
    "6a: the bare-floor rule",
    marker="def check_bare_floor")

rep("check_paper.py",
    "    check_flat_sense(src)",
    "    check_flat_sense(src)\n    check_bare_floor(src)",
    "6b: invoked",
    marker="\n    check_bare_floor(src)")

# ------------------------------------------------- 7 the accepted distance
rep("check_paper.py",
    '''        if rp is not None and cpage - rp > 2:
            warn("floats",
                 f"{name} is first cited on page {rp} and printed on "
                 f"page {cpage}")''',
    '''        allowed = 2
        for prefix, (gap, _why) in FLOAT_DISTANCE_OK.items():
            if caption_text.get(key, "").startswith(prefix):
                allowed = gap
                break
        if rp is not None and cpage - rp > allowed:
            warn("floats",
                 f"{name} is first cited on page {rp} and printed on "
                 f"page {cpage}"
                 + (f"; {allowed} pages are accepted for this float, see "
                    f"FLOAT_DISTANCE_OK" if allowed > 2 else ""))''',
    "7a: an accepted distance per float",
    marker="FLOAT_DISTANCE_OK.items()")

rep("check_paper.py",
    '''    caption_page, ref_page, bib_page = {}, {}, None''',
    '''    caption_page, ref_page, bib_page = {}, {}, None
    caption_text = {}''',
    "7b: the caption text, for keying the allowance",
    marker="caption_text = {}")

rep("check_paper.py",
    '''        for m in re.finditer(r"^(Figure|Table) (\\d+):", txt, re.M):
            caption_page.setdefault((m.group(1), m.group(2)), page)''',
    '''        for m in re.finditer(r"^(Figure|Table) (\\d+):", txt, re.M):
            caption_page.setdefault((m.group(1), m.group(2)), page)
            caption_text.setdefault(
                (m.group(1), m.group(2)),
                re.sub(r"\\s+", " ", txt[m.end():m.end() + 90]).strip())''',
    "7c: captured where the caption is printed",
    marker="caption_text.setdefault(")

ALLOWANCE = '''# Floats whose citation-to-print distance is a placement decision rather
# than a defect, keyed by the opening words of the caption so that the
# entry survives renumbering.  The expected case is silent; a distance
# that GROWS past the entry speaks up again.
#
# Table 3 (Every (evaluator, corpus) cell...) is cited in Section 4.2 for
# a range and read row by row in Section 5.3, and the 25-row float has to
# sit beside the section that reads it.  The distance is the cost of that.
# DO NOT close the gap by deleting the Section 4.2 citation: that citation
# is what makes the range of Dblock checkable against the table, which is
# the hole this paper closed once already.
FLOAT_DISTANCE_OK = {
    "Every (evaluator, corpus) cell":
        (6, "read row by row in Section 5.3, cited for a range in 4.2"),
}


def check_float_placement(pdf, appendix_floats=frozenset()):'''

rep("check_paper.py",
    "def check_float_placement(pdf, appendix_floats=frozenset()):",
    ALLOWANCE,
    "7d: the record, including what not to do about it",
    marker="FLOAT_DISTANCE_OK = {")

SELFTEST = '''

def check_bare_floor_rule():
    """"the floor" with nothing attached."""
    import check_paper as C
    ok = [r"it is not at the grid floor", r"the exact floor of 0.017",
          r"the masked floor is characterised", r"gives it its floor",
          r"which is not a floor", r"the floor of that instrument",
          r"the floor imposed by conditionals", r"the size of that floor"]
    bad = [r"Read in the upper tail it leaves the floor and moves",
           r"so that the floor is not mistaken for an artefact"]
    for s in ok:
        del C.FAIL[:]
        C.check_bare_floor(s)
        assert not C.FAIL, (s, [m for _, m in C.FAIL])
    for s in bad:
        del C.FAIL[:]
        C.check_bare_floor(s)
        assert C.FAIL, s
    del C.FAIL[:]
    del C.WARN[:]
    print("  catch: a floor with nothing saying which floor")


check_bare_floor_rule()


check_absence_scope_rule()'''

rep("check_paper_selftest.py",
    "\n\ncheck_absence_scope_rule()",
    SELFTEST,
    "8: its selftest",
    marker="def check_bare_floor_rule")


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
        if _lab[0] not in "12345":
            continue
        for _m in re.finditer(_pat, re.sub(r"\s+", " ", _b)):
            shaped.append((_name, _lab, _m.group(0)))
if shaped:
    print("\n  !! replacement text uses shapes the build budgets:")
    for _name, _lab, _hit in shaped:
        print("     %-34s %-30s %r" % (_name, _lab[:28], _hit))
print(f"done: {N} edits")
