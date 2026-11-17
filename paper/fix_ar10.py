r"""Section 1.2, rendered into Japanese and read back.

Items #25 to #36 of the correction table.  The author read Section 1.2 one
sentence at a time and stopped at each place the Japanese could not be
written without asking a question the English does not answer.  Three
decisions came out of that reading and they shape this patch:

  * Section 1.2 drops its numbers.  They are in the abstract and again in
    Sections 5 and 6, and carrying them here forces in terms the reader does
    not have yet -- cell, midrank, grid step, the median of what.  Every
    one of those was a stop.  What survives is said without them: the causal
    part is small and no more than a few times the smallest non-zero value
    the statistic can return.  That is a statement about resolution, not a
    figure.

  * The first consequence loses the argument about supplying the backward
    factors from the joint.  Eq. (3) is defined through Eq. (2) on the
    conditionals the evaluator emits; an autoregressive evaluator emits no
    right-hand conditional, so Eq. (3) does not stand for it, and that is
    the whole of it.  The sentence that said "for any model whose
    conditionals come from a joint --- an autoregressive evaluator among
    them --- sigma is identically zero" put an autoregressive evaluator in a
    class it is not in and contradicted the same paragraph four sentences
    earlier.  It goes.

  * Each question is named where it is answered.  "Both questions" was two
    of three and the reader had to count back; the decomposition paragraph
    carried no label at all while the paragraph after it did.  And the first
    question is answered by the identity, not by Section 5: Section 5
    measures, and the labelling premise it leans on is Ref. [1]'s own and
    belongs to the second question.  fix_ar08 settled that for Section 1.1
    and this settles it for Section 1.2, which still said "twice".

Run:  python fix_ar10.py <paper dir>
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


# ------------------------------------------------- #26  the first consequence
rep("sec_intro.tex",
    r"""\emph{First}, what an autoregressive evaluator can report here is not what
the name promises, and the difference is worth being exact about.  The
backward term of Ref.~\cite{sagawa2026} is obtained by re-indexing: the
reversed sequence is fed to the same model as an ordinary input and scored
in a second forward pass, so it is available to an autoregressive model, and
Ref.~\cite{sagawa2026} computes it on \textsc{gpt-2}.  What is not available
is a conditional on the future.  Equation~\eqref{eq:fb} holds every token at
its own position and asks for its probability given what stands to its
right, and a model
that attends only to what precedes supplies none of those factors.  They are
nevertheless fixed by its joint, and anything fixed by a joint satisfies
Eq.~\eqref{eq:fbzero} by construction, so supplying them that way returns
the zero rather than escaping it.  Unavailable, or zero: in neither case
does an autoregressive evaluator report anything about the text here.
Equation~\eqref{eq:delta} is what can be computed in its place --- but its
two terms score two \emph{different} sequences, and
Section~\ref{sec:notareversal} sets out what follows from that.  We therefore write it $\Delta$
throughout and reserve $\sigma$ for Eq.~\eqref{eq:fb}.  Keeping the two
apart matters for a second reason, independent of the first: they behave
differently under the very operation that defines them.  For any model whose
conditionals come from a joint --- an autoregressive evaluator among them ---
$\sigma$ is identically zero while $\Delta$ is not, which
Section~\ref{sec:fbdef} proves as an identity.""",
    r"""\emph{First}, an autoregressive evaluator has no part here.  The backward
term of Eq.~\eqref{eq:fb} asks each token for its probability given what
stands to its right, and a model that attends only to what precedes does not
emit it, so Eq.~\eqref{eq:fb} does not stand for an autoregressive
evaluator.  What Ref.~\cite{sagawa2026} computes is Eq.~\eqref{eq:delta},
whose two terms score two \emph{different} sequences, and
Section~\ref{sec:notareversal} sets out what follows from that.  We
therefore write it $\Delta$ throughout and reserve $\sigma$ for
Eq.~\eqref{eq:fb}.""",
    "26: the first consequence, without the argument from the joint")

# ------------------------------------------------ #27 #30  the second
rep("sec_intro.tex",
    r"""\emph{Second}, $\Delta$ does separate the two label groups, and we ask what in
them it responds to.  On a fixed text Eq.~\eqref{eq:delta} lacks an
origin.  The
distribution of $\Delta$ over the $n!$ arrangements of a text's own
$n$ sentences supplies an origin, and the authored arrangement can be
located against that distribution.  Locating it decomposes the measured
distance into two: the part the order a passage came in earns on its own,
and the part only causal order earns.  Across the AR ladder the causal
part is $\ShareZMin\%$ to $\ShareZMax\%$ of the total in units with no
ceiling, and $\ShareEvalMin\%$ to $\ShareEvalMax\%$ in midrank units.  That
part separates the two label groups in \ContrastNRejecting\ of the
\ContrastNCells\ (evaluator, corpus) cells (worst cell $p =
\ContrastPWorst$, two-sided Mann--Whitney against a Bonferroni threshold
of $\ContrastBonferroni$) and in
midrank units it is \CausalCompStepsMin\ to \CausalCompStepsMax\ steps of the
$1/n!$ grid the statistic lives
on, one step being the smallest non-zero reading available: what the median
establishes is that the two label groups differ, not by how much.  That part is \CausalCompStepsMin\ to \CausalCompStepsMax\ steps at
every size we
measured, over a \TrendCapSpan-fold range of parameters.  Read higher up the
range the same contrast is neither at the grid floor nor flat.  Nothing separates
the two groups by more than $\TailBelowOnsetMax$ points below a midrank of
$\TailOnsetThr$, and above it every evaluator does; at the top of the range
the separation grows along the AR ladder in units that have no ceiling.  One contrast, two statistics, two
answers --- which is the subject of Sections~\ref{sec:resolution}
and~\ref{sec:window}.""",
    r"""\emph{Second}, $\Delta$ does separate the two label groups, and we ask what in them it responds to.  On a fixed text
