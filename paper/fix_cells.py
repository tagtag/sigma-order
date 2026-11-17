r"""The reader's findings A and B: the autoregressive cells get a table.

A.  "separates the two label groups in N of the 25 (evaluator, corpus)
    cells" is the paper's most-repeated number -- abstract, Section 1,
    Section 5.3, Section 7, the comparison table -- and the 25 cells are
    tabulated nowhere.  contrast_macros pools the per-cell p and r into
    min/max/count, so the evaluator dimension never reaches the output: a
    reader cannot see whether the cells that fail are spread across the
    ladder or stacked on one rung, and neither can the author.  Section 5.4
    spends a subsection on the evaluator axis.

B.  The raw \Dblock is tabulated nowhere either, which is what leaves
    Section 4.2's "No stable scale" -- one of the three conclusions -- with
    its numbers in prose only, and leaves Section 2.1's factor of 7.2-10.9
    with no printed denominator.

Both are the same defect as the between-set one, and both are fixed by one
table: blk already carries sigma_written and percentile_written per record,
so a cell can print the authored median of \Dblock beside the contrast that
cell supports.  Per-evaluator counts become macros, and Section 5.3 states
the breakdown rather than only the total.

C.  Section 6.3's causal component of the between-set reading is still
    prose-only, but its evaluator dimension is visible (two numbers, two
    counts).  Following Table 4's own practice, the sentence now says it is
    a summary.

D.  Section 6.4's "not the order they sit in" is read, two paragraphs after
    Section 6.3 reports a sign disagreement, as denying it.  Section 6.3
    scopes the same claim itself; Section 6.4 gets the same scope.

Run:  python fix_cells.py <paper dir>
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


# =============================================== 1: keep the cells, not just
#                                                    their min and max
rep("make_tables.py",
    r"""def contrast_macros(blk, kinds):""",
    r"""def contrast_macros(blk, kinds, outdir=None):""",
    "1: the function can write its table",
    marker="def contrast_macros(blk, kinds, outdir=None):")

rep("make_tables.py",
    r"""    ps, rs = [], []
    for model in models:
        for corpus in corpora:
            recs = blk.get((model, corpus), {})""",
    r"""    ps, rs = [], []
    cells = []          # (model, corpus, median Dblock authored, r, p)
    for model in models:
        for corpus in corpora:
            recs = blk.get((model, corpus), {})""",
    "2: the per-cell record is kept",
    marker="(model, corpus, median Dblock authored, r, p)")

rep("make_tables.py",
    r"""            u, p = mannwhitneyu(pc, pn, alternative="two-sided")
            ps.append(float(p))
            rs.append(2.0 * u / (len(pc) * len(pn)) - 1.0)""",
    r"""            u, p = mannwhitneyu(pc, pn, alternative="two-sided")
            ps.append(float(p))
            rr = 2.0 * u / (len(pc) * len(pn)) - 1.0
            rs.append(rr)
            # The authored median of Dblock in the same cell.  It is the
            # quantity Section 4.2 quotes a range of and Section 2.1 takes
            # a ratio of, and it was printed in no table.
            sw = [r["sigma_written"] for r in recs.values()
                  if r.get("sigma_written") is not None]
            cells.append((model, corpus,
                          float(np.median(sw)) if sw else None,
                          rr, float(p)))""",
    "3: the authored median of Dblock travels with its cell",
    marker="The authored median of Dblock in the same cell")

# =============================================== 4: the table and the
#                                                    per-evaluator counts
rep("make_tables.py",
    r"""    mac("ContrastRMin", f"{min(rs):+.3f}")
    mac("ContrastRMax", f"{max(rs):+.3f}")""",
    r"""    mac("ContrastRMin", f"{min(rs):+.3f}")
    mac("ContrastRMax", f"{max(rs):+.3f}")
    # Per evaluator.  "N of 25" says nothing about whether the cells that
    # fail are spread over the ladder or stacked on one rung, and Section
    # 5.4 argues about the ladder for a whole subsection.
    for model in models:
        t = TAG.get(model)
        if not t:
            continue
        own = [c for c in cells if c[0] == model]
        if not own:
            continue
        mac(f"ContrastNRejecting{t}",
            str(sum(1 for c in own if c[4] < bon)))
        mac(f"ContrastNCellsOf{t}", str(len(own)))
        sw = [c[2] for c in own if c[2] is not None]
        if sw:
            mac(f"ContrastDeltaMed{t}", f"{float(np.median(sw)):+.4f}")
    if outdir:
        lines = [r"% generated by make_tables.py -- do not edit",
                 r"\begin{tabular}{llrrr}",
                 r"\toprule",
                 r"evaluator & corpus & median $\Dblock$ & $r$ & $p$ \\",
                 r"\midrule"]
        for model, corpus, sw, rr, p in cells:
            lines.append(
                f"{model.split('/')[-1]} & {corpus.replace('fixed_text_', '')}"
                f" & " + ("--" if sw is None else f"${sw:+.4f}$")
                + f" & ${rr:+.3f}$ & ${tex_p_bare(p)}$ \\\\")
        lines += [r"\bottomrule", r"\end{tabular}"]
        open(os.path.join(outdir, "tab_blkcells.tex"), "w").write(
            "\n".join(lines) + "\n")
        print(f"  tab_blkcells.tex  ({len(cells)} cells)")""",
    "4: per-evaluator counts, and the table the 25 cells never had",
    marker="tab_blkcells.tex")

rep("make_tables.py",
    r"""    contrast_macros(blk, kinds)""",
    r"""    contrast_macros(blk, kinds, args.outdir)""",
    "5: invoked with an outdir")

# =============================================== 6: registered
rep("make_tables.py",
    r"""                "ContrastNPositive", "ContrastRMedian", "ContrastRMin",
                "ContrastRMax",""",
    r"""                "ContrastNPositive", "ContrastRMedian", "ContrastRMin",
                "ContrastRMax",
                "ContrastNRejectingGPTtwo", "ContrastNCellsOfGPTtwo",
                "ContrastNRejectingGPTtwoMedium",
                "ContrastNCellsOfGPTtwoMedium",
                "ContrastNRejectingGPTtwoLarge",
                "ContrastNCellsOfGPTtwoLarge",
                "ContrastNRejectingGPTtwoXL", "ContrastNCellsOfGPTtwoXL",
                "ContrastNRejectingQwen", "ContrastNCellsOfQwen",
                "ContrastDeltaMedGPTtwo", "ContrastDeltaMedQwen",""",
    "6: registered",
    marker='"ContrastNRejectingGPTtwo", "ContrastNCellsOfGPTtwo",')

# =============================================== 7: Section 5.3 states the
#                                                    breakdown and cites it
rep("sec_decomp.tex",
    r"""It does not separate them
