r"""The between-set sign claim, checked where the real values are.

Companion to fix_between.py.  Section 6.3 now reports that the two masked
evaluators disagree in sign on the between-set reading.  That is a measured
claim, and the measurement behind it was wrong for several revisions -- the
macros came from a single-evaluator file -- so the number is checked rather
than trusted.

The check belongs in check_paper.py and not in make_tables.py: the generator
is exercised by synthetic fixtures in which the evaluators do agree, so a
guard there fires on a fixture rather than on the paper.

Run AFTER fix_between.py:  python fix_between_check.py <paper dir>
"""
import io
import os
import sys

os.chdir(sys.argv[1])
N = 0

CHECK = '''def check_between_sign(src, tables_dir):
    """Section 6.3 reports that the two masked evaluators disagree in sign.

    That is a measured claim.  For several revisions the macros behind the
    paragraph came from a single-evaluator file, and one sentence asserted
    an agreement the data contradicts; nothing caught it because the
    reading had no table and the macros had no evaluator dimension.
    """
    mpath = os.path.join(tables_dir, "macros.tex")
    if not os.path.isfile(mpath) or "FbBetweenNOpposite" not in src:
        return
    v = newcommands(open(mpath, encoding="utf-8").read()).get(
        "FbBetweenNOpposite")
    if v is None or "TODO" in v:
        return
    try:
        n = int(v)
    except ValueError:
        return
    if n < 1:
        fail("between",
             "the two masked evaluators agree in sign on every corpus "
             "(FbBetweenNOpposite = " + v + "); Section 6.3 reports that "
             "they do not, and has to be rewritten")


def check_quantities(src, tables_dir):'''

SELFTEST = '''check_orphan_rule()


def check_between_sign_rule():
    """An agreement in sign must be reported, not printed over."""
    import check_paper as C
    with tempfile.TemporaryDirectory() as d:
        src = "on \\\\FbBetweenNOpposite of the corpora they do not agree"
        for v, want in (("2", False), ("0", True)):
            with open(os.path.join(d, "macros.tex"), "w") as fh:
                fh.write("\\\\newcommand{\\\\FbBetweenNOpposite}{" + v + "}\\n")
            C.check_between_sign(src, d)
            got = any("agree in sign on every corpus" in m for _, m in C.FAIL)
            assert got is want, (v, [m for _, m in C.FAIL])
            del C.FAIL[:]
            del C.WARN[:]
    print("  catch: the evaluators agreeing where the prose says they do not")


check_between_sign_rule()
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


rep("check_paper.py",
    "def check_quantities(src, tables_dir):",
    CHECK,
    "1: the sign claim is checked against the generated number",
    marker="def check_between_sign")

rep("check_paper.py",
    "    check_param_strings(args.tables)",
    "    check_param_strings(args.tables)\n"
    "    check_between_sign(src, args.tables)",
    "2: invoked",
    marker="check_between_sign(src, args.tables)")

rep("check_paper_selftest.py",
    "check_orphan_rule()\n",
    SELFTEST,
    "3: its selftest, both directions",
    marker="check_between_sign_rule")

print(f"done: {N} edits")
