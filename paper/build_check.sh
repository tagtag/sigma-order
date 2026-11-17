#!/bin/sh
# Build and check the paper without the measurement data present.
#
# make_tables.py cannot run here: blkord_*.json and the sigma_fb shards live
# on the measurement machine, and running it without them rewrites every
# table as a stub.  So tables/ is taken as it stands, and the two things the
# generator changes of fix_apply_tables.py would alter in it are simulated:
#
#   * the macros it newly defines (#82 NPerGroup, #129 TrendCeilNDropRho and
#     friends) get placeholder values, purely so latex has something to set;
#   * the names it takes off the retirement list (#166, #173) are taken off
#     the "% retired:" lines that check_paper.py reads.
#
# Both are undone before this script exits, so nothing generated is left
# modified.  The real values come from make_tables.py on the measurement
# machine.
#
#     sh build_check.sh
#
set -e
cd "$(dirname "$0")"

M=tables/macros.tex
BK=$(mktemp)
cp "$M" "$BK"
trap 'cp "$BK" "$M"; rm -f "$BK"' EXIT INT TERM

for name in NPerGroup TrendCeilNDropRho TrendCeilNDropP TrendCeilNDropNEval; do
    if ! grep -q "newcommand{\\\\$name}" "$M"; then
        case $name in
            NPerGroup)            v=100   ;;
            TrendCeilNDropRho)    v=+0.00 ;;
            TrendCeilNDropP)      v=1.000 ;;
            TrendCeilNDropNEval)  v=4     ;;
        esac
        printf '%s\n' "\\newcommand{\\$name}{$v}  % PLACEHOLDER, build_check.sh" >> "$M"
        echo "  placeholder \\$name = $v"
    fi
done

python3 - "$M" <<'PY'
import re
import sys

path = sys.argv[1]
src = open(path, encoding="utf-8").read()
names = ["FbRMax", "FbCausalBertBase", "FbCausalLLaDA",
         "FbCausalStepsBertBase", "FbCausalStepsLLaDA",
         "CtrlDMin", "CtrlDMax"]
hit = []
for name in names:
    pat = re.compile(r"(^% retired:.*?)\s\b" + name + r"\b", re.M)
    if pat.search(src):
        src = pat.sub(r"\1", src, count=1)
        hit.append(name)
if hit:
    open(path, "w", encoding="utf-8").write(src)
    print("  un-retired for this build: " + ", ".join(hit))
PY

echo "--- latexmk ---"
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex > /tmp/build_check.log 2>&1 \
    || { echo "LATEX FAILED; tail of log:"; tail -30 /tmp/build_check.log; exit 1; }
echo "  main.pdf built"

echo "--- check_paper.py ---"
python3 -I check_paper.py
