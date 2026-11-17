#!/usr/bin/env python3
"""Batch 6: #174, the masked-evaluator sweep through Section 6.

Sections 4 and 5 use "evaluator" on its own for the autoregressive ones,
because Delta exists for no other kind.  Section 6 is about sigma, which
exists for no autoregressive evaluator, so a bare "evaluator" there reads
as the wrong class.  Every site in Section 6 that means the model doing the
scoring is written "masked evaluator".

Sites left to their own corrections and not touched here:
  :59  (#144, the Ref.[1] evaluators), :100 and :222 (#160, the scope of
  Eq.(fbzero)), :125 (#149, the Table 7 caption), :211 (#158), :326
  (#183/#184).

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b6.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("sec_truesigma.tex",
     "non-zero reading appears is a measure of the evaluator's \\emph{in}compatibility",
     "non-zero reading appears is a measure of the masked evaluator's \\emph{in}compatibility",
     "174 true:37"),

    ("sec_truesigma.tex",
     "Table~\\ref{tab:fbrank} gives, for each evaluator and corpus, the median",
     "Table~\\ref{tab:fbrank} gives, for each masked evaluator and corpus, the median",
     "174 true:132"),

    ("sec_truesigma.tex",
     "\\caption{The same measurement as Table~\\ref{tab:fbrank}, summarised per\nevaluator:",
     "\\caption{The same measurement as Table~\\ref{tab:fbrank}, summarised per\nmasked evaluator:",
     "174 true:141 caption",
     "batch 17 (#172)"),

    ("sec_truesigma.tex",
     "\\paragraph{The authored arrangement's midrank is a property of the\nevaluator.}",
     "\\paragraph{The authored arrangement's midrank is a property of the\nmasked evaluator.}",
     "174 true:151 heading"),

    ("sec_truesigma.tex",
     "Nothing about the texts changed between them; only the evaluator",
     "Nothing about the texts changed between them; only the masked evaluator",
     "174 true:166"),

    ("sec_truesigma.tex",
     "The two evaluators do agree on one thing, and it is worth separating from",
     "The two masked evaluators do agree on one thing, and it is worth separating from",
     "174 true:171"),

    ("sec_truesigma.tex",
     "Of the \\FbNTestsCausal\\ evaluator--corpus tests of causal against non-causal,",
     "Of the \\FbNTestsCausal\\ masked-evaluator--corpus tests of causal against non-causal,",
     "174 true:185"),

    ("sec_truesigma.tex",
     "each evaluator, \\texttt{LLaDA} gives \\FbSignNegLLaDA\\ negative ($p =",
     "each masked evaluator, \\texttt{LLaDA} gives \\FbSignNegLLaDA\\ negative ($p =",
     "174 true:190"),

    ("sec_truesigma.tex",
     "\\FbNCells\\ cells would be the wrong test: both evaluators score the",
     "\\FbNCells\\ cells would be the wrong test: both masked evaluators score the",
     "174 true:196"),

    ("sec_truesigma.tex",
     "a defect of the evaluator: Eq.~\\eqref{eq:fbzero} makes it identically zero",
     "a defect of the masked evaluator: Eq.~\\eqref{eq:fbzero} makes it identically zero",
     "174 true:250"),

    ("sec_truesigma.tex",
     "evaluator's incompatibility and not of the text's causal structure.",
     "masked evaluator's incompatibility and not of the text's causal structure.",
     "174 true:259"),

    ("sec_truesigma.tex",
     "\\subsection{The mask rate this evaluator was trained at}",
     "\\subsection{The mask rate this masked evaluator was trained at}",
     "174 true:299 heading",
     "batch 29 (#235)"),

    ("sec_truesigma.tex",
     "It does not collapse.  Across all \\FbNTexts\\ texts and both evaluators ---",
     "It does not collapse.  Across all \\FbNTexts\\ texts and both masked evaluators ---",
     "174 true:311"),

    ("sec_truesigma.tex",
     "whose arrangements the evaluator cannot separate at all would have no",
     "whose arrangements the masked evaluator cannot separate at all would have no",
     "174 true:314"),

    ("sec_truesigma.tex",
     "evaluators within texts is the level the groups sit at, not the order",
     "masked evaluators within texts is the level the groups sit at, not the order",
     "174 true:322"),

    ("sec_truesigma.tex",
     "identity rather than on either evaluator.",
     "identity rather than on either masked evaluator.",
     "174 true:331"),
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
    print("batch 6: #174 masked evaluator through Section 6")
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
