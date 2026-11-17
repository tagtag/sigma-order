r"""Table 1 carries the comparison its own caption makes.

The caption says "its median is the larger of the two quantities in N of M
cells" and the table prints one of the two.  A reader cannot check the
claim the caption makes without turning to Table 3, fourteen pages on, and
matching five numbers by corpus order.  That is the shape closed twice
already this week -- a measurement reported only as a macro, with no table
to read it off.

The block median is already computed in table_token(), one line above the
row it does not go into.  Adding the column settles four things at once:

  * the caption's comparison can be checked in the table that makes it;
  * Section 2.1's ratio can be divided out in one place;
  * Section 2.1 no longer has to cite Table 3, so Table 3's first citation
    moves from page 6 to its own section and the float warning shrinks;
  * the sentence that aimed the reader at Table 3 -- "the denominators are
    the gpt2 rows of Table 3, in the same corpus order" -- goes, which is
    fourteen words back against a length budget with no headroom.

AND THE COMPARISON IS CHECKED, not asserted.  The two columns come from
different measurement files: the token table reads the pll records, Table 3
reads the blkord ones.  The prose has been claiming they agree on the
gpt2 cells; nothing verified it.  The new check does, cell by cell, in
corpus order.

If that check FAILS on first run, the failure is the finding: it means the
sentence this patch deletes was asserting an agreement that does not hold,
and the column should stay while we look at why.  It is written to FAIL
rather than warn for that reason.

Run:  python fix_table1.py <paper dir>
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


# -------------------------------------------------------- 1 the column
rep("make_tables.py",
    r'''        r"\begin{tabular}{llrrr}",
        r"\toprule",
        r"evaluator & corpus & $n$ & median $\Delta_{\mathrm{token}}$ & $r$ \\",''',
    r'''        r"\begin{tabular}{llrrrr}",
        r"\toprule",
        # The block median goes in beside the token one.  The caption
        # compares the two and printed only one of them, which sent a
        # reader to Table 3 and fourteen pages away to divide.
        r"evaluator & corpus & $n$ & median $\Delta_{\mathrm{token}}$ & "
        r"median $\Delta_{\mathrm{block}}$ & $r$ \\",''',
    "1a: the header gains a column")

rep("make_tables.py",
    r'''            lines.append(f"{name} & {corpus} & {len(tall)} & "
                         f"{t_med:.4f} & {rcol} \\\\")''',
    r'''            lines.append(f"{name} & {corpus} & {len(tall)} & "
                         f"{t_med:.4f} & {b_med:.4f} & {rcol} \\\\")''',
    "1b: the row gains the block median already computed above it")

# -------------------------------------------------------- 2 the selftest
rep("make_tables_selftest.py",
    r'''            assert len(cells) == 5, f"expected 5 columns, got {len(cells)}: {l}"
            assert cells[-2] != "--", f"token median missing: {l}"
            assert cells[-1] != "--", f"token effect size missing: {l}"''',
    r'''            assert len(cells) == 6, f"expected 6 columns, got {len(cells)}: {l}"
            assert cells[-3] != "--", f"token median missing: {l}"
            assert cells[-2] != "--", f"block median missing: {l}"
            assert cells[-1] != "--", f"token effect size missing: {l}"''',
    "2a: six columns, and the new one is not allowed to be empty")

rep("make_tables_selftest.py",
    r'''        tmed = [float([c.strip() for c in l.split("&")][-2]) for l in body]''',
    r'''        tmed = [float([c.strip() for c in l.split("&")][-3]) for l in body]''',
    "2b: the token median moved one column left of the end")

rep("make_tables_selftest.py",
    r'''    print("  tab_token.tex written, 5 columns, no missing cells")''',
    r'''    print("  tab_token.tex written, 6 columns, no missing cells")''',
    "2c: and the line that reports it")

# -------------------------------------------------------- 3 the cross-check
CHECK = '''def _numtext(cell):
    """A printed number, comparable across tables that delimit it
    differently: one prints 0.3182 and the other $+0.3182$."""
    return re.sub(r"[$+\\s]", "", cell)


def check_token_block_agree(tables_dir):
    """Table 1's block column against Table 3's, cell by cell.

    The two come from different measurement files -- tab_token from the
    pll records, tab_blkcells from the blkord ones -- and the prose has
    been asserting that they agree on the \\\\texttt{gpt2} cells without
    anything checking it.  Now that both are printed, they can be read
    against each other, which is the only reason it is safe to delete the
    sentence that used to point one at the other.

    Corpus order is already enforced across generated tables; this is the
    value check that goes with it.
    """
    tok = os.path.join(tables_dir, "tab_token.tex")
    blk = os.path.join(tables_dir, "tab_blkcells.tex")
    if not (os.path.isfile(tok) and os.path.isfile(blk)):
        return

    def rows(path, model_col, corpus_col, value_col, want_model=None):
        out = []
        for line in open(path, encoding="utf-8"):
            if not line.rstrip().endswith(r"\\\\") or "evaluator" in line:
                continue
            c = [x.strip() for x in line.split("&")]
            if len(c) <= max(model_col, corpus_col, value_col):
                continue
            model = c[model_col].split("(")[0].strip()
            if want_model and want_model not in model and model:
                continue
            out.append((model, c[corpus_col], c[value_col]))
        return out

    # tab_token: evaluator | corpus | n | Dtok | Dblk | r   (one evaluator,
    # whose name is printed on its first row only)
    t = [(c, v) for _, c, v in rows(tok, 0, 1, 4)]
    # tab_blkcells: evaluator | corpus | median Dblock | r | p
    b = [(c, v) for m, c, v in rows(blk, 0, 1, 2) if m.startswith("gpt2")
         and m == "gpt2"]
    if not t or not b:
        return
    if len(t) != len(b):
        fail("tokenblock",
             "Table 1 has %d rows and Table 3 has %d \\\\texttt{gpt2} rows; "
             "they are meant to be the same cells" % (len(t), len(b)))
        return
    for (ct, vt), (cb, vb) in zip(t, b):
        if ct != cb:
            fail("tokenblock",
                 "Table 1 and Table 3 disagree on corpus order: %s vs %s"
                 % (ct, cb))
        elif _numtext(vt) != _numtext(vb):
            fail("tokenblock",
                 "median $\\\\Delta_{block}$ for %s is %s in Table 1 and %s in "
                 "Table 3.  The two are computed from different measurement "
                 "files, and Section 2.1 reads the ratio as though they were "
                 "the same number." % (ct, vt, vb))


def check_corpus_order(tables_dir):'''

rep("check_paper.py",
    "def check_corpus_order(tables_dir):",
    CHECK,
    "3a: the two tables are compared, not assumed to agree",
    marker="def check_token_block_agree")

rep("check_paper.py",
    "    check_corpus_order(args.tables)",
    "    check_corpus_order(args.tables)\n"
    "    check_token_block_agree(args.tables)",
    "3b: invoked",
    marker="\n    check_token_block_agree(args.tables)")

# -------------------------------------------------------- 4 the prose
rep("main.tex",
    r"""factor of \SigTokRatioMin--\SigTokRatioMax; the denominators are the
