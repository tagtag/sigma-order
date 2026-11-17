r"""The eighth read: the last family, which is not a reversal word.

Six rounds of scanning were organised around the vocabulary of reversal.
What survived is a different type -- naming Ref. [1]'s quantity with a
definite article, so that the sentence asserts WHICH quantity the
thermodynamic reading means.  Section 2.2 p.7 withdrew exactly that, and
left "an entropy production with a zero on a single text".

 1. Section 6.1, the one the reader marks.  "The quantity Sagawa names is,
    for the evaluators Sagawa uses, simultaneously trivial and unevaluable"
    collides head-on with Section 1 First, which concedes that the backward
    term of Ref. [1] is obtained by re-indexing, is available to an
    autoregressive model, and is computed there on GPT-2.  What is trivial
    and unevaluable for those evaluators is sigma, not Ref. [1]'s quantity.
    Calling sigma "the quantity Sagawa names" is the definite article again.
    It is also the only place in the paper where an author's name appears
    outside the bibliography, twice, in a critical sentence.

 2. Section 7's close, "the entropy production itself", same type.

 6. The Section 6 title, "Results III: the entropy production itself".
    NOT on the reader's list -- the scan word reaches it and the report does
    not name it.  Same defect, more prominent, and the section's own opening
    already carries the limited claim ("a comparison that has one").
    Revert by restoring the one line if this goes too far.

Two of precision, not of type:

 4. Section 7, "so not even the average is available here", one clause
    before citing Fig. 4 of Ref. [1] -- which plots that average.  What is
    unavailable is the theorem about it.

 3. The comparison table, "one sequence against two assembly orders",
    a preposition left from "against its own reverse".  Section 2.2's
    naming paragraph and Section 1 both read "under".

 5. Section 6.1's "The backward term", two pages after Section 1 First used
    the same phrase for Ref. [1]'s, which IS available.  One clause fixes it.

Run:  python fix_coldread_h.py <paper dir>
"""
import io
import os
import sys

os.chdir(sys.argv[1])
N = 0


def rep(path, a, b, label, marker=None):
    """marker: text unique to the result, required when b still contains a."""
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
    print(f"  {label}")
    N += 1


# =================================================== 1: the flagged sentence
rep("sec_truesigma.tex",
    r"""and an autoregressive model's is not.  The
quantity Sagawa names is, for the evaluators Sagawa uses, simultaneously
trivial and unevaluable.  That explains the substitution of $\Delta$ for
$\sigma$; it does not license it.""",
    r"""and an autoregressive model's is not.  So
$\sigma$ is, for the evaluators Ref.~\cite{sagawa2026} uses, simultaneously
trivial and unevaluable.  That explains the substitution of $\Delta$ for
$\sigma$; it does not license reading $\Delta$ as $\sigma$.""",
    "1: sigma is named as sigma, and the author's name leaves the prose")

# ======================================================= 2: Section 7's close
rep("main.tex",
    r"""a substitute score: what a masked model supplies instead is the entropy
production itself (Section~\ref{sec:fbdef}), and what that reports is the""",
    r"""a substitute score: what a masked model supplies instead is a comparison
with a zero on the text it is read from (Section~\ref{sec:fbdef}), and what
that reports is the""",
    "2: the close keeps the limit Section 2.2 p.7 set")

# ======================================================= 3: the table's verb
rep("main.tex",
    r"""                    & one sequence against
                      two assembly orders \\""",
    r"""                    & one sequence under
                      two assembly orders \\""",
    "3: under, as in Section 2.2's naming paragraph and Section 1")

# ============================================= 4: what is unavailable is the
#                                                  theorem, not the average
rep("main.tex",
    r"""so not even the average is available here, and Ref.~\cite{sagawa2026} states
for that case that the averages are not guaranteed to be non-negative.""",
    r"""so the theorem does not reach the average here either, and
Ref.~\cite{sagawa2026} states for that case that the averages are not
guaranteed to be non-negative.""",
    "4: Ref. [1] plots that average in Fig. 4; the theorem is what stops")

# ====================================== 5: which backward term, two pages on
rep("sec_truesigma.tex",
    r"""being exact about why, because the two available answers are different.  The
backward term is $\log P_{\mathrm{r2l}}(x)$, and each of its factors""",
    r"""being exact about why, because the two available answers are different.  The
backward term of Eq.~\eqref{eq:fb} is $\log P_{\mathrm{r2l}}(x)$, and each of
its factors""",
    "5: Section 1 First used the same phrase for Ref. [1]'s, which is available")

# ===================================== 6: NOT on the reader's list -- the
#                                          title is the same defect, louder.
#  To revert: restore \section{Results III: the entropy production itself}
rep("sec_truesigma.tex",
    r"""\section{Results III: the entropy production itself}""",
    r"""\section{Results III: $\sigma$, on masked evaluators}""",
    "6: the section title states what is measured and claims nothing")

print(f"done: {N} edits")
