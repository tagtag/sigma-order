#!/usr/bin/env python3
"""make_tables.py: the midrank grid (#253) and the tail test (#256).

#253  grid_macros divided by n! and then rounded.  Both are wrong.

      The grid.  Eq.(midrank) counts ties as halves and the authored
      arrangement is always tied with itself, so

          2 n! pct = 2a + t ,

      with a the count strictly below and t >= 1 the number tied.  That is
      an integer, and an odd one in the ordinary case t = 1, so a midrank
      falls halfway between the multiples of 1/n!: the grid is 1/2n!.
      With n = 4 that is 1/48 = 0.0208 and not 1/24 = 0.0417.

      The rounding.  steps.append(round(v / step)) turned the causal
      component into whole steps, which is how it printed as "1 to 2" while
      the authored component, printed unrounded, read 8.5 and 9.5 -- values
      that are 17/48 and 19/48 and could not have been whole steps of 1/24.
      The components are medians over texts, and a median over an even
      count is a mean of two grid values and need not be on the grid, so
      rounding them to whole steps states a precision they do not have.
      They are now printed to a tenth of a step, like the authored one.

      A guard checks what the argument does establish: that every midrank
      is on the 1/2n! grid.  check_grid_resolution.py checks the same thing
      standing alone, and reports where the medians fall.

      \\NPerms is untouched: it is n! = 24 and the paper still uses it for
      the size of the permutation set.  The grid denominator is \\GridK.

#256  The lower block of Table 5 reports the share of causal texts above
      the non-causal group's own 90th percentile, against a null of 10%.
      That is a one-sample question about a binomial proportion.  The code
      answered it with a Fisher exact test against a synthetic second row
      of the same size, which answers a two-sample question nobody asked
      and treats a constructed expectation as a draw.  binomtest is the
      test the caption describes, and it is already imported a few lines
      below for TailSignP.

Both change printed numbers, so make_tables.py must be re-run and the
tables and macros regenerated.  \\TailZNRejecting and \\TailZPMax will
move; Section 5.4 quotes both through macros and needs no edit.

Idempotent.  Run from the directory holding make_tables.py.

    python3 -I fix_apply_grid.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #253 the docstring ------------------------------------------------
    ("make_tables.py",
     "    The midrank over n! arrangements lives on a grid of width 1/n!.  With\n"
     "    n = 4 that is 1/24 = 0.0417, and a causal component of +0.042 is exactly\n"
     "    one grid step: the smallest non-zero value the statistic can take.  If\n",
     "    Eq.(midrank) counts ties as halves and the authored arrangement is\n"
     "    always tied with itself, so 2 n! pct = 2a + t is an integer and the\n"
     "    grid one reading lives on is 1/2n!, not 1/n!.  With n = 4 that is\n"
     "    1/48 = 0.0208, the smallest non-zero value a midrank can take, and a\n"
     "    causal component of +0.042 is two grid steps.  The components are\n"
     "    medians over texts and need not land on the grid, so they are printed\n"
     "    to a tenth of a step rather than rounded to whole ones.  If\n",
     "253 grid docstring"),

    # ---- #253 the step itself ----------------------------------------------
    ("make_tables.py",
     "    k = max(nperm)\n"
     "    step = 1.0 / k\n",
     "    # The grid is 1/2n!, not 1/n!: see this function's docstring and\n"
     "    # Eq.(midrank).  \\NPerms stays n!; \\GridK is the grid denominator.\n"
     "    k = 2 * max(nperm)\n"
     "    step = 1.0 / k\n"
     "    # What the argument establishes is that a midrank is on this grid.\n"
     "    # Section 5.3 says so, so the build stops rather than printing it\n"
     "    # when it is false.\n"
     "    loose = [float(r[\"percentile_written\"])\n"
     "             for recs in blk.values() for r in recs.values()\n"
     "             if np.isfinite(r.get(\"percentile_written\", float(\"nan\")))\n"
     "             and abs(float(r[\"percentile_written\"]) * k\n"
     "                     - round(float(r[\"percentile_written\"]) * k)) > 1e-6]\n"
     "    if loose:\n"
     "        raise SystemExit(\n"
     "            \"grid_macros: %d midranks are off the 1/%d grid (%s); \"\n"
     "            \"Section 5.3 states that grid as the resolution of one \"\n"
     "            \"reading\" % (len(loose), k,\n"
     "                          \", \".join(f\"{v:.6f}\" for v in loose[:4])))\n",
     "253 grid step and guard",
     "fix_apply_grid2.py (#258)"),

    # ---- #253 unrounded steps ----------------------------------------------
    ("make_tables.py",
     "        steps.append(round(v / step))\n",
     "        steps.append(v / step)\n",
     "253 unrounded steps"),

    ("make_tables.py",
     "    mac(\"CausalCompStepsMin\", str(min(steps)))\n"
     "    mac(\"CausalCompStepsMax\", str(max(steps)))\n"
     "    mac(\"CausalCompNDistinct\", str(len(set(steps))))\n",
     "    mac(\"CausalCompStepsMin\", trim_step(min(steps)))\n"
     "    mac(\"CausalCompStepsMax\", trim_step(max(steps)))\n"
     "    mac(\"CausalCompNDistinct\", str(len({trim_step(s) for s in steps})))\n",
     "253 step macros"),

    ("make_tables.py",
     "    mac(\"AuthoredCompStepsMin\", f\"{min(auth) / step:.1f}\")\n"
     "    mac(\"AuthoredCompStepsMax\", f\"{max(auth) / step:.1f}\")\n"
     "    mac(\"AuthoredCompSpanSteps\", f\"{(max(auth) - min(auth)) / step:.1f}\")\n",
     "    mac(\"AuthoredCompStepsMin\", trim_step(min(auth) / step))\n"
     "    mac(\"AuthoredCompStepsMax\", trim_step(max(auth) / step))\n"
     "    mac(\"AuthoredCompSpanSteps\", trim_step((max(auth) - min(auth)) / step))\n",
     "253 authored step macros"),

    # ---- #253 the formatter ------------------------------------------------
    ("make_tables.py",
     "def grid_macros(blk, kinds):\n",
     "def trim_step(v):\n"
     "    \"\"\"A step count to a tenth, without a trailing '.0'.\n"
     "\n"
     "    The components are medians and are not always whole steps, so they\n"
     "    cannot be printed as integers; printing 2.0 where 2 is meant reads\n"
     "    as a measured tenth that is not there.\n"
     "    \"\"\"\n"
     "    s = f\"{v:.1f}\"\n"
     "    return s[:-2] if s.endswith(\".0\") else s\n"
     "\n"
     "\n"
     "def grid_macros(blk, kinds):\n",
     "253 trim_step"),

    # ---- #256 the import ---------------------------------------------------
    ("make_tables.py",
     "    from scipy.stats import fisher_exact\n",
     "    from scipy.stats import binomtest, fisher_exact\n",
     "256 binomtest import"),

    # ---- #256 the test -----------------------------------------------------
    ("make_tables.py",
     "                exp = int(round((1 - TAIL_Q) * len(zc)))\n"
     "                _, pz = fisher_exact([[k, len(zc) - k], [exp, len(zc) - exp]])\n",
     "                # One-sample: is the share of causal texts above the\n"
     "                # non-causal group's own TAIL_Q percentile greater than\n"
     "                # the 1 - TAIL_Q that cut defines?  Fisher against a\n"
     "                # synthetic row of the same size answers a two-sample\n"
     "                # question that was never asked, and treats a constructed\n"
     "                # expectation as a draw.\n"
     "                pz = binomtest(k, len(zc), 1 - TAIL_Q,\n"
     "                               alternative=\"two-sided\").pvalue\n",
     "256 one-sample binomtest"),
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
    print("make_tables.py: the 1/2n! grid and the one-sample tail test")
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
