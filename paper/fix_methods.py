r"""Section 3, read as a reader: twelve places that point instead of naming.

Methods carries the highest density of these in the paper (7.5 sites per
thousand words against a median of 3.9).  Nothing here is false.  In every
one of them a reader has to supply something the sentence withheld: a
reason not yet given, a noun elided twice, an ordinal standing for a model,
a paragraph referred to by position among four.

Ordered as the PDF prints them.  The heavier seven first in the list below;
the file applies them in source order.

   L383   the one thing that bears on Section 6.4
   L384   the first ... the second ... conditionals it did
   L392   and the reason decides            (the reason is not yet given)
   L414   rather than a detail of it        (of what?)
   L418   does not notice                   (notice what?)
   L419   the paragraph above               (one of four)
   L421   the one model class that has one  (two pro-forms, one clause)
   L442   centred at zero by identity       (collides with the paper's own
                                             reserved sense of "identity")
   L452   before noticing                   (noticing what?)
   L457   share ties between the arrangements that are tied   (circular)
   L472   the second half of the statement ... and the same material
   L509   it is the one Section 4 rests on

L442 is the one to look at twice.  Fifteen lines above it a source comment
reserves "the identity", unqualified, for sigma = 0 of Eq. (fbzero),
because the abstract once called both exact results "an identity" and the
definite article swallowed the second.  The antisymmetry is then introduced
and called an identity in the next paragraph.

Run:  python fix_methods.py <paper dir>
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


# ---------------------------------------------------------- L383 and L384
rep("main.tex",
    r"""(Section~\ref{sec:limitations} returns to this).  The masked pair differs in the one thing that bears on
Section~\ref{sec:maskrate}: \texttt{bert-base} is trained at a single masking
rate and \texttt{LLaDA} at a rate drawn uniformly, so the chain rule asks the
first for conditionals it never saw and the second only for conditionals it
did.""",
    r"""(Section~\ref{sec:limitations} returns to this).  The masked pair differs in
exactly the way that matters for Section~\ref{sec:maskrate}:
\texttt{bert-base} is trained at a single masking rate and \texttt{LLaDA} at
a rate drawn uniformly, so the chain rule asks \texttt{bert-base} for
conditionals it never saw in training and \texttt{LLaDA} only for
conditionals it saw.""",
    "L383, L384: what matters, and which model is which")

# ----------------------------------------------------------------- L392
rep("main.tex",
    r"""once.  That is available for an autoregressive evaluator and for no other
kind, and the reason decides which evaluators appear in which half of this
paper.""",
    r"""once.  That is available for an autoregressive evaluator and for no other
kind.  The rest of this subsection says why, and the same reason decides
which evaluators appear in which half of this paper.""",
    "L392: the reason is given below, and the sentence says so")

# ----------------------------------------------------------------- L414
rep("main.tex",
    r"""choice, and because the size of what that choice can move is the subject of
Section~\ref{sec:fbdef} rather than a detail of it.""",
    r"""choice, and because how much that choice can move the number is the subject
of Section~\ref{sec:fbdef}, not a detail to be set aside here.""",
    "L414: what the choice moves, and what it is not a detail of")

# ------------------------------------------------- L418, L419 and L421
rep("main.tex",
    r"""Section~\ref{sec:blkord} does not notice, because it is score-agnostic: it
asks only for a number per token sequence.  But the paragraph above says
plainly that the quantity so obtained is not $\Delta$, so a comparison
between it and $\Delta$ compares two different things and concludes about
neither.  The substitution also puts a quantity devised to work around the
absence of a backward process on the one model class that has one.""",
    r"""Section~\ref{sec:blkord} does not notice the substitution, because it is
score-agnostic: it asks only for a number per token sequence.  But the
quantity so obtained is not $\Delta$: $\Delta$ asks for $\log P$ from one
distribution, and a masked model supplies no single distribution.  A
comparison between it and $\Delta$ compares two different things and
concludes about neither.  The substitution also takes a quantity devised to
work around the absence of a backward process and applies it to masked
models, the only class for which a backward process exists.""",
    "L418, L419, L421: notice what, which paragraph, and which class")

# ----------------------------------------------------------------- L442
rep("main.tex",
    r"""set $\{\Delta(\pi)\}$ is centred at zero by identity.""",
    r"""set $\{\Delta(\pi)\}$ is centred at zero by construction.""",
    "L442: not \"identity\", which this paper reserves for Eq. (fbzero)")

# ----------------------------------------------------------------- L452
rep("main.tex",
    r"""known.  We ran it before noticing, obtained a large effect size and a very""",
    r"""known.  We ran it before noticing the antisymmetry, obtained a large effect
size and a very""",
    "L452: noticing what",
    marker="antisymmetry, obtained a large effect")

# ----------------------------------------------------------------- L457
rep("main.tex",
    r"""The rank must share ties between the arrangements that are tied.  A score that cannot distinguish the arrangements at all gives""",
    r"""Arrangements that produce the same value of $\Delta$ must share a rank.  A
score that cannot distinguish the arrangements at all gives""",
    "L457: the rule, stated without using the word it defines")

# ----------------------------------------------------------------- L472
rep("main.tex",
    r"""comparison is made.  This is the second half of the statement in
Section~\ref{sec:notareversal}: the arrangements being compared are
different sequences, which is why $\Delta$ is not a path against its
reverse, and the same material, which is why the design controls what a
comparison between two corpora cannot control.""",
    r"""comparison is made.  Section~\ref{sec:notareversal} said that the
arrangements being compared are different sequences, which is why $\Delta$
is not a path against its reverse.  They are also the same material, which
is why the design controls what a comparison between two corpora cannot
control.""",
    "L472: two sentences, each with its subject in front of its verb")

# ----------------------------------------------------------------- L509
rep("main.tex",
    r"""One thing survives the exchange, and it is the one Section~\ref{sec:authored}
rests on.""",
    r"""One thing survives the exchange, and Section~\ref{sec:authored} rests on
it.""",
    "L509: the thing, not a pro-form standing for it")

# Two refinements, both the same shape as the "the one rung" one: a
# pro-form is the defect, a determiner with its noun present is not.
# "of this paper", "of this subsection" are not "the opposite of this".
SUSPECT = re.compile(
    r"\bthe ones?\s*(?=[.,;:]|\b(?:that|which|it|we|they|the|is|are)\b)|"
    r"\bof (?:that|this)\s*(?=[.,;:]|\b(?:is|are|was|were|and|or|we|it|they)\b)|"
    r"\b(?:that kind|this kind|a kind|that form|this form|"
    r"the thing|in this sense|this reading|the other one|"
    r"such a|that of|need not\b(?!\s+\w)|does not\.|do not\.|cannot\.|"
    r"\bis of the\b|\bis of a\b|\band not of\b|\bbut not of\b)", re.I)
bad = [(lab, m.group(0)) for lab, b in WROTE for m in SUSPECT.finditer(b)]
if bad:
    print("\n  !! replacement text contains new pointing constructions:")
    for lab, hit in bad:
        print("     %-40s %r" % (lab, hit))
    raise SystemExit("fix the replacements before shipping this patch")
print(f"done: {N} edits (replacement text clean)")
