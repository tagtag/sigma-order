#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate every table AND every number quoted in the prose, as LaTeX.

Nothing numeric in this paper is typed by hand.  Tables are written as
\\input-able fragments, and each figure quoted in the running text becomes a
macro in macros.tex, so the sentence reads

    causality accounts for \\CausalRatioOpus of the effect

and cannot drift from the measurement.  Rerunning the measurement and this
script updates the prose.

Outputs (into --outdir):
    macros.tex        \\newcommand for each quoted figure
    tab_blkord.tex    within-text permutation set, the decisive table
    tab_pll.tex       evaluator comparison, sigma and effect size
    tab_capacity.tex  toy-system capacity sweep

    python3 make_tables.py --pll ../order-intervention/results_pll \\
        --blkord ../order-intervention/results_blkord \\
        --toy ../bert-affinity --outdir tables
"""

import argparse
import glob
import itertools
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np
from math import comb
from scipy.stats import mannwhitneyu, wilcoxon

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

EXACT_MAX_N = 8          # 8! = 40320 dot products, under a second


def spearman(x, y):
    """Spearman rho, with an EXACT two-sided p-value at small n.

    ``scipy.stats.spearmanr`` returns a p-value from the t-approximation at
    every sample size.  Every correlation this paper reports is at n = 5 --
    five autoregressive evaluators on the ladder, five widths in the
    capacity sweep -- and at n = 5 the smallest two-sided p an exact test
    can produce is 2/5! = 0.0167.  The asymptotic form returned 0.005 for
    the ceiling trend, a value that is not attainable, and the exact figure
    is 0.033.

    rho is Pearson on midranks, which is Spearman with the usual tie
    correction.  Under the null the two rank vectors are independent, so the
    null distribution of rho is its distribution over the n! relabellings of
    one of them; the denominator is invariant under those, so only the
    numerator has to be recomputed.  Returns (rho, p, exact).
    """
    from scipy.stats import rankdata, spearmanr
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    n = len(x)
    rx = rankdata(x)
    ry = rankdata(y)
    rx = rx - rx.mean()
    ry = ry - ry.mean()
    den = math.sqrt(float((rx ** 2).sum()) * float((ry ** 2).sum()))
    if den == 0:                      # one side constant: rho undefined
        return float("nan"), 1.0, True
    rho = float((rx * ry).sum() / den)
    if n > EXACT_MAX_N:
        return rho, float(spearmanr(x, y).pvalue), False
    perms = np.array(list(itertools.permutations(range(n))))
    rhos = (rx * ry[perms]).sum(axis=1) / den
    p = float(np.mean(np.abs(rhos) >= abs(rho) - 1e-12))
    return rho, p, True


def _lt(text, thr):
    """A macro body compared with a threshold, tolerating a TODO."""
    try:
        return float(text) < thr
    except (TypeError, ValueError):
        return False


def exact_p_floor(n):
    """The smallest two-sided p the exact rank null can return at this n."""
    return 2.0 / math.factorial(n)


# Measurements this file emits that the prose deliberately does not
# quote.  An orphan NOT on this list is a number the text dropped,
# and check_paper.py fails on one: that is how \BlkNSepCausal came
# to sit unused while three sentences asserted what it counts, and
# how \TailSweepLoSixty sat unused while Section 5.3 claimed to
# report the whole sweep.  A warning listing a hundred names is not
# a check; this list is the declaration that makes one possible.
RETIRED = (
    # the gap-to-room ratio: Section 5.4 withdrew the claim that the room
    # closes, and the analysis went with it.  The columns are still in
    # tab_saturation and the values still in the JSON.
    "GapGPTtwo", "GapQwen", "GapSpreadRatio", "PctCGPTtwo", "PctCQwen",
    "PctNGPTtwo", "PctNQwen", "RCausal", "RGPTtwo", "RQwen", "RatioGPTtwo",
    "RatioHiGPTtwo", "RatioHiQwen", "RatioLoGPTtwo", "RatioLoQwen",
    "RatioMax", "RatioMin", "RatioNCI", "RatioOverlapHi",
    "RatioOverlapLo", "RatioQwen", "RatioWidestHi", "RatioWidestLo",
    # the pseudo-log-likelihood comparison, withdrawn in Section 3.2 and
    # retained in the repository (Section 8).
    "ARSpanRatio", "BlkNSepMasked", "BlkNTotMasked", "BlkPBestMasked",
    "BlkPctCMasked", "BlkPctNMasked", "BlkRMasked", "ParamsBertLarge",
    # the ceiling rise, withdrawn with the saturation argument.
    "CeilRise", "CeilRiseUnits",
    # the single-evaluator between-set macros.  forward_backward_sigma.json
    # is one model; the reading is now generated per evaluator from
    # results_sigfb, where both are.  The file and its generator stay: the
    # cross-check they carry on FbNCorpora still runs.
    "FbBetweenMin", "FbBetweenMax", "FbBetweenNCorpora",
    "FbBetweenCausal", "FbBetweenNNeg",
    # the threshold sweep, printed as tab_sweep rather than quoted.
    "TailSweepHiEighty", "TailSweepHiFifty", "TailSweepHiNinety",
    "TailSweepHiNinetyFive", "TailSweepHiSeventy", "TailSweepHiSixty",
    "TailSweepLoEighty", "TailSweepLoFifty", "TailSweepLoNinety",
    "TailSweepLoNinetyFive", "TailSweepLoSeventy", "TailSweepLoSixty",
    # per-evaluator values whose table already prints the column; the prose
    # quotes the two ends of the ladder and the median.
    "CausalGPTtwoLarge", "CausalGPTtwoMedium", "CausalGPTtwoXL",
    "ShareGPTtwo", "ShareGPTtwoLarge", "ShareGPTtwoMedium",
    "ShareGPTtwoXL", "ShareQwen", "TailDiffGPTtwoLarge",
    "TailDiffGPTtwoMedium", "TailDiffGPTtwoXL",
    # counts and diagnostics the prose states as a rule instead of a number.
    "NBlkordCells", "ShareEvalNEval", "ShareZNEval", "TailTrendNEval",
    # withdrawn: a sign test over cells that are not independent draws
    "TailSignP",
    "TrendAuthoredNDistinct", "TrendAuthoredZNDistinct",
    "TrendCeilNDistinct", "TrendCeilNNDistinct", "TrendShareZNDistinct",
    "TrendSignificantIs",
    # sigma detail per evaluator; Section 6 quotes the pair it compares.
    "CtrlSigMax", "CtrlSigMeanAbs",
    "CtrlSigMedian", "CtrlSigMin", "CtrlSigmaHead",
    # FbCausalBertBase, FbCausalLLaDA and their step forms came off this
    # list with #166: Section 6.3 now gives both readings' causal
    # components side by side, to show that they agree in direction and
    # are not in the same units.
    "FbDispNSurviving", "FbDispPMax",
    "FbDispPMaxBertBase", "FbPctCausalBertBase",
    "FbPctCausalLLaDA", "FbPctNoncausalBertBase", "FbPctNoncausalLLaDA",
    "FbRBertBase", "FbRLLaDA", "FbRMin", "ToyCapMonotone",
    # FbRMax came off this list when Section 6.3 began naming the one
    # cell where r is positive (#173).  The retirement was right while
    # the prose only said "one cell below".
    # The same per-evaluator values for the three middle rungs.  The prose
    # quotes the two ends of the ladder and the median, so every middle-rung
    # macro is retired by construction; they are listed rather than matched
    # by pattern so that one the prose does start using shows up as a stale
    # retirement rather than being silently covered.
    "CeilGPTtwoLarge", "CeilGPTtwoMedium", "CeilGPTtwoXL",
    "CeilNGPTtwoLarge", "CeilNGPTtwoMedium", "CeilNGPTtwoXL",
    "GapGPTtwoLarge", "GapGPTtwoMedium", "GapGPTtwoXL",
    "PctCGPTtwoLarge", "PctCGPTtwoMedium", "PctCGPTtwoXL",
    "PctNGPTtwoLarge", "PctNGPTtwoMedium", "PctNGPTtwoXL",
    "RGPTtwoLarge", "RGPTtwoMedium", "RGPTtwoXL",
    "RatioGPTtwoLarge", "RatioGPTtwoMedium", "RatioGPTtwoXL",
    "RatioHiGPTtwoLarge", "RatioHiGPTtwoMedium", "RatioHiGPTtwoXL",
    "RatioLoGPTtwoLarge", "RatioLoGPTtwoMedium", "RatioLoGPTtwoXL",
    "RoomGPTtwoLarge", "RoomGPTtwoMedium", "RoomGPTtwoXL",
    # counts behind the causal/authored ratio, which the prose states as a
    # range rather than a tally
    "CausalRatioNPos", "CausalRatioNTot",
    # Delta detail the decomposition tables print.
    "AuthoredCausal", "BlkNSepCausal", "BlkNTotCausal", "BlkPBestCausal",
    "BlkPctCCausal", "BlkPctNCausal", "BlkRCausal", "CausalCompCapHi",
    "CausalCompCapLo", "CausalCompCapSpan", "CausalCompCausal",
    "CausalCompMax", "CausalCompMin", "CausalRatioCausal",
    "CausalRatioMax", "CausalRatioMedian", "CausalRatioMin",
    "ContrastPBest", "NSepCausal", "NTotCausal", "PctVsNullP",
    "SigmaCausal", "TailZPMax",
)


# The other half of a withdrawal.  RETIRED above is the macros, and the
# orphan check makes that half impossible to leave undone.  This is the
# prose, which had no list and no check: \texttt{bert-large} outlived the
# retirement of \ParamsBertLarge by weeks, "pseudo-log-likelihood" kept six
# mentions of a comparison that needed one, and "flat" went on describing a
# series the data had stopped supporting.
#
#   word -> (budget, the withdrawal it belongs to, why that budget)
#
# The budget is not always zero.  A withdrawal worth recording needs the
# record, and the question that went unasked was how many times.  A budget
# of None means the word has a check of its own; it is listed here so one
# place holds the whole of what a withdrawal removed.
WITHDRAWN_FROM_PROSE = {
    "bert-large": (
        0, "the pseudo-log-likelihood comparison",
        "it was in this paper only for that comparison"),
    "pseudo-log-likelihood": (
        1, "the pseudo-log-likelihood comparison",
        "the appendix normalises exp of it as one of three candidate "
        "joints, which is the only place the quantity is computed"),
    "flat": (
        None, "the saturation argument",
        "check_flat_sense() carries this one: the word is permitted only "
        "in the negative, which a count cannot express"),
}


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


def _check_macro_name(name):
    """A control sequence may contain letters only.

    \\TailSweepLo50 was emitted for six thresholds and the document stopped
    with "Missing \\begin{document}" pointing at macros.tex -- a long way
    from the loop that wrote it.  Refusing the name here names the loop.
    """
    if not name.isalpha():
        raise ValueError(
            f"macro name {name!r} is not all letters; LaTeX control "
            f"sequences take letters only, so spell digits out "
            f"(TailSweepLoFifty, not TailSweepLo50)")


def mac(name, value):
    _check_macro_name(name)
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


def corpus_base(name):
    """The bare corpus name.

    The masked runs key cells by meta.corpus, which carries a
    "fixed_text_" prefix, and CORPUS_ORDER lists the bare names.  Testing
    membership on the full string put every masked corpus in order_c's
    alphabetical tail, so the masked tables ran F, GPT54, GPT56, Gemini31,
    O while every autoregressive table ran O, GPT54, GPT56, Gemini31, F --
    invisibly, because the tables print the stripped name either way.
    """
    return name[len("fixed_text_"):] if name.startswith("fixed_text_") \
        else name


def order_c(names):
    known = sorted((n for n in names if corpus_base(n) in CORPUS_ORDER),
                   key=lambda n: CORPUS_ORDER.index(corpus_base(n)))
    return known + sorted(n for n in names
                          if corpus_base(n) not in CORPUS_ORDER)


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
    """Parameter count as it should read in a table cell or a panel title.

    One decimal above 1000M, with a trailing zero stripped: 1.6B, not the
    1B integer division used to give.  \\Params<Tag> was fixed for this and
    this was not, which is the usual consequence of two formatters.
    """
    p = PARAMS.get(model)
    if not p:
        return "?"
    if p < 1000:
        return f"{p}M"
    return f"{p / 1000:.1f}".rstrip("0").rstrip(".") + "B"


def rb(a, b):
    if len(a) < 2 or len(b) < 2:
        return np.nan, np.nan
    st = mannwhitneyu(a, b, alternative="two-sided", method="asymptotic")
    return 2.0 * st.statistic / (len(a) * len(b)) - 1.0, float(st.pvalue)


def ar_only(models, kinds):
    """The autoregressive evaluators, in order.

    The Delta instrument reports only these.  A masked evaluator can be run
    through it, and three were while the paper used a pseudo-log-likelihood,
    but PLL is not the logarithm of anything and the paper no longer reports
    it: those rows would be measurements of a quantity the text disowns.
    They stay in results_blkord/ as the record of what was tried, and are
    filtered out here, at the one place every Delta table draws its
    evaluators from.  The masked evaluators appear in their own table,
    through the forward and backward chain rule, which IS a log-probability
    (table_fbrank).
    """
    return [m for m in order_m(models) if kinds.get(m) == "causal"]


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
    mac("NEval", str(len(ar_only({m for m, _ in blk}, kinds))))
    mac("NCorp", str(len({c for _, c in blk})))
    # Equation (rb) names n_1 and n_2 and the paper never gave their
    # values.  They are in the measurements.  Define the macro only if
    # every cell agrees, on the rule enumeration_macros() uses for the
    # block count: a disagreement would make the sentence false, and an
    # undefined macro prints as a TODO that make_arxiv.sh refuses.
    sizes = set()
    for recs in blk.values():
        for cat in ("causal", "noncausal"):
            sizes.add(sum(1 for q in recs if q[0] == cat))
    sizes.discard(0)
    if len(sizes) == 1:
        mac("NPerGroup", str(sizes.pop()))
    else:
        print(f"  WARNING: label groups differ in size {sorted(sizes)}; "
              f"the sentence giving n_1 = n_2 is false as written")
    models = ar_only({m for m, _ in blk}, kinds)
    corpora = order_c({c for _, c in blk})
    lines = [
        r"% generated by make_tables.py -- do not edit",
        r"\begin{tabular}{llrrrrr}",
        r"\toprule",
        r"evaluator & corpus & $n$ & causal & non-causal & $r$ & $p$ \\",
        r"\midrule",
    ]
    ratios_ = {}
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
            # authored order.  This divides by the AUTHORED component, so it
            # is how large the causal part is relative to that -- a ratio.
            # table_decomposition's "share" divides by the total instead,
            # which is what a share is.  Both were called share, and the two
            # names then stood side by side in the abstract reading as a
            # contradiction (10-19% against -8% to +40%).
            coh = mn - 0.5
            ratios_[(model, corpus)] = (mc - mn) / coh if coh else np.nan
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

    # prose numbers.  Autoregressive evaluators only, and paired within a
    # corpus, like every other Delta figure: this used to run over every
    # model in blk, so it pooled the masked runs that ar_only() exists to
    # keep out, and pooled texts rather than taking the median of the
    # per-corpus medians that Section 3.4 states as the rule.
    ar_models = ar_only({m for m, _ in blk}, kinds)
    percorpus_c, percorpus_n = [], []
    for model in ar_models:
        for corpus in order_c({c for _, c in blk}):
            recs = blk.get((model, corpus), {})
            pc = [r["percentile_written"] for k, r in recs.items()
                  if k[0] == "causal"]
            pn = [r["percentile_written"] for k, r in recs.items()
                  if k[0] == "noncausal"]
            if pc and pn:
                percorpus_c.append(float(np.median(pc)))
                percorpus_n.append(float(np.median(pn)))
    allpc, allpn = percorpus_c, percorpus_n
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
            # NOT emitted as BlkPMax{tag}: pmin is a MINIMUM, the name
            # said maximum, the p tests the causal group against the 0.50
            # null rather than the two groups against each other, and the
            # loop computes it for one model per tag.  Three sentences
            # quoted it for "present in every corpus and evaluator".
            # contrast_macros() measures that claim instead.
            mac(f"BlkPBest{tag}", tex_p_bare(pmin))
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

    if ratios_:
        v = np.array([s for s in ratios_.values() if np.isfinite(s)])
        if len(v):
            mac("CausalRatioMedian", f"{100*np.median(v):.0f}")
            mac("CausalRatioMin", f"{100*v.min():+.0f}")
            mac("CausalRatioMax", f"{100*v.max():+.0f}")
            mac("NBlkordCells", str(len(ratios_)))
            mac("CausalRatioNPos", str(int((v > 0.05).sum())))
            mac("CausalRatioNTot", str(len(v)))
    print(f"  tab_blkord.tex  ({len(ratios_)} cells)")


# -------------------------------------------------------------- pll
def capacity_scale_macros(blk, kinds):
    """How far the magnitude of Delta moves with the evaluator.

    Measured between the two ends of the autoregressive ladder, on the
    authored arrangement of the same texts.  The source is results_blkord/,
    not results_pll/: the published between-set protocol was run on three
    evaluators only, of which one is autoregressive, so results_pll/ has no
    ladder in it.  The enumeration run has all five, and sigma_written is the
    same quantity -- [log P(x) - log P(x reversed)] / L for the arrangement a
    writer chose.

    Magnitudes, because a ratio of signed medians would hide a sign change
    instead of showing it.  CapNSign counts the corpora whose sign differs
    between the two ends, so a reader can see whether the ratio is taken
    between two like-signed numbers.
    """
    models = ar_only({m for m, _ in blk}, kinds)
    if len(models) < 2:
        return
    lo, hi = models[0], models[-1]
    ratios, nsign, mlo, mhi = [], 0, [], []
    for corpus in order_c({c for _, c in blk}):
        a = blk.get((lo, corpus))
        b = blk.get((hi, corpus))
        if not a or not b:
            continue
        ma = float(np.median([r["sigma_written"] for r in a.values()]))
        mb = float(np.median([r["sigma_written"] for r in b.values()]))
        if ma == 0.0:
            continue
        mlo.append(ma)
        mhi.append(mb)
        ratios.append(abs(mb) / abs(ma))
        nsign += int((ma > 0) != (mb > 0))
    if not ratios:
        return
    mac("CapRatioMedian", f"{np.median(ratios):.2f}")
    mac("CapRatioMin", f"{min(ratios):.2f}")
    mac("CapRatioMax", f"{max(ratios):.2f}")
    mac("CapNCorpora", str(len(ratios)))
    mac("CapNUp", str(int(sum(r > 1 for r in ratios))))
    mac("CapNSign", str(nsign))
    mac("CapDeltaLo", f"{np.median(mlo):+.4f}")
    mac("CapDeltaHi", f"{np.median(mhi):+.4f}")


def table_pll(pll, kinds, outdir):
    if not pll:
        return
    models = ar_only({m for m, _ in pll}, kinds)
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

    # The published evaluator, read on its own.  The two masked arms of this
    # loop (bert-base, bert-large) produced \SigmaMasked and \RMasked, which
    # the prose set beside the autoregressive ones; that comparison is
    # withdrawn together with the quantity it compared.
    for tag, model in (("Causal", "gpt2"),):
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
    models = ar_only({m for m, _ in pll}, kinds)
    corpora = order_c({c for _, c in pll})
    lines = [
        r"% generated by make_tables.py -- do not edit",
        r"\begin{tabular}{llrrrr}",
        r"\toprule",
        # The block median goes in beside the token one.  The caption
        # compares the two and printed only one of them, which sent a
        # reader to Table 3 and fourteen pages away to divide.
        r"evaluator & corpus & $n$ & median $\Delta_{\mathrm{token}}$ & "
        r"median $\Delta_{\mathrm{block}}$ & $r$ \\",
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
            if abs(t_med) > abs(b_med):
                larger += 1
                # Only here.  The prose quotes this range for the cells in
                # which the token median IS the larger; computed over every
                # cell it would start below 1 under the word "larger".
                if abs(b_med) > 1e-9:
                    ratio.append(abs(t_med) / abs(b_med))
            k = kind_str(kinds.get(model))
            neg[k][1] += 1
            if np.isfinite(t_rb) and t_rb < 0:
                neg[k][0] += 1
            cells += 1
            name = (f"{model.split('/')[-1]} ({params_str(model)}, "
                    f"{kind_str(kinds.get(model))})") if first else ""
            first = False
            # In math mode, like every other generated table: outside it
            # a negative value prints a hyphen, and Table 1 sits beside
            # Table 3 where the same number carries a minus.
            rcol = f"${t_rb:+.3f}$" if np.isfinite(t_rb) else "--"
            lines.append(f"{name} & {corpus} & {len(tall)} & "
                         f"${t_med:.4f}$ & ${b_med:.4f}$ & {rcol} \\\\")
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
            "ARSpanRatio": ("Qwen/Qwen3-4B-Base", "gpt2"),
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
            # Section 3.2 argues about a model whose conditionals belong to
            # NO joint, and quoted the normalisation measured on a
            # consistent oracle.  This is the same check on deliberately
            # inconsistent conditionals, which is the case the section is
            # about.
            if "max_abs_norm_dev_inconsistent" in d:
                mac("AoarNormDevInc",
                    tex_sci(d["max_abs_norm_dev_inconsistent"], 1))
            # The system THIS test runs on.  The prose reached for the
            # appendix's \ToyStates when it first described it, which is a
            # different system entirely.
            for k, name in (("L", "AoarL"), ("V", "AoarV"),
                            ("n_states", "AoarStates"),
                            ("n_orders", "AoarNOrders")):
                if k in d:
                    mac(name, str(d[k]))
            return


def table_bayes_route(toy_dir, outdir):
    """The control that separates the model from the route.

    Equation (11)'s rate needs p_theta(. | x_{-k}).  A masked model emits it;
    an autoregressive model has no head that does, so for that class it is
    recovered from the joint.  The capacity table therefore uses two
    different constructions on its two kinds of row, which is forced -- one
    class has no second option -- but leaves open whether a non-zero reading
    belongs to the model or to the construction.

    bayes_route_control.py gives one masked model both routes at every width
    of the capacity sweep, and this reads the result.
    """
    p = os.path.join(toy_dir or "", "bayes_route_control.json")
    if not os.path.isfile(p):
        return
    rows = json.load(open(p)).get("rows") or []
    if not rows:
        return
    lines = [
        r"% generated by make_tables.py -- do not edit",
        r"\begin{tabular}{rrrrrcr}",
        r"\toprule",
        r" & & & \multicolumn{2}{c}{$\sigEP$} & & \\",
        r"\cmidrule(lr){4-5}",
        r"$d$ & params & loss & emitted & recovered & "
        r"$J(\text{emitted} \,\|\, \text{recovered})$ & "
        r"$\langle|\sigma|\rangle$ \\",
        r"\midrule",
    ]
    for r in rows:
        jr = r["joint_routes"]
        jmax = max(abs(q["sigma"]) for q in jr)
        jeff = [q["jeffreys_vs_head"] for q in jr]
        lines.append(
            f"{r['d']} & {r['params']} & {r['final_loss']:.4f} & "
            f"{r['head']['sigma']:.4f} & ${tex_sci(jmax)}$ & "
            f"{min(jeff):.2f}--{max(jeff):.2f} & "
            f"{r['sigma_l2r_r2l']['mean_abs']:.4f} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(outdir, "tab_bayesroute.tex"), "w").write(
        "\n".join(lines) + "\n")

    top = rows[-1]
    jr = top["joint_routes"]
    mac("CtrlNWidths", str(len(rows)))
    mac("CtrlDMin", str(rows[0]["d"]))
    mac("CtrlDMax", str(top["d"]))
    mac("CtrlSigmaHead", f"{top['head']['sigma']:.4f}")
    mac("CtrlSigmaJointMax",
        tex_sci(max(abs(q["sigma"]) for r in rows for q in r["joint_routes"])))
    jeff = [q["jeffreys_vs_head"] for q in jr]
    mac("CtrlJeffreysMin", f"{min(jeff):.2f}")
    mac("CtrlJeffreysMax", f"{max(jeff):.2f}")
    # The level of <|sigma|> at every width, not just the widest.  Section
    # 6.3 argued that the incompatible regime is not being left behind, and
    # supported it with sigma_EP's rise -- which is the one inference
    # Appendix A forbids: the sweep shows no relation between the two, which
    # at that n is not the same as showing they move apart.
    # The supportable form is sigma's own readings: if none of them is small,
    # the sweep shows nothing heading for zero.
    allsig = [r["sigma_l2r_r2l"]["mean_abs"] for r in rows]
    mac("CtrlSigAbsMin", f"{min(allsig):.4f}")
    mac("CtrlSigAbsMax", f"{max(allsig):.4f}")
    sg = top["sigma_l2r_r2l"]
    mac("CtrlSigMedian", f"{sg['median']:+.4f}")
    mac("CtrlSigMeanAbs", f"{sg['mean_abs']:.4f}")
    mac("CtrlSigMin", f"{sg['min']:+.4f}")
    mac("CtrlSigMax", f"{sg['max']:+.4f}")

    # Do the two instruments move together across the sweep?  Neither is a
    # transform of the other, so this is a check that they are sensitive to
    # one property, not a claim about the relation between their sizes.
    if len(rows) > 2:
        d = [r["d"] for r in rows]
        se = [r["head"]["sigma"] for r in rows]
        sg2 = [r["sigma_l2r_r2l"]["mean_abs"] for r in rows]
        for tag, a, b in (("EP", d, se), ("Sig", d, sg2), ("XS", se, sg2)):
            rho, pv, _ = spearman(a, b)
            mac(f"CtrlRho{tag}", f"{rho:+.2f}")
            mac(f"CtrlP{tag}", f"{pv:.3f}")
        # \CtrlNWidths already carries this n; a second spelling of the same
        # number is how two of them drift apart.
        mac("CtrlPFloor", f"{exact_p_floor(len(rows)):.3f}")
    print(f"  tab_bayesroute.tex  ({len(rows)} widths)")


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
        # Endpoints, not max over min.  The prose says "from d = 32 to
        # d = 160", and max/min answered a different question: the sweep is
        # not monotone -- it dips at the second width -- so the smallest
        # value is not the one at the smallest model, and max/min (4.1)
        # overstated what the capacity trend supports (3.5).
        bywidth = sorted(mlm, key=lambda r: r["d"])
        mac("ToyCapRatio",
            f"{bywidth[-1]['sigma'] / bywidth[0]['sigma']:.1f}")
        mac("ToyCapMonotone",
            "yes" if all(bywidth[i]["sigma"] <= bywidth[i + 1]["sigma"]
                         for i in range(len(bywidth) - 1)) else "no")
        mac("ToySpanRatio",
            f"{max(r['sigma'] for r in mlm) / min(r['sigma'] for r in mlm):.1f}")
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
    models = ar_only({m for m, _ in blk}, kinds)
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
    # How many texts each ceiling fraction is a fraction OF.  Section 5.4
    # rests its saturation claim on this fraction rising 32% -> 40%, having
    # withdrawn the authored component's rise because one grid step is not a
    # measured size.  The same question has to be asked of the replacement:
    # a fraction over n texts moves in units of 1/n, and a rise of 8 points
    # is only evidence if 8 points is several of those units.  Measuring it
    # is the point -- asserting that a proportion "has no grid" would be the
    # same mistake in a new place.
    ceil_n = []
    for model in models:
        fc, fn, gaps, per_corpus = [], [], [], []
        for corpus in corpora:
            recs = blk.get((model, corpus), {})
            c = [r["is_strict_max"] for k, r in recs.items() if k[0] == "causal"]
            n = [r["is_strict_max"] for k, r in recs.items() if k[0] == "noncausal"]
            if c:
                fc.append(float(np.mean(c)))
                ceil_n.append(len(c))
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
        # params_str, not a second formatter: p//1000 printed 1B for
        # gpt2-xl in this table while every other one printed 1.6B, and
        # the 13-fold span quoted in Section 3.1 is 1.6B/124M.
        ps = "--" if not p else params_str(model)
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
    # This column is a median of \\NCorp per-corpus ratios, so it can only
    # take one of those \\NCorp values and its bootstrap interval can only
    # have endpoints among them.  That is a grid, and this paper refuses
    # every other grid-bound number the status of a measured size, so the
    # same question is asked here and the answer is printed.
    if all_ratios:
        mac("RatioNDistinct", str(len({f"{r:.2f}" for r in all_ratios})))
        # RatioNEval is emitted below with the same expression; emitting it
        # twice is how a macro ends up both retired and in use.
    if all_ci:
        ends = {f"{v:.2f}" for lo, hi in all_ci for v in (lo, hi)}
        mac("RatioNDistinctEnds", str(len(ends)))
        mac("RatioNAtEnd", str(sum(
            1 for r, (lo, hi) in zip(all_ratios, all_ci)
            if f"{r:.2f}" in (f"{lo:.2f}", f"{hi:.2f}"))))
    # The span and the common overlap, so the prose never has to name which
    # evaluator sits at an extreme: a superlative typed by hand goes stale the
    # moment the measurements change, and two of them already had.
    # The ceiling fraction's own resolution, by the same test Section 5.3
    # applies to the midrank.  CeilRiseUnits is the 32% -> 40% rise expressed
    # in units of 1/n: if it comes out near 1 the replacement evidence is in
    # the same condition as the component it replaced, and Section 5.4 would
    # have to say so.
    if ceil_n:
        nmin = min(ceil_n)
        mac("CeilNTexts", str(nmin))
        mac("CeilResolution", f"{100.0 / nmin:.1f}")
        lo_t, hi_t = TAG.get(models[0]), TAG.get(models[-1])
        if lo_t and hi_t and f"Ceil{lo_t}" in MACROS and f"Ceil{hi_t}" in MACROS:
            rise = float(MACROS[f"Ceil{hi_t}"]) - float(MACROS[f"Ceil{lo_t}"])
            mac("CeilRise", f"{rise:.0f}")
            mac("CeilRiseUnits", f"{rise / (100.0 / nmin):.1f}")
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
    models = ar_only({m for m, _ in blk}, kinds)
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
    got, gotz, swapped, n_over = {}, {}, {}, []
    for model in models:
        a_, c_, az_, cz_ = [], [], [], []
        as_, cs_ = [], []            # the same two with the labels exchanged
        for corpus in corpora:
            recs = blk.get((model, corpus), {})
            pc = [r["percentile_written"] for k, r in recs.items() if k[0] == "causal"]
            pn = [r["percentile_written"] for k, r in recs.items() if k[0] == "noncausal"]
            if not pc or not pn:
                continue
            a_.append(float(np.median(pn)) - 0.5)
            c_.append(float(np.median(pc)) - float(np.median(pn)))
            # The same decomposition with the two labels exchanged.  The
            # paper claimed Eq. (8) is "independent of whether the labelling
            # is correct", which is not so: Eq. (8) SELECTS the non-causal
            # set, and selecting the other set is a different number.  Both
            # sets are authored, so either choice yields an authored
            # component, and the difference between the two choices is
            # exactly Eq. (9).  Measuring the swap lets the paper say that
            # from a number instead of asserting an independence it does
            # not have -- and the swapped share comes out negative, which
            # is the plainest way to show the quantity is not label-free.
            as_.append(float(np.median(pc)) - 0.5)
            cs_.append(float(np.median(pn)) - float(np.median(pc)))
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
        # A share above 100% would mean a negative authored component.  The
        # caption used to explain that case; it does not occur, and a
        # caption explaining an absent row sends the reader looking for it.
        # The explanation lives here instead, and this macro counts the
        # rows that would need it -- so if one ever appears, the number
        # stops being zero and the omission is visible.
        if share > 1.0 or auth < 0:
            n_over.append(model)
        got[model] = (auth, caus, share)
        if as_ and cs_ and kinds.get(model) == "causal":
            a2, c2 = float(np.median(as_)), float(np.median(cs_))
            t2 = a2 + c2
            swapped[model] = (a2, c2, c2 / t2 if t2 else float("nan"))
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
                mac(f"CausalRatio{tag}", f"{100*share:.0f}")
    # The z decomposition has no ceiling and no grid, so its share is the
    # one to quote when the midrank share sits at the statistic's resolution.
    zsh = [v for v in gotz.values() if np.isfinite(v)]
    if zsh:
        mac("ShareZMin", f"{100 * min(zsh):.0f}")
        mac("ShareZMax", f"{100 * max(zsh):.0f}")
        mac("ShareZNEval", str(len(zsh)))

    # Do the two normalisations agree evaluator by evaluator?  The caption
    # said their agreement was what showed the midrank's ceiling was not
    # driving the split.  They do not agree: measured, the rank correlation
    # between the two share columns is negative and one evaluator differs by
    # more than a factor of two.  What the two forms do share is the range,
    # and that is the claim the ceiling argument needs.
    pair = [(got[m][2], gotz[m]) for m in got
            if m in gotz and np.isfinite(got[m][2]) and np.isfinite(gotz[m])]
    if len(pair) > 2:
        rho, pv, _ = spearman([a for a, _ in pair], [b for _, b in pair])
        mac("ShareFormRho", f"{rho:+.2f}")
        mac("ShareFormP", f"{pv:.3f}")
        mac("ShareFormNEval", str(len(pair)))
        worst = max(pair, key=lambda t: max(t) / min(t) if min(t) > 0 else 0)
        if min(worst) > 0:
            mac("ShareFormWorst", f"{max(worst) / min(worst):.1f}")
    # The range of the per-evaluator share.  The prose said "a tenth to a
    # fifth" in three places, in words, which is a ratio spelled out in prose
    # -- the thing this file exists to avoid.  It also sat next to the range
    # over the individual (evaluator, corpus) cells, and the two read as a
    # contradiction rather than as two levels of aggregation.
    if n_over:
        print("  WARNING: share above 100% (negative authored component) "
              "for " + ", ".join(n_over) + " -- Table 2's caption says "
              "nothing about this case because it did not occur; it does "
              "now and the caption needs a line.")
    ev = [share for (_, _, share) in got.values() if np.isfinite(share)]
    if ev:
        mac("ShareEvalMin", f"{100 * min(ev):.0f}")
        mac("ShareEvalMax", f"{100 * max(ev):.0f}")
        mac("ShareEvalNEval", str(len(ev)))

    # What the decomposition becomes if the two labels are exchanged.  The
    # paper described Eq. (8) as independent of the labelling; it is not,
    # and the size of the dependence is this.  One evaluator is quoted in
    # full so a reader can check the arithmetic, and the range of the
    # swapped share is given because its sign changes, which no
    # label-independent quantity does.
    if swapped:
        lo_m = [m for m in order_m(set(swapped)) ][0]
        a2, c2, s2 = swapped[lo_m]
        a1, c1, s1 = got[lo_m]
        mac("SwapEval", lo_m.split("/")[-1].replace("_", r"\_"))
        mac("SwapAuthored", f"{a2:+.3f}")
        mac("SwapCausal", f"{c2:+.3f}")
        mac("SwapAuthoredOrig", f"{a1:+.3f}")
        mac("SwapCausalOrig", f"{c1:+.3f}")
        sw = [q for (_, _, q) in swapped.values() if np.isfinite(q)]
        if sw:
            mac("SwapShareMin", f"{100 * min(sw):.0f}")
            mac("SwapShareMax", f"{100 * max(sw):.0f}")
            mac("SwapShareNNeg", str(sum(1 for q in sw if q < 0)))
            mac("SwapShareNEval", str(len(sw)))

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
        # The grid is 1/2n!, not 1/n!: Eq.(midrank) counts the authored
        # arrangement's tie with itself as a half, so 2 n! pct is an
        # integer and a midrank falls halfway between the multiples of
        # 1/n!.  grid_macros does the same thing for Section 5; this is
        # the copy Section 6 reads its steps from, and #253 missed it.
        k = 2 * max(kk) if kk else 0
    models = order_m({m for m, _ in cells})
    corpora = order_c({c for _, c in cells})
    lines = [
        r"% generated by make_tables.py -- do not edit",
        r"\begin{tabular}{llrrrrrrrr}",
        r"\toprule",
        r"evaluator & corpus & $n$ & degen & causal & non-causal & "
        r"$p_{c}$ & $p_{nc}$ & $r$ & $p$ \\",
        r"\midrule",
    ]
    per_model = defaultdict(lambda: {"a": [], "c": [], "r": [],
                                     "w": [], "wc": []})
    # The between-set reading, keyed by cell so it can be tabulated.  It
    # used to be generated from a separate single-evaluator file.
    between = {}
    between_c = {}
    n_texts = n_degen = 0
    # A text scored by two evaluators is one text and two scorings.  n_texts
    # counted rows, and the prose then wrote "across all 2000 texts and both
    # evaluators", which multiplies the 2000 by two a second time.  Keep both
    # numbers, and name each after what it counts.
    seen_texts = set()
    all_r, all_rp, all_disp = [], [], []
    # Displacement is a per-evaluator reading: one evaluator can sit far from
    # the null in every corpus while the other sits on it.  Pooling the two
    # and quoting the pooled maximum put bert-base's p into a sentence about
    # LLaDA, which then claimed that twenty tests "reject" at p < 0.989.
    disp_by_model = defaultdict(list)
    for model in models:
        for corpus in corpora:
            recs = cells.get((model, corpus))
            if not recs:
                continue
            live = [r for r in recs if not r.get("degenerate")]
            degen = len(recs) - len(live)
            for r in recs:
                seen_texts.add((corpus, r.get("category"), r.get("index")))
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
            # These were computed and then thrown away, while the
            # caption and Section 6.3 both said the table showed them.
            # Keep them per group so the row can print both.
            qdisp = {}
            for side, v in (("c", pc), ("n", pn)):
                dd = np.asarray(v, float) - 0.5
                if (dd != 0).sum() >= 6:
                    try:
                        q = float(wilcoxon(dd, alternative='two-sided').pvalue)
                    except ValueError:
                        continue
                    qdisp[side] = q
                    all_disp.append(q)
                    disp_by_model[model].append(q)
            per_model[model]["a"].append(mn - 0.5)
            per_model[model]["c"].append(mc - mn)
            per_model[model]["r"].append(r_rb)
            # sigma of the authored arrangement itself, nothing rearranged.
            wa = [r["sigma_fb_written"] for r in live
                  if r.get("sigma_fb_written") is not None]
            wc = [r["sigma_fb_written"] for r in live
                  if r["category"] == "causal"
                  and r.get("sigma_fb_written") is not None]
            wn = [r["sigma_fb_written"] for r in live
                  if r["category"] == "noncausal"
                  and r.get("sigma_fb_written") is not None]
            if wa:
                per_model[model]["w"].append(float(np.median(wa)))
                between[(model, corpus)] = float(np.median(wa))
            if wc and wn:
                comp = float(np.median(wc)) - float(np.median(wn))
                per_model[model]["wc"].append(comp)
                # Kept per cell as well, so the lower block of
                # tab_fbbetween can print what the prose used to
                # summarise.
                between_c[(model, corpus)] = comp
            lines.append(
                f"{model.split('/')[-1]} & {corpus.replace('fixed_text_', '')}"
                f" & {len(recs)} & {degen} & ${mc:.3f}$ & ${mn:.3f}$ & "
                f"{tex_p(qdisp['c']) if 'c' in qdisp else '---'} & "
                f"{tex_p(qdisp['n']) if 'n' in qdisp else '---'} & "
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
    for model, qs in disp_by_model.items():
        t = TAG.get(model)
        if t and qs:
            mac(f"FbNTestsDisp{t}", str(len(qs)))
            mac(f"FbDispPMax{t}", tex_sci(max(qs)))
            mac(f"FbDispNRejecting{t}",
                str(sum(1 for q in qs if q < 0.05 / len(all_disp))))
    if all_disp:
        mac("FbNTestsDisp", str(len(all_disp)))
        # Its own correction.  \\FbBonferroni is 0.05 over the number of
        # CAUSAL tests, which is half as many; quoting it as the threshold
        # these were judged against would be the wrong number.
        mac("FbDispBonferroni", f"{0.05 / len(all_disp):.4f}")
        mac("FbDispPMax", tex_sci(max(all_disp)))
        mac("FbDispNSurviving",
            str(sum(1 for q in all_disp if q < 0.05 / len(all_disp))))
    mac("FbNCorpora", str(len(corpora)))
    mac("FbNScorings", str(n_texts))
    mac("FbNTexts", str(len(seen_texts)))
    mac("FbNCells", str(len(all_r)))
    mac("FbDegenTotal", str(n_degen))
    if all_r:
        mac("FbRMin", f"{min(all_r):+.3f}")
        mac("FbRMax", f"{max(all_r):+.3f}")
        mac("FbNNegative", str(sum(1 for r in all_r if r < 0)))
    # The between-set reading as a table.  It had none, which is why prose
    # naming an evaluator the data did not cover went unnoticed.
    if between:
        bm = order_m({m for m, _ in between})
        bc = order_c({c for _, c in between})
        bl = [r"% generated by make_tables.py -- do not edit",
              r"\begin{tabular}{l" + "r" * len(bm) + "}",
              r"\toprule",
              "corpus & " + " & ".join(m.split("/")[-1] for m in bm)
              + r" \\",
              r"\midrule"]
        for c in bc:
            row = [c.replace("fixed_text_", "")]
            for m in bm:
                v = between.get((m, c))
                row.append("--" if v is None else f"${v:+.4f}$")
            bl.append(" & ".join(row) + r" \\")
        if any(between_c.get((m, c)) is not None for m in bm for c in bc):
            bl += [r"\midrule",
                   r"\multicolumn{%d}{l}{\emph{causal component}} \\"
                   % (len(bm) + 1)]
            for c in bc:
                row = [c.replace("fixed_text_", "")]
                for m in bm:
                    v = between_c.get((m, c))
                    row.append("--" if v is None else f"${v:+.4f}$")
                bl.append(" & ".join(row) + r" \\")
        bl += [r"\bottomrule", r"\end{tabular}"]
        open(os.path.join(outdir, "tab_fbbetween.tex"), "w").write(
            "\n".join(bl) + "\n")
        print(f"  tab_fbbetween.tex  ({len(bc)} corpora)")
        if len(bm) == 2:
            opp = sum(1 for c in bc
                      if between.get((bm[0], c)) is not None
                      and between.get((bm[1], c)) is not None
                      and between[(bm[0], c)] * between[(bm[1], c)] < 0)
            mac("FbBetweenNOpposite", str(opp))
            mac("FbBetweenNCompared", str(len(bc)))
    # How far apart the evaluators place the same texts, in grid steps.  The
    # prose spelled this out as "about thirteen", which is 0.2708/0.0208 --
    # one evaluator's displacement over the other's, or its displacement in
    # half-steps.  The quantity the sentence claims is the difference, and
    # that is 7.0.  A number written as a word is a number nothing checks.
    auth_steps = []
    for model, d in per_model.items():
        if d["a"] and k:
            auth_steps.append(float(np.median(d["a"])) * k)
    if len(auth_steps) >= 2:
        mac("FbStepGap", f"{max(auth_steps) - min(auth_steps):.1f}")

    # The per-evaluator decomposition, which the prose quotes and the
    # per-corpus table above does not show.  Recovering -0.2708 from that
    # table meant taking its non-causal column, subtracting 0.5, and taking a
    # median over five corpora -- and then multiplying by n! for the steps.
    # Delta has had this table since the beginning (tab_decomposition);
    # sigma quoted the same kind of number with nowhere to look it up.
    dec = [r"% generated by make_tables.py -- do not edit",
           r"\begin{tabular}{lrrrrr}", r"\toprule",
           r"evaluator & authored & steps & causal & steps & $r$ \\",
           r"\midrule"]
    nrow = 0
    for model in models:
        d = per_model.get(model)
        if not d or not d["a"]:
            continue
        au, ca = float(np.median(d["a"])), float(np.median(d["c"]))
        dec.append(f"{model.split('/')[-1]} & ${au:+.4f}$ & "
                   f"${au * k:+.1f}$ & ${ca:+.4f}$ & ${ca * k:+.1f}$ & "
                   f"${np.median(d['r']):+.3f}$ \\\\")
        nrow += 1
    dec += [r"\bottomrule", r"\end{tabular}"]
    if nrow:
        open(os.path.join(outdir, "tab_fbdecomp.tex"), "w").write(
            "\n".join(dec) + "\n")
        print(f"  tab_fbdecomp.tex  ({nrow} evaluators)")

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
        # Where each label group's median sits relative to the null, per
        # corpus.  The prose claimed a direction for the within-text
        # displacement and quoted FbSignNeg, which counts negative effect
        # sizes -- a different quantity, and one that happened to give 5
        # where the displacement gives 4.  The group-level fact is the one
        # the sentence wanted and it was nowhere in the paper: under both
        # evaluators the causally labelled group sits below the null.
        below = sum(1 for ai, ci in zip(d["a"], d["c"]) if ai + ci < 0)
        mac(f"FbCausalBelow{t}", str(below))
        mac(f"FbAuthoredAbove{t}", str(sum(1 for ai in d["a"] if ai > 0)))
        mac(f"FbNCorporaOf{t}", str(len(d["a"])))
        if d["w"]:
            mac(f"FbBetweenMin{t}", f"{min(d['w']):+.4f}")
            mac(f"FbBetweenMax{t}", f"{max(d['w']):+.4f}")
            mac(f"FbBetweenNPos{t}", str(sum(1 for v in d["w"] if v > 0)))
            mac(f"FbBetweenNOf{t}", str(len(d["w"])))
        if d["wc"]:
            mac(f"FbBetweenCausal{t}", f"{float(np.median(d['wc'])):+.4f}")
            mac(f"FbBetweenNNegOf{t}",
                str(sum(1 for v in d["wc"] if v < 0)))

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
        # Strictly opposite signs, not "not all the same": a median of
        # exactly zero is an absence of sign, not a disagreement, and the
        # selftest's synthetic fixture produces one.  A real zero would be
        # visible in the printed per-evaluator numbers.
        # Section 6.5 states in its own words that the two evaluators agree
        # in sign and that the mask rate is therefore not what separates
        # them.  That sentence is hand-written, so the measurement behind it
        # is an assertion here rather than a macro: if the agreement ever
        # fails, the build stops instead of printing prose that says it
        # holds.  (This was \\FbMaskRateVerdict, which no longer has a
        # reader.)
        if any(v > 0 for v in vals) and any(v < 0 for v in vals):
            raise SystemExit(
                "mask rate: the two masked evaluators no longer agree in "
                "sign (%s).  Section 6.5 asserts that they do; rewrite it "
                "before rebuilding." % rs)


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
                # Read from a different file than \\FbNCorpora, and used for
                # the same corpora in adjacent subsections.
                if MACROS.get("FbNCorpora", str(len(ms))) != str(len(ms)):
                    raise SystemExit(
                        "FbBetweenNCorpora=%d but FbNCorpora=%s: the "
                        "within-set and between-set runs do not cover the "
                        "same corpora, and the text reads them as one set"
                        % (len(ms), MACROS["FbNCorpora"]))
        else:
            if "causal_component" in d:
                mac("FbBetweenCausal", f"{d['causal_component']:+.4f}")
                mac("FbBetweenNNeg", str(d.get("n_causal_component_negative", 0)))


def trim_step(v):
    """A step count to a tenth, without a trailing '.0'.

    The components are medians and are not always whole steps, so they
    cannot be printed as integers; printing 2.0 where 2 is meant reads
    as a measured tenth that is not there.
    """
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def grid_macros(blk, kinds):
    """What resolution the midrank has, and whether the reading is at it.

    Eq.(midrank) counts ties as halves and the authored arrangement is
    always tied with itself, so 2 n! pct = 2a + t is an integer and the
    grid one reading lives on is 1/2n!, not 1/n!.  With n = 4 that is
    1/48 = 0.0208, the smallest non-zero value a midrank can take, and a
    causal component of +0.042 is two grid steps.  The components are
    medians over texts and need not land on the grid, so they are printed
    to a tenth of a step rather than rounded to whole ones.  If
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
    # The grid is 1/2n!, not 1/n!: see this function's docstring and
    # Eq.(midrank).  \NPerms stays n!; \GridK is the grid denominator.
    k = 2 * max(nperm)
    step = 1.0 / k
    # What the argument establishes is that a midrank is on this grid.
    # Section 5.3 says so, so the build stops rather than printing it
    # when it is false.
    #
    # The failure this is for is a half-step offset -- the midrank
    # carrying Eq.(midrank)'s tie half while the code divides by n! --
    # so the test is whether a value is nearer a half-step point than a
    # grid point, not whether it is on the grid to machine precision.
    # make_tables_selftest.py's fixture is written to three decimals
    # and is off by 0.008 of a step; an exact test stops it for no
    # reason.  check_grid_resolution.py runs the exact test where the
    # data is exact, on the measurements, and is what Section 5.3 cites.
    loose = [float(r["percentile_written"])
             for recs in blk.values() for r in recs.values()
             if np.isfinite(r.get("percentile_written", float("nan")))
             and 0.25 <= abs(float(r["percentile_written"]) * k) % 1.0
                       <= 0.75]
    if loose:
        raise SystemExit(
            "grid_macros: %d midranks sit nearer a half-step than a "
            "point of the 1/%d grid (%s); Section 5.3 states that grid "
            "as the resolution of one reading" % (len(loose), k,
                          ", ".join(f"{v:.6f}" for v in loose[:4])))
    mac("GridStep", f"{step:.4f}")
    mac("GridK", str(k))

    ar = [m for m in order_m({m for m, _ in blk}) if kinds.get(m) == "causal"]
    comps, steps, params, auth = [], [], [], []
    for model in ar:
        c_, a_ = [], []
        for corpus in order_c({c for _, c in blk}):
            recs = blk.get((model, corpus), {})
            pc = [r["percentile_written"] for q, r in recs.items()
                  if q[0] == "causal"]
            pn = [r["percentile_written"] for q, r in recs.items()
                  if q[0] == "noncausal"]
            if pc and pn:
                c_.append(float(np.median(pc)) - float(np.median(pn)))
                a_.append(float(np.median(pn)) - 0.5)
        if not c_:
            continue
        v = float(np.median(c_))
        comps.append(v)
        steps.append(v / step)
        auth.append(float(np.median(a_)))
        if PARAMS.get(model):
            params.append(PARAMS[model])
    if not comps:
        return
    mac("CausalCompMin", f"{min(comps):+.3f}")
    mac("CausalCompMax", f"{max(comps):+.3f}")
    mac("CausalCompNEval", str(len(comps)))
    mac("CausalCompStepsMin", trim_step(min(steps)))
    mac("CausalCompStepsMax", trim_step(max(steps)))
    mac("CausalCompNDistinct", str(len({trim_step(s) for s in steps})))
    # The authored component read on the SAME grid, because the paper quotes
    # one grid step as a resolution floor in this section and, two
    # subsections later, quotes a rise of one grid step as a measurement.
    # Two different readings of the authored component are involved and they
    # need separate macros: how far it sits from the null, which is several
    # steps and well resolved, and how far it moves across the ladder, which
    # is one step and is not.  The prose said "spans several", which is the
    # first number attached to the second question.
    # How much the authored component varies across the FIVE GENERATORS.
    # All texts in these corpora were produced by a language model, so the
    # "authored order" is an order a left-to-right sampler emitted.  If the
    # component were an artefact of that, it should be much the same
    # whichever model did the emitting; if it tracked something about the
    # particular writer, it should not.  This is the one discriminating
    # number the existing data can offer, and the paper has to report it
    # whichever way it comes out.
    spread = []
    for model in ar:
        per = []
        for corpus in order_c({c for _, c in blk}):
            recs = blk.get((model, corpus), {})
            pn = [r["percentile_written"] for k, r in recs.items()
                  if k[0] == "noncausal"]
            if pn:
                per.append(float(np.median(pn)) - 0.5)
        if len(per) > 1:
            spread.append((max(per) - min(per)) / step)
    if spread:
        mac("AuthoredCorpSpreadSteps", f"{float(np.median(spread)):.1f}")
        mac("AuthoredCorpSpreadMax", f"{max(spread):.1f}")
        mac("AuthoredCorpNGen", str(len(order_c({c for _, c in blk}))))
    mac("AuthoredCompStepsMin", trim_step(min(auth) / step))
    mac("AuthoredCompStepsMax", trim_step(max(auth) / step))
    mac("AuthoredCompSpanSteps", trim_step((max(auth) - min(auth)) / step))
    mac("AuthoredCompSpan", f"{max(auth) - min(auth):.3f}")
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


