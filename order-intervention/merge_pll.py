#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge pll_sigma.py shards and build the evaluator comparison.

Each pll_sigma.py run writes one JSON per (model, corpus, shard) with the
per-text records and the statistics of that shard alone.  This merges the
shards of a (model, corpus) pair, recomputes the statistics on the whole
corpus, and lays the evaluators side by side.

The table to read
-----------------
For each corpus and each evaluator:

    med sigma   the median block-level entropy production over ALL texts.
                The question "is sigma a property of the text or of the
                autoregressive factorisation" is answered by this column: a
                direction-neutral evaluator that still reports a large sigma
                says the asymmetry is in the text.
    r           the causal/non-causal effect size, which is what Sagawa's
                claim rests on.  r ~ 0 under a masked evaluator means the
                separation does not survive removing the evaluator's
                directional bias.

The decisive line is the SCALE-MATCHED PAIR:

    bert-base-uncased  110M  masked
    gpt2               117M  causal

Same era, near-identical size.  A difference between these two is a
difference of directionality, not of capacity -- which is the one objection a
single-model result could not answer.

    python3 merge_pll.py --dir results_pll
"""

import argparse
import glob
import json
import os
from collections import defaultdict

import numpy as np
from scipy.stats import mannwhitneyu

# evaluator metadata: parameter count and whether it is direction neutral.
# Used only for the report, never for the statistics.
KNOWN = {
    "bert-base-uncased": (110, "masked"),
    "bert-large-uncased": (340, "masked"),
    "answerdotai_ModernBERT-base": (150, "masked"),
    "answerdotai_ModernBERT-large": (395, "masked"),
    "GSAI-ML_LLaDA-8B-Base": (8000, "masked"),
    "gpt2": (117, "causal"),
    "gpt2-medium": (345, "causal"),
    "gpt2-large": (774, "causal"),
    "Qwen_Qwen3-4B-Base": (4000, "causal"),
}
# the pair whose comparison the argument turns on
MATCHED_PAIR = ("bert-base-uncased", "gpt2")


def rank_biserial(a, b):
    if len(a) < 2 or len(b) < 2:
        return float("nan"), float("nan")
    st = mannwhitneyu(a, b, alternative="two-sided", method="asymptotic")
    return 2.0 * st.statistic / (len(a) * len(b)) - 1.0, float(st.pvalue)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", default="pll_comparison.json")
    args = ap.parse_args()

    # (model, corpus) -> {(category, index): record}, so re-running a shard
    # cannot double-count a text
    bucket = defaultdict(dict)
    kinds = {}
    shards = defaultdict(set)
    for f in sorted(glob.glob(os.path.join(args.dir, "pll_*.json"))):
        if os.path.basename(f).startswith("pll_comparison"):
            continue
        d = json.load(open(f))
        if "records" not in d:
            continue
        model = d["model"]
        corpus = d["corpus"].replace("fixed_text_", "").replace(".json", "")
        kinds[model] = d["kind"]
        shards[(model, corpus)].add(d.get("shard", "0/1"))
        for r in d["records"]:
            bucket[(model, corpus)][(r["category"], r["index"])] = r

    if not bucket:
        raise SystemExit(f"no pll_*.json with records in {args.dir}")

    out = {"dir": args.dir, "cells": {}}
    rows = []
    for (model, corpus), recs in sorted(bucket.items()):
        rs = list(recs.values())
        cell = {"model": model, "kind": kinds[model], "corpus": corpus,
                "n": len(rs), "shards": sorted(shards[(model, corpus)])}
        for key, lab in (("sigma_block_per_T", "block"),
                         ("sigma_token_per_T", "token")):
            a = np.array([r[key] for r in rs if r["category"] == "causal"], float)
            b = np.array([r[key] for r in rs if r["category"] == "noncausal"], float)
            allv = np.concatenate([a, b]) if len(a) + len(b) else np.array([])
            r_rb, p = rank_biserial(a, b)
            cell[lab] = {
                "n_causal": len(a), "n_noncausal": len(b),
                "median_all": float(np.median(allv)) if len(allv) else None,
                "median_causal": float(np.median(a)) if len(a) else None,
                "median_noncausal": float(np.median(b)) if len(b) else None,
                "rank_biserial": float(r_rb), "p": p,
            }
        out["cells"][f"{model}|{corpus}"] = cell
        rows.append(cell)

    models = sorted({c["model"] for c in rows},
                    key=lambda m: (KNOWN.get(m.replace("/", "_"), (0, ""))[0], m))
    corpora = sorted({c["corpus"] for c in rows})

    print("=" * 104)
    print("Block reversal: does the entropy production survive a "
          "direction-neutral evaluator?")
    print("  med sigma = median over all texts;  r = causal vs non-causal "
          "effect size")
    print("=" * 104)
    hdr = f"{'evaluator':<28}{'params':>8}{'dir':>9}"
    for c in corpora:
        hdr += f"{c[:9]:>19}"
    print(hdr)
    print(f"{'':<28}{'':>8}{'':>9}" + "".join(
        f"{'med sigma / r':>19}" for _ in corpora))
    for m in models:
        meta = KNOWN.get(m.replace("/", "_"), (None, kinds.get(m, "?")))
        pstr = f"{meta[0]}M" if meta[0] and meta[0] < 1000 else (
            f"{meta[0]//1000}B" if meta[0] else "?")
        line = f"{m[:27]:<28}{pstr:>8}{kinds[m]:>9}"
        for c in corpora:
            cell = out["cells"].get(f"{m}|{c}")
            if cell is None:
                line += f"{'--':>19}"
            else:
                bl = cell["block"]
                line += f"{bl['median_all']:>11.4f} /{bl['rank_biserial']:>6.3f}"
        print(line)

    print()
    print("=" * 104)
    print("Token reversal (destroys grammar; shown for completeness, not for "
          "the causal claim)")
    print("=" * 104)
    for m in models:
        line = f"{m[:27]:<28}{'':>8}{kinds[m]:>9}"
        for c in corpora:
            cell = out["cells"].get(f"{m}|{c}")
            if cell is None:
                line += f"{'--':>19}"
            else:
                tk = cell["token"]
                line += f"{tk['median_all']:>11.4f} /{tk['rank_biserial']:>6.3f}"
        print(line)

    # ---------------- the scale-matched pair ----------------
    mk, ck = MATCHED_PAIR
    have = [c for c in corpora
            if f"{mk}|{c}" in out["cells"] and f"{ck}|{c}" in out["cells"]]
    if have:
        print()
        print("=" * 104)
        print(f"Scale-matched pair: {mk} (masked) vs {ck} (causal)")
        print("  A difference here is directionality, not capacity.")
        print("=" * 104)
        print(f"{'corpus':<12}{'sigma masked':>15}{'sigma causal':>15}"
              f"{'ratio*':>9}{'r masked':>11}{'r causal':>11}")
        print("  * the ratio is printed for completeness only; the two sigma "
              "scales are not commensurable")
        pair = {}
        for c in have:
            bm = out["cells"][f"{mk}|{c}"]["block"]
            bc = out["cells"][f"{ck}|{c}"]["block"]
            # kept in the JSON for completeness, but it compares a
            # pseudo-log-likelihood difference with a log-probability
            # difference, which are on different scales by construction
            ratio = (bm["median_all"] / bc["median_all"]
                     if bc["median_all"] else float("nan"))
            pair[c] = {"sigma_masked": bm["median_all"],
                       "sigma_causal": bc["median_all"], "ratio": ratio,
                       "r_masked": bm["rank_biserial"],
                       "r_causal": bc["rank_biserial"],
                       "p_masked": bm["p"], "p_causal": bc["p"]}
            print(f"{c:<12}{bm['median_all']:>15.5f}{bc['median_all']:>15.5f}"
                  f"{ratio:>9.3f}{bm['rank_biserial']:>11.4f}"
                  f"{bc['rank_biserial']:>11.4f}")
        out["matched_pair"] = {"masked": mk, "causal": ck, "by_corpus": pair}

        rm = np.array([v["r_masked"] for v in pair.values()])
        rc = np.array([v["r_causal"] for v in pair.values()])
        sm = np.array([v["sigma_masked"] for v in pair.values()])
        scv = np.array([v["sigma_causal"] for v in pair.values()])
        out["matched_pair"]["summary"] = {
            "n_corpora": len(have),
            "median_r_masked": float(np.median(rm)),
            "median_r_causal": float(np.median(rc)),
            "median_sigma_masked": float(np.median(sm)),
            "median_sigma_causal": float(np.median(scv)),
            "corpora_masked_separates": int((np.abs(rm) > 0.2).sum()),
            "corpora_causal_separates": int((np.abs(rc) > 0.2).sum()),
        }

        print()
        print("=" * 104)
        print("Reading")
        print("=" * 104)
        s = out["matched_pair"]["summary"]
        print(f"  median sigma_block : masked {s['median_sigma_masked']:+.5f}"
              f"   causal {s['median_sigma_causal']:+.5f}")
        print(f"  median r           : masked {s['median_r_masked']:+.4f}"
              f"   causal {s['median_r_causal']:+.4f}")
        print(f"  corpora with |r|>0.2: masked "
              f"{s['corpora_masked_separates']}/{len(have)}"
              f"   causal {s['corpora_causal_separates']}/{len(have)}")
        print()
        print("  NOTE: the two sigma columns are NOT commensurable and no")
        print("  verdict is drawn from their ratio.  A pseudo-log-likelihood")
        print("  sums conditionals on L-1 tokens; an autoregressive log P sums")
        print("  conditionals on k-1 tokens.  The scales differ by")
        print("  construction, so a smaller masked sigma says nothing about")
        print("  whether the asymmetry survived.  Only the rank-based effect")
        print("  size r is comparable across scorer types, and the reading")
        print("  below uses r alone.")
        print()
        nm, nc = s["corpora_masked_separates"], s["corpora_causal_separates"]
        rm_, rc_ = s["median_r_masked"], s["median_r_causal"]
        if nm > nc and rm_ > rc_:
            print("  The direction-neutral evaluator separates causal from")
            print("  non-causal BETTER than the autoregressive one at matched")
            print(f"  scale ({nm}/{len(have)} corpora vs {nc}/{len(have)};"
                  f" median r {rm_:+.3f} vs {rc_:+.3f}).")
            print("  So the separation is not an artefact of the evaluator's")
            print("  training direction -- removing that direction sharpens it.")
            print("  What the autoregressive evaluator adds is an artefact in")
            print("  the other direction: see the within-text permutation test,")
            print("  where it scores the authored order of NON-CAUSAL text as")
            print("  nearly as special as causal text, compressing the")
            print("  difference.")
        elif nc > nm and rc_ > rm_:
            print("  The autoregressive evaluator separates causal from")
            print("  non-causal better than the direction-neutral one at")
            print(f"  matched scale ({nc}/{len(have)} vs {nm}/{len(have)};"
                  f" median r {rc_:+.3f} vs {rm_:+.3f}).")
            print("  Part of the separation is then carried by the evaluator's")
            print("  training direction rather than by the text.")
        else:
            print(f"  Masked {nm}/{len(have)} corpora (median r {rm_:+.3f}),"
                  f" causal {nc}/{len(have)} (median r {rc_:+.3f}).")
            print("  Too close to call from these corpora; report both.")

    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
    print(f"\n# wrote {args.out}")


if __name__ == "__main__":
    main()
