r"""The eleven orphans fix_cells.py created.

ContrastNRejecting{t} / ContrastNCellsOf{t} were emitted for all five rungs
and quoted for two, and ContrastDeltaMed{t} was emitted for all five and
quoted for none -- the table prints that column, so the macros were never
needed.  Either is the same error the orphan check exists to catch: a
generated number with no reader.

The breakdown is one macro instead of ten.  It spells out every rung, so
the evaluator dimension reaches the page in full rather than at the two
ends, which was the point of the finding; and it has exactly one reader.

Run AFTER fix_cells.py:  python fix_cells2.py <paper dir>
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


# ================================================ 1: ten macros become one
rep("make_tables.py",
    r"""    for model in models:
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
            mac(f"ContrastDeltaMed{t}", f"{float(np.median(sw)):+.4f}")""",
    r"""    by_eval = []
    for model in models:
        own = [c for c in cells if c[0] == model]
        if not own:
            continue
        by_eval.append(
            "\\texttt{%s}~%d/%d" % (model.split("/")[-1].replace("_", "-"),
                                    sum(1 for c in own if c[4] < bon),
                                    len(own)))
    if by_eval:
        # One macro with one reader, spelling out every rung.  Emitting a
        # pair per evaluator and quoting the two ends left nine generated
        # numbers nothing read, and still showed the ladder at its ends.
        mac("ContrastRejectByEval", ", ".join(by_eval))""",
    "1: the breakdown is one macro, every rung, one reader",
    marker="ContrastRejectByEval")

# ================================================ 2: the registration follows
rep("make_tables.py",
    r"""                "ContrastNRejectingGPTtwo", "ContrastNCellsOfGPTtwo",
                "ContrastNRejectingGPTtwoMedium",
                "ContrastNCellsOfGPTtwoMedium",
                "ContrastNRejectingGPTtwoLarge",
                "ContrastNCellsOfGPTtwoLarge",
                "ContrastNRejectingGPTtwoXL", "ContrastNCellsOfGPTtwoXL",
                "ContrastNRejectingQwen", "ContrastNCellsOfQwen",
                "ContrastDeltaMedGPTtwo", "ContrastDeltaMedQwen",""",
    r"""                "ContrastRejectByEval",""",
    "2: registered as one name")

# ================================================ 3: the sentence
rep("sec_decomp.tex",
    r"""The cells that clear the threshold are not
stacked on one rung of the ladder --- \ContrastNRejectingGPTtwo\ of
\ContrastNCellsOfGPTtwo\ at the bottom and \ContrastNRejectingQwen\ of
\ContrastNCellsOfQwen\ at the top --- and
Table~\ref{tab:blkcells} prints every cell, since a count over a ladder
says nothing about where on the ladder it falls.""",
    r"""The cells that clear the threshold are not
stacked on one rung of the ladder --- \ContrastRejectByEval\ --- and
Table~\ref{tab:blkcells} prints every cell, since a count over a ladder
says nothing about where on the ladder it falls.""",
    "3: the sentence reads the one macro")

# ================================================ 4: the selftest follows
rep("make_tables_selftest.py",
    r"""    assert g["ContrastNCellsOfGPTtwo"] == "5", g.get("ContrastNCellsOfGPTtwo")
    assert g["ContrastNCellsOfQwen"] == "5", g.get("ContrastNCellsOfQwen")
    assert g["ContrastNRejectingGPTtwo"] == "5", \
        g.get("ContrastNRejectingGPTtwo")""",
    r"""    by = g.get("ContrastRejectByEval", "")
    assert by.count("/") == 5, by          # one entry per rung
    assert by.count("5/5") == 5, by        # this fixture separates in all
    assert "gpt2-medium" in by, by         # including the middle rungs""",
    "4: the selftest reads the one macro, and checks every rung is in it")

print(f"done: {N} edits")
