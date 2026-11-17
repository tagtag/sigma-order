#!/usr/bin/env python3
"""Batch 18: Section 6.3, the between-set reading -- #157(b) #158 #159
#160(b) #161 #162 #164(b) #165 #166 #175.

  #157(b) "sigma separates the authored arrangement from its rearrangements
        by an amount that depends on which masked evaluator is used" is the
        authored component again, under another name.
  #158  "carries the evaluator's incompatibility, and carries it large
        enough to dominate everything else" reads sigma's magnitude as an
        amount, which Section 6.1 has just ruled out.  Two measured facts
        replace it.
  #159  Table 9's upper block is not the authored component: make_tables.py
        takes the median of sigma over all live texts of a cell, both
        labels together.  And its null is zero, not 0.50.
  #160(b) "an evaluator whose conditionals came from a joint" -- a masked
        one, and "derive".
  #161  "do not agree on the sign" -- of what.  FbBetweenNOpposite counts
        the sign of the upper block, not of the causal component below it.
  #162  "Equation (fbzero) settles that before any corpus is scored" --
        what is settled in advance.
  #164(b) / #175  "the between-set reading" is used for the scoring mode,
        while Section 5.1 uses "between-set" for the comparison between the
        two label groups.  The scoring mode becomes the "unrearranged
        reading", paired with the within-text reading of Section 6.2.
  #165 / #166  "the same side of zero as the within-text reading" -- say
        the direction, and that the two readings are in different units.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b18.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #157(b) + #158 ---------------------------------------------------
    ("sec_truesigma.tex",
     "Taken together: $\\sigma$ separates the authored arrangement from its\n"
     "rearrangements by an amount that depends on which masked evaluator is used,\n"
     "and the separation between causally and arbitrarily ordered texts that\n"
     "$\\Delta$ shows in \\ContrastNRejecting\\ of \\ContrastNCells\\ cells does not\n"
     "reappear here.  This is\n"
     "Eq.~\\eqref{eq:fbzero} seen from the measurement side.  The identity says\n"
     "that where the conditionals derive from a joint there is no value range at\n"
     "all; what the measurement adds is that where they do not --- which is the\n"
     "case for \\texttt{bert-base} and \\texttt{LLaDA} alike --- the range that opens carries the\n"
     "evaluator's incompatibility, and carries it large enough to dominate\n"
     "everything else.",
     "Taken together: the authored component under $\\sigma$ moves\n"
     "$\\FbStepGap$ grid steps when the masked evaluator is changed, while\n"
     "exchanging the causal and non-causal labels leaves \\FbNSurviving\\ of\n"
     "\\FbNCells\\ cells surviving correction.  The separation between causally and\n"
     "arbitrarily ordered texts that $\\Delta$ shows in \\ContrastNRejecting\\ of\n"
     "\\ContrastNCells\\ cells does not reappear here.  This is\n"
     "Eq.~\\eqref{eq:fbzero} seen from the measurement side.  The identity says\n"
     "that where the conditionals derive from a joint there is no value range at\n"
     "all; what the measurement adds is that where they do not --- which is the\n"
     "case for \\texttt{bert-base} and \\texttt{LLaDA} alike --- what moves inside\n"
     "the range that opens is the evaluator and not the label.",
     "157b+158 true:229"),

    # ---- #159 + #160(b) + #161 + #175 (caption) ---------------------------
    ("sec_truesigma.tex",
     "\\caption{The between-set reading of Eq.~\\eqref{eq:fb}.  \\emph{Upper block}:\n"
     "the median $\\sigma$ of the authored arrangement itself, per token, with\n"
     "nothing rearranged.  \\emph{Lower block}: the causal component of the same\n"
     "reading, the median $\\sigma$ of the causally labelled texts less that of\n"
     "the non-causal ones, in the same cells.  For\n"
     "an evaluator whose conditionals came from a joint every entry would be\n"
     "exactly zero by Eq.~\\eqref{eq:fbzero}.  None is, and on\n"
     "\\FbBetweenNOpposite\\ of the \\FbBetweenNCompared\\ corpora the two masked evaluators\n"
     "do not agree on the sign.}",
     "\\caption{The unrearranged reading of Eq.~\\eqref{eq:fb}: each text scored\n"
     "once in each direction, in the arrangement it came in, with no permutation\n"
     "set and no midrank.  \\emph{Upper block}: the median $\\sigma$ over all of a\n"
     "cell's texts, both label groups together, per token.  It is not the authored\n"
     "component of Eq.~\\eqref{eq:auth}, which is a midrank against a null of\n"
     "$0.50$; the null here is $\\sigma = 0$.  \\emph{Lower block}: the causal\n"
     "component of this reading --- the median $\\sigma$ of the causally labelled\n"
     "texts less that of the non-causal ones --- which shares its name with\n"
     "Eq.~\\eqref{eq:caus} but is a difference of raw $\\sigma$ values rather than\n"
     "of midranks.  For a masked evaluator whose conditionals derive from a joint\n"
     "every entry of both blocks would be exactly zero by Eq.~\\eqref{eq:fbzero}.\n"
     "None is, and on \\FbBetweenNOpposite\\ of the \\FbBetweenNCompared\\ corpora\n"
     "the two masked evaluators give the upper block's median $\\sigma$ opposite\n"
     "signs.}",
     "159+160b+161+175 tab:fbbetween caption"),

    # ---- #164(b) + #175 (prose) + #162 ------------------------------------
    ("sec_truesigma.tex",
     "The between-set reading makes the same point more directly.  Scoring each\n"
     "text once in each direction, with nothing rearranged, the median $\\sigma$\n"
     "runs",
     "A second reading makes the same point more directly.  Call it the\n"
     "\\emph{unrearranged reading}: Eq.~\\eqref{eq:fb} evaluated as it stands, on\n"
     "the text in the arrangement it came in, with no permutation set behind it.\n"
     "Across cells the median $\\sigma$\nruns",
     "164b+175 true:258"),

    ("sec_truesigma.tex",
     "On\n\\FbBetweenNOpposite\\ of the \\FbBetweenNCompared\\ corpora the two do not\n"
     "agree on the sign.  The texts are identical; what differs is which masked evaluator\n"
     "computed $\\sigma$.  Equation~\\eqref{eq:fbzero} settles that before any corpus\n"
     "is scored, and this confirms it rather than establishing it.",
     "On\n\\FbBetweenNOpposite\\ of the \\FbBetweenNCompared\\ corpora the two give that\n"
     "median opposite signs.  The texts are identical; what differs is which masked\n"
     "evaluator computed $\\sigma$.  What Eq.~\\eqref{eq:fbzero} settles before any\n"
     "corpus is scored is that a non-zero reading belongs to the evaluator's\n"
     "incompatibility rather than to the text; a disagreement in sign on identical\n"
     "texts is one way that shows, and confirms it rather than establishing it.",
     "161+162 true:264"),

    # ---- #165 + #166 -------------------------------------------------------
    ("sec_truesigma.tex",
     "negative in \\FbBetweenNNegOfLLaDA\\ and \\FbBetweenNNegOfBertBase\\ corpora\n"
     "respectively --- the same side of zero as the within-text reading, and the\n"
     "same failure to reach significance.",
     "negative in \\FbBetweenNNegOfLLaDA\\ and \\FbBetweenNNegOfBertBase\\ corpora\n"
     "respectively.  Both readings therefore give the causal group's median less\n"
     "the non-causal group's the same sign, as a median over corpora: the causally\n"
     "labelled texts sit lower.  The two are not in the same units: the\n"
     "within-text reading is a difference of midranks ($\\FbCausalLLaDA$ and\n"
     "$\\FbCausalBertBase$, or $\\FbCausalStepsLLaDA$ and\n"
     "$\\FbCausalStepsBertBase$ grid steps), the unrearranged reading a difference\n"
     "of raw $\\sigma$.  The agreement is therefore one of direction and not of\n"
     "size, and neither reaches significance.",
     "165+166 true:272"),
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
            print(f"  skip  {label:<36} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                # A later batch rewrote this passage, so on a re-run neither
                # the old text nor this batch's own replacement is here.
                print(f"  pass  {label:<36} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<36} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<36} {name}")
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
    print("batch 18: Section 6.3, the unrearranged reading")
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
