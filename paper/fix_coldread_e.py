r"""Fifth batch of the independent read.  The first four are the substantive
ones; all are checked against the generator.

27. "The value range of $\sigma$ contains no property of the text", twice,
    with no hypothesis attached.  Eq. (fbzero) is derived FROM "if the
    conditionals are those of some joint"; Section 6.2 then measures a
    sigma that depends on the text, because real masked evaluators are not
    consistent.  Stated flatly the two passages contradict Section 6.

28. "positive in \TailNPositive of them ($p = \TailSignP$, sign test)".
    The \TailNCells cells are \TrendNEval evaluators read on \NCorp
    corpora -- five dependent copies of the same corpora, not 25 draws.
    Section 6.3 makes exactly this objection about its own cells.  The
    pooled p goes; the per-cell tests already carry the threshold.

29. "the two forms do not track each other" / "They do not agree evaluator
    by evaluator", both from \ShareFormRho at \ShareFormP over five points.
    An absence, from an n the same paper says cannot establish one -- the
    defect fixed in Section 6.3 last round, surviving in two more places.
    What IS measured is the factor, and that is what the argument needs.

30. "there the share runs \ShareZMin to \ShareZMax, THE SAME RANGE".  The
    twin of this sentence in the caption was corrected to "overlapping
    ranges of one order" and this one was not.

31. "Table~\ref{tab:decomposition} and Figure~\ref{fig:blkord} give the
    midrank".  tab_decomposition has no midrank column: it prints the two
    components, their share, and the same three in z.  The figure does.

32. \FbNCorpora and \FbBetweenNCorpora are read from different JSON files
    and used for the same corpora in adjacent subsections.  Nothing made
    them agree; now a mismatch fails the build.

33. \SigTokRatioMin--Max are computed over every cell, and quoted for the
    \NTokLarger cells where the token median IS the larger.  If those
    differ the quoted range starts below 1, under the word "larger".

34. The tab:token caption says "its median is the larger of the two" with
    no count, and "in several cells" where \NTokNegAR/\NTokNegARTot exist.

35. "Section~\ref{sec:fbdef} is the measurement of how far two of them
    stand apart".  sec:fbdef is the definition; sec:fbresult measures.

36. "the component takes \CausalCompNDistinct distinct values".  The macro
    is len(set(steps)) -- distinct STEP COUNTS after rounding to the grid.

37. \FbMaskRateVerdict is still generated and is retired, so the sentence
    it was written for is now hand-asserted.  The generator keeps the
    measurement as an assertion instead: if the two evaluators ever stop
    agreeing in sign, the build fails rather than leaving prose that says
    they agree.

38. Two adjacent paragraphs of Section 6.5 open "What differs between the
    two evaluators is".
"""
import io
import os
import sys

os.chdir(sys.argv[1])
N = 0


def rep(path, a, b, label, marker=None):
    """marker: text unique to the result, required when b still contains a.

    Without it, a replacement that keeps its own search text (b beginning
    with a, say) passes the count check on a second run and applies twice.
    Two of this batch's edits did exactly that."""
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


# ------------------------------------------------ 27: the identity's premise
rep("sec_intro.tex",
    r"""The value range of $\sigma$ contains no property of the text.  Three
consequences follow, and they are the content of this paper.""",
    r"""Wherever that premise holds there is no value range to read: $\sigma$ is
the same number, zero, for every text.  Three consequences follow, and they
are the content of this paper.""",
    "27a: the introduction states the identity under its hypothesis")

rep("sec_truesigma.tex",
    r"""Eq.~\eqref{eq:fbzero} seen from the measurement side.  The identity says the
value range of $\sigma$ contains no property of the text; what the
measurement adds is that the range it does contain --- the evaluator's
incompatibility --- is large enough to dominate everything else.""",
    r"""Eq.~\eqref{eq:fbzero} seen from the measurement side.  The identity says
that where the conditionals descend from a joint there is no value range at
all; what the measurement adds is that where they do not --- which is the
case for every masked evaluator we have --- the range that opens carries the
evaluator's incompatibility, and carries it large enough to dominate
everything else.""",
    "27b: Section 6.2, where a text-dependent sigma is being measured")

# --------------------------------------- 28: the cells are not independent
rep("sec_decomp.tex",
    r"""The difference is positive in
\TailNPositive\ of them ($p = \TailSignP$, sign test), and it runs from
$\TailDiffMin$ to $\TailDiffMax$ points on a grid of
$\CeilResolution$.""",
    r"""The difference is positive in
\TailNPositive\ of them, and it runs from $\TailDiffMin$ to $\TailDiffMax$
points on a grid no coarser than $\CeilResolution$.  We quote no pooled test
on that count: the \TailNCells\ cells are \TrendNEval\ evaluators read on the
same \NCorp\ corpora, so they are not \TailNCells\ independent draws, for the
reason Section~\ref{sec:fbresult} gives about its own.""",
    "28: the sign test over dependent cells is withdrawn and the reason given")

