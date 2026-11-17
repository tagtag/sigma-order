r"""Table 3 is reachable from all three of its callers, and countable.

1.  Section 2.1 quotes a factor of \SigTokRatioMin--\SigTokRatioMax between
    \Dtok and \Dblock.  Since fix_cells.py the denominators are printed, in
    the \texttt{gpt2} rows of Table 3, in the same corpus order as Table 1
    -- but neither the sentence nor either caption says so, so a reader has
    to notice the correspondence thirteen pages apart and do the division.
    One clause, and Section 2.1 joins the caption's list of callers; the
    caption already names the other two.

2.  The \texttt{gpt2-medium}/\textsc{Gemini31} cell prints 0.002, which is
    the Bonferroni threshold 2.0e-3 to the printed precision -- and
    \texttt{gpt2-medium} reaches 4/5 only if that cell clears it.  A reader
    checking the 18 stops there, which is the one thing a table added for
    checkability must not do.  A star marks the cells that clear the
    threshold, as tab_sweep already does, so the count can be read off
    rather than recomputed.  One math group, not two abutting ones, for the
    reason tab_sweep's own helper records.

Run:  python fix_guide.py <paper dir>
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


# ======================================================== 1: the star column
rep("make_tables.py",
    r"""                + f" & ${rr:+.3f}$ & ${tex_p_bare(p)}$ \\\\")""",
    r"""                + f" & ${rr:+.3f}$ & $" + tex_p_bare(p)
                + (r"^{*}" if p < bon else "") + r"$ \\")""",
    "1: the cells that clear the threshold are marked",
    marker='(r"^{*}" if p < bon else "")')

rep("sec_decomp.tex",
    r"""between the label groups, and its two-sided Mann--Whitney $p$.  The counts
quoted in this section and in Section~\ref{sec:capacity} are taken over
these rows; the $\Dblock$ column is the quantity
Section~\ref{sec:capacity} reports a range of.}""",
    r"""between the label groups, and its two-sided Mann--Whitney $p$.  A star
marks the cells that clear the Bonferroni threshold of
$\ContrastBonferroni$, so the counts this section quotes can be read off
rather than recomputed from a $p$ printed at the threshold.  Those counts,
and the ones in Section~\ref{sec:capacity}, are taken over these rows; the
$\Dblock$ column is the quantity Section~\ref{sec:capacity} reports a range
of, and the denominators of the factor quoted in
Section~\ref{sec:fixedtext}.}""",
    "2: the caption explains the star and names its third caller")

# ================================================= 3: Section 2.1 points at it
rep("main.tex",
    r"""two in \NTokLarger\ of the \NTokCells\ evaluator--corpus cells, by a factor of
\SigTokRatioMin--\SigTokRatioMax, and its causal/non-causal effect size $r$""",
    r"""two in \NTokLarger\ of the \NTokCells\ evaluator--corpus cells, by a factor
of \SigTokRatioMin--\SigTokRatioMax (the denominators are the
\texttt{gpt2} rows of Table~\ref{tab:blkcells}, in the same corpus order),
and its causal/non-causal effect size $r$""",
    "3: the factor says where its denominator is printed")

print(f"done: {N} edits")
