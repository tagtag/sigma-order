r"""Sections 2.1 and 2.2, rendered into Japanese and read back.

Items #37 to #68.  Almost every one is the same defect: a sentence that
names a comparison, a pair, a side, a direction or a row, and leaves the
other half of it outside the sentence.  The English reads as though the
reader still has the previous paragraph in working memory; the Japanese
cannot be written at all until the missing half is named, which is how
each of these was found.

Four are more than wording.

  #39 / #44  Section 2.1 announced "the fact that settles the choice" and
    then reported $r$ as negative in 3 of 5 cells, which reads as a sign
    split evenly.  The values are -0.279, -0.522, -0.214 against +0.050
    and +0.078: three real and two at zero.  The paper was stating its own
    evidence more weakly than the evidence is.  The announcement goes and
    the attribution moves onto the measurement it belongs to.

  #45  The same caption says "the \NTokNegARTot\ autoregressive cells",
    which reads as several autoregressive evaluators.  tab_token.tex has
    one, \textsc{gpt-2}, on five corpora.  The choice of block reversal,
    which everything after Section 2.1 depends on, rests on measurements
    made with a single evaluator, and the caption should not disguise
    that.

  #61  Under $\Delta$ the causal group scores higher; under $\sigma$ it
    scores lower.  Section 2.2 explains the first direction (causal prose
    has strong forward dependence) and nothing in the paper explains the
    second.  A reader who has been given a reason for one sign will ask
    about the other, and silence reads as not having noticed.  The answer
    is that the question does not arise -- Eq. (4) makes a reading of
    $\sigma$ in either direction a reading of the evaluator -- and
    Section 6.3 now says so.

  #66  "$\Delta$ needs one joint $P$, which a masked model does not
    supply" reads as though Eq. (1) cannot be computed on a masked model.
    Section 3.2 says the opposite in as many words: the shape can of
    course be evaluated there.  What fails is the identification, not the
    arithmetic.  The sentence and the contrast table's "requires" row both
    now say that.

The last of those also closes the budget this project left open: with
"nothing in the model makes the choice" rewritten, the paper has no bare
"the choice" left, so the budget goes to zero.

Run:  python fix_ar11.py <paper dir>
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
    WROTE.append((label, a, b))
    print(f"  {label}")
    N += 1


# =====================================================================
#  Section 2.1
# =====================================================================

# ---- #37  the build is not part of the research
rep("main.tex",
    r"""Here every text cut into exactly $\NBlocks$ blocks and none was dropped,
which the build checks for the block count; a text that failed to split would not appear in the measurements at all.""",
    r"""Here every text cut into exactly $\NBlocks$ blocks and none was dropped; a
text that failed to split would not appear in the measurements at all.""",
    "37: the build check leaves the paper")

# ---- #38 #39  the work we re-examine; the empty announcement
rep("main.tex",
    r"""Only $\Dblock$ bears on sentence order, and the work we re-examine says so
first:""",
    r"""Only $\Dblock$ bears on sentence order, and Ref.~\cite{sagawa2026} says so
first:""",
    "38: Ref. [1], not a paraphrase of it")

rep("main.tex",
    r"""We reproduce that, and add the fact
that settles which of the two reversals the analysis uses from here on.  Both quantities are measured on the same texts, and""",
    r"""We reproduce that.  Both quantities are measured on the same texts, and""",
    "39a: the announcement goes")

# ---- #40 #41  the two; both sides
rep("main.tex",
    r"""$\Dtok$ is reported in Table~\ref{tab:token}.  Its median is the larger of
the two in \NTokLarger\ of the \NTokCells\ evaluator--corpus cells, by a
factor of \SigTokRatioMin--\SigTokRatioMax, which Table~\ref{tab:token}
prints both sides of.""",
    r"""$\Dtok$ is reported in Table~\ref{tab:token}.  Its median is larger than
