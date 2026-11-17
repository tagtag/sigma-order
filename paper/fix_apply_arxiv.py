#!/usr/bin/env python3
"""make_arxiv.sh's ancillary list is missing the two check scripts.

Section 6.3 now names check_two_constructions.py (#182), and make_arxiv.sh
refuses to package a bundle in which a script the text names is absent from
anc/.  It is added here, together with check_rank_pvalues.py, which is not
named in the text but produces three of Appendix A's numbers -- the rank
correlations of the route-control sweep and the floor of the exact rank
null -- and so belongs with the other scripts that stand behind quoted
figures.

Both live outside paper/, like every other measurement script in the list:

    order-intervention/check_two_constructions.py
    bert-affinity/check_rank_pvalues.py

Idempotent.  Run from the directory holding make_arxiv.sh.

    python3 -I fix_apply_arxiv.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("make_arxiv.sh",
     "         ../order-intervention/forward_backward_decomposition.py \\\n",
     "         ../order-intervention/forward_backward_decomposition.py \\\n"
     "         ../order-intervention/check_two_constructions.py \\\n",
     "anc: check_two_constructions.py"),

    ("make_arxiv.sh",
     "         ../bert-affinity/compare_repro.py \\\n",
     "         ../bert-affinity/compare_repro.py \\\n"
     "         ../bert-affinity/check_rank_pvalues.py \\\n",
     "anc: check_rank_pvalues.py"),
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
    print("make_arxiv.sh: the two check scripts in anc/")
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