everywhere: the worst cell gives $p = \ContrastPWorst$, and the
rank-biserial effect size runs from $\ContrastRMin$ to $\ContrastRMax$ with
a median of $\ContrastRMedian$.""",
    r"""It does not separate them
everywhere: the worst cell gives $p = \ContrastPWorst$, and the
rank-biserial effect size runs from $\ContrastRMin$ to $\ContrastRMax$ with
a median of $\ContrastRMedian$.  The cells that clear the threshold are not
stacked on one rung of the ladder --- \ContrastNRejectingGPTtwo\ of
\ContrastNCellsOfGPTtwo\ at the bottom and \ContrastNRejectingQwen\ of
\ContrastNCellsOfQwen\ at the top --- and
Table~\ref{tab:blkcells} prints every cell, since a count over a ladder
says nothing about where on the ladder it falls.""",
    "7: the breakdown is stated, not only the total",
    marker="not\nstacked on one rung of the ladder")

# =============================================== 8: the table float
rep("sec_decomp.tex",
    r"""\paragraph{The median is one statistic of the contrast, and not a
representative one.}""",
    r"""\begin{table}[tbp]
\centering
{\small\input{tables/tab_blkcells}}
\caption{Every (evaluator, corpus) cell of the autoregressive ladder: the
median $\Dblock$ of the authored arrangement, the rank-biserial effect size
between the label groups, and its two-sided Mann--Whitney $p$.  The counts
quoted in this section and in Section~\ref{sec:capacity} are taken over
these rows; the $\Dblock$ column is the quantity
Section~\ref{sec:capacity} reports a range of.}
\label{tab:blkcells}
\end{table}

\paragraph{The median is one statistic of the contrast, and not a
representative one.}""",
    "8: the float",
    marker="label{tab:blkcells}")

# =============================================== 9: Section 4.2 cites it
rep("main.tex",
    r"""arrangement moves from $\CapDeltaLo$ to $\CapDeltaHi$ on identical texts.""",
    r"""arrangement moves from $\CapDeltaLo$ to $\CapDeltaHi$ on identical texts
(Table~\ref{tab:blkcells} prints it for every cell).""",
    "9: the range has a table behind it")

# =============================================== 10: Section 6.3's summary
#                                                     says that it is one
rep("sec_truesigma.tex",
    r"""\FbBetweenNNegOf{BertBase}\ corpora --- the same side of zero as the""".replace("{BertBase}", "BertBase"),
    r"""\FbBetweenNNegOfBertBase\ corpora, summarised rather than printed --- the
same side of zero as the""",
    "10: a summary is named as one, as Table 4's caption already does",
    marker="summarised rather than printed")

# =============================================== 11: Section 6.4's scope
rep("sec_truesigma.tex",
    r"""evaluators is the level the groups sit at, not the order they sit in.""",
    r"""evaluators in this reading is the level the groups sit at, not the order
they sit in.""",
    "11: scoped, so it does not read as denying Section 6.3's disagreement")


# =============================================== 12: the selftest covers the
#                                                     dimension, not just the
#                                                     total
rep("make_tables_selftest.py",
    """    assert float(g["ContrastRMedian"]) > 0.9, g["ContrastRMedian"]""",
    """    assert float(g["ContrastRMedian"]) > 0.9, g["ContrastRMedian"]
    # The count is over a ladder, so the ladder has to survive into the
    # output: "N of 25" was reported for revisions with no way to see
    # whether the failures were spread or stacked.
    assert g["ContrastNCellsOfGPTtwo"] == "5", g.get("ContrastNCellsOfGPTtwo")
    assert g["ContrastNCellsOfQwen"] == "5", g.get("ContrastNCellsOfQwen")
    assert g["ContrastNRejectingGPTtwo"] == "5", \\
        g.get("ContrastNRejectingGPTtwo")
    with tempfile.TemporaryDirectory() as _d:
        M.MACROS.clear()
        M.contrast_macros(blk, kinds, _d)
        assert os.path.exists(os.path.join(_d, "tab_blkcells.tex")), \\
            "the autoregressive cells have no table again"
        rows = open(os.path.join(_d, "tab_blkcells.tex")).read()
        assert rows.count(chr(92) * 2) >= 25, rows
    print("  contrast cells: the ladder survives into the macros and a table")""",
    "12: the per-evaluator counts and the table are asserted",
    marker="the ladder survives into the macros")

print(f"done: {N} edits")
