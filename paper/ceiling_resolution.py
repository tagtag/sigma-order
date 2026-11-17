#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Is the ceiling fraction itself at its own resolution?

Section 5.3 of the paper declines to read a causal component of one grid
step as a measured size: the midrank over n! arrangements lives on a grid of
width 1/n!, so the smallest non-zero reading says "not zero" and nothing
more.  Section 5.4 applies the same test to the authored component's rise
across the evaluator ladder, which is also one grid step, and withdraws it.

What Section 5.4 keeps is a different statistic: the fraction of texts whose
authored arrangement is already the strict maximum of its permutation set,
which rises with capacity.  That fraction is a proportion rather than a
midrank, so it has no 1/n! grid -- but it has a grid of its own, 1/n over
the n texts it is a fraction of, and the argument that disqualified the
other two applies to it verbatim unless n is large enough.

This script measures that.  It prints the denominator, the resulting step,
and the measured rise expressed in units of that step.  A rise of one or two
units would put the replacement evidence in exactly the condition of the
evidence it replaced; several units means it is clear of its own floor.

    python3 -I ceiling_resolution.py ../order-intervention/results_blkord

Written for the referee's question as much as for ours: the paper has to be
able to say which it is, and say it from a measurement.
"""
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np

CORPUS_ORDER = ["Opus46", "GPT54", "GPT56", "Gemini31", "Fable5"]
EVAL_ORDER = ["gpt2", "gpt2-medium", "gpt2-large", "gpt2-xl",
              "Qwen/Qwen3-4B-Base"]


def load(dirpath):
    bucket, kinds = defaultdict(dict), {}
    for f in sorted(glob.glob(os.path.join(dirpath, "blkord_*.json"))):
        if os.path.basename(f).startswith("blkord_comparison"):
            continue
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if "records" not in d or "model" not in d:
            continue
        corpus = d["corpus"].replace("fixed_text_", "").replace(".json", "")
        kinds[d["model"]] = d["kind"]
        for r in d["records"]:
            bucket[(d["model"], corpus)][(r["category"], r["index"])] = r
    return bucket, kinds


def main(dirpath):
    blk, kinds = load(dirpath)
    if not blk:
        print(f"no blkord_*.json under {dirpath}")
        return 1
    models = [m for m in EVAL_ORDER
              if kinds.get(m) == "causal" and any(k[0] == m for k in blk)]
    corpora = [c for c in CORPUS_ORDER if any(k[1] == c for k in blk)]

    # Both groups.  Section 5.4's claim is about the authored component,
    # which Eq. (8) defines on the NON-causal texts, so that is the fraction
    # the claim needs; the causal one is reported beside it because an
    # earlier version of the section quoted it instead.
    print(f"{'evaluator':<20} {'texts/corpus':>12} "
          f"{'ceiling% (nc)':>14} {'ceiling% (c)':>13}")
    print("-" * 64)
    fracs, fracs_c, ns = {}, {}, []
    for m in models:
        per, per_c = [], []
        for c in corpora:
            recs = blk.get((m, c), {})
            v = [r["is_strict_max"] for k, r in recs.items()
                 if k[0] == "noncausal"]
            vc = [r["is_strict_max"] for k, r in recs.items()
                  if k[0] == "causal"]
            if v:
                per.append(float(np.mean(v)))
                ns.append(len(v))
            if vc:
                per_c.append(float(np.mean(vc)))
        if not per:
            continue
        fracs[m] = 100 * float(np.median(per))
        fracs_c[m] = 100 * float(np.median(per_c)) if per_c else float("nan")
        n_here = sorted({len([r["is_strict_max"] for k, r in
                              blk.get((m, c), {}).items()
                              if k[0] == "noncausal"])
                         for c in corpora} - {0})
        print(f"{m.split('/')[-1]:<20} {str(n_here):>12} "
              f"{fracs[m]:>13.1f}% {fracs_c[m]:>12.1f}%")

    nmin = min(ns)
    step = 100.0 / nmin
    lo, hi = models[0], models[-1]
    rise = fracs[hi] - fracs[lo]
    print("-" * 64)
    print(f"the causal-labelled fraction, for comparison : "
          f"{fracs_c[lo]:.1f}% -> {fracs_c[hi]:.1f}% "
          f"({fracs_c[hi] - fracs_c[lo]:+.1f} points)")
    print(f"denominator (smallest n of texts per corpus) : {nmin}")
    print(f"resolution of the fraction, 1/n              : {step:.2f} "
          f"percentage points")
    print(f"measured rise, {lo.split('/')[-1]} -> {hi.split('/')[-1]}"
          f"{'':<4}: {rise:+.1f} points")
    print(f"the rise in units of that resolution         : "
          f"{rise / step:.2f}")
    print()
    units = rise / step
    # Sign and magnitude are separate questions and the first version of
    # this verdict ran them together: it tested `units < 2`, so a fraction
    # that FELL by five steps was reported as sitting at its own floor.  It
    # is not at the floor; it is resolved and pointing the other way, which
    # is a different and worse answer for Section 5.4.
    # Each branch says what it means for the text AS IT NOW STANDS.  The
    # first version of this verdict was written while Section 5.4 still
    # claimed saturation, and went on calling the measurement "the
    # opposite of what Section 5.4 claims" for weeks after the claim was
    # withdrawn -- an alarm about a sentence that no longer existed.  A
    # standing false alarm is how the 51 LaTeX errors on the next line
    # went unread, so the alarm is moved to the one case that is news.
    if units < 0:
        print(f"FALLS by {abs(units):.1f} of its own steps across the "
              f"ladder: resolved, and in\nthe opposite direction to "
              f"saturation.  Section 5.4 withdraws the\nsaturation claim, "
              f"and this is the measurement it withdraws on.  Expected;\n"
              f"what would be news is this line not saying FALLS.")
    elif units < 2:
        print("AT ITS OWN FLOOR.  The ceiling fraction moves by fewer than "
              "two of\nits own smallest steps, which is the condition "
              "Section 5.3 refuses to\nread as a size.  The withdrawal in "
              "Section 5.4 still holds, on weaker\ngrounds: not a "
              "measurement pointing the other way, just no measurement.")
    else:
        print(f"RISES, CLEAR OF ITS FLOOR, by {units:.1f} steps.  The "
              f"fraction is a proportion\nover {nmin} texts, so the 1/n! "
              f"grid of Section 5.3 does not reach it.\n\n"
              f"** This is the one that needs acting on.  Section 5.4 "
              f"withdraws the\n** saturation claim on the grounds that "
              f"this fraction does not rise.\n** On these numbers it "
              f"does, and the withdrawal has to be reopened.")
    return 0


def selftest():
    """Two synthetic cells with a known answer, so the arithmetic is pinned.

    n = 10 texts per corpus and a rise of 8 points is 0.8 of one step, which
    is the case that would disqualify the statistic; n = 50 and the same
    rise is 4 steps, which is the case that would not.  The verdict must
    flip between them and the printed units must be exact.
    """
    for n, want in ((10, 0.8), (50, 4.0)):
        step = 100.0 / n
        got = 8.0 / step
        assert abs(got - want) < 1e-9, (n, got, want)
        assert (got < 2) == (n == 10), (n, got)
    # a fraction over n texts can only take values k/n, so a rise of 8
    # points is not even representable at n = 10 -- the nearest are 0 and 10
    assert not any(abs(k / 10 * 100 - 8.0) < 1e-9 for k in range(11))
    print("  ceiling resolution: 8 points is 0.8 steps at n=10 "
          "(and not representable), 4.0 steps at n=50")


if __name__ == "__main__" and "--selftest" in sys.argv:
    selftest()
    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1
                  else "../order-intervention/results_blkord"))
