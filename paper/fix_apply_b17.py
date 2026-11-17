#!/usr/bin/env python3
"""Batch 17: Section 6.3, first half -- #150 #151(prose) #153 #154 #156
#157 #172 #173.

  #150  "Two readings come out of it, and they are of different kinds" --
        the two are not named until two paragraph headings later, with a
        table caption in between.  Name them here.
  #151  The prose says the table carries a signed-rank test of each group
        against the null; after fix_apply_tables.py it does, in two named
        columns, so the sentence can point at them.
  #153  "and bert-base FbSignNegBertBase" drops the word negative, which
        the LLaDA half carries.
  #154  "a smallest attainable two-sided p of 2/2^FbNCorporaOfLLaDA" is
        given without its derivation, and bert-base's p turns out to be
        that bound exactly.
  #156  "every masked evaluator we have" -- there are two and they are
        named a paragraph earlier.
  #157  "separates the authored arrangement from its rearrangements by an
        amount that depends on which masked evaluator is used" renames a
        quantity that already has a name: the authored component of
        Eq.(auth), which Table 8 prints.
  #172  Table 8's caption, like Table 3's: name the columns from the left,
        say what the median is over, and what the sign of r means.
  #173  "which does reverse in one cell below" -- name the cell, and keep
        it apart from the other single cell this section names.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b17.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #150 + #151 (prose) ----------------------------------------------
    ("sec_truesigma.tex",
     "Table~\\ref{tab:fbrank} gives, for each masked evaluator and corpus, the median\n"
     "midrank of the authored arrangement in each label group, a signed-rank test of\n"
     "each group against the $0.50$ null, and the effect size between them.  Two\n"
     "readings come out of it, and they are of different kinds.",
     "Table~\\ref{tab:fbrank} gives, for each masked evaluator and corpus, the median\n"
     "midrank of the authored arrangement in each label group, the two-sided\n"
     "Wilcoxon signed-rank $p$ of each group against the $0.50$ null in the\n"
     "$p_{c}$ and $p_{nc}$ columns, and the effect size between the groups.  Two\n"
     "readings come out of it, and they are of different kinds: where the authored\n"
     "arrangement sits, which turns out to be a property of the masked evaluator\n"
     "rather than of the text, and what the causal label adds to that, which turns\n"
     "out to be almost nothing.",
     "150+151 true:145"),

    # ---- #172 --------------------------------------------------------------
    ("sec_truesigma.tex",
     "\\caption{The same measurement as Table~\\ref{tab:fbrank}, summarised per\n"
     "masked evaluator: the median over corpora of the authored component\n"
     "$\\mathrm{med}(\\mathrm{pct}_{\\text{non-causal}}) - 0.50$ and of the causal\n"
     "component of Eq.~\\eqref{eq:caus}, each also in steps of the\n"
     "$1/\\GridK = \\GridStep$ grid, with the median effect size.",
     "\\caption{The same measurement as Table~\\ref{tab:fbrank}, summarised per\n"
     "masked evaluator.  Columns from the left: the masked evaluator; the authored\n"
     "component $\\mathrm{med}(\\mathrm{pct}_{\\text{non-causal}}) - 0.50$, as a\n"
     "median over the \\NCorp\\ corpora; that component in steps of the\n"
     "$1/\\GridK = \\GridStep$ grid; the causal component of Eq.~\\eqref{eq:caus},\n"
     "likewise a median over corpora; that component in grid steps; and $r$, the\n"
     "median over the \\NCorp\\ corpora of the rank-biserial correlation\n"
     "Table~\\ref{tab:fbrank} prints cell by cell, negative when the causal group\n"
     "ranks lower.",
     "172 tab:fbdecomp caption"),

    # ---- #157 --------------------------------------------------------------
    ("sec_truesigma.tex",
     "Under \\texttt{LLaDA} the authored arrangement sits far below the null ---\n"
     "$\\FbAuthoredLLaDA$, or $\\FbAuthoredStepsLLaDA$ steps of the\n"
     "$1/\\GridK = \\GridStep$ grid (Table~\\ref{tab:fbdecomp}) --- and it is far from the null in both",
     "Under \\texttt{LLaDA} the authored component of Eq.~\\eqref{eq:auth}, read\n"
     "under $\\sigma$, is $\\FbAuthoredLLaDA$: the authored arrangement sits that\n"
     "far below the null, or $\\FbAuthoredStepsLLaDA$ steps of the\n"
     "$1/\\GridK = \\GridStep$ grid (Table~\\ref{tab:fbdecomp}).  It is far from the null in both",
     "157 true:164",
     "batch 29 (cold read)"),

    # ---- #173 --------------------------------------------------------------
    ("sec_truesigma.tex",
     "That is not a statement about the two groups'\norder, which does reverse in one cell below.",
     "That is not a statement about the two groups'\n"
     "order, which does reverse in one cell: \\texttt{LLaDA} on \\textsc{Opus46},\n"
     "the only cell of Table~\\ref{tab:fbrank} where $r$ is positive\n"
     "($r = \\FbRMax$).",
     "173 true:189"),

    # ---- #153 + #154 -------------------------------------------------------
    ("sec_truesigma.tex",
     "within\neach masked evaluator, \\texttt{LLaDA} gives \\FbSignNegLLaDA\\ negative ($p =\n"
     "\\FbSignPLLaDA$, exact binomial) and \\texttt{bert-base} \\FbSignNegBertBase\\\n"
     "($p = \\FbSignPBertBase$).  Neither reaches $0.05$ and neither could: an\n"
     "exact binomial over $\\FbNCorporaOfLLaDA$ corpora has a smallest attainable\n"
     "two-sided $p$ of $2/2^{\\FbNCorporaOfLLaDA}$, which is above that\n"
     "threshold.",
     "within\n"
     "each masked evaluator, \\texttt{LLaDA} gives \\FbSignNegLLaDA\\ negative ($p =\n"
     "\\FbSignPLLaDA$, exact binomial) and \\texttt{bert-base}\n"
     "\\FbSignNegBertBase\\ negative ($p = \\FbSignPBertBase$).  Neither reaches\n"
     "$0.05$ and neither could.  Under the null each corpus is an independent coin,\n"
     "so the most extreme outcome --- all $\\FbNCorporaOfLLaDA$ on one side --- has\n"
     "probability $1/2^{\\FbNCorporaOfLLaDA}$, and the two-sided $p$ of that\n"
     "outcome is $2/2^{\\FbNCorporaOfLLaDA} = \\FbSignPBertBase$: the smallest the\n"
     "test can return at this $n$, and the value \\texttt{bert-base} takes.",
     "153+154 true:196"),

    # ---- #156 --------------------------------------------------------------
    ("sec_truesigma.tex",
     "case for every masked evaluator we have ---",
     "case for \\texttt{bert-base} and \\texttt{LLaDA} alike ---",
     "156 true:210"),
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
    print("batch 17: Section 6.3, first half")
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
