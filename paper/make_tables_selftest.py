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
        # gpt2: token reversal 2x, no flip.
        make_cell(os.path.join(pll, "pll_gpt2__A__0-1.json"),
                  "gpt2", "causal", "Opus46",
                  blk_causal=0.400, blk_non=0.300,
                  tok_causal=0.800, tok_non=0.600)

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
        assert len(body) == 3, f"expected 3 data rows, got {len(body)}"
        for l in body:
            cells = [c.strip() for c in l.split("&")]
            assert len(cells) == 5, f"expected 5 columns, got {len(cells)}: {l}"
            assert cells[-2] != "--", f"token median missing: {l}"
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
        tmed = [float([c.strip() for c in l.split("&")][-2]) for l in body]
        assert abs(tmed[0] - 0.5) < 0.01 and abs(tmed[1] - 0.5) < 0.01, \
            f"bert token medians should be near 0.50, got {tmed[:2]}"
        assert abs(tmed[2] - 0.7) < 0.01, \
            f"gpt2 token median should be near 0.70, got {tmed[2]}"

        # --- the macros say what the table shows ----------------------------
        assert macro("NTokCells") == "3"
        assert macro("NTokLarger") == "3", \
            "every synthetic cell has the larger token median"
        assert macro("NTokNegMasked") == "1", "one masked corpus flips sign"
        assert macro("NTokNegMaskedTot") == "2"
        assert macro("NTokNegAR") == "0"
        assert macro("NTokNegARTot") == "1"
        lo, hi = float(macro("SigTokRatioMin")), float(macro("SigTokRatioMax"))
        assert 1.0 < lo <= hi, f"ratio range looks wrong: {lo}-{hi}"
        assert abs(lo - 2.0) < 0.2, f"gpt2 ratio should be about 2, got {lo}"
        assert abs(hi - 20.0) < 2.0, f"bert ratio should be about 20, got {hi}"

    print("make_tables selftest: OK")
    print("  tab_token.tex written, 5 columns, no missing cells")
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
