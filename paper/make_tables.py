#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate every table AND every number quoted in the prose, as LaTeX.

Nothing numeric in this paper is typed by hand.  Tables are written as
\\input-able fragments, and each figure quoted in the running text becomes a
macro in macros.tex, so the sentence reads

    causality accounts for \\CausalShareOpus of the effect

and cannot drift from the measurement.  Rerunning the measurement and this
script updates the prose.

Outputs (into --outdir):
    macros.tex        \\newcommand for each quoted figure
    tab_blkord.tex    within-text permutation test, the decisive table
    tab_pll.tex       evaluator comparison, sigma and effect size
    tab_capacity.tex  toy-system capacity sweep

    python3 make_tables.py --pll ../order-intervention/results_pll \\
        --blkord ../order-intervention/results_blkord \\
        --toy ../bert-affinity --outdir tables
"""

import argparse
import glob
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np
from math import comb
from scipy.stats import mannwhitneyu, wilcoxon

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CORPUS_ORDER = ["Opus46", "GPT54", "GPT56", "Gemini31", "Fable5"]
# ordered by parameter count: the capacity series is what the paper reads
EVAL_ORDER = ["bert-base-uncased", "gpt2", "bert-large-uncased",
              "gpt2-medium", "gpt2-large", "gpt2-xl",
              "Qwen/Qwen3-4B-Base", "GSAI-ML/LLaDA-8B-Base"]
# LaTeX control sequences may contain letters only, so every evaluator gets a
# letter-only tag and the prose references \Authored<Tag>, \Share<Tag> etc.
TAG = {
    "bert-base-uncased": "BertBase",
    "bert-large-uncased": "BertLarge",
    "gpt2": "GPTtwo",
    "gpt2-medium": "GPTtwoMedium",
    "gpt2-large": "GPTtwoLarge",
    "gpt2-xl": "GPTtwoXL",
    "Qwen/Qwen3-4B-Base": "Qwen",
    "GSAI-ML/LLaDA-8B-Base": "LLaDA",
}

PARAMS = {"bert-base-uncased": 110, "gpt2": 124,
          "bert-large-uncased": 340, "GSAI-ML/LLaDA-8B-Base": 8000,
          "gpt2-medium": 355, "gpt2-large": 774, "gpt2-xl": 1558,
          "Qwen/Qwen3-4B-Base": 4000}
MACROS = {}


def mac(name, value):
    MACROS[name] = value


def tex_sci(x, nd=2):
    """Scientific notation as math-mode CONTENT, no $ delimiters.

    The earlier ad-hoc .replace() chains produced things like
    $3.99\\times10^{-20$}$ -- the exponent brace was closed by the appended
    "}" while the "e-" had already eaten part of the number.  Splitting the
    mantissa and exponent explicitly is the only way this stays right for
    every magnitude and sign.
    """
    if x == 0:
        return "0"
    m, e = f"{x:.{nd}e}".split("e")
    return f"{m}\\times10^{{{int(e)}}}"


def tex_p_bare(p):
    """A p-value as math-mode CONTENT, with no $ delimiters.

    Macro values go in the prose inside $...$, so a value carrying its own $
    would close the math and raise "Missing $ inserted".
    """
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return "\\mathrm{n/a}"
    # at 1e-4 the three-decimal branch printed 0.000, which reads as zero
    if p < 1e-3:
        m, e = f"{p:.0e}".split("e")
        return f"{m}\\times10^{{{int(e)}}}"
    return f"{p:.3f}"


def tex_p(p):
    """A p-value for a plain (non-math) table column: delimiters included."""
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return "--"
    return f"${tex_p_bare(p)}$"


def load_cells(dirpath, prefix):
    bucket, kinds = defaultdict(dict), {}
    if not dirpath or not os.path.isdir(dirpath):
        return bucket, kinds
    for f in sorted(glob.glob(os.path.join(dirpath, f"{prefix}_*.json"))):
        if os.path.basename(f).startswith(f"{prefix}_comparison"):
            continue
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if "records" not in d or "model" not in d:
            continue
        corpus = d["corpus"].replace("fixed_text_", "").replace(".json", "")
        kinds[d["model"]] = d["kind"]
        for r in d["records"]:
            bucket[(d["model"], corpus)][(r["category"], r["index"])] = r
    return bucket, kinds


def order_c(names):
    return [c for c in CORPUS_ORDER if c in names] + \
           sorted(n for n in names if n not in CORPUS_ORDER)


def order_m(names):
    return [m for m in EVAL_ORDER if m in names] + \
           sorted(n for n in names if n not in EVAL_ORDER)


def kind_str(kind):
    """How a model class is printed.

    The JSON records the class as "masked" or "causal", the latter meaning
    causal (left-to-right) attention.  Printing it as "causal" put that word
    in the same table row as the causal/non-causal TEXT labels, with two
    different meanings and nothing to tell them apart.  Nothing in this paper
    calls a model class "causal"; it is spelled out instead.
    """
    return {"causal": "AR", "masked": "masked"}.get(kind, kind or "?")


def params_str(model):
    """Parameter count as it should read in a table cell."""
    p = PARAMS.get(model)
    if not p:
        return "?"
    return f"{p}M" if p < 1000 else f"{p // 1000}B"


def rb(a, b):
    if len(a) < 2 or len(b) < 2:
        return np.nan, np.nan
    st = mannwhitneyu(a, b, alternative="two-sided", method="asymptotic")
    return 2.0 * st.statistic / (len(a) * len(b)) - 1.0, float(st.pvalue)


# -------------------------------------------------------------- blkord
def enumeration_macros(blk):
    """How many blocks each text has, and how many orders that gives.

    The paper says "every text here has exactly four sentence blocks, so the
    4! = 24 enumeration is exact".  That is a claim about the corpora, not a
    constant of the construction, and it was typed in as though it were one.
    If a single text had five blocks it would be false and nothing would say
    so.  Read it from the measurements instead, and define nothing when the
    texts disagree -- the undefined macro then prints as a TODO, which
    make_arxiv.sh refuses to package.
    """
    nb, npm, exact = set(), set(), []
    for recs in blk.values():
        for r in recs.values():
            if "n_blocks" in r:
                nb.add(int(r["n_blocks"]))
            if "n_perms" in r:
                npm.add(int(r["n_perms"]))
            exact.append(bool(r.get("exact_enumeration", False)))
    if not nb:
        return
    if len(nb) > 1 or len(npm) > 1:
        print(f"  WARNING: texts do not agree on block count {sorted(nb)} "
              f"or permutation count {sorted(npm)}; the sentence claiming a "
              f"single exact enumeration is false as written")
        return
    if not all(exact):
        n = sum(1 for e in exact if not e)
        print(f"  WARNING: {n} text(s) were sampled, not enumerated; "
              f"'the enumeration is exact' is false as written")
        return
    mac("NBlocks", str(nb.pop()))
    mac("NPerms", str(npm.pop()))


def table_blkord(blk, kinds, outdir):
    if not blk:
        return
    enumeration_macros(blk)
    # The design counts the prose states.  "Five corpora" and "five
    # evaluators" are facts about the measurements present, not constants of
    # the method: a run missing one evaluator would still produce tables and
    # macros, and the sentence would still say five.
    mac("NEval", str(len({m for m, _ in blk})))
    mac("NCorp", str(len({c for _, c in blk})))
    models = order_m({m for m, _ in blk})
    corpora = order_c({c for _, c in blk})
    lines = [
        r"% generated by make_tables.py -- do not edit",
        r"\begin{tabular}{llrrrrr}",
        r"\toprule",
        r"evaluator & corpus & $n$ & causal & non-causal & $r$ & $p$ \\",
        r"\midrule",
    ]
    shares = {}
    for model in models:
        first = True
        for corpus in corpora:
            recs = blk.get((model, corpus))
            if not recs:
                continue
            pc = np.array([r["percentile_written"] for k, r in recs.items()
                           if k[0] == "causal"], float)
            pn = np.array([r["percentile_written"] for k, r in recs.items()
                           if k[0] == "noncausal"], float)
            if len(pc) < 2 or len(pn) < 2:
                continue
            r_rb, p = rb(pc, pn)
            mc, mn = float(np.median(pc)), float(np.median(pn))
            # how much of the distance from the 0.50 null is attributable to
            # causality, over and above the coherence of an arbitrary but
            # authored order
            coh = mn - 0.5
            shares[(model, corpus)] = (mc - mn) / coh if coh else np.nan
            name = (f"{model.split('/')[-1]} ({params_str(model)}, "
                    f"{kind_str(kinds.get(model))})") if first else ""
            first = False
            lines.append(f"{name} & {corpus} & {len(pc)+len(pn)} & "
                         f"{mc:.3f} & {mn:.3f} & {r_rb:+.3f} & {tex_p(p)} \\\\")
        if not first:
            lines.append(r"\addlinespace")
    if lines[-1] == r"\addlinespace":
        lines.pop()
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(outdir, "tab_blkord.tex"), "w").write("\n".join(lines) + "\n")

    # prose numbers
    allpc, allpn = [], []
    for (model, corpus), recs in blk.items():
        allpc += [r["percentile_written"] for k, r in recs.items() if k[0] == "causal"]
        allpn += [r["percentile_written"] for k, r in recs.items() if k[0] == "noncausal"]
    if allpc:
        mac("MedPctCausal", f"{np.median(allpc):.3f}")
        mac("MedPctNoncausal", f"{np.median(allpn):.3f}")
        d = np.array(allpc) - 0.5
        if (d != 0).sum() >= 10:
            mac("PctVsNullP", tex_p_bare(float(wilcoxon(d, alternative="two-sided").pvalue)))
    # separation counts and median effect size per evaluator, for the prose
    for model, tag in (("bert-base-uncased", "Masked"), ("gpt2", "Causal")):
        rs, nsep, ntot, pmin = [], 0, 0, 1.0
        for corpus in corpora:
            recs = blk.get((model, corpus))
            if not recs:
                continue
            pc = np.array([r["percentile_written"] for k, r in recs.items()
                           if k[0] == "causal"], float)
            pn = np.array([r["percentile_written"] for k, r in recs.items()
                           if k[0] == "noncausal"], float)
            if len(pc) < 2 or len(pn) < 2:
                continue
            r_rb, _ = rb(pc, pn)
            rs.append(r_rb); ntot += 1
            if abs(r_rb) > 0.2:
                nsep += 1
            d = pc - 0.5
            if (d != 0).sum() >= 10:
                pmin = min(pmin, float(wilcoxon(d, alternative="two-sided").pvalue))
        if rs:
            mac(f"BlkR{tag}", f"{np.median(rs):+.3f}")
            mac(f"BlkNSep{tag}", str(nsep))
            mac(f"BlkNTot{tag}", str(ntot))
            mac(f"BlkPMax{tag}", tex_p_bare(pmin))
        # the median position of each group, per evaluator
        pcs, pns = [], []
        for corpus in corpora:
            recs = blk.get((model, corpus))
            if not recs:
                continue
            a = [r["percentile_written"] for k, r in recs.items() if k[0] == "causal"]
            b = [r["percentile_written"] for k, r in recs.items() if k[0] == "noncausal"]
            if a and b:
                pcs.append(np.median(a)); pns.append(np.median(b))
        if pcs:
            mac(f"BlkPctC{tag}", f"{np.median(pcs):.3f}")
            mac(f"BlkPctN{tag}", f"{np.median(pns):.3f}")

    # Median effect size AND median within-corpus gap, for every evaluator.
    # The two answer different questions and the paper has to keep them apart.
    # Gap{t} is what Figure 1 shows: the distance between the two medians on
    # the bounded midrank scale.  It compresses as an evaluator saturates,
    # because both groups pile up against the ceiling at 1.00.  R{t} is a rank
    # statistic -- it measures how far the two groups overlap -- and is blind
    # to a compression that shrinks the gap and the within-group spread by the
    # same factor.  Reporting only R{t} and calling the contrast undiminished
    # would contradict the figure on the facing page, so both are generated.
    allgaps = []
    for model in models:
        t = TAG.get(model)
        if not t:
            continue
        rs, gaps, mcs, mns = [], [], [], []
        for corpus in corpora:
            recs = blk.get((model, corpus))
            if not recs:
                continue
            pc = np.array([r["percentile_written"] for k, r in recs.items()
                           if k[0] == "causal"], float)
            pn = np.array([r["percentile_written"] for k, r in recs.items()
                           if k[0] == "noncausal"], float)
            if len(pc) < 2 or len(pn) < 2:
                continue
            r_rb, _ = rb(pc, pn)
            rs.append(r_rb)
            gaps.append(float(np.median(pc) - np.median(pn)))
            mcs.append(float(np.median(pc)))
            mns.append(float(np.median(pn)))
        if rs:
            mac(f"R{t}", f"{np.median(rs):+.3f}")
            mac(f"Gap{t}", f"{np.median(gaps):+.3f}")
            # the operating point of the evaluator: how far it has already
            # driven an arbitrary authored order towards the 1.00 ceiling.
            # Gap{t} turns out to be ordered by this and not by parameter
            # count, which is the point Section 5.2 makes.
            mac(f"PctC{t}", f"{np.median(mcs):.3f}")
            mac(f"PctN{t}", f"{np.median(mns):.3f}")
            # the room left above an arbitrary authored order: 1 - that median.
            # Generated rather than worked out in the prose, because a ratio
            # between two of these was once stated from memory and was wrong.
            mac(f"Room{t}", f"{1.0 - np.median(mns):.3f}")
            allgaps.append(float(np.median(gaps)))

    # the spread of the raw gap across evaluators, which the prose calls a
    # fivefold spread in two places.  Generated for the same reason the
    # capacity ratios are: a ratio spelled out in words survives a change to
    # the numbers it was computed from.
    allgaps = [g for g in allgaps if abs(g) > 1e-9]
    if len(allgaps) > 1:
        mac("GapSpreadRatio", f"{max(allgaps) / min(allgaps):.1f}")

    if shares:
        v = np.array([s for s in shares.values() if np.isfinite(s)])
        if len(v):
            mac("CausalShareMedian", f"{100*np.median(v):.0f}")
            mac("CausalShareMin", f"{100*v.min():+.0f}")
            mac("CausalShareMax", f"{100*v.max():+.0f}")
            mac("NBlkordCells", str(len(shares)))
            mac("CausalShareNPos", str(int((v > 0.05).sum())))
            mac("CausalShareNTot", str(len(v)))
    print(f"  tab_blkord.tex  ({len(shares)} cells)")


# -------------------------------------------------------------- pll
def table_pll(pll, kinds, outdir):
    if not pll:
        return
    models = order_m({m for m, _ in pll})
    corpora = order_c({c for _, c in pll})
    lines = [
        r"% generated by make_tables.py -- do not edit",
        r"\begin{tabular}{llrrrr}",
        r"\toprule",
        r"evaluator & corpus & $n$ & median $\Delta_{\mathrm{block}}$ & $r$ & $p$ \\",
        r"\midrule",
    ]
    cap = {}
    for model in models:
        first = True
        for corpus in corpora:
            recs = pll.get((model, corpus))
            if not recs:
                continue
            allv = np.array([r["sigma_block_per_T"] for r in recs.values()], float)
            a = np.array([r["sigma_block_per_T"] for k, r in recs.items()
                          if k[0] == "causal"], float)
            b = np.array([r["sigma_block_per_T"] for k, r in recs.items()
                          if k[0] == "noncausal"], float)
            r_rb, p = rb(a, b)
            cap[(model, corpus)] = float(np.median(allv))
            name = (f"{model.split('/')[-1]} ({params_str(model)}, "
                    f"{kind_str(kinds.get(model))})") if first else ""
            first = False
            lines.append(f"{name} & {corpus} & {len(allv)} & "
                         f"{np.median(allv):.4f} & {r_rb:+.3f} & {tex_p(p)} \\\\")
        if not first:
            lines.append(r"\addlinespace")
    if lines[-1] == r"\addlinespace":
        lines.pop()
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(outdir, "tab_pll.tex"), "w").write("\n".join(lines) + "\n")

    # capacity ratios, bert-base -> bert-large
    ratios = []
    for corpus in corpora:
        b = cap.get(("bert-base-uncased", corpus))
        l = cap.get(("bert-large-uncased", corpus))
        if b and l:
            ratios.append(l / b)
    if ratios:
        mac("CapRatioMedian", f"{np.median(ratios):.2f}")
        mac("CapRatioMin", f"{min(ratios):.2f}")
        mac("CapRatioMax", f"{max(ratios):.2f}")
        mac("CapNCorpora", str(len(ratios)))
        mac("CapNUp", str(int(sum(r > 1 for r in ratios))))

    # the scale-matched pair, plus the larger masked model
    for tag, model in (("Masked", "bert-base-uncased"), ("Causal", "gpt2"),
                       ("MaskedLarge", "bert-large-uncased")):
        s = [cap[(model, c)] for c in corpora if (model, c) in cap]
        rr = []
        for c in corpora:
            recs = pll.get((model, c))
            if not recs:
                continue
            a = [r["sigma_block_per_T"] for k, r in recs.items() if k[0] == "causal"]
            bb = [r["sigma_block_per_T"] for k, r in recs.items() if k[0] == "noncausal"]
            v, _ = rb(np.array(a), np.array(bb))
            if np.isfinite(v):
                rr.append(v)
        if s:
            mac(f"Sigma{tag}", f"{np.median(s):.4f}")
        if rr:
            mac(f"R{tag}", f"{np.median(rr):+.3f}")
            mac(f"NSep{tag}", str(int(sum(abs(v) > 0.2 for v in rr))))
            mac(f"NTot{tag}", str(len(rr)))
    print(f"  tab_pll.tex  ({len(cap)} cells)")


# -------------------------------------------------------------- token
def table_token(pll, kinds, outdir):
    """Token reversal: the measurement Section 2.1 sets aside, reported.

    Section 2.1 gives two reasons for working with block reversal instead:
    that token reversal produces the larger quantity, and that its
    causal/non-causal effect size changes sign between corpora.  Both are
    grounds for a choice the whole paper rests on, so both are shown here
    rather than asserted, and the numbers the prose quotes come from the
    macros built below -- never typed into the sentence.

    The table is deliberately its own, and small: it is the one place
    sigma_token appears, and nothing downstream reads it.
    """
    if not pll:
        return
    models = order_m({m for m, _ in pll})
    corpora = order_c({c for _, c in pll})
    lines = [
        r"% generated by make_tables.py -- do not edit",
        r"\begin{tabular}{llrrr}",
        r"\toprule",
        r"evaluator & corpus & $n$ & median $\Delta_{\mathrm{token}}$ & $r$ \\",
        r"\midrule",
    ]
    ratio = []            # median sigma_token / median sigma_block, per cell
    larger = 0            # cells where the token median is the larger one
    neg = defaultdict(lambda: [0, 0])    # model class -> [negative r, cells]
    cells = 0
    for model in models:
        first = True
        for corpus in corpora:
            recs = pll.get((model, corpus))
            if not recs:
                continue
            tall = np.array([r["sigma_token_per_T"] for r in recs.values()
                             if "sigma_token_per_T" in r], float)
            if not len(tall):
                continue
            ta = np.array([r["sigma_token_per_T"] for k, r in recs.items()
                           if k[0] == "causal" and "sigma_token_per_T" in r],
                          float)
            tb = np.array([r["sigma_token_per_T"] for k, r in recs.items()
                           if k[0] == "noncausal" and "sigma_token_per_T" in r],
                          float)
            t_med = float(np.median(tall))
            t_rb, _ = rb(ta, tb)
            blk = np.array([r["sigma_block_per_T"] for r in recs.values()], float)
            b_med = float(np.median(blk))
            if abs(b_med) > 1e-9:
                ratio.append(abs(t_med) / abs(b_med))
            if abs(t_med) > abs(b_med):
                larger += 1
            k = kind_str(kinds.get(model))
            neg[k][1] += 1
            if np.isfinite(t_rb) and t_rb < 0:
                neg[k][0] += 1
            cells += 1
            name = (f"{model.split('/')[-1]} ({params_str(model)}, "
                    f"{kind_str(kinds.get(model))})") if first else ""
            first = False
            rcol = f"{t_rb:+.3f}" if np.isfinite(t_rb) else "--"
            lines.append(f"{name} & {corpus} & {len(tall)} & "
                         f"{t_med:.4f} & {rcol} \\\\")
        if not first:
            lines.append(r"\addlinespace")
    if not cells:
        return
    if lines[-1] == r"\addlinespace":
        lines.pop()
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(outdir, "tab_token.tex"), "w").write("\n".join(lines) + "\n")

    if ratio:
        mac("SigTokRatioMin", f"{min(ratio):.1f}")
        mac("SigTokRatioMax", f"{max(ratio):.1f}")
    mac("NTokLarger", str(larger))
    mac("NTokCells", str(cells))
    for tag, kind in (("Masked", "masked"), ("AR", "AR")):
        if neg[kind][1]:
            mac(f"NTokNeg{tag}", str(neg[kind][0]))
            mac(f"NTokNeg{tag}Tot", str(neg[kind][1]))
    print(f"  tab_token.tex  ({cells} cells)")


# -------------------------------------------------------------- toy
def capacity_ratio_macros():
    """The capacity ratios the prose states in words.

    "A factor of thirty-four within the autoregressive pair" was written when
    gpt2 was listed at 117M.  Correcting that count to the checkpoint's 124M
    moved the ratio to 32 and left the word behind, in two places, because a
    ratio spelled out in prose is not something any check could see.  These
    come from the same PARAMS the table column does.
    """
    def ratio(a, b):
        if a in PARAMS and b in PARAMS:
            return PARAMS[a] / PARAMS[b]
        return None
    for name, (a, b) in {
            "MaskedSpanRatio": ("GSAI-ML/LLaDA-8B-Base", "bert-base-uncased"),
            "BertSpanRatio": ("bert-large-uncased", "bert-base-uncased"),
            "ARSpanRatio": ("Qwen/Qwen3-4B-Base", "gpt2"),
            "ScaleCostRatio": ("GSAI-ML/LLaDA-8B-Base", "gpt2"),
    }.items():
        r = ratio(a, b)
        if r is not None:
            mac(name, f"{r:.0f}" if r >= 10 else f"{r:.1f}")


def repro_macros(toy_dir):
    """How closely the published per-text values were reproduced.

    The paper says the statistical layer "agrees to 10^-13".  That figure was
    typed in from a run, and nothing connected it to the run afterwards.  It
    is the largest absolute difference recorded by
    reproduce_sagawa_stats.py, so read it from there.
    """
    p = os.path.join(toy_dir or "", "sagawa_repro.json")
    if not os.path.isfile(p):
        return
    blob = json.load(open(p))
    rows = blob["recomputed"] if isinstance(blob, dict) else blob
    errs = [r[k] for r in rows for k in r
            if k.startswith("max_abs_err_sigma") and r[k] is not None]
    if not errs:
        return
    mac("ReproMaxErr", tex_sci(max(errs), 1))
    mac("ReproNCorpora", str(len(rows)))


def selftest_macros(blkord_dir):
    """The two tolerances the any-order self-test reaches.

    Quoted in the Reproducibility section.  Typed in from a run until now,
    with nothing connecting them to a run afterwards; aoar_selftest.py now
    writes them beside itself whenever it passes.
    """
    cands = []
    if blkord_dir:
        cands.append(blkord_dir)
        cands.append(os.path.dirname(blkord_dir.rstrip("/")))
    for base in cands:
        p = os.path.join(base, "aoar_selftest.json")
        if os.path.isfile(p):
            d = json.load(open(p))
            mac("AoarOrderDev", tex_sci(d["max_abs_order_dev"], 1))
            mac("AoarNormDev", tex_sci(d["max_abs_norm_dev"], 1))
            return


def table_capacity(toy_dir, outdir):
    repro_macros(toy_dir)
    p = os.path.join(toy_dir or "", "capacity_results.json")
    if not os.path.isfile(p):
        return
    d = json.load(open(p))
    rows = d.get("rows", [])
    lines = [
        r"% generated by make_tables.py -- do not edit",
        r"\begin{tabular}{lrrrrr}",
        r"\toprule",
        # NOT \sigma: this column is the entropy production of the induced
        # Glauber chain, a different quantity from Eq. (1) of the paper
        r"model & $d$ & params & loss & $\sigma_{\mathrm{EP}}$"
        r" & $\mathrm{rms}|A|$ \\",
        r"\midrule",
    ]
    for r in rows:
        sig = r["sigma"]
        sig_s = f"${tex_sci(sig)}$" if sig < 1e-6 else f"{sig:.4f}"
        lines.append(f"{r['kind']} & {r['d']} & {r['params']} & "
                     f"{r['final_loss']:.4f} & {sig_s} & "
                     f"{r['affinity_rms']:.4f} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(outdir, "tab_capacity.tex"), "w").write("\n".join(lines) + "\n")

    mlm = [r for r in rows if r.get("kind") == "MLM"]
    ar = [r for r in rows if r.get("kind") == "AR"]
    if mlm:
        mac("ToySigmaMin", tex_sci(min(r["sigma"] for r in mlm)))
        mac("ToySigmaMax", tex_sci(max(r["sigma"] for r in mlm)))
        mac("ToyCapRatio", f"{max(r['sigma'] for r in mlm)/min(r['sigma'] for r in mlm):.1f}")
        mac("ToyNCap", str(len(mlm)))
        mac("ToyDMin", str(min(r["d"] for r in mlm)))
        mac("ToyDMax", str(max(r["d"] for r in mlm)))
    if ar:
        mac("ToySigmaAR", tex_sci(ar[0]["sigma"], 1))
        # how far the masked floor sits above the autoregressive zero.  The
        # prose said "eighteen orders of magnitude"; the span is 17.2 to 17.8,
        # so the word took the top of the range.  Report the bottom, which is
        # the one the claim needs.
        lo = min(r["sigma"] for r in mlm)
        if ar[0]["sigma"] > 0 and lo > 0:
            mac("ToyOrdersAbove",
                str(int(math.floor(math.log10(lo / ar[0]["sigma"])))))
        mac("ToyRmsAR", f"{ar[0]['affinity_rms']:.4f}")
    mac("ToyL", str(d.get("L", "?")))
    mac("ToyV", str(d.get("V", "?")))
    mac("ToyStates", str(d.get("V", 0) ** d.get("L", 0)))
    mac("ToyN", f"{d.get('N', 0):,}".replace(",", "{,}"))
    print(f"  tab_capacity.tex  ({len(rows)} rows)")


def gap_room_ratio(pc, pn):
    """Gap between the two medians, as a fraction of the room above the
    non-causal median.

    The midrank is bounded above by 1.00, so an evaluator that has already
    pushed an arbitrary authored order to 0.90 leaves at most 0.10 for the
    labelled contrast to occupy.  Dividing by that room is what makes the
    contrast comparable across evaluators that sit at different heights;
    the raw gap is not.  Returns nan when there is no room left to divide by.
    """
    mn = float(np.median(pn))
    room = 1.0 - mn
    if room < 1e-9:
        return np.nan
    return (float(np.median(pc)) - mn) / room


def boot_ratio_ci(per_corpus, rng, B=2000):
    """A 95% interval for the median-over-corpora of gap_room_ratio.

    Each draw resamples the texts within every corpus -- the two label groups
    independently, because they are different texts -- recomputes the ratio
    per corpus, and takes the median across corpora, which is the statistic
    the table reports.  The denominator is small for a saturated evaluator, so
    this interval is the thing that says whether its ratio is really distinct
    from another's; quoting the ratio without it would hide that.  Draws in
    which a corpus has no room left are dropped rather than clipped, and the
    surviving count is returned so a thin resample cannot pass as a tight one.
    """
    vals = []
    for _ in range(B):
        rs = []
        for pc, pn in per_corpus:
            r = gap_room_ratio(rng.choice(pc, size=len(pc), replace=True),
                               rng.choice(pn, size=len(pn), replace=True))
            if np.isfinite(r):
                rs.append(r)
        if rs:
            vals.append(float(np.median(rs)))
    if len(vals) < B // 2:
        return np.nan, np.nan, len(vals)
    return (float(np.percentile(vals, 2.5)),
            float(np.percentile(vals, 97.5)), len(vals))


def table_saturation(blk, kinds, outdir):
    """How much room the measure has left, and what the contrast does with it.

    Once the authored order IS the single most forward-costly arrangement, no
    normalisation can express a further increase: that ceiling is in the
    phenomenon, not in the statistic.  The fraction of texts sitting at it
    therefore bounds how far this protocol can be pushed.

    The last two columns are why the table matters to Section 5.2.  The raw
    gap between the two medians varies fivefold across evaluators and tracks
    neither parameter count nor model class; measured against the room that
    was left above the non-causal median it moves far less.  So the raw gap is
    a fact about where the evaluator sits, not about the texts.  The non-causal
    median itself is quoted in the prose as PctN<Tag> rather than given a
    column here, because an eighth column overflows the text block.
    """
    if not blk:
        return
    models = order_m({m for m, _ in blk})
    corpora = order_c({c for _, c in blk})
    # fixed seed: the interval is part of a published number and must not move
    # between runs of this script
    rng = np.random.default_rng(20261110)
    lines = [
        r"% generated by make_tables.py -- do not edit",
        # seven columns, not eight: the non-causal median was measured to
        # 46.7pt past the text block here and is quoted in the prose instead
        r"\begin{tabular}{llrrrrr}",
        r"\toprule",
        r" & & & \multicolumn{2}{c}{at ceiling} & & gap / room \\",
        r"\cmidrule(lr){4-5}",
        r"evaluator & direction & params & causal & non-causal"
        r" & gap & (95\% CI) \\",
        r"\midrule",
    ]
    n_rows = 0
    all_ratios, all_ci = [], []
    for model in models:
        fc, fn, gaps, per_corpus = [], [], [], []
        for corpus in corpora:
            recs = blk.get((model, corpus), {})
            c = [r["is_strict_max"] for k, r in recs.items() if k[0] == "causal"]
            n = [r["is_strict_max"] for k, r in recs.items() if k[0] == "noncausal"]
            if c:
                fc.append(float(np.mean(c)))
            if n:
                fn.append(float(np.mean(n)))
            pc = np.array([r["percentile_written"] for k, r in recs.items()
                           if k[0] == "causal"], float)
            pn = np.array([r["percentile_written"] for k, r in recs.items()
                           if k[0] == "noncausal"], float)
            if len(pc) >= 2 and len(pn) >= 2:
                per_corpus.append((pc, pn))
                gaps.append(float(np.median(pc) - np.median(pn)))
        if not fc:
            continue
        p = PARAMS.get(model)
        ps = "--" if not p else (f"{p}M" if p < 1000 else f"{p//1000}B")
        if per_corpus:
            ratio = float(np.median([gap_room_ratio(a, b)
                                     for a, b in per_corpus]))
            lo, hi, nboot = boot_ratio_ci(per_corpus, rng)
            rat = (f"{ratio:.2f}  [{lo:.2f}, {hi:.2f}]"
                   if np.isfinite(lo) else f"{ratio:.2f}  [--]")
            gap_s = f"${np.median(gaps):+.3f}$"
        else:
            ratio, lo, hi = np.nan, np.nan, np.nan
            rat, gap_s = "--", "--"
        lines.append(f"{model.split('/')[-1]} & {kind_str(kinds.get(model))} & {ps} & "
                     f"{100*np.median(fc):.0f}\\% & "
                     f"{100*np.median(fn):.0f}\\% & "
                     f"{gap_s} & {rat}" + r" \\")
        n_rows += 1
        t = TAG.get(model)
        if t:
            mac(f"Ceil{t}", f"{100*np.median(fc):.0f}")
            mac(f"CeilN{t}", f"{100*np.median(fn):.0f}")
            if np.isfinite(ratio):
                mac(f"Ratio{t}", f"{ratio:.2f}")
            if np.isfinite(lo):
                mac(f"RatioLo{t}", f"{lo:.2f}")
                mac(f"RatioHi{t}", f"{hi:.2f}")
        if np.isfinite(ratio):
            all_ratios.append(ratio)
            if np.isfinite(lo):
                all_ci.append((lo, hi))
    # The span and the common overlap, so the prose never has to name which
    # evaluator sits at an extreme: a superlative typed by hand goes stale the
    # moment the measurements change, and two of them already had.
    if all_ratios:
        mac("RatioMin", f"{min(all_ratios):.2f}")
        mac("RatioMax", f"{max(all_ratios):.2f}")
        mac("RatioNEval", str(len(all_ratios)))
    if all_ci:
        olo, ohi = max(a for a, _ in all_ci), min(b for _, b in all_ci)
        mac("RatioNCI", str(len(all_ci)))
        if olo <= ohi:
            # every interval contains this range, so no pair is separated
            mac("RatioOverlapLo", f"{olo:.2f}")
            mac("RatioOverlapHi", f"{ohi:.2f}")
        # Deliberately left undefined when the intervals do NOT all overlap.
        # Section 5.2 asserts that they do; if a future measurement breaks
        # that, these become [TODO:RatioOverlapLo] and make_arxiv.sh refuses
        # to package, which is what should happen -- the sentence would be
        # false and has to be rewritten rather than quietly kept.
        # widest interval, named by its width rather than by guesswork
        w = max(all_ci, key=lambda t: t[1] - t[0])
        mac("RatioWidestLo", f"{w[0]:.2f}")
        mac("RatioWidestHi", f"{w[1]:.2f}")
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(outdir, "tab_saturation.tex"), "w").write(
        "\n".join(lines) + "\n")
    print(f"  tab_saturation.tex  ({n_rows} evaluators)")


def table_decomposition(blk, kinds, outdir):
    """Split the within-text distance from the 0.50 null into two components.

    The non-causal texts have an arbitrary sentence order that a writer
    nevertheless chose, so their distance from the null measures what ANY
    authored order earns.  Whatever the causal texts have beyond that is the
    part only causal order earns.  Doing this per evaluator is what separates
    a property of the text from a property of the evaluator.
    """
    if not blk:
        return
    models = order_m({m for m, _ in blk})
    corpora = order_c({c for _, c in blk})
    lines = [
        r"% generated by make_tables.py -- do not edit",
        r"\begin{tabular}{llrrrrrr}",
        r"\toprule",
        r" & & \multicolumn{3}{c}{midrank} & \multicolumn{3}{c}{$z$} \\",
        r"\cmidrule(lr){3-5}\cmidrule(lr){6-8}",
        r"evaluator & direction & authored & causal & share"
        r" & authored & causal & share \\",
        r"\midrule",
    ]
    got, gotz = {}, {}
    for model in models:
        a_, c_, az_, cz_ = [], [], [], []
        for corpus in corpora:
            recs = blk.get((model, corpus), {})
            pc = [r["percentile_written"] for k, r in recs.items() if k[0] == "causal"]
            pn = [r["percentile_written"] for k, r in recs.items() if k[0] == "noncausal"]
            if not pc or not pn:
                continue
            a_.append(float(np.median(pn)) - 0.5)
            c_.append(float(np.median(pc)) - float(np.median(pn)))
            # z has no ceiling and its null is 0 for the same antisymmetry
            # reason, so it is the check on the midrank split
            zc1 = [r["z_written"] for k, r in recs.items()
                   if k[0] == "causal" and np.isfinite(r.get("z_written", np.nan))]
            zn1 = [r["z_written"] for k, r in recs.items()
                   if k[0] == "noncausal" and np.isfinite(r.get("z_written", np.nan))]
            if zc1 and zn1:
                az_.append(float(np.median(zn1)))
                cz_.append(float(np.median(zc1)) - float(np.median(zn1)))
        if not a_:
            continue
        auth, caus = float(np.median(a_)), float(np.median(c_))
        tot = auth + caus
        share = caus / tot if tot else float("nan")
        got[model] = (auth, caus, share)
        zc, zn = cz_, az_
        if zc and zn:
            az = float(np.median(zn))
            cz = float(np.median(zc))
            tz = az + cz
            # tz > 0, not tz: a negative total flips the sign twice and
            # prints a large POSITIVE share for a component that subtracts
            sz = cz / tz if tz > 0 else float("nan")
            if kinds.get(model) == "causal":
                gotz[model] = sz
            zcols = (f"${az:+.3f}$ & ${cz:+.3f}$ & "
                     + (f"{100*sz:.0f}\\%" if np.isfinite(sz) else "--"))
        else:
            zcols = "-- & -- & --"
        lines.append(f"{model.split('/')[-1]} & {kind_str(kinds.get(model))} & "
                     f"${auth:+.3f}$ & ${caus:+.3f}$ & "
                     + (f"{100*share:.0f}\\%" if np.isfinite(share) else "--")
                     + " & " + zcols + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(outdir, "tab_decomposition.tex"), "w").write(
        "\n".join(lines) + "\n")

    # The per-evaluator macros are emitted by the loop below, which already
    # keys on TAG; the Masked/Causal pair here is kept only while the text
    # still references it.  With PLL dropped the masked rows have no source
    # and the pair resolves to TODO, which is the correct visible failure.
    for model, tag in (("bert-base-uncased", "Masked"), ("gpt2", "Causal")):
        if model in got:
            auth, caus, share = got[model]
            mac(f"Authored{tag}", f"{auth:+.3f}")
            mac(f"CausalComp{tag}", f"{caus:+.3f}")
            if np.isfinite(share):
                mac(f"CausalShare{tag}", f"{100*share:.0f}")
    # The z decomposition has no ceiling and no grid, so its share is the
    # one to quote when the midrank share sits at the statistic's resolution.
    zsh = [v for v in gotz.values() if np.isfinite(v)]
    if zsh:
        mac("ShareZMin", f"{100 * min(zsh):.0f}")
        mac("ShareZMax", f"{100 * max(zsh):.0f}")
        mac("ShareZNEval", str(len(zsh)))
    # and one set per evaluator, for the capacity series in the prose
    for model, (auth, caus, share) in got.items():
        t = TAG.get(model)
        if not t:
            continue
        mac(f"Authored{t}", f"{auth:+.3f}")
        mac(f"Causal{t}", f"{caus:+.3f}")
        if np.isfinite(share):
            mac(f"Share{t}", f"{100*share:.0f}")
        p = PARAMS.get(model)
        if p:
            # used both inside $...$ (abstract) and in a tabular cell (text
            # mode), so it has to be mode-agnostic
            unit = "M" if p < 1000 else "B"
            val = p if p < 1000 else p // 1000
            mac(f"Params{t}",
                f"\\ensuremath{{{val}\\,\\mathrm{{{unit}}}}}")
    print(f"  tab_decomposition.tex  ({len(got)} evaluators)")


# ------------------------------------------------------- forward/backward
def load_sigfb(dirpath):
    """{(model, corpus): [records]} from block_sigma_fb.py, shards merged."""
    cells = defaultdict(list)
    for f in sorted(glob.glob(os.path.join(dirpath, "*.json"))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        m = d.get("meta") or {}
        if m.get("script") != "block_sigma_fb.py" or "records" not in d:
            continue
        cells[(m.get("model", "?"), m.get("corpus", "?"))] += d["records"]
    return cells


def table_fbrank(dirpath, outdir, k=None):
    """Where the written arrangement ranks under the TRUE sigma.

    Unlike the Delta instrument this one exists only for masked evaluators,
    and a rank exists at all only because the evaluator is incompatible: the
    n! values coincide exactly when its conditionals come from a joint.
    Degenerate texts are counted and excluded from the effect size rather
    than ranked, so a near-compatible evaluator cannot contribute a
    percentile made out of rounding noise.
    """
    cells = load_sigfb(dirpath)
    if not cells:
        return
    if k is None:
        kk = {r.get("n_perms") for recs in cells.values() for r in recs
              if r.get("n_perms")}
        k = max(kk) if kk else 0
    models = order_m({m for m, _ in cells})
    corpora = order_c({c for _, c in cells})
    lines = [
        r"% generated by make_tables.py -- do not edit",
        r"\begin{tabular}{llrrrrrr}",
        r"\toprule",
        r"evaluator & corpus & $n$ & degen & causal & non-causal & $r$ & $p$ \\",
        r"\midrule",
    ]
    per_model = defaultdict(lambda: {"a": [], "c": [], "r": []})
    n_texts = n_degen = 0
    all_r, all_rp, all_disp = [], [], []
    for model in models:
        for corpus in corpora:
            recs = cells.get((model, corpus))
            if not recs:
                continue
            live = [r for r in recs if not r.get("degenerate")]
            degen = len(recs) - len(live)
            n_texts += len(recs)
            n_degen += degen
            pc = [r["percentile_written"] for r in live
                  if r["category"] == "causal"]
            pn = [r["percentile_written"] for r in live
                  if r["category"] == "noncausal"]
            if not pc or not pn:
                continue
            r_rb, p_val = rb(pc, pn)
            mc, mn = float(np.median(pc)), float(np.median(pn))
            all_r.append(r_rb)
            all_rp.append(float(p_val))
            # Is each set displaced from the null at all?  r is silent
            # on this: both sets could sit at 0.50 and still differ.
            for v in (pc, pn):
                dd = np.asarray(v, float) - 0.5
                if (dd != 0).sum() >= 6:
                    try:
                        all_disp.append(float(wilcoxon(
                            dd, alternative='two-sided').pvalue))
                    except ValueError:
                        pass
            per_model[model]["a"].append(mn - 0.5)
            per_model[model]["c"].append(mc - mn)
            per_model[model]["r"].append(r_rb)
            lines.append(
                f"{model.split('/')[-1]} & {corpus.replace('fixed_text_', '')}"
                f" & {len(recs)} & {degen} & ${mc:.3f}$ & ${mn:.3f}$ & "
                f"${r_rb:+.3f}$ & {tex_p(p_val)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(outdir, "tab_fbrank.tex"), "w").write(
        "\n".join(lines) + "\n")
    print(f"  tab_fbrank.tex  ({len(all_r)} cells, {n_texts} texts, "
          f"{n_degen} degenerate)")

    # The causal contrast is one test per (evaluator, corpus).  With
    # that many, the count that matters is how many survive a
    # correction, not how many fall below 0.05 on their own.
    if all_rp:
        thr = 0.05 / len(all_rp)
        mac("FbNTestsCausal", str(len(all_rp)))
        mac("FbBonferroni", f"{thr:.4f}")
        mac("FbNSurviving", str(sum(1 for q in all_rp if q < thr)))
        mac("FbNNominal", str(sum(1 for q in all_rp if q < 0.05)))
        mac("FbNExpected", f"{0.05 * len(all_rp):.1f}")
    if all_disp:
        mac("FbNTestsDisp", str(len(all_disp)))
        mac("FbDispPMax", tex_sci(max(all_disp)))
        mac("FbDispNSurviving",
            str(sum(1 for q in all_disp if q < 0.05 / len(all_disp))))
    mac("FbNCorpora", str(len(corpora)))
    mac("FbNTexts", str(n_texts))
    mac("FbNCells", str(len(all_r)))
    mac("FbDegenTotal", str(n_degen))
    if all_r:
        mac("FbRMin", f"{min(all_r):+.3f}")
        mac("FbRMax", f"{max(all_r):+.3f}")
        mac("FbNNegative", str(sum(1 for r in all_r if r < 0)))
    for model, d in per_model.items():
        t = TAG.get(model)
        if not t or not d["a"]:
            continue
        mac(f"FbPctCausal{t}", f"{np.median(np.array(d['a']) + 0.5 + np.array(d['c'])):.3f}")
        mac(f"FbPctNoncausal{t}", f"{np.median(np.array(d['a']) + 0.5):.3f}")
        mac(f"FbR{t}", f"{np.median(d['r']):+.3f}")
        auth = float(np.median(d["a"]))
        caus = float(np.median(d["c"]))
        mac(f"FbAuthored{t}", f"{auth:+.4f}")
        mac(f"FbCausal{t}", f"{caus:+.4f}")
        if k:
            mac(f"FbAuthoredSteps{t}", f"{auth * k:+.1f}")
            mac(f"FbCausalSteps{t}", f"{caus * k:+.1f}")
        neg = sum(1 for v in d["r"] if v < 0)
        n_c = len(d["r"])
        if n_c >= 2:
            hi = max(neg, n_c - neg)
            pp = min(1.0, 2.0 * sum(comb(n_c, i)
                                    for i in range(hi, n_c + 1))
                     / 2.0 ** n_c)
            mac(f"FbSignP{t}", f"{pp:.3f}")
            mac(f"FbSignNeg{t}", f"{neg}/{n_c}")

    # The mask-rate sentence is generated, not typed: which claim is true
    # depends on whether the two evaluators agree, and that is measured.
    rs = {TAG.get(m): float(np.median(d["r"])) for m, d in per_model.items()
          if TAG.get(m) and d["r"]}
    if len(rs) >= 2:
        vals = list(rs.values())
        same = all(v < 0 for v in vals) or all(v > 0 for v in vals)
        if same:
            mac("FbMaskRateVerdict",
                "They agree in sign, so the reading does not depend on "
                "whether the evaluator saw the mask rates the chain rule "
                "asks it for.")
        else:
            mac("FbMaskRateVerdict",
                "They do not agree in sign, and the mask rate is the "
                "difference between them; the \\textsc{bert} reading has to "
                "be set aside.")


def fb_between_macros(dirpath):
    """The between-set forward/backward reading, from the stored summaries."""
    for name, src in (("sigma", "forward_backward_sigma.json"),
                      ("decomp", "forward_backward_decomposition.json")):
        path = os.path.join(dirpath, src)
        if not os.path.exists(path):
            continue
        d = json.load(open(path))
        if name == "sigma":
            ms = [c["median_all"] for c in d.get("corpora", {}).values()]
            if ms:
                mac("FbBetweenMin", f"{min(ms):.4f}")
                mac("FbBetweenMax", f"{max(ms):.4f}")
                mac("FbBetweenNCorpora", str(len(ms)))
        else:
            if "causal_component" in d:
                mac("FbBetweenCausal", f"{d['causal_component']:+.4f}")
                mac("FbBetweenNNeg", str(d.get("n_causal_component_negative", 0)))


def grid_macros(blk, kinds):
    """What resolution the midrank has, and whether the reading is at it.

    The midrank over n! arrangements lives on a grid of width 1/n!.  With
    n = 4 that is 1/24 = 0.0417, and a causal component of +0.042 is exactly
    one grid step: the smallest non-zero value the statistic can take.  If
    every evaluator returns one or two steps, the measurement is at its
    resolution floor and its magnitude is not informative -- which is what
    the unbounded z decomposition is for.  These macros let the paper state
    that rather than quote +0.042 as though it were a measured size.
    """
    if not blk:
        return
    nperm = {r["n_perms"] for recs in blk.values() for r in recs.values()
             if "n_perms" in r}
    if not nperm:
        return
    k = max(nperm)
    step = 1.0 / k
    mac("GridStep", f"{step:.4f}")
    mac("GridK", str(k))

    ar = [m for m in order_m({m for m, _ in blk}) if kinds.get(m) == "causal"]
    comps, steps, params = [], [], []
    for model in ar:
        c_ = []
        for corpus in order_c({c for _, c in blk}):
            recs = blk.get((model, corpus), {})
            pc = [r["percentile_written"] for q, r in recs.items()
                  if q[0] == "causal"]
            pn = [r["percentile_written"] for q, r in recs.items()
                  if q[0] == "noncausal"]
            if pc and pn:
                c_.append(float(np.median(pc)) - float(np.median(pn)))
        if not c_:
            continue
        v = float(np.median(c_))
        comps.append(v)
        steps.append(round(v / step))
        if PARAMS.get(model):
            params.append(PARAMS[model])
    if not comps:
        return
    mac("CausalCompMin", f"{min(comps):+.3f}")
    mac("CausalCompMax", f"{max(comps):+.3f}")
    mac("CausalCompNEval", str(len(comps)))
    mac("CausalCompStepsMin", str(min(steps)))
    mac("CausalCompStepsMax", str(max(steps)))
    mac("CausalCompNDistinct", str(len(set(steps))))
    # how far the capacity range reaches, so "no trend" has a span attached
    if len(params) >= 2:
        mac("CausalCompCapSpan", f"{max(params) / min(params):.0f}")
        mac("CausalCompCapLo", params_str(
            [m for m in ar if PARAMS.get(m) == min(params)][0]))
        mac("CausalCompCapHi", params_str(
            [m for m in ar if PARAMS.get(m) == max(params)][0]))


def cross_instrument_macros():
    """Deliberately empty.

    This used to form \\AuthoredRatio, the authored component under Delta
    divided by the one under sigma.  The sigma side is the median over the
    masked evaluators, and those two numbers have OPPOSITE SIGNS
    (+0.021 for bert-base, -0.271 for LLaDA), so their median is an average
    of a positive and a negative reading and the ratio formed from it means
    nothing -- it printed 3.  The disagreement between the two evaluators is
    the finding; collapsing it to a median destroys exactly the thing worth
    reporting.  The two components are quoted separately in
    Section~\\ref{sec:fbresult} instead.
    """
    return


def trend_macros(blk, kinds):
    """Does any component of the decomposition track evaluator capacity?

    The paper used to assert that the causal contribution falls as the
    evaluator saturates.  Measured on the autoregressive ladder it does not:
    what rises with capacity is the fraction of texts whose authored order is
    already the extreme arrangement, while the ceiling-free z share is flat.
    These macros put a rank correlation on each component, so the text states
    what was measured rather than what was expected.
    """
    from scipy.stats import spearmanr

    ar = [m for m in order_m({m for m, _ in blk})
          if kinds.get(m) == "causal" and PARAMS.get(m)]
    if len(ar) < 4:
        return
    par = [PARAMS[m] for m in ar]
    series = {}
    for m in ar:
        a_, c_, z_, ceil_ = [], [], [], []
        for corpus in order_c({c for _, c in blk}):
            recs = blk.get((m, corpus), {})
            pc = [r["percentile_written"] for q, r in recs.items()
                  if q[0] == "causal"]
            pn = [r["percentile_written"] for q, r in recs.items()
                  if q[0] == "noncausal"]
            if not pc or not pn:
                continue
            a_.append(float(np.median(pn)) - 0.5)
            c_.append(float(np.median(pc)) - float(np.median(pn)))
            # The midrank cannot reach 1.0: the written arrangement is itself
            # one of the n!, so at least one value ties it and the maximum is
            # 1 - 0.5/n!.  The runner records the real test as is_strict_max,
            # which is what table_saturation uses; comparing the midrank with
            # 1.0 makes the series identically zero and the correlation
            # undefined.
            sm = [r["is_strict_max"] for q, r in recs.items()
                  if q[0] == "causal" and "is_strict_max" in r]
            if sm:
                ceil_.append(float(np.mean(sm)))
            zc = [r["z_written"] for q, r in recs.items() if q[0] == "causal"
                  and np.isfinite(r.get("z_written", np.nan))]
            zn = [r["z_written"] for q, r in recs.items()
                  if q[0] == "noncausal"
                  and np.isfinite(r.get("z_written", np.nan))]
            if zc and zn:
                az = float(np.median(zn))
                cz = float(np.median(zc)) - az
                z_.append(cz / (az + cz) if az + cz > 0 else float("nan"))
        if not a_:
            return
        series.setdefault("authored", []).append(float(np.median(a_)))
        series.setdefault("causal", []).append(float(np.median(c_)))
        series.setdefault("ceiling", []).append(
            float(np.median(ceil_)) if ceil_ else float("nan"))
        zz = [v for v in z_ if np.isfinite(v)]
        series.setdefault("sharez", []).append(float(np.median(zz)) if zz
                                               else float("nan"))

    for key, tag in (("authored", "Authored"), ("causal", "Causal"),
                     ("ceiling", "Ceil"), ("sharez", "ShareZ")):
        y = series.get(key)
        if not y or not np.all(np.isfinite(y)):
            continue
        # Quantise before ranking.  These components are differences of
        # medians on a grid of width 1/n!, so values that are mathematically
        # equal come out of floating point differing in the sixteenth
        # decimal, and a rank correlation turns that noise into an ordering.
        # Measured here the causal component is 1/24 for four of the five
        # autoregressive evaluators; left unrounded it split them into two
        # groups and reported rho = -0.79, against -0.35 for the correct
        # all-tied treatment.  The resolution that makes this necessary is
        # the subject of the section on the grid.
        yq = np.round(np.asarray(y, float), 12)
        rho, pv = spearmanr(par, yq)
        mac(f"Trend{tag}NDistinct", str(len(set(yq.tolist()))))
        mac(f"Trend{tag}Rho", f"{rho:+.2f}")
        mac(f"Trend{tag}P", f"{pv:.3f}")
    mac("TrendNEval", str(len(ar)))
    mac("TrendQuantum", "12")
    mac("TrendCapSpan", f"{max(par) / min(par):.0f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pll", default="../order-intervention/results_pll")
    ap.add_argument("--blkord", default="../order-intervention/results_blkord")
    ap.add_argument("--toy", default="../bert-affinity")
    ap.add_argument("--sigfb", default="../order-intervention/results_sigfb")
    ap.add_argument("--fbjson", default="../order-intervention")
    ap.add_argument("--outdir", default="tables")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    # Delete every table this script owns before writing any of them.  Each
    # table_* function returns early when its measurements are missing, which
    # used to leave whatever was already on disk in place -- a table from an
    # earlier run, or one unpacked from a release tarball -- and the document
    # would then compile with stale numbers and no warning.  A missing table is
    # a build failure one can see; a stale one is not.
    for name in ("tab_blkord.tex", "tab_pll.tex", "tab_token.tex",
                 "tab_capacity.tex", "tab_saturation.tex",
                 "tab_decomposition.tex", "tab_fbrank.tex", "macros.tex"):
        try:
            os.unlink(os.path.join(args.outdir, name))
        except FileNotFoundError:
            pass
    pll, kp = load_cells(args.pll, "pll")
    blk, kb = load_cells(args.blkord, "blkord")
    kinds = {**kp, **kb}
    sig = load_sigfb(args.sigfb)
    print(f"# pll cells: {len(pll)}   blkord cells: {len(blk)}   "
          f"sigfb cells: {len(sig)}")

    table_blkord(blk, kinds, args.outdir)
    table_decomposition(blk, kinds, args.outdir)
    table_saturation(blk, kinds, args.outdir)
    table_pll(pll, kinds, args.outdir)
    table_token(pll, kinds, args.outdir)
    table_capacity(args.toy, args.outdir)
    table_fbrank(args.sigfb, args.outdir)
    fb_between_macros(args.fbjson)
    grid_macros(blk, kinds)
    trend_macros(blk, kinds)
    cross_instrument_macros()
    capacity_ratio_macros()
    selftest_macros(args.blkord)

    # Every macro the prose may reference is defined even when its measurement
    # is not in yet, so the document always compiles; a missing number shows up
    # as a visible TODO instead of an undefined-control-sequence error.
    expected = ["FbNTestsCausal", "FbBonferroni", "FbNSurviving",
                "FbNNominal", "FbNExpected", "FbNTestsDisp",
                "FbDispPMax", "FbDispNSurviving",
                "FbAuthoredStepsBertBase", "FbCausalStepsBertBase",
                "FbAuthoredStepsLLaDA", "FbCausalStepsLLaDA",
                "FbSignPBertBase", "FbSignNegBertBase",
                "FbSignPLLaDA", "FbSignNegLLaDA",
                "TrendAuthoredRho", "TrendAuthoredP",
                "TrendCausalRho", "TrendCausalP",
                "TrendCeilRho", "TrendCeilP",
                "TrendShareZRho", "TrendShareZP",
                "TrendNEval", "TrendCapSpan", "TrendQuantum",
                "TrendCausalNDistinct", "TrendAuthoredNDistinct",
                "TrendCeilNDistinct", "TrendShareZNDistinct",
                "GridStep", "GridK", "CausalCompMin", "CausalCompMax",
                "CausalCompNEval", "CausalCompStepsMin", "CausalCompStepsMax",
                "CausalCompNDistinct", "CausalCompCapSpan",
                "CausalCompCapLo", "CausalCompCapHi",
                "FbNCorpora", "FbNTexts", "FbNCells", "FbDegenTotal",
                "FbRMin", "FbRMax", "FbNNegative", "FbMaskRateVerdict",
                "FbPctCausalBertBase", "FbPctNoncausalBertBase", "FbRBertBase",
                "FbAuthoredBertBase", "FbCausalBertBase",
                "FbPctCausalLLaDA", "FbPctNoncausalLLaDA", "FbRLLaDA",
                "FbAuthoredLLaDA", "FbCausalLLaDA",
                "FbBetweenMin", "FbBetweenMax", "FbBetweenNCorpora",
                "FbBetweenCausal", "FbBetweenNNeg",
                "AuthoredGPTtwoMedium", "CausalGPTtwoMedium",
                "ShareGPTtwoMedium", "ParamsGPTtwoMedium",
                "AuthoredGPTtwoLarge", "CausalGPTtwoLarge",
                "ShareGPTtwoLarge", "ParamsGPTtwoLarge",
                "AuthoredGPTtwoXL", "CausalGPTtwoXL",
                "ShareGPTtwoXL", "ParamsGPTtwoXL",
                "ShareZMin", "ShareZMax", "ShareZNEval",
                "MedPctCausal", "MedPctNoncausal", "PctVsNullP",
                "CausalShareMedian", "CausalShareMin", "CausalShareMax",
                "NBlkordCells", "NBlocks", "NPerms", "NEval", "NCorp", "CapRatioMedian", "CapRatioMin", "CapRatioMax",
                "CapNCorpora", "CapNUp", "SigmaMasked", "SigmaCausal",
                "AuthoredMasked", "CausalCompMasked", "CausalShareMasked",
                "AuthoredCausal", "CausalCompCausal", "CausalShareCausal",
                "BlkRMasked", "BlkNSepMasked", "BlkNTotMasked", "BlkPMaxMasked",
                "BlkPctCMasked", "BlkPctNMasked",
                "BlkRCausal", "BlkNSepCausal", "BlkNTotCausal", "BlkPMaxCausal",
                "BlkPctCCausal", "BlkPctNCausal",
                "NSepMasked", "NTotMasked", "NSepCausal", "NTotCausal",
                # token reversal, reported only in the between-set table
                "SigTokRatioMin", "SigTokRatioMax", "NTokLarger", "NTokCells",
                "NTokNegMasked", "NTokNegMaskedTot",
                "NTokNegAR", "NTokNegARTot",
                "RMaskedLarge", "SigmaMaskedLarge", "NSepMaskedLarge",
                "NTotMaskedLarge",
                "ToyNCap", "ToyDMin", "ToyDMax", "ToyOrdersAbove",
                "ReproMaxErr", "ReproNCorpora",
                "AoarOrderDev", "AoarNormDev",
                "MaskedSpanRatio", "BertSpanRatio", "ARSpanRatio",
                "ScaleCostRatio", "GapSpreadRatio",
                # per-evaluator, for the capacity series in the prose
                "AuthoredBertBase", "CausalBertBase", "ShareBertBase",
                "ParamsBertBase", "CeilBertBase", "CeilNBertBase",
                "AuthoredBertLarge", "CausalBertLarge", "ShareBertLarge",
                "ParamsBertLarge", "CeilBertLarge", "CeilNBertLarge",
                "AuthoredLLaDA", "CausalLLaDA", "ShareLLaDA",
                "ParamsLLaDA", "CeilLLaDA", "CeilNLLaDA",
                "AuthoredGPTtwo", "CausalGPTtwo", "ShareGPTtwo",
                "ParamsGPTtwo", "CeilGPTtwo", "CeilNGPTtwo",
                "AuthoredQwen", "CausalQwen", "ShareQwen",
                "ParamsQwen", "CeilQwen", "CeilNQwen",
                # median r and median median-gap per evaluator; see the note
                # in table_blkord on why both are needed
                "RBertBase", "RBertLarge", "RLLaDA", "RGPTtwo", "RQwen",
                "GapBertBase", "GapBertLarge", "GapLLaDA", "GapGPTtwo",
                "GapQwen",
                "PctCBertBase", "PctCBertLarge", "PctCLLaDA", "PctCGPTtwo",
                "PctCQwen",
                "PctNBertBase", "PctNBertLarge", "PctNLLaDA", "PctNGPTtwo",
                "PctNQwen",
                "RoomBertBase", "RoomBertLarge", "RoomLLaDA", "RoomGPTtwo",
                "RoomQwen",
                # the gap measured against the room left above the non-causal
                # median, with its bootstrap interval
                "RatioBertBase", "RatioBertLarge", "RatioLLaDA", "RatioGPTtwo",
                "RatioQwen",
                "RatioLoBertBase", "RatioHiBertBase",
                "RatioLoBertLarge", "RatioHiBertLarge",
                "RatioLoLLaDA", "RatioHiLLaDA",
                "RatioLoGPTtwo", "RatioHiGPTtwo",
                "RatioLoQwen", "RatioHiQwen",
                "RatioMin", "RatioMax", "RatioNEval", "RatioNCI",
                "RatioOverlapLo", "RatioOverlapHi",
                "RatioWidestLo", "RatioWidestHi",
                "RMasked", "RCausal", "ToySigmaMin", "ToySigmaMax",
                "ToyCapRatio", "ToySigmaAR", "ToyRmsAR", "ToyL", "ToyV",
                "ToyStates", "ToyN"]
    out = [r"% generated by make_tables.py -- do not edit"]
    missing = []
    for k in expected:
        if k in MACROS:
            out.append(f"\\newcommand{{\\{k}}}{{{MACROS[k]}}}")
        else:
            missing.append(k)
            out.append(f"\\newcommand{{\\{k}}}{{\\textbf{{[TODO:{k}]}}}}")
    for k, v in MACROS.items():
        if k not in expected:
            out.append(f"\\newcommand{{\\{k}}}{{{v}}}")
    open(os.path.join(args.outdir, "macros.tex"), "w").write("\n".join(out) + "\n")
    print(f"  macros.tex  ({len(MACROS)} defined"
          + (f", {len(missing)} still TODO: {', '.join(missing)}" if missing else "")
          + ")")

    # Any table whose measurements were missing does not exist now, because
    # everything this script owns was deleted above.  Write a visible stub for
    # it rather than leaving the \input dangling: the document still compiles
    # while a run is in progress, and the stub carries a TODO marker that
    # make_arxiv.sh refuses to package.
    for name in ("tab_blkord.tex", "tab_pll.tex", "tab_token.tex",
                 "tab_capacity.tex", "tab_saturation.tex",
                 "tab_decomposition.tex"):
        path = os.path.join(args.outdir, name)
        if os.path.exists(path):
            continue
        stem = name[:-4].replace("_", r"\_")
        open(path, "w").write(
            "% generated by make_tables.py -- no measurements for this table\n"
            "\\begin{tabular}{l}\n\\toprule\n"
            f"\\textbf{{[TODO:{stem}]}} no measurements for this table \\\\\n"
            "\\bottomrule\n\\end{tabular}\n")
        print(f"  {name}  STUB -- no measurements")


if __name__ == "__main__":
    main()