# ------------------------------------- 29: an absence from five points, x2
rep("sec_decomp.tex",
    r"""Per evaluator the
two forms do not track each other --- they rank-correlate at $\rho =
\ShareFormRho$ ($p = \ShareFormP$) and one evaluator's share differs between
them by a factor of $\ShareFormWorst$ --- which is the same statement again:
a component one grid step wide does not have a share that survives being
renormalised.""",
    r"""Per evaluator the two forms are not
interchangeable: one evaluator's share differs between them by a factor of
$\ShareFormWorst$.  Whether they track each other across the
$\ShareFormNEval$ evaluators is not a question $\ShareFormNEval$ points can
settle either way ($\rho = \ShareFormRho$, $p = \ShareFormP$); the factor is
the measured part, and it is the same statement again: a component one grid
step wide does not have a share that survives being renormalised.""",
    "29a: Section 5.3")

rep("main.tex",
    r"""They do not agree evaluator by evaluator: across
the $\ShareFormNEval$ of them the two columns rank-correlate at $\rho =
\ShareFormRho$ ($p = \ShareFormP$), and one differs between the forms by a
factor of $\ShareFormWorst$.""",
    r"""They are not interchangeable
evaluator by evaluator: one differs between the forms by a factor of
$\ShareFormWorst$.  Across the $\ShareFormNEval$ of them the two columns
rank-correlate at $\rho = \ShareFormRho$ ($p = \ShareFormP$), which settles
nothing either way at that $n$.""",
    "29b: the Table 2 caption")

# ------------------------------------------------ 30: the untouched twin
rep("sec_decomp.tex",
    r"""there the share runs $\ShareZMin\%$ to $\ShareZMax\%$,
the same range by a normalisation that cannot saturate.""",
    r"""there the share runs $\ShareZMin\%$ to $\ShareZMax\%$ ---
the same order of magnitude, by a normalisation that cannot saturate.""",
    "30: overlapping ranges of one order, as the caption now says")

# ------------------------------------------- 31: what that table prints
rep("main.tex",
    r"""Table~\ref{tab:decomposition} and Figure~\ref{fig:blkord} give the midrank of the authored arrangement among all arrangements of the same text.""",
    r"""Figure~\ref{fig:blkord} gives the midrank of the authored arrangement among
all arrangements of the same text, and Table~\ref{tab:decomposition} gives
that midrank split by Eq.~\eqref{eq:auth} into its two components.""",
    "31: the table prints components, the figure prints the midrank")

# ------------------------------------------------- 35: definition vs result
rep("main.tex",
    r"""It supplies one for each $\pi$, and
Section~\ref{sec:fbdef} is the measurement of how far two of them stand
apart --- $\sigma \neq 0$ is exactly a certificate that they do not coincide.""",
    r"""It supplies one for each $\pi$, and $\sigma$ is
the measurement of how far two of them stand apart --- $\sigma \neq 0$ is
exactly a certificate that they do not coincide.  Section~\ref{sec:fbdef}
defines it and Section~\ref{sec:fbresult} measures it.""",
    "35: the cross-reference points at the subsection that does the thing")

# -------------------------------------------- 36: step counts, not values
rep("sec_decomp.tex",
    r"""Across the \CausalCompNEval\ autoregressive evaluators the component takes
\CausalCompNDistinct\ distinct values, between \CausalCompStepsMin\ and
\CausalCompStepsMax\ steps.""",
    r"""Across the \CausalCompNEval\ autoregressive evaluators the component lands
on \CausalCompNDistinct\ distinct multiples of that grid, between
\CausalCompStepsMin\ and \CausalCompStepsMax\ steps.""",
    "36: the macro counts distinct step counts and the sentence says so")

# --------------------------------------------------- 38: the same opening
rep("sec_truesigma.tex",
    r"""What differs between the two evaluators is how far the authored arrangement
sits from the null, and that is the quantity Eq.~\eqref{eq:fbzero} predicts
should carry the evaluator rather than the text.""",
    r"""How far the authored arrangement sits from the null is exactly the quantity
Eq.~\eqref{eq:fbzero} predicts should carry the evaluator rather than the
text.""",
    "38: the second paragraph does not repeat the first's opening")

# ================================================= the generator: 32, 33, 34, 37
rep("make_tables.py",
    r"""            b_med = float(np.median(blk))
            if abs(b_med) > 1e-9:
                ratio.append(abs(t_med) / abs(b_med))
            if abs(t_med) > abs(b_med):
                larger += 1""",
    r"""            b_med = float(np.median(blk))
            if abs(t_med) > abs(b_med):
                larger += 1
                # Only here.  The prose quotes this range for the cells in
                # which the token median IS the larger; computed over every
                # cell it would start below 1 under the word "larger".
                if abs(b_med) > 1e-9:
                    ratio.append(abs(t_med) / abs(b_med))""",
    "33: the ratio range is the range over the cells it is quoted for")