TAIL_THRESHOLDS = (0.50, 0.60, 0.70, 0.80, 0.90, 0.95)
TAIL_TAGS = ("Fifty", "Sixty", "Seventy", "Eighty", "Ninety", "NinetyFive")
TAIL_Q = 0.90          # the non-causal percentile the z tail is cut at


def tail_macros(blk, kinds, outdir):
    """How far into the upper tail the causal/non-causal contrast reaches.

    Two statistics of one contrast, and the paper needs both because they
    disagree about resolution.  The MEDIAN midrank difference is one step of
    the 1/n! grid (Section 5.3).  The TAIL difference -- how much more often
    a causal text's authored arrangement is the strict maximum of its own
    permutation set -- is tens of points on a 1/n_text grid, and is what
    Section 5.4 reports after its saturation argument failed.

    The tail is also measured on z, which has no ceiling, as the fraction of
    causal texts above the non-causal group's own TAIL_Q percentile.  That
    null is 1 - TAIL_Q by construction, so the statistic needs no grid and
    no bound, and it answers the obvious objection that the midrank tail is
    an artefact of the midrank's upper limit.
    """
    from scipy.stats import binomtest, fisher_exact

    if not blk:
        return
    models = ar_only({m for m, _ in blk}, kinds)
    corpora = order_c({c for _, c in blk})
    if not models:
        return

    def groups(recs, key):
        c = [r[key] for k, r in recs.items() if k[0] == "causal" and key in r]
        n = [r[key] for k, r in recs.items()
             if k[0] == "noncausal" and key in r]
        return c, n

    # ---------------------------------------------- the sweep, reported whole
    sweep = {}
    for model in models:
        row = []
        for t in TAIL_THRESHOLDS:
            per = []
            for corpus in corpora:
                c, n = groups(blk.get((model, corpus), {}),
                              "percentile_written")
                if c and n:
                    per.append(float(np.mean([q > t for q in c]))
                               - float(np.mean([q > t for q in n])))
            if per:
                row.append(float(np.median(per)))
        sweep[model] = row
    lo, hi = models[0], models[-1]
    # A control sequence may contain letters only, so the threshold goes
    # into the name spelled out.  \\TailSweepLo50 compiles to "Missing
    # \\begin{document}" with the offending line pointing at macros.tex,
    # which is a long way from the generator that wrote it.
    for j, t in enumerate(TAIL_THRESHOLDS):
        tag = TAIL_TAGS[j]
        if len(sweep.get(lo, [])) > j and len(sweep.get(hi, [])) > j:
            mac(f"TailSweepLo{tag}", f"{100 * sweep[lo][j]:.0f}")
            mac(f"TailSweepHi{tag}", f"{100 * sweep[hi][j]:.0f}")
    mac("TailSweepNThr", str(len(TAIL_THRESHOLDS)))

    # where the contrast first exceeds one point, so the prose can say
    # "nothing below X" from a measurement rather than by reading the table
    first = None
    for j, t in enumerate(TAIL_THRESHOLDS):
        vals = [sweep[m][j] for m in models if len(sweep[m]) > j]
        if vals and min(vals) > 0.01:
            first = t
            break
    if first is not None:
        mac("TailOnsetThr", f"{first:.2f}")
        # The threshold is where the WORST evaluator passes one point, so
        # below it the worst is small and the others need not be.  Four
        # sentences read it as "no evaluator differs by a point below
        # here" while the table beside them printed +2 and +3.  The honest
        # companion is the largest contrast any evaluator shows below the
        # onset, measured over the same sweep.
        below = [sweep[m][j] for m in models
                 for j, t in enumerate(TAIL_THRESHOLDS)
                 if t < first and len(sweep[m]) > j]
        if below:
            mac("TailBelowOnsetMax", f"{100 * max(below):.0f}")

    # ------------------------------------- cell by cell, on both statistics
    # One row per evaluator, one column per corpus.  The first version gave
    # a row to each of the 25 cells, which is 25 rows of 7 columns: it fits
    # no top slot, becomes a float page, and queued behind everything else
    # already deferred -- cited on page 19 and printed on page 28.  The
    # per-cell p-values are not lost, they are summarised as counts
    # (TailNRejecting, TailPMax), which is what the prose uses; what a
    # reader needs from the table is the spread, and the differences show
    # it directly.
    ps_mid, ps_z, diffs, ztail, n_cells = [], [], [], [], 0
    per_model, grid_mid, grid_z = {}, {}, {}
    for model in models:
        dm, zm = [], []
        for corpus in corpora:
            recs = blk.get((model, corpus), {})
            c, n = groups(recs, "is_strict_max")
            if not c or not n:
                grid_mid[(model, corpus)] = None
                grid_z[(model, corpus)] = None
                continue
            cc, nn = int(round(sum(c))), int(round(sum(n)))
            _, p = fisher_exact([[cc, len(c) - cc], [nn, len(n) - nn]])
            d = 100.0 * (cc / len(c) - nn / len(n))
            ps_mid.append(p)
            diffs.append(d)
            dm.append(d)
            grid_mid[(model, corpus)] = (d, p)
            zc, zn = groups(recs, "z_written")
            zc = [v for v in zc if np.isfinite(v)]
            zn = [v for v in zn if np.isfinite(v)]
            grid_z[(model, corpus)] = None
            if len(zc) > 4 and len(zn) > 4:
                cut = float(np.quantile(zn, TAIL_Q))
                k = int(sum(1 for v in zc if v > cut))
                zt = 100.0 * k / len(zc)
                # One-sample: is the share of causal texts above the
                # non-causal group's own TAIL_Q percentile greater than
                # the 1 - TAIL_Q that cut defines?  Fisher against a
                # synthetic row of the same size answers a two-sample
                # question that was never asked, and treats a constructed
                # expectation as a draw.
                pz = binomtest(k, len(zc), 1 - TAIL_Q,
                               alternative="two-sided").pvalue
                ps_z.append(pz)
                ztail.append(zt)
                zm.append(zt)
                grid_z[(model, corpus)] = (zt, pz)
            n_cells += 1
        if dm:
            per_model[model] = (float(np.median(dm)),
                                float(np.median(zm)) if zm else float("nan"))

    # The section says it reports the sweep rather than the threshold that
    # maximises the contrast.  Quoting four of six thresholds in prose does
    # not do that, so the sweep goes out as a table and the claim is true.
    # Which sweep thresholds are the strict-maximum cut in disguise.  For
    # n = 4 the attainable midranks are (k + 0.5)/24, so the only one above
    # 0.95 is 23.5/24 and "> 0.95" IS "strict maximum" -- Section 5.3
    # offered the two as different cuts and the table printed each pair
    # equal in all five rows.  Dropping the column would strand its
    # retirement entries, so the duplication is measured and named instead.
    have = [m for m in models if m in per_model]
    dupthr = None
    for j, t in enumerate(TAIL_THRESHOLDS):
        if not have:
            break
        if all(len(sweep.get(m, [])) > j
               and abs(100 * sweep[m][j] - per_model[m][0]) < 0.5
               for m in have):
            dupthr = t
            break
    if dupthr is not None:
        mac("TailSweepDupThr", f"{dupthr:.2f}")

    sw = [r"% generated by make_tables.py -- do not edit",
          r"\begin{tabular}{l" + "r" * (len(TAIL_THRESHOLDS) + 1) + "}",
          r"\toprule",
          "evaluator & "
          + " & ".join(f"$>{t:.2f}$" for t in TAIL_THRESHOLDS)
          + r" & strict max \\",
          r"\midrule"]
    for model in models:
        row = sweep.get(model, [])
        if len(row) < len(TAIL_THRESHOLDS):
            continue
        tailv = per_model.get(model, (float("nan"),))[0] \
            if model in per_model else float("nan")
        sw.append(f"{model.split('/')[-1]} & "
                  + " & ".join(f"{100*v:.0f}" for v in row)
                  + (f" & {tailv:+.0f}" if np.isfinite(tailv) else " & --")
                  + r" \\")
    sw += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(outdir, "tab_sweep.tex"), "w").write(
        "\n".join(sw) + "\n")

    bon = 0.05 / len(ps_mid) if ps_mid else 1.0

    def cell(v, star):
        if v is None:
            return "--"
        # one math group, not two abutting ones: $+21$$^{*}$ typesets with
        # a seam between the number and its marker
        return f"${v:+.0f}" + (r"^{*}" if star else "") + "$"

    lines = [
        r"% generated by make_tables.py -- do not edit",
        r"\begin{tabular}{l" + "r" * (len(corpora) + 1) + "}",
        r"\toprule",
        "evaluator & " + " & ".join(corpora) + r" & median \\",
        r"\midrule",
        r"\multicolumn{" + str(len(corpora) + 2)
        + r"}{l}{\emph{midrank: points by which more causal than "
          r"non-causal texts reach the strict maximum}} \\",
    ]
    for model in models:
        row = [cell(None if grid_mid.get((model, c)) is None
                    else grid_mid[(model, c)][0],
                    grid_mid.get((model, c)) is not None
                    and grid_mid[(model, c)][1] < bon)
               for c in corpora]
        med = per_model.get(model, (float("nan"),))[0]
        lines.append(f"{model.split('/')[-1]} & " + " & ".join(row)
                     + f" & ${med:+.0f}$" + r" \\")
    lines += [
        r"\addlinespace",
        r"\multicolumn{" + str(len(corpora) + 2)
        + r"}{l}{\emph{$z$, no ceiling: \% of causal texts above the "
          r"non-causal $" + str(int(round(100 * TAIL_Q)))
        + r"$th percentile (null $"
        + str(int(round(100 * (1 - TAIL_Q)))) + r"\%$)}} \\",
    ]
    for model in models:
        row = []
        for c in corpora:
            g = grid_z.get((model, c))
            row.append("--" if g is None
                       else f"{g[0]:.0f}" + (r"$^{*}$" if g[1] < bon else ""))

        z = per_model.get(model, (0, float("nan")))[1]
        lines.append(f"{model.split('/')[-1]} & " + " & ".join(row)
                     + (f" & {z:.0f}" if np.isfinite(z) else " & --")
                     + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(outdir, "tab_tail.tex"), "w").write(
        "\n".join(lines) + "\n")

    if not n_cells:
        return
    bon = 0.05 / len(ps_mid)
    mac("TailNCells", str(n_cells))
    mac("TailBonferroni", tex_sci(bon, 1))
    mac("TailNRejecting", str(sum(1 for p in ps_mid if p < bon)))
    mac("TailPMax", tex_sci(max(ps_mid), 1))
    mac("TailDiffMin", f"{min(diffs):+.0f}")
    mac("TailDiffMax", f"{max(diffs):+.0f}")
    mac("TailNPositive", str(sum(1 for d in diffs if d > 0)))
    # The sign is the strong part of the cell-level evidence and the
    # magnitude is not: 24 of 25 cells positive is a sign test, while only
    # 8 clear a Bonferroni threshold.  Both are reported, because quoting
    # either alone misstates what the cells show.
    from scipy.stats import binomtest
    mac("TailSignP", tex_sci(binomtest(sum(1 for d in diffs if d > 0),
                                       len(diffs), 0.5).pvalue, 1))
    if ps_z:
        mac("TailZQ", f"{int(round(100 * TAIL_Q))}")
        mac("TailZNull", f"{int(round(100 * (1 - TAIL_Q)))}")
        mac("TailZMin", f"{min(ztail):.0f}")
        mac("TailZMax", f"{max(ztail):.0f}")
        mac("TailZNRejecting", str(sum(1 for p in ps_z if p < bon)))
        mac("TailZPMax", tex_sci(max(ps_z), 1))
    for model, (d, z) in per_model.items():
        t = TAG.get(model)
        if t:
            mac(f"TailDiff{t}", f"{d:+.0f}")
            if np.isfinite(z):
                mac(f"TailZ{t}", f"{z:.0f}")
    # and the ladder trend, by the paper's own within-corpus pairing, which
    # is NOT the difference of the two medians: the two aggregations give
    # p = 0.083 and p = 0.033 on this data, and the paired one is the rule
    # Section 3.4 states.
    par = [PARAMS[m] for m in models if PARAMS.get(m)]
    yy = [per_model[m][0] for m in models if PARAMS.get(m) and m in per_model]
    if len(par) == len(yy) and len(yy) > 3:
        rho, p, _ = spearman(par, yy)
        mac("TailTrendRho", f"{rho:+.2f}")
        mac("TailTrendP", f"{p:.3f}")
        mac("TailTrendNEval", str(len(yy)))
    # The same ladder on the ceiling-free tail.  This is the statistic the
    # paper should lead with: its null is fixed by construction, it has no
    # bound to saturate against, and more of its cells reject.  On the
    # measured data it is the midrank tail that fails to reach 0.05 and
    # this one that reaches the smallest value n = 5 admits.
    zz = [per_model[m][1] for m in models if PARAMS.get(m) and m in per_model]
    if len(par) == len(zz) and len(zz) > 3 and all(np.isfinite(zz)):
        rho, p, _ = spearman(par, zz)
        mac("TailZTrendRho", f"{rho:+.2f}")
        mac("TailZTrendP", f"{p:.3f}")
        # The same correlation on the rungs that share a family, where only
        # size differs.  The Limitations say the family confound bears
        # hardest on this one trend; a caveat is the weaker answer when the
        # subset can simply be measured.  This is NOT a new member of
        # Section 5.4's family -- it is the same statistic on a subset of
        # the same points, and TrendNTested is deliberately not incremented
        # for it.  n = 4 floors at 2/4! = 0.083, which the prose states.
        fam = [m for m in models if m.startswith("gpt2") and PARAMS.get(m)
               and m in per_model]
        if len(fam) > 2:
            fz = [per_model[m][1] for m in fam]
            if all(np.isfinite(fz)):
                frho, fp, _ = spearman([PARAMS[m] for m in fam], fz)
                mac("TailZFamRho", f"{frho:+.2f}")
                mac("TailZFamP", f"{fp:.3f}")
                mac("TailZFamNEval", str(len(fam)))
                mac("TailZFamFloor", f"{exact_p_floor(len(fam)):.3f}")
        # Fold the two tail trends into Section 5.4's count, which
        # trend_macros() could not do because they are measured here.
        extra = sum(1 for k in ("TailTrendP", "TailZTrendP")
                    if k in MACROS and _lt(MACROS[k], 0.05))
        if "TrendNTested" in MACROS:
            MACROS["TrendNTested"] = str(int(MACROS["TrendNTested"]) + 2)
            MACROS["TrendNSignificant"] = str(
                int(MACROS["TrendNSignificant"]) + extra)
            # HERE, not where TrendNTested is first set: the tail trends are
            # folded in afterwards, so a threshold computed from the earlier
            # count would be 0.05/6 printed beside a family of 8.  The
            # threshold these correlations WOULD be judged against if this
            # section corrected them the way its cell tests are corrected;
            # the prose states that it lies below the exact floor rather
            # than quietly not correcting.
            MACROS["TrendBonferroni"] = (
                f"{0.05 / int(MACROS['TrendNTested']):.4f}")
    print(f"  tab_tail.tex  ({n_cells} cells)")


