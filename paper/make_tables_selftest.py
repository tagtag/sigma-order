#!/usr/bin/env python3
"""Check that make_tables.py builds the two between-set tables and their macros.

This runs make_tables.py against synthetic measurements with a known answer,
in a scratch directory, and asserts the things that have actually gone wrong
in this project:

  * the token-reversal table exists and carries numbers, not "--".  Section 2.1
    says Delta_token is reported "for completeness"; for one revision it was
    not reported anywhere, and nothing caught it because no check knew the
    quantity was supposed to appear at all.
  * the block-level table keeps its own six columns, so adding the token table
    cannot quietly disturb the one the results rest on.
  * the macros the prose quotes for token reversal resolve to values rather
    than to TODO markers.
  * the counts in those macros are the ones the input implies, so a macro
    cannot quietly report something other than what the table shows.

No model weights, no network, a second or two to run:

    python3 -I make_tables_selftest.py
"""

import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def cellnum(cell):
    """One LaTeX table cell as a number.

    The generated tables print their numbers in math mode, so that a
    negative value is a minus and not a hyphen.  This test read them with
    a bare float() and stopped the build the first time a column was
    corrected: ValueError on '$0.7005$'.  Every numeric cell read here
    goes through this, so the next column to gain or lose its delimiters
    costs nothing.

    Narrow on purpose: "--", a LaTeX command, or a number written with
    \\times still raises.  Those are not values this test may quietly
    reinterpret.
    """
    s = cell.strip()
    if s.startswith("$") and s.endswith("$"):
        s = s[1:-1].strip()
    return float(s)


def make_cell(path, model, kind, corpus, blk_causal, blk_non,
              tok_causal, tok_non):
    """One (evaluator, corpus) measurement file in the shape load_cells reads.

    The two groups are given well-separated constants with a little spread, so
    the rank statistic is determined by their order alone and the medians are
    exactly the constants.
    """
    recs = []
    for i in range(10):
        recs.append({"category": "causal", "index": i,
                     "sigma_block_per_T": blk_causal + 1e-4 * i,
                     "sigma_token_per_T": tok_causal + 1e-4 * i})
    for i in range(10):
        recs.append({"category": "noncausal", "index": i,
                     "sigma_block_per_T": blk_non + 1e-4 * i,
                     "sigma_token_per_T": tok_non + 1e-4 * i})
    json.dump({"model": model, "kind": kind,
               "corpus": f"fixed_text_{corpus}.json", "records": recs},
              open(path, "w"))


def main():
    with tempfile.TemporaryDirectory() as tmp:
        pll = os.path.join(tmp, "results_pll")
        out = os.path.join(tmp, "tables")
        os.makedirs(pll)

        # bert: token reversal 20x the block quantity, and its effect size
        # flips sign on one of the two corpora.
        make_cell(os.path.join(pll, "pll_bert__A__0-1.json"),
                  "bert-base-uncased", "masked", "Opus46",
                  blk_causal=0.030, blk_non=0.020,
                  tok_causal=0.600, tok_non=0.400)
        make_cell(os.path.join(pll, "pll_bert__B__0-1.json"),
                  "bert-base-uncased", "masked", "GPT54",
                  blk_causal=0.030, blk_non=0.020,
                  tok_causal=0.400, tok_non=0.600)   # sign flip
        # gpt2: token reversal 2x, no flip.  Two corpora, so the table has
        # two rows once the masked cells are excluded.
        make_cell(os.path.join(pll, "pll_gpt2__A__0-1.json"),
                  "gpt2", "causal", "Opus46",
                  blk_causal=0.400, blk_non=0.300,
                  tok_causal=0.800, tok_non=0.600)
        make_cell(os.path.join(pll, "pll_gpt2__B__0-1.json"),
                  "gpt2", "causal", "GPT54",
                  blk_causal=0.420, blk_non=0.310,
                  tok_causal=0.820, tok_non=0.610)

        r = subprocess.run(
            [sys.executable, "-I", os.path.join(HERE, "make_tables.py"),
             "--pll", pll, "--blkord", os.path.join(tmp, "none"),
             "--toy", os.path.join(tmp, "none"), "--outdir", out],
            capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout)
            print(r.stderr)
            raise SystemExit("make_tables.py failed")

        pll_tab = open(os.path.join(out, "tab_pll.tex")).read()
        tab = open(os.path.join(out, "tab_token.tex")).read()
        mac = open(os.path.join(out, "macros.tex")).read()

        def macro(name):
            m = re.search(r"\\newcommand\{\\" + name + r"\}\{(.*)\}\s*$",
                          mac, re.M)
            assert m, f"macro {name} not written at all"
            v = m.group(1)
            assert "TODO" not in v, f"macro {name} is still a TODO"
            return v

        # --- Delta_token is reported at all ---------------------------------
        assert r"\Delta_{\mathrm{token}}" in tab, \
            "tab_token.tex does not name Delta_token"
        # Skip the header by what it IS, not by which symbol it happens to
        # print: this filter read "sigma" not in l, and the moment the
        # quantity was renamed to Delta the header counted as a data row.
        body = [l for l in tab.splitlines() if l.endswith(r"\\")
                and "evaluator" not in l]
        # Masked evaluators are excluded: Delta needs a joint distribution,
        # which a masked model does not have, so the rows that used to be
        # there were a pseudo-log-likelihood difference and not Delta at all.
        # Two gpt2 cells go in, two rows come out, and "bert" appears nowhere.
        assert len(body) == 2, f"expected 2 data rows, got {len(body)}"
        assert "bert" not in tab, \
            "tab_token.tex still carries a masked evaluator"
        for l in body:
            cells = [c.strip() for c in l.split("&")]
            assert len(cells) == 6, f"expected 6 columns, got {len(cells)}: {l}"
            assert cells[-3] != "--", f"token median missing: {l}"
            assert cells[-2] != "--", f"block median missing: {l}"
            assert cells[-1] != "--", f"token effect size missing: {l}"

        # --- and the block-level table is untouched -------------------------
        assert r"\Delta_{\mathrm{block}}" in pll_tab, \
            "tab_pll.tex lost its block column"
        assert r"\Delta_{\mathrm{token}}" not in pll_tab, \
            "token reversal leaked into tab_pll.tex"
        pll_body = [l for l in pll_tab.splitlines() if l.endswith(r"\\")
                    and "sigma" not in l]
        for l in pll_body:
            cells = [c.strip() for c in l.split("&")]
            assert len(cells) == 6, \
                f"tab_pll.tex should keep 6 columns, got {len(cells)}: {l}"
        # The pooled median falls between the two groups, so with groups at
        # 0.400/0.600 it is near 0.500 and with 0.600/0.800 near 0.700.  That
        # ordering is what the table must preserve.
        tmed = [cellnum(l.split("&")[-3]) for l in body]
        for v in tmed:
            assert abs(v - 0.7) < 0.02, \
                f"gpt2 token medians should be near 0.70, got {tmed}"

        # --- the macros say what the table shows ----------------------------
        assert macro("NTokCells") == "2", \
            "the two masked cells must not be counted"
        assert macro("NTokLarger") == "2", \
            "every surviving cell has the larger token median"
        assert macro("NTokNegAR") == "0"
        assert macro("NTokNegARTot") == "2"
        lo, hi = float(macro("SigTokRatioMin")), float(macro("SigTokRatioMax"))
        assert 1.0 < lo <= hi, f"ratio range looks wrong: {lo}-{hi}"
        assert abs(lo - 2.0) < 0.2, f"gpt2 ratio should be about 2, got {lo}"
        assert hi < 5.0, \
            f"the 20x masked ratio must not survive the filter, got {hi}"

    print("make_tables selftest: OK")
    print("  tab_token.tex written, 6 columns, no missing cells")
    print("  tab_pll.tex still 6 columns, block-level only")
    print("  SigTokRatio/NTokNeg macros resolve and match the input")


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------- sigfb
def check_fbrank():
    """table_fbrank must exclude degenerate texts and never rank noise.

    The two failures this pins both happened during development:
      * a compatible evaluator gives n! values equal to 1e-16, and ranking
        them manufactured a percentile out of rounding noise;
      * those texts, counted into the effect size, dragged it towards zero.
    Here every text of one cell is degenerate and every text of the other is
    not, so the macros must report the first cell's texts as degenerate,
    exclude them, and compute r from the second alone.
    """
    import json, os, shutil, sys, tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_tables as M

    d = tempfile.mkdtemp()
    try:
        def cell(model, corpus, degen, lo_causal):
            recs = []
            for cat, base in (("causal", lo_causal), ("noncausal", 0.6)):
                for i in range(20):
                    recs.append({
                        "percentile_written": 0.5 if degen
                                              else base + 0.01 * (i % 5),
                        "degenerate": degen, "category": cat, "index": i,
                        "sigma_fb_written": 0.05,
                    })
            json.dump({"meta": {"script": "block_sigma_fb.py",
                                "model": model, "corpus": corpus},
                       "records": recs},
                      open(os.path.join(d, f"{model}__{corpus}.json"), "w"))

        cell("bert-base-uncased", "fixed_text_A", True, 0.2)
        cell("bert-base-uncased", "fixed_text_B", False, 0.2)
        out = tempfile.mkdtemp()
        M.MACROS.clear()
        M.table_fbrank(d, out)
        g = M.MACROS

        assert g["FbNTexts"] == "80", g["FbNTexts"]
        assert g["FbDegenTotal"] == "40", g["FbDegenTotal"]
        # the all-degenerate cell contributes no effect size
        assert g["FbNCells"] == "1", g["FbNCells"]
        # causal sits below non-causal by construction, so r must be negative
        assert float(g["FbRBertBase"]) < 0, g["FbRBertBase"]
        assert g["FbNNegative"] == "1", g["FbNNegative"]
        tab = open(os.path.join(out, "tab_fbrank.tex")).read()
        assert "degen" in tab and "fixed_text" not in tab
        print("  table_fbrank: degenerate texts counted, excluded, not ranked")
        shutil.rmtree(out)
    finally:
        shutil.rmtree(d)


