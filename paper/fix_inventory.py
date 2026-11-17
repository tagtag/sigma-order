r"""Every model the prose names is a model the inventory lists.

\texttt{bert-large} was named once in Section 3.2 and had no row in the
Section 3.1 table, because its parameter count was retired with the
pseudo-log-likelihood comparison and the name was not.  Reading forward,
the sentence is sound; the defect is a disagreement with a table seventy
lines back, and the clause attached to it ("which appears nowhere else")
told the reader not to go looking.

That one is a cross-reference, which is the kind of thing a build does
better than a reader.  The evaluator table is the paper's inventory: a
model named in the prose and missing from it is either a model the paper
forgot to list, or a name left behind by a removal that was already
decided.  Both have happened here, and the second is the one that leaves
no trace anywhere else.

Matching is by containment against the table's own spellings, so the short
forms the prose uses --- \texttt{bert-base} for \texttt{bert-base-uncased},
\texttt{LLaDA} for \texttt{GSAI-ML/LLaDA-8B-Base} --- resolve without a
second list to maintain.

Run:  python fix_inventory.py <paper dir>
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


CHECK = '''# \\texttt{} spans that are not model names.  The author block's address is
# the only one today; a new entry here is a decision, like every other
# allow-list in this file.
TEXTTT_NOT_A_MODEL = {
    "tag@granular.com",
}


def check_model_inventory(src):
    """Every model the prose names has a row in the evaluator table.

    The Section 3.1 table is the paper's inventory of evaluators.
    \\\\texttt{bert-large} sat in Section 3.2 with no row in it: its
    parameter macro had been retired with the pseudo-log-likelihood
    comparison and the name had not, so the prose named a model the paper
    did not otherwise admit to using.  Nothing else in the build could
    notice, because a retired macro is retired correctly and a word in
    prose is just a word.

    Names are matched by containment against the table's own spellings, so
    \\\\texttt{bert-base} resolves to \\\\texttt{bert-base-uncased} and
    \\\\texttt{LLaDA} to \\\\texttt{GSAI-ML/LLaDA-8B-Base} without a second
    list of aliases to keep in step.
    """
    tab = re.search(r"model & parameters & direction & role.*?"
                    r"\\\\end\\{tabular\\}", src, re.S)
    if not tab:
        fail("inventory", "the evaluator table of Section 3.1 was not "
             "found; check_model_inventory keys on its header row")
        return
    listed = re.findall(r"\\\\texttt\\{([^{}]*)\\}", tab.group(0))
    if not listed:
        fail("inventory", "the evaluator table names no models")
        return
    body = src[:tab.start()] + src[tab.end():]
    for name in sorted(set(re.findall(r"\\\\texttt\\{([^{}]*)\\}", body))):
        if name.startswith("\\\\") or name in TEXTTT_NOT_A_MODEL:
            continue
        if not any(name.lower() in row.lower() for row in listed):
            fail("inventory",
                 "\\\\texttt{%s} is named in the prose and has no row in the "
                 "evaluator table of Section 3.1 --- either it belongs in "
                 "the table, or it is a name left behind by a removal "
                 "(check the RETIRED list in make_tables.py)" % name)


def check_corpus_order(tables_dir):'''

rep("check_paper.py",
    "def check_corpus_order(tables_dir):",
    CHECK,
    "1: the check",
    marker="def check_model_inventory")

rep("check_paper.py",
    "    check_double_superscript(args.tables)",
    "    check_double_superscript(args.tables)\n"
    "    check_model_inventory(src)",
    "2: invoked",
    marker="\n    check_model_inventory(src)")

SELFTEST = '''

def check_model_inventory_rule():
    """A model named in the prose with no row in the evaluator table."""
    import check_paper as C
    table = (r"\\begin{tabular}{llll}"
             r"model & parameters & direction & role \\\\"
             r"\\texttt{gpt2} & 124M & autoregressive & x \\\\"
             r"\\texttt{bert-base-uncased} & 110M & masked & y \\\\"
             r"\\texttt{GSAI-ML/LLaDA-8B-Base} & 8B & masked & z \\\\"
             r"\\end{tabular}")
    for prose, want in (
            (r"we scored with \\texttt{bert-base} and \\texttt{LLaDA}", False),
            (r"\\texttt{gpt2} is the published evaluator", False),
            (r"we also ran \\texttt{bert-large} and withdrew it", True),
            (r"write to \\texttt{tag@granular.com}", False)):
        del C.FAIL[:]
        C.check_model_inventory(table + " " + prose)
        assert bool(C.FAIL) is want, (prose, [m for _, m in C.FAIL])
    del C.FAIL[:]
    C.check_model_inventory("no table here")
    assert C.FAIL, "a missing table should be reported, not passed"
    del C.FAIL[:]
    del C.WARN[:]
    print("  catch: a model named in prose and absent from the inventory")


check_model_inventory_rule()


check_double_superscript_rule()'''

rep("check_paper_selftest.py",
    "\n\ncheck_double_superscript_rule()",
    SELFTEST,
    "3: its selftest",
    marker="def check_model_inventory_rule")

print(f"done: {N} edits")
