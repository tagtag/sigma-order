#!/usr/bin/env python3
"""Batch 3: the last two "most costly" sites, and one sentence split.

  #126  Two sites the first pass missed because the words fall across a
        line break or take a different shape: main.tex:234 ("the most
        costly of all $n!$") and :1265 ("the most costly\narrangement").
        Both become "the strict maximum", the name Section 5.3 gives it.
  #187  main.tex:233 and :1265 say "at the top of the range" for the
        reading Section 5.3 names "the tail".  Both move to "the tail"
        here; the remaining sites of this sweep are in batch 4.
  (The abstract sentence that batch 2 rewrites is split there, not here:
   unsplit it runs to 51 words and check_paper.py refuses it.)

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b3.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #126 + #187, abstract -------------------------------------------
    ("main.tex",
     "from there up every one of them does; at the top of the range, where an\n"
     "authored arrangement is the most costly of all $n!$, the causal group",
     "from there up every one of them does; in the tail, where an\n"
     "authored arrangement is the strict maximum over all $n!$, the causal group",
     "126+187 abstract"),

    # ---- #126 + #187, Section 7 ------------------------------------------
    ("main.tex",
     "At the top of the range the causal group reaches the most costly\n"
     "arrangement $\\TailDiffGPTtwo$ to $\\TailDiffQwen$ points more often, as a\n"
     "median over corpora.",
     "In the tail the causal group reaches the strict maximum\n"
     "$\\TailDiffGPTtwo$ to $\\TailDiffQwen$ points more often than the non-causal\n"
     "group, as a median over corpora.",
     "126+187 sec7"),

    # ---- #187, Section 7: one reading, one name ---------------------------
    ("main.tex",
     "Read in the upper tail it leaves the\ngrid floor and moves along the AR ladder.",
     "Read in the tail it leaves the\ngrid floor and moves along the AR ladder.",
     "187 sec7 upper tail"),
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
        # Which test means "already applied" depends on how the two
        # strings nest.  If old is a substring of new (an insertion), old
        # survives the edit, so only the presence of new can decide; if new
        # is a substring of old (a deletion), new is there before the edit,
        # so old has to be looked for first.
        done = (new in text) if old in new else (old not in text and new in text)
        if done:
            print(f"  skip  {label:<22} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                # A later batch rewrote this passage, so on a re-run neither
                # the old text nor this batch's own replacement is here.
                print(f"  pass  {label:<22} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<22} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<22} {name}")
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
    print("batch 3: #126 remainder, #187 first sites")
    print("-" * 66)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 66)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 66)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
