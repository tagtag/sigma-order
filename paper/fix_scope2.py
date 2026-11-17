r"""The twins of the two sentences Section 7 had scoped, and a check for them.

Scoping "no identity is available for it" in Section 7 left two sentences
of the same family unscoped:

  Section 6.3  "There is no limit in which $\Delta$ becomes zero and no
               identity to appeal to"
  Section 1    "Nothing in that is an identity, and no identity is
               available"

Both are true of the fixed-text reading and false of the ensemble one,
where Ref. [1]'s Eq. (34) is exactly such an identity -- a point Section
2.2 makes itself, citing Ref. [1] describing the theorem as automatically
satisfied.

The shape is worth naming, because nothing in this paper could have caught
it.  Each sentence is internally consistent, cites nothing, breaks no
budget and contradicts no other sentence here.  It is wrong only against
Ref. [1], and only for a reader who knows Eq. (34).  So the check below
does not look for a contradiction; it requires that a claim about the
ABSENCE of an identity, a zero, an origin or an anchor say which reading
it is made in.  That much is a shape.

AND "FLOOR", which this paper uses in three senses -- the resolution of
the $1/n!$ grid, the attainable minimum of an exact $p$, and the part of
$\sigma$ that no ordering explains -- twice without a qualifier:

  Section 7  "Read in the upper tail it leaves the floor"
  Section 8  "The masked floor is characterised only in..."

The first takes the name the clause before it already implies.  The second
is a heading that introduces a term its paragraph never defines, with the
definition sitting in the paragraph's last sentence; moving it forward
costs nothing.

(The resolution sense is itself called two things, "the grid floor" and
"the resolution floor", one occurrence each.  Picking one is a separate
sweep and is not done here.)

Run:  python fix_scope2.py <paper dir>
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


# ------------------------------------------------------- 1 the two twins
rep("sec_truesigma.tex",
    r"""becomes zero and no identity to appeal to: it is a log-ratio between a text""",
    r"""becomes zero and, on a fixed text, no identity to appeal to: it is a
log-ratio between a text""",
    "1: Section 6.3 says which reading has no identity")

rep("sec_intro.tex",
    r"""Nothing in that is an identity, and no identity is
available: $\Delta$ is a log-ratio between a text and its reversal, and""",
    r"""Nothing in that is an identity, and on a fixed text no identity is
available: $\Delta$ is a log-ratio between a text and its reversal, and""",
    "2: Section 1 says the same")

# --------------------------------------------------------- 2 the floors
rep("main.tex",
    r"""Read in the upper tail it leaves the
floor and moves along the ladder.""",
    r"""Read in the upper tail it leaves the
grid floor and moves along the ladder.""",
    "3: which floor, in a paragraph whose previous clause counts grid steps")

rep("main.tex",
    r"""\emph{The masked floor is characterised only in the exactly solvable system.}
Two controls on text remain:""",
    r"""\emph{The masked floor is characterised only in the exactly solvable system.}
It is the part of $\sigma$ that no ordering of the content can explain, and
Appendix~\ref{sec:toy} is where it is measured.  Two controls on text remain:""",
    "4a: the term is defined in the paragraph's first sentence, not its last",
    marker="It is the part of $\\sigma$ that no ordering")

rep("main.tex",
    r"""Their $\sigma$ would bound the part of the masked
reading that no ordering of the content can explain.""",
    r"""Their $\sigma$ would bound it.""",
    "4b: the tail no longer repeats the definition")

rep("main.tex",
    r"""coherent discourse, so what we call authored arrangement mixes topical continuity,
anaphoric dependence and given--new ordering.""",
    r"""coherent discourse, so what we call authored arrangement mixes topical
