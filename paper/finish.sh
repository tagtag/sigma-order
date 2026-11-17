#!/bin/sh
# Everything that has to pass before the bundle goes out.  Run it ONCE,
# after the last correction -- not after each one.
#
#     sh finish.sh
#
# build_paper.sh rebuilds main.aux, so check_paper.py's float and
# cross-reference checks are settled here rather than read off a stale
# build as in quickfix.sh.  make_repo.sh runs the self-tests from a fresh
# copy and checks the README against the tree; make_arxiv.sh packs the
# bundle and builds arxiv_main.pdf from it alone.
set -e
cd "$(dirname "$0")"

echo "=== build ==="
sh build_paper.sh

echo
echo "=== check_paper.py ==="
python3 -I check_paper.py

echo
echo "=== make_repo.sh ==="
sh make_repo.sh

echo
echo "=== make_arxiv.sh ==="
sh make_arxiv.sh

echo
echo "=== the bundle ==="
pdftotext arxiv_main.pdf - | grep -c TODO | sed 's/^/  TODO in arxiv_main.pdf: /'
pdfinfo arxiv_main.pdf | grep Pages | sed 's/^/  /'
tar tzf arxiv_submission.tar.gz | grep -c 'anc/' | sed 's/^/  ancillary files: /'