def contrast_macros(blk, kinds, outdir=None):
    """Is the causal/non-causal separation present in every cell?

    Three sentences -- abstract, introduction, Section 5.3 -- said it is,
    citing $p < \\BlkPMaxCausal$.  That macro is wrong three times over.
    Its name says max and \\texttt{pmin = min(pmin, p)} makes it a minimum,
    so "below it in every cell" is true of no cell but one.  The p it holds
    is a Wilcoxon of the CAUSAL group against the 0.50 null, which is a
    different question from whether the two groups differ.  And it is
    computed for \\texttt{gpt2} alone, in a loop that fixes one model per
    tag, so "every evaluator" came from one.

    This measures the claim as made: a two-sided Mann-Whitney between the
    label groups in every (evaluator, corpus) cell of the autoregressive
    ladder, the count that clears a Bonferroni threshold, and the worst p
    among them -- which is the number a sentence of that shape needs.
    """
    from scipy.stats import mannwhitneyu

    if not blk:
        return
    models = ar_only({m for m, _ in blk}, kinds)
    corpora = order_c({c for _, c in blk})
    ps, rs = [], []
    cells = []          # (model, corpus, median Dblock authored, r, p)
    for model in models:
        for corpus in corpora:
            recs = blk.get((model, corpus), {})
            pc = [r["percentile_written"] for k, r in recs.items()
                  if k[0] == "causal"]
            pn = [r["percentile_written"] for k, r in recs.items()
                  if k[0] == "noncausal"]
            if len(pc) < 2 or len(pn) < 2:
                continue
            u, p = mannwhitneyu(pc, pn, alternative="two-sided")
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
                          rr, float(p)))
    if not ps:
        return
    bon = 0.05 / len(ps)
    # The corpus axis, published so check_corpus_order can compare the
    # table bodies against it.  A file and not a macro: it is machine-only,
    # no prose quotes it, and a generated macro with no reader is exactly
    # what the orphan check exists to report.
    if outdir:
        open(os.path.join(outdir, "corpus_order.txt"), "w").write(
            " ".join(corpus_base(c) for c in corpora) + "\n")
    mac("ContrastNCells", str(len(ps)))
    # The cell count is a product and the prose should be able to say so.
    # Both sets are already fixed above: models is ar_only() of the keys,
    # corpora is order_c() of them, and len(ps) is one test per pair.  A
    # reader who cannot see 25 as 5 x 5 cannot check the claim against the
    # table, which is the hole this paper is about.
    mac("ContrastNEval", str(len(models)))
    mac("ContrastNCorpora", str(len(corpora)))
    mac("ContrastNRejecting", str(sum(1 for q in ps if q < bon)))
    mac("ContrastBonferroni", tex_sci(bon, 1))
    mac("ContrastPWorst", tex_p_bare(max(ps)))
    mac("ContrastPBest", tex_p_bare(min(ps)))
    mac("ContrastNPositive", str(sum(1 for r in rs if r > 0)))
    mac("ContrastRMedian", f"{float(np.median(rs)):+.3f}")
    mac("ContrastRMin", f"{min(rs):+.3f}")
    mac("ContrastRMax", f"{max(rs):+.3f}")
    # Per evaluator.  "N of 25" says nothing about whether the cells that
    # fail are spread over the ladder or stacked on one rung, and Section
    # 5.4 argues about the ladder for a whole subsection.
    by_eval = []
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
        mac("ContrastRejectByEval", ", ".join(by_eval))
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
                + f" & ${rr:+.3f}$ & $" + tex_p_bare(p)
                # {} and not nothing: tex_p_bare ends in a superscript
                # below 1e-3, and "10^{-4}^{*}" is the double superscript
                # that TeX refused 17 times a pass.  The empty group gives
                # the star an atom of its own and typesets identically.
                + (r"{}^{*}" if p < bon else "") + r"$ \\")
        lines += [r"\bottomrule", r"\end{tabular}"]
        open(os.path.join(outdir, "tab_blkcells.tex"), "w").write(
            "\n".join(lines) + "\n")
        print(f"  tab_blkcells.tex  ({len(cells)} cells)")


