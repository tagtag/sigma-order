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
fig1_block_order   The decisive result.  Where the AUTHORED sentence order sits
                   among all 4! = 24 orders of the same text, for causal and
                   non-causal texts, against the 0.50 null.  Within-text, so
                   length, vocabulary, style and topic are held fixed.
fig2_capacity      sigma_EP of Eq. (sigep), the entropy production of the
                   chain induced by a model's own conditionals, against model
                   capacity in the exactly solvable toy system.

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
PARAMS = {"bert-base-uncased": "110M", "gpt2": "124M",
          "bert-large-uncased": "340M", "Qwen/Qwen3-4B-Base": "4B",
          "GSAI-ML/LLaDA-8B-Base": "8B"}



def kind_str(kind):
    """Model class as printed; see the note in make_tables.py.  "causal" in
    the JSON means causal attention, and must not share a panel with the
    causal/non-causal text labels under that name."""
    return {"causal": "AR", "masked": "masked"}.get(kind, kind or "?")


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
def ar_only(models, kinds):
    """The autoregressive evaluators, in order.

    Delta exists only for a model that supplies a joint, so only these are
    drawn.  The masked runs in results_blkord/ were scored with a
    pseudo-log-likelihood; they are kept as a record and filtered out here,
    exactly as in make_tables.py, so the figure and the tables show the same
    evaluators.
    """
    return [m for m in order_models(models) if kinds.get(m) == "causal"]


def fig_block_order(blk, kinds, outdir):
    if not blk:
        print("  fig1 skipped: no blkord_*.json yet")
        return
    models = ar_only({m for m, _ in blk}, kinds)
    if not models:
        print("  fig1 skipped: no autoregressive evaluator in results_blkord")
        return
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
                     f"{kind_str(kinds.get(model))})")
        ax.set_ylim(0.45, 1.02)
    for r in range(nrow):
        flat[r * ncol].set_ylabel("position of the authored order\n"
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
def fig_capacity(toy_dir, outdir):
    """The exactly solvable system, alone.

    The right-hand panel put median sigma_block for the two BERT evaluators
    against parameter count.  That number is a pseudo-log-likelihood
    difference, not Delta, and the paper no longer reports it; a panel is not
    the place to keep a measurement the text has withdrawn.  What is left is
    the one reading in the figure that is exact.
    """
    rows = None
    p = os.path.join(toy_dir or "", "capacity_results.json")
    if os.path.isfile(p):
        rows = json.load(open(p)).get("rows")
    if not rows:
        print("  fig2 skipped: no capacity_results.json")
        return

    fig, axes = plt.subplots(1, 1, figsize=(3.4, 2.5), squeeze=False)
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
            # line, where it sits to within 4e-20 -- not "to 20 significant
            # figures", which an earlier caption said and which means nothing
            # for a value compared against zero.
            ax.axhline(0.0, color=C[1], linewidth=1.0, zorder=2)
            ax.annotate(f"autoregressive: $\\sigma_{{\\mathrm{{EP}}}} = "
                        f"{ar[0]['sigma']:.1e}".replace("e-", r"\times10^{-")
                        + "}$ (machine zero)",
                        xy=(0.03, 0.0), xycoords=("axes fraction", "data"),
                        xytext=(0.03, 0.0012),
                        textcoords=("axes fraction", "data"),
                        fontsize=6.5, color=C[1], va="bottom")
        ax.set_xscale("log")
        ax.set_ylim(bottom=-0.0012)
        ax.set_xlabel("parameters")
        ax.set_ylabel("$\\sigma_{\\mathrm{EP}}$  (exact, Schnakenberg)")
        ax.set_title("exactly solvable system\n(detailed balance: "
                     "$\\sigma_{\\mathrm{EP}}=0$ exactly)")
        ax.legend(loc="upper left")
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(outdir, f"fig2_capacity.{ext}"))
    plt.close(fig)
    print("  fig2_capacity written")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pll", default="../order-intervention/results_pll")
    ap.add_argument("--blkord", default="../order-intervention/results_blkord")
    ap.add_argument("--toy", default="../bert-affinity")
    ap.add_argument("--outdir", default="figures")
    args = ap.parse_args()

    setup()
    os.makedirs(args.outdir, exist_ok=True)
    # Delete the figures this script owns before drawing any of them.  A figure
    # whose measurements are missing is simply not drawn, which used to leave
    # whatever was already on disk in place -- a figure from an earlier run, or
    # one unpacked from a release tarball.  make_tables.py was given this guard
    # after a stale table shipped; the figures never were, and a stale panel
    # with the old model-class labels survived here until the PDF was read.
    import glob as _glob
    for _f in _glob.glob(os.path.join(args.outdir, "fig*_*.pdf")) + \
              _glob.glob(os.path.join(args.outdir, "fig*_*.png")):
        try:
            os.unlink(_f)
        except OSError:
            pass
    pll, kinds_p = load_cells(args.pll, "pll")
    blk, kinds_b = load_cells(args.blkord, "blkord")
    kinds = {**kinds_p, **kinds_b}
    print(f"# pll cells: {len(pll)}   blkord cells: {len(blk)}")

    fig_block_order(blk, kinds, args.outdir)
    fig_capacity(args.toy, args.outdir)

    # A figure that could not be drawn does not exist now, because everything
    # this script owns was deleted above.  Write a visible placeholder so the
    # document still compiles during a partial run, carrying the same TODO
    # marker the table stubs use; make_arxiv.sh refuses to package on it.
    for stem, what in (("fig1_block_order", "within-text permutation test"),
                       ("fig2_capacity", "capacity sweep")):
        path = os.path.join(args.outdir, stem + ".pdf")
        if os.path.exists(path):
            continue
        f, ax = plt.subplots(figsize=(6.0, 1.4))
        ax.axis("off")
        ax.text(0.5, 0.5, f"[TODO:{stem}] no measurements for the {what}",
                ha="center", va="center", fontsize=11)
        f.savefig(path, bbox_inches="tight")
        plt.close(f)
        print(f"  {stem}.pdf  STUB -- no measurements")

    print(f"# figures in {args.outdir}/")


if __name__ == "__main__":
    main()
