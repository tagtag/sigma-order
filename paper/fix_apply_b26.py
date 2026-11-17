#!/usr/bin/env python3
"""Batch 26: Appendix A, the last of it -- #225 and #226(b).

  #225  "The incompatibility that gives sigEP its floor" uses the noun for
        the first time since Section 3.2's "compatibility conditions", with
        its referent several paragraphs back; and "its floor" is a measured
        level, not a proven bound.
  #226(b) The remaining sigEP uses of "floor": this appendix's three, and
        the two captions.  What was measured is that sigEP does not vanish
        at any of the widths and does not fall as d grows.  The Jeffreys
        identity quoted here gives positivity when the two conditional sets
        differ, which is not a level either.  The word is dropped for
        sigEP; the grid floor, the resolution floor and the exact floor of
        a p keep theirs.
  (also)  Equation (wemit), introduced in batch 25, is cited where the
        emitted route is read.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b26.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- cite eq:wemit -----------------------------------------------------
    ("main.tex",
     "For the emitted route there is no such cancellation: $p_\\theta(\\cdot \\mid\n"
     "x_{-k})$ does not take the shape",
     "For the emitted route of Eq.~\\eqref{eq:wemit} there is no such\n"
     "cancellation: $p_\\theta(\\cdot \\mid x_{-k})$ does not take the shape",
     "cite eq:wemit"),

    # ---- #226(b): the appendix's own three --------------------------------
    ("main.tex",
     "by this, and it is worth saying so where the $\\sigEP$ floor is introduced.  Equation~\\eqref{eq:antisym}",
     "by this, and it is worth saying so here, where $\\sigEP$ has just been shown\n"
     "not to vanish at any of the $\\ToyNCap$ widths measured.\n"
     "Equation~\\eqref{eq:antisym}",
     "226b main:1740"),

    # ---- #225 --------------------------------------------------------------
    ("main.tex",
     "derive from any joint.  The incompatibility that gives $\\sigEP$ its floor is\n"
     "exactly the property Eq.~\\eqref{eq:antisym} does not call on, so it cannot\n"
     "reach the rank statistic the rest of this paper uses.",
     "derive from any joint.  What makes $\\sigEP$ non-zero --- that the masked\n"
     "conditionals are those of no single joint --- is exactly the property\n"
     "Eq.~\\eqref{eq:antisym} does not call on, so it cannot reach the rank\n"
     "statistic the rest of this paper uses.",
     "225 main:1743"),

    ("main.tex",
     "The size of that floor is not arbitrary: it equals an average Jeffreys",
     "The size of that non-zero value is not arbitrary: it equals an average Jeffreys",
     "226b main:1747"),

    ("main.tex",
     "it here only so that the $\\sigEP$ floor is not mistaken for an unexplained",
     "it here only so that a non-zero $\\sigEP$ is not mistaken for an unexplained",
     "226b main:1752"),

    # ---- #226(b): the two captions ----------------------------------------
    ("main.tex",
     "whatever its accuracy; the masked values are the floor of that instrument,\n"
     "and the widest model's value is $\\ToyCapRatio$ times the narrowest's.",
     "whatever its accuracy; the masked values are what the instrument returns\n"
     "when no joint accounts for its conditionals, and the widest model's value is\n"
     "$\\ToyCapRatio$ times the narrowest's.",
     "226b fig2 caption"),

    ("main.tex",
     "beside it; the masked rows are the floor imposed by conditionals that belong\nto no joint.",
     "beside it; the masked rows are what conditionals belonging to no joint\nproduce instead.",
     "226b tab:capacity caption",
     "batch 27 (#220)"),
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
            print(f"  skip  {label:<26} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                # A later batch rewrote this passage, so on a re-run neither
                # the old text nor this batch's own replacement is here.
                print(f"  pass  {label:<26} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<26} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<26} {name}")
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
    print("batch 26: Appendix A, #225 and #226")
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