\texttt{gpt2} rows of Table~\ref{tab:blkcells}, in the same corpus order.""",
    r"""factor of \SigTokRatioMin--\SigTokRatioMax, which Table~\ref{tab:token}
prints both sides of.""",
    "4a: the ratio is divisible in the table that reports it")

rep("main.tex",
    r"""\caption{Token reversal, the alternative this section sets aside, on the same
texts as every other measurement here: the median of
$\Dtok$ and the rank-biserial effect size $r$ of Eq.~\eqref{eq:rb}.""",
    r"""\caption{The two reversals side by side on the same texts, which is the
comparison this section makes: the medians of $\Dtok$ and $\Dblock$, and
the rank-biserial effect size $r$ of Eq.~\eqref{eq:rb} on the token
reading.""",
    "4b: the caption describes a table that now carries both quantities")


def _budget_shapes():
    try:
        src = io.open("check_paper.py", encoding="utf-8").read()
        m = re.search(r"ELLIPSIS_SHAPES = \{.*?\n\}", src, re.S)
        ns = {}
        exec(m.group(0), ns)
        return ns["ELLIPSIS_SHAPES"]
    except Exception as exc:
        print(f"  (no shape self-scan: {exc})")
        return {}


shaped = []
for _name, (_pat, _budget) in sorted(_budget_shapes().items()):
    for _lab, _b in WROTE:
        if not _lab.startswith("4"):
            continue
        for _m in re.finditer(_pat, re.sub(r"\s+", " ", _b)):
            shaped.append((_name, _lab, _m.group(0)))
if shaped:
    print("\n  !! replacement text uses shapes the build budgets:")
    for _name, _lab, _hit in shaped:
        print("     %-34s %-30s %r" % (_name, _lab[:28], _hit))
print(f"done: {N} edits")
