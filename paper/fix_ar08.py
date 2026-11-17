r"""Section 5 was answering the third open question under the first's name.

Rendering Section 1.1 into Japanese, the author asked what the answer to
the first question is.  Twice the answer given back to him mixed in the
decomposition -- the split of the distance into the part any authored
arrangement earns and the part the labels earn -- and twice he said that
belongs to the third question, not the first.  He was right both times,
and the mixing was not in the rendering.  It is in the paper.

The two questions are these:

  FIRST   What does the entropy production of Ref. [1] mean in its
          fixed-text reading?  Answering it needs a comparison whose zero
          holds on the text being read.

  THIRD   Can genuine causal dependence be separated from mere temporal
          ordering?  Answering it needs an origin to measure a distance
          from, and then a decomposition against that origin.

What answers the first is Section 2.2 -- no theorem places the zero of
$\Delta$ on a fixed text -- together with Section 6, which constructs a
comparison that has one and finds that its value reports the evaluator.
What answers the third is Section 3.3, which supplies an origin by the
antisymmetry, and Section 5, which reads the separation off it.

Section 1.1 said otherwise:

    The first is answered twice over: Section 5 reads what Ref. [1]'s own
    first step found, and Section 6 constructs that comparison for a
    fixed text.

and Section 5 opened by claiming the first question's words for itself:

    Section 2.2 named Ref. [1]'s own first step toward saying what its
    quantity means.  This section is that step re-measured.

Section 5 contains no answer to the first question.  5.1 is the labelling,
which is the second.  5.2 is the decomposition, which is the third.  5.3
and 5.4 are how far the decomposition can be read.  The section is the
third question's section, under the first question's banner, which is why
a reader who follows the banner arrives at the decomposition and takes it
for the answer to a question it does not answer.

Nothing measured changes.  What changes is which section is said to answer
what, in the two places that say it.

The reassignment also closes a second thing Section 1.1 did: it discussed
the first question, moved to the third, moved to the second, and then
returned to the first with its definition.  The definition now comes with
the question, and each question is said once.

Run:  python fix_ar08.py <paper dir>
"""
import io
import os
import re
import sys

os.chdir(sys.argv[1])
N = 0
WROTE = []


def rep(path, a, b, label):
    global N
    assert a not in b, f"{label}: b contains a"
    s = io.open(path, encoding="utf-8").read()
    if s.count(a) == 0 and s.count(b) >= 1:
        print(f"  (already) {label}")
        return
    assert s.count(a) == 1, f"{label}: found {s.count(a)} in {path}"
    io.open(path, "w", encoding="utf-8").write(s.replace(a, b))
    WROTE.append((label, b))
    print(f"  {label}")
    N += 1


# ------------------------------------------------- 1. Section 1.1's roll-call
rep("sec_intro.tex",
    r"""Two of the three are questions this paper takes up directly, and they need
different things.  The first is answered twice over:
Section~\ref{sec:causal} reads what Ref.~\cite{sagawa2026}'s own first step
found, and Section~\ref{sec:truesigma} constructs that comparison for a
fixed text.  The third is a question about $\Delta$, and the same
measurement answers it in part without settling it: the distance $\Delta$
reports can be separated into the part any arrangement a passage came in
earns and the part the labels earn, once there is an origin to measure the
distance from.  The second --- the labelling --- conditions what either
answer can mean, and Section~\ref{sec:construct} weighs it separately.  The
first is a question about what the entropy production of
Ref.~\cite{sagawa2026} means in its fixed-text reading: the setting in
which the text was produced by another model
(Section~\ref{sec:notareversal}).  Answering it needs a comparison whose
zero holds on that text, which the model class Ref.~\cite{sagawa2026} uses
cannot supply.""",
    r"""Two of the three are questions this paper takes up directly, and they need
different things.

The first is a question about what the entropy production of
Ref.~\cite{sagawa2026} means in its fixed-text reading: the setting in
which the text was produced by another model.  Answering it needs a
comparison whose zero holds on that text, which the model class
Ref.~\cite{sagawa2026} uses cannot supply.
Section~\ref{sec:notareversal} shows that no theorem places such a zero for
$\Delta$, and Section~\ref{sec:truesigma} constructs a comparison that has
one and measures it.

The third is a question about $\Delta$, and a different measurement answers
it in part without settling it: the distance $\Delta$ reports can be
separated into the part any arrangement a passage came in earns and the
part the labels earn, once there is an origin to measure the distance from.
Section~\ref{sec:blkord} supplies that origin and Section~\ref{sec:causal}
reads the separation off it.  No answer to the first question comes from
there, and none to the third from Section~\ref{sec:truesigma}.

The second --- the labelling --- conditions what either answer can mean,
and Section~\ref{sec:construct} weighs it separately.""",
    "1: each question said once, with the sections that answer it")

# -------------------------------------------- 2. what Section 5 says it is
rep("main.tex",
    r"""Section~\ref{sec:notareversal} named Ref.~\cite{sagawa2026}'s own first
step toward saying what its quantity means.  This section is that step
re-measured,""",
    r"""Section~\ref{sec:notareversal} named Ref.~\cite{sagawa2026}'s own first
step.  What the quantity means is settled there and in
Section~\ref{sec:truesigma}; this section re-measures that step and reads it
for what it separates,""",
    "2: Section 5 drops the first question's banner")

print(f"done: {N} edits")

# ------------------------------------------------------------- self-scan
LONG = [(lab, len(s.split())) for lab, b in WROTE
        for s in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", b))
        if len(s.split()) > 50]
if LONG:
    print("\n  !! replacement text has sentences over 50 words:")
    for lab, n in LONG:
        print(f"     {lab[:40]:42s} {n} words")

src = io.open("sec_intro.tex", encoding="utf-8").read()
for phrase in ("answered twice over", "toward saying what its quantity means"):
    if phrase in src or phrase in io.open("main.tex", encoding="utf-8").read():
        print(f"  !! {phrase!r} is still in the paper")
