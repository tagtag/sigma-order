#!/usr/bin/env python3
"""Batch 7: #100, #123, #152, #163, #168, #199.

  #100  "A larger model has sharper conditionals and treats an arrangement
        and its reverse more differently, so ..." -- the clause before "so"
        is a guess about why, and nothing here measures it.  Only what was
        measured is kept.
  #123  "model" where the paper's own terminology requires "evaluator".
  #152  "is reporting the model" -> is reporting a property of the masked
        evaluator.  Also the two sites in Section 7's scope paragraph.
  #163  "which model assembles them" -- what differs is not the assembly
        but which masked evaluator computed sigma.
  #168  "a better model estimates that ratio rather than abolishing it" --
        "better" is undefined (the AR ladder orders parameter count), and
        "estimates" implies a true value this paper never posits.  Both
        sites, Section 6.3 and Section 1.2.
  #199  "what a model trained on text finds likely, and how highly that
        model ranks an authored arrangement" -- under LLaDA the authored
        arrangement sits below the null, and sigma's midrank is not a rank
        by likelihood.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b7.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #100 -------------------------------------------------------------
    ("main.tex",
     "A larger model\nhas sharper conditionals and treats an arrangement and its reverse more\n"
     "differently, so the size of $\\Delta$ carries the evaluator as well as\n"
     "whatever property of the text is of interest, and a single reading does not\nseparate them.",
     "So the size of $\\Delta$ carries the autoregressive evaluator as well as\n"
     "whatever property of the text is of interest, and a single reading does not\nseparate them.",
     "100 main:1100"),

    # ---- #199 -------------------------------------------------------------
    ("main.tex",
     "Every statement here about authored arrangement is a\n"
     "statement about what a model trained on text finds likely, and how highly\n"
     "that model ranks an authored arrangement is part of the measurement rather\n"
     "than a nuisance to be removed.",
     "Every statement here about an authored arrangement is a\n"
     "statement about where an evaluator places it among the rearrangements of\n"
     "the same sentences.  That placement is above the null under some\n"
     "evaluators and below it under others ($\\FbAuthoredLLaDA$ under\n"
     "\\texttt{LLaDA}, Table~\\ref{tab:fbdecomp}), and it is part of the\n"
     "measurement rather than a nuisance to be removed.",
     "199 main:1366"),

    # ---- #152 -------------------------------------------------------------
    ("sec_truesigma.tex",
     "A\nquantity whose reading moves that far when the model is replaced is\nreporting the model.",
     "A\nquantity whose reading moves that far when the masked evaluator is replaced\n"
     "is reporting a property of that evaluator.",
     "152 true:168"),

    # ---- #163 -------------------------------------------------------------
    ("sec_truesigma.tex",
     "The texts are identical; what differs is which model\nassembles them.",
     "The texts are identical; what differs is which masked evaluator\ncomputed $\\sigma$.",
     "163 true:238",
     "batch 18 (#161, #162)"),

    # ---- #168 -------------------------------------------------------------
    ("sec_truesigma.tex",
     "log-ratio between a text\nand its reversal, and a better model estimates that ratio rather than\nabolishing it.",
     "log-ratio between a text\nand its reversal, and nothing makes that ratio vanish as the autoregressive\n"
     "evaluator's parameter count grows along the AR ladder.",
     "168 true:279"),

    ("sec_intro.tex",
     "A better model estimates the ratio better rather than\nmaking it vanish, and along the AR ladder its magnitude grows.",
     "Nothing makes that ratio vanish as the autoregressive evaluator's parameter\n"
     "count grows along the AR ladder; measured, its magnitude grows.",
     "168 intro:192"),
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
            print(f"  skip  {label:<18} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                # A later batch rewrote this passage, so on a re-run neither
                # the old text nor this batch's own replacement is here.
                print(f"  pass  {label:<18} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<18} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<18} {name}")
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
    print("batch 7: #100 #123 #152 #163 #168 #199")
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