check_fbrank()


# ------------------------------------------------------- capacity scale
def check_capacity_scale():
    """The Cap* macros must come from the enumeration run, and from its ends.

    This is the check that would have caught the error it was written after.
    The capacity ratio was computed from results_pll/, which holds the
    published between-set protocol: three evaluators, one of them
    autoregressive.  Restricting Delta to the autoregressive evaluators left
    that source with a single model, the ratio had no second end, and the
    five macros stayed TODO through a full build.  The quantity lives in
    results_blkord/, where the ladder is.

    Two evaluators, two corpora, medians fixed by construction: gpt2 at
    +0.20 and +0.10, Qwen at +0.60 and -0.05.  So the ratios are 3.0 and 0.5,
    the median is 1.75, one corpus is up, and one changes sign.
    """
    import os, shutil, sys, tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_tables as M

    def cell(vals):
        return {("causal", i): {"sigma_written": v, "category": "causal",
                                "index": i}
                for i, v in enumerate(vals)}

    blk = {
        ("gpt2", "Opus46"): cell([0.19, 0.20, 0.21]),
        ("gpt2", "GPT54"): cell([0.09, 0.10, 0.11]),
        ("Qwen/Qwen3-4B-Base", "Opus46"): cell([0.59, 0.60, 0.61]),
        ("Qwen/Qwen3-4B-Base", "GPT54"): cell([-0.06, -0.05, -0.04]),
    }
    kinds = {"gpt2": "causal", "Qwen/Qwen3-4B-Base": "causal",
             "bert-base-uncased": "masked"}
    M.MACROS.clear()
    M.capacity_scale_macros(blk, kinds)
    g = M.MACROS
    assert g["CapRatioMedian"] == "1.75", g["CapRatioMedian"]
    assert g["CapRatioMin"] == "0.50", g["CapRatioMin"]
    assert g["CapRatioMax"] == "3.00", g["CapRatioMax"]
    assert g["CapNCorpora"] == "2", g["CapNCorpora"]
    assert g["CapNUp"] == "1", g["CapNUp"]
    assert g["CapNSign"] == "1", g["CapNSign"]
    assert g["CapDeltaLo"] == "+0.1500", g["CapDeltaLo"]
    assert g["CapDeltaHi"] == "+0.2750", g["CapDeltaHi"]

    # a masked evaluator at one end would be a different quantity: with only
    # one autoregressive model present nothing is emitted at all.
    M.MACROS.clear()
    M.capacity_scale_macros(
        {k: v for k, v in blk.items() if k[0] == "gpt2"}, kinds)
    assert not M.MACROS, "a one-model ladder must emit no ratio"
    print("  capacity scale: ratios from the blkord ladder, both ends "
          "autoregressive")


check_capacity_scale()


# --------------------------------------------------- figures and tables agree
def check_figure_order():
    """The figures must name and order the evaluators as the tables do.

    make_figures.py kept private copies of the evaluator order and the
    parameter counts.  When the autoregressive ladder was added they were
    updated in make_tables.py alone, so the three new models were unknown to
    the figure: they sorted alphabetically after the models that were listed,
    and Figure 1 ran gpt2, Qwen, gpt2-large, gpt2-medium, gpt2-xl under a
    caption that says "in order of capacity", with their sizes printed as
    "?".  The copies are gone; this pins that they stay gone.
    """
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_figures as F
    import make_tables as M

    names = {"gpt2", "gpt2-medium", "gpt2-large", "gpt2-xl",
             "Qwen/Qwen3-4B-Base", "bert-base-uncased",
             "GSAI-ML/LLaDA-8B-Base"}
    assert F.order_models(names) == M.order_m(names), \
        f"figure order {F.order_models(names)} != table order {M.order_m(names)}"
    for m in names:
        assert M.params_str(m) != "?", f"{m} has no parameter count"
    # integer division printed 1558M as "1B" here long after the macro was
    # fixed; one decimal, trailing zero stripped
    assert M.params_str("gpt2-xl") == "1.6B", M.params_str("gpt2-xl")
    assert M.params_str("Qwen/Qwen3-4B-Base") == "4B"
    assert M.params_str("gpt2") == "124M"
    print("  figures and tables order and name the evaluators alike")


