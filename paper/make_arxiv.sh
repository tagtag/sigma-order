#!/bin/sh
#=====================================================================
# Assemble the arXiv submission bundle and verify it compiles ALONE.
#
# arXiv compiles the source on its own machines, so the usual failure is a
# file the local build found but the bundle does not contain -- an \input of
# a generated table, a figure outside graphicspath, a .sty that happens to sit
# in the working directory.  This script therefore copies only what goes up,
# into an empty directory, and builds there.  If that build succeeds the
# upload will too.
#
# What goes in:
#   main.tex            the source
#   tables/*.tex        generated tables and the prose macros (\input by name)
#   figures/*.pdf       figures only as PDF; the .png copies are for screen
#   anc/                ancillary files: the measurement and figure scripts,
#                       which arXiv keeps downloadable beside the paper.
#                       The Reproducibility section claims every number comes
#                       from them, so they belong with it.
#
# What stays out: main.pdf (arXiv builds its own), build.log, *.aux, the .png
# figures, __pycache__, and the measurement JSONs (too large; they are in the
# repository the paper points to).
#
#   sh make_arxiv.sh                      rebuild, check, bundle
#   SKIP_REBUILD=1 sh make_arxiv.sh       bundle what is already on disk
#   sh make_arxiv.sh --strip              also delete the \todo note
#   FORCE_PDFLATEX=1 sh make_arxiv.sh     use pdflatex even if latexmk exists
#=====================================================================

set -e
cd "$(dirname "$0")"

# The same PY as build_paper.sh, and for the same reason: on this project's
# machine the bare python3 has no numpy, so every call below that ran as
# python3 failed after a full rebuild had already been done.
: "${PY:=python3}"

OUT=arxiv_submission
TGZ=arxiv_submission.tar.gz
STRIP=0
[ "${1:-}" = "--strip" ] && STRIP=1

echo "=== 0. regenerate the tables and figures from the measurements ==="
# Never trust whatever happens to be in tables/ and figures/.  Those are build
# products, and a stale copy -- from a test run, or from a tarball that shipped
# with them -- would put the wrong numbers into a submission that looks
# finished.  Regenerate, then refuse if the inputs were not there.
if [ "${SKIP_REBUILD:-0}" = "1" ]; then
    echo "  SKIPPED by request (SKIP_REBUILD=1) -- tables/ and figures/ are"
    echo "  used as they stand.  Check them yourself before uploading."
else
    # Keep the output.  Discarding it and saying "run it directly to see why"
    # made a missing scipy look like a mystery; the cause was one line down.
    if sh build_paper.sh >build_paper.log 2>&1; then
        echo "  rebuilt from \$PLL/\$BLKORD/\$TOY"
    else
        echo "  build_paper.sh FAILED.  Its last 25 lines:"
        tail -25 build_paper.log | sed 's/^/    /'
        echo "  (full output in paper/build_paper.log)"
        exit 1
    fi
fi

echo
echo "=== 0a2. do the parts of the document point at each other? ==="
# The checks below this one all ask whether the document was built from real
# measurements.  This one asks something the built document cannot answer: a
# reference list prints whether or not anything cites it, a figure appears
# whether or not a sentence points at it, and a sentence can promise that a
# quantity is reported with no table reporting it.  All three shipped in this
# project, in PDFs that looked correct.  Refuse to package on any of them.
$PY -I check_paper_selftest.py >/dev/null || {
    echo "  ERROR: check_paper.py no longer catches what it claims to;"
    echo "  run  $PY -I check_paper_selftest.py  to see which case."
    exit 1
}
$PY -I check_paper.py --tex main.tex --tables tables || exit 1

echo
echo "=== 0a3. is the draft dressing off? ==="
# \draftlinestrue prints line numbers in the margin so that a reader can
# say "line 412" instead of hunting for a sentence.  They are for the
# read-through and not for the archive, and nothing else would notice:
# the document compiles, every number is right, and the margin is full of
# numbers.  Refuse here, where the refusal costs one line to clear.
if grep -q '^[^%]*\\draftlinestrue' main.tex; then
    echo "  ERROR: main.tex still has \\draftlinestrue, so the submission"
    echo "  would carry draft line numbers in the margin."
    echo "  Set  \\draftlinesfalse  in the preamble and rebuild."
    exit 1