that of $\Dblock$ in \NTokLarger\ of the \NTokCells\ evaluator--corpus
cells, by a factor of \SigTokRatioMin--\SigTokRatioMax;
Table~\ref{tab:token} prints the two medians rather than the ratio.""",
    "40+41: larger than what, and what the table prints")

# ---- #39b #44  what r actually is, and whose fact it is
rep("main.tex",
    r"""--- is \emph{negative}, the non-causal texts scoring higher, in
\NTokNegAR\ of \NTokNegARTot\ cells.  A quantity whose sign on the contrast of interest flips
when the reversal operation is changed is not measuring that contrast, so the
block-level analysis is the one followed from here on, and $\Dtok$ appears
only in that table.""",
    r"""--- is \emph{negative}, the non-causal texts scoring higher, in
\NTokNegAR\ of the \NTokNegARTot\ cells, and negligible in the rest:
nowhere is it positive to any degree.  This effect size is not in
Ref.~\cite{sagawa2026}; it is what settles which of the two reversals the
analysis uses from here on.  The texts and the labels are the same; only
the reversal changes, from blocks to tokens, and the sign of the effect
size changes with it.  A quantity whose sign on the contrast of interest
turns over when only the reversal operation is changed is not measuring
that contrast, so the block-level analysis is the one followed from here
on, and $\Dtok$ appears only in Table~\ref{tab:token}.""",
    "39b+42+44: the fact attributed, the flip spelled out, r stated as it is")

# ---- #43 #44 #45 #46  the caption
rep("main.tex",
    r"""\caption{The two reversals side by side on the same texts, which is the
comparison this section makes: the medians of $\Dtok$ and $\Dblock$, and
the rank-biserial effect size $r$ of Eq.~\eqref{eq:rb} on the token
reading.  It is""",
    r"""\caption{Token reversal and block reversal side by side on the same texts,
which is the comparison this section makes: the medians of $\Dtok$ and
$\Dblock$, and the rank-biserial effect size $r$ of Eq.~\eqref{eq:rb} under
the token reversal.  It is""",
    "43: the two reversals named, and reading dropped for reversal")

rep("main.tex",
    r"""is dominated by grammaticality: its median is the larger of the two
quantities in \NTokLarger\ of \NTokCells\ cells, and $r$ is negative --- the
non-causal texts scoring higher --- in \NTokNegAR\ of the
\NTokNegARTot\ autoregressive cells of this table, which a measure of
causal order should not do.  Nothing else in
this paper reads $\Dtok$.}""",
    r"""is dominated by grammaticality: its median is larger than that of $\Dblock$
in \NTokLarger\ of \NTokCells\ cells, and $r$ is negative --- the
non-causal texts scoring higher --- in \NTokNegAR\ of the
\NTokNegARTot\ cells of this table, every one of them \textsc{gpt-2}, and
negligible in the rest.  Nothing else in this paper reads $\Dtok$.}""",
    "44+45+46: one evaluator named, the verdict left to the text")


# =====================================================================
#  Section 2.2
# =====================================================================

# ---- #47  printed, and which pair
rep("main.tex",
    r"""Equation~\eqref{eq:fbzero} is printed for the
left-to-right and right-to-left pair, but what""",
    r"""Equation~\eqref{eq:fbzero} is stated for the
left-to-right and right-to-left pair that defines $\sigma$, but what""",
    "47: stated, and the pair tied back to sigma")

# ---- #48 #49 #50 #51  the four in the zero sentence
rep("main.tex",
    r"""that this text is symmetric under the chosen $R$ for this model --- and
not the value a quantity takes when there is nothing to report; its
non-negativity is a statement about an average under $P_c$, with
equality when the law is invariant under $R$.  That is the sense in which it
is not anchored for a single text (Section~\ref{sec:capacity}).""",
    r"""that this text is symmetric under the chosen block-reversal map $R$ for
