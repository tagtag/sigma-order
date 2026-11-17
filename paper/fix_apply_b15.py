#!/usr/bin/env python3
"""Batch 15: Sections 6.1 and 6.2 -- #144 #145 #146 #147 #160(a).

  #144  "sigma is not something it can be asked for" and "simultaneously
        trivial and unevaluable" read as though Eq.(3) itself fails to
        stand.  It stands; what fails is that an autoregressive evaluator
        cannot supply the conditionals it needs.  The sentence that then
        supplies them from the joint and reports the zero is withdrawn
        along with it: that is the reading Eq.(fbzero) is being asked not
        to carry.
  #145  "both quantities are non-zero for every one of them" and "nothing
        in that sweep" -- name the quantities and the sweep.
  #146  "no one joint accounts for all of those orders" -- say that this is
        what incompatibility is.  "Eq.(fbzero) does not bind it" -- name
        what it does not bind.  And the closing warning: the identity fixes
        what a non-zero reading means, but not what the value moves with,
        so whether it separates the labels is a measurement.
  #147  "A single sigma(x) says how much incompatibility one text exposes"
        and "whether causal order exposes more of it" read sigma's
        magnitude as an amount of something, which #146 has just ruled out.
  #160(a) Eq.(4)'s scope: it is about evaluators that can supply the
        conditionals Eq.(2) asks for, which is the masked ones.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b15.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #144 -------------------------------------------------------------
    ("sec_truesigma.tex",
     "its factors\n"
     "conditions on a suffix while the prefix is still unknown; a model that\n"
     "attends only to what precedes emits none of them, so $\\sigma$ is not\n"
     "something it can be asked for.  Those factors are nevertheless fixed by its\n"
     "joint, and anything fixed by a joint satisfies Eq.~\\eqref{eq:fbzero} by\n"
     "construction, so supplying them that way returns the zero rather than\n"
     "escaping it.  Unavailable, or zero: in neither case does it report anything\n"
     "about the text.  What is\n"
     "absent is not a number but an independent number: a\n"
     "masked model's backward term is new information because its conditionals\n"
     "derive from no joint, and an autoregressive model's conditionals do\n"
     "derive from a joint.  So\n"
     "$\\sigma$ is, for the evaluators Ref.~\\cite{sagawa2026} uses, simultaneously\n"
     "trivial and unevaluable.  That explains the substitution of $\\Delta$ for\n"
     "$\\sigma$; it does not license reading $\\Delta$ as $\\sigma$.",
     "its factors\n"
     "conditions on a suffix while the prefix is still unknown, and a model that\n"
     "attends only to what precedes emits none of them.  Equation~\\eqref{eq:fb}\n"
     "is well defined; what an autoregressive evaluator cannot do is supply the\n"
     "conditionals it asks for.  So $\\sigma$ is not evaluable on the\n"
     "autoregressive evaluators Ref.~\\cite{sagawa2026} uses.  What is absent is\n"
     "not a number but an independent number: a masked model's backward term is\n"
     "new information because its conditionals derive from no joint, and an\n"
     "autoregressive model's conditionals derive from one.  That explains the\n"
     "substitution of $\\Delta$ for $\\sigma$; it does not license reading $\\Delta$\n"
     "as $\\sigma$.",
     "144 true:45"),

    # ---- #146 + #145 + #160(a) --------------------------------------------
    ("sec_truesigma.tex",
     "A masked evaluator can be placed here, and is the only kind that can.  It\n"
     "supplies every conditional Eq.~\\eqref{eq:aoar} asks for, in any order, and no\n"
     "\\emph{one} joint accounts for all of those orders, so\n"
     "Eq.~\\eqref{eq:fbzero} does not bind it.  Appendix~\\ref{sec:toy} measured that incompatibility directly, as the\n"
     "entropy production $\\sigEP$ on a system small enough to enumerate, and\n"
     "Table~\\ref{tab:bayesroute} reads $\\sigma$ itself on those same models: both\n"
     "quantities are non-zero for every one of them, and nothing in that sweep\n"
     "relates their sizes (Section~\\ref{sec:fbresult} gives the rank correlation\n"
     "and the $n$ it rests on).  Here $\\sigma$ is read off real text, where the first of those\n"
     "two facts is what the identity predicts and the second is a warning against\n"
     "reading its magnitude as an amount.",
     "A masked evaluator can be placed here, and is the only kind that can.  It\n"
     "supplies every conditional Eq.~\\eqref{eq:aoar} asks for, in any order.  That\n"
     "is also the scope of Eq.~\\eqref{eq:fbzero}: it says that $\\sigma$ vanishes\n"
     "for an evaluator whose conditionals derive from one joint, and an evaluator\n"
     "that cannot supply those conditionals is not a case of it either way.  For a\n"
     "masked evaluator no \\emph{one} joint need account for all of the unmasking\n"
     "orders --- that is what incompatibility is --- and where none does,\n"
     "Eq.~\\eqref{eq:fbzero} does not force $\\sigma$ to zero.\n"
     "Appendix~\\ref{sec:toy} measured that incompatibility directly, as the\n"
     "entropy production $\\sigEP$ on a system small enough to enumerate, and\n"
     "Table~\\ref{tab:bayesroute} reads $\\sigma$ itself on those same models:\n"
     "$\\sigEP$ and $\\sigma$ are both non-zero at every width of that sweep, and\n"
     "nothing in it relates their sizes (Section~\\ref{sec:fbresult} gives the rank\n"
     "correlation and the $n$ it rests on).  Here $\\sigma$ is read off real text.\n"
     "What the identity fixes is what a non-zero reading means --- that the\n"
     "conditionals behind it derive from no single joint --- and not what the\n"
     "value moves with.  Whether it also happens to separate the two label groups\n"
     "is therefore not settled in advance, and has to be measured.",
     "145+146+160a true:64"),

    # ---- #147 -------------------------------------------------------------
    ("sec_truesigma.tex",
     "A single $\\sigma(x)$ says how much incompatibility one text exposes.  The\n"
     "question is whether \\emph{causal order} exposes more of it, and for that the\n"
     "text has to be compared with itself.",
     "A single non-zero $\\sigma(x)$ says that the conditionals behind it derive\n"
     "from no single joint, and nothing more; it is not an amount of anything.\n"
     "The question this section asks is narrower: whether the value $\\sigma$\n"
     "returns is nevertheless higher on the arrangement a text came in than on its\n"
     "rearrangements, and for that the text has to be compared with itself.",
     "147 true:78"),
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
            print(f"  skip  {label:<22} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                # A later batch rewrote this passage, so on a re-run neither
                # the old text nor this batch's own replacement is here.
                print(f"  pass  {label:<22} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<22} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<22} {name}")
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
    print("batch 15: Sections 6.1 and 6.2")
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
