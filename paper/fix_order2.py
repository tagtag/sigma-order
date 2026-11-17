r"""The corpus order check fired on its first run, and it was right.

    tab_fbbetween.tex names corpora out of the canonical order:
      Fable5 GPT54 GPT56 Gemini31 Opus46 (canonical: Opus46 GPT54 GPT56
      Gemini31 Fable5)

Cause.  The masked runs key their cells by meta.corpus, which carries the
"fixed_text_" prefix; CORPUS_ORDER lists the bare names.  order_c() tests
membership on the full string, finds none of them, and drops every masked
corpus into its alphabetical tail -- so the masked tables have been ordered
F, GPT54, GPT56, Gemini31, O while every autoregressive table is ordered
O, GPT54, GPT56, Gemini31, F.  The tables print the stripped name, so
nothing on the page said which order it was in.

This is the defect the check was built for and it was already in the paper:
Table 7 and Table 9 do not share a row order with Table 1 and Table 3.  The
numbers are unaffected; the rows move.

Fix at the cause: order_c() looks up the bare name, so one ordering governs
both halves of the paper.  The display is unchanged -- the prefix was
already stripped when printing.

Also, \CorpusOrder was generated and quoted by no prose, which the orphan
check reports and should: it is machine-only, not a number for a reader,
and RETIRED would be the wrong word for it.  It becomes a plain file beside
the tables instead, which is what it always was.

Run:  python fix_order2.py <paper dir>
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


# ===================================== 1: one ordering for both halves
rep("make_tables.py",
    r"""def order_c(names):
    return [c for c in CORPUS_ORDER if c in names] + \
           sorted(n for n in names if n not in CORPUS_ORDER)""",
    r"""def corpus_base(name):
    """ + '"""' + r"""The bare corpus name.

    The masked runs key cells by meta.corpus, which carries a
    "fixed_text_" prefix, and CORPUS_ORDER lists the bare names.  Testing
    membership on the full string put every masked corpus in order_c's
    alphabetical tail, so the masked tables ran F, GPT54, GPT56, Gemini31,
    O while every autoregressive table ran O, GPT54, GPT56, Gemini31, F --
    invisibly, because the tables print the stripped name either way.
    """ + '"""' + r"""
    return name[len("fixed_text_"):] if name.startswith("fixed_text_") \
        else name


def order_c(names):
    known = sorted((n for n in names if corpus_base(n) in CORPUS_ORDER),
                   key=lambda n: CORPUS_ORDER.index(corpus_base(n)))
    return known + sorted(n for n in names
                          if corpus_base(n) not in CORPUS_ORDER)""",
    "1: order_c looks up the bare name, so one order governs both halves")

# ===================================== 2: the order is a file, not a macro
rep("make_tables.py",
    r"""    # The corpus axis, published so check_corpus_order can compare the
    # table bodies against it.  Taken here because these are the corpora of
    # the autoregressive ladder, which is the order Section 2.1 asserts
    # Table 1 and Table 3 share.  No generated number carries an ordering.
    mac("CorpusOrder", " ".join(corpora))""",
    r"""    # The corpus axis, published so check_corpus_order can compare the
    # table bodies against it.  A file and not a macro: it is machine-only,
    # no prose quotes it, and a generated macro with no reader is exactly
    # what the orphan check exists to report.
    if outdir:
        open(os.path.join(outdir, "corpus_order.txt"), "w").write(
            " ".join(corpus_base(c) for c in corpora) + "\n")""",
    "2: machine-only, so not a macro")

# ===================================== 3: the check reads the file
rep("check_paper.py",
    r"""    mpath = os.path.join(tables_dir, "macros.tex")
    if not os.path.isfile(mpath):
        return
    order = newcommands(open(mpath, encoding="utf-8").read()).get(
        "CorpusOrder")
    if not order or "TODO" in order:
        return
    canon = order.split()""",
    r"""    opath = os.path.join(tables_dir, "corpus_order.txt")
    if not os.path.isfile(opath):
        return
    canon = open(opath, encoding="utf-8").read().split()
    if not canon:
        return""",
    "3: the check reads the file")

rep("check_paper.py",
    r"""        if os.path.basename(p) == "macros.tex":
            continue""",
    r"""        if os.path.basename(p) == "macros.tex":
            continue
        if os.path.basename(p) == "corpus_order.txt":
            continue""",
    "3b: and does not check itself",
    marker='"corpus_order.txt":\n            continue')

# ===================================== 4: the selftest follows the cause
rep("check_paper_selftest.py",
    r"""        with open(os.path.join(d, "macros.tex"), "w") as fh:
            fh.write("\\newcommand{\\CorpusOrder}{Opus46 GPT54 GPT56}\n")""",
    r"""        with open(os.path.join(d, "corpus_order.txt"), "w") as fh:
            fh.write("Opus46 GPT54 GPT56\n")""",
    "4: the selftest writes the file")

rep("make_tables_selftest.py",
    "\ncheck_contrast_cells()\n",
    "\n" +
    r"""def check_corpus_prefix():
    """ + '"""' + r"""One corpus ordering, whichever name the run keys cells by.

    The masked runs carry a "fixed_text_" prefix and the autoregressive
    ones do not; membership was tested on the full string, so the two
    halves of the paper were ordered differently and no page showed it.
    """ + '"""' + r"""
    import make_tables as M
    bare = ["Opus46", "GPT54", "GPT56", "Gemini31", "Fable5"]
    assert M.order_c(set(bare)) == bare, M.order_c(set(bare))
    pre = {"fixed_text_" + c for c in bare}
    got = [M.corpus_base(c) for c in M.order_c(pre)]
    assert got == bare, got
    mixed = M.order_c(set(bare[:2]) | {"fixed_text_" + c for c in bare[2:]})
    assert [M.corpus_base(c) for c in mixed] == bare, mixed
    print("  corpus order: one axis, prefixed or not")


check_corpus_prefix()
check_contrast_cells()
""",
    "5: the selftest pins the cause, not only the symptom",
    marker="def check_corpus_prefix")

print(f"done: {N} edits")
