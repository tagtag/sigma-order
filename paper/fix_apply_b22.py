#!/usr/bin/env python3
"""Batch 22: #197 and #205 -- the closing paragraph of Section 7, and the
credit Ref.[1] is owed for the labelling caveat.

  #197  An addition the author asked for: a paragraph at the end of
        Section 7 saying what was gained by introducing sigma at all, given
        that it does not separate the two label groups.
  #205  Ref.~[1] Sec. V B states for itself that the causal/non-causal
        labels are defined by the generation prompt rather than by a formal
        criterion, that it makes no claim to a general quantitative measure
        of causal structure, and that a prompt-independent definition would
        be needed.  Section 5.1 credits this; Section 7's "as a test"
        paragraph and Section 8's label item did not.  (The absence of a
        human-written control is a different matter and is NOT in Ref.~[1],
        so it is not credited there; see #205 in the corrections table.)

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b22.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #205, Section 7 ---------------------------------------------------
    ("main.tex",
     "but the\nsets were never\ncharacterised\n"
     "except by the prompt that produced them, so the separation has no established\nreferent.",
     "but the\nsets were never characterised except by the prompt that produced them, so\n"
     "the separation has no established referent.  Ref.~\\cite{sagawa2026} says as\n"
     "much for its own corpora: the labels are fixed by the generation prompt\n"
     "rather than by a formal criterion, and a prompt-independent definition of\n"
     "causal ordering would be needed to do better~\\cite[Sec.~V~B]{sagawa2026}.",
     "205 sec7"),

    # ---- #197 --------------------------------------------------------------
    ("main.tex",
     "On a masked evaluator the quantity is\n"
     "defined, and Section~\\ref{sec:fbresult} measures what it reports there: a\n"
     "property of the masked evaluator, not of the text.",
     "On a masked evaluator the quantity is\n"
     "defined, and Section~\\ref{sec:fbresult} measures what it reports there: a\n"
     "property of the masked evaluator, not of the text.\n"
     "\n"
     "It may be asked what was gained by introducing $\\sigma$ at all, if it does\n"
     "not separate the two label groups.  Three things.  That a non-zero $\\sigma$\n"
     "reads the masked evaluator's incompatibility does not settle whether its\n"
     "value also happens to separate the causal and non-causal groups; nothing\n"
     "fixes that in advance, so it had to be measured.  What Section~\\ref{sec:fbresult}\n"
     "returned is that on these two masked evaluators only \\FbNSurviving\\ of\n"
     "\\FbNTestsCausal\\ cells survives correction --- which is a statement about\n"
     "these two and not about masked evaluators in general.  And $\\sigma$, not\n"
     "$\\Delta$, is what the thermodynamic reading extends to directly, so how it\n"
     "behaves on real text is worth knowing in its own right.",
     "197 sec7 closing",
     "batch 29 (cold read)"),
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
    print("batch 22: #197 the closing paragraph, #205 the Ref.[1] credit")
    print("-" * 62)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 62)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 62)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