this model --- and not an origin of the kind $\sigma$ has, the value
returned whenever there is nothing to report.  Its non-negativity is a
statement about an average under $P_c$, with equality when $P_c$ is
invariant under $R$, and no average can be taken over one text.  That is
the sense in which it has no origin for a single text
(Section~\ref{sec:capacity}).""",
    "48+49+50+51: R named, the two zeros contrasted, P_c named, origin")

# ---- #52  the double negative
rep("main.tex",
    r"""Eq.~\eqref{eq:fbzero} gives that an origin.  Both statements hold whether or
not the text came from the model.""",
    r"""Eq.~\eqref{eq:fbzero} gives that an origin.  Neither the absence of an
origin under text reversal nor its presence under schedule reversal depends
on where the text came from.""",
    "52: said as content rather than as two statements holding")

# ---- #53  the antisymmetry, in one clause
rep("main.tex",
    r"""without either reversal doing the work: Section~\ref{sec:blkord} supplies
$\Delta$ with an origin, on an autoregressive evaluator and for any score
whatever, from the antisymmetry rather than from reversing anything --- an
origin, and not an entropy production.""",
    r"""without either reversal doing the work.  Section~\ref{sec:blkord} supplies
$\Delta$ with an origin: $\Delta(\pi) = -\Delta(\pi \circ \mathrm{rev})$, so
the $n!$ values come in pairs and the set is centred at zero.  That holds on
an autoregressive evaluator and for any score whatever, and it comes from
the antisymmetry rather than from reversing anything --- an origin, and not
an entropy production.""",
    "53: the antisymmetry written out where it is first appealed to")

# ---- #54 #55  which name, and a property of the evaluator
rep("main.tex",
    r"""reports is a separate question, and the answer is not what the name
promises: Section~\ref{sec:fbresult} measures it and finds it
reporting the evaluator rather than the text.""",
    r"""reports is a separate question, and the answer is not what the name
\emph{entropy production} promises: Section~\ref{sec:fbresult} measures it
and finds it reporting a property of the evaluator rather than of the text.""",
    "54+55: the name said, and the property restored")

# ---- #56  That / it
rep("main.tex",
    r"""probability for a sequence and for a rearrangement of it.  That is a
well-defined quantity, and this paper measures it throughout.  What it is
not is a quantity with a zero.""",
    r"""probability for a sequence and for a rearrangement of it.  That is
$\Delta$, a well-defined quantity, and this paper measures it throughout.
$\Delta$ is not a quantity with a zero.""",
    "56: Delta named where the paper first commits to measuring it")

# ---- #57  the general principle, marked as one
rep("main.tex",
    r"""it~\cite[Sec.~V~B]{sagawa2026}.  The theorems that place a quantity's zero and its sign are what
say what it is a quantity of.  A correlation between that quantity and a
label, found afterwards, is not:""",
    r"""it~\cite[Sec.~V~B]{sagawa2026}.  In general it is the theorems placing a
quantity's zero and its sign that say what it is a quantity of, and in the
fixed-text reading there are none.  A correlation between $\Delta$ and a
label, found afterwards, does not supply one:""",
    "57: a general principle, and then its application")

# ---- #58 #59 #60  the source, the model, model-relative
rep("main.tex",
    r"""forward and backward cross-entropy of a fixed corpus is not an informational
asymmetry in the source.  It is a property of the model and of the order in
which that model consumes its input --- which is consistent with reading
$\Delta$ as model-relative, and is one reason its dependence on the evaluator
(Section~\ref{sec:capacity}) is worth measuring rather than assuming away.""",
    r"""forward and backward cross-entropy of a fixed corpus is not an informational
