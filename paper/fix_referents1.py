r"""Unanchored referents, batch 1 of a systematic sweep.

295 candidate sites were extracted by pattern from the expanded source and
read with their context.  Two patterns are triaged here -- ordinals used as
nouns (26 sites) and demonstrative + abstract noun (23 sites) -- of which
six need the referent named.  The other 43 have their antecedent in the
same sentence or the one before and are left alone; the file does not list
them, but they were read.

The six:

1. Section 1, three-questions paragraph.  "The third is a question about
   $\Delta$ ... The first is a question about what THAT QUANTITY means."
   The nearest antecedent is $\Delta$, from the sentence about the third
   question -- and the first question is not about $\Delta$, it is about
   the quantity Ref. [1] names.  The ordinal order and the antecedent
   order run opposite ways, so the reader who resolves it locally gets it
   backwards.

2. Section 4.1.  "A component that is much the same whichever model
   produced the text is what the sampling account predicts, so THIS
   READING is not evidence against IT."  Two pronouns, and "reading" is
   the paper's word for a single value of $\Delta$, which is not what is
   meant: what is meant is the spread just reported.

3. Section 5.4.  "A stronger evaluator in THIS SENSE pushes an arbitrary
   authored arrangement towards the top."  The preceding sentence is about
   Spearman using only ranks; no sense of "stronger" has been given.  The
   paper's own word for the axis is the ladder.

4. Section 6.3.  "that group is above the null in ... under THE FIRST
   evaluator and in ... under THE SECOND."  The two are named a sentence
   and a half earlier, with two sentences in between.

5. Section 7, first conclusion.  "what Eq. (3) reverses instead is the
   order in which a model assembles a text ... and only THE SECOND has a
   zero that holds on the text being read."  Same shape as the two fixed
   earlier today, and again the two candidates are the pair the paragraph
   exists to separate.

6. Section 8.  "the second rebuilding the first's masked models ... before
   giving each of them THE SECOND ROUTE."  Two different "second"s in one
   sentence: the second script and the second route.

Run:  python fix_referents1.py <paper dir>
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


rep("sec_intro.tex",
    r"""The first is a question about what that quantity
means, and answering it for a fixed text needs a comparison whose zero""",
    r"""The first is a question about what the entropy
production of Ref.~\cite{sagawa2026} means, and answering it for a fixed
text needs a comparison whose zero""",
    "1: the first question is about Ref. [1]'s quantity, not the one the "
    "sentence before names")

rep("main.tex",
    r"""predicts, so this reading is not evidence against it.  We therefore state this""",
    r"""predicts, so the spread just reported is not evidence against that
account.  We therefore state this""",
    "2: the measurement and the account are named instead of pronouns")

rep("sec_decomp.tex",
    r"""A stronger evaluator in this sense pushes an arbitrary authored""",
    r"""An evaluator higher up the ladder pushes an arbitrary authored""",
    "3: the axis is the ladder, which is the word the section uses")

rep("sec_truesigma.tex",
    r"""$\FbAuthoredAboveBertBase$ corpora under the first evaluator and in
$\FbAuthoredAboveLLaDA$ under the second.""",
    r"""$\FbAuthoredAboveBertBase$ corpora under \texttt{bert-base} and in
$\FbAuthoredAboveLLaDA$ under \texttt{LLaDA}.""",
    "4: the evaluators are named where the ordinals reached back three "
    "sentences")

rep("main.tex",
    r"""assembles a text, with the text held fixed, and only the second has a zero
that holds on the text being read (Section~\ref{sec:notareversal}).""",
    r"""assembles a text, with the text held fixed, and only $\sigma$ has a zero
that holds on the text being read (Section~\ref{sec:notareversal}).""",
    "5: the quantity with the zero is named, as in Sections 2.1 and 2.2")

rep("main.tex",
    r"""Table~\ref{tab:bayesroute}, the second rebuilding the first's masked models
from the same seed and reproducing its $\sigEP$ column exactly before
giving each of them the second route.""",
    r"""Table~\ref{tab:bayesroute}, the latter rebuilding the masked models of
\fn{capacity_sweep.py} from the same seed and reproducing its $\sigEP$
column exactly before giving each of them the second route.""",
    "6: one 'second' per sentence, and it is the route")

print(f"done: {N} edits")
