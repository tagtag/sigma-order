#!/usr/bin/env python3
"""Batch 25: Appendix A, the route control -- #214 #215 #222 #223 #224
#225 #226(b).

  #215  The route-control paragraph starts from its conclusion and gives
        the grounds afterwards, so it cannot be followed.  It becomes three
        paragraphs in order: what the two routes are and why the table of
        the previous section leaves a question open; what Table 11 does and
        what it returns; and what the zero does and does not establish.
  #214  "Table 11 gives the same model both routes at every width" and
        "Every route through a joint returns zero" -- say which model and
        how many joints.
  #222  The two routes are stated in prose only, and "Eq.(sigep) vanishes
        for any conditionals that derive from a joint" is left as an
        assertion.  Two lines of algebra make it a proof.
  #223  "how far the recovered conditionals are from the model's own" --
        with p_theta and p_Q named, say it in symbols.
  #224  "which is what the identity predicts for a model whose conditionals
        belong to no joint" -- the identity has no antecedent, and neither
        Eq.(4) nor Eq.(sigep) predicts a non-zero value.  Both say a
        quantity vanishes if the conditionals derive from one joint; that
        the measured values are non-zero is a measurement.
  #225  "The incompatibility that gives sigEP its floor" -- the noun is
        first used here, and "its floor" is a measured level and not a
        proven bound.
  #226(b) The remaining sigEP uses of "floor": Section 8's item, the two
        captions, and the three sites in this appendix.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b25.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #215 + #214 + #222 -------------------------------------------------
    ("main.tex",
     "The reading therefore belongs to the conditionals the model emits, and not to\n"
     "the route.  Table~\\ref{tab:bayesroute} gives the same model both routes at\n"
     "every width.  Every route through a joint returns zero, to\n"
     "$\\CtrlSigmaJointMax$; the emitted conditionals do not.  That zero is not\n"
     "evidence about the model --- Eq.~\\eqref{eq:sigep} vanishes for any\n"
     "conditionals that derive from a joint, so a route through one cannot report\n"
     "anything else --- but it is what makes the asymmetry harmless: the two routes\n"
     "coincide exactly when a joint exists, so the difference in construction can\n"
     "produce a difference in value only where the property under test fails.",
     "Computing $\\sigEP$ needs conditionals, and from a masked model there are two\n"
     "ways to get them.  Let $x$ and $y$ differ at site $k$ alone, so that\n"
     "$x_{-k} = y_{-k}$.  The \\emph{emitted} route takes what one forward pass\n"
     "with site $k$ masked returns,\n"
     "\\begin{equation}\n"
     "w_{\\mathrm{emit}}(x \\to y) \\;=\\; \\frac{1}{L}\\, p_\\theta(y_k \\mid x_{-k}) ,\n"
     "\\label{eq:wemit}\n"
     "\\end{equation}\n"
     "and the \\emph{recovered} route builds a joint $Q$ over whole sequences from\n"
     "the same model and renormalises it at site $k$,\n"
     "\\begin{equation}\n"
     "w_{\\mathrm{rec}}(x \\to y) \\;=\\; \\frac{1}{L}\\, p_Q(y_k \\mid x_{-k}) ,\n"
     "\\qquad\n"
     "p_Q(y_k \\mid x_{-k}) \\;=\\;\n"
     "  \\frac{Q(x_{-k}, y_k)}{\\sum_{v} Q(x_{-k}, v)} .\n"
     "\\label{eq:wrec}\n"
     "\\end{equation}\n"
     "An autoregressive model has no emitted route, so the autoregressive row of\n"
     "Table~\\ref{tab:capacity} is built the second way --- which leaves open\n"
     "whether that table's contrast is a property of the models or of the route.\n"
     "\n"
     "Table~\\ref{tab:bayesroute} closes it.  At each width it takes \\emph{one}\n"
     "trained masked model and builds its Glauber rates both ways, recovering from\n"
     "three different joints $Q$, which Table~\\ref{tab:bayesroute} names.\n"
     "The two readings are of the same model, so any\n"
     "difference between them is the route and nothing else.  Every recovered\n"
     "route returns zero, to $\\CtrlSigmaJointMax$; the emitted one does not.\n"
     "\n"
     "That zero is not evidence about the model.  Equation~\\eqref{eq:sigep}\n"
     "vanishes for any rates built from a joint, as Eq.~\\eqref{eq:wrec} shows\n"
     "directly: $Q(x)\\,w_{\\mathrm{rec}}(x \\to y)$ equals\n"
     "$\\tfrac{1}{L}\\,Q(x_{-k}, x_k)\\,Q(x_{-k}, y_k) / \\sum_{v} Q(x_{-k}, v)$,\n"
     "which is symmetric under exchanging $x_k$ and $y_k$ and therefore equals\n"
     "$Q(y)\\,w_{\\mathrm{rec}}(y \\to x)$.  Detailed balance holds with respect to\n"
     "$Q$ and $\\sigEP$ vanishes identically, so a route through a joint cannot\n"
     "report anything else.  What makes the asymmetry harmless is that the two\n"
     "routes coincide exactly when a joint exists, so a difference in construction\n"
     "can produce a difference in value only where the property under test fails.\n"
     "For the emitted route there is no such cancellation: $p_\\theta(\\cdot \\mid\n"
     "x_{-k})$ does not take the shape $Q(x_{-k}, \\cdot) / \\sum_{v} Q(x_{-k}, v)$\n"
     "for any single $Q$, and that is what is being measured.",
     "214+215+222 main:1665",
     "batch 26 (#225, #226)"),

    # ---- #223 --------------------------------------------------------------
    ("main.tex",
     "What the control does measure is how far the recovered conditionals are from\n"
     "the model's own: a Jeffreys divergence $J$ runs from $\\CtrlJeffreysMin$ to\n"
     "$\\CtrlJeffreysMax$ at\n"
     "the widest model, \\emph{depending on which joint was recovered from}.",
     "What the control does measure is how far $p_Q$ is from $p_\\theta$: a\n"
     "Jeffreys divergence $J$ between the two runs from $\\CtrlJeffreysMin$ to\n"
     "$\\CtrlJeffreysMax$ at the widest model, \\emph{depending on which joint $Q$\n"
     "was recovered from}.",
     "223 main:1676"),

    # ---- #224 --------------------------------------------------------------
    ("main.tex",
     "Both quantities are non-zero at every width, which is what the\n"
     "identity predicts for a model whose conditionals belong to no joint, read in\n"
     "two quantities rather than one.",
     "Both $\\sigEP$ and $\\sigma$ are non-zero at every width.  Each would have to\n"
     "vanish if the conditionals derived from one joint --- $\\sigEP$ by\n"
     "Eq.~\\eqref{eq:sigep}, $\\sigma$ by Eq.~\\eqref{eq:fbzero} --- so neither zero\n"
     "is available to this model; that the measured values are non-zero is a\n"
     "measurement and not a prediction of either identity.  One failure, read in\n"
     "two quantities rather than one.",
     "224 main:1685"),
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
            print(f"  skip  {label:<24} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                # A later batch rewrote this passage, so on a re-run neither
                # the old text nor this batch's own replacement is here.
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
    print("batch 25: Appendix A, the route control")
    print("-" * 54)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 54)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 54)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
