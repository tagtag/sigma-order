r"""The tenth read: Section 5's preamble, twice wrong in two sentences.

 1. It re-states what Section 2.2 already said, in nearly the same words and
    with the same citation, eight pages later -- and Section 2.2's own last
    line is "Section 5 asks what the step found", so the reader is told the
    thing and then told it again.  Section 6 shows the right form: it does
    not re-state, it points back ("Section 2.2 gave the reason...").  The
    preamble takes that form instead.

 2. "What decides what the step can mean is the labelling" is singular and
    exclusive, and Section 5.2 says the opposite in as many words: "The two
    are separate objections and we offer them as such... Neither rests on
    the other."  The replacement claims order, not uniqueness.

 3. Section 5.1's opening sentence is the third statement of the same thing
    inside two lines (preamble, subsection title, sentence).  Deleting it
    orphans the "They" that follows, so the next sentence takes the noun.

Not a source correction, recorded here because the comment that produced
edit 3 of fix_coldread_i.py carried a wrong fact of mine: Ref. [1] Sec. V B
uses GPT-2 ALONE; the Qwen3-4B-Base re-evaluation is its Appendix C.  The
count comparison was dropped before that reached the source, so no sentence
in the paper is affected -- but nothing should ever say "[1, Sec. V B] uses
two evaluators".

Run:  python fix_coldread_j.py <paper dir>
"""
import io
import os
import sys

os.chdir(sys.argv[1])
N = 0


def rep(path, a, b, label, marker=None):
    """marker: text unique to the result, required when b still contains a."""
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


# ============== 1+2: the preamble points back instead of re-stating,
#                     and claims order rather than uniqueness
rep("main.tex",
    r"""Reference~\cite{sagawa2026} presents the labelled contrast as a first step
toward saying what the entropy production means once it is applied to a real
language model~\cite[Sec.~V~B]{sagawa2026}.  This section is that step
re-measured, across a ladder of \TrendNEval\ evaluators.  What decides what
the step can mean is the labelling, which comes first.""",
    r"""Section~\ref{sec:notareversal} ended at Ref.~\cite{sagawa2026}'s own first
step toward saying what its quantity means.  This section is that step
re-measured, across a ladder of \TrendNEval\ evaluators.  The labelling comes
first, because everything after depends on what it records.""",
    "1+2: Section 6's form, and order rather than uniqueness")

# ============== 3: the third statement of the same thing goes, and the
#                   orphaned pronoun takes its noun
rep("main.tex",
    r"""\label{sec:construct}
Everything in this section uses the causal/non-causal labels, so it is worth
being exact about what those labels are.

They record that a language model, given a prompt asking for a short passage""",
    r"""\label{sec:construct}
The labels record that a language model, given a prompt asking for a short
passage""",
    "3: deletion plus the pronoun's antecedent, as one edit")

print(f"done: {N} edits")
