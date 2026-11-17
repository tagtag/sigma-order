r"""A withdrawal is one decision that lands in two places.

RETIRED in make_tables.py covers the macros, and the orphan check makes
that half impossible to leave half done: drop a number without declaring
it and the build says so.

The prose half had neither a list nor a check.  That is the whole of why
three separate half-removals were still in the paper this week:

  \texttt{bert-large}   its parameter count was retired with the
                        pseudo-log-likelihood comparison; the name stayed
                        in Section 3.2, in a sentence that had a reason to
                        exist, with no row in the Section 3.1 table.

  pseudo-log-likelihood six mentions survived a withdrawal that needed
                        one, because the mentions were converted from
                        measurements into a record and nobody counted the
                        record.

  "flat"                the saturation claim was withdrawn and three
                        summaries went on calling a falling series flat.

None of these was a slip in execution.  Each was a decision carried out
where a machine was watching and not carried out where none was.

So the withdrawal now declares both halves in one place.  Each word gets a
budget, because "remove every trace" is usually wrong -- a withdrawal that
is worth recording needs the record, and the question nobody asked was how
many times.  A budget of None means the word has a check of its own and is
listed here only so the withdrawal's record is complete.

The three above are registered at the counts they now have, so this is a
regression test for today as well as a trap for tomorrow.

Run:  python fix_withdrawn.py <paper dir>
"""
import io
import os
import sys

os.chdir(sys.argv[1])
N = 0


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


# ----------------------------------------------- 1 the declaration
DECL = '''    "SigmaCausal", "TailZPMax",
)


# The other half of a withdrawal.  RETIRED above is the macros, and the
# orphan check makes that half impossible to leave undone.  This is the
# prose, which had no list and no check: \\texttt{bert-large} outlived the
# retirement of \\ParamsBertLarge by weeks, "pseudo-log-likelihood" kept six
# mentions of a comparison that needed one, and "flat" went on describing a
# series the data had stopped supporting.
#
#   word -> (budget, the withdrawal it belongs to, why that budget)
#
# The budget is not always zero.  A withdrawal worth recording needs the
# record, and the question that went unasked was how many times.  A budget
# of None means the word has a check of its own; it is listed here so one
# place holds the whole of what a withdrawal removed.
WITHDRAWN_FROM_PROSE = {
    "bert-large": (
        0, "the pseudo-log-likelihood comparison",
        "it was in this paper only for that comparison"),
    "pseudo-log-likelihood": (
        1, "the pseudo-log-likelihood comparison",
        "the appendix normalises exp of it as one of three candidate "
        "joints, which is the only place the quantity is computed"),
    "flat": (
        None, "the saturation argument",
        "check_flat_sense() carries this one: the word is permitted only "
        "in the negative, which a count cannot express"),
}


CORPUS_ORDER = ["Opus46", "GPT54", "GPT56", "Gemini31", "Fable5"]'''

rep("make_tables.py",
    '''    "SigmaCausal", "TailZPMax",
)


CORPUS_ORDER = ["Opus46", "GPT54", "GPT56", "Gemini31", "Fable5"]''',
    DECL,
    "1: the prose half is declared beside the macro half",
    marker="WITHDRAWN_FROM_PROSE = {")

# ----------------------------------------------- 2 it travels with the macros
rep("make_tables.py",
    '''    for i in range(0, len(RETIRED), 8):
        out.append("% retired: " + " ".join(RETIRED[i:i + 8]))''',
    '''    for i in range(0, len(RETIRED), 8):
        out.append("% retired: " + " ".join(RETIRED[i:i + 8]))
    # Same route as the retired list: check_paper.py reads the declaration
    # out of macros.tex rather than importing this file.
    for w, (budget, group, why) in sorted(WITHDRAWN_FROM_PROSE.items()):
        out.append("%% withdrawn-prose: %s|%s|%s|%s"
                   % (w, "-" if budget is None else budget, group, why))''',
    "2: the declaration travels with the macros",
    marker="withdrawn-prose: %s")

