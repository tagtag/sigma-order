#!/usr/bin/env python3
"""The midrank's grid is 1/2n!, not 1/n!.  Checked against the measurements.

Section 5.3 of the paper states a resolution for the midrank, and
Sections 1, 4.2 and 6.1 read numbers in units of it.  Until #253 all of them
said the grid was 1/n!.  It is not.  Equation (midrank) is

    pct = [ #{Delta < Delta_id} + (1/2) #{Delta = Delta_id} ] / n!

so, writing a for the count strictly below and t >= 1 for the number of
arrangements tied with the authored one (itself included),

    2 n! pct = 2a + t ,

an integer, and an odd one whenever t is odd -- the ordinary case t = 1.
The midrank therefore lands halfway between the multiples of 1/n! and the
grid is twice as fine as the paper said.  The paper's own generated numbers
already showed it: the authored component printed as 8.5 and 9.5 steps,
which are 17/48 and 19/48.  The causal component printed as 1 to 2 steps
only because make_tables.py rounded; on the right grid it is 2 to 4.

This script checks the claim on the measured values rather than on the
argument above, and fails if any of it is false:

  1. every midrank is a multiple of 1/2n!;
  2. some midrank is NOT a multiple of 1/n!, so the finer grid is the
     real one and not a technicality;
  3. every per-cell median, and every component built from them, is on
     the 1/4n! grid -- a median over an even count is a mean of two
     values on the 1/2n! grid, so 1/4n! is what it is guaranteed, and
     anything coarser than that would mean the records are not what
     Eq.(midrank) produces.  How many of them land on the finer 1/2n!
     grid is reported and not required: the paper quotes them in grid
     units to a tenth of a step for exactly this reason;
  4. the smallest non-zero distance from the 0.50 null that any text
     attains is exactly 1/2n!.

Usage, from order-intervention/:

    python3 -I check_grid_resolution.py
    python3 -I check_grid_resolution.py --blkord results_blkord

Writes nothing.  Exit status 0 if every check passes, 1 otherwise.
"""

import argparse
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np

TOL = 1e-9


def load_cells(dirpath, prefix="blkord"):
    """Same shape as make_tables.py's load_cells, so the two agree."""
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


