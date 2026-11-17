#!/usr/bin/env python3
"""make_tables_selftest.py: #259 -- check_grid_steps pinned the old grid.

check_grid_steps exists to keep one magnitude from being a resolution floor
in Section 5.3 and a measured rise in Section 5.4.  That purpose is
untouched by #253.  What it also did was assert the grid itself --

    assert g["GridK"] == "24"
    assert g["CausalCompStepsMax"] == "1"

-- so the old claim was written into the test, and correcting the generator
made the test fail.  The expectations move to the 1/48 grid: the causal
component of 1/24 is two steps, and the authored component's span of
0.396 - 0.354 = 0.042 is two steps as well.  The relation the test is
really for, that the span is on the causal component's ruler, is unchanged
and still asserted.

The fixture's midranks stay as they are.  0.5 + 0.354 = 0.854 is 40.992
steps of 1/48 rather than 41, because 0.354 is the measured value rounded
to three decimals; #258 is why the generator's guard reads that as on the
grid.

Idempotent.  Run from the directory holding make_tables_selftest.py.

    python3 -I fix_apply_selftest2.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- the docstring -----------------------------------------------------
    ("make_tables_selftest.py",
     "    Section 5.3 reads a causal component of one step as the resolution floor\n"
     "    and declines to treat its size as measured.  Section 5.4 reported the\n"
     "    authored component as rising across the ladder, and that rise is\n"
     "    0.396 - 0.354 = 0.042, which is one step of the same grid.  The same\n"
     "    magnitude was a floor in one place and a result in the other.\n",
     "    Section 5.3 reads a causal component of two steps as the resolution\n"
     "    floor and declines to treat its size as measured.  Section 5.4 reported\n"
     "    the authored component as rising across the ladder, and that rise is\n"
     "    0.396 - 0.354 = 0.042, which is two steps of the same grid.  The same\n"
     "    magnitude was a floor in one place and a result in the other.\n",
     "259 docstring"),

    # ---- the fixture's comment ---------------------------------------------
    ("make_tables_selftest.py",
     "    # authored component 0.354 -> 0.396 across the ladder: one step of 1/24.\n"
     "    # causal component held at exactly one step throughout.\n",
     "    # authored component 0.354 -> 0.396 across the ladder: 0.042, which is\n"
     "    # two steps of the 1/48 grid (#253).  causal component held at the same\n"
     "    # two steps throughout, so the span and the floor stay comparable.\n",
     "259 fixture comment"),

    # ---- the grid assertions -----------------------------------------------
    ("make_tables_selftest.py",
     "    assert g[\"GridK\"] == \"24\", g[\"GridK\"]\n"
     "    assert g[\"CausalCompStepsMax\"] == \"1\", g[\"CausalCompStepsMax\"]\n",
     "    assert g[\"GridK\"] == \"48\", g[\"GridK\"]\n"
     "    assert g[\"CausalCompStepsMax\"] == \"2\", g[\"CausalCompStepsMax\"]\n",
     "259 grid assertions"),

    # ---- the span ----------------------------------------------------------
    ("make_tables_selftest.py",
     "    assert abs(float(g[\"AuthoredCompSpanSteps\"]) - 1.0) < 0.05, \\\n",
     "    assert abs(float(g[\"AuthoredCompSpanSteps\"]) - 2.0) < 0.05, \\\n",
     "259 span assertion"),
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
    print("make_tables_selftest.py: check_grid_steps on the 1/48 grid")
    print("-" * 58)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 58)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 58)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
