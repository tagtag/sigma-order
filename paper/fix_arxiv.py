r"""Two things that stand between a green build and an upload.

$PY.  build_paper.sh takes PY so that a machine whose `python3` has no
numpy can still build -- which is this project's own machine.
make_arxiv.sh calls bare `python3` eight times, so the packaging script
fails on exactly the setup the build script was written for, and fails
late, after a full rebuild.

DRAFT LINE NUMBERS.  \draftlinestrue puts line numbers in the margin for
the read-through.  Nothing stops them going up with the submission.  A
preprint with line numbers is not fatal, but it is not what was meant, and
the toggle was added on the understanding that packaging would refuse
while it is on.  That half was never written; this is it.

The refusal is a refusal and not a warning, and it says the one line that
clears it.

Run:  python fix_arxiv.py <paper dir>
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


# ------------------------------------------------------------- 1 $PY
src = io.open("make_arxiv.sh", encoding="utf-8").read()
if ': "${PY:=python3}"' not in src:
    anchor = '''OUT=arxiv_submission'''
    assert src.count(anchor) == 1
    src = src.replace(anchor, '''# The same PY as build_paper.sh, and for the same reason: on this project's
# machine the bare python3 has no numpy, so every call below that ran as
# python3 failed after a full rebuild had already been done.
: "${PY:=python3}"

''' + anchor)
    # Every bare python3 that RUNS something, including heredocs.  The two
    # inside the error messages are instructions to a person and stay as
    # they are only if they would still work; they are rewritten too, so a
    # reader copying the line gets the interpreter the script used.
    n_before = len(re.findall(r"(?m)^(\s*)python3\b", src))
    src = re.sub(r"(?m)^(\s*)python3\b", r"\1$PY", src)
    src = src.replace("run  python3 -I check_paper_selftest.py",
                      "run  $PY -I check_paper_selftest.py")
    io.open("make_arxiv.sh", "w", encoding="utf-8").write(src)
    print(f"  1: PY is honoured ({n_before} bare python3 calls rewritten)")
    N += 1
else:
    print("  (already) 1: PY is honoured")

# --------------------------------------------------- 2 the draftlines gate
rep("make_arxiv.sh",
    '''echo
echo "=== 0b. do the numbers come from real measurements? ==="''',
    '''echo
echo "=== 0a3. is the draft dressing off? ==="
# \\draftlinestrue prints line numbers in the margin so that a reader can
# say "line 412" instead of hunting for a sentence.  They are for the
# read-through and not for the archive, and nothing else would notice:
# the document compiles, every number is right, and the margin is full of
# numbers.  Refuse here, where the refusal costs one line to clear.
if grep -q '^[^%]*\\\\draftlinestrue' main.tex; then
    echo "  ERROR: main.tex still has \\\\draftlinestrue, so the submission"
    echo "  would carry draft line numbers in the margin."
    echo "  Set  \\\\draftlinesfalse  in the preamble and rebuild."
    exit 1
fi
echo "  draft line numbers are off"

echo
echo "=== 0b. do the numbers come from real measurements? ==="''',
    "2: packaging refuses while the line numbers are on",
    marker="0a3. is the draft dressing off?")

print(f"done: {N} edits")
