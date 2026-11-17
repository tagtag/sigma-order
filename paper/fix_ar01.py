r"""Two counts the prose needs and the generator did not emit.

The abstract says the contrast separates the groups in N of 25 (evaluator,
corpus) cells.  A reader who wants to check that against the tables has to
work out what 25 is made of, and the paper never says: there is no macro
for the number of autoregressive evaluators in that measurement, nor for
the number of corpora.  \TrendNEval exists but is emitted by a different
function over a different set, and \FbNCorpora counts the masked side.

contrast_macros() already has both sets in hand, one line above the count
it emits.  This emits them beside it, so the prose can print 25 as the
product it is, and so a later check can verify that it is.

Run:  python fix_ar01.py <paper dir>
"""
import io
import os
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


# ------------------------------------------------- 1 emit the two counts
rep("make_tables.py",
    '''    mac("ContrastNCells", str(len(ps)))''',
    '''    mac("ContrastNCells", str(len(ps)))
    # The cell count is a product and the prose should be able to say so.
    # Both sets are already fixed above: models is ar_only() of the keys,
    # corpora is order_c() of them, and len(ps) is one test per pair.  A
    # reader who cannot see 25 as 5 x 5 cannot check the claim against the
    # table, which is the hole this paper is about.
    mac("ContrastNEval", str(len(models)))
    mac("ContrastNCorpora", str(len(corpora)))''',
    "1: ContrastNEval and ContrastNCorpora, beside the count they factor",
    marker='mac("ContrastNEval"')

# ------------------------------------------- 2 register the two new names
rep("make_tables.py",
    '''                "ContrastNCells", "ContrastNRejecting",''',
    '''                "ContrastNCells", "ContrastNEval", "ContrastNCorpora",
                "ContrastNRejecting",''',
    "2: and both are expected, so a run that stops emitting them is caught",
    marker='"ContrastNEval", "ContrastNCorpora",')

print(f"done: {N} edits")
