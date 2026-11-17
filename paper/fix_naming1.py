r"""Naming instead of pointing, batch 1.

The sweep that found eleven unanchored referents used the wrong bar.  It
asked whether an antecedent could be RECOVERED, and 284 of 295 sites
passed.  The bar that matters is whether the thing is NAMED, and far fewer
pass that.  This is why sentences the sweep cleared still stopped a reader.

Three shapes, all the same habit:

  ellipsis   "A masked model's need not"  (two nouns and a verb elided)
  deixis     "The corpora at issue are not of that kind"
  stand-in   "as material they are matched"

The constraint, checkable in the diff: a replacement must be wording the
paper ALREADY USES somewhere else.  Nothing here is invented; every
expansion below is lifted from a sentence elsewhere in the paper that says
the same thing concretely.  So no claim can be widened by this patch, and
the words can be found in the previous version.

Ten sites.  The sources of the replacements:

  1,2  "conditionals come from a joint" -- the clause immediately before.
  3    "survives the transfer" -- the clause immediately before.
  4    "supply the conditionals on the future" -- Section 2.1, abstract.
  5    "controls" -- the same clause.
  6    "changed" -- the clause immediately before.
  7    "a draw from the evaluator's distribution" -- Section 2.2.
  8    "a zero that holds on the text being read" -- Sections 1 and 7.
  9    "the tokens, the length and the vocabulary are identical and only
        their arrangement differs" -- the sentence before it.
  10   "no origin" and "the title" -- the emphasised heading it sits under.

Run:  python fix_naming1.py <paper dir>
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


# ------------------------------------------------------------ ellipsis
rep("main.tex",
    r"""A masked model's need not: it supplies a distribution for each unmasking
order and no single one of them for all.  Wherever the identity holds, the
value range of $\sigma$ carries no property of the text; where it fails,""",
    r"""A masked model's conditionals need not come from a joint: it supplies a
distribution for each unmasking order, and no single one of them covers all
orders.  Where that identity holds, $\sigma$ is the same number, zero,
whatever the text; where it fails,""",
    "1: the elided nouns and verb are supplied, and the zero is stated")

rep("sec_truesigma.tex",
    r"""descend from no joint, and an autoregressive model's is not.""",
    r"""descend from no joint, and an autoregressive model's conditionals do
descend from a joint.""",
    "2: the possessive gets its noun and the verb its complement")

rep("main.tex",
    r"""survives the transfer; the zero does not.""",
    r"""survives the transfer; the zero does not survive it.""",
    "3: the elided verb is supplied")

rep("main.tex",
    r"""a masked model supplies and a model that attends only to what precedes
cannot.""",
    r"""a masked model supplies and a model that attends only to what precedes
cannot supply.""",
    "4: the elided verb is supplied")

rep("main.tex",
    r"""reverse, and the same material, which is why the design controls what a
comparison between two corpora cannot.""",
    r"""reverse, and the same material, which is why the design controls what a
comparison between two corpora cannot control.""",
    "5: the elided verb is supplied")

rep("sec_truesigma.tex",
    r"""Nothing about the texts changed between them; only the evaluator did.""",
    r"""Nothing about the texts changed between them; only the evaluator
changed.""",
    "6: the elided verb is supplied")

# ------------------------------------------------------------ deixis
rep("main.tex",
    r"""The corpora at issue are not of that kind.  They are fixed texts, produced""",
    r"""The corpora at issue are not draws from any evaluator's distribution.
They are fixed texts, produced""",
    "7: 'that kind' is named, in Section 2.2's own words")

rep("main.tex",
    r"""not the zero.  The quantity of Ref.~\cite{sagawa2026} has no zero of that
kind on a single text.""",
    r"""not the zero.  The quantity of Ref.~\cite{sagawa2026} has no zero that
holds on the text being read.""",
    "8: 'that kind' is named, in Sections 1 and 7's own words")

# ------------------------------------------------------------ stand-in
rep("main.tex",
    r"""reverses is the text; as
material they are matched, which is why a difference between them can be
attributed to order and to nothing else.""",
    r"""reverses is the text; as
material they are matched --- same tokens, same length, same vocabulary ---
which is why a difference between them can be attributed to order and to
nothing else.""",
    "9: what 'material' means is carried into the clause that uses it")

rep("main.tex",
    r"""This is the one the
title names, and the one the antisymmetry of Section~\ref{sec:blkord}
answers directly.""",
    r"""The missing origin is what the
title names, and what the antisymmetry of Section~\ref{sec:blkord} answers
directly.""",
    "10: two 'the one's become the thing itself")

print(f"done: {N} edits")
