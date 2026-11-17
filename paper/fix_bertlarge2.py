r"""A removal that was decided and half done.

tables/macros.tex declares \ParamsBertLarge RETIRED.  The decision to keep
\texttt{bert-large} out of this paper was taken, the number was retired,
and the name stayed behind in one sentence of Section 3.2 -- where it then
needed a clause explaining that it appears nowhere else, which was both
circular and false of the sentence containing it.

Reading it, the question was the right one: why is this model not in the
Section 3.1 table?  Because the paper reports nothing from it.  Then it
does not belong in the prose either, and the same paragraph already ends
with the record that does belong:

    Those measurements are retained in the repository and are not reported
    here.

The count stays, because "three" says the substitution was tried more
widely than on the two evaluators the paper keeps.  Which three is a
question the repository answers.

This REPLACES fix_bertlarge.py, which named all three and went the wrong
way.  It applies whether or not that one was run.

Run:  python fix_bertlarge2.py <paper dir>
"""
import io
import os
import re
import sys

os.chdir(sys.argv[1])
N = 0
WROTE = []

BEFORE_FIX = r"""exactly that, for three
masked evaluators --- the two this paper reports and \texttt{bert-large},
which appears nowhere else because nothing it produced is reported.  We
concluded that the comparison with the autoregressive readings means
nothing."""

AFTER_FIX = r"""exactly that, for \texttt{bert-base}, \texttt{LLaDA} and
\texttt{bert-large}, and concluded that the comparison with the
autoregressive readings means nothing.  The $\sigma$ measurements below use
\texttt{bert-base} and \texttt{LLaDA}; \texttt{bert-large} is named here
only so the record of what was withdrawn is complete, and no number from it
appears in this paper."""

REPLACEMENT = r"""exactly that, for three masked evaluators, and concluded that the
comparison with the autoregressive readings means nothing."""


def rep_alt(path, alts, b, label, marker):
    """Like rep(), but the file may be in either of two prior states."""
    global N
    s = io.open(path, encoding="utf-8").read()
    if marker in s:
        print(f"  (already) {label}")
        return
    hits = [a for a in alts if s.count(a) == 1]
    assert len(hits) == 1, (
        f"{label}: {len(hits)} of {len(alts)} candidate texts matched once; "
        "the file is in neither expected state")
    io.open(path, "w", encoding="utf-8").write(s.replace(hits[0], b))
    WROTE.append((label, b))
    print(f"  {label}"
          + ("  [fix_bertlarge.py had been applied]"
             if hits[0] is AFTER_FIX else ""))
    N += 1


rep_alt("main.tex",
        [BEFORE_FIX, AFTER_FIX],
        REPLACEMENT,
        "the name goes where the number already went",
        marker="exactly that, for three masked evaluators, and concluded")

SUSPECT = re.compile(
    r"\bthe ones?\s*(?=[.,;:]|\b(?:that|which|it|we|they|the|is|are)\b)|"
    r"\b(?:that kind|this kind|a kind|that form|this form|"
    r"of that|of this|the thing|in this sense|this reading|the other one|"
    r"such a|that of|need not\b(?!\s+\w)|does not\.|do not\.|cannot\.|"
    r"\bis of the\b|\bis of a\b|\band not of\b|\bbut not of\b)", re.I)
bad = [(lab, m.group(0)) for lab, b in WROTE for m in SUSPECT.finditer(b)]
if bad:
    print("\n  !! replacement text contains new pointing constructions:")
    for lab, hit in bad:
        print("     %-40s %r" % (lab, hit))
    raise SystemExit("fix the replacements before shipping this patch")
print(f"done: {N} edits (replacement text clean)")
