#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Apply the terminology table: one object, one word.

Nine objects had between two and five names each.  The counts below were
measured on the text this was run against, not remembered, and every
replacement is written out rather than done by a blanket substitution,
because four of the nine words carry a second sense that has to survive:

    position   a token index (kept) vs a value's place in its set (midrank)
    step       the 1/n! quantum (kept) vs a stage of a construction (stage)
    ordering   discourse order (kept) vs a rank order
    set        a set of texts (kept) vs the n! arrangements of one text

Whitespace is collapsed before matching, because a two-word term that
happens to wrap across a line is invisible to a literal search -- which is
how "permutation construction" survived a rule naming it.

    python3 -I apply_terms.py .
"""
import io
import os
import re
import sys

FILES = ("main.tex", "sec_intro.tex", "sec_decomp.tex", "sec_truesigma.tex")

# (file or None for all, pattern, replacement, how many hits to require)
# A pattern matches across line breaks: \s+ stands for any run of whitespace.
EDITS = [
    # ---- 1. the arrangement a text is actually in ------------------------
    (None, r"authored\s+order", "authored arrangement", None),
    ("main.tex", r"the\s+\\emph\{authored\s+arrangement\}\s+of\s+a\s+text",
     r"the \\emph{authored arrangement} of a text", None),
    ("main.tex", r"distinguish\s+the\s+block\s+orders\s+at\s+all",
     "distinguish the arrangements at all", 1),
    ("sec_truesigma.tex", r"reversing\s+the\s+block\s+order\s+changes",
     "reversing the arrangement changes", 1),

    # ---- 2/3. midrank, and position kept for a token index ---------------
    ("main.tex", r"The\s+position\s+of\s+the\s+authored\s+arrangement\s+"
                 r"within\s+its\s+own\s+set",
     "The midrank of the authored arrangement within its own set", 1),
    ("main.tex", r"below\s+is\s+the\s+second\s+step,\s+the\s+position\s+of\s+"
                 r"\$\\Delta\(\\mathrm\{id\}\)\$\s+within\s+that\s+set",
     r"below is the second stage: where $\\Delta(\\mathrm{id})$ falls "
     r"within that set", 1),
    ("main.tex", r"give\s+the\s+position\s+of\s+the\s+authored\s+arrangement\s+"
                 r"among\s+all\s+orders",
     "give the midrank of the authored arrangement among all arrangements", 1),
    ("main.tex", r"the\s+median\s+position\s+of\s+the\s+texts\s+labelled",
     "the median midrank of the texts labelled", 1),
    ("sec_decomp.tex", r"its\s+authored\s+arrangement\s+has\s+a\s+position",
     "its authored arrangement has a midrank", 1),
    ("sec_decomp.tex", r"decomposes\s+the\s+median\s+position's\s+distance",
     "decomposes the median midrank's distance", 1),
    ("sec_truesigma.tex", r"read\s+as\s+the\s+position\s+of\s+the\s+authored\s+"
                          r"arrangement",
     "read as the midrank of the authored arrangement", 1),
    ("sec_truesigma.tex", r"The\s+authored\s+arrangement's\s+position\s+is\s+a\s+"
                          r"property",
     "The authored arrangement's midrank is a property", 1),
    ("sec_truesigma.tex", r"would\s+manufacture\s+a\s+percentile\s+out\s+of",
     "would manufacture a midrank out of", 1),

    # ---- 4. distance from the null, one name -----------------------------
    (None, r"displacement\s+tests", "distance-from-null tests", None),
    ("sec_truesigma.tex", r"\\texttt\{LLaDA\}'s\s+displacement\s+from\s+the\s+null",
     r"\\texttt{LLaDA}'s distance from the null", 1),

    # ---- 5. the grid step ------------------------------------------------
    ("sec_decomp.tex", r"grid\s+steps\s+---\s+the\s+same\s+quantum\s+this\s+"
                       r"section",
     "grid steps --- the same grid step this section", 1),

    # ---- 6. stage, for a step of a construction --------------------------
    ("main.tex", r"Two\s+steps\s+are\s+involved\s+and\s+they\s+are\s+not\s+the\s+"
                 r"same\s+step,",
     "Two stages are involved and they are not the same stage,", 1),
    ("main.tex", r"and\s+it\s+is\s+the\s+step\s+that\s+disposes\s+of\s+the\s+unit",
     "and it is the stage that disposes of the unit", 1),
    ("main.tex", r"Stopping\s+after\s+the\s+first\s+step\s+would\s+leave",
     "Stopping after the first stage would leave", 1),
    ("main.tex", r"and\s+in\s+two\s+separate\s+steps:\s+the\s+permutation\s+set",
     "and in two separate stages: the permutation set", 1),
    ("main.tex", r"Neither\s+step\s+answers\s+the\s+second\.",
     "Neither stage answers the second.", 1),
    ("sec_truesigma.tex", r"only\s+one\s+of\s+the\s+two\s+steps\s+of\s+"
                          r"Section~\\ref\{sec:blkord\}\s+carries\s+over",
     r"only one of the two stages of Section~\\ref{sec:blkord} carries over",
     1),
    ("sec_truesigma.tex", r"What\s+survives\s+is\s+the\s+second\s+step\.",
     "What survives is the second stage.", 1),

    # ---- 7/8. arrangement, and the permutation set -----------------------
    ("main.tex", r"within\\emph\{\}", "within", 0),   # no-op guard
    ("main.tex", r"across\s+its\s+permutations\.",
     "across its arrangements.", 1),
    ("main.tex", r"cancels\s+between\s+the\s+permutations\s+of\s+one\s+text",
     "cancels between the arrangements of one text", 1),
    ("sec_truesigma.tex", r"in\s+each\s+direction,\s+without\s+permutations,",
     "in each direction, without rearranging,", 1),
    ("sec_decomp.tex", r"the\s+top\s+of\s+its\s+own\s+permutation\s+range",
     "the top of its own permutation set", 1),
    ("sec_decomp.tex", r"would\s+be\s+ranked\s+as\s+an\s+ordering",
     "would be ranked as though ordered", 1),

    # ---- 9. the two label groups -----------------------------------------
    (None, r"the\s+two\s+sets\s+differ", "the two label groups differ", None),
    ("main.tex", r"topic\s+differences\s+that\s+separate\s+the\s+two\s+sets",
     "topic differences that separate the two label groups", 1),
    ("sec_intro.tex", r"within\s+texts\s+\(the\s+authored\s+arrangement's\s+rank\s+"
                      r"among\s+the\s+\$n!\$\)\s+and\s+between\s+the\s+two\s+sets",
     r"within texts (the authored arrangement's rank among the $n!$) and "
     r"between the two label groups", 1),
    ("sec_intro.tex", r"absence\s+of\s+any\s+criterion\s+defining\s+the\s+two\s+"
                      r"sets",
     "absence of any criterion defining the two label groups", 1),
    ("sec_truesigma.tex", r"and\s+the\s+two\s+sets\s+have\s+no\s+criterion",
     "and the two label groups have no criterion", 1),
]


def main(root):
    os.chdir(root)
    total = 0
    for fname, pat, rep, want in EDITS:
        targets = FILES if fname is None else (fname,)
        hits = 0
        for t in targets:
            s = io.open(t, encoding="utf-8").read()
            new, n = re.subn(pat, rep, s)
            if n:
                io.open(t, "w", encoding="utf-8").write(new)
            hits += n
        if want is not None and hits != want:
            print(f"  !! {pat[:52]} -> {hits} hits, expected {want}")
        elif hits:
            print(f"  {hits:>3}  {rep[:62]}")
        total += hits
    print(f"\n{total} replacements")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
