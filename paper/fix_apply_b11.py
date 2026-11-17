#!/usr/bin/env python3
"""Batch 11: Section 4.2 -- #97, #98, #99, #75(d).

  #97  "No origin: it is not anchored for a single text" -- "it" is Delta;
        the same construction was already levelled in Section 2.2.
  #98  "only the last is an origin" says which of the three is an origin
        and leaves the other two unnamed.
  #99  "the median Dblock" needs saying that it is a raw value and not a
        midrank, since the numbers beside it in Section 4.1 are midranks;
        and "larger at the top of the AR ladder" needs its baseline.
  #75(d) The closing paragraph of Section 4.2 withdraws a comparison that
        Section 3.2 no longer describes, so it has nothing to refer to.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b11.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #98 ---------------------------------------------------------------
    ("main.tex",
     "Three independent deficiencies, none of which involves the labels.  They are\n"
     "usually run together under ``no zero'', and they should not be: only the last\n"
     "is an origin.",
     "Three independent deficiencies, none of which involves the labels.  They are\n"
     "usually run together under ``no zero'', and they should not be: one of them\n"
     "concerns the unit a reading is in, one its sign, and only one an origin.",
     "98 main:1098"),

    # ---- #99 ---------------------------------------------------------------
    ("main.tex",
     "the median $\\Dblock$ of the authored\narrangement moves from $\\CapDeltaLo$ to $\\CapDeltaHi$ on identical texts\n"
     "(Table~\\ref{tab:blkcells} prints it for every cell).",
     "the median $\\Dblock$ of the authored\n"
     "arrangement --- the raw value of Eq.~\\eqref{eq:delta}, not a midrank ---\n"
     "moves from $\\CapDeltaLo$ to $\\CapDeltaHi$ on identical texts\n"
     "(Table~\\ref{tab:blkcells} prints it for every cell).",
     "99a main:1109"),

    ("main.tex",
     "$\\CapNCorpora$ corpora, larger at the top of the AR ladder in $\\CapNUp$ of them,",
     "$\\CapNCorpora$ corpora, larger at the top of the AR ladder than at the\n"
     "bottom in $\\CapNUp$ of them,",
     "99b main:1116"),

    # ---- #97 ---------------------------------------------------------------
    ("main.tex",
     "\\emph{No origin: it is not anchored for a single text.}  The missing origin is what the",
     "\\emph{No origin: $\\Delta$ has no origin for a single text.}  The missing origin is what the",
     "97 main:1137"),

    # ---- #75 (d) -----------------------------------------------------------
    ("main.tex",
     "A fourth candidate, the absence of a common unit between model classes, is\n"
     "not on the list.  It was measured as the ratio between a masked evaluator's\n"
     "score and an autoregressive one's, which is a ratio between a number and a\n"
     "different number (Section~\\ref{sec:scope}).  It is withdrawn together with\n"
     "the comparison it was drawn from.\n\n",
     "A fourth candidate, the absence of a common unit between the two model\n"
     "classes, is not on the list: $\\Delta$ exists for autoregressive evaluators\n"
     "and $\\sigma$ for masked ones (Section~\\ref{sec:scope}), so there is no\n"
     "reading of one to put beside a reading of the other.\n\n",
     "75d main:1148"),
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
            print(f"  skip  {label:<16} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                # A later batch rewrote this passage, so on a re-run neither
                # the old text nor this batch's own replacement is here.
                print(f"  pass  {label:<16} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<16} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<16} {name}")
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
    print("batch 11: Section 4.2")
    print("-" * 48)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 48)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 48)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
