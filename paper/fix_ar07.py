r"""Section 1's opening, as a Japanese rendering left it.

Twenty lines of Section 1 were rendered into Japanese one sentence at a
time and read back by the author.  Five sentences could not be rendered
without asking a question the English does not answer, and each question
had an answer somewhere else in the paper.  That is the shape: not a
missing fact, a fact in the wrong place.

  #20  "the joint distribution that the evaluator defines" -- evaluator is
       first used here and Section 1 never says what one is.  The
       definition lives in the abstract and in Section 3.1, so a reader
       who starts at Section 1 meets an undefined term.

  #21  "measures both readings on the same texts" -- which two is not in
       the sentence, and the same paragraph opens with "The reading is
       supported by...", where reading means the thermodynamic reading.
       One word, two unrelated things, four sentences apart.  The abstract
       says "measures both reversals" for the identical claim, so the
       paper already has the right word in one of the two places.
       "settles the choice" has the same hole: the choice of what, and
       with what consequence, are both outside the sentence.

  #22  "why the token reversal behaves as it does" -- the antecedent is
       two sentences back, with the Section 2.1 sentence in between.

  #23  "dominated by a syntactic artifact" -- first use, no content.
       Section 2.1 has it: token reversal gives "a sequence with the same
       tokens and no grammar".  One clause of that is brought forward.
       The mechanism is NOT explained, because the next sentence says
       this paper does not measure why.

  #24  "We reproduce this." -- this is Ref. [1]'s analysis, but the three
       preceding sentences are about token reversal, so it reads as
       though only the token reversal was reproduced.

Section 2.1 carries the same "settles the choice" and is fixed with it.

With both of those named, one bare "the choice" is left in the paper --
"requires choosing $\pi$, and nothing in the model makes the choice" --
and that one is fine: the choice is named in its own sentence.  So
"choice" joins AMBIGUOUS_NOUNS at a budget of 1, which is the pattern this
file already uses for "floor": the legitimate site is silent and a new one
speaks up.

Run:  python fix_ar07.py <paper dir>
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


# ---- #20  evaluator, said once in Section 1
rep("sec_intro.tex",
    r"""Here $P$ is the joint distribution over token sequences that the evaluator
defines; for an autoregressive model""",
    r"""Here $P$ is the joint distribution over token sequences that the evaluator
--- the model that scores the text --- defines; for an autoregressive model""",
    "20: evaluator glossed at its first use in Section 1")

# ---- #21 #22 #23  the three in one sentence group
rep("sec_intro.tex",
    r"""Ref.~\cite{sagawa2026} reports the token reversal to be dominated by a
syntactic artifact and coarse-grains to blocks for that reason;
Section~\ref{sec:fixedtext} measures both readings on the same texts and
gives the one fact that settles the choice.  Neither we nor
Ref.~\cite{sagawa2026} measure \emph{why} the token reversal behaves as it
does; what is measured is that it does.""",
    r"""Token reversal leaves the same tokens with no grammar, and
Ref.~\cite{sagawa2026} reports the token reversal to be dominated by that
syntactic artifact, coarse-graining to blocks for that reason.
Section~\ref{sec:fixedtext} measures both reversals --- tokens and blocks
--- on the same texts and gives the one fact that settles which of the two
the analysis uses from here on.  Neither we nor Ref.~\cite{sagawa2026}
measure \emph{why} the token reversal is dominated by that artifact; what is
measured is that it is.""",
    "21+22+23: both reversals, the choice named, the artifact given content")

# ---- #24  what was reproduced
rep("sec_intro.tex",
    r"""We reproduce this.  Before any of what follows, the statistical layer of the
published analysis""",
    r"""We reproduce the analysis of Ref.~\cite{sagawa2026}.  Before any of what
follows, the statistical layer of the published analysis""",
    "24: the analysis, not the token reversal")

# ---- #21 again, where Section 2.1 says it
rep("main.tex",
    r"""We reproduce that, and add the fact
that settles the choice.""",
    r"""We reproduce that, and add the fact
that settles which of the two reversals the analysis uses from here on.""",
    "21b: the same sentence in Section 2.1")


# ---- the rule the first of those leaves behind
rep("check_paper.py",
    r"""AMBIGUOUS_NOUNS = ("quantity", "labels", "measurement", "comparison",
                   "reading", "distance", "statistic", "contrast")""",
    r"""AMBIGUOUS_NOUNS = ("quantity", "labels", "measurement", "comparison",
                   "reading", "distance", "statistic", "contrast",
                   "choice")""",
    "25: choice joins the family")

rep("check_paper.py",
    r"""    "quantity": 16, "labels": 9, "measurement": 11, "comparison": 2,
    "reading": 0, "distance": 3, "statistic": 9, "contrast": 9,
}""",
    r"""    "quantity": 16, "labels": 9, "measurement": 11, "comparison": 2,
    "reading": 0, "distance": 3, "statistic": 9, "contrast": 9,
    # The one left is "requires choosing $\\pi$, and nothing in the model
    # makes the choice", where the sentence names it.  The two that are
    # gone were both "the fact that settles the choice", in Section 1 and
    # in Section 2.1, neither of which said what was being chosen.
    "choice": 1,
}""",
    "26: budget 1, the site that is legitimate")

print(f"done: {N} edits")

# ------------------------------------------------------------- self-scan
LONG = [(lab, len(s.split())) for lab, b in WROTE
        for s in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", b))
        if len(s.split()) > 50]
if LONG:
    print("\n  !! replacement text has sentences over 50 words:")
    for lab, n in LONG:
        print(f"     {lab[:40]:42s} {n} words")

for lab, b in WROTE:
    for word in ("readings", "behaves as it does", "We reproduce this"):
        if word in b:
            print(f"  !! {lab}: replacement still contains {word!r}")
