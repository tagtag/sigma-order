r"""The four checks of fix_ar04 were defined and never called.

fix_ar04 inserted them and then did nothing, because its second edit was
guarded by

    marker="check_bare_definite(src)"

and that string is inside the text the FIRST edit inserts: the definition
line reads "def check_bare_definite(src):".  So the guard saw its own
marker in the file, said "(already)", and the call site was never touched.
The build then reported "all relation checks pass" with four rules sitting
in the file unused -- the exact failure mode this project keeps finding in
the paper, reproduced in the tool meant to catch it: a thing declared in
one place and not followed through in the other.

A marker has to be absent from the patch's own replacement text, not only
from the file before it runs.  check_cell_product(args.tables) is: the
definition reads def check_cell_product(tables_dir), so the call form
exists nowhere until this patch writes it.

With the calls in place the three budgets have to be the numbers the paper
actually has, which count_ar.py reports from the same string check_paper.py
reads -- main.tex with its 8 \input files expanded, 280,511 characters.
The seeds in fix_ar04 came from a concatenation of the .tex files and were
too low everywhere.

These are an inventory, not a target:

    bare definite + ambiguous noun     79    (measurement 26, quantity 21)
    counts written as words            37    ("two evaluators" alone is 21)
    comparatives with no baseline      19

Each number is a place a reader has to supply something the sentence does
not give.  They come down as the sections are rendered into Japanese and
read back; they are never raised to make a build pass.

Table 2 joins Table 3 in FLOAT_DISTANCE_OK for the same reason Table 3 is
there: tab:decomposition is cited in Section 3.4, where the decomposition
is defined, and printed beside Section 5, where it is read row by row.

Run:  python fix_ar05.py <paper dir>
"""
import io
import os
import sys

os.chdir(sys.argv[1])
N = 0
APPLIED = []       # every replacement this run has written


def rep(path, a, b, label, marker=None):
    """A marker must not be inside text an EARLIER edit of this patch wrote.

    That is what went wrong in fix_ar04: its second edit was guarded by a
    string the first edit inserts, so on the very first run the guard was
    already satisfied and the edit never happened.  A marker inside its
    OWN replacement is normal -- that is the thing being looked for.
    """
    global N
    assert a not in b or marker, f"{label}: b contains a; pass a marker"
    if marker is not None:
        assert not any(marker in prev for prev in APPLIED), (
            f"{label}: the marker is inside text an earlier edit of this "
            f"patch inserted, so this edit would always look applied")
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
    APPLIED.append(b)
    print(f"  {label}")
    N += 1


# --------------------------------------------------- 1 call them at last
rep("check_paper.py",
    """    check_bare_floor(src)
    check_absence_scope(src)""",
    """    check_bare_floor(src)
    check_bare_definite(src)
    check_spelled_counts(src)
    check_comparison_target(src)
    check_cell_product(args.tables)
    check_absence_scope(src)""",
    "1: the four rules are invoked",
    marker="check_cell_product(args.tables)")

# ------------------------------------- 2 the budgets the paper really has
rep("check_paper.py",
    """BARE_NOUN_BUDGET = {
    "quantity": 16, "labels": 9, "measurement": 11, "comparison": 2,
    "reading": 0, "distance": 3, "statistic": 9, "contrast": 9,
}""",
    """BARE_NOUN_BUDGET = {
    "quantity": 21, "labels": 9, "measurement": 26, "comparison": 2,
    "reading": 0, "distance": 3, "statistic": 9, "contrast": 9,
}""",
    "2: bare definite nouns, 79 of them, counted on the expanded source")

rep("check_paper.py",
    "SPELLED_COUNT_BUDGET = 17",
    "SPELLED_COUNT_BUDGET = 37",
    "3: counts written as words")

rep("check_paper.py",
    "COMPARATIVE_BUDGET = 14",
    "COMPARATIVE_BUDGET = 19",
    "4: comparatives with no baseline in their own sentence")

# ---------------------------------------------- 3 Table 2's own placement
rep("check_paper.py",
    '''FLOAT_DISTANCE_OK = {
    "Every (evaluator, corpus) cell":
        (6, "read row by row in Section 5.3, cited for a range in 4.2"),
}''',
    '''FLOAT_DISTANCE_OK = {
    "Every (evaluator, corpus) cell":
        (6, "read row by row in Section 5.3, cited for a range in 4.2"),
    # Cited in Section 3.4, where Eqs. (12) and (13) define what it
    # decomposes, and printed beside Section 5, which reads it per
    # evaluator.  The gap opened when the abstract grew; the placement
    # was right before and is right now.  DO NOT move the table to the
    # citation: Section 5's reading is what the table is for.
    "Decomposition of the within-text distance":
        (4, "defined in Section 3.4, read per evaluator in Section 5"),
}''',
    "5: Table 2's citation-to-print distance, with the reason it is right",
    marker="Decomposition of the within-text distance")

print(f"done: {N} edits")