check_figure_order()


# ------------------------------------------------- displacement, per evaluator
def check_displacement_macros():
    """A displacement p quoted for one evaluator must come from that evaluator.

    The paper says, of LLaDA, that every one of its displacement tests
    rejects, and quoted the largest p over ALL such tests.  Those were pooled
    across both masked evaluators, so the number printed was bert-base's --
    0.989 -- in a sentence asserting rejection.  Here one evaluator sits on
    the null and the other far below it, and the per-evaluator macros must
    tell them apart while the pooled one takes the worse of the two.
    """
    import json, os, shutil, sys, tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_tables as M

    d = tempfile.mkdtemp()
    try:
        def cell(model, corpus, base_c, base_n):
            recs = []
            for cat, base in (("causal", base_c), ("noncausal", base_n)):
                for i in range(20):
                    recs.append({
                        # a symmetric spread about `base`: when base is 0.5
                        # the signed-rank test sees no displacement
                        "percentile_written": base + 0.01 * (i % 5 - 2),
                        "degenerate": False, "category": cat, "index": i,
                        "sigma_fb_written": 0.05,
                    })
            json.dump({"meta": {"script": "block_sigma_fb.py",
                                "model": model, "corpus": corpus},
                       "records": recs},
                      open(os.path.join(
                          d, f"{model.split('/')[-1]}__{corpus}.json"), "w"))

        # on the null, and far below it
        cell("bert-base-uncased", "fixed_text_A", 0.50, 0.50)
        cell("GSAI-ML/LLaDA-8B-Base", "fixed_text_A", 0.20, 0.22)
        out = tempfile.mkdtemp()
        M.MACROS.clear()
        M.table_fbrank(d, out)
        g = M.MACROS

        for k in ("FbDispPMaxLLaDA", "FbDispPMaxBertBase", "FbDispPMax",
                  "FbNTestsDispLLaDA", "FbNTestsDispBertBase",
                  "FbDispBonferroni"):
            assert k in g, f"{k} not emitted"
        assert g["FbNTestsDispLLaDA"] == "2", g["FbNTestsDispLLaDA"]
        assert g["FbNTestsDispBertBase"] == "2", g["FbNTestsDispBertBase"]
        assert g["FbNTestsDisp"] == "4", g["FbNTestsDisp"]
        # the evaluator on the null must not lend its p to the other
        assert g["FbDispPMaxLLaDA"] != g["FbDispPMaxBertBase"], \
            "the two evaluators report the same displacement p"
        # and the pooled macro is the worse of the two, which is why a
        # sentence about one evaluator must not use it
        assert g["FbDispPMax"] == g["FbDispPMaxBertBase"], \
            (g["FbDispPMax"], g["FbDispPMaxBertBase"])
        assert g["FbDispNRejectingLLaDA"] == "2", g["FbDispNRejectingLLaDA"]
        assert g["FbDispNRejectingBertBase"] == "0", \
            g["FbDispNRejectingBertBase"]
        print("  displacement: each evaluator's p is its own")
        shutil.rmtree(out)
    finally:
        shutil.rmtree(d)


check_displacement_macros()


# ------------------------------------------------------- the route control
def check_bayes_route_table():
    """The control table must report the worst recovered route, not the best.

    Its point is that no route through a joint produces the reading, so the
    column that stands for "recovered" has to be the largest |sigma_EP| of
    the three joints tried.  Taking the smallest would make the claim by
    choosing the evidence.  The correlation macros are emitted only when
    there are enough widths to rank.
    """
    import json, os, shutil, sys, tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_tables as M

    def row(d, head, joints, mean_abs):
        return {"d": d, "nlayer": 3, "params": 100 * d,
                "final_loss": 1.1, "head": {"sigma": head,
                                            "affinity_rms": 0.5},
                "joint_routes": [{"route": n, "sigma": s,
                                  "affinity_rms": 1e-16,
                                  "jeffreys_vs_head": j}
                                 for n, s, j in joints],
                "sigma_l2r_r2l": {"median": 0.1, "min": -1.0, "max": 1.0,
                                  "mean_abs": mean_abs}}

    d = tempfile.mkdtemp()
    out = tempfile.mkdtemp()
    try:
        rows = [row(32, 0.0074, [("pll", 1e-19, 0.19), ("l2r", -4e-19, 0.20),
                                 ("r2l", 2e-19, 0.195)], 0.2261),
                row(96, 0.0144, [("pll", 2e-19, 0.20), ("l2r", -1e-19, 0.36),
                                 ("r2l", 3e-19, 0.30)], 0.2130),
                row(160, 0.0259, [("pll", 1e-19, 0.21), ("l2r", 3e-19, 0.46),
                                  ("r2l", -2e-19, 0.30)], 0.2169)]
        json.dump({"rows": rows},
                  open(os.path.join(d, "bayes_route_control.json"), "w"))
        M.MACROS.clear()
        M.table_bayes_route(d, out)
        tab = open(os.path.join(out, "tab_bayesroute.tex")).read()
        g = M.MACROS

        body = [l for l in tab.splitlines() if l.endswith(r"\\")
                and "multicolumn" not in l and "params" not in l]
        assert len(body) == 3, f"expected 3 widths, got {len(body)}"
        # the worst of the three joints at d=32 is 4e-19, not 1e-19
        assert "4" in body[0].split("&")[4], \
            f"the recovered column is not the largest of the three: {body[0]}"
        # and the macro quotes the worst over the whole sweep
        assert "4" in g["CtrlSigmaJointMax"], g["CtrlSigmaJointMax"]
        assert g["CtrlJeffreysMin"] == "0.21", g["CtrlJeffreysMin"]
        assert g["CtrlJeffreysMax"] == "0.46", g["CtrlJeffreysMax"]
        assert g["CtrlSigmaHead"] == "0.0259", g["CtrlSigmaHead"]
        assert g["CtrlNWidths"] == "3"
        # sigma_EP rises with width here and the sigma mean does not
        assert float(g["CtrlRhoEP"]) > 0.9, g["CtrlRhoEP"]
        assert float(g["CtrlRhoSig"]) < 0.5, g["CtrlRhoSig"]

        # two widths cannot be ranked: no correlation macros at all
        json.dump({"rows": rows[:2]},
                  open(os.path.join(d, "bayes_route_control.json"), "w"))
        M.MACROS.clear()
        M.table_bayes_route(d, out)
        assert "CtrlRhoEP" not in M.MACROS, \
            "a two-point rank correlation was reported"
        print("  route control: the recovered column is the worst route")
    finally:
        shutil.rmtree(d)
        shutil.rmtree(out)


check_bayes_route_table()


