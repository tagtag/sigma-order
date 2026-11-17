r"""Two ellipses in eight words, over the two things not to confuse.

    "...on a fixed text the two differ in what each supplies -- $\sigma$
     has a zero there and $\Delta$ has none -- and writing both as
     $\sigma$ is what lets the second be read as though it had the
     first's."

"the second" is $\Delta$ and "the first's" is $\sigma$'s ZERO, the noun
itself elided.  Both referents have to be recovered from a list two
clauses back, and they are precisely the pair the sentence exists to keep
apart: a reader who recovers them the wrong way round reads the sentence
as its own opposite.

Same shape as Section 2.1's "Only the second bears on sentence order",
fixed earlier today.  An ordinal is the wrong device wherever the two
candidates are the two the reader has just been told not to confuse.
Both are named; the length is unchanged.

Edits 2 and 3 are mine to clean up.  check_sigma_prime(), added this
morning, prints a SyntaxWarning on every run of check_paper.py -- its
docstring is not a raw string, so the "\s" of "$\sigma$" and the "\D" of
"\Dblock" are invalid escapes.  A build log that cries wolf is a build log
people stop reading, which is the whole premise of this apparatus.

Run:  python fix_ellipsis.py <paper dir>
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


# ======================================================= 1: the paper
rep("main.tex",
    r"""there and $\Delta$ has none --- and writing both as $\sigma$ is what lets
the second be read as though it had the first's.""",
    r"""there and $\Delta$ has none --- and writing both as $\sigma$ is what lets
$\Delta$ be read as though it had $\sigma$'s zero.""",
    "1: both referents are named where the ordinals stood")

# ======================================== 2 and 3: the warning on every run
rep("check_paper.py",
    'def check_sigma_prime(src):\n    """No sigma-shaped symbol',
    'def check_sigma_prime(src):\n    r"""No sigma-shaped symbol',
    "2: the docstring is raw, so its backslashes are literal",
    marker='r"""No sigma-shaped symbol')

rep("check_paper.py",
    r'"no definition.  It is written \Dblock here." % (form, n))',
    r'"no definition.  It is written \\Dblock here." % (form, n))',
    "3: and the message escapes its own backslash",
    marker=r'written \\Dblock here.')

print(f"done: {N} edits")
