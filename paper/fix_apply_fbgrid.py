#!/usr/bin/env python3
"""make_tables.py: #264 -- table_fbrank computes its own grid, and #253
left it on 1/n!.

grid_macros was not the only place that divides by the grid.  table_fbrank
finds its own n! from the records and reports the forward/backward
components in steps of it:

    kk = {r.get("n_perms") ...}
    k = max(kk) if kk else 0
    ...
    mac(f"FbAuthoredSteps{t}", f"{auth * k:+.1f}")

so Section 6 and the abstract quote \\FbAuthoredStepsLLaDA = -6.5 and
\\FbAuthoredStepsBertBase = +0.5 -- steps of 1/24 -- while the prose beside
them says the grid is $1/\\GridK = \\GridStep$, which #253 made 1/48.  The
half-integers are the same tell as the authored component's 8.5: a midrank
is an odd multiple of 1/2n!, so expressed in 1/n! it is always a half.

The same reasoning applies here as in grid_macros, for the same reason:
Eq.(midrank) counts the authored arrangement's tie with itself as a half.
After this, -6.5 becomes -13 and +0.5 becomes +1, \\FbStepGap doubles, and
the numbers agree with the grid the prose names.

This changes printed numbers, so make_tables.py must be re-run.

Idempotent.  Run from the directory holding make_tables.py.

    python3 -I fix_apply_fbgrid.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("make_tables.py",
     "        kk = {r.get(\"n_perms\") for recs in cells.values() for r in recs\n"
     "              if r.get(\"n_perms\")}\n"
     "        k = max(kk) if kk else 0\n",
     "        kk = {r.get(\"n_perms\") for recs in cells.values() for r in recs\n"
     "              if r.get(\"n_perms\")}\n"
     "        # The grid is 1/2n!, not 1/n!: Eq.(midrank) counts the authored\n"
     "        # arrangement's tie with itself as a half, so 2 n! pct is an\n"
     "        # integer and a midrank falls halfway between the multiples of\n"
     "        # 1/n!.  grid_macros does the same thing for Section 5; this is\n"
     "        # the copy Section 6 reads its steps from, and #253 missed it.\n"
     "        k = 2 * max(kk) if kk else 0\n",
     "264 fbrank grid"),
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
    print("make_tables.py: table_fbrank on the 1/2n! grid")
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