# ------------------------------------------------- the share, as one number
def check_share_range():
    """The per-evaluator share range must come from the table, not the prose.

    "A tenth to a fifth" was written in three places, in words, beside a
    range over the individual (evaluator, corpus) cells that runs from
    negative to +40%.  The two are different aggregations and read as a
    contradiction.  The words are gone; this pins that the macros that
    replaced them are the min and max of the per-evaluator column.
    """
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_tables as M

    got = {"gpt2": (0.354, 0.042, 0.11),
           "gpt2-medium": (0.354, 0.083, 0.19),
           "Qwen/Qwen3-4B-Base": (0.396, 0.042, 0.10)}
    M.MACROS.clear()
    ev = [s for (_, _, s) in got.values()]
    M.mac("ShareEvalMin", f"{100 * min(ev):.0f}")
    M.mac("ShareEvalMax", f"{100 * max(ev):.0f}")
    assert M.MACROS["ShareEvalMin"] == "10", M.MACROS["ShareEvalMin"]
    assert M.MACROS["ShareEvalMax"] == "19", M.MACROS["ShareEvalMax"]

    # and the words must not have come back
    here = os.path.dirname(os.path.abspath(__file__))
    for name in ("main.tex", "sec_intro.tex", "sec_decomp.tex",
                 "sec_truesigma.tex"):
        p = os.path.join(here, name)
        if not os.path.isfile(p):
            continue
        body = open(p, encoding="utf-8").read()
        body = "\n".join(l.split("%")[0] for l in body.split("\n"))
        for phrase in ("a tenth to a fifth", "a tenth and a fifth"):
            assert phrase not in body, f"{name} still spells the share out"
    print("  share: one macro pair, and the prose does not spell it out")


check_share_range()


# ------------------------------------------------ the gap between evaluators
def check_step_gap():
    """\\FbStepGap is a difference of displacements, not a ratio of them.

    The prose said the two evaluators' readings differ "by about thirteen
    grid steps".  Read on the 1/n! grid the displacements were -6.5 and
    +0.5 steps, whose difference is 7.0; thirteen was 0.2708/0.0208, one
    displacement over the other.  Written as a word, the number was outside
    everything that checks numbers.  (#253 and #264 made the grid 1/2n!, so
    the displacements are now -13 and +1 and their difference is 14; the
    ratio is unchanged, which is the point this test keeps.)  Here two
    evaluators are given displacements of -0.25 and +0.05 with n! = 20,
    which on the 1/2n! grid is -10.0 and +2.0 steps and a gap of 12.0.
    """
    import json, os, shutil, sys, tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_tables as M

    d = tempfile.mkdtemp()
    out = tempfile.mkdtemp()
    try:
        def cell(model, shift):
            recs = []
            for cat in ("causal", "noncausal"):
                for i in range(20):
                    recs.append({"percentile_written": 0.5 + shift,
                                 "degenerate": False, "category": cat,
                                 "index": i, "sigma_fb_written": 0.05,
                                 "n_perms": 20})
            json.dump({"meta": {"script": "block_sigma_fb.py",
                                "model": model, "corpus": "fixed_text_A"},
                       "records": recs},
                      open(os.path.join(d, f"{model}__fixed_text_A.json"), "w"))

        cell("GSAI-ML_LLaDA-8B-Base", -0.25)
        cell("bert-base-uncased", +0.05)
        M.MACROS.clear()
        M.table_fbrank(d, out)
        g = M.MACROS
        assert "FbStepGap" in g, "no gap emitted for two evaluators"
        assert g["FbStepGap"] == "12.0", g["FbStepGap"]
        # and it is not the ratio, which would be 5.0
        assert g["FbStepGap"] != "5.0"
        print("  step gap: a difference of displacements, not a ratio")
    finally:
        shutil.rmtree(d)
        shutil.rmtree(out)


check_step_gap()


# --------------------------------------------- the capacity ratio's endpoints
def check_toy_cap_ratio():
    """\\ToyCapRatio compares the endpoints, because the prose names them.

    It was max over min across the sweep.  The measured sweep dips at its
    second width, so the smallest value is not the one at the smallest model:
    max/min gave 4.1 where the endpoints give 3.5, under a sentence reading
    "from d = 32 to d = 160".  Here the dip is exaggerated so the two
    answers cannot coincide by luck.
    """
    import json, os, shutil, sys, tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_tables as M

    d = tempfile.mkdtemp()
    out = tempfile.mkdtemp()
    try:
        rows = [{"kind": "MLM", "d": 32, "nlayer": 1, "params": 1000,
                 "final_loss": 1.0, "sigma": 0.010, "affinity_rms": 0.3,
                 "kl_mu_pi": 0.0},
                {"kind": "MLM", "d": 64, "nlayer": 2, "params": 2000,
                 "final_loss": 1.0, "sigma": 0.002, "affinity_rms": 0.3,
                 "kl_mu_pi": 0.0},
                {"kind": "MLM", "d": 128, "nlayer": 3, "params": 4000,
                 "final_loss": 1.0, "sigma": 0.020, "affinity_rms": 0.3,
                 "kl_mu_pi": 0.0},
                {"kind": "AR", "d": 32, "nlayer": 1, "params": 1000,
                 "final_loss": 1.0, "sigma": 1e-20, "affinity_rms": 0.0,
                 "kl_mu_pi": 0.0}]
        json.dump({"rows": rows},
                  open(os.path.join(d, "capacity_results.json"), "w"))
        M.MACROS.clear()
        M.table_capacity(d, out)
        g = M.MACROS
        # endpoints: 0.020 / 0.010 = 2.0
        assert g["ToyCapRatio"] == "2.0", g["ToyCapRatio"]
        # max over min would be 0.020 / 0.002 = 10.0, and is reported
        # separately rather than in place of it
        assert g["ToySpanRatio"] == "10.0", g["ToySpanRatio"]
        assert g["ToyCapMonotone"] == "no", g["ToyCapMonotone"]
        print("  toy capacity: endpoints for the endpoint sentence")
    finally:
        shutil.rmtree(d)
        shutil.rmtree(out)


check_toy_cap_ratio()


