r"""Section 2.1's "the second" points across the distinction it just drew.

The antecedent is the pair in "The corresponding quantities are written
\Dtok and \Dblock here", so "the second" is \Dblock.  But the sentence
immediately before it ends on a different pair -- "a statement made about
$\sigma$ here is never a statement about $\sigma_{block}$ there, and THE
TWO can and do have different signs" -- and a paragraph break stands
between the ordinal and the pair it means.  Read from the nearer pair,
"the second" is $\sigma_{block}$: Ref. [1]'s quantity, not this paper's.

Either reading lands on a block-level quantity, so nothing downstream
breaks.  What is unfortunate is the axis of the ambiguity: it is exactly
the distinction the paragraph exists to draw.  An ordinal is the wrong
device in the one place where the two candidates are the two things the
reader has just been told not to confuse.

One word.

Run:  python fix_second.py <paper dir>
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


rep("main.tex",
    r"""Only the second bears on sentence order, and the work we re-examine says so""",
    r"""Only $\Dblock$ bears on sentence order, and the work we re-examine says so""",
    "the ordinal is replaced by the name it meant")

print(f"done: {N} edits")
