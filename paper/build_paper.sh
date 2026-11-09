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
#=====================================================================

set -e

: "${PLL:=../order-intervention/results_pll}"
: "${BLKORD:=../order-intervention/results_blkord}"
: "${TOY:=../bert-affinity}"
: "${PY:=python3}"

cd "$(dirname "$0")"

echo "=== 1. tables and prose numbers ==="
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
    pdflatex -interaction=nonstopmode main.tex >build.log 2>&1 || true
    pdflatex -interaction=nonstopmode main.tex >>build.log 2>&1 || true
    [ -f main.pdf ] || { grep -A3 "^! " build.log | head -40; exit 1; }
fi

echo
echo "=== 4. what is still missing ==="
# A TODO in the PDF is a number that has not been measured yet; a \todo in the
# source is prose still to be written.  Both are listed so nothing silently
# ships as a placeholder.
grep -o "TODO:[A-Za-z]*" tables/macros.tex | sort -u | sed 's/^/  number  /' || true
grep -c "todo{" main.tex | sed 's/^/  prose placeholders: /'

echo
ls -la main.pdf
echo "done."