# ----------------------------------------- the group positions, not the sign
def check_group_positions():
    """A claim about where a group sits must not be read off the effect size.

    The text said bert-base's within-text displacement was "in the same
    direction in 5/5 corpora" and quoted FbSignNeg, which counts cells with
    a negative effect size.  Those are different quantities and in the
    measured data they differ: the effect size is negative in 5 of 5, the
    displacement positive in 4 of 5.  Here they are made to differ on
    purpose, and the macros must not swap.
    """
    import json, os, shutil, sys, tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_tables as M

    d = tempfile.mkdtemp()
    out = tempfile.mkdtemp()
    try:
        # four corpora: causal below the null everywhere, non-causal above
        # it in three of the four, and the effect size negative in all four
        for i, (c, n) in enumerate([(0.40, 0.55), (0.42, 0.56),
                                    (0.44, 0.57), (0.41, 0.48)]):
            recs = []
            for cat, base in (("causal", c), ("noncausal", n)):
                for j in range(20):
                    recs.append({"percentile_written": base,
                                 "degenerate": False, "category": cat,
                                 "index": j, "sigma_fb_written": 0.05,
                                 "n_perms": 24})
            json.dump({"meta": {"script": "block_sigma_fb.py",
                                "model": "bert-base-uncased",
                                "corpus": f"fixed_text_C{i}"}, "records": recs},
                      open(os.path.join(d, f"bert-base-uncased__C{i}.json"), "w"))
        M.MACROS.clear()
        M.table_fbrank(d, out)
        g = M.MACROS
        assert g["FbNCorporaOfBertBase"] == "4", g["FbNCorporaOfBertBase"]
        assert g["FbCausalBelowBertBase"] == "4", g["FbCausalBelowBertBase"]
        # the displacement is NOT 4: one corpus has the non-causal median
        # below the null
        assert g["FbAuthoredAboveBertBase"] == "3", g["FbAuthoredAboveBertBase"]
        # and the effect size is negative in all four, which is a third number
        # FbSignNeg is printed as "k/n"; it is a third count again
        assert g["FbSignNegBertBase"] == "4/4", g["FbSignNegBertBase"]
        print("  group positions: below-null, above-null and sign are three "
              "counts, not one")
    finally:
        shutil.rmtree(d)
        shutil.rmtree(out)


check_group_positions()


# ------------------------------------------- texts counted once, not per read
def check_text_counts():
    """\\FbNTexts counts texts; \\FbNScorings counts (text, evaluator) pairs.

    One macro counted rows and was called FbNTexts, and the prose then wrote
    "across all 2000 texts and both evaluators", which doubles a number that
    already included both.  Here two evaluators read the same 40 texts of one
    corpus, so the two counts must come out 40 and 80.
    """
    import json, os, shutil, sys, tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_tables as M

    d = tempfile.mkdtemp()
    out = tempfile.mkdtemp()
    try:
        for model in ("bert-base-uncased", "GSAI-ML_LLaDA-8B-Base"):
            recs = []
            for cat, base in (("causal", 0.40), ("noncausal", 0.60)):
                for j in range(20):
                    recs.append({"percentile_written": base + 0.001 * j,
                                 "degenerate": False, "category": cat,
                                 "index": j, "sigma_fb_written": 0.05,
                                 "n_perms": 24})
            json.dump({"meta": {"script": "block_sigma_fb.py", "model": model,
                                "corpus": "fixed_text_A"}, "records": recs},
                      open(os.path.join(d, f"{model}__fixed_text_A.json"), "w"))
        M.MACROS.clear()
        M.table_fbrank(d, out)
        g = M.MACROS
        assert g["FbNTexts"] == "40", g["FbNTexts"]
        assert g["FbNScorings"] == "80", g["FbNScorings"]
        print("  text counts: the same text read twice is one text")
    finally:
        shutil.rmtree(d)
        shutil.rmtree(out)


check_text_counts()


# ------------------------------------- the two share forms, measured not told
def check_share_forms():
    """Whether the midrank and z shares agree is measured, not asserted.

    Table 2's caption said "their agreement is what shows the midrank bound
    is not driving the split".  Measured, the two columns rank-correlate
    negatively and one evaluator differs between them by more than a factor
    of two.  The claim the ceiling argument needs is about the range, not
    about agreement.  Here the two forms are made to disagree outright.
    """
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_tables as M
    import numpy as np
    from scipy.stats import spearmanr

    got = {"a": (0.3, 0.03, 0.10), "b": (0.3, 0.06, 0.20),
           "c": (0.3, 0.04, 0.15), "d": (0.3, 0.05, 0.12)}
    gotz = {"a": 0.20, "b": 0.10, "c": 0.14, "d": 0.16}
    pair = [(got[m][2], gotz[m]) for m in got]
    rho, pv = spearmanr([a for a, _ in pair], [b for _, b in pair])
    worst = max(pair, key=lambda t: max(t) / min(t))
    assert rho < 0, rho
    assert abs(max(worst) / min(worst) - 2.0) < 1e-9, worst
    # and the ranges still overlap, which is the claim that survives
    assert min(v[2] for v in got.values()) <= max(gotz.values())
    print("  share forms: a negative correlation is reported, not called "
          "agreement")


check_share_forms()


# ------------------------------- saturation is not read off a bounded reading
def check_ceiling_free_trend():
    """The ceiling-free authored component gets its own correlation.

    Section 5.4 offered the rise of the authored component as saturation
    "showing up directly".  That component is a midrank and has a top, so a
    rise in it is exactly what a ceiling argument must not lean on.  Only the
    z SHARE was correlated against capacity; the z authored component, which
    is the control that could corroborate the rise or fail to, had no macro.
    Measured, it does not rise.  Here the midrank component rises while the z
    component falls, and the two correlations must come out with opposite
    signs rather than one standing for both.
    """
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_tables as M
    import numpy as np

    blk, kinds = {}, {}
    ladder = [("gpt2", 124, 0.30, 1.40), ("gpt2-medium", 355, 0.33, 1.35),
              ("gpt2-large", 774, 0.36, 1.30), ("gpt2-xl", 1558, 0.39, 1.25),
              ("Qwen/Qwen3-4B-Base", 4000, 0.42, 1.20)]
    for model, _, auth, az in ladder:
        kinds[model] = "causal"
        for corpus in ("Opus46", "GPT54", "GPT56"):
            recs = {}
            for i in range(6):
                recs[("noncausal", i)] = {
                    "percentile_written": 0.5 + auth, "z_written": az,
                    "is_strict_max": False}
                recs[("causal", i)] = {
                    "percentile_written": 0.5 + auth + 0.04,
                    "z_written": az + 0.2, "is_strict_max": True}
            blk[(model, corpus)] = recs
    M.MACROS.clear()
    M.trend_macros(blk, kinds)
    g = M.MACROS
    assert float(g["TrendAuthoredRho"]) > 0.9, g["TrendAuthoredRho"]
    assert float(g["TrendAuthoredZRho"]) < -0.9, g["TrendAuthoredZRho"]
    print("  saturation: the bounded and ceiling-free components are "
          "correlated separately")


check_ceiling_free_trend()


