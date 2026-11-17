#!/usr/bin/env python3
"""Batch 14: #110 and #121.

  #110  Table 3's caption names its columns but not what they are taken
        over, what the sign of r means, or what the Dblock column is in.
        The same omission as #172 for Table 8.
  #121  "the top rung is a different family" -- which ladder, and different
        from what.

  (#106 and #119 are recorded as no-change: #106 was withdrawn, and #119
  only notes that Table 4's strict-maximum column and the upper block of
  Table 5 carry the same five numbers, which is correct and intended.)

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b14.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #110 -------------------------------------------------------------
    ("sec_decomp.tex",
     "\\caption{Every (evaluator, corpus) cell of the AR ladder: the\n"
     "median $\\Dblock$ of the authored arrangement, the rank-biserial effect size\n"
     "between the label groups, and its two-sided Mann--Whitney $p$.",
     "\\caption{Every (evaluator, corpus) cell of the AR ladder.  Columns from the\n"
     "left: the evaluator; the corpus; the median over that cell's texts of\n"
     "$\\Dblock$, the raw value of Eq.~\\eqref{eq:delta} for the authored\n"
     "arrangement, per token; the rank-biserial correlation $r$ of\n"
     "Eq.~\\eqref{eq:rb} between the two label groups, positive when the causal\n"
     "group ranks higher; and its two-sided Mann--Whitney $p$.",
     "110 tab:blkcells"),

    # ---- #121 -------------------------------------------------------------
    ("sec_decomp.tex",
     "That is not the\nsame variable as parameter count: the top rung is a different family\n"
     "pretrained on different data, so the AR ladder orders parameter count and\n"
     "evaluator provenance together",
     "That is not the\nsame variable as parameter count: the AR ladder's top rung,\n"
     "\\texttt{Qwen3-4B-Base}, is a different family from the four \\textsc{gpt-2}\n"
     "rungs below it and was pretrained on different data, so the AR ladder orders\n"
     "parameter count and evaluator provenance together",
     "121 decomp:227"),
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
            print(f"  skip  {label:<20} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                # A later batch rewrote this passage, so on a re-run neither
                # the old text nor this batch's own replacement is here.
                print(f"  pass  {label:<20} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<20} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<20} {name}")
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
    print("batch 14: #110 Table 3 caption, #121 the top rung")
    print("-" * 56)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 56)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 56)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