def trend_macros(blk, kinds):
    """Does any component of the decomposition track evaluator capacity?

    The paper used to assert that the causal contribution falls as the
    evaluator saturates.  Measured on the autoregressive ladder it does not:
    what rises with capacity is the fraction of texts whose authored order is
    already the extreme arrangement, while the ceiling-free z share is flat.
    These macros put a rank correlation on each component, so the text states
    what was measured rather than what was expected.

    The p-values come from the exact rank null, not from scipy's
    asymptotic approximation: see spearman() above for why that
    distinction is not cosmetic at the n of this ladder.
    """
    ar = [m for m in order_m({m for m, _ in blk})
          if kinds.get(m) == "causal" and PARAMS.get(m)]
    if len(ar) < 4:
        return
    par = [PARAMS[m] for m in ar]
    series = {}
    for m in ar:
        a_, c_, z_, ceil_, azs_ = [], [], [], [], []
        ceiln_ = []
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
            # Two sets, two fractions.  Section 5.4 paired its ceiling
            # evidence with the authored component of Eq. (8), which is
            # defined on the NON-causal texts, while the fraction it quoted
            # was computed on the causal ones.  Both are measured here so
            # the section can use the one that matches and report the other.
            sm = [r["is_strict_max"] for q, r in recs.items()
                  if q[0] == "causal" and "is_strict_max" in r]
            smn = [r["is_strict_max"] for q, r in recs.items()
                   if q[0] == "noncausal" and "is_strict_max" in r]
            if sm:
                ceil_.append(float(np.mean(sm)))
            if smn:
                ceiln_.append(float(np.mean(smn)))
            zc = [r["z_written"] for q, r in recs.items() if q[0] == "causal"
                  and np.isfinite(r.get("z_written", np.nan))]
            zn = [r["z_written"] for q, r in recs.items()
                  if q[0] == "noncausal"
                  and np.isfinite(r.get("z_written", np.nan))]
            if zc and zn:
                az = float(np.median(zn))
                cz = float(np.median(zc)) - az
                z_.append(cz / (az + cz) if az + cz > 0 else float("nan"))
                # The authored component itself, in the ceiling-free units.
                # Only its SHARE was tracked, so the one series that could
                # corroborate a rise in the bounded authored component --
                # or fail to -- was never correlated against capacity.
                azs_.append(az)
        if not a_:
            return
        series.setdefault("authored", []).append(float(np.median(a_)))
        series.setdefault("causal", []).append(float(np.median(c_)))
        series.setdefault("ceiling", []).append(
            float(np.median(ceil_)) if ceil_ else float("nan"))
        series.setdefault("ceilingn", []).append(
            float(np.median(ceiln_)) if ceiln_ else float("nan"))
        zz = [v for v in z_ if np.isfinite(v)]
        series.setdefault("sharez", []).append(float(np.median(zz)) if zz
                                               else float("nan"))
        azz = [v for v in azs_ if np.isfinite(v)]
        series.setdefault("authoredz", []).append(float(np.median(azz))
                                                  if azz else float("nan"))

    for key, tag in (("authored", "Authored"), ("causal", "Causal"),
                     ("ceiling", "Ceil"), ("ceilingn", "CeilN"),
                     ("sharez", "ShareZ"), ("authoredz", "AuthoredZ")):
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
        rho, pv, _ = spearman(par, yq)
        mac(f"Trend{tag}NDistinct", str(len(set(yq.tolist()))))
        mac(f"Trend{tag}Rho", f"{rho:+.2f}")
        mac(f"Trend{tag}P", f"{pv:.3f}")
    # Section 5.4 says the rise in the causal strict-maximum fraction is
    # carried by the smallest evaluator on its own.  That is a claim
    # about what is left when it goes, so measure the remainder instead
    # of describing it.
    yc = series.get("ceiling")
    if yc and len(yc) > 3 and np.all(np.isfinite(yc)):
        yq = np.round(np.asarray(yc, float), 12)
        i = int(np.argmin(par))
        keep = [j for j in range(len(par)) if j != i]
        rho_d, p_d, _ = spearman([par[j] for j in keep],
                                 [yq[j] for j in keep])
        mac("TrendCeilNDropRho", f"{rho_d:+.2f}")
        mac("TrendCeilNDropP", f"{p_d:.3f}")
        mac("TrendCeilNDropNEval", str(len(keep)))
    # "The only component with a significant trend" is a claim about all of
    # them at once, and nothing checked it.  Counting here makes it a number
    # the self-test can hold the sentence to.
    # The tail trend of tail_macros() is one of the correlations Section
    # 5.4 reports, so it belongs in this count; it is emitted later, which
    # is why the count is taken there instead.  Here we record only the
    # components this function measured.
    sig = [t for t in ("Authored", "Causal", "Ceil", "CeilN", "ShareZ",
                       "AuthoredZ")
           if f"Trend{t}P" in MACROS and _lt(MACROS[f"Trend{t}P"], 0.05)]
    tested = [t for t in ("Authored", "Causal", "Ceil", "CeilN", "ShareZ",
                          "AuthoredZ") if f"Trend{t}P" in MACROS]
    mac("TrendNTested", str(len(tested)))
    mac("TrendNSignificant", str(len(sig)))
    mac("TrendSignificantIs", ", ".join(sig) if sig else "none")
    mac("TrendNEval", str(len(ar)))
    mac("TrendPFloor", f"{exact_p_floor(len(ar)):.3f}")
    mac("TrendQuantum", "12")
    mac("TrendCapSpan", f"{max(par) / min(par):.0f}")
    # and the span WITHIN one family, which is a different number: the top
    # of the ladder is a different model family on a different corpus, and
    # Section 3.1 called the whole 32-fold span a within-family series.
    fam = [PARAMS[m] for m in ar if m.startswith("gpt2")]
    if len(fam) > 1:
        mac("TrendCapSpanFamily", f"{max(fam) / min(fam):.0f}")


