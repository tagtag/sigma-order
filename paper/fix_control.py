r"""Why the shuffle control is empty, said in full.

    "such a comparison can only restate $\Delta(\mathrm{id}) > 0$, which is
     already known."

Written as a proposition, $\Delta(\mathrm{id}) > 0$ reads as something the
construction guarantees.  It is not.  The antisymmetry fixes the SET
$\{\Delta(\pi)\}$ symmetric about zero; it fixes no sign for any particular
$\Delta(\mathrm{id})$, which is an empirical value and could be either way.

And "already known" never says known from what.  A reader is left choosing
between "guaranteed a priori", which is false, and "visible in the measured
values", which is true and unstated.  Asked about it, the reader took the
first, which is the only reading the sentence offers evidence for.

The argument in full: with $\pi$ drawn uniformly, $\mathbb{E}[\Delta(\pi)]
= 0$ exactly, by Eq. (antisym) and for any model and any text.  The shuffle
arm therefore contributes a zero and some noise, and the test collapses to
asking whether $\Delta(\mathrm{id})$ sits above zero -- which the
$\Delta(\mathrm{id})$ values answer by themselves, with no permutations
run at all.  That is what makes it empty, and it is also the contrast the
next sentence needs: the midrank reads $\Delta(\mathrm{id})$ against the
whole set, and a rank is not determined by a sign.

AND THE STATUS, which is where the two sentences disagreed.  Section 4.2
owns this question and answers it the other way round: the antisymmetry
pairs the values {d, -d}, so half of any text's arrangements are negative
and "nothing distinguishes the sign of the authored one in advance.  That
it comes out positive here is a measurement."  As a fact "already known"
was true -- the sign is stable, differing between the ends of the ladder in
0 of 5 corpora -- but the two sentences told a reader opposite things about
whether the proposition was given or measured.  The cross-reference makes
them agree in the text as well as in the data.

Apply fix_methods.py first; this is written against the sentence as that
patch leaves it.

Run:  python fix_control.py <paper dir>
"""
import io
import os
import re
import sys

os.chdir(sys.argv[1])
N = 0
WROTE = []


def rep(path, a, b, label, marker=None):
    global N
    assert a not in b or marker, f"{label}: b contains a; pass a marker"
    s = io.open(path, encoding="utf-8").read()
    if marker is not None:
        if marker in s:
            print(f"  (already) {label}")
            return
    elif s.count(a) == 0 and s.count(b) >= 1:
        print(f"  (already) {label}")
        return
    assert s.count(a) == 1, f"{label}: {s.count(a)} in {path}"
    io.open(path, "w", encoding="utf-8").write(s.replace(a, b))
    WROTE.append((label, b))
    print(f"  {label}")
    N += 1


rep("main.tex",
    r"""first.  Comparing the authored arrangement against a shuffled one compares it against
the \emph{centre} of a symmetric set, which is zero by construction; such a
comparison can only restate $\Delta(\mathrm{id}) > 0$, which is already
known.  We ran it before noticing the antisymmetry, obtained a large effect
size and a very
small $p$, and retracted it;""",
    r"""first.  Comparing the authored arrangement against a shuffled one compares
it against the \emph{centre} of a symmetric set, and with $\pi$ drawn
uniformly Eq.~\eqref{eq:antisym} puts that centre at zero exactly, for any
model and any text.  The shuffle arm therefore supplies a zero and some
noise, and the test collapses to asking whether $\Delta(\mathrm{id})$ sits
above zero.  The measured values of $\Delta(\mathrm{id})$ answer that by
themselves, with no permutations run at all, and what they answer is a
measurement and not a property of the construction
(Section~\ref{sec:capacity}).  We ran it before noticing the
antisymmetry, obtained a large effect size and a very small $p$, and
retracted it;""",
    "the shuffle arm is a zero, and the sign was never in the construction")

SUSPECT = re.compile(
    r"\bthe ones?\s*(?=[.,;:]|\b(?:that|which|it|we|they|the|is|are)\b)|"
    r"\bof (?:that|this)\s*(?=[.,;:]|\b(?:is|are|was|were|and|or|we|it|they)\b)|"
    r"\b(?:that kind|this kind|a kind|that form|this form|"
    r"the thing|in this sense|this reading|the other one|"
    r"such a|that of|need not\b(?!\s+\w)|does not\.|do not\.|cannot\.|"
    r"\bis of the\b|\bis of a\b|\band not of\b|\bbut not of\b)", re.I)
bad = [(lab, m.group(0)) for lab, b in WROTE for m in SUSPECT.finditer(b)]
if bad:
    print("\n  !! replacement text contains new pointing constructions:")
    for lab, hit in bad:
        print("     %-40s %r" % (lab, hit))
    raise SystemExit("fix the replacements before shipping this patch")
print(f"done: {N} edits (replacement text clean)")