Eq.~\eqref{eq:delta} lacks an origin.  The distribution of $\Delta$ over the
$n!$ arrangements of a text's own $n$ sentences supplies an origin, and the
authored arrangement can be located against that distribution.  Locating it
decomposes the measured distance --- how far that position lies from the
middle of the distribution --- into two: the part the order a passage came
in earns on its own, and the part only causal order earns.  The causal part
is small --- within a few multiples of the smallest non-zero value that can
be read off at all.  Read as the median of each label group's
position, what is established is that the two label groups differ, not by
how much.  Read higher in the distribution the same contrast behaves
differently.  One contrast, two statistics, two answers --- which is the
subject of Sections~\ref{sec:resolution} and~\ref{sec:window}.""",
    "27+30: the second consequence, qualitative and with the first behind it")

# ----------------------------------------------------- #30  the third
rep("sec_intro.tex",
    r"""\emph{Third}, $\sigma$ does not measure causality either, and
Eq.~\eqref{eq:fbzero} says why before any measurement is taken.  A
non-zero reading is a measure of the evaluator's \emph{in}compatibility --- its
conditionals descending from no joint --- as exposed by that text.  We measure
it on two masked evaluators across $\FbNCorpora$ corpora, both within texts (the authored arrangement's rank among the $n!$) and between the two label groups.
Both constructions place the \emph{median} causal contribution on the same
side of zero, and it is the side that subtracts: a causal text exposes
\emph{less} of the evaluator's incompatibility, not more.  Cell by cell the
sign holds in \FbNNegative\ of the \FbNCells\ evaluator--corpus cells rather
than in all of them, the magnitude does not reach significance, and in any
case a contrast that did
would be a contrast in how much of the evaluator's defect a text exposes,
which is not a property of the text's causal structure.""",
    r"""\emph{Third}, $\sigma$ does not measure causality either, and
Eq.~\eqref{eq:fbzero} says why before any measurement is taken.  A non-zero
reading is a measure of the evaluator's \emph{in}compatibility --- its
conditionals descending from no joint --- as exposed by that text.  We
measure it on masked evaluators, and whatever comes out is a contrast in how
much of the evaluator's defect a text exposes, which is not a property of
the text's causal structure.""",
    "30: the third consequence, qualitative")

# ------------------------------------------------------- #33  which two
rep("sec_intro.tex",
    r"""Both questions therefore have answers, and they rest on different things.""",
    r"""The first and the third of the three questions above therefore have
answers, and they rest on different things.""",
    "33: the first and the third, named")

# ------------------------------------- #34 #35 #36  the third's paragraph
rep("sec_intro.tex",
    r"""The separation \emph{can} be carried out on $\Delta$, and the
answer is a measurement: $\ShareZMin\%$ to $\ShareZMax\%$ of the distance
is attributable to causal order and the rest to the arrangement being the
order the passage was produced in; read instead on the midrank it is
$\ShareEvalMin\%$ to
$\ShareEvalMax\%$, where the causal part is
\CausalCompStepsMin--\CausalCompStepsMax\ steps of a grid and its size is
not resolved.  Nothing in that is an identity, and on a fixed text no identity is
available: $\Delta$ is a log-ratio between a text and its reversal, and
nothing drives that to zero as a model improves.  A better model estimates
the ratio better rather than making it vanish, and across the AR ladder its
magnitude grows by a factor of $\CapRatioMedian$.  The reasons it cannot
answer the causal question are the size of that share and the absence of any criterion defining the two label groups.""",
    r"""\emph{The third.}  The separation \emph{can} be carried out on $\Delta$,
and the answer is a measurement: part of the distance is attributable to
causal order and the rest to the arrangement being the order the passage was
produced in, with the causal part within a few multiples of the smallest
non-zero value that can be read off and its size not resolved.  Nothing
in that is an identity, and on a fixed text no identity is available:
$\Delta$ is the log of the ratio between the probability given to a text and
that given to its reversal --- the difference of the two terms of
Eq.~\eqref{eq:delta}.  A better model estimates the ratio better rather than
making it vanish, and along the AR ladder its magnitude grows.  The reasons
it cannot answer the causal question are the size of that share and the
absence of any criterion defining the two label groups.""",
    "34+35+36: labelled, qualitative, and the log-ratio tied to Eq. (1)")

# --------------------------------------------- #25 #34  the first's paragraph
rep("sec_intro.tex",
    r"""The first is answered in the other direction, and twice.  Read on what
Ref.~\cite{sagawa2026}'s own first step produced,
Section~\ref{sec:causal} finds the quantity varying with the labels and the
labels with no criterion behind them, so the variation has no referent to be
a meaning.  Read on the comparison constructed for a fixed text,
Eq.~\eqref{eq:fbzero} answers before anything is measured: $\sigma$ is""",
    r"""\emph{The first.}  It is answered in the other direction, and not by a
measurement.  Equation~\eqref{eq:fbzero} answers before anything is
measured: $\sigma$ is""",
    "25+34: labelled, and the route through Section 5 withdrawn")

# ------------------------------------------ the budget this patch earns
rep("check_paper.py",
    "SENTENCE_BUDGET = 44   # reported by the build after fix_split3",
    "SENTENCE_BUDGET = 40   # fix_ar09 took it to 42, this patch to 40",
    "budget: over-50 sentences 44 -> 40")

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
    for word in ("an autoregressive evaluator among them",
                 "and twice", "Both questions therefore"):
        if word in b:
            print(f"  !! {lab}: replacement still contains {word!r}")