continuity, backward pronoun resolution and the placement of new
information.""",
    "5: three linguists' terms become three descriptions")

# ----------------------------------------------------------- 3 the check
CHECK = '''# Deliberately narrow.  "no origin" was tried here and taken out: this
# paper says it of several different objects -- the set of $f(p)$, the
# comparison, the expression -- and six of the seven sites were about
# something other than Ref. [1]'s quantity.  A check that cries wolf six
# times to catch one is how the LaTeX errors went unread for weeks.
ABSENCE_CLAIMS = (
    r"\\bno identity\\b",
    r"\\bunanchored\\b",
    r"\\bhas no zero\\b",
    r"\\bno zero that\\b",
)
# A claim of absence is scoped if any of these stands near it.
ABSENCE_SCOPED = re.compile(
    r"fixed[- ]text|on the text being read|single (?:fixed )?text|"
    r"one text|a single reading|for a single|a text the evaluator|"
    r"on the text it is read from",
    re.I)


def check_absence_scope(src):
    """A claim that something is absent has to say where it is absent.

    "No identity is available", "its central quantity is unanchored", "it
    has no zero" are true of the fixed-text reading and false of the
    ensemble one, where Ref. [1]'s Eq. (34) is exactly such an identity.
    Three sentences of this family were live at once, in Sections 1, 6.3
    and 7, and nothing here could have caught them: each is internally
    consistent, cites nothing, breaks no budget, and contradicts no other
    sentence in this paper.  They are wrong only against Ref. [1].

    So this does not look for the contradiction.  It requires the claim to
    name its setting, which is a shape -- a qualifier naming the
    fixed-text reading within a sentence's reach.  A claim that genuinely
    holds in both settings is phrased without these words, or says so and
    adds a qualifier here.
    """
    body = strip_comments(src)
    body = re.sub(r"\\\\begin\\{thebibliography\\}.*?\\\\end\\{thebibliography\\}",
                  " ", body, flags=re.S)
    flat = re.sub(r"\\s+", " ", body)
    for pat in ABSENCE_CLAIMS:
        for m in re.finditer(pat, flat, re.I):
            near = flat[max(0, m.start() - 170):m.end() + 170]
            if not ABSENCE_SCOPED.search(near):
                fail("absence",
                     "\\"%s\\" with no setting named: ...%s... --- the "
                     "ensemble reading of Ref. [1] has an identity and a "
                     "zero (its Eq. (34)), so a claim that there is none "
                     "has to say it is about the fixed-text reading"
                     % (m.group(0), flat[max(0, m.start() - 70):m.end() + 70]))


def check_flat_sense(src):'''

rep("check_paper.py",
    "def check_flat_sense(src):",
    CHECK,
    "6a: the check",
    marker="def check_absence_scope")

rep("check_paper.py",
    "    check_flat_sense(src)",
    "    check_flat_sense(src)\n    check_absence_scope(src)",
    "6b: invoked",
    marker="\n    check_absence_scope(src)")

SELFTEST = '''

def check_absence_scope_rule():
    """A claim of absence that does not say in which reading."""
    import check_paper as C
    ok = [r"on a fixed text no identity is available",
          r"its central quantity is unanchored in the fixed-text reading",
          r"the quantity has no zero that holds on the text being read",
          r"it has no origin, and no theorem reaches a single fixed text"]
    bad = [r"Nothing in that is an identity, and no identity is available",
           r"Its central quantity is unanchored, and the quantity it was",
           r"there is no limit in which it becomes zero and no identity to"]
    for s in ok:
        del C.FAIL[:]
        C.check_absence_scope(s)
        assert not C.FAIL, (s, [m for _, m in C.FAIL])
    for s in bad:
        del C.FAIL[:]
        C.check_absence_scope(s)
        assert C.FAIL, s
    del C.FAIL[:]
    del C.WARN[:]
    print("  catch: an absence claim that does not name its reading")


check_absence_scope_rule()


check_flat_rule()'''

rep("check_paper_selftest.py",
    "\n\ncheck_flat_rule()",
    SELFTEST,
    "7: its selftest",
    marker="def check_absence_scope_rule")


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
        if not _lab[0].isdigit() or _lab[0] in "67":
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
       if lab[0] in "12345" for m in SUSPECT.finditer(b)]
if bad:
    print("\n  !! replacement text contains new pointing constructions:")
    for lab, hit in bad:
        print("     %-40s %r" % (lab, hit))
    raise SystemExit("fix the replacements before shipping this patch")
print(f"done: {N} edits (replacement text clean)")
