r"""The table was corrected and the test that reads it was not.

fix_tables3 put tab_token's numbers in math mode, because outside it a
negative value prints a hyphen while the same number in the facing table
prints a minus.  make_tables_selftest.py reads those cells back with
float(), so the first build after the correction stopped at

    ValueError: could not convert string to float: '$0.7005$'

This is the shape of defect the paper itself is about: a decision made in
one place and not followed in the other.  The repair is not to special-case
the dollar signs at the one call site but to give the file a single way of
reading a numeric cell, so the next column that gains a delimiter -- or
loses one -- does not stop a build again.

cellnum() is deliberately narrow.  It strips the math delimiters and
nothing else: a cell holding "--", a LaTeX command, or a number dressed in
\times still raises, because those are not numbers this test may silently
reinterpret.

Run:  python fix_selftest_math.py <paper dir>
"""
import io
import os
import re
import sys

os.chdir(sys.argv[1])
PATH = "make_tables_selftest.py"
N = 0

src = io.open(PATH, encoding="utf-8").read()

# ------------------------------------------------------------ 1 the helper
HELPER = '''HERE = os.path.dirname(os.path.abspath(__file__))


def cellnum(cell):
    """One LaTeX table cell as a number.

    The generated tables print their numbers in math mode, so that a
    negative value is a minus and not a hyphen.  This test read them with
    a bare float() and stopped the build the first time a column was
    corrected: ValueError on '$0.7005$'.  Every numeric cell read here
    goes through this, so the next column to gain or lose its delimiters
    costs nothing.

    Narrow on purpose: "--", a LaTeX command, or a number written with
    \\\\times still raises.  Those are not values this test may quietly
    reinterpret.
    """
    s = cell.strip()
    if s.startswith("$") and s.endswith("$"):
        s = s[1:-1].strip()
    return float(s)'''

anchor = "HERE = os.path.dirname(os.path.abspath(__file__))"
if "def cellnum(" in src:
    print("  (already) 1: cellnum()")
else:
    assert src.count(anchor) == 1, f"1: {src.count(anchor)} HERE assignments"
    src = src.replace(anchor, HELPER)
    print("  1: cellnum(), at module level")
    N += 1

# -------------------------------------------------------- 2 the call site
old = 'tmed = [float([c.strip() for c in l.split("&")][-3]) for l in body]'
new = 'tmed = [cellnum(l.split("&")[-3]) for l in body]'
if new in src:
    print("  (already) 2: the token median column")
else:
    assert src.count(old) == 1, f"2: {src.count(old)} occurrences of the read"
    src = src.replace(old, new)
    print("  2: the token median column is read through it")
    N += 1

# ------------------------------- 3 any other bare float() on a table cell
#
# One is enough to stop a build, so the file is scanned rather than
# trusted: a float() applied to something split out of a LaTeX line is the
# same defect waiting for the next column.  Reported, not rewritten --
# rewriting what I have not read is how the last three hours went.
leftover = [
    (i + 1, l.strip())
    for i, l in enumerate(src.split("\n"))
    if re.search(r'float\(.*split\("&"\)', l) and "cellnum" not in l
]
if leftover:
    print("\n  !! other cells still read with a bare float():")
    for ln, text in leftover:
        print(f"     line {ln}: {text}")

if N:
    io.open(PATH, "w", encoding="utf-8").write(src)
print(f"done: {N} edits")
