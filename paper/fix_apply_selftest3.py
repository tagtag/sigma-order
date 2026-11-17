#!/usr/bin/env python3
"""make_tables_selftest.py: #267 -- check_step_gap pinned the old grid.

The same thing #259 found in check_grid_steps, in the one other self-test
that counts grid steps.  check_step_gap exists to keep \\FbStepGap a
DIFFERENCE of the two evaluators' displacements and not a RATIO of them,
and that purpose is untouched by #264.  What it also did was fix the grid:
its fixture puts the two displacements at -0.25 and +0.05 with n! = 20 and
asserts a gap of 6.0, which is 1/20 units.  On the 1/2n! grid the
displacements are -10.0 and +2.0 steps and the gap is 12.0.

Verified against the patched table_fbrank on this exact fixture: FbStepGap
comes out '12.0'.

The second assertion, that the gap is not 5.0, still does its job: 5.0 is
0.25/0.05, a ratio, and a ratio does not change with the grid.

Idempotent.  Run from the directory holding make_tables_selftest.py.

    python3 -I fix_apply_selftest3.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("make_tables_selftest.py",
     "    The prose said the two evaluators' readings differ \"by about thirteen\n"
     "    grid steps\".  The displacements were -6.5 and +0.5 steps, whose\n"
     "    difference is 7.0; thirteen is 0.2708/0.0208, one displacement over the\n"
     "    other.  Written as a word, the number was outside everything that checks\n"
     "    numbers.  Here two evaluators are given displacements of -0.25 and +0.05\n"
     "    on a grid of 1/20, which is -5.0 and +1.0 steps and a gap of 6.0.\n",
     "    The prose said the two evaluators' readings differ \"by about thirteen\n"
     "    grid steps\".  Read on the 1/n! grid the displacements were -6.5 and\n"
     "    +0.5 steps, whose difference is 7.0; thirteen was 0.2708/0.0208, one\n"
     "    displacement over the other.  Written as a word, the number was outside\n"
     "    everything that checks numbers.  (#253 and #264 made the grid 1/2n!, so\n"
     "    the displacements are now -13 and +1 and their difference is 14; the\n"
     "    ratio is unchanged, which is the point this test keeps.)  Here two\n"
     "    evaluators are given displacements of -0.25 and +0.05 with n! = 20,\n"
     "    which on the 1/2n! grid is -10.0 and +2.0 steps and a gap of 12.0.\n",
     "267 docstring"),

    ("make_tables_selftest.py",
     "        assert g[\"FbStepGap\"] == \"6.0\", g[\"FbStepGap\"]\n",
     "        assert g[\"FbStepGap\"] == \"12.0\", g[\"FbStepGap\"]\n",
     "267 gap assertion"),
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
    print("make_tables_selftest.py: check_step_gap on the 1/2n! grid")
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
