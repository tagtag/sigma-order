#!/usr/bin/env python3
"""make_arxiv.sh: check_grid_resolution.py in anc/.

#253 rests on a claim about the statistic's resolution that the paper now
states in Section 5.3 and reads numbers against in Sections 1, 4.2 and 6.1.
check_grid_resolution.py is what establishes it from the measurements
rather than from the argument, so it belongs with the other scripts that
stand behind quoted figures.

Idempotent.  Run from the directory holding make_arxiv.sh.

    python3 -I fix_apply_anc2.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("make_arxiv.sh",
     "         ../order-intervention/check_two_constructions.py \\\n",
     "         ../order-intervention/check_two_constructions.py \\\n"
     "         ../order-intervention/check_grid_resolution.py \\\n",
     "anc: check_grid_resolution.py"),
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
            print(f"  skip  {label:<32} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                print(f"  pass  {label:<32} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<32} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<32} {name}")
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
    print("make_arxiv.sh: check_grid_resolution.py in anc/")
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
