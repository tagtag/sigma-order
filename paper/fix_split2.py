r"""The long-sentence tail, batch 1 of the sweep: six splits and a check fix.

54 sentences run over 50 words.  Sorted and read, they fall in three
groups: long because they list generated numbers (splitting gains
nothing), long because they are a semicolon list (an enumeration is what
it is), and long because one sentence carries three or four claims.  Only
the third group is worth touching, and these six are from it.

THE RULE, as before and checkable in the diff: SPLIT, DO NOT REWRITE.
Every clause carrying a claim keeps its words; what changes is where the
sentence ends and the connective that joins the pieces.

  1. Section 5.4's threshold sentence, 77 words: where the onset is, what
     single evaluators do below it, what the table shows, what the sweep
     is not for.  Four claims, two dash-pairs, one semicolon.

  2. Section 1, 57 words: that no identity is available, why, and how the
     magnitude behaves across the ladder.

  3. Section 4.1, 78 words: the claim, then twenty-five words of numbers
     inside a dash-pair, then the rest of the claim.  The subject and its
     final clause are separated by the whole parenthesis; the numbers go
     after.

  4. Section 1, 56 words: a claim and its two halves of evidence.

  5. Section 1, 55 words: subject and verb separated by a 25-word
     apposition.  Rebuilt as three short sentences -- and not with
     "supplying one", which would put back the pro-form that this pass
     spent the day removing.

  6. Section 2.1, 54 words: three claims in one.

AND a false positive in the check added an hour ago: the author
affiliation is counted as a 57-word sentence.  prose_sentences now starts
at the abstract.

Run:  python fix_split2.py <paper dir>
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


# ------------------------------------------------------------------ 1
rep("sec_decomp.tex",
    r"""$t = \TailOnsetThr$ the worst evaluator shows no difference worth a point,
and $\TailOnsetThr$ is where the worst of them first passes one --- single
evaluators reach $\TailBelowOnsetMax$ points below it, which the table shows
and this threshold does not --- and from there the difference opens for all
of them; Table~\ref{tab:sweep} gives every
threshold and every evaluator, and no test is run on the sweep --- it
locates the contrast, and the cell-level tests below measure it.""",
    r"""$t = \TailOnsetThr$ the worst evaluator shows no difference worth a point,
and $\TailOnsetThr$ is where the worst of them first passes one.  Single
evaluators reach $\TailBelowOnsetMax$ points below it, which the table shows
and this threshold does not, and from there the difference opens for all of
them.  Table~\ref{tab:sweep} gives every threshold and every evaluator, and
no test is run on the sweep: it locates the contrast, and the cell-level
tests below measure it.""",
    "1: four claims, three sentences")

# ------------------------------------------------------------------ 2
rep("sec_intro.tex",
    r"""Nothing in that is an identity, and no identity is
available: $\Delta$ is a log-ratio between a text and its reversal, and
nothing drives that to zero as a model improves --- a better model estimates
the ratio better rather than making it vanish, and across the ladder its
magnitude grows by a factor of $\CapRatioMedian$.""",
    r"""Nothing in that is an identity, and no identity is
available: $\Delta$ is a log-ratio between a text and its reversal, and
nothing drives that to zero as a model improves.  A better model estimates
the ratio better rather than making it vanish, and across the ladder its
magnitude grows by a factor of $\CapRatioMedian$.""",
    "2: the claim, then how the magnitude behaves")

# ------------------------------------------------------------------ 3
rep("main.tex",
    r"""evaluator ranks a text's own arrangement above most rearrangements of the
same sentences --- across the \TrendNEval\ autoregressive evaluators the median
midrank is $\MedPctNoncausal$ on the non-causal texts and $\MedPctCausal$ on
the causal ones, against a null of $0.50$; these are medians of medians and
their difference is not any evaluator's component --- and that this is so whichever group is asked, long before any
question about causal structure is settled.""",
    r"""evaluator ranks a text's own arrangement above most rearrangements of the
same sentences, and that this is so whichever group is asked, long before
any question about causal structure is settled.  Across the
\TrendNEval\ autoregressive evaluators the median midrank is
$\MedPctNoncausal$ on the non-causal texts and $\MedPctCausal$ on the causal
ones, against a null of $0.50$; these are medians of medians and their
difference is not any evaluator's component.""",
    "3: the claim first, the numbers after")