# ----------------------------------------------- 3 the check
CHECK = '''def check_withdrawn_words(src, tables_dir):
    """A word a withdrawal removed, still in the prose.

    make_tables.py declares what each withdrawal takes out of the text,
    beside the macros it retires, and writes both into macros.tex.  This
    reads the prose half back.

    The failure it is built for is not a slip.  It is a decision taken
    once and carried out only where something was watching: the macro goes
    because the orphan check would catch it, and the word stays because
    nothing would.  Three of those were live in this paper at once.
    """
    mpath = os.path.join(tables_dir, "macros.tex")
    if not os.path.isfile(mpath):
        return
    rules = []
    for line in open(mpath, encoding="utf-8"):
        m = re.match(r"%\\s*withdrawn-prose:\\s*(.+?)\\|(.*?)\\|(.*?)\\|(.*)$",
                     line)
        if m:
            rules.append(tuple(g.strip() for g in m.groups()))
    body = strip_comments(src)
    body = re.sub(r"\\\\begin\\{thebibliography\\}.*?\\\\end\\{thebibliography\\}",
                  " ", body, flags=re.S)
    flat = re.sub(r"\\s+", " ", body)
    for word, budget, group, why in rules:
        if budget == "-":
            continue          # governed by a check of its own
        n = len(re.findall(r"\\b" + re.escape(word) + r"\\b", flat, re.I))
        if n > int(budget):
            fail("withdrawn",
                 "\\"%s\\" appears %d time(s) in the prose.  %s withdrew it "
                 "and allows %s: %s.  Either that withdrawal is not "
                 "finished, or the budget in WITHDRAWN_FROM_PROSE "
                 "(make_tables.py) has to move, with a reason."
                 % (word, n, group[0].upper() + group[1:], budget, why))


def check_model_inventory(src):'''

rep("check_paper.py",
    "def check_model_inventory(src):",
    CHECK,
    "3: the check",
    marker="def check_withdrawn_words")

rep("check_paper.py",
    "    check_model_inventory(src)",
    "    check_model_inventory(src)\n"
    "    check_withdrawn_words(src, args.tables)",
    "4: invoked",
    marker="\n    check_withdrawn_words(src, args.tables)")

SELFTEST = '''

def check_withdrawn_words_rule():
    """A word a withdrawal removed, still in the prose."""
    import check_paper as C
    decl = ("% withdrawn-prose: bert-large|0|the PLL comparison|it was here "
            "only for that\\n"
            "% withdrawn-prose: pseudo-log-likelihood|1|the PLL comparison|"
            "the appendix computes it once\\n"
            "% withdrawn-prose: flat|-|the saturation argument|"
            "check_flat_sense carries it\\n")
    cases = [
        (r"we used \\texttt{bert-base} throughout", False),
        (r"we also ran \\texttt{bert-large}", True),
        (r"a pseudo-log-likelihood is computed in the appendix", False),
        (r"a pseudo-log-likelihood here and a pseudo-log-likelihood there",
         True),
        (r"the series is flat and flat and flat", False),   # delegated
        (r"% bert-large in a comment does not count", False),
    ]
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "macros.tex"), "w") as fh:
            fh.write(decl)
        for prose, want in cases:
            del C.FAIL[:]
            C.check_withdrawn_words(prose, d)
            assert bool(C.FAIL) is want, (prose, [m for _, m in C.FAIL])
    del C.FAIL[:]
    C.check_withdrawn_words(r"\\texttt{bert-large}", "/nonexistent")
    assert not C.FAIL, "no macros.tex means nothing to enforce"
    del C.FAIL[:]
    del C.WARN[:]
    print("  catch: a word a withdrawal removed, still in the prose")


check_withdrawn_words_rule()


check_model_inventory_rule()'''

rep("check_paper_selftest.py",
    "\n\ncheck_model_inventory_rule()",
    SELFTEST,
    "5: its selftest",
    marker="def check_withdrawn_words_rule")

print(f"done: {N} edits")
