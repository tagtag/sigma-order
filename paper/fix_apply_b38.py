#!/usr/bin/env python3
"""Batch 38: #260 -- one name for Eq.(fb), everywhere.

#255 stopped calling Eq.(fb) an entropy production and left three names in
its place: "an order comparison" in the subtitle, "the forward/backward
quantity" where the paper reserves the letter and in two captions, and "two
assembly orders" wherever it says what the thing does.  A paper whose
subject is one quantity being given another's name should not carry three
names for its own.

All four sites become assembly-order.  It says what Eq.(fb) compares and
carries no suggestion of a time reversal, which "forward/backward" does --
and that suggestion is the one #255 withdrew.

Left alone: "forward--backward asymmetry" at sec_intro.tex:33 and
main.tex:561, which names the phenomenon Ref.[arrow] measured in language,
and "forward and backward cross-entropy" at main.tex:548, which is a
quantity of someone else's.  Those are not Eq.(fb) and the word is right
for them.

The macro names (\\FbAuthoredSteps and the rest) are untouched: they are
identifiers, not prose.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b38.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("main.tex",
     "\\large a fixed-text measure without a zero, and an order comparison\n"
     "that vanishes identically}",
     "\\large a fixed-text measure without a zero, and an assembly-order\n"
     "comparison that vanishes identically}",
     "260 subtitle"),

    ("main.tex",
     "reserve $\\sigma$ for the forward/backward quantity of Eq.~\\eqref{eq:fb} --- the",
     "reserve $\\sigma$ for the assembly-order quantity of Eq.~\\eqref{eq:fb} --- the",
     "260 sec2.2 reserve"),

    ("sec_truesigma.tex",
     "% The forward/backward quantity of Eq.(fb), measured on masked evaluators.",
     "% The assembly-order quantity of Eq.(fb), measured on masked evaluators.",
     "260 sec6 header"),

    ("sec_truesigma.tex",
     "\\caption{The forward/backward quantity of\n"
     "Eq.~\\eqref{eq:fb}, read as the midrank",
     "\\caption{The assembly-order quantity of\n"
     "Eq.~\\eqref{eq:fb}, read as the midrank",
     "260 tab:fbrank caption"),
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
    print("batch 38: one name for Eq.(fb) -- assembly-order")
    print("-" * 52)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 52)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 52)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