# ------------------------------------------------------------------ 4
rep("sec_intro.tex",
    r"""range the same contrast is neither at the floor nor flat: nothing separates the two
groups by more than $\TailBelowOnsetMax$ points below a midrank of
$\TailOnsetThr$ --- above it every evaluator does --- and at the top of the
range the
separation grows along the ladder in units that have no ceiling.""",
    r"""range the same contrast is neither at the floor nor flat.  Nothing separates
the two groups by more than $\TailBelowOnsetMax$ points below a midrank of
$\TailOnsetThr$, and above it every evaluator does; at the top of the range
the separation grows along the ladder in units that have no ceiling.""",
    "4: the claim, then its two halves of evidence")

# ------------------------------------------------------------------ 5
rep("sec_intro.tex",
    r"""them it responds to.  Supplying the origin that Eq.~\eqref{eq:delta} lacks ---
the distribution of $\Delta$ over the $n!$ arrangements of a text's own
$n$ sentences, against which the authored arrangement can be located ---
decomposes the measured distance into two: the part the order a passage
came in earns on its own, and the
part only causal order earns.""",
    r"""them it responds to.  Equation~\eqref{eq:delta} lacks an origin.  The
distribution of $\Delta$ over the $n!$ arrangements of a text's own
$n$ sentences supplies an origin, and the authored arrangement can be
located against that distribution.  Locating it decomposes the measured
distance into two: the part the order a passage came in earns on its own,
and the part only causal order earns.""",
    "5: subject and verb are no longer twenty-five words apart")

# ------------------------------------------------------------------ 6
rep("main.tex",
    r"""notational fastidiousness and the choice of letter is an argument: on a
fixed text the two differ in what each supplies --- $\sigma$ has a zero
there and $\Delta$ has none --- and writing both as $\sigma$ is what lets
$\Delta$ be read as though it had $\sigma$'s zero.""",
    r"""notational fastidiousness, and the choice of letter is an argument.  On a
fixed text the two differ in what each supplies: $\sigma$ has a zero there
and $\Delta$ has none.  Writing both as $\sigma$ is what lets $\Delta$ be
read as though it had $\sigma$'s zero.""",
    "6: three claims, three sentences")

# ------------------------------------------------------------------ 7
rep("check_paper.py",
    r'''    t = re.sub(r"\\begin\{(table|figure|equation|align|tabular|center)\*?\}"
               r".*?\\end\{\1\*?\}", " ", src, flags=re.S)''',
    r'''    # Start at the abstract: the author block is not prose, and its
    # affiliation line was being counted as a 57-word sentence.
    i = src.find(r"\begin{abstract}")
    t = src[i:] if i > 0 else src
    t = re.sub(r"\\begin\{(table|figure|equation|align|tabular|center)\*?\}"
               r".*?\\end\{\1\*?\}", " ", t, flags=re.S)''',
    "7: the affiliation is not a sentence",
    marker="Start at the abstract")

rep("check_paper.py",
    '''        (r"\\b(?:need not|does not|do not|cannot|can|could|would|did)[.,;:]", 8),''',
    '''        # 9 and not 8 since fix_split2: splitting Section 5.4's threshold
        # sentence turned a dash into a comma, and the pattern keys on the
        # punctuation after the modal.  The construction is unchanged --
        # "which the table shows and this threshold does not [show]", a
        # parallel with its verb one clause back, like the other eight.
        (r"\\b(?:need not|does not|do not|cannot|can|could|would|did)[.,;:]", 9),''',
    "8: the budget records why it moved",
    marker="9 and not 8 since fix_split2")

SUSPECT = re.compile(
    r"\b(?:the one|the ones|that kind|this kind|a kind|that form|this form|"
    r"of that|of this|the thing|in this sense|this reading|the other one|"
    r"such a|that of|need not\b(?!\s+\w)|does not\.|do not\.|cannot\.|"
    r"\bis of the\b|\bis of a\b|\band not of\b|\bbut not of\b)", re.I)
bad = [(lab, m.group(0)) for lab, b in WROTE for m in SUSPECT.finditer(b)]
if bad:
    print("\n  !! replacement text contains new pointing constructions:")
    for lab, hit in bad:
        print("     %-40s %r" % (lab, hit))
    raise SystemExit("fix the replacements before shipping this patch")
print(f"done: {N} edits (replacement text clean)")
