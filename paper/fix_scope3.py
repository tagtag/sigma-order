r"""A qualifier that reached half its sentence, and four bare floors.

HALF A FIX.  Section 6.3 now reads

    "There is no limit in which $\Delta$ becomes zero and, on a fixed
     text, no identity to appeal to"

and the qualifier sits in the second clause only.  The first is the same
family: in the ensemble reading there IS a limit in which the quantity
vanishes, and this paper states it two sections earlier -- "its
non-negativity is a statement about an average under $P_\to$, with
equality when the law is invariant under $R$".  Moving the qualifier to
the front scopes both clauses and costs nothing.

That is the fourth half-fix of this kind.  The pattern is always the same:
a repair made where a reader stopped, rather than over the construction
the reader stopped in.

THE ORIGIN FAMILY.  "Equation (delta) lacks an origin", in Section 1,
belongs to the same class and was written by one of these patches
(fix_split2, splitting a 55-word sentence).  Of eight occurrences of the
origin family it is the only one needing a qualifier; the rest are either
qualified already, or about something other than Ref. [1]'s quantity.

That audit is recorded below rather than turned into a check.  Six of the
eight would be false alarms, and a check that cries wolf six times to
catch one is how the LaTeX errors went unread for weeks.  What goes into
the check is "no limit in which", which has one occurrence and is a real
member of the family.

FLOORS.  This paper calls three different things a floor: the resolution
of the $1/n!$ grid, the attainable minimum of an exact $p$, and the part
of $\sigma$ no ordering explains.  Four sites say "the floor" with no
qualifier, one of them a run-in heading, which is read with no context at
all by anyone skimming.  The grid sense takes "grid floor", which names
the object rather than the property it has, is already the majority
spelling after the last patch, and matches the shape of "exact floor" and
"masked floor".

Run:  python fix_scope3.py <paper dir>
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


# --------------------------------------------------- 1 the half-scoped one
rep("sec_truesigma.tex",
    r"""None of this transfers to $\Delta$.  There is no limit in which $\Delta$
becomes zero and, on a fixed text, no identity to appeal to: it is a
log-ratio between a text""",
    r"""None of this transfers to $\Delta$.  On a fixed text there is no limit in
which $\Delta$ becomes zero and no identity to appeal to: it is a
log-ratio between a text""",
    "1: the qualifier in front, where it reaches both clauses")

# --------------------------------------------------- 2 the origin family
rep("sec_intro.tex",
    r"""them it responds to.  Equation~\eqref{eq:delta} lacks an origin.  The""",
    r"""them it responds to.  On a fixed text Eq.~\eqref{eq:delta} lacks an
origin.  The""",
    "2: the one member of the origin family that needed a qualifier")

# --------------------------------------------------- 3 the four bare floors
rep("sec_decomp.tex",
    r"""\paragraph{In the tail it is not at the floor.}""",
    r"""\paragraph{In the tail it is not at the grid floor.}""",
    "3a: the heading, which is read with no context by anyone skimming")

rep("sec_decomp.tex",
    r"""That floor also fixes what the other correlations in this section can be
asked to say,""",
    r"""That exact floor also fixes what the other correlations in this section can
be asked to say,""",
    "3b: the $p$-value sense, named as Section 8 names it")

rep("sec_decomp.tex",
    r"""the midrank range, where it is not at the floor.  Read there it is not flat""",
    r"""the midrank range, where it is not at the grid floor.  Read there it is not
flat""",
    "3c: Section 5.4 referring back to that heading")

rep("sec_intro.tex",
    r"""range the same contrast is neither at the floor nor flat.""",
    r"""range the same contrast is neither at the grid floor nor flat.""",
    "3d: Section 1")

# --------------------------------------------------- 4 the check, and the audit
rep("check_paper.py",
    '''    r"\\bno zero that\\b",
)''',
    '''    r"\\bno zero that\\b",
    r"\\bno limit in which\\b",
)
# AUDITED ONCE, NOT CHECKED: the "origin" family, 2026-11-15, eight
# occurrences.  Only Section 1's "Eq. (1) lacks an origin" needed a
# qualifier; two carry one already, and five are about something other
# than Ref. [1]'s quantity -- the set of f(p), the comparison, the
# expression, and the origin this paper supplies.  Adding the family here
# would fail six true sentences to catch one false one.  Re-audit by hand
# if the family grows; do not widen this tuple to cover it.''',
    "4a: \"no limit in which\" joins the family, and the audit is recorded",
    marker="no limit in which")

SELFTEST_ADD = '''    bad = [r"Nothing in that is an identity, and no identity is available",
           r"Its central quantity is unanchored, and the quantity it was",
           r"there is no limit in which it becomes zero and no identity to",
           r"There is no limit in which $\\Delta$ becomes zero, and it is a"]'''

rep("check_paper_selftest.py",
    '''    bad = [r"Nothing in that is an identity, and no identity is available",
           r"Its central quantity is unanchored, and the quantity it was",
           r"there is no limit in which it becomes zero and no identity to"]''',
    SELFTEST_ADD,
    "4b: the selftest covers the new member",
    marker="becomes zero, and it is a")


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
        if _lab[0] == "4":
            continue
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
bad = [(lab, m.group(0)) for lab, b in WROTE
       if lab[0] in "123" for m in SUSPECT.finditer(b)]
if bad:
    print("\n  !! replacement text contains new pointing constructions:")
    for lab, hit in bad:
        print("     %-40s %r" % (lab, hit))
    raise SystemExit("fix the replacements before shipping this patch")
print(f"done: {N} edits (replacement text clean)")
