#!/usr/bin/env python3
"""Batch 41: #263 -- the AI-use acknowledgment APS requires in the paper.

APS requires substantive AI use to be disclosed in the submitted paper, and
names what the disclosure must contain: the tool and its version, how it
assisted, and how the authors directed and verified its output.  Use in the
conduct of the research belongs in the methods, figure generation in the
caption, everything else in the acknowledgments.  Nothing here was used to
produce a measurement or a figure, so the acknowledgments is the place.

The section goes after Reproducibility and before \\appendix, which is where
a reader looking for it will be and keeps it out of the appendix.  arXiv
asks for disclosure too and the v1 Comments field carries it; this is the
copy that travels with the PDF, which is what a referee reads.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b41.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("main.tex",
     "\\fn{capacity_sweep.py} from the same seed and reproducing its $\\sigEP$\n"
     "column exactly before giving each of them the second route.\n"
     "\n"
     "% =====================================================================\n"
     "% The toy system was Section 4.3 of the main text.",

     "\\fn{capacity_sweep.py} from the same seed and reproducing its $\\sigEP$\n"
     "column exactly before giving each of them the second route.\n"
     "\n"
     "\\section*{Acknowledgments}\n"
     "\n"
     "The author used two AI assistants in preparing this paper and records\n"
     "their use here.  Claude (Anthropic, claude-opus-5) assisted in\n"
     "drafting and revising the text, in a sentence-by-sentence review of the\n"
     "manuscript that produced most of the corrections it went through, and in\n"
     "writing several of the verification scripts distributed with it.\n"
     "ChatGPT (OpenAI, GPT-6) gave a critical reading of a late draft.\n"
     "Neither was used to produce any measurement or any figure.\n"
     "\n"
     "Every number in this paper comes from the author's own code, run on the\n"
     "author's machines, and every quoted value was checked against the script\n"
     "that generates it.  The author directed the work, accepted or rejected\n"
     "each suggestion, and is responsible for the content.\n"
     "\n"
     "% =====================================================================\n"
     "% The toy system was Section 4.3 of the main text.",
     "263 acknowledgments"),
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
    print("batch 41: the AI-use acknowledgment")
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