rep("make_tables.py",
    r"""    mac("FbBetweenMin", f"{min(ms):.4f}")
                mac("FbBetweenMax", f"{max(ms):.4f}")
                mac("FbBetweenNCorpora", str(len(ms)))""",
    r"""    mac("FbBetweenMin", f"{min(ms):.4f}")
                mac("FbBetweenMax", f"{max(ms):.4f}")
                mac("FbBetweenNCorpora", str(len(ms)))
                # Read from a different file than \\FbNCorpora, and used for
                # the same corpora in adjacent subsections.
                if MACROS.get("FbNCorpora", str(len(ms))) != str(len(ms)):
                    raise SystemExit(
                        "FbBetweenNCorpora=%d but FbNCorpora=%s: the "
                        "within-set and between-set runs do not cover the "
                        "same corpora, and the text reads them as one set"
                        % (len(ms), MACROS["FbNCorpora"]))""",
    "32: a mismatch between the two corpus counts fails the build",
    marker="within-set and between-set runs do not cover the")

rep("make_tables.py",
    r"""        same = all(v < 0 for v in vals) or all(v > 0 for v in vals)
        if same:
            mac("FbMaskRateVerdict",
                "They agree in sign, so the reading does not depend on "
                "whether the evaluator saw the mask rates the chain rule "
                "asks it for.")
        else:
            mac("FbMaskRateVerdict",
                "They do not agree in sign, and the mask rate is the "
                "difference between them; the \\textsc{bert} reading has to "
                "be set aside.")""",
    r"""        same = all(v < 0 for v in vals) or all(v > 0 for v in vals)
        # Section 6.5 states in its own words that the two evaluators agree
        # in sign and that the mask rate is therefore not what separates
        # them.  That sentence is hand-written, so the measurement behind it
        # is an assertion here rather than a macro: if the agreement ever
        # fails, the build stops instead of printing prose that says it
        # holds.  (This was \\FbMaskRateVerdict, which no longer has a
        # reader.)
        if not same:
            raise SystemExit(
                "mask rate: the two masked evaluators no longer agree in "
                "sign (%s).  Section 6.5 asserts that they do; rewrite it "
                "before rebuilding." % rs)""",
    "37: the hand-written verdict is backed by an assertion, not a dead macro")

rep("main.tex",
    r"""is dominated by grammaticality: its median is the larger of the two
quantities, and $r$ is negative --- the non-causal texts scoring higher --- in
several cells, which a measure of causal order should not do.""",
    r"""is dominated by grammaticality: its median is the larger of the two
quantities in \NTokLarger\ of \NTokCells\ cells, and $r$ is negative --- the
non-causal texts scoring higher --- in \NTokNegAR\ of \NTokNegARTot\
autoregressive cells, which a measure of causal order should not do.""",
    "34: the caption carries the counts the body quotes")

# ---------------------------------------- the bookkeeping the two imply
# FbMaskRateVerdict is no longer generated, so a retirement entry for it is
# stale and check_paper fails on stale entries.
rep("make_tables.py",
    r""""FbDispPMaxBertBase", "FbMaskRateVerdict", "FbPctCausalBertBase",""",
    r""""FbDispPMaxBertBase", "FbPctCausalBertBase",""",
    "37b: the retirement entry goes with the macro")

# TailSignP lost its only reader in 28.  It stays generated -- the count it
# summarises is still printed -- and is declared retired like the rest.
rep("make_tables.py",
    r"""    "NBlkordCells", "ShareEvalNEval", "ShareZNEval", "TailTrendNEval",""",
    r"""    "NBlkordCells", "ShareEvalNEval", "ShareZNEval", "TailTrendNEval",
    # withdrawn: a sign test over cells that are not independent draws
    "TailSignP",""",
    "28b: TailSignP declared retired",
    marker="# withdrawn: a sign test over cells that are not independent")

rep("make_tables.py",
    r""""FbRMin", "FbRMax", "FbNNegative", "FbMaskRateVerdict",""",
    r""""FbRMin", "FbRMax", "FbNNegative",""",
    "37c: and out of the expected-names list, since nothing emits it")

# The comment that justified 15 last round still asserted the absence that
# 15 removed from the prose.
rep("make_tables.py",
    r"""    # Appendix A forbids, since the two quantities do not track each other.""",
    r"""    # Appendix A forbids: the sweep shows no relation between the two, which
    # at that n is not the same as showing they move apart.""",
    "15b: the comment says what the corrected prose says")

print(f"done: {N} edits")
