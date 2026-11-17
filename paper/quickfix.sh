#!/bin/sh
# Apply one or more NEW correction batches and check the prose.  Nothing
# else: no re-run of the 40 batches already in the tree, no PDF, no
# repository, no arXiv bundle.
#
#     sh quickfix.sh b41              one batch
#     sh quickfix.sh b41 b42 grid3    several, in the order given
#
# WHY NOT apply_all.sh.  That script exists to rebuild this tree from the
# pristine one, and it starts python 47 times; a dry-run first doubles it
# to 94.  For a batch that is not yet in the tree, neither is needed: each
# fix_apply_*.py checks every target before it writes anything and aborts
# the whole batch on a miss, so running it directly is already the dry-run.
# This script starts python once per batch plus once for the check.
#
# WHAT THE CHECK COVERS.  check_paper.py reads the .tex files directly for
# the prose rules -- sentence budget, glossary, bare referents, retired
# macros -- so those are current the moment a batch lands.  Its float and
# cross-reference checks read main.aux, which is whatever the last build
# left behind: if the batch touched a \label, a \ref or a float, that part
# of the report is stale and only finish.sh settles it.
#
# WHEN THE EDITING IS DONE: sh finish.sh
set -e
cd "$(dirname "$0")"

if [ $# -eq 0 ]; then
    echo "usage: sh quickfix.sh <batch> [<batch> ...]   e.g. sh quickfix.sh b41"
    exit 2
fi

for b in "$@"; do
    f="fix_apply_$b.py"
    [ -f "$f" ] || { echo "no such batch: $f"; exit 1; }
    python3 -I "$f"
    echo
done

echo "--- md5 ---"
md5sum main.tex sec_intro.tex sec_decomp.tex sec_truesigma.tex make_tables.py
echo
echo "--- check_paper.py (prose current; floats/refs from the last build) ---"
python3 -I check_paper.py
