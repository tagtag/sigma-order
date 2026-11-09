#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build every figure in the paper straight from the measurement JSONs.

No number and no bar in this paper is typed by hand: each figure is produced
from the same files the measurement scripts wrote, so a rerun of the
measurement regenerates the figure.  Panels whose input is missing are skipped
with a notice rather than faked, so this can be run on partial results while
jobs are still going.

Figures
-------
fig1_block_order   The decisive result.  Where the WRITTEN sentence order sits
                   among all 4! = 24 orders of the same text, for causal and
                   non-causal texts, against the 0.50 null.  Within-text, so
                   length, vocabulary, style and topic are held fixed.
fig2_capacity      sigma against evaluator capacity, in the exactly solvable
                   toy system and in the BERT pair.  sigma rises with capacity
                   in both, so it has no capacity-independent value.
fig3_evaluators    sigma and the causal/non-causal effect size for each
                   evaluator, with the scale-matched masked/causal pair
                   (bert-base 110M, gpt2 117M) adjacent.

    python3 make_figures.py --pll ../order-intervention/results_pll \\
        --blkord ../order-intervention/results_blkord \\
        --toy ../bert-affinity --outdir figures
"""

import argparse
import glob
import json
import os
import sys
from collections import defaultdict

# so `python3 -I make_figures.py` finds figstyle.py beside it
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from scipy.stats import mannwhitneyu

from figstyle import C, GRID, INK, INK_MUTED, MARKERS, NULLC, setup, tidy

import matplotlib.pyplot as plt  # noqa: E402

CORPUS_ORDER = ["Opus46", "GPT54", "GPT56", "Gemini31", "Fable5"]
# fixed evaluator order: smallest first, masked before causal at equal size
# ordered by parameter count: the capacity series is what the paper reads
EVAL_ORDER = ["bert-base-uncased", "gpt2", "bert-large-uncased",
              "Qwen/Qwen3-4B-Base", "GSAI-ML/LLaDA-8B-Base"]
PARAMS = {"bert-base-uncased": "110M", "gpt2": "117M",
          "bert-large-uncased": "340M", "Qwen/Qwen3-4B-Base": "4B",
          "GSAI-ML/LLaDA-8B-Base": "8B"}


def load_cells(dirpath, prefix):
    """Per-(model, corpus) records, de-duplicated across shards."""
    bucket = defaultdict(dict)
    kinds = {}
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


def short_name(model):
    """Display name for a crowded axis."""
    n = model.split("/")[-1]
    # NOT "-base": stripping it turns bert-base-uncased into "bert", which is
    # then indistinguishable from bert-large in the same axis
    for suffix in ("-uncased", "-Base"):
        n = n.replace(suffix, "")
    return n


def order_corpora(names):
    known = [c for c in CORPUS_ORDER if c in names]
    return known + sorted(n for n in names if n not in CORPUS_ORDER)


def order_models(names):
    known = [m for m in EVAL_ORDER if m in names]
    return known + sorted(n for n in names if n not in EVAL_ORDER)


def boot_median_ci(x, B=4000, seed=0):
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float)
    if len(x) < 5:
        return np.nan, np.nan
    m = np.median(rng.choice(x, size=(B, len(x)), replace=True), axis=1)
    return tuple(np.percentile(m, [2.5, 97.5]))


def rb(a, b):
    if len(a) < 2 or len(b) < 2:
        return np.nan
    st = mannwhitneyu(a, b, alternative="two-sided", method="asymptotic")
    return 2.0 * st.statistic / (len(a) * len(b)) - 1.0


# ---------------------------------------------------------------- figure 1
def fig_block_order(blk, kinds, outdir):
    if not blk:
        print("  fig1 skipped: no blkord_*.json yet")
        return
    models = order_models({m for m, _ in blk})
    corpora = order_corpora({c for _, c in blk})
    n = len(models)
    # Five panels across one text width squeeze the tick labels into each
    # other; wrap instead, at most three per row.
    # Three columns across a 6.5in text width leaves each panel about 2.2in,
    # which is too small to read.  Two columns give 3.2in each.
    ncol = 1 if n == 1 else (2 if n <= 6 else 3)
    nrow = (n + ncol - 1) // ncol
    # Sized to a 6.5in text width so LaTeX does not downscale it: a figure
    # wider than \textwidth has every label shrunk by the same factor.
    width = min(6.5, 3.1 * ncol + 0.5)
    fig, axes2d = plt.subplots(nrow, ncol,
                               figsize=(width, 1.95 * nrow + 0.3),
                               sharey=True, squeeze=False)
    flat = [a for row in axes2d for a in row]
    for a in flat[n:]:
        a.set_visible(False)
    axes = [flat]
    for ax, model in zip(flat, models):
        tidy(ax)
        # the null: a score that cannot tell the arrangements apart
        ax.axhline(0.5, color=NULLC, linewidth=0.8, linestyle=(0, (4, 2)),
                   zorder=1)
        xs = np.arange(len(corpora))
        for j, cat in enumerate(("causal", "noncausal")):
            med, lo, hi = [], [], []
            for corpus in corpora:
                recs = blk.get((model, corpus), {})
                v = [r["percentile_written"] for k, r in recs.items()
                     if k[0] == cat]
                if not v:
                    med.append(np.nan); lo.append(np.nan); hi.append(np.nan)
                    continue
                med.append(float(np.median(v)))
                a, b = boot_median_ci(v)
                lo.append(a); hi.append(b)
            med = np.array(med); lo = np.array(lo); hi = np.array(hi)
            # a small x offset keeps the two markers from overlapping, which
            # is the 2px-gap rule in print terms
            off = (j - 0.5) * 0.18
            ax.errorbar(xs + off, med, yerr=[med - lo, hi - med],
                        fmt=MARKERS[j], color=C[j], ecolor=C[j],
                        elinewidth=0.9, capsize=1.8, markersize=4.2,
                        markeredgecolor="white", markeredgewidth=0.5,
                        linestyle="none", zorder=3,
                        label="causal" if cat == "causal" else "non-causal")
        ax.set_xticks(xs)
        ax.set_xticklabels(corpora, rotation=35, ha="right")
        ax.set_title(f"{model.split('/')[-1]}  ({PARAMS.get(model, '?')}, "
                     f"{kinds.get(model, '?')})")
        ax.set_ylim(0.45, 1.02)
    for r in range(nrow):
        flat[r * ncol].set_ylabel("position of the written order\n"
                                  "among all 24 orders")
    # label the null on the line itself, not floating in the middle of the panel
    # the 0.50 line is explained in the caption; an in-figure note here
    # collided with the lowest data points
    # one legend for the whole figure, outside the data area: inside a panel it
    # collided with the null line
    h, l = flat[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.06),
               handletextpad=0.4, columnspacing=1.6)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(outdir, f"fig1_block_order.{ext}"))
    plt.close(fig)
    print("  fig1_block_order written")


# ---------------------------------------------------------------- figure 2
def fig_capacity(pll, toy_dir, outdir):
    rows = None
    p = os.path.join(toy_dir or "", "capacity_results.json")
    if os.path.isfile(p):
        rows = json.load(open(p)).get("rows")
    have_pll = bool(pll)
    if not rows and not have_pll:
        print("  fig2 skipped: neither capacity_results.json nor pll_*.json")
        return

    ncol = int(bool(rows)) + int(have_pll)
    fig, axes = plt.subplots(1, ncol, figsize=(3.1 * ncol + 0.3, 2.5),
                             squeeze=False)
    k = 0
    if rows:
        ax = tidy(axes[0][k]); k += 1
        mlm = [r for r in rows if r.get("kind") == "MLM"]
        ar = [r for r in rows if r.get("kind") == "AR"]
        if mlm:
            x = [r["params"] for r in mlm]
            y = [r["sigma"] for r in mlm]
            ax.plot(x, y, MARKERS[0] + "-", color=C[0], markeredgecolor="white",
                    markeredgewidth=0.5, zorder=3, label="masked (MLM)")
        if ar:
            # A log y-axis would span 18 decades to reach the AR value and the
            # MLM rise -- the point of this panel -- would flatten into a line.
            # So the axis is linear and the AR result is stated on the zero
            # line, which is where it sits to 20 significant figures.
            ax.axhline(0.0, color=C[1], linewidth=1.0, zorder=2)
            ax.annotate(f"autoregressive: $\\sigma = "
                        f"{ar[0]['sigma']:.1e}".replace("e-", r"\times10^{-")
                        + "}$ (machine zero)",
                        xy=(0.03, 0.0), xycoords=("axes fraction", "data"),
                        xytext=(0.03, 0.0012),
                        textcoords=("axes fraction", "data"),
                        fontsize=6.5, color=C[1], va="bottom")
        ax.set_xscale("log")
        ax.set_ylim(bottom=-0.0012)
        ax.set_xlabel("parameters")
        ax.set_ylabel("$\\sigma$  (exact, Schnakenberg)")
        ax.set_title("exactly solvable system\n(detailed balance: "
                     "$\\sigma_{\\mathrm{true}}=0$)")
        ax.legend(loc="upper left")
    if have_pll:
        ax = tidy(axes[0][k])
        base, large = "bert-base-uncased", "bert-large-uncased"
        corpora = order_corpora({c for _, c in pll})
        drawn = 0
        ends = []
        for corpus in corpora:
            vb = [r["sigma_block_per_T"]
                  for r in pll.get((base, corpus), {}).values()]
            vl = [r["sigma_block_per_T"]
                  for r in pll.get((large, corpus), {}).values()]
            if not vb or not vl:
                continue
            ax.plot([110, 340], [np.median(vb), np.median(vl)],
                    MARKERS[0] + "-", color=C[0], alpha=0.85,
                    markeredgecolor="white", markeredgewidth=0.5, zorder=3)
            ends.append((float(np.median(vl)), corpus))
            drawn += 1
        # labels at nearly equal heights overlapped; push them apart
        if ends:
            ends.sort()
            span = max(e[0] for e in ends) - min(e[0] for e in ends)
            gap = 0.055 * max(span, 1e-9)
            placed = []
            for y, name in ends:
                yy = y if not placed else max(y, placed[-1] + gap)
                placed.append(yy)
                ax.annotate(name, xy=(340, y), xytext=(348, yy),
                            textcoords="data", fontsize=6.5, color=INK_MUTED,
                            va="center",
                            arrowprops=(dict(arrowstyle="-", color=GRID,
                                             linewidth=0.5)
                                        if abs(yy - y) > 1e-12 else None))
        if drawn == 0:
            ax.text(0.5, 0.5, "bert-large not finished yet",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=7, color=INK_MUTED)
        ax.set_xlabel("parameters (M)")
        ax.set_ylabel("median $\\sigma_{block}$ per token")
        ax.set_title("BERT pair on the fixed texts")
        ax.set_xlim(70, 470)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(outdir, f"fig2_capacity.{ext}"))
    plt.close(fig)
    print("  fig2_capacity written")


# ---------------------------------------------------------------- figure 3
def fig_evaluators(pll, blk, kinds, outdir):
    """Effect size, and the decomposition of the within-text distance.

    An earlier version of this figure put median sigma for a masked and a
    causal evaluator side by side as bars.  That invites a comparison that
    cannot be made: a pseudo-log-likelihood sums conditionals on L-1 tokens
    and an autoregressive log P sums conditionals on k-1 tokens, so the two
    scales differ by construction and the ratio means nothing.  Only
    rank-based quantities and the percentile decomposition are comparable
    across scorer types, so only those are drawn.
    """
    if not pll and not blk:
        print("  fig3 skipped: no results yet")
        return
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.6))

    # (a) effect size by corpus and evaluator -- a rank statistic, comparable
    ax = tidy(axes[0])
    if pll:
        models = order_models({m for m, _ in pll})
        corpora = order_corpora({c for _, c in pll})
        w = 0.8 / max(len(models), 1)
        xs = np.arange(len(corpora))
        for j, model in enumerate(models):
            vals = []
            for corpus in corpora:
                recs = pll.get((model, corpus), {})
                if not recs:
                    vals.append(np.nan); continue
                a = [r["sigma_block_per_T"] for k, r in recs.items() if k[0] == "causal"]
                b = [r["sigma_block_per_T"] for k, r in recs.items() if k[0] == "noncausal"]
                vals.append(rb(a, b))
            ax.bar(xs + (j - (len(models) - 1) / 2) * w, vals, width=w * 0.86,
                   color=C[j % len(C)], zorder=3, linewidth=0,
                   label=f"{short_name(model)} "
                         f"({PARAMS.get(model, '?')}, {kinds.get(model, '?')})")
        ax.set_xticks(xs)
        ax.set_xticklabels(corpora, rotation=35, ha="right")
        ax.axhline(0.0, color=NULLC, linewidth=0.8)
        ax.set_ylabel("effect size $r$")
        ax.set_title("causal vs non-causal, between texts")
        # headroom so the legend never sits on top of a bar
        lo, hi = ax.get_ylim()
        ax.set_ylim(lo, hi + 0.42 * (hi - lo))
        ax.legend(loc="upper left", fontsize=6.5)

    # (b) the decomposition, from the within-text permutation test
    ax = tidy(axes[1])
    if blk:
        bmodels = order_models({m for m, _ in blk})
        bcorp = order_corpora({c for _, c in blk})
        auth, caus, labels, kinds_l = [], [], [], []
        for model in bmodels:
            a_, c_ = [], []
            for corpus in bcorp:
                recs = blk.get((model, corpus), {})
                pc = [r["percentile_written"] for k, r in recs.items() if k[0] == "causal"]
                pn = [r["percentile_written"] for k, r in recs.items() if k[0] == "noncausal"]
                if not pc or not pn:
                    continue
                a_.append(np.median(pn) - 0.5)
                c_.append(np.median(pc) - np.median(pn))
            if not a_:
                continue
            auth.append(float(np.median(a_)))
            caus.append(float(np.median(c_)))
            labels.append(f"{short_name(model)}\n({kinds.get(model, '?')})")
            kinds_l.append(kinds.get(model, "?"))
        if labels:
            xs = np.arange(len(labels))
            # a 2px-equivalent gap between the stacked segments, so the two
            # components never read as one bar
            ax.bar(xs, auth, width=0.55, color="#b9bcc0", zorder=3,
                   linewidth=0, label="any authored order")
            ax.bar(xs, caus, bottom=np.array(auth) + 0.004, width=0.55,
                   color=C[0], zorder=3, linewidth=0, label="causal order only")
            for x, a_v, c_v in zip(xs, auth, caus):
                ax.annotate(f"{c_v:+.3f}", xy=(x, a_v + c_v + 0.012),
                            ha="center", fontsize=6.5, color=C[0])
            ax.set_xticks(xs)
            ax.set_xticklabels(labels, fontsize=6.5, rotation=30, ha="right")
            ax.axhline(0.0, color=NULLC, linewidth=0.8)
            ax.set_ylabel("distance from the 0.50 null")
            ax.set_title("what that distance is made of, within text")
            lo, hi = ax.get_ylim()
            ax.set_ylim(lo, hi + 0.42 * (hi - lo))
            ax.legend(loc="upper left", fontsize=6.5)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(outdir, f"fig3_evaluators.{ext}"))
    plt.close(fig)
    print("  fig3_evaluators written")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pll", default="../order-intervention/results_pll")
    ap.add_argument("--blkord", default="../order-intervention/results_blkord")
    ap.add_argument("--toy", default="../bert-affinity")
    ap.add_argument("--outdir", default="figures")
    args = ap.parse_args()

    setup()
    os.makedirs(args.outdir, exist_ok=True)
    pll, kinds_p = load_cells(args.pll, "pll")
    blk, kinds_b = load_cells(args.blkord, "blkord")
    kinds = {**kinds_p, **kinds_b}
    print(f"# pll cells: {len(pll)}   blkord cells: {len(blk)}")

    fig_block_order(blk, kinds, args.outdir)
    fig_capacity(pll, args.toy, args.outdir)
    fig_evaluators(pll, blk, kinds, args.outdir)
    print(f"# figures in {args.outdir}/")


if __name__ == "__main__":
    main()
