r"""The corpus axis gets the check the evaluator axis already has.

Section 2.1 now says the denominators of its factor are "the \texttt{gpt2}
rows of Table~\ref{tab:blkcells}, in the same corpus order" as Table 1.
That is a claim about STRUCTURE, and structure appears in none of the
generated numbers: both tables can stay individually correct while their
orders diverge, and the only thing that breaks is one sentence, silently.
It is the between-set defect again -- a dimension present in the data and
checked by nothing.

The check is worth more than the sentence it protects.  Table 1, Table 3,
Table 5's column headers, Table 8 and Figure 1's x axis all assume one
corpus order; any pair diverging breaks several readings at once.  One rule
covers them: every generated table that names corpora names them in the
canonical order.

Compared on the OUTPUT, not the input: an ordering agreed upstream and
disturbed by a renderer would pass an input-side check.  make_tables emits
the canonical order as a macro and check_paper reads each table body back.
Tables carry corpora as rows (tab_blkcells, tab_fbbetween) or as columns
(tab_sweep), so the check tests runs rather than a single sequence: in a
row table each evaluator's block is one run, in a column table the header
is.

Two hardenings for the percentile rule, decided rather than left to chance:

  * the plural.  "the 10th and 90th percentiles" is a legitimate form the
    paper may yet need; "its percentiles" is not.  The ordinal requirement
    now applies to both numbers, so the plural is permitted exactly where
    the singular is, instead of passing or failing by accident of word
    boundary.

  * the scan.  A bibliography entry whose title contains "percentile", or
    a verbatim block, is not the paper's own prose.  Neither is in the
    source today; both are excluded now rather than after a build fails on
    a reference someone added.

And the note gains a positive referent, so a new occurrence can be judged
by asking what it is rather than by matching a string.

The float WARN is left as it is, with its reason recorded beside the float:
the distance grew because a missing reference was added, which the metric
scores as a regression.

Run:  python fix_order.py <paper dir>
"""
import io
import os
import sys

os.chdir(sys.argv[1])
N = 0

CHECK = '''def check_corpus_order(tables_dir):
    """Every generated table names corpora in the canonical order.

    Section 2.1 asserts that Table 1 and Table 3 share it, and no number
    carries an ordering, so nothing else would notice a divergence: both
    tables would stay correct and one sentence would quietly stop being
    true.  The evaluator axis has had this check for longer; this is its
    twin.

    Read off the table bodies rather than the inputs -- an order agreed
    upstream and disturbed by a renderer passes an input-side check.
    Corpora appear as rows in some tables and as columns in others, so
    what is tested is each RUN: a sequence of corpus names ends when one
    repeats, and every run must agree with the canonical order restricted
    to the names it contains.
    """
    mpath = os.path.join(tables_dir, "macros.tex")
    if not os.path.isfile(mpath):
        return
    order = newcommands(open(mpath, encoding="utf-8").read()).get(
        "CorpusOrder")
    if not order or "TODO" in order:
        return
    canon = order.split()
    rank = {c: i for i, c in enumerate(canon)}
    pat = re.compile("|".join(re.escape(c) for c in canon))
    for p in sorted(glob.glob(os.path.join(tables_dir, "*.tex"))):
        if os.path.basename(p) == "macros.tex":
            continue
        seen, runs, cur = set(), [], []
        for m in pat.finditer(open(p, encoding="utf-8").read()):
            c = m.group(0)
            if c in seen:
                runs.append(cur)
                seen, cur = set(), []
            seen.add(c)
            cur.append(c)
        runs.append(cur)
        for run in runs:
            if len(run) < 2:
                continue
            if [rank[c] for c in run] != sorted(rank[c] for c in run):
                fail("order",
                     os.path.basename(p) + " names corpora out of the "
                     "canonical order: " + " ".join(run) + " (canonical: "
                     + " ".join(canon) + ")")
                break


def check_quantities(src, tables_dir):'''

