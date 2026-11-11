#!/usr/bin/env python3
"""Compare our recomputed statistics against the ones the source repository ships.

`reproduce_sagawa_stats.py` produced two tables: what we recompute from the
released per-text values, and what the repository's own
`mann_whitney_results_*.csv` files contain.  Putting them side by side was as
far as it went -- the comparison itself was left to the eye, while the paper
states that "every effect size and rank statistic reported there is
recovered".  A claim checked by eye is a claim nothing re-checks when the
inputs change.

    python3 -I compare_repro.py                 # from bert-affinity/
    python3 -I compare_repro.py --json X --log Y

Two modes, and the script says which one it ran in:

  exact      the JSON carries the shipped values at full precision, because
             reproduce_sagawa_stats.py stored them.  Differences are real.
  truncated  only the old log is available, whose table was printed to six
             decimal places.  A shipped p of 4.473e-06 appears there as
             0.000004, so p can be checked to about one significant figure
             and no further.  U and r are unaffected.

Re-run reproduce_sagawa_stats.py against the source repository to get the
exact mode.  Exit status is 1 on any disagreement beyond the tolerance the
mode allows, or if a corpus is in one source and not the other -- a silently
dropped corpus would otherwise improve the agreement it is meant to test.
"""

import argparse
import json
import os
import re
import sys

TOL_U = 1e-6          # same integer ranks on both sides; noise only
TOL_R = 1e-5          # the shipped CSV prints r to six decimals
TOL_P_REL_EXACT = 1e-6
TOL_P_REL_TRUNC = 0.5   # six decimal places leaves ~1 significant figure

LABEL = {"token": "sigma_token_per_T", "block": "sigma_block_per_T"}
ALIAS = {"statistical test": "TII"}   # the log names a family by its directory


def canon(tag):
    fam, _, rest = tag.partition("/")
    return f"{ALIAS.get(fam, fam)}/{rest}"


def parse_log(path):
    """{corpus: {'token': (U, p, r), ...}} from section 3 of the log."""
    out, cur, inside = {}, None, False
    for line in open(path, encoding="utf-8"):
        if line.startswith("3) repository"):
            inside = True
            continue
        if not inside:
            continue
        m = re.match(r"^--- (.+?) ---\s*$", line)
        if m:
            cur = m.group(1).strip()
            out[cur] = {}
            continue
        if cur is None:
            continue
        # the "(outliers removed)" rows deliberately do not match: the
        # paper's statistics are the full-sample ones
        m = re.match(r"^\s*sigma_(token|block)_per_T\s+([0-9.eE+-]+)\s+"
                     r"([0-9.eE+-]+)\s+([0-9.eE+-]+)\s*$", line)
        if m:
            kind, u, p, r = m.groups()
            out[cur][kind] = (float(u), float(p), float(r))
    return {k: v for k, v in out.items() if v}


def from_json_shipped(shipped):
    """The same shape, from values stored at full precision."""
    out = {}
    for tag, rows in shipped.items():
        cell = {}
        for kind, label in LABEL.items():
            row = rows.get(label)
            if row and row.get("U") is not None:
                cell[kind] = (float(row["U"]), float(row["p"]),
                              float(row["rank_biserial_r"]))
        if cell:
            out[tag] = cell
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=os.path.join(here, "sagawa_repro.json"))
    ap.add_argument("--log", default=os.path.join(here, "sagawa_repro.log"))
    args = ap.parse_args()

    blob = json.load(open(args.json))
    if isinstance(blob, dict) and "recomputed" in blob:
        rows = blob["recomputed"]
        shipped_raw = blob.get("shipped") or {}
    else:                                   # the older bare-list format
        rows, shipped_raw = blob, {}

    if shipped_raw:
        mode, tol_p = "exact", TOL_P_REL_EXACT
        shipped = {canon(k): v for k, v in from_json_shipped(shipped_raw).items()}
    elif os.path.isfile(args.log):
        mode, tol_p = "truncated", TOL_P_REL_TRUNC
        shipped = {canon(k): v for k, v in parse_log(args.log).items()}
    else:
        print("no shipped statistics to compare against")
        return 1

    recomputed = {canon(r["tag"]): r for r in rows}
    bad = []
    for t in sorted(set(recomputed) - set(shipped)):
        bad.append(f"{t}: recomputed, but no shipped statistics for it")
    for t in sorted(set(shipped) - set(recomputed)):
        bad.append(f"{t}: shipped, but we did not recompute it")

    worst = {"U": (0.0, ""), "r": (0.0, ""), "p": (0.0, "")}
    n = 0
    for tag in sorted(set(recomputed) & set(shipped)):
        ours, theirs = recomputed[tag], shipped[tag]
        for kind in ("token", "block"):
            if kind not in theirs:
                bad.append(f"{tag}/{kind}: missing from the shipped table")
                continue
            u_t, p_t, r_t = theirs[kind]
            du = abs(ours[f"U_{kind}"] - u_t)
            dr = abs(ours[f"r_{kind}"] - r_t)
            # p: the paper's two tables use different scipy conventions
            # (exact, and asymptotic with continuity correction), which the
            # reproduction script documents, so the closer of ours must match
            dp = min(abs(ours[f"p_{kind}_exact"] - p_t),
                     abs(ours[f"p_{kind}_asymptotic_cc"] - p_t))
            dp_rel = dp / max(abs(p_t), 1e-300)
            n += 1
            for key, val in (("U", du), ("r", dr), ("p", dp_rel)):
                if val > worst[key][0]:
                    worst[key] = (val, f"{tag}/{kind}")
            if du > TOL_U:
                bad.append(f"{tag}/{kind}: U {ours[f'U_{kind}']} vs {u_t}")
            if dr > TOL_R:
                bad.append(f"{tag}/{kind}: r {ours[f'r_{kind}']:.6f} vs {r_t:.6f}")
            if dp_rel > tol_p:
                bad.append(f"{tag}/{kind}: p {ours[f'p_{kind}_exact']:.6e} / "
                           f"{ours[f'p_{kind}_asymptotic_cc']:.6e} "
                           f"vs shipped {p_t:.6e}")

    print(f"mode: {mode}"
          + ("" if mode == "exact" else
             "  (p checkable to about one significant figure only; "
             "re-run reproduce_sagawa_stats.py for the exact comparison)"))
    print(f"compared {n} (corpus, reversal) pairs across "
          f"{len(set(recomputed) & set(shipped))} corpora")
    print(f"  worst |dU|      = {worst['U'][0]:.3g}   {worst['U'][1]}")
    print(f"  worst |dr|      = {worst['r'][0]:.3g}   {worst['r'][1]}")
    print(f"  worst rel |dp|  = {worst['p'][0]:.3g}   {worst['p'][1]}")
    errs = [r[f"max_abs_err_sigma_{k}{s}"] for r in rows
            for k in ("token", "block") for s in ("", "_per_T")
            if f"max_abs_err_sigma_{k}{s}" in r]
    if errs:
        print(f"  worst |sigma recomputed - shipped| = {max(errs):.3g}")

    if bad:
        print(f"\n{len(bad)} disagreement(s):")
        for b in bad:
            print("  " + b)
        return 1
    print("\nevery shipped U, r and p is recovered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