def on_grid(value, denom):
    """Is value an integer multiple of 1/denom?"""
    return abs(value * denom - round(value * denom)) <= TOL * max(1.0, denom)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blkord", default="results_blkord")
    args = ap.parse_args()

    blk, kinds = load_cells(args.blkord)
    if not blk:
        print(f"FAIL  no blkord cells under {args.blkord}")
        return 1

    nperms = {int(r["n_perms"]) for recs in blk.values() for r in recs.values()
              if "n_perms" in r}
    if len(nperms) != 1:
        print(f"FAIL  the cells do not share one n!: {sorted(nperms)}")
        return 1
    nfac = nperms.pop()
    fine, coarse = 2 * nfac, nfac

    print(f"cells            {len(blk)}")
    print(f"n!               {nfac}")
    print(f"claimed grid     1/{fine} = {1.0 / fine:.6f}")
    print(f"previous claim   1/{coarse} = {1.0 / coarse:.6f}")
    print()

    pcts = [float(r["percentile_written"])
            for recs in blk.values() for r in recs.values()
            if np.isfinite(r.get("percentile_written", float("nan")))]
    if not pcts:
        print("FAIL  no finite midranks")
        return 1

    failures = []

    # ---- 1. every midrank on the 1/2n! grid -----------------------------
    off_fine = [v for v in pcts if not on_grid(v, fine)]
    print(f"[1] midranks on the 1/{fine} grid        "
          f"{len(pcts) - len(off_fine)}/{len(pcts)}")
    if off_fine:
        failures.append(f"{len(off_fine)} midranks off the 1/{fine} grid, "
                        f"e.g. {off_fine[0]!r}")

    # ---- 2. the finer grid is the real one ------------------------------
    off_coarse = [v for v in pcts if not on_grid(v, coarse)]
    half = len(off_coarse)
    print(f"[2] midranks NOT on the 1/{coarse} grid      "
          f"{half}/{len(pcts)}"
          + ("   <- the old claim was false" if half else ""))
    if not off_coarse:
        failures.append(
            f"every midrank is a multiple of 1/{coarse}; the 1/{fine} grid "
            "would then be an overstatement in the other direction")

    # ---- 3. medians and components --------------------------------------
    # A median over an even count is a mean of two values on the 1/2n!
    # grid, so 1/4n! is guaranteed and 1/2n! is not.  The paper does not
    # claim the finer one for them; it quotes them to a tenth of a step.
    guaranteed = 2 * fine
    med_off, comp_off, meds, comps = [], [], [], []
    for key, recs in sorted(blk.items()):
        for cat in ("causal", "noncausal"):
            vals = [float(r["percentile_written"]) for k, r in recs.items()
                    if k[0] == cat
                    and np.isfinite(r.get("percentile_written", float("nan")))]
            if not vals:
                continue
            m = float(np.median(vals))
            meds.append(m)
            if not on_grid(m, guaranteed):
                med_off.append((key, cat, m, len(vals)))
        pc = [float(r["percentile_written"]) for k, r in recs.items()
              if k[0] == "causal"
              and np.isfinite(r.get("percentile_written", float("nan")))]
        pn = [float(r["percentile_written"]) for k, r in recs.items()
              if k[0] == "noncausal"
              and np.isfinite(r.get("percentile_written", float("nan")))]
        if pc and pn:
            for name, v in (("causal", float(np.median(pc)) - float(np.median(pn))),
                            ("authored", float(np.median(pn)) - 0.5)):
                comps.append(v)
                if not on_grid(v, guaranteed):
                    comp_off.append((key, name, v))
    on_fine = sum(1 for v in meds + comps if on_grid(v, fine))
    print(f"[3] medians + components on 1/{guaranteed}      "
          f"{len(meds) + len(comps) - len(med_off) - len(comp_off)}"
          f"/{len(meds) + len(comps)}")
    print(f"    of those, also on 1/{fine}          "
          f"{on_fine}/{len(meds) + len(comps)}"
          "   (reported, not required)")
    if med_off:
        k, cat, m, n = med_off[0]
        failures.append(f"{len(med_off)} cell medians off the 1/{guaranteed} "
                        f"grid, e.g. {k[0]}/{k[1]} {cat} = {m!r} over {n} texts")
    if comp_off:
        k, name, v = comp_off[0]
        failures.append(f"{len(comp_off)} components off the 1/{guaranteed} "
                        f"grid, e.g. {k[0]}/{k[1]} {name} = {v!r}")

    # ---- 4. the smallest non-zero reading --------------------------------
    dists = [abs(v - 0.5) for v in pcts]
    nz = [d for d in dists if d > TOL]
    smallest = min(nz) if nz else float("nan")
    print(f"[4] smallest non-zero |pct - 0.50|     {smallest:.6f}"
          f"   (1/{fine} = {1.0 / fine:.6f})")
    if not nz:
        failures.append("every text sits at the null; nothing to resolve")
    elif abs(smallest - 1.0 / fine) > TOL * fine:
        failures.append(f"the smallest non-zero distance is {smallest!r}, "
                        f"not 1/{fine} = {1.0 / fine!r}")
    at_null = len(dists) - len(nz)
    if at_null:
        print(f"    texts exactly at the null          {at_null}"
              "   (all n! tied; reported at the null)")

    print()
    if failures:
        for f in failures:
            print(f"FAIL  {f}")
        return 1
    print(f"PASS  the midrank lives on the 1/{fine} grid, and {half} of "
          f"{len(pcts)} midranks")
    print(f"      are off the 1/{coarse} grid the paper used to claim.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