SELFTEST = '''check_percentile_rule()


def check_corpus_order_rule():
    """A table whose corpora are permuted must be caught."""
    import check_paper as C
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "macros.tex"), "w") as fh:
            fh.write("\\\\newcommand{\\\\CorpusOrder}{Opus46 GPT54 GPT56}\\n")

        def table(seq):
            with open(os.path.join(d, "tab_x.tex"), "w") as fh:
                fh.write("\\n".join(r + " & 1 \\\\\\\\" for r in seq) + "\\n")

        table(["Opus46", "GPT54", "GPT56"])
        C.FAIL[:] = []
        C.check_corpus_order(d)
        assert not C.FAIL, [m for _, m in C.FAIL]

        # two evaluator blocks, each in order: still fine
        table(["Opus46", "GPT54", "GPT56", "Opus46", "GPT54", "GPT56"])
        C.FAIL[:] = []
        C.check_corpus_order(d)
        assert not C.FAIL, [m for _, m in C.FAIL]

        # one block permuted
        table(["Opus46", "GPT56", "GPT54"])
        C.FAIL[:] = []
        C.check_corpus_order(d)
        assert any("out of the canonical order" in m for _, m in C.FAIL), \\
            [m for _, m in C.FAIL]
        C.FAIL[:] = []
        del C.WARN[:]
    print("  catch: a generated table that permutes the corpus axis")


check_corpus_order_rule()
'''


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


# ===================================== 1: the canonical order is published
rep("make_tables.py",
    r"""    mac("ContrastNCells", str(len(ps)))""",
    r"""    # The corpus axis, published so check_corpus_order can compare the
    # table bodies against it.  Taken here because these are the corpora of
    # the autoregressive ladder, which is the order Section 2.1 asserts
    # Table 1 and Table 3 share.  No generated number carries an ordering.
    mac("CorpusOrder", " ".join(corpora))
    mac("ContrastNCells", str(len(ps)))""",
    "1: the canonical corpus order becomes a macro",
    marker='mac("CorpusOrder"')

rep("make_tables.py",
    r"""                "FbBetweenNOpposite", "FbBetweenNCompared",""",
    r"""                "FbBetweenNOpposite", "FbBetweenNCompared",
                "CorpusOrder",""",
    "2: registered",
    marker='"CorpusOrder",')

# ===================================== 3: the check and its invocation
rep("check_paper.py",
    "def check_quantities(src, tables_dir):",
    CHECK,
    "3: the corpus axis is compared across table bodies",
    marker="def check_corpus_order")

rep("check_paper.py",
    "    check_percentile_sense(src)",
    "    check_percentile_sense(src)\n"
    "    check_corpus_order(args.tables)",
    "4: invoked",
    marker="check_corpus_order(args.tables)")

# ===================================== 5: the percentile hardenings
rep("check_paper.py",
    r"""    flat = re.sub(r"\s+", " ", src)
    for m in re.finditer(r"percentile", flat):""",
    r"""    # Not the paper's own prose: a reference title, a verbatim block.
    # Neither is in the source today; excluded before one arrives.
    body = re.sub(r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}",
                  " ", src, flags=re.S)
    body = re.sub(r"\\begin\{verbatim\}.*?\\end\{verbatim\}", " ", body,
                  flags=re.S)
    body = re.sub(r"\\verb\|[^|]*\|", " ", body)
    flat = re.sub(r"\s+", " ", body)
    # The plural is permitted exactly where the singular is: "the 10th and
    # 90th percentiles" is a form this paper may need, "its percentiles" is
    # not, and which way the plural fell was an accident of word boundary.
    for m in re.finditer(r"percentiles?", flat):""",
    "5: the plural is decided, and the scan excludes what is not our prose",
    marker="The plural is permitted exactly where the singular is")

rep("glossary.txt",
    'sense and not the string',
    'sense and not the string.  Stated positively, the permitted referent '
    'is a quantile of a distribution of VALUES -- the tail statistic reads '
    'a fraction of causal texts above a quantile of the non-causal group\'s '
    'own z distribution -- so a new occurrence is judged by asking whether '
    'it names one of those, not by matching the spelling',
    "6: the note names the referent, not only what it is not",
    marker="Stated positively, the permitted referent")

# ===================================== 7: the float distance, with its reason
rep("sec_decomp.tex",
    r"""\begin{table}[tbp]
\centering
{\small\input{tables/tab_blkcells}}""",
    r"""% check_paper float distance: three call sites spanning 13 pages
% (Sections 2.1, 4.2, 5.3).  Printed next to the densest of them, 5.3,
% where the table is read row by row; the first-citation distance grew
% when 2.1's missing reference was ADDED, which this metric scores as a
% regression.  Accepted as a WARN rather than moved.
\begin{table}[tbp]
\centering
{\small\input{tables/tab_blkcells}}""",
    "7: the accepted distance carries its reason where the next reader looks",
    marker="check_paper float distance")


# ===================================== 8: its selftest
rep("check_paper_selftest.py",
    "check_percentile_rule()\n",
    SELFTEST,
    "8: a permuted corpus axis must be caught",
    marker="check_corpus_order_rule")

print(f"done: {N} edits")