asymmetry in the source --- the process that produced the text.  It is a
property of the evaluator and of the order in which the evaluator consumes
its input.  That is consistent with reading $\Delta$ as a quantity of the
text and the evaluator together rather than of the text alone, and it is one
reason its dependence on the evaluator (Section~\ref{sec:capacity}) is worth
measuring rather than assuming away.""",
    "58+59+60: the source glossed, the evaluator named, model-relative opened")

# ---- #62  why it is the wrong place
rep("main.tex",
    r"""None of this makes the framework the wrong one; it makes a fixed text
prepared outside the model the wrong place for it.""",
    r"""None of this makes the framework the wrong one.  What the theorems ask for
is an ensemble of trajectories drawn from the model's own distribution, not
one fixed text prepared outside it.""",
    "62: the reason returned to the conclusion")

# ---- #63  what sigma reverses
rep("main.tex",
    r"""compete: as sequences they are distinct, which is why what $\Delta$
reverses is the text; as""",
    r"""compete: as sequences they are distinct, which is why what $\Delta$
reverses is the text itself, where $\sigma$ reverses the order of assembly
with the text held fixed; as""",
    "63: the other half of the contrast")

# ---- #64  two consequences, two reasons
rep("main.tex",
    r"""nothing else.  Together
they say what $\Delta$ is --- a comparison between two sequences matched in
everything but order --- and that is at once why it reads order well and why
it has no origin on the text it is read from.""",
    r"""nothing else.  Together they say what $\Delta$ is: a comparison between two
sequences matched in everything but order.  $\Delta$ picks up differences in
order, because any difference between the two can only come from order; and
$\Delta$ has no origin on the text it is read from, because the two are
different sequences and no reference point lies on the text itself.""",
    "64: one fact, two consequences, each with its reason")

# ---- #65  not zero at all
rep("main.tex",
    r"""whose conditionals come from a joint, while $\Delta$ for those same models
is not zero at all --- as sharp a separation as two quantities can have.""",
    r"""whose conditionals come from a joint, while $\Delta$ for those same models
is not identically zero, taking a value that varies from text to text ---
as sharp a separation as two quantities can have.""",
    "65: identically zero, which is what was meant")

# ---- #66  computable, but not Delta
rep("main.tex",
    r"""$\Delta$ needs \emph{one} joint $P$ for Eq.~\eqref{eq:delta}, which an
autoregressive factorisation supplies and a masked model does not
(Section~\ref{sec:scope}); $\sigma$ needs a conditional on the future, which
a masked model supplies and a model that attends only to what precedes
cannot supply.""",
    r"""$\Delta$ needs its two terms to come from \emph{one} joint $P$.  An
autoregressive factorisation supplies one; a masked model supplies one for
each $\pi$ and none that Eq.~\eqref{eq:delta} can be written in without
choosing a $\pi$ the model does not single out, so the shape of
Eq.~\eqref{eq:delta} can be evaluated there but the result is not $\Delta$
(Section~\ref{sec:scope}).  $\sigma$ needs a conditional on the future,
which a masked model supplies and an autoregressive evaluator cannot.""",
    "66: the shape is computable; the identification is not")

rep("main.tex",
    r"""requires            & \emph{one} joint $P$
                    & a conditional on the future \\""",
    r"""requires            & its two terms to come from
                      \emph{one} joint $P$
                    & a conditional on the future \\""",
    "66b: the same correction in the contrast table")

# ---- #66c  the sentence that the budget was holding open
rep("main.tex",
    r"""requires choosing $\pi$,
and nothing in the model makes the choice.""",
    r"""requires choosing $\pi$,
and the model does not single out one.""",
    "66c: the model does not single out one")

rep("check_paper.py",
    r"""    # The one left is "requires choosing $\\pi$, and nothing in the model
    # makes the choice", where the sentence names it.  The two that are
    # gone were both "the fact that settles the choice", in Section 1 and
    # in Section 2.1, neither of which said what was being chosen.
    "choice": 1,""",
    r"""    # Zero since fix_ar11.  The last one was "requires choosing $\\pi$, and
    # nothing in the model makes the choice", now "the model does not
    # single out one"; the two before it were "the fact that settles the
    # choice", in Section 1 and in Section 2.1.
    "choice": 0,""",
    "66d: budget 1 -> 0, no bare 'the choice' is left")

# ---- #67  surviving what
rep("main.tex",
    r"""                    & \quad \FbNCells, \FbNSurviving\ surviving \\
