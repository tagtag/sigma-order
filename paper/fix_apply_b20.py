#!/usr/bin/env python3
"""Batch 20: Section 6.4 -- #183 and #184.

  #183  "How far the authored arrangement sits from the null" needs to say
        under which quantity, since Section 4 uses the same words for the
        midrank under Delta.
  #184  "exactly the quantity Eq.(fbzero) predicts should carry the
        evaluator rather than the text" goes past what Section 6.1 settled.
        The identity fixes whether a value range opens at all; it does not
        say what the value moves with inside it.  That the reading moves
        with the evaluator and not with the label is what Section 6.3
        measured.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b20.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("sec_truesigma.tex",
     "How far the authored arrangement sits from the null is exactly the quantity\n"
     "Eq.~\\eqref{eq:fbzero} predicts should carry the evaluator rather than the\n"
     "text.  We do not claim",
     "How far the authored arrangement sits from the null under $\\sigma$ is the\n"
     "quantity Section~\\ref{sec:fbresult} measured, and what it found was that\n"
     "its value tracks the masked evaluator and not the label.  We do not claim",
     "183+184 true:378"),
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
    print("batch 20: Section 6.4")
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