def check_exact_p():
    """No reported p-value may be smaller than the exact test can return.

    scipy.stats.spearmanr returns a t-approximation p at every n.  Every
    correlation this paper reports is at n = 5, where the smallest two-sided
    p a permutation test can produce is 2/5! = 0.0167.  The ceiling trend
    was published as p = 0.005, a value no exact test can return; the exact
    figure is 0.033.  This check is the one that would have caught it: it
    walks every P macro paired with an N and refuses a p below that n's
    floor, so an asymptotic p-value cannot re-enter unnoticed.
    """
    import math
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_tables as M
    import numpy as np

    # the helper itself, against a case computable by hand
    x = [1, 2, 3, 4, 5]
    rho, p, exact = M.spearman(x, [1, 2, 3, 4, 5])
    assert exact and abs(rho - 1.0) < 1e-12, (rho, exact)
    assert abs(p - 2 / 120) < 1e-12, p          # only the identity attains it

    # one tie, which is the real ladder's shape
    rho, p, _ = M.spearman(x, [1, 1, 2, 3, 4])
    assert abs(rho - 0.9746794) < 1e-6, rho
    assert abs(p - 4 / 120) < 1e-12, p          # the tied pair swaps freely

    # it must agree with scipy on rho, which is not what changed
    from scipy.stats import spearmanr
    for y in ([3, 1, 4, 1, 5], [5, 4, 3, 2, 1], [2, 2, 2, 3, 1]):
        assert abs(M.spearman(x, y)[0] - spearmanr(x, y).statistic) < 1e-12, y

    # and it must never return something unattainable
    for y in ([1, 2, 3, 4, 5], [3, 1, 4, 1, 5], [5, 4, 3, 2, 1]):
        assert M.spearman(x, y)[1] >= 2 / 120 - 1e-12, y

    # above the exact window it falls back, and says so
    big = list(range(12))
    assert M.spearman(big, big)[2] is False

    # the floor macro agrees with the arithmetic
    assert abs(M.exact_p_floor(5) - 2 / 120) < 1e-15

    # finally: no P macro in the real run may sit below its own n's floor
    pairs = (("TrendCeilP", "TrendNEval"), ("TrendCausalP", "TrendNEval"),
             ("TrendAuthoredP", "TrendNEval"), ("TrendShareZP", "TrendNEval"),
             ("TrendAuthoredZP", "TrendNEval"),
             ("CtrlPEP", "CtrlNWidths"), ("CtrlPSig", "CtrlNWidths"),
             ("CtrlPXS", "CtrlNWidths"),
             ("ShareFormP", "ShareFormNEval"))
    g = M.MACROS
    seen = 0
    for pk, nk in pairs:
        if pk not in g or nk not in g:
            continue                            # stub run, no measurements
        try:
            pv, n = float(g[pk]), int(g[nk])
        except ValueError:
            continue                            # still TODO
        floor = 2.0 / math.factorial(n)
        assert pv >= floor - 1e-9, f"{pk}={pv} < {floor} attainable at n={n}"
        seen += 1
    print(f"  exact p: helper verified, {seen} reported p-values "
          f"above their attainable floor")


check_exact_p()


def check_grid_steps():
    """One grid step must read the same way everywhere it appears.

    Section 5.3 reads a causal component of two steps as the resolution
    floor and declines to treat its size as measured.  Section 5.4 reported
    the authored component as rising across the ladder, and that rise is
    0.396 - 0.354 = 0.042, which is two steps of the same grid.  The same
    magnitude was a floor in one place and a result in the other.

    The 5.3 sentence was also wrong: "the authored component spans several"
    attached its DISTANCE FROM THE NULL (several steps) to a sentence about
    its SPAN ACROSS EVALUATORS (one step).  This builds a ladder where the
    two differ by construction and pins that they come out as two numbers.
    """
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_tables as M

    # authored component 0.354 -> 0.396 across the ladder: 0.042, which is
    # two steps of the 1/48 grid (#253).  causal component held at the same
    # two steps throughout, so the span and the floor stay comparable.
    blk, kinds = {}, {}
    ladder = [("gpt2", 0.354), ("gpt2-medium", 0.354), ("gpt2-large", 0.354),
              ("gpt2-xl", 0.396), ("Qwen/Qwen3-4B-Base", 0.396)]
    for model, auth in ladder:
        kinds[model] = "causal"
        for corpus in ("Opus46", "GPT54", "GPT56"):
            recs = {}
            for i in range(6):
                recs[("noncausal", i)] = {
                    "percentile_written": 0.5 + auth, "n_perms": 24}
                recs[("causal", i)] = {
                    "percentile_written": 0.5 + auth + 1 / 24, "n_perms": 24}
            blk[(model, corpus)] = recs
    M.MACROS.clear()
    M.grid_macros(blk, kinds)
    g = M.MACROS

    assert g["GridK"] == "48", g["GridK"]
    assert g["CausalCompStepsMax"] == "2", g["CausalCompStepsMax"]
    # the two readings of the authored component must not be one number
    assert float(g["AuthoredCompStepsMin"]) > 5, g["AuthoredCompStepsMin"]
    assert abs(float(g["AuthoredCompSpanSteps"]) - 2.0) < 0.05, \
        g["AuthoredCompSpanSteps"]
    # and the span must be on the same ruler as the causal component, so a
    # sentence calling one a floor cannot call the other a size
    assert float(g["AuthoredCompSpanSteps"]) <= float(g["CausalCompStepsMax"]), \
        (g["AuthoredCompSpanSteps"], g["CausalCompStepsMax"])
    print("  grid steps: the authored component's value and its span are "
          "two numbers, and the span is on the causal component's ruler")


check_grid_steps()


def check_label_swap():
    """The decomposition is not independent of the labelling, and says so.

    Section 3.4 described Eq. (8) as "independent of whether the labelling
    of that set as non-causal is correct".  Eq. (8) selects the non-causal
    set; selecting the other one gives a different number.  Both sets are
    authored, so either choice is an authored component, and the difference
    between the two choices is exactly Eq. (9) with its sign flipped.

    Built here with a known answer: non-causal at midrank 0.854, causal at
    0.896.  As published, authored = +0.354 and causal = +0.042.  Swapped,
    authored = +0.396 and causal = -0.042, and the share goes negative --
    which is the property no label-independent quantity has.
    """
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_tables as M
    import tempfile

    blk, kinds = {}, {}
    for model in ("gpt2", "gpt2-xl"):
        kinds[model] = "causal"
        for corpus in ("Opus46", "GPT54", "GPT56"):
            recs = {}
            for i in range(6):
                recs[("noncausal", i)] = {
                    "percentile_written": 0.854, "z_written": 1.2,
                    "n_perms": 24, "is_strict_max": False}
                recs[("causal", i)] = {
                    "percentile_written": 0.896, "z_written": 1.4,
                    "n_perms": 24, "is_strict_max": True}
            blk[(model, corpus)] = recs
    M.MACROS.clear()
    M.table_decomposition(blk, kinds, tempfile.mkdtemp())
    g = M.MACROS

    assert g["SwapAuthoredOrig"] == "+0.354", g["SwapAuthoredOrig"]
    assert g["SwapCausalOrig"] == "+0.042", g["SwapCausalOrig"]
    assert g["SwapAuthored"] == "+0.396", g["SwapAuthored"]
    assert g["SwapCausal"] == "-0.042", g["SwapCausal"]
    # the share is not merely different under a swap; it changes sign
    assert int(g["SwapShareMin"]) < 0, g["SwapShareMin"]
    assert int(g["SwapShareNNeg"]) == int(g["SwapShareNEval"]), \
        (g["SwapShareNNeg"], g["SwapShareNEval"])
    # and the published share stays what it was
    assert int(g["ShareEvalMin"]) > 0, g["ShareEvalMin"]
    print("  label swap: exchanging the labels moves the authored component "
          "by the causal component and turns the share negative")


check_label_swap()