fi
echo "  draft line numbers are off"

echo
echo "=== 0b. do the numbers come from real measurements? ==="
# A table built from no input still produces a file, with every quoted number
# replaced by a visible TODO.  Count those, and count the measurement files
# the tables were built from, so an empty or partial run cannot pass silently.
$PY - <<'PY2' || exit 1
import glob, os, sys, re
pll = os.environ.get("PLL", "../order-intervention/results_pll")
blk = os.environ.get("BLKORD", "../order-intervention/results_blkord")
n_pll = len(glob.glob(os.path.join(pll, "pll_*.json")))
n_blk = len(glob.glob(os.path.join(blk, "blkord_*.json")))
print(f"  measurement files: {n_pll} in {pll}, {n_blk} in {blk}")
if n_pll == 0 and n_blk == 0:
    print("  ERROR: no measurement files at all -- nothing to submit")
    sys.exit(1)
# Texts too short to permute are dropped by block_order_pll.py.  That used to
# be invisible: the per-corpus n simply came out lower and the paper still
# said 200.  Refuse to package while any text is missing for that reason.
dropped = 0
for f in glob.glob(os.path.join(blk, "blkord_*.json")):
    try:
        import json as _json
        d = _json.load(open(f))
    except Exception:
        continue
    dropped += int(d.get("n_skipped", 0) or 0)
if dropped:
    print(f"  ERROR: {dropped} text(s) were dropped as too short to permute.")
    print("  Every per-corpus n in the paper is then smaller than the corpus,")
    print("  and nothing in the text says so.  Look at the 'skipped' list in")
    print("  the blkord JSONs before submitting.")
    sys.exit(1)
try:
    macros = open("tables/macros.tex").read()
except OSError:
    print("  ERROR: tables/macros.tex was not generated")
    sys.exit(1)
todos = sorted(set(re.findall(r"TODO:([A-Za-z]+)", macros)))
if todos:
    print(f"  ERROR: {len(todos)} quoted number(s) have no measurement behind")
    print(f"  them: {', '.join(todos)}")
    print("  These print as [TODO:Name] in the PDF.  Fix the measurements or")
    print("  remove the sentences that cite them before submitting.")
    sys.exit(1)
# A whole table can also be missing its input.  make_tables.py deletes every
# table it owns before regenerating, then leaves a stub carrying a TODO marker
# for any it could not build, so a stale table from an earlier run or from a
# release tarball can no longer pass as current.  Refuse on the stub.
stubs = sorted(os.path.basename(p) for p in glob.glob("tables/tab_*.tex")
               if "[TODO:" in open(p).read())
if stubs:
    print(f"  ERROR: {len(stubs)} table(s) have no measurements behind them:")
    print(f"  {', '.join(stubs)}")
    sys.exit(1)
# A figure can be a stub too.  make_figures.py deletes every figure it owns
# before drawing and leaves a placeholder for any it could not draw, so a
# stale figure from an earlier run cannot ship; this refuses on the stub.
import subprocess
figstubs = []
if subprocess.run(["which", "pdftotext"], capture_output=True).returncode == 0:
    for f in sorted(glob.glob("figures/fig*.pdf")):
        t = subprocess.run(["pdftotext", f, "-"], capture_output=True, text=True)
        if "[TODO:" in (t.stdout or ""):
            figstubs.append(os.path.basename(f))
if figstubs:
    print(f"  ERROR: {len(figstubs)} figure(s) have no measurements behind them:")
    print(f"  {', '.join(figstubs)}")
    sys.exit(1)
print("  every quoted number, table and figure is backed by a measurement")
PY2

