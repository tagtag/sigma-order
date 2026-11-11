#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Independent reproduction of the statistical layer of

  T. Sagawa, "Stochastic Thermodynamics for Autoregressive Generative Models:
  A Non-Markovian Perspective", PRX Intelligence (accepted 2026), DOI 10.1103/tv38-b23y,
  arXiv:2604.07867, code/data: https://github.com/taksagawa/Paper2026

What this checks
----------------
The fixed-text experiment reduces to one quantity per text,

    sigma_token = log P(forward token sequence) - log P(token-reversed sequence)
    sigma_block = log P(forward token sequence) - log P(block-reversed sequence)

both evaluated with the SAME autoregressive model (protocol reversal, not
Bayesian retrodiction).  The repository ships the raw per-text log-likelihoods
(ll_fwd, ll_token_rev, ll_block_rev), so the entire statistical analysis can be
recomputed WITHOUT running any language model.  This script:

  1. recomputes sigma_token and sigma_block from the raw log-likelihoods and
     checks them against the shipped sigma columns,
  2. recomputes the causal-vs-noncausal Mann-Whitney U test and the
     rank-biserial correlation r for every corpus,
  3. compares the result with the repository's own mann_whitney_results_*.csv.

Reproducing this layer establishes the baseline that an any-order (masked
diffusion) extension has to match: swapping the evaluator changes only the
three log-likelihood columns, nothing downstream.

Usage
-----
    python3 reproduce_sagawa_stats.py --repo /path/to/Paper2026