\bottomrule""",
    r"""                    & \quad \FbNCells, \FbNSurviving\ surviving \\
                    &
                    & \quad the correction for multiple \\
                    &
                    & \quad comparisons \\
\bottomrule""",
    "67: surviving the correction for multiple comparisons")

# ---- #68  which row, and what license means
rep("main.tex",
    r"""significantly in \ContrastNRejecting\ --- and the row above says what a
separation would and would not license.""",
    r"""significantly in \ContrastNRejecting\ --- and the ``a separation under it
would mean'' row says what may and may not be concluded from a separation.""",
    "68: the row named and license opened")


# =====================================================================
#  Section 6.3
# =====================================================================

# ---- #61  the direction of sigma, which the paper never addressed
rep("sec_truesigma.tex",
    r"""measurement.

Nor does the sweep""",
    r"""measurement.  The direction differs between the two: under $\Delta$ the
causal group scores higher, under $\sigma$ lower.  We do not account for
that difference, and nothing here needs to --- by Eq.~\eqref{eq:fbzero} a
reading of $\sigma$ of any size, in either direction, is a reading of the
evaluator's incompatibility and not of the text's causal structure.

Nor does the sweep""",
    "61: the sign difference between Delta and sigma, stated and set aside")

# ------------------------------------------ the budget this patch earns
rep("check_paper.py",
    "SENTENCE_BUDGET = 40   # fix_ar09 took it to 42, this patch to 40",
    "SENTENCE_BUDGET = 39   # fix_ar10 took it to 40, this patch to 39",
    "budget: over-50 sentences 40 -> 39")

print(f"done: {N} edits")


# ------------------------------------------------------------- self-scan
def _nouns():
    try:
        src = io.open("check_paper.py", encoding="utf-8").read()
        ns = {}
        exec(re.search(r"AMBIGUOUS_NOUNS = \(.*?\)", src, re.S).group(0), ns)
        exec(re.search(r"NOUN_QUALIFIERS = \(.*?\)", src, re.S).group(0), ns)
        return ns["AMBIGUOUS_NOUNS"], ns["NOUN_QUALIFIERS"]
    except Exception as exc:
        print(f"  (no noun self-scan: {exc})")
        return (), ()


AMB, QUAL = _nouns()
bad = []
for lab, a, b in WROTE:
    for noun in AMB:
        pat = r"\bthe %s\b(?!\s+(?:%s))" % (noun, "|".join(QUAL))
        before = len(re.findall(pat, re.sub(r"\s+", " ", a)))
        after = len(re.findall(pat, re.sub(r"\s+", " ", b)))
        if after > before:
            bad.append((lab, noun, after - before))
if bad:
    print("\n  !! this patch ADDS bare ambiguous nouns:")
    for lab, noun, n in bad:
        print('     %-40s +%d bare "the %s"' % (lab[:40], n, noun))

grew = []
for lab, a, b in WROTE:
    def longest(t):
        ss = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", t))
        return max((len(s.split()) for s in ss), default=0)
    if longest(b) > 50 and longest(b) > longest(a):
        grew.append((lab, longest(a), longest(b)))
if grew:
    print("\n  !! replacement LENGTHENS a sentence past 50 words:")
    for lab, x, y in grew:
        print(f"     {lab[:40]:42s} {x} -> {y} words")

for lab, a, b in WROTE:
    for word in ("the work we re-examine", "prints both sides of",
                 "is not anchored", "model-relative",
                 "the larger of the two"):
        if word in b:
            print(f"  !! {lab}: replacement still contains {word!r}")
