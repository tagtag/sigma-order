#!/usr/bin/env python3
"""Batch 4: one name for the tail (#187), ceiling-free z in Section 7
(#185), and the table citation the no-extrapolation item lacked (#206).

  #187  Three names were in use for one reading: "at the top of the range",
        "the tail", and "in the upper tail".  The paper settles on "the
        tail", and says once, at its first use in Section 5.3, what it is:
        the top of the midrank range.  Remaining sites after batch 3:
        sec_decomp.tex:136, :164, :194 (Table 5 caption), main.tex:1396.
  #185  Section 7 uses "ceiling-free units" without ever tying it to the
        z of Section 5.3.  Its first use in that section now carries the
        definition, and the second says "ceiling-free z units".
  #206  "the labelled contrast in the tail, in ceiling-free units" cites no
        table.  It is the lower block of Table 5, median TailZGPTtwo to
        TailZQwen.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b4.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #187: first use in Section 5.3 carries the one note -------------
    ("sec_decomp.tex",
     "Table~\\ref{tab:tail} gives the contrast at the top of the range cell by\ncell:",
     "Table~\\ref{tab:tail} gives the contrast in the tail --- the top of the\n"
     "midrank range --- cell by cell:",
     "187 decomp:136 first use"),

    ("sec_decomp.tex",
     "about the contrast.  Read at the top of the range the same labels on the",
     "about the contrast.  Read in the tail the same labels on the",
     "187 decomp:164"),

    ("sec_decomp.tex",
     "\\caption{The causal/non-causal contrast at the top of the range, for every",
     "\\caption{The causal/non-causal contrast in the tail, for every",
     "187 decomp:194 caption"),

    # ---- #187 + #206: Section 8, no extrapolation ------------------------
    ("main.tex",
     "One quantity rises\nmonotonically over the range measured --- the labelled contrast in the\n"
     "upper tail, in ceiling-free units --- and we state it as that and nothing\nmore.",
     "One quantity rises\nmonotonically over the range measured --- the labelled contrast in the\n"
     "tail, in ceiling-free $z$ units (Table~\\ref{tab:tail}, second block: a median\n"
     "of $\\TailZGPTtwo$ at \\texttt{gpt2} and $\\TailZQwen$ at the top of the\n"
     "AR ladder) --- and we state it as that and nothing more.",
     "187+206 main:1396"),

    # ---- #185: Section 7, first use defines z ----------------------------
    ("main.tex",
     "to the labels in ceiling-free units ($\\ShareEvalMin\\%$ to",
     "to the labels in ceiling-free $z$ units\n"
     "($z = \\Delta(\\mathrm{id})/\\mathrm{sd}\\{\\Delta(\\pi)\\}$,\n"
     "Section~\\ref{sec:resolution}; $\\ShareEvalMin\\%$ to",
     "185 main:1255"),

    ("main.tex",
     "In\nceiling-free units that separation grows monotonically along the AR ladder",
     "In\nceiling-free $z$ units that separation grows monotonically along the AR ladder",
     "185 main:1268"),
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
    print("batch 4: #187 the tail, #185 ceiling-free z, #206 table citation")
    print("-" * 68)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 68)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 68)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
