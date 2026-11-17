#!/usr/bin/env python3
"""check_paper_selftest.py's clean fixture has no evaluator table.

check_paper.py's check_model_inventory keys on the header row of the
Section 3.1 evaluator table and fails when it cannot find one.  The
self-test's GOOD_TEX --- the document every defect case is a mutation of,
and the one case that must PASS --- never had that table, so the self-test
has been failing since that check was added.  It fails the same way on a
tree with none of the #69-#250 corrections applied, so this is not
something those introduced; make_repo.sh runs the self-tests from the copy
and refuses to publish while one fails, which is where it surfaced.

The fixture gains a minimal evaluator table with the header the check keys
on.  It is a plain centred tabular rather than a float, so it needs no
label and no reference and the crossref check is unaffected.

Idempotent.  Run from the directory holding check_paper_selftest.py.

    python3 -I fix_apply_selftest.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("check_paper_selftest.py",
     'We measure $\\sigblock$ and, for completeness, $\\sigtok$.\n'
     'The evaluators are masked language models \\cite{bert}.\n',
     'We measure $\\sigblock$ and, for completeness, $\\sigtok$.\n'
     'The evaluators are masked language models \\cite{bert}.\n'
     '\\begin{center}\n'
     '\\begin{tabular}{llll}\n'
     'model & parameters & direction & role \\\\\n'
     '\\texttt{bert-base-uncased} & 110\\,M & masked & $\\sigma$ \\\\\n'
     '\\end{tabular}\n'
     '\\end{center}\n',
     "evaluator table in GOOD_TEX"),
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
    print("self-test fixture: the evaluator table check_model_inventory needs")
    print("-" * 66)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 66)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 66)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
