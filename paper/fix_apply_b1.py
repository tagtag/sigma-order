#!/usr/bin/env python3
"""Batch 1 of the #69-#226 application: the whole-paper term sweeps.

These are the corrections whose remedy is one wording used consistently
everywhere, rather than a rewrite of one passage.  They go first so that
the later batches can be written against text whose terms are already
settled.

  #126  "the extreme arrangement" / "the most costly arrangement"
        -> "the strict maximum", the name Section 5.3 gives it.
  #130  "the room above an authored arrangement" -> the gap between the
        authored arrangement's midrank and the 1.00 ceiling, said in words
        at each of the six sites.
  #155  "descend from a joint" -> "derive from a joint", and the two sites
        that say "come from one/any joint" brought into the same wording.
  #187  three names for one reading ("at the top of the range", "the
        tail", "in the upper tail") -> "the tail", with a single note at
        its first use in Section 5.3.
  #207  "capacity" -> "parameter count" in the body; Appendix A keeps
        width d, which it defines.

Idempotent: every replacement is checked for before being made, and a
second run reports 0 changes.  Run from the directory holding main.tex.

    python3 -I fix_apply_b1.py
    python3 -I fix_apply_b1.py --dry-run
"""

import argparse
import os
import sys

FILES = ["main.tex", "sec_intro.tex", "sec_decomp.tex", "sec_truesigma.tex"]

# (file, old, new, label).  old must occur exactly once unless count is given.
EDITS = [
    # ---- #155: descend -> derive ---------------------------------------
    ("main.tex",
     "identity that makes $\\sigma$ vanish wherever the conditionals descend from a",
     "identity that makes $\\sigma$ vanish wherever the conditionals derive from a",
     "155 main:289"),
    ("main.tex",
     "wherever the conditionals descend from a joint --- which is the case the",
     "wherever the conditionals derive from a joint --- which is the case the",
     "155 main:1329",
     "batch 21 (#160c)"),
    ("main.tex",
     "conditionals that descend from a joint, so a route through one cannot report",
     "conditionals that derive from a joint, so a route through one cannot report",
     "155 main:1567",
     "batch 25 (#215, #222)"),
    ("main.tex",
     "orders.  That failure to come from one joint is what we call the",
     "orders.  That failure to derive from one joint is what we call the",
     "155 main:262"),
    ("main.tex",
     "come from any joint.  The incompatibility that gives $\\sigEP$ its floor is",
     "derive from any joint.  The incompatibility that gives $\\sigEP$ its floor is",
     "155 main:1605",
     "batch 26 (#225)"),
    ("sec_intro.tex",
     "conditionals descending from no joint --- as exposed by that text.  We",
     "conditionals deriving from no joint --- as exposed by that text.  We",
     "155 intro:176"),
    ("sec_intro.tex",
     "identically zero wherever the conditionals descend from a joint, so whatever",
     "identically zero wherever the conditionals derive from a joint, so whatever",
     "155 intro:200"),
    ("sec_truesigma.tex",
     "--- the failure of its conditionals to descend from any joint --- as exposed",
     "--- the failure of its conditionals to derive from any joint --- as exposed",
     "155 true:38"),
    ("sec_truesigma.tex",
     "descend from no joint, and an autoregressive model's conditionals do\ndescend from a joint.  So",
     "derive from no joint, and an autoregressive model's conditionals do\nderive from a joint.  So",
     "155 true:57-58",
     "batch 15 (#144)"),
    ("sec_truesigma.tex",
     "that where the conditionals descend from a joint there is no value range at",
     "that where the conditionals derive from a joint there is no value range at",
     "155 true:207"),
    ("sec_truesigma.tex",
     "wherever the conditionals descend from a joint, so a reading of any size is",
     "wherever the conditionals derive from a joint, so a reading of any size is",
     "155 true:250"),

    # ---- #126: one name for the strict maximum --------------------------
    ("main.tex",
     "how often the authored arrangement is already the single most costly arrangement.",
     "how often the authored arrangement is already the strict maximum over its\n$n!$ arrangements.",
     "126 main:947"),
    ("main.tex",
     "extreme arrangement establishing no trend across the AR ladder",
     "strict maximum establishing no trend across the AR ladder",
     "126 main:1313",
     "batch 21 (#193, #195)"),
    ("sec_decomp.tex",
     "authored arrangement \\emph{is} the extreme arrangement no normalisation can",
     "authored arrangement \\emph{is} the strict maximum no normalisation can",
     "126 decomp:234"),
    ("sec_decomp.tex",
     "causal texts at the extreme arrangement, which references no other group,",
     "causal texts at the strict maximum, which references no other group,",
     "126 decomp:366"),
]


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

    print("batch 1: whole-paper term sweeps (#126, #155)")
    print("-" * 60)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 60)
        print("FAIL  nothing written; fix the target above and re-run.")
        return 1
    made, skipped, passed = result
    print("-" * 60)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
