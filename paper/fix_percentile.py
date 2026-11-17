r"""The percentile rule inverts: one permitted form, everything else fails.

fix_glossary.py narrowed "percentile" to "percentile of", and that only
catches the preposition.  The midrank under the wrong name is one keystroke
away in every other direction, and this paper writes possessives constantly
("the authored arrangement's rank among the $n!$", "the non-causal group's
own ... percentile"):

    the percentile of the authored arrangement     caught
    the authored arrangement's percentile          NOT caught
    its percentile                                 NOT caught
    percentile within its permutation set          NOT caught
    percentile rank                                NOT caught

Enumerating prepositions never finishes.  The paper already has the right
pattern for this and applies it to its own symbols -- "this paper reserves
$\sigma$ for Eq. (3)" -- which fixes the permitted use instead of counting
the forbidden ones.  So: the only permitted form is an ordinal,
"<number>th percentile", as all five sites in the text and tab_tail's
generated header write it.  Everything else fails.

A string rule cannot tell the two SENSES apart -- "the authored arrangement
sits at the 85th percentile" would pass, and means the midrank -- so the
note in glossary.txt states the sense rather than the spelling, which is
what stops a later reader from widening it back.

One site has to move: Section 5.4's "measured against the non-causal
group's own percentile" is the bare possessive, back-referring to the
$\TailZQ$th percentile four paragraphs above.  It gets the ordinal the
other four sites have, which is also clearer at the distance it is read.

Run:  python fix_percentile.py <paper dir>
"""
import io
import os
import sys

os.chdir(sys.argv[1])
N = 0

CHECK = '''PERCENTILE_OK = re.compile(r"(\\d+|\\\\[A-Za-z]+)\\$?\\s*th\\s*$")


def check_percentile_sense(src):
    """One permitted spelling of "percentile": an ordinal.

    glossary.txt bans phrases, which works where the misuse has a fixed
    shape.  This one does not: the midrank called a percentile can be
    written with any preposition or with a possessive, and this paper
    writes possessives throughout, so a banned-form list cannot close.
    The permitted form is fixed instead -- "<number>th percentile", which
    is how all of the text's uses and tab_tail's header write the quantile
    -- and everything else fails.

    The two senses are not distinguishable by string: "sits at the 85th
    percentile" passes this and would mean the midrank.  glossary.txt
    carries the sense, this carries the spelling.
    """
    flat = re.sub(r"\\s+", " ", src)
    for m in re.finditer(r"percentile", flat):
        before = flat[max(0, m.start() - 48):m.start()]
        if not PERCENTILE_OK.search(before):
            fail("percentile",
                 "\\"percentile\\" without an ordinal: ..."
                 + before[-40:] + "percentile... -- this paper says "
                 "\\"midrank\\" for a position in a permutation set, and "
                 "spells the quantile \\"<number>th percentile\\"")


def check_quantities(src, tables_dir):'''

SELFTEST = '''check_orphan_rule()


def check_percentile_rule():
    """The ordinal is the only permitted spelling; the rest must fail."""
    import check_paper as C
    ok = [r"above the non-causal group's own $\\TailZQ$th percentile",
          r"the non-causal $90$th percentile (null $10\\%$)",
          "causal texts above the non-causal group's own\\n$\\\\TailZQ$th "
          "percentile, so its null"]
    bad = [r"the percentile of the authored arrangement",
           r"the authored arrangement's percentile",
           r"its percentile among the $n!$ arrangements",
           r"the percentile rank of the written order",
           r"percentile within its permutation set"]
    for s in ok:
        C.FAIL[:] = []
        C.check_percentile_sense(s)
        assert not C.FAIL, (s, [m for _, m in C.FAIL])
    for s in bad:
        C.FAIL[:] = []
        C.check_percentile_sense(s)
        assert C.FAIL, s
    C.FAIL[:] = []
    del C.WARN[:]
    print("  catch: percentile written for a midrank, in any construction")


check_percentile_rule()
'''


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
    print(f"  {label}")
    N += 1


# ============================================= 1: the one site that moves
rep("sec_decomp.tex",
    r"""and the ceiling-free tail contrast above, which is measured against the
non-causal group's own percentile.""",
    r"""and the ceiling-free tail contrast above, which is measured against the
non-causal group's own $\TailZQ$th percentile.""",
    "1: the bare possessive gets the ordinal the other four sites have")

# ============================================= 2: the allow-list check
rep("check_paper.py",
    "def check_quantities(src, tables_dir):",
    CHECK,
    "2: one permitted spelling, everything else fails",
    marker="def check_percentile_sense")

rep("check_paper.py",
    "    check_between_sign(src, args.tables)",
    "    check_between_sign(src, args.tables)\n"
    "    check_percentile_sense(src)",
    "3: invoked",
    marker="check_percentile_sense(src)\n")

# ============================================= 4: glossary carries the sense
rep("glossary.txt",
    "[tex] midrank | median position, percentile of   #",
    "[tex] midrank | median position   #",
    "4: the spelling moves to check_percentile_sense")

rep("glossary.txt",
    '"percentile" is the same case: the bare word is a quantile of a '
    'distribution of values (Section 5.4\'s tail statistic, and tab_tail\'s '
    'header), and only "percentile of" -- the midrank under the wrong '
    'name -- is the error this rule exists for',
    '"percentile" is NOT the same case and is not listed here: a '
    'banned-form list cannot close over it, because the midrank can be '
    'called a percentile with any preposition or with a possessive, and '
    'this paper writes possessives throughout.  check_percentile_sense() '
    'fixes the permitted spelling instead -- an ordinal, "<number>th '
    'percentile" -- and fails everything else.  The SENSE that spelling is '
    'permitted FOR is a quantile of a distribution of values (Section '
    '5.4\'s tail statistic, and tab_tail\'s header), never a position '
    'within a permutation set; "sits at the 85th percentile" passes the '
    'spelling check and is still wrong, which is why this note states the '
    'sense and not the string',
    "5: the note states the sense, which no string rule can carry",
    marker="NOT the same case and is not listed here")

# ============================================= 6: the selftest
rep("check_paper_selftest.py",
    "check_orphan_rule()\n",
    SELFTEST,
    "6: its selftest, five permitted-adjacent forms and five misuses",
    marker="check_percentile_rule")

print(f"done: {N} edits")