def param_macros():
    """\\Params<Tag> for every evaluator this paper names, whatever it reports.

    These used to be emitted inside the decomposition loop.  When the Delta
    tables were restricted to the autoregressive evaluators, the masked ones
    lost their parameter counts too -- and those are still named, in the
    evaluator table and in the sigma results.  A parameter count is not a
    measurement; it does not belong to whichever table happens to run.
    """
    for model, p in PARAMS.items():
        t = TAG.get(model)
        if not t:
            continue
        # Integer division printed gpt2-xl's 1558M as "1B".  One decimal,
        # with a trailing zero stripped, gives 1.6B / 4B / 8B.
        if p < 1000:
            mac(f"Params{t}", f"{p}M")
        else:
            v = f"{p / 1000:.1f}".rstrip("0").rstrip(".")
            mac(f"Params{t}", f"{v}B")


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
                 "tab_tail.tex", "tab_sweep.tex",
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
    capacity_scale_macros(blk, kinds)
    table_decomposition(blk, kinds, args.outdir)
    table_saturation(blk, kinds, args.outdir)
    table_pll(pll, kinds, args.outdir)
    table_token(pll, kinds, args.outdir)
    table_capacity(args.toy, args.outdir)
    table_bayes_route(args.toy, args.outdir)
    table_fbrank(args.sigfb, args.outdir)
    fb_between_macros(args.fbjson)
    grid_macros(blk, kinds)
    contrast_macros(blk, kinds, args.outdir)
    trend_macros(blk, kinds)
    tail_macros(blk, kinds, args.outdir)
    cross_instrument_macros()
    param_macros()
    capacity_ratio_macros()
    selftest_macros(args.blkord)

    # Every macro the prose may reference is defined even when its measurement
    # is not in yet, so the document always compiles; a missing number shows up
    # as a visible TODO instead of an undefined-control-sequence error.
    expected = ["NPerGroup",
                "TrendCeilNDropRho", "TrendCeilNDropP",
                "TrendCeilNDropNEval",
                "FbNTestsCausal", "FbBonferroni", "FbNSurviving",
                "FbNNominal", "FbNExpected", "FbNTestsDisp",
                "FbDispPMax", "FbDispNSurviving", "FbDispBonferroni",
                "FbNTestsDispLLaDA", "FbDispPMaxLLaDA",
                "FbDispNRejectingLLaDA",
                "FbNTestsDispBertBase", "FbDispPMaxBertBase",
                "FbDispNRejectingBertBase",
                "FbStepGap",
                "FbAuthoredStepsBertBase", "FbCausalStepsBertBase",
                "FbAuthoredStepsLLaDA", "FbCausalStepsLLaDA",
                "FbSignPBertBase", "FbSignNegBertBase",
                "FbSignPLLaDA", "FbSignNegLLaDA",
                "FbBetweenMinLLaDA", "FbBetweenMaxLLaDA",
                "FbBetweenNPosLLaDA", "FbBetweenNOfLLaDA",
                "FbBetweenCausalLLaDA", "FbBetweenNNegOfLLaDA",
                "FbBetweenMinBertBase", "FbBetweenMaxBertBase",
                "FbBetweenNPosBertBase", "FbBetweenNOfBertBase",
                "FbBetweenCausalBertBase", "FbBetweenNNegOfBertBase",
                "FbBetweenNOpposite", "FbBetweenNCompared",
                "TrendAuthoredRho", "TrendAuthoredP",
                "TrendCausalRho", "TrendCausalP",
                "TrendCeilRho", "TrendCeilP",
                "TrendShareZRho", "TrendShareZP",
                "TrendAuthoredZRho", "TrendAuthoredZP",
                "TrendAuthoredZNDistinct",
                "TrendNEval", "TrendCapSpan", "TrendQuantum",
                "TailSweepNThr", "TailOnsetThr", "TailBelowOnsetMax",
                "TailSweepDupThr",
                "TailNCells", "TailBonferroni", "TailNRejecting",
                "TailPMax", "TailDiffMin", "TailDiffMax", "TailNPositive",
                "TailZQ", "TailZNull", "TailZMin", "TailZMax",
                "TailZNRejecting", "TailZPMax",
                "ContrastNCells", "ContrastNEval", "ContrastNCorpora",
                "ContrastNRejecting",
                "ContrastBonferroni", "ContrastPWorst", "ContrastPBest",
                "ContrastNPositive", "ContrastRMedian", "ContrastRMin",
                "ContrastRMax",
                "ContrastRejectByEval",
                "TailTrendRho", "TailTrendP", "TailTrendNEval",
                "TailZTrendRho", "TailZTrendP", "TailSignP",
                "TailZFamRho", "TailZFamP", "TailZFamNEval",
                "TailZFamFloor",
                "TailSweepLoFifty", "TailSweepHiFifty", "TailSweepLoSixty",
                "TailSweepHiSixty", "TailSweepLoSeventy", "TailSweepHiSeventy",
                "TailSweepLoEighty", "TailSweepHiEighty", "TailSweepLoNinety",
                "TailSweepHiNinety", "TailSweepLoNinetyFive", "TailSweepHiNinetyFive",
                "TailDiffGPTtwo", "TailDiffGPTtwoMedium",
                "TailDiffGPTtwoLarge", "TailDiffGPTtwoXL", "TailDiffQwen",
                "TailZGPTtwo", "TailZGPTtwoMedium", "TailZGPTtwoLarge",
                "TailZGPTtwoXL", "TailZQwen",
                "TrendPFloor", "TrendNSignificant", "TrendSignificantIs",
                "TrendCapSpanFamily",
                "TrendNTested", "TrendBonferroni",
                "TrendCeilNRho", "TrendCeilNP", "TrendCeilNNDistinct",
                "TrendCausalNDistinct", "TrendAuthoredNDistinct",
                "TrendCeilNDistinct", "TrendShareZNDistinct",
                "GridStep", "GridK", "CausalCompMin", "CausalCompMax",
                "CausalCompNEval", "CausalCompStepsMin", "CausalCompStepsMax",
                "CausalCompNDistinct", "CausalCompCapSpan",
                "AuthoredCorpSpreadSteps", "AuthoredCorpSpreadMax",
                "AuthoredCorpNGen",
                "AuthoredCompStepsMin", "AuthoredCompStepsMax",
                "AuthoredCompSpanSteps", "AuthoredCompSpan",
                "CausalCompCapLo", "CausalCompCapHi",
                "RatioNDistinct", "RatioNDistinctEnds", "RatioNAtEnd",
                "FbNCorpora", "FbNTexts", "FbNScorings", "FbNCells",
                "FbDegenTotal",
                "FbRMin", "FbRMax", "FbNNegative",
                "FbPctCausalBertBase", "FbPctNoncausalBertBase", "FbRBertBase",
                "FbAuthoredBertBase", "FbCausalBertBase",
                "FbPctCausalLLaDA", "FbPctNoncausalLLaDA", "FbRLLaDA",
                "FbAuthoredLLaDA", "FbCausalLLaDA",
                "FbCausalBelowBertBase", "FbAuthoredAboveBertBase",
                "FbNCorporaOfBertBase",
                "FbCausalBelowLLaDA", "FbAuthoredAboveLLaDA",
                "FbNCorporaOfLLaDA",
                "FbBetweenMin", "FbBetweenMax", "FbBetweenNCorpora",
                "FbBetweenCausal", "FbBetweenNNeg",
                "AuthoredGPTtwoMedium", "CausalGPTtwoMedium",
                "ShareGPTtwoMedium", "ParamsGPTtwoMedium",
                "AuthoredGPTtwoLarge", "CausalGPTtwoLarge",
                "ShareGPTtwoLarge", "ParamsGPTtwoLarge",
                "AuthoredGPTtwoXL", "CausalGPTtwoXL",
                "ShareGPTtwoXL", "ParamsGPTtwoXL",
                "ShareZMin", "ShareZMax", "ShareZNEval",
                "ShareFormRho", "ShareFormP", "ShareFormNEval",
                "ShareFormWorst",
                "ShareEvalMin", "ShareEvalMax", "ShareEvalNEval",
                "SwapEval", "SwapAuthored", "SwapCausal",
                "SwapAuthoredOrig", "SwapCausalOrig",
                "SwapShareMin", "SwapShareMax", "SwapShareNNeg",
                "SwapShareNEval",
                "MedPctCausal", "MedPctNoncausal", "PctVsNullP",
                "CausalRatioMedian", "CausalRatioMin", "CausalRatioMax",
                "NBlkordCells", "NBlocks", "NPerms", "NEval", "NCorp", "CapRatioMedian", "CapRatioMin", "CapRatioMax",
                "CapNCorpora", "CapNUp", "CapNSign",
                "CapDeltaLo", "CapDeltaHi", "SigmaCausal",
                "AuthoredCausal", "CausalCompCausal", "CausalRatioCausal",
                "BlkRMasked", "BlkNSepMasked", "BlkNTotMasked", "BlkPBestMasked",
                "BlkPctCMasked", "BlkPctNMasked",
                "BlkRCausal", "BlkNSepCausal", "BlkNTotCausal", "BlkPBestCausal",
                "BlkPctCCausal", "BlkPctNCausal", "NSepCausal", "NTotCausal",
                # token reversal, reported only in the between-set table
                "SigTokRatioMin", "SigTokRatioMax", "NTokLarger", "NTokCells",
                "NTokNegAR", "NTokNegARTot",
                "ToyNCap", "ToyDMin", "ToyDMax", "ToyOrdersAbove",
                "ReproMaxErr", "ReproNCorpora",
                "AoarOrderDev", "AoarNormDev", "AoarNormDevInc",
                "AoarL", "AoarV", "AoarStates", "AoarNOrders",
                "ARSpanRatio", "GapSpreadRatio",
                # per-evaluator, for the capacity series in the prose
                
                "ParamsBertBase", 
                
                "ParamsBertLarge", 
                
                "ParamsLLaDA", 
                "AuthoredGPTtwo", "CausalGPTtwo", "ShareGPTtwo",
                "CeilNTexts", "CeilResolution", "CeilRise", "CeilRiseUnits",
                "ParamsGPTtwo", "CeilGPTtwo", "CeilNGPTtwo",
                "AuthoredQwen", "CausalQwen", "ShareQwen",
                "ParamsQwen", "CeilQwen", "CeilNQwen",
                # median r and median median-gap per evaluator; see the note
                # in table_blkord on why both are needed
                "RGPTtwo", "RQwen",
                "GapGPTtwo",
                "GapQwen",
                "PctCGPTtwo",
                "PctCQwen",
                "PctNGPTtwo",
                "PctNQwen",
                "RoomGPTtwo",
                "RoomQwen",
                # the gap measured against the room left above the non-causal
                # median, with its bootstrap interval
                "RatioGPTtwo",
                "RatioQwen",
                
                
                
                "RatioLoGPTtwo", "RatioHiGPTtwo",
                "RatioLoQwen", "RatioHiQwen",
                "RatioMin", "RatioMax", "RatioNEval", "RatioNCI",
                "RatioOverlapLo", "RatioOverlapHi",
                "RatioWidestLo", "RatioWidestHi", "RCausal", "ToySigmaMin", "ToySigmaMax",
                "ToyCapRatio", "ToyCapMonotone", "ToySpanRatio", "ToySigmaAR", "ToyRmsAR", "ToyL", "ToyV",
                "ToyStates", "ToyN",
                "CtrlNWidths", "CtrlDMin", "CtrlDMax",
                "CtrlSigmaHead", "CtrlSigmaJointMax",
                "CtrlJeffreysMin", "CtrlJeffreysMax",
                "CtrlSigMedian", "CtrlSigMeanAbs",
                "CtrlSigMin", "CtrlSigMax",
                "CtrlRhoEP", "CtrlPEP", "CtrlRhoSig",
                "CtrlPSig", "CtrlRhoXS", "CtrlPXS"]
    # The retired list travels with the macros, so check_paper.py needs no
    # import of this file to tell a declared non-use from a dropped number.
    out = [r"% generated by make_tables.py -- do not edit"]
    for i in range(0, len(RETIRED), 8):
        out.append("% retired: " + " ".join(RETIRED[i:i + 8]))
    # Same route as the retired list: check_paper.py reads the declaration
    # out of macros.tex rather than importing this file.
    for w, (budget, group, why) in sorted(WITHDRAWN_FROM_PROSE.items()):
        out.append("%% withdrawn-prose: %s|%s|%s|%s"
                   % (w, "-" if budget is None else budget, group, why))
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
                 "tab_tail.tex", "tab_sweep.tex",
                 "tab_decomposition.tex", "tab_fbrank.tex",
                 "tab_bayesroute.tex", "tab_fbdecomp.tex"):
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
