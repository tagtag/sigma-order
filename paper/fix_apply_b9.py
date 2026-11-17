#!/usr/bin/env python3
"""Batch 9: Sections 3.3 and 3.4 -- #76 #77 #78 #79 #80 #81 #82 #85 #86 #88.

  #76  Equations (pair) and (antisym) are written for an arbitrary score S,
        so the quantity they define is not Eq.(1)'s Delta unless S is log P
        from one joint -- which Section 3.2 has just said a masked model
        does not supply.  Writing Delta_S for the general case removes the
        contradiction and leaves Delta for Eq.(1).
  #77  "come in pairs {d, -d}" -- define d.
  #78  "the control we reached for first" is not named, and the sentence
        that follows reports running and retracting it.  Name it (the
        shuffle control) and drop the account of having run it.
  #79  "A score that cannot distinguish the arrangements at all" -- say it
        in terms of S.
  #80  "They are also the same material, which is why the design controls
        what a comparison between two corpora cannot control" -- open out
        what is controlled.
  #81  "a comparison between two corpora" -- corpus is reserved for the
        five scored corpora; this contrast is between the two label groups.
  #82  Eq.(rb) gives n1 and n2 as "the group sizes" without their values.
  #85  The authored arrangement is the identity arrangement, which is a
        statement about the text and not about any score, so Section 6.2
        can score the same arrangement under sigma.
  #86  "with the two labels exchanged" -- name them.
  #88  The AR ladder's abbreviation is introduced in the abstract only.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b9.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #76 + #77 --------------------------------------------------------
    ("main.tex",
     "Writing the definition out at both members of that pair, for any score $S$ ---\n"
     "the evaluator's score of Section~\\ref{sec:scope}, or any other function of a\n"
     "token sequence ---\n"
     "\\begin{equation}\n"
     "\\Delta(\\pi) = \\frac{S(x_\\pi) - S(x_{\\pi\\circ\\mathrm{rev}})}{L},\n"
     "\\qquad\n"
     "\\Delta(\\pi\\circ\\mathrm{rev})\n"
     "  = \\frac{S(x_{\\pi\\circ\\mathrm{rev}}) - S(x_\\pi)}{L} ,\n"
     "\\label{eq:pair}\n"
     "\\end{equation}\n"
     "which are the same two numbers subtracted in the opposite order.  The two\n"
     "lines of Eq.~\\eqref{eq:pair} therefore give\n"
     "\\begin{equation}\n"
     "\\Delta(\\pi) \\;=\\; -\\,\\Delta(\\pi\\circ\\mathrm{rev}).\n"
     "\\label{eq:antisym}\n"
     "\\end{equation}",
     "Writing the definition out at both members of that pair, for any score $S$ ---\n"
     "the evaluator's score of Section~\\ref{sec:scope}, or any other function of a\n"
     "token sequence ---\n"
     "\\begin{equation}\n"
     "\\Delta_S(\\pi) = \\frac{S(x_\\pi) - S(x_{\\pi\\circ\\mathrm{rev}})}{L},\n"
     "\\qquad\n"
     "\\Delta_S(\\pi\\circ\\mathrm{rev})\n"
     "  = \\frac{S(x_{\\pi\\circ\\mathrm{rev}}) - S(x_\\pi)}{L} ,\n"
     "\\label{eq:pair}\n"
     "\\end{equation}\n"
     "which are the same two numbers subtracted in the opposite order.  The two\n"
     "lines of Eq.~\\eqref{eq:pair} therefore give\n"
     "\\begin{equation}\n"
     "\\Delta_S(\\pi) \\;=\\; -\\,\\Delta_S(\\pi\\circ\\mathrm{rev}).\n"
     "\\label{eq:antisym}\n"
     "\\end{equation}\n"
     "When $S$ is the exact $\\log P$ of one joint distribution --- which\n"
     "Section~\\ref{sec:scope} says is available for an autoregressive evaluator\n"
     "and for no other kind --- $\\Delta_S$ is the $\\Delta$ of\n"
     "Eq.~\\eqref{eq:delta}, and the two are written interchangeably from here on.",
     "76 eq:pair/antisym"),

    ("main.tex",
     "Nothing in this depends on what $S$ is.  It need not be a log-probability, need\n"
     "not be normalised, and need not come from a consistent joint distribution: it\n"
     "need only return a number for a token sequence.  The $n!$ values of $\\Delta$\n"
     "thus come in pairs $\\{d, -d\\}$ for any evaluator whatever.",
     "Nothing in this depends on what $S$ is.  It need not be a log-probability, need\n"
     "not be normalised, and need not derive from a consistent joint distribution: it\n"
     "need only return a number for a token sequence.  The $n!$ values of $\\Delta_S$\n"
     "thus come in pairs: writing $d = \\Delta_S(\\pi)$, the partner arrangement\n"
     "$\\pi\\circ\\mathrm{rev}$ contributes $-d$, for any evaluator whatever.",
     "77 main:811"),

    ("main.tex",
     "Since $\\pi \\mapsto \\pi\\circ\\mathrm{rev}$ is a measure-preserving involution on\n"
     "the symmetric group, the distribution of $\\Delta$ over a uniformly drawn $\\pi$",
     "Since $\\pi \\mapsto \\pi\\circ\\mathrm{rev}$ is a measure-preserving involution on\n"
     "the symmetric group, the distribution of $\\Delta_S$ over a uniformly drawn $\\pi$",
     "76 main:813"),

    ("main.tex",
     "set $\\{\\Delta(\\pi)\\}$ is centred at zero by construction.",
     "set $\\{\\Delta_S(\\pi)\\}$ is centred at zero by construction.",
     "76 main:818"),

    ("main.tex",
     "text and the values $\\Delta(\\pi)$ they produce; it creates a reference where",
     "text and the values $\\Delta_S(\\pi)$ they produce; it creates a reference where",
     "76 main:823"),

    # ---- #78 ---------------------------------------------------------------
    ("main.tex",
     "Equation~\\eqref{eq:antisym} also disqualifies the control we reached for\n"
     "first.  Comparing the authored arrangement against a shuffled one compares",
     "Equation~\\eqref{eq:antisym} also disqualifies the obvious control, which is\n"
     "to compare the authored arrangement against a shuffled one.  That compares",
     "78a main:834"),

    ("main.tex",
     "(Section~\\ref{sec:capacity}).  We ran it before noticing the\n"
     "antisymmetry, obtained a large effect size and a very small $p$, and\n"
     "retracted it; the antisymmetry above is what makes the\n"
     "result empty, and it does so whatever the model or the text.  What is not forced",
     "(Section~\\ref{sec:capacity}).  The antisymmetry is what makes that control\n"
     "empty, and it does so whatever the model or the text.  What is not forced",
     "78b main:842"),

    # ---- #79 ---------------------------------------------------------------
    ("main.tex",
     "A\nscore that cannot distinguish the arrangements at all gives $\\Delta(\\pi) = 0$ for every $\\pi$, and a count of",
     "A\nscore that returns the same number for every arrangement of one text ---\n"
     "$S(x_\\pi)$ independent of $\\pi$ --- gives $\\Delta_S(\\pi) = 0$ for every\n"
     "$\\pi$.  A count of",
     "79 main:852"),

    # ---- #80 + #81 ---------------------------------------------------------
    ("main.tex",
     "They are also the same material, which\nis why the design controls what a comparison between two corpora cannot\ncontrol.",
     "They are also the same material: length, vocabulary, style and topic are held\n"
     "fixed across the arrangements of one text, which a comparison between the two\n"
     "label groups cannot do, since those are different texts.",
     "80+81 main:877"),

    # ---- #82 ---------------------------------------------------------------
    ("main.tex",
     "with $U$ the Mann--Whitney statistic and $n_1, n_2$ the group sizes, so that",
     "with $U$ the Mann--Whitney statistic and $n_1, n_2$ the group sizes --- here\n"
     "$n_1 = n_2 = \\NPerGroup$ texts per label group in each corpus\n"
     "\\cite{sagawa2026} --- so that",
     "82 eq:rb"),

    # ---- #85 ---------------------------------------------------------------
    ("main.tex",
     "One term has to be fixed before the equations.  The \\emph{authored arrangement} of a\n"
     "text is the arrangement that text is actually in, the one scored as\n"
     "$\\Delta(\\mathrm{id})$.",
     "One term has to be fixed before the equations.  The \\emph{authored arrangement} of a\n"
     "text is the arrangement that text is actually in: the identity arrangement\n"
     "$\\mathrm{id}$ of its $n$ blocks, scored here as $\\Delta(\\mathrm{id})$.  It is\n"
     "a property of the text and not of any score, which is why\n"
     "Section~\\ref{sec:fbrank} can score the same arrangement under $\\sigma$.",
     "85 main:892"),

    # ---- #86 ---------------------------------------------------------------
    ("main.tex",
     "selecting the causal group instead is a different measurement: with the\ntwo labels\nexchanged,",
     "selecting the causal group instead is a different measurement: with the\n"
     "causal and non-causal labels exchanged,",
     "86 main:919"),
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
    print("batch 9: Sections 3.3 and 3.4")
    print("-" * 56)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 56)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 56)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
