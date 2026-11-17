#!/usr/bin/env python3
"""Batch 5: #207 capacity, #189 the gpt-2 rungs, #148 the two masked
evaluators, #122 pretrained on different data.

  #207  "capacity" is undefined and carries two senses: parameter count in
        the body, transformer width d in Appendix A.  The body sites move
        to "parameter count"; Appendix A keeps width d, which it defines.
        Sites: main.tex:677 (Table 1), :695, :699, :1414,
        sec_decomp.tex:227.
  #189  "the rungs that share a family" / "that are one family" never names
        the family.  It is the four gpt-2 rungs, the fifth being
        Qwen3-4B-Base.  The same sentences say "at that n no p can reach
        0.05" without giving n or the floor.
  #148  "the two evaluators" at sec_truesigma.tex:108 is the first use and
        says neither that they are masked nor which two.  main.tex:1425 and
        sec_truesigma.tex:223 take "masked" as well; sec_decomp.tex:70 is a
        different claim -- any two rungs of the AR ladder -- and says so.
  #122  "trained on a different corpus" reserves "corpus" for the five
        scored corpora; the evaluator was pretrained on different data.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b5.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #207 -------------------------------------------------------------
    ("main.tex",
     "& $\\ParamsGPTtwoMedium$ & autoregressive & $\\Delta$: capacity series \\\\",
     "& $\\ParamsGPTtwoMedium$ & autoregressive & $\\Delta$: parameter-count series \\\\",
     "207 table 1"),

    ("main.tex",
     "Four of the five autoregressive evaluators are a capacity series within one\n"
     "family, spanning $\\TrendCapSpanFamily$-fold from $\\ParamsGPTtwo$ to\n"
     "$\\ParamsGPTtwoXL$; the fifth extends the AR ladder to $\\TrendCapSpan$-fold but\n"
     "is a different family on a different corpus under a different recipe, so a\n"
     "trend across the whole AR ladder is not attributable to capacity alone",
     "Four of the five autoregressive evaluators differ in parameter count within one\n"
     "family, the four \\textsc{gpt-2} rungs, spanning $\\TrendCapSpanFamily$-fold from\n"
     "$\\ParamsGPTtwo$ to $\\ParamsGPTtwoXL$; the fifth, \\texttt{Qwen3-4B-Base},\n"
     "extends the AR ladder to $\\TrendCapSpan$-fold but is a different family\n"
     "pretrained on different data under a different recipe, so a\n"
     "trend across the whole AR ladder is not attributable to parameter count alone",
     "207+189+122 main:695",
     "batch 27 (#88)"),

    ("main.tex",
     "Everything stated against\ncapacity is stated over the AR ladder as a whole and we do not separate the",
     "Everything stated against\nparameter count is stated over the AR ladder as a whole and we do not separate the",
     "207 main:1414"),

    ("sec_decomp.tex",
     "That is not the\nsame variable as capacity: the top rung is a different family trained on a\n"
     "different corpus, so the AR ladder orders size and model provenance together",
     "That is not the\nsame variable as parameter count: the top rung is a different family\n"
     "pretrained on different data, so the AR ladder orders parameter count and\n"
     "evaluator provenance together",
     "207+122+123 decomp:227",
     "batch 14 (#121)"),

    # ---- #189 -------------------------------------------------------------
    ("main.tex",
     "\\TailZFamNEval\\ rungs that share a family, where only size differs, it\n"
     "keeps the same ordering (Section~\\ref{sec:window}; at that $n$ no $p$ can\n"
     "reach $0.05$, so this is an ordering and not a second trend).",
     "\\TailZFamNEval\\ \\textsc{gpt-2} rungs, where only parameter count differs, it\n"
     "keeps the same ordering (Section~\\ref{sec:window}; with $n = \\TailZFamNEval$\n"
     "the smallest attainable two-sided $p$ is $\\TailZFamFloor$, so this is an\n"
     "ordering and not a second trend).",
     "189 main:1272"),

    ("main.tex",
     "read again on the \\TailZFamNEval\\ rungs that are one family, where it keeps\n"
     "the same ordering.",
     "read again on the \\TailZFamNEval\\ \\textsc{gpt-2} rungs, where it keeps\n"
     "the same ordering.",
     "189 main:1419"),

    ("sec_decomp.tex",
     "same quantity on the \\TailZFamNEval\\ rungs that are one family and differ in\n"
     "size alone:",
     "same quantity on the \\TailZFamNEval\\ \\textsc{gpt-2} rungs, which differ in\n"
     "parameter count alone:",
     "189 decomp:347"),

    ("sec_decomp.tex",
     "trend --- with \\TailZFamNEval\\ points no two-sided $p$ below\n"
     "$\\TailZFamFloor$ is attainable, so nothing measured on four rungs could\n"
     "reach $0.05$ ---",
     "trend --- with $n = \\TailZFamNEval$ no two-sided $p$ below\n"
     "$\\TailZFamFloor$ is attainable, so nothing measured on those four rungs could\n"
     "reach $0.05$ ---",
     "189 decomp:350"),

    # ---- #148 -------------------------------------------------------------
    ("sec_truesigma.tex",
     "\\FbNTexts\\ texts read by each of the two evaluators.",
     "\\FbNTexts\\ texts read by each of the two masked evaluators used here,\n"
     "\\texttt{bert-base-uncased} and \\texttt{LLaDA-8B-Base}.",
     "148 true:108 first use"),

    ("sec_truesigma.tex",
     "\\FbBetweenNOpposite\\ of the \\FbBetweenNCompared\\ corpora the two evaluators",
     "\\FbBetweenNOpposite\\ of the \\FbBetweenNCompared\\ corpora the two masked evaluators",
     "148 true:223",
     "batch 18 (#159, #161, #175)"),

    ("main.tex",
     "more force to $\\sigma$, where the two evaluators differ in objective,",
     "more force to $\\sigma$, where the two masked evaluators differ in objective,",
     "148 main:1425"),

    ("sec_decomp.tex",
     "and a difference between two evaluators of one step is a difference between",
     "and a difference between any two evaluators of one step is a difference between",
     "148 decomp:70",
     "batch 42 (#265)"),
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
    print("batch 5: #207 capacity, #189 gpt-2 rungs, #148 masked evaluators, #122")
    print("-" * 72)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 72)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 72)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
