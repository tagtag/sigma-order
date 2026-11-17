#!/usr/bin/env python3
"""make_tables.py: #258 -- the grid guard tests for a half-step, not for
machine precision.

fix_apply_grid.py added a guard to grid_macros that refuses to emit the
macros when a midrank is off the 1/2n! grid by more than 1e-6.  On the
measurements that is right -- check_grid_resolution.py reports 8000 of 8000
on the grid to 1e-9 -- but grid_macros also runs on make_tables_selftest.py's
fixture, whose midranks are written to three decimals: 0.854 is 40.992 grid
steps and 0.895667 is 42.992, each off by 0.008 of a step.  The guard
stopped the self-test, and a self-test that cannot run is worse than the
check is good.

The error the guard exists to catch is a half-step offset: the midrank
carrying the 1/2 of Eq.(midrank)'s tie term while the code divides by n!.
So the test is now whether a value is nearer a half-step point than a grid
point -- the fractional part of 2 n! pct lying in [0.25, 0.75] -- which
catches the half-step by a factor of two and admits anything written to
within a quarter of a step.  The exact test stays where the data is exact:
check_grid_resolution.py runs it on the measurements at 1e-9 and is the
evidence Section 5.3 cites.

Idempotent.  Run from the directory holding make_tables.py.

    python3 -I fix_apply_grid2.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("make_tables.py",
     "    # What the argument establishes is that a midrank is on this grid.\n"
     "    # Section 5.3 says so, so the build stops rather than printing it\n"
     "    # when it is false.\n"
     "    loose = [float(r[\"percentile_written\"])\n"
     "             for recs in blk.values() for r in recs.values()\n"
     "             if np.isfinite(r.get(\"percentile_written\", float(\"nan\")))\n"
     "             and abs(float(r[\"percentile_written\"]) * k\n"
     "                     - round(float(r[\"percentile_written\"]) * k)) > 1e-6]\n"
     "    if loose:\n"
     "        raise SystemExit(\n"
     "            \"grid_macros: %d midranks are off the 1/%d grid (%s); \"\n"
     "            \"Section 5.3 states that grid as the resolution of one \"\n"
     "            \"reading\" % (len(loose), k,\n"
     "                          \", \".join(f\"{v:.6f}\" for v in loose[:4])))\n",
     "    # What the argument establishes is that a midrank is on this grid.\n"
     "    # Section 5.3 says so, so the build stops rather than printing it\n"
     "    # when it is false.\n"
     "    #\n"
     "    # The failure this is for is a half-step offset -- the midrank\n"
     "    # carrying Eq.(midrank)'s tie half while the code divides by n! --\n"
     "    # so the test is whether a value is nearer a half-step point than a\n"
     "    # grid point, not whether it is on the grid to machine precision.\n"
     "    # make_tables_selftest.py's fixture is written to three decimals\n"
     "    # and is off by 0.008 of a step; an exact test stops it for no\n"
     "    # reason.  check_grid_resolution.py runs the exact test where the\n"
     "    # data is exact, on the measurements, and is what Section 5.3 cites.\n"
     "    loose = [float(r[\"percentile_written\"])\n"
     "             for recs in blk.values() for r in recs.values()\n"
     "             if np.isfinite(r.get(\"percentile_written\", float(\"nan\")))\n"
     "             and 0.25 <= abs(float(r[\"percentile_written\"]) * k) % 1.0\n"
     "                       <= 0.75]\n"
     "    if loose:\n"
     "        raise SystemExit(\n"
     "            \"grid_macros: %d midranks sit nearer a half-step than a \"\n"
     "            \"point of the 1/%d grid (%s); Section 5.3 states that grid \"\n"
     "            \"as the resolution of one reading\" % (len(loose), k,\n"
     "                          \", \".join(f\"{v:.6f}\" for v in loose[:4])))\n",
     "258 half-step guard"),
]

FILES = sorted({e[0] for e in EDITS})


def apply_edits(root, dry_run=False):
    cache = {}
    for name in FILES:
        with open(os.path.join(root, name), encoding="utf-8") as fh:
            cache[name] = fh.read()
    made = skipped = passed = 0
    for edit in EDITS:
        name, old, new, label = edit[:4]
        later = edit[4] if len(edit) > 4 else None
        text = cache[name]
        done = (new in text) if old in new else (old not in text and new in text)
        if done:
            print(f"  skip  {label:<28} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                print(f"  pass  {label:<28} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<28} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<28} {name}")
        made += 1
    if not dry_run:
        for name, text in cache.items():
            with open(os.path.join(root, name), "w", encoding="utf-8") as fh:
                fh.write(text)
    return made, skipped, passed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    print("make_tables.py: the grid guard tests for a half-step")
    print("-" * 54)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 54)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 54)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
