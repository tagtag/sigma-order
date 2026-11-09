#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared figure style for the paper.

Colour choices are not a matter of taste here.  The three categorical hues are
Okabe-Ito steps, assigned in a FIXED order (never cycled), and the set was
checked with the palette validator rather than eyeballed:

    #0072B2, #D55E00, #009E73   (light surface)
      lightness band    PASS
      chroma floor      PASS
      CVD separation    PASS  worst adjacent dE 11.0 (deutan), 30.9 (tritan)
      normal vision     PASS  worst adjacent dE 25.8
      contrast >= 3:1   PASS

Every series also carries a distinct marker, so identity is never colour alone
-- which matters for a paper that will be read in greyscale print.

Other rules followed: one y-axis per panel and never two scales in one
(sigma and the effect size go in separate panels), a legend whenever two or
more series are drawn, thin marks, and a grid that sits behind the data and
stays recessive.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# fixed categorical order; index 0 is always "causal", 1 always "non-causal"
C = ["#0072B2", "#D55E00", "#009E73"]
MARKERS = ["o", "s", "^"]
INK = "#1a1a1a"
INK_MUTED = "#6b6b6b"
GRID = "#dcdcdc"
NULLC = "#9a9a9a"


def setup():
    plt.rcParams.update({
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "font.family": "serif",
        "font.size": 8,
        "axes.labelsize": 8,
        "axes.titlesize": 8.5,
        "legend.fontsize": 7.5,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "axes.edgecolor": INK_MUTED,
        "axes.linewidth": 0.6,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_MUTED,
        "ytick.color": INK_MUTED,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 2.5,
        "ytick.major.size": 2.5,
        "lines.linewidth": 1.2,
        "lines.markersize": 4.0,
        "legend.frameon": False,
        "axes.grid": False,
    })


def tidy(ax, ygrid=True):
    """Recessive grid behind the data; no top or right spine."""
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if ygrid:
        ax.yaxis.grid(True, color=GRID, linewidth=0.5, zorder=0)
        ax.set_axisbelow(True)
    return ax
