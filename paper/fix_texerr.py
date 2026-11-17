r"""51 LaTeX errors, one cause, and the reason nobody noticed for weeks.

THE ERROR.

    l.9 ...1 & $+0.3676$ & $+0.311$ & $1\times10^{-4}^
                                                     {*}$ \\

tex_p_bare() returns math CONTENT, and below 1e-3 that content ends in a
superscript: "1\times10^{-4}".  tab_blkcells then appends the significance
marker as a second superscript on the same atom.  TeX refuses it.  17
starred cells over three pdflatex passes is the 51.

What TeX does after refusing is the part that matters: it does not stop,
and it does not typeset what was asked for.  Seventeen cells of a table
that is going to arXiv have been rendering as whatever TeX recovered to.

The fix is the empty group: "1\times10^{-4}{}^{*}" attaches the star to an
atom of its own.  The other two star sites format integers, which have no
superscript to collide with, and are left alone.

WHY IT SURVIVED.  build_paper.sh has been printing "latex errors: 51" on
every run since the star column was added.  A count with nothing consuming
it is not a check -- it is a number in a wall of output, and this is the
third instrument in two days found in that state (the ceiling-fraction
verdict, the long-sentence budget, and now this).  The count becomes a
FAIL with the messages broken out, and the build exits non-zero so a
`&& make_arxiv.sh` stops.

AND A CHECK BEFORE LATEX.  check_paper reads the generated tables already.
A double superscript is a shape -- "^{...}^" -- so it can be caught where
it is written instead of in a log nobody reads.  That is the one that will
fire next time, since it names the table and the cell.

Run:  python fix_texerr.py <paper dir>
"""
import io
import os
import re
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


# ------------------------------------------------------------ 1 the cause
rep("make_tables.py",
    '''                + (r"^{*}" if p < bon else "") + r"$ \\\\")''',
    '''                # {} and not nothing: tex_p_bare ends in a superscript
                # below 1e-3, and "10^{-4}^{*}" is the double superscript
                # that TeX refused 17 times a pass.  The empty group gives
                # the star an atom of its own and typesets identically.
                + (r"{}^{*}" if p < bon else "") + r"$ \\\\")''',
    "1: the star gets an atom of its own",
    marker='{} and not nothing')

# --------------------------------------------------------- 2 the gauge
rep("build_paper.sh",
    '''    fi
    grep -c "^! " build.log | sed "s/^/  latex errors: /" || true
    latexmk -c >/dev/null 2>&1 || true''',
    '''    fi
    texerr=$(grep -c "^! " build.log || true)
    echo "  latex errors: $texerr"
    [ "$texerr" -eq 0 ] || grep "^! " build.log | sort | uniq -c | sort -rn \\
        | sed "s/^/    /"
    latexmk -c >/dev/null 2>&1 || true''',
    "2a: latexmk branch reports what the errors are",
    marker='texerr=$(grep -c "^! " build.log || true)\n    echo')

rep("build_paper.sh",
    '''    [ -f main.pdf ] || { grep -A3 "^! " build.log | head -40; exit 1; }
    grep -c "^! " build.log | sed "s/^/  latex errors: /" || true
fi''',
    '''    [ -f main.pdf ] || { grep -A3 "^! " build.log | head -40; exit 1; }
    texerr=$(grep -c "^! " build.log || true)
    echo "  latex errors: $texerr"
    [ "$texerr" -eq 0 ] || grep "^! " build.log | sort | uniq -c | sort -rn \\
        | sed "s/^/    /"
fi''',
    "2b: pdflatex branch reports what the errors are",
    marker='''exit 1; }
    texerr=''')

rep("build_paper.sh",
    '''ls -la main.pdf
echo "done."''',
    '''ls -la main.pdf
echo "done."

# A "! " line means TeX REFUSED something and carried on, so the PDF exists
# and does not contain what was asked for.  This was printed as a bare count
# for weeks while 17 table cells typeset wrongly on every pass.  It is a
# failure now, and non-zero here stops a `&& make_arxiv.sh`.
if [ "${texerr:-0}" -gt 0 ]; then
    echo
    echo "FAIL: $texerr LaTeX error(s) -- see \\"=== 3. PDF ===\\" above."
    echo "A refused construct is still in the PDF as whatever TeX recovered"
    echo "to, so this is a typesetting defect and not a warning."
    exit 1
fi''',
    "2c: the count becomes a failure",
    marker="stops a `&& make_arxiv.sh`")

# --------------------------------------------------------- 3 before latex
CHECK = '''def check_double_superscript(tables_dir):
    """A second superscript on an atom that already has one.

    "$1\\\\times10^{-4}^{*}$" -- a significance star appended to a p-value
    that tex_p_bare already wrote in exponent form.  TeX refuses it, says
    so in the log, and carries on, so the PDF is built and seventeen cells
    of it are wrong.

    The log said this 51 times a build and nothing read the log.  Caught
    here it names the file and the line, which is what makes it a
    one-minute fix instead of a grep through three pdflatex passes.
    """
    pat = re.compile(r"\\^\\{[^{}]*\\}\\s*\\^")
    for fn in sorted(os.listdir(tables_dir)):
        if not fn.endswith(".tex"):
            continue
        with open(os.path.join(tables_dir, fn), encoding="utf-8") as fh:
            body = fh.readlines()
        for i, line in enumerate(body, 1):
            m = pat.search(line)
            if m:
                fail("texmath",
                     "%s line %d: a superscript on a superscript, "
                     "...%s... -- TeX refuses this and typesets something "
                     "else; give the second one an empty group, {}^{*}"
                     % (fn, i, line[max(0, m.start() - 24):m.end() + 8]
                        .strip()))


def check_corpus_order(tables_dir):'''

rep("check_paper.py",
    "def check_corpus_order(tables_dir):",
    CHECK,
    "3a: the check",
    marker="def check_double_superscript")

rep("check_paper.py",
    "    check_corpus_order(args.tables)",
    "    check_corpus_order(args.tables)\n"
    "    check_double_superscript(args.tables)",
    "3b: invoked",
    marker="\n    check_double_superscript(args.tables)")

SELFTEST = '''

def check_double_superscript_rule():
    """A star on a p-value already in exponent form."""
    import check_paper as C
    with tempfile.TemporaryDirectory() as d:
        for body, want in (
                (r"a & $+0.311$ & $1\\times10^{-4}^{*}$ \\\\", True),
                (r"a & $+0.311$ & $1\\times10^{-4}{}^{*}$ \\\\", False),
                (r"a & $+0.311$ & $0.004^{*}$ \\\\", False),
                (r"a & $x^{2}$ and $y^{3}$ \\\\", False)):
            with open(os.path.join(d, "tab_x.tex"), "w") as fh:
                fh.write(body + "\\n")
            del C.FAIL[:]
            C.check_double_superscript(d)
            assert bool(C.FAIL) is want, (body, [m for _, m in C.FAIL])
    del C.FAIL[:]
    del C.WARN[:]
    print("  catch: a superscript written on a superscript")


check_double_superscript_rule()


check_flat_rule()'''

rep("check_paper_selftest.py",
    "\n\ncheck_flat_rule()",
    SELFTEST,
    "4: its selftest",
    marker="def check_double_superscript_rule")

print(f"done: {N} edits")