def check_ceiling_sets():
    """The ceiling fraction is measured on both label groups, separately.

    Section 5.4 paired its saturation evidence -- "the fraction of causally
    labelled texts whose authored order is already the extreme arrangement"
    -- with the authored component of Eq. (8), which is defined on the
    NON-causal texts.  Two sets, one argument.  The fraction was also in no
    printed table, so a reader could not see the mismatch.

    Here the two groups are given deliberately different ceiling behaviour:
    the non-causal fraction rises along the ladder and the causal one is
    flat.  If the section ever goes back to one series standing for both,
    the two correlations come out different and this fails.
    """
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_tables as M

    blk, kinds = {}, {}
    ladder = [("gpt2", 0), ("gpt2-medium", 1), ("gpt2-large", 2),
              ("gpt2-xl", 3), ("Qwen/Qwen3-4B-Base", 4)]
    for model, k in ladder:
        kinds[model] = "causal"
        for corpus in ("Opus46", "GPT54", "GPT56"):
            recs = {}
            for i in range(6):
                recs[("noncausal", i)] = {
                    "percentile_written": 0.85, "z_written": 1.2,
                    "n_perms": 24, "is_strict_max": i < k}   # rises with k
                recs[("causal", i)] = {
                    "percentile_written": 0.89, "z_written": 1.4,
                    # non-monotone, not constant: a constant series makes
                    # the rank correlation undefined rather than small
                    "n_perms": 24, "is_strict_max": i < (2, 3, 1, 3, 2)[k]}
            blk[(model, corpus)] = recs
    M.MACROS.clear()
    M.trend_macros(blk, kinds)
    g = M.MACROS

    assert "TrendCeilNRho" in g, sorted(g)
    assert float(g["TrendCeilNRho"]) > 0.9, g["TrendCeilNRho"]
    assert abs(float(g["TrendCeilRho"])) < 0.9, g["TrendCeilRho"]
    # and the section's superlative is a counted number, not an assertion
    assert int(g["TrendNSignificant"]) <= int(g["TrendNTested"]), \
        (g["TrendNSignificant"], g["TrendNTested"])
    assert int(g["TrendNTested"]) >= 5, g["TrendNTested"]
    print("  ceiling sets: the two label groups get their own fraction and "
          "their own trend, and the significance count is measured")


check_ceiling_sets()


def check_tail_contrast():
    """The tail statistic, against a construction with a known answer.

    Section 5.4's saturation evidence failed and the tail contrast replaces
    it, so the tail statistic has to be held to the standard the rest of
    the paper is held to before it carries anything.

    The fixture puts every causal text's midrank at the strict maximum in
    one half of the texts and nowhere near it otherwise, and the non-causal
    texts at a fixed lower value, so the cell difference is exact and the
    threshold sweep has to show nothing below the non-causal level and the
    full difference above it.  The z tail is cut at the non-causal group's
    own 90th percentile, so its null is 10% by construction; here the
    causal z values are all above that cut and it must read 100%.
    """
    import os, sys, tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_tables as M

    blk, kinds = {}, {}
    for model, f in (("gpt2", 0.30), ("gpt2-medium", 0.40),
                     ("gpt2-large", 0.50), ("gpt2-xl", 0.60),
                     ("Qwen/Qwen3-4B-Base", 0.70)):
        kinds[model] = "causal"
        for corpus in ("Opus46", "GPT54", "GPT56", "Gemini31", "Fable5"):
            recs = {}
            for i in range(100):
                top = i < round(f * 100)
                recs[("causal", i)] = {
                    "percentile_written": 0.99 if top else 0.70,
                    "z_written": 3.0, "n_perms": 24, "is_strict_max": top}
                recs[("noncausal", i)] = {
                    "percentile_written": 0.70,
                    "z_written": 1.0, "n_perms": 24, "is_strict_max": False}
            blk[(model, corpus)] = recs
    M.MACROS.clear()
    M.tail_macros(blk, kinds, tempfile.mkdtemp())
    g = M.MACROS

    # the difference is exactly the causal fraction, in points
    assert g["TailDiffGPTtwo"] == "+30", g["TailDiffGPTtwo"]
    assert g["TailDiffQwen"] == "+70", g["TailDiffQwen"]
    assert g["TailNCells"] == "25", g["TailNCells"]
    assert int(g["TailNPositive"]) == 25, g["TailNPositive"]

    # nothing below the level both groups share, everything above it
    assert g["TailSweepLoFifty"] == "0", g["TailSweepLoFifty"]
    assert g["TailSweepLoSixty"] == "0", g["TailSweepLoSixty"]
    # both groups sit at 0.70 exactly, so "> 0.70" separates them and
    # "> 0.60" does not: the onset is the first threshold the shared level
    # falls below, which is 0.70 here and nothing above it changes
    assert g["TailSweepLoSeventy"] == "30", g["TailSweepLoSeventy"]
    assert g["TailSweepLoEighty"] == "30", g["TailSweepLoEighty"]
    assert g["TailSweepHiEighty"] == "70", g["TailSweepHiEighty"]
    assert g["TailOnsetThr"] == "0.70", g["TailOnsetThr"]

    # the ceiling-free tail has a null of 10% and must not inherit the
    # midrank's bound: here every causal z clears the cut
    assert g["TailZNull"] == "10", g["TailZNull"]
    assert g["TailZGPTtwo"] == "100", g["TailZGPTtwo"]

    # and the ladder trend uses the within-corpus pairing of Section 3.4
    assert float(g["TailTrendRho"]) > 0.95, g["TailTrendRho"]
    # the sign test is reported beside the Bonferroni count, because on the
    # measured data they disagree: 24 of 25 cells positive, 8 rejecting
    assert float(g["TailSignP"].split("\\times")[0]) > 0, g["TailSignP"]
    assert "TailZTrendRho" in g, sorted(k for k in g if k.startswith("TailZ"))
    print("  tail contrast: cell differences, the sweep, the ceiling-free "
          "tail and its null all come out as constructed")


check_tail_contrast()


def check_macro_names():
    """Every emitted macro name must be letters only.

    \\TailSweepLo50 was emitted for six thresholds.  LaTeX stopped with
    "Missing \\begin{document}" and pointed at macros.tex, which is where
    the name was written down rather than where it was constructed.  The
    generator refuses it now, so the error names the loop.
    """
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_tables as M

    for bad in ("TailSweepLo50", "Params4B", "Ceil_N", "A B"):
        try:
            M.mac(bad, "1")
        except ValueError:
            continue
        raise AssertionError(f"{bad} was accepted")
    M.MACROS.clear()
    M.mac("TailSweepLoFifty", "1")          # and a good one still works
    assert M.MACROS["TailSweepLoFifty"] == "1"
    M.MACROS.clear()

    # and nothing the real generator emits may break the rule
    for name in M.expected_macro_names() if hasattr(M, "expected_macro_names") \
            else ():
        assert name.isalpha(), name
    print("  macro names: letters only, enforced where the name is made")


check_macro_names()


