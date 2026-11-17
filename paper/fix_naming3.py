r"""Naming instead of pointing, batch 3 -- the last of them.

Three sites remain after batches 1 and 2.  The sweep is otherwise done:
the twenty-five "the one"s are ordinary restrictive relatives, the eleven
"in the sense of" uses are the standard idiom for citing a definition, the
fourteen "is a statement about" uses are scoping a claim rather than
hiding one, and every remaining "that X" has its referent inside its own
sentence.

  1. "What differs between the two evaluators IN THIS READING is the
     level the groups sit at."  Added two days ago to stop the sentence
     reading as a denial of Section 6.3's sign disagreement -- and added
     as a pointer rather than a name.  The reading is the within-text one.

  2. "No theorem fixes where the zero of SUCH A QUANTITY lies on one
     text."  The quantity is one evaluated on a fixed text, which is what
     the two sentences before establish.

  3. "the statements below are OF A KIND that holds either way."  The
     property meant is that they survive exchanging the label groups,
     which the same sentence has just described.

The self-scan from batch 2 runs here too.

Run:  python fix_naming3.py <paper dir>
"""
import io
import os
import re
import sys

os.chdir(sys.argv[1])
N = 0
WROTE = []


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
    WROTE.append((label, b))
    print(f"  {label}")
    N += 1


rep("sec_truesigma.tex",
    r"""evaluators in this reading is the level the groups sit at, not the order
they sit in.""",
    r"""evaluators within texts is the level the groups sit at, not the order
they sit in.""",
    "1: the reading is named rather than pointed at")

rep("main.tex",
    r"""fixes where the zero of such a quantity lies on one text.""",
    r"""fixes where the zero of a quantity evaluated on a fixed text lies.""",
    "2: the quantity is described rather than gestured at")

rep("main.tex",
    r"""the exchange for every evaluator), and the statements below are of a kind
that holds either way:""",
    r"""the exchange for every evaluator), and the statements below survive the
exchange:""",
    "3: the property is stated rather than called a kind")

SUSPECT = re.compile(
    r"\b(?:the one|the ones|that kind|this kind|a kind|that form|this form|"
    r"of that|of this|the thing|in this sense|this reading|the other one|"
    r"such a|need not\b(?!\s+\w)|does not\.|do not\.|cannot\.)", re.I)
bad = [(lab, m.group(0)) for lab, b in WROTE for m in SUSPECT.finditer(b)]
if bad:
    print("\n  !! replacement text contains new pointing constructions:")
    for lab, hit in bad:
        print("     %-40s %r" % (lab, hit))
    raise SystemExit("fix the replacements before shipping this patch")
print(f"done: {N} edits (replacement text clean)")
