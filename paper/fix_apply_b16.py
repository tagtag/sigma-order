#!/usr/bin/env python3
"""Batch 16: Table 7's caption and the Section 6.2 null -- #149 #160(b)
#164(a) #171.

  #149  The caption argues the autoregressive exclusion a third time.
        Section 6.1 and Section 1.2 both make that case; a reference is
        enough.
  #160(b) "A compatible evaluator" -- the scope of Eq.(fbzero) is a masked
        evaluator whose conditionals derive from one joint.
  #164(a) "within-text reading" is used from Section 6.2 on and never
        defined.  Its first use carries the definition.
  #171  The caption's column list skips the first two columns and names
        none of them, and after #151 there are two more.  All ten columns
        are named from the left.

Idempotent.  Run from the directory holding main.tex.  Depends on
fix_apply_tables.py for the two columns it describes.

    python3 -I fix_apply_b16.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #160(b) ----------------------------------------------------------
    ("sec_truesigma.tex",
     "Two situations make the $n!$ values coincide, and both must be reported at\n"
     "the null rather than ranked.  A compatible evaluator gives $f(\\pi) = 0$ for\n"
     "every $\\pi$ by Eq.~\\eqref{eq:fbzero};",
     "Two situations make the $n!$ values coincide, and both must be reported at\n"
     "the null rather than ranked.  A masked evaluator whose conditionals derive\n"
     "from one joint gives $f(\\pi) = 0$ for every $\\pi$ by\n"
     "Eq.~\\eqref{eq:fbzero};",
     "160b true:104"),

    # ---- #164(a) ----------------------------------------------------------
    ("sec_truesigma.tex",
     "\\FbNTexts\\ texts read by each of the two masked evaluators used here,\n"
     "\\texttt{bert-base-uncased} and \\texttt{LLaDA-8B-Base}.",
     "\\FbNTexts\\ texts read by each of the two masked evaluators used here,\n"
     "\\texttt{bert-base-uncased} and \\texttt{LLaDA-8B-Base}.\n"
     "\n"
     "This is the \\emph{within-text reading}: one text, its $n!$ arrangements\n"
     "scored by Eq.~\\eqref{eq:fbperm}, and the authored arrangement's midrank\n"
     "among them.  Section~\\ref{sec:fbresult} also reads $\\sigma$ a second way,\n"
     "without rearranging anything, and keeps the two apart throughout.",
     "164a true:108"),

    # ---- #149 + #171 ------------------------------------------------------
    ("sec_truesigma.tex",
     "the $n!$ arrangements of the same text's own sentences.  Columns: $n$ texts,\n"
     "how many were degenerate (all $n!$ values tied, hence reported at the null\n"
     "and excluded from $r$), the median midrank in each label group with a\n"
     "signed-rank test of that group against the $0.50$ null, and the\n"
     "rank-biserial effect size between the groups with its two-sided\n"
     "Mann--Whitney $p$.  Masked evaluators only: a model that attends\n"
     "only to what precedes emits none of the backward term's factors, and\n"
     "supplying them from its joint returns the zero of\n"
     "Eq.~\\eqref{eq:fbzero}.}",
     "the $n!$ arrangements of the same text's own sentences.  Columns from the\n"
     "left: the masked evaluator; the corpus; $n$, the texts in that cell; how\n"
     "many were degenerate (all $n!$ values tied, hence reported at the null and\n"
     "excluded from $r$); the median midrank of the causal group and of the\n"
     "non-causal group; $p_{c}$ and $p_{nc}$, the two-sided Wilcoxon signed-rank\n"
     "$p$ of each group against the $0.50$ null; $r$, the rank-biserial\n"
     "correlation of Eq.~\\eqref{eq:rb} between the two groups, negative when the\n"
     "causal group ranks lower; and its two-sided Mann--Whitney $p$.  The two\n"
     "signed-rank columns answer a different question from the last one: whether\n"
     "each group is displaced from the null at all, as against whether the groups\n"
     "differ from each other.  Masked evaluators only\n"
     "(Section~\\ref{sec:truesigma}).}",
     "149+171 tab:fbrank caption"),
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
    print("batch 16: Table 7 caption, the Section 6.2 null")
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