echo
echo "=== 1. collect ==="
rm -rf "$OUT" "$TGZ"
mkdir -p "$OUT/tables" "$OUT/figures" "$OUT/anc"

cp main.tex "$OUT/"
cp tables/*.tex "$OUT/tables/"
cp figures/*.pdf "$OUT/figures/"

# Every file main.tex \input{}s that is not a generated table.  This step
# used to copy main.tex and nothing else.  When the paper grew three sections
# into files of their own the bundle lost them silently: the local build was
# fine, because the files were sitting in the working directory, and only the
# arXiv machine would have seen a document with three sections missing.  Step
# 2 below caught it -- that is what step 2 is for -- but a collect step that
# needs catching will eventually be run with step 2 skipped.  Derived from the
# source now, so a section added later is copied without anyone remembering.
grep -o '\\input{[^}]*}' main.tex | sed 's/.*{//; s/}//' | sort -u |
while read -r f; do
    case "$f" in
        tables/*|figures/*) continue ;;
    esac
    [ -f "$f.tex" ] && cp "$f.tex" "$OUT/"
done

# ancillary: the scripts that generate every number and figure
cp make_tables.py make_tables_selftest.py make_figures.py figstyle.py \
   check_paper.py check_paper_selftest.py glossary.txt \
   build_paper.sh "$OUT/anc/" 2>/dev/null || true
for f in ../order-intervention/block_order_pll.py \
         ../order-intervention/block_order_selftest.py \
         ../order-intervention/block_split_selftest.py \
         ../order-intervention/pll_sigma.py \
         ../order-intervention/pll_selftest.py \
         ../order-intervention/aoar_core.py \
         ../order-intervention/order_intervention.py \
         ../order-intervention/merge_blkord.py \
         ../order-intervention/merge_pll.py \
         ../order-intervention/block_sigma_fb.py \
         ../order-intervention/block_sigma_fb_selftest.py \
         ../order-intervention/block_vs_fb_selftest.py \
         ../order-intervention/merge_sigfb.py \
         ../order-intervention/forward_backward_sigma.py \
         ../order-intervention/forward_backward_decomposition.py \
         ../order-intervention/check_two_constructions.py \
         ../order-intervention/check_grid_resolution.py \
         ../bert-affinity/mlm_entropy_production.py \
         ../bert-affinity/cycle_affinity.py \
         ../bert-affinity/capacity_sweep.py \
         ../bert-affinity/bayes_route_control.py \
         ../bert-affinity/reproduce_sagawa_stats.py \
         ../bert-affinity/compare_repro.py \
         ../bert-affinity/check_rank_pvalues.py \
         ceiling_resolution.py \
         ../order-intervention/README.md; do
    [ -f "$f" ] && cp "$f" "$OUT/anc/"
done
echo "  main.tex, $(ls "$OUT/tables" | wc -l) table file(s), "\
"$(ls "$OUT/figures" | wc -l) figure(s), $(ls "$OUT/anc" | wc -l) ancillary file(s)"

if [ "$STRIP" = "1" ]; then
    $PY - "$OUT/main.tex" <<'PY'
import re, sys
p = sys.argv[1]
s = open(p).read()
# remove \todo{...} with balanced braces, however long
out, i, removed = [], 0, 0
while True:
    j = s.find("\\todo{", i)
    if j < 0:
        out.append(s[i:]); break
    out.append(s[i:j])
    k, depth = j + 6, 1
    while k < len(s) and depth:
        if s[k] == "{": depth += 1
        elif s[k] == "}": depth -= 1
        k += 1
    i = k; removed += 1
open(p, "w").write("".join(out))
print(f"  stripped {removed} todo note(s) from the copy")
PY
fi

echo
echo "=== 2. what the source asks for, and whether it is here ==="
$PY - "$OUT" <<'PY'
import os, re, sys
root = sys.argv[1]
src = open(os.path.join(root, "main.tex")).read()
missing = []
for m in re.finditer(r"\\input\{([^}]+)\}", src):
    name = m.group(1)
    cands = [name, name + ".tex"]
    if not any(os.path.exists(os.path.join(root, c)) for c in cands):
        missing.append(("input", name))
for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", src):
    name = m.group(1)
    cands = [os.path.join("figures", name), name,
             os.path.join("figures", name + ".pdf"), name + ".pdf"]
    if not any(os.path.exists(os.path.join(root, c)) for c in cands):
        missing.append(("graphic", name))
for kind, name in missing:
    print(f"  MISSING {kind}: {name}")
print("  all referenced files present" if not missing
      else f"  {len(missing)} missing -- the arXiv build would fail")
sys.exit(1 if missing else 0)
PY

# Every script the paper names must be in anc/.  The Reproducibility
# section says every number in the paper comes from these, so a name in the
# text with no file beside it is a claim the bundle does not keep.  The list
# above is hand-written and had drifted: the text named six scripts and the
# bundle shipped four.
$PY - "$OUT" <<'ANCPY' || exit 1
import glob, os, re, sys
out = sys.argv[1]
named = set()
for f in glob.glob(os.path.join(out, "*.tex")):
    s = open(f, encoding="utf-8").read()
    s = "\n".join(l.split("%")[0] for l in s.split("\n"))
    for m in re.findall(r"\\(?:fn|texttt|path)\{([^}]*\.py)\}", s):
        named.add(m.replace("\\_", "_"))
have = set(os.listdir(os.path.join(out, "anc")))
missing = sorted(n for n in named if n not in have)
if missing:
    print("  MISSING from anc/, but named in the text: " + ", ".join(missing))
    print("  add them to the ancillary list in make_arxiv.sh")
    raise SystemExit(1)
print(f"  all {len(named)} script(s) the text names are in anc/")
ANCPY

echo
echo "=== 3. build in isolation (this is what arXiv will do) ==="
# latexmk is not everywhere (the Kyoto ICR login nodes have pdflatex only),
# so fall back to running pdflatex the required number of times by hand.
# Three passes: one to write the .aux, one to resolve references, one for the
# reference list to settle.
if command -v latexmk >/dev/null 2>&1 && [ "${FORCE_PDFLATEX:-0}" != "1" ]; then
    ( cd "$OUT" && latexmk -pdf -interaction=nonstopmode main.tex \
        >arxiv_build.log 2>&1 || true )
else
    echo "  latexmk not found; using pdflatex directly (3 passes)"
    ( cd "$OUT" && : >arxiv_build.log
      for pass in 1 2 3; do
          printf '\n===== pdflatex pass %s =====\n' "$pass" >>arxiv_build.log
          pdflatex -interaction=nonstopmode main.tex >>arxiv_build.log 2>&1 || true
      done )
fi
if [ ! -f "$OUT/main.pdf" ]; then
    echo "  FAILED. No PDF was produced."
    if grep -q "^! " "$OUT/arxiv_build.log" 2>/dev/null; then
        echo "  --- LaTeX errors ---"
        grep -A3 "^! " "$OUT/arxiv_build.log" | tail -40
    else
        # no "! " line means latexmk itself refused, or a file could not be
        # found before TeX started; the tail is the only place that says so
        echo "  No LaTeX error line in the log, so the failure is before or"
        echo "  around TeX itself.  Last 30 lines of"
        echo "  $OUT/arxiv_build.log:"
        tail -30 "$OUT/arxiv_build.log" | sed 's/^/    /'
        echo "  --- what is in the directory ---"
        ( cd "$OUT" && ls -la | sed 's/^/    /' )
        command -v latexmk >/dev/null 2>&1 \
            || echo "    NOTE: latexmk is not on PATH here"
        command -v pdflatex >/dev/null 2>&1 \
            || echo "    NOTE: pdflatex is not on PATH here"
    fi
    exit 1
fi
echo "  built: $(cd "$OUT" && pdfinfo main.pdf | awk '/Pages/{print $2}') pages,"\
" $(grep -c '^! ' "$OUT/arxiv_build.log" || true) error(s)"

# Boxes that run past the text block.  This build is the one with the real
# numbers in it, so it is the only place a table's true width can be measured;
# a table that overflows here overflows in the submitted PDF.  Small ones are
# normal in justified text, so only the ones worth looking at are listed.
$PY - "$OUT/arxiv_build.log" <<'PY'
import re, sys
log = open(sys.argv[1], errors="replace").read()
w = sorted({float(x) for x in
            re.findall(r"Overfull \\hbox \(([0-9.]+)pt too wide\)", log)},
           reverse=True)
big = [x for x in w if x >= 5.0]
if not big:
    print("  no box runs more than 5pt past the text block")
else:
    print(f"  {len(big)} box(es) run past the text block by 5pt or more:"
          f" {', '.join(f'{x:.0f}pt' for x in big[:6])}"
          + (" ..." if len(big) > 6 else ""))
    print("  A wide table is the usual cause; \\small on it, or a shorter")
    print("  column, fixes it.  For the line numbers:")
    print("      grep -n -B2 Overfull paper/arxiv_build.log")
PY

echo
echo "=== 3b. is the repository URL set? ==="
if grep -qE '^\\newcommand\{\\repourl\}\{\}' "$OUT/main.tex" \
   && ! grep -qE 'renewcommand\{\\repourl\}\{[^}]+\}' "$OUT/main.tex"; then
    echo "  NOT SET.  \\repourl is empty, so the Reproducibility section"
    echo "  carries a red note instead of a link.  Publish the repository,"
    echo "  then in main.tex set"
    echo "    \\renewcommand{\\repourl}{https://github.com/USER/REPO}"
else
    grep -oE 'renewcommand\{\\repourl\}\{[^}]*\}' "$OUT/main.tex" \
        | sed 's/^/  set to: /' | tail -1
fi

echo
echo "=== 4. remaining notes in the source ==="
# The \todo in \repoline is the fallback for an unset \repourl: with the URL
# set it is never expanded, so it does not print in red or anywhere else.
# Counting it reported a note to resolve in a document that had none, and
# step 3b above has already established which case this is.
n=$(grep -c "todo{" "$OUT/main.tex" || true)
if grep -q '^.renewcommand{.repourl}{[^}]' "$OUT/main.tex"; then
    n=$((n - 1))
fi
if [ "$n" -gt 0 ]; then
    printf '  %s todo note(s) still in the source -- these print in red in the PDF.\n' "$n"
    echo "  Run with --strip once they are resolved, or edit main.tex."
else
    echo "  none that reach the page"
fi

echo
echo "=== 5. pack ==="
# Keep the PDF step 3 built, before it is deleted from the bundle.  That build
# is the only faithful preview of the submission -- same isolated tree, same
# files present, same number of pdflatex passes as arXiv runs -- so discarding
# it left nothing to check the upload against.  It is saved beside the paper
# under a name that cannot be mistaken for the local build.
cp "$OUT/main.pdf" arxiv_main.pdf
# Keep the build log too, for the same reason.  Step 3 ends by telling the
# reader to grep it for the line numbers of any overfull box; this step then
# deleted it, so the instruction pointed at a file that no longer existed by
# the time anyone could follow it.  It is moved beside the paper, not removed.
[ -f "$OUT/arxiv_build.log" ] && mv "$OUT/arxiv_build.log" arxiv_build.log
# arXiv wants the files at the archive root, not inside a directory
( cd "$OUT" && rm -f main.pdf main.aux main.log main.out main.fls \
        main.fdb_latexmk arxiv_build.log && tar czf "../$TGZ" . )
ls -la "$TGZ"
tar tzf "$TGZ" | sed 's/^/  /'
echo
echo "Upload $TGZ to arXiv. It unpacks to main.tex, tables/, figures/, anc/;"
echo "arXiv compiles main.tex with pdflatex and keeps anc/ as ancillary files."
echo
echo "Check paper/arxiv_main.pdf, not paper/main.pdf: it is the PDF built from"
echo "the bundle alone, which is what arXiv will produce."
