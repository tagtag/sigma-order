#!/usr/bin/env python3
"""make_repo.sh never ships paper/ceiling_gap.log or ceiling_resolution.log.

check_readme.py counts 49 files named in README.md's Layout and finds 47 in
the assembled copy; the two missing are the measurement logs that live in
paper/.  Two separate causes, both in make_repo.sh:

  * the copy step takes paper/*.tex, *.py, *.sh and *.txt, and no *.log, so
    neither log reaches the copy at all;
  * the .gitignore it writes excludes paper/*.log with one exception,
    !paper/ceiling_resolution.log, and ceiling_gap.log has none.

Both logs are named in the README, so both have to be copied and both have
to be exempt.  The blanket paper/*.log rule stays: it is there to keep
LaTeX's own logs out, and build.log and the arXiv logs are still ignored.

The two logs are produced by, from paper/, a python that has numpy and
scipy:

    python3 -I ceiling_resolution.py ../order-intervention/results_blkord \\
        > ceiling_resolution.log 2>&1
    python3 -I ceiling_gap.py ../order-intervention/results_blkord \\
        > ceiling_gap.log 2>&1

Idempotent.  Run from the directory holding make_repo.sh.

    python3 -I fix_apply_repo.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    ("make_repo.sh",
     'cp "$SRC/paper"/*.txt "$REPO/paper/" 2>/dev/null || true\n',
     'cp "$SRC/paper"/*.txt "$REPO/paper/" 2>/dev/null || true\n'
     '# The measurement logs README.md names in its Layout.  Not *.log: that\n'
     '# would take build.log and the arXiv logs with it.  Named one by one, so\n'
     '# that a log added later and listed in the README fails check_readme.py\n'
     '# here rather than reaching a reader as a dangling line.\n'
     'for f in ceiling_resolution.log ceiling_gap.log; do\n'
     '    [ -f "$SRC/paper/$f" ] && cp "$SRC/paper/$f" "$REPO/paper/"\n'
     'done\n',
     "copy the two logs"),

    ("make_repo.sh",
     "!paper/ceiling_resolution.log\n",
     "!paper/ceiling_resolution.log\n"
     "# ...and the one beside it, which records what the rise in the\n"
     "# ceiling-fraction gap is made of.  README.md names both.\n"
     "!paper/ceiling_gap.log\n",
     "exempt ceiling_gap.log"),
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
            print(f"  skip  {label:<24} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                print(f"  pass  {label:<24} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<24} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<24} {name}")
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
    print("make_repo.sh: ship the two measurement logs README.md names")
    print("-" * 60)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 60)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 60)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