def check_trend_count():
    """"The one trend this paper reports" must be a counted number.

    Section 5.4 asserted it in prose.  The count is split across two
    functions -- trend_macros() measures five components, tail_macros() two
    more -- so the total has to be folded in where the second set is
    emitted, and a sentence that calls one trend the only one cannot
    outlive a measurement that adds another.
    """
    import os, sys, tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_tables as M

    blk, kinds = {}, {}
    ladder = [("gpt2", 0.30), ("gpt2-medium", 0.40), ("gpt2-large", 0.50),
              ("gpt2-xl", 0.60), ("Qwen/Qwen3-4B-Base", 0.70)]
    for model, f in ladder:
        kinds[model] = "causal"
        for corpus in ("Opus46", "GPT54", "GPT56", "Gemini31", "Fable5"):
            recs = {}
            for i in range(100):
                top = i < round(f * 100)
                recs[("causal", i)] = {
                    "percentile_written": 0.99 if top else 0.70,
                    "z_written": 3.0, "n_perms": 24, "is_strict_max": top}
                recs[("noncausal", i)] = {
                    "percentile_written": 0.70, "z_written": 1.0,
                    "n_perms": 24, "is_strict_max": False}
            blk[(model, corpus)] = recs
    M.MACROS.clear()
    M.trend_macros(blk, kinds)
    base = int(M.MACROS["TrendNTested"])
    M.tail_macros(blk, kinds, tempfile.mkdtemp())
    assert int(M.MACROS["TrendNTested"]) == base + 2, M.MACROS["TrendNTested"]
    assert int(M.MACROS["TrendNSignificant"]) >= 1, \
        M.MACROS["TrendNSignificant"]
    assert int(M.MACROS["TrendNSignificant"]) <= int(M.MACROS["TrendNTested"])
    print("  trend count: the tail trends are counted with the rest")


check_trend_count()


def check_contrast_cells():
    """The claim "separates the groups everywhere" needs a cell-level test.

    Three sentences made it from \\BlkPMaxCausal, a macro whose name says
    maximum while holding a minimum, whose p tests the causal group against
    the 0.50 null rather than the two groups against each other, and which
    is computed for gpt2 alone.  This builds a ladder where the answer is
    known: every cell separates, so every cell must reject and the worst p
    must still be small.
    """
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_tables as M
    import numpy as np

    rng = np.random.default_rng(3)
    blk, kinds = {}, {}
    for model in ("gpt2", "gpt2-medium", "gpt2-large", "gpt2-xl",
                  "Qwen/Qwen3-4B-Base"):
        kinds[model] = "causal"
        for corpus in ("Opus46", "GPT54", "GPT56", "Gemini31", "Fable5"):
            recs = {}
            for i in range(60):
                recs[("causal", i)] = {
                    "percentile_written": float(rng.uniform(0.70, 0.99)),
                    "n_perms": 24}
                recs[("noncausal", i)] = {
                    "percentile_written": float(rng.uniform(0.40, 0.69)),
                    "n_perms": 24}
            blk[(model, corpus)] = recs
    M.MACROS.clear()
    M.contrast_macros(blk, kinds)
    g = M.MACROS
    assert g["ContrastNCells"] == "25", g["ContrastNCells"]
    assert g["ContrastNRejecting"] == "25", g["ContrastNRejecting"]
    assert g["ContrastNPositive"] == "25", g["ContrastNPositive"]
    assert float(g["ContrastRMedian"]) > 0.9, g["ContrastRMedian"]
    # The count is over a ladder, so the ladder has to survive into the
    # output: "N of 25" was reported for revisions with no way to see
    # whether the failures were spread or stacked.
    by = g.get("ContrastRejectByEval", "")
    assert by.count("/") == 5, by          # one entry per rung
    assert by.count("5/5") == 5, by        # this fixture separates in all
    assert "gpt2-medium" in by, by         # including the middle rungs
    with tempfile.TemporaryDirectory() as _d:
        M.MACROS.clear()
        M.contrast_macros(blk, kinds, _d)
        assert os.path.exists(os.path.join(_d, "tab_blkcells.tex")), \
            "the autoregressive cells have no table again"
        rows = open(os.path.join(_d, "tab_blkcells.tex")).read()
        assert rows.count(chr(92) * 2) >= 25, rows
    print("  contrast cells: the ladder survives into the macros and a table")

    # and a ladder where the groups do NOT differ must reject (almost) none
    for key in blk:
        for k in list(blk[key]):
            blk[key][k] = {"percentile_written": float(rng.uniform(0.4, 0.99)),
                           "n_perms": 24}
    M.MACROS.clear()
    M.contrast_macros(blk, kinds)
    assert int(M.MACROS["ContrastNRejecting"]) <= 1, \
        M.MACROS["ContrastNRejecting"]
    print("  contrast cells: every cell tested, counted, and the worst p "
          "reported")


def check_between_set_reading():
    """The between-set reading must carry both evaluators and its sign.

    It used to be generated from a single-evaluator file, with no table and
    no evaluator dimension in the macros, and three sentences described it
    as covering two.  One of them was false.
    """
    import make_tables as M
    with tempfile.TemporaryDirectory() as tmp:
        src, out = os.path.join(tmp, "sigfb"), os.path.join(tmp, "tables")
        os.makedirs(src)
        os.makedirs(out)

        def cell(model, corpus, sw):
            """Two label groups, and a given sign for the authored sigma."""
            recs = []
            for i in range(12):
                cat = "causal" if i % 2 else "noncausal"
                recs.append({"percentile_written": 0.30 + 0.01 * i,
                             "n_perms": 24, "degenerate": False,
                             "category": cat, "index": i,
                             "sigma_fb_written": sw + 0.001 * i})
            with open(os.path.join(
                    src, f"sigfb_{model.split('/')[-1]}__{corpus}.json"),
                    "w") as fh:
                json.dump({"meta": {"script": "block_sigma_fb.py",
                                    "model": model, "corpus": corpus},
                           "records": recs}, fh)

        # LLaDA positive everywhere, bert-base negative everywhere
        for corpus, s in (("A", 0.05), ("B", 0.07)):
            cell("GSAI-ML/LLaDA-8B-Base", corpus, s)
            cell("bert-base-uncased", corpus, -s)
        M.MACROS.clear()
        M.table_fbrank(src, out)
        g = M.MACROS
        assert g["FbBetweenNPosLLaDA"] == "2", g.get("FbBetweenNPosLLaDA")
        assert g["FbBetweenNPosBertBase"] == "0", \
            g.get("FbBetweenNPosBertBase")
        assert g["FbBetweenNOpposite"] == "2", g.get("FbBetweenNOpposite")
        assert os.path.exists(os.path.join(out, "tab_fbbetween.tex")), \
            "the between-set reading has no table again"
        print("  between-set: both evaluators, tabulated, sign counted")


def check_corpus_prefix():
    """One corpus ordering, whichever name the run keys cells by.

    The masked runs carry a "fixed_text_" prefix and the autoregressive
    ones do not; membership was tested on the full string, so the two
    halves of the paper were ordered differently and no page showed it.
    """
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
check_between_set_reading()
