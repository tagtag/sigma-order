#!/bin/sh
# Apply the Japanese-review corrections #69-#226, the two cold reads
# (#227-#252) and the reader's four objections (#253-#268) to the English
# source.
#
# The corrections were collected while the paper was rendered sentence by
# sentence into Japanese.  They are applied here in 44 batches plus seven
# generator patches, in this order, because each batch is written against the
# text the batches before it produced.
#
#     sh apply_all.sh            apply everything, in place
#     sh apply_all.sh --dry-run  apply everything to a throwaway copy and
#                                report, leaving this tree untouched
#
# --dry-run copies the five files the patches touch into a temporary
# directory and runs there.  It cannot be done by having each batch skip its
# writes: batch 14 edits a sentence batch 5 produces, so a run that writes
# nothing stops at the first such dependency.
#
# Each batch is idempotent: running it again reports every edit as already
# in place.  An edit whose passage a later batch rewrote is reported as
# "superseded by batch NN" rather than as a failure.  A batch that cannot
# find a target it owns stops and writes nothing, so one batch cannot leave
# a file half-edited.
#
# AFTERWARDS, on the machine that has the measurements:
#
#     python3 -I make_tables.py        # regenerates tables/ and macros.tex
#     latexmk -pdf main.tex
#     python3 -I check_paper.py
#
# make_tables.py MUST be re-run: fix_apply_tables.py adds two columns to
# tab_fbrank (#151), defines \NPerGroup (#82) and \TrendCeilNDropRho (#129),
# and takes six names off the retirement list, and the prose now uses all of
# them.  fix_apply_grid.py then changes \GridStep and \GridK to the 1/2n!
# grid (#253) and the lower block of Table 5 to a one-sample binomial test
# (#256), both of which move printed numbers.  Without the measurement data
# make_tables.py rewrites every table as a stub, so do not run it anywhere
# else.
#
# ALSO on that machine, before the build:
#
#     cd ../order-intervention
#     python3 -I check_grid_resolution.py | tee check_grid_resolution.log
#
# That is what establishes #253 from the measurements rather than from the
# argument.  Add order-intervention/check_grid_resolution.py and .log to
# README.md's Layout, or check_readme.py in make_repo.sh will stop.
#
set -e
cd "$(dirname "$0")"

SOURCES="main.tex sec_intro.tex sec_decomp.tex sec_truesigma.tex make_tables.py make_tables_selftest.py check_paper.py check_paper_selftest.py make_repo.sh make_arxiv.sh"

run_batches() {
    i=1
    while [ $i -le 44 ]; do
        python3 -I "fix_apply_b$i.py"
        echo
        i=$((i + 1))
    done
    python3 -I fix_apply_tables.py
    echo
    python3 -I fix_apply_grid.py
    echo
    python3 -I fix_apply_grid2.py
    echo
    python3 -I fix_apply_fbgrid.py
    echo
    python3 -I fix_apply_selftest.py
    echo
    python3 -I fix_apply_selftest2.py
    echo
    python3 -I fix_apply_selftest3.py
    echo
    python3 -I fix_apply_repo.py
    echo
    python3 -I fix_apply_arxiv.py
    echo
    python3 -I fix_apply_anc2.py
}

if [ "$1" = "--dry-run" ]; then
    SANDBOX=$(mktemp -d)
    trap 'rm -rf "$SANDBOX"' EXIT INT TERM
    cp $SOURCES fix_apply_b*.py fix_apply_tables.py fix_apply_grid.py fix_apply_grid2.py fix_apply_fbgrid.py fix_apply_selftest.py fix_apply_selftest2.py fix_apply_selftest3.py fix_apply_repo.py fix_apply_arxiv.py fix_apply_anc2.py "$SANDBOX/"
    echo "DRY RUN in $SANDBOX; this tree is not touched."
    echo
    ( cd "$SANDBOX" && run_batches )
    echo
    echo "DRY RUN finished.  Nothing in this directory was changed."
    echo "Run 'sh apply_all.sh' to apply it here."
    exit 0
fi

run_batches

echo
echo "All 44 batches, the three generator patches, the self-test fixture, the
repository patch and the two arXiv patches are in."
echo "Next: python3 -I make_tables.py, then latexmk -pdf main.tex,"
echo "      then python3 -I check_paper.py."