"""

import argparse
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu


def rank_biserial(a, b):
    """r = 2U/(n1 n2) - 1 with U computed for sample a against sample b."""
    U = mannwhitneyu(a, b, alternative="two-sided", use_continuity=True).statistic
    return 2.0 * U / (len(a) * len(b)) - 1.0, U


def analyse_corpus(path, tag=None):
    df = pd.read_csv(path)
    out = {"file": path, "tag": tag, "n_rows": len(df)}

    # --- 1. sigma definition check -----------------------------------
    st = df["ll_fwd"] - df["ll_token_rev"]
    sb = df["ll_fwd"] - df["ll_block_rev"]
    out["max_abs_err_sigma_token"] = float(np.max(np.abs(st - df["sigma_token"])))
    out["max_abs_err_sigma_block"] = float(np.max(np.abs(sb - df["sigma_block"])))
    # per-T normalisation
    out["max_abs_err_sigma_token_per_T"] = float(
        np.max(np.abs(st / df["T"] - df["sigma_token_per_T"])))
    out["max_abs_err_sigma_block_per_T"] = float(
        np.max(np.abs(sb / df["T"] - df["sigma_block_per_T"])))

    # --- 2. Mann-Whitney / rank-biserial -----------------------------
    c = df[df["category"] == "causal"]
    n = df[df["category"] == "noncausal"]
    out["n_causal"], out["n_noncausal"] = len(c), len(n)
    # Both p-value conventions are reported: the paper's Methods text states a
    # two-sided ASYMPTOTIC test with continuity correction, while the shipped
    # mann_whitney_test.py (GPT-2 / Table II) calls scipy with method="exact".
    # Table III (Qwen3) matches the asymptotic values.  Reporting both makes the
    # discrepancy explicit and shows it changes no conclusion.
    for key, col in (("token", "sigma_token_per_T"), ("block", "sigma_block_per_T")):
        r, U = rank_biserial(c[col].values, n[col].values)
        out[f"U_{key}"] = float(U)
        out[f"r_{key}"] = float(r)
        out[f"p_{key}_exact"] = float(mannwhitneyu(
            c[col], n[col], alternative="two-sided", method="exact").pvalue)
        out[f"p_{key}_asymptotic_cc"] = float(mannwhitneyu(
            c[col], n[col], alternative="two-sided", use_continuity=True,
            method="asymptotic").pvalue)
        out[f"median_causal_{key}"] = float(np.median(c[col]))
        out[f"median_noncausal_{key}"] = float(np.median(n[col]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="path to the Paper2026 checkout")
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "sagawa_repro.json"))
    args = ap.parse_args()

    files = []
    # Table II family: gpt2/text_sets/fixed_text_output_<GEN>/raw_results_fixed_texts.csv
    for f in sorted(glob.glob(os.path.join(
            args.repo, "gpt2", "text_sets*", "fixed_text_output_*",
            "raw_results_fixed_texts.csv"))):
        tag = "TII/" + os.path.basename(os.path.dirname(f)).replace("fixed_text_output_", "")
        files.append((f, tag))
    # Table III family: gpt2/text_sets2/<evaluator>/raw_results_fixed_texts_<GEN>.csv
    for f in sorted(glob.glob(os.path.join(
            args.repo, "gpt2", "text_sets2", "*", "raw_results_fixed_texts_*.csv"))):
        ev = os.path.basename(os.path.dirname(f))
        gen = os.path.basename(f).replace("raw_results_fixed_texts_", "").replace(".csv", "")
        files.append((f, f"{ev}/{gen}"))
    if not files:
        sys.exit(f"no raw_results_fixed_texts*.csv found under {args.repo}")

    rows = [analyse_corpus(f, tag) for f, tag in files]

    print("=" * 112)
    print("1) sigma definition check:  sigma = ll_fwd - ll_rev")
    print("   (max |recomputed - shipped| over all texts; float64 noise expected)")
    print("=" * 112)
    print(f"{'corpus':<24}{'rows':>6}{'err sig_tok':>14}{'err sig_blk':>14}"
          f"{'err tok/T':>14}{'err blk/T':>14}")
    for r in rows:
        print(f"{r['tag']:<24}{r['n_rows']:>6}{r['max_abs_err_sigma_token']:>14.2e}"
              f"{r['max_abs_err_sigma_block']:>14.2e}"
              f"{r['max_abs_err_sigma_token_per_T']:>14.2e}"
              f"{r['max_abs_err_sigma_block_per_T']:>14.2e}")

    for key in ("token", "block"):
        print()
        print("=" * 112)
        print(f"2) causal vs noncausal, {key}-level reversal "
              f"(U and r recomputed; both p conventions shown)")
        print("=" * 112)
        print(f"{'corpus':<24}{'nC':>4}{'nN':>4}{'U':>8}{'r':>10}"
              f"{'p_exact':>14}{'p_asym+cc':>14}{'med_C':>10}{'med_N':>10}")
        for r in rows:
            print(f"{r['tag']:<24}{r['n_causal']:>4}{r['n_noncausal']:>4}"
                  f"{r[f'U_{key}']:>8.0f}{r[f'r_{key}']:>10.4f}"
                  f"{r[f'p_{key}_exact']:>14.4e}{r[f'p_{key}_asymptotic_cc']:>14.4e}"
                  f"{r[f'median_causal_{key}']:>10.4f}{r[f'median_noncausal_{key}']:>10.4f}")

    # --- 3. compare with the repository's own test output ------------
    print()
    print("=" * 112)
    print("3) repository's own mann_whitney_results_*.csv (for direct comparison)")
    print("=" * 112)
    shipped = sorted(glob.glob(os.path.join(
        args.repo, "gpt2", "text_sets*", "**", "mann_whitney_results_*.csv"),
        recursive=True))
    # The shipped values are also KEPT, at full precision, not only printed.
    # Printing them beside ours left the comparison to the eye, and a printed
    # table rounds: a p of 4.473e-06 shows as 0.000004, which cannot be
    # compared with anything.  compare_repro.py reads what is stored here.
    shipped_rows = {}
    for f in shipped:
        tag = (os.path.basename(os.path.dirname(f)) + "/"
               + os.path.basename(f).replace("mann_whitney_results_", "").replace(".csv", ""))
        d = pd.read_csv(f)
        keep = [c for c in ("label", "U", "p", "rank_biserial_r") if c in d.columns]
        print(f"\n--- {tag} ---")
        print(d[keep].to_string(index=False) if keep else d.to_string(index=False))
        if "label" in d.columns:
            shipped_rows[tag] = {
                str(row["label"]): {
                    k: (float(row[k]) if k in d.columns and pd.notna(row[k])
                        else None)
                    for k in ("U", "p", "rank_biserial_r")
                }
                for _, row in d.iterrows()
            }

    with open(args.out, "w") as fh:
        json.dump({"recomputed": rows, "shipped": shipped_rows}, fh, indent=1)
    print(f"\n# wrote {args.out}")
    print("# run  python3 -I compare_repro.py  to check the two against "
          "each other")


if __name__ == "__main__":
    main()
