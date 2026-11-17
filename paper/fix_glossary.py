r"""The percentile rule names a word where it meant a phrase.

glossary.txt reads

    [tex] midrank | median position, percentile

and the paper uses "percentile" five times in a different sense: the
$\TailZQ$th percentile of the non-causal group's own distribution, which is
the definition of the tail statistic in Section 5.4, and which tab_tail's
generated header prints as well.  That is a quantile of a distribution of
values, not a rank within a permutation set, and renaming it would make
Section 5.4 harder to read for no gain.

What the rule is for is "the percentile of the authored arrangement" --
the midrank called by the wrong name.  That is a phrase, and the rule's own
note already does this for its neighbour: "this rule names the phrases
rather than the word", said of "position", whose other sense is a token
index.  "percentile" has an other sense for the same reason.

So the banned form becomes "percentile of", which catches the misuse and
leaves the quantile alone.  The rule is narrower than it was; the note
records why, so that a later reader does not widen it back without knowing
what it would start catching.

Run:  python fix_glossary.py <paper dir>
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


rep("glossary.txt",
    "[tex] midrank | median position, percentile   #",
    "[tex] midrank | median position, percentile of   #",
    "the rule names the phrase, as its own note says of \"position\"")

rep("glossary.txt",
    "which is why this rule names the phrases rather than the word",
    "which is why this rule names the phrases rather than the word.  "
    "\"percentile\" is the same case: the bare word is a quantile of a "
    "distribution of values (Section 5.4's tail statistic, and tab_tail's "
    "header), and only \"percentile of\" -- the midrank under the wrong "
    "name -- is the error this rule exists for",
    "the note records what the narrowing costs",
    marker="is the same case: the bare word is a quantile")

print(f"done: {N} edits")
