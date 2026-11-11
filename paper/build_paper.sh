#!/bin/sh
#=====================================================================
# One command: measurements -> tables -> figures -> PDF.
#
# Safe to run while jobs are still going: tables and figures are built from
# whatever JSONs exist, a panel with no input is skipped with a notice, and a
# number that is not measured yet appears in the PDF as a visible [TODO:Name]
# rather than breaking the build.  So this can be run repeatedly as results
# land.
#
#   sh build_paper.sh                       # defaults below
#   PLL=/path/results_pll sh build_paper.sh
#   PY=/path/to/python3 sh build_paper.sh   # a python that has numpy/scipy
#   MODULE=none sh build_paper.sh           # never try `module load`
#=====================================================================

set -e

: "${PLL:=../order-intervention/results_pll}"
: "${BLKORD:=../order-intervention/results_blkord}"
: "${TOY:=../bert-affinity}"
: "${PY:=python3}"
# the site module the measurements were made under; it carries numpy, scipy
# and matplotlib
: "${MODULE:=pytorch/2.4.1}"

cd "$(dirname "$0")"

echo "=== 0. python ==="
# A bare login shell on the cluster has no numpy or scipy, and `module load`
# does not survive a logout, so running this script after logging in failed
# with a bare ModuleNotFoundError and no hint of the cause.  Load the module
# here instead of expecting it to have been loaded by hand -- but only when
# the current python actually cannot import what the scripts need, so this
# stays a no-op on a machine with its own environment.
if $PY -c 'import numpy, scipy, matplotlib' >/dev/null 2>&1; then
    echo "  $($PY -c 'import sys; print(sys.executable)') has numpy, scipy, matplotlib"
elif [ "$MODULE" = none ]; then
    echo "  ERROR: $PY cannot import numpy/scipy/matplotlib and MODULE=none."
    echo "  Set PY to a python that has them."; exit 1
else
    if [ -f /etc/profile.d/modules.sh ]; then
        . /etc/profile.d/modules.sh
    fi
    module load "$MODULE" >/dev/null 2>&1 || true
    if $PY -c 'import numpy, scipy, matplotlib' >/dev/null 2>&1; then
        echo "  loaded $MODULE for numpy, scipy and matplotlib"
    else
        echo "  ERROR: $PY cannot import numpy, scipy and matplotlib, and"
        echo "  loading '$MODULE' did not supply them.  Either"
        echo "    PY=/path/to/python3 sh build_paper.sh"
        echo "  with a python that has them, or load the right module first."
        echo "  What is missing:"
        $PY -c 'import importlib
for m in ("numpy","scipy","matplotlib"):
    try: importlib.import_module(m); print("    have",m)
    except Exception as e: print("    MISSING",m,"--",e)' 2>&1 | sed 's/^/  /'
        exit 1
    fi
fi

echo
echo "=== 1. tables and prose numbers ==="
# The generator is checked against synthetic measurements with a known answer
# before it is run on the real ones.  It needs no data and takes a second; a
# table that silently stops being written is the failure it catches.
$PY -I make_tables_selftest.py || exit 1
# the sentence splitter the whole within-text test rests on
$PY -I ../order-intervention/block_split_selftest.py >/dev/null || exit 1
$PY -I make_tables.py --pll "$PLL" --blkord "$BLKORD" --toy "$TOY" \
    --outdir tables

echo
echo "=== 2. figures ==="
$PY -I make_figures.py --pll "$PLL" --blkord "$BLKORD" --toy "$TOY" \
    --outdir figures

echo
echo "=== 3. PDF ==="
if command -v latexmk >/dev/null 2>&1; then
    latexmk -pdf -interaction=nonstopmode main.tex >build.log 2>&1 || true
    if [ ! -f main.pdf ]; then
        echo "LaTeX produced no PDF; the errors were:"
        grep -A3 "^! " build.log | head -40; exit 1
    fi
    grep -c "^! " build.log | sed "s/^/  latex errors: /" || true
    latexmk -c >/dev/null 2>&1 || true
else
    # Three passes -- the same number make_arxiv.sh uses, and the same number
    # arXiv's own pdflatex run needs: one to write the .aux, one to resolve
    # the references, one for the page numbers to settle after any shift.
    # Two did not guarantee convergence, and a local PDF that differs from the
    # submitted one is worse than no local PDF at all.
    : >build.log
    for pass in 1 2 3; do
        printf '\n===== pdflatex pass %s =====\n' "$pass" >>build.log
        pdflatex -interaction=nonstopmode main.tex >>build.log 2>&1 || true
    done
    [ -f main.pdf ] || { grep -A3 "^! " build.log | head -40; exit 1; }
    grep -c "^! " build.log | sed "s/^/  latex errors: /" || true
fi

echo
echo "=== 4. what is still missing ==="
# A TODO in the PDF is a number that has not been measured yet; a \todo in the
# source is prose still to be written.  Both are listed so nothing silently
# ships as a placeholder.
grep -o "TODO:[A-Za-z]*" tables/macros.tex | sort -u | sed 's/^/  number  /' || true
# A \todo in the source is prose still to be written.  The one in \repoline
# is the fallback for an unset \repourl: while the URL is set it is never
# typeset, and counting it reported a missing piece in a document that had
# none.  \todo{ appears once per use; the \newcommand that defines it spells
# the name \todo} and is not counted.
ntodo=$(grep -c 'todo{' main.tex)
if grep -q '^.renewcommand{.repourl}{[^}]' main.tex; then
    echo "  prose placeholders: $((ntodo - 1))"
    echo "  (repourl is set, so the todo fallback in repoline is not typeset)"
else
    echo "  prose placeholders: $ntodo"
    echo "  (repourl is EMPTY -- the Reproducibility line will print a TODO)"
fi
echo
echo "=== 5. relations ==="
# Everything above checks that the document was built.  This checks what a
# built document cannot show: a reference nothing cites, a float nothing
# points at, a quantity the prose names and no table reports.  Each of those
# shipped at least once, and each produced a PDF that looked correct.  The
# failure is reported rather than fatal, so a working draft still gets its
# PDF; make_arxiv.sh treats the same failure as a refusal to package.
$PY -I check_paper.py --tex main.tex --tables tables || \
    echo "  (the PDF was still built; make_arxiv.sh will refuse to package it)"

echo
ls -la main.pdf
echo "done."
