r"""An ellipsis in the abstract that the naming sweep's patterns missed.

    "The reversal that carries that separation is of the text's sentence
     blocks and not of its tokens"

Two supplies:

  "is OF the text's sentence blocks" -- the head noun is elided.  A
  predicative genitive is grammatical, and in a sentence whose subject is
  already "the reversal that ..." it asks the reader to carry that noun
  across a relative clause to use it again.

  "that separation" -- the separation reported in the clause before.
  Naming it as the reported one also marks it as Ref. [1]'s result rather
  than this paper's, which is what the rest of the sentence goes on to
  say.

The sweep's patterns covered possessives with no noun ("a masked model's")
and modals with no verb ("need not"), but not predicates with no head noun
("is of X").  That shape is now in the scan at the bottom of this file, so
the pattern list carries it for the next pass.

Run:  python fix_abs_ellipsis.py <paper dir>
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


rep("main.tex",
    r"""sentence order is arbitrary.  The reversal that carries that separation is of
the text's sentence blocks and not of its tokens:""",
    r"""sentence order is arbitrary.  The reversal that carries the reported
separation is a reversal of the text's sentence blocks and not of its
tokens:""",
    "the head noun and the separation are both supplied")

rep("main.tex",
    r"""sentences in all $n!$ orders.  From here the reversal is of the sentence
blocks rather than the tokens --- the coarse-graining the published analysis""",
    r"""sentences in all $n!$ orders.  From here the reversal rearranges the
sentence blocks rather than the tokens --- the coarse-graining the published
analysis""",
    "2: the same shape, two paragraphs later")

rep("sec_truesigma.tex",
    r"""absence is not of a number but of an independent one: a""",
    r"""absence is not of a number but of an independent number: a""",
    "3: 'one' gets the noun it stands for")

SUSPECT = re.compile(
    r"\b(?:the one|the ones|that kind|this kind|a kind|that form|this form|"
    r"of that|of this|the thing|in this sense|this reading|the other one|"
    r"such a|need not\b(?!\s+\w)|does not\.|do not\.|cannot\.|"
    r"\bis of the\b|\bis of a\b)", re.I)
bad = [(lab, m.group(0)) for lab, b in WROTE for m in SUSPECT.finditer(b)]
if bad:
    print("\n  !! replacement text contains new pointing constructions:")
    for lab, hit in bad:
        print("     %-40s %r" % (lab, hit))
    raise SystemExit("fix the replacements before shipping this patch")
print(f"done: {N} edits (replacement text clean)")
