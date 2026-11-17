#!/usr/bin/env python3
"""Prove that check_paper.py catches each defect it claims to catch.

A checker that silently stops catching something is worse than no checker,
because the build still goes green.  So every class of defect this project
actually shipped is reconstructed here in a minimal document, and the check
must fail on it and pass on the repaired version.

    python3 -I check_paper_selftest.py

No LaTeX, no data, under a second.
"""

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKER = os.path.join(HERE, "check_paper.py")

GOOD_TEX = r"""
\documentclass{article}
\newcommand{\sigblock}{\sigma_{\mathrm{block}}}
\newcommand{\sigtok}{\sigma_{\mathrm{token}}}
\input{tables/macros}
\begin{document}
We measure $\sigblock$ and, for completeness, $\sigtok$.
The evaluators are masked language models \cite{bert}.
\begin{center}
\begin{tabular}{llll}
model & parameters & direction & role \\
\texttt{bert-base-uncased} & 110\,M & masked & $\sigma$ \\
\end{tabular}
\end{center}
The median is \MedPct, as Table~\ref{tab:one} and Figure~\ref{fig:one} show.
\begin{table}[t]
\input{tables/tab_one}
\caption{A table.}
\label{tab:one}
\end{table}
\begin{figure}[t]
\includegraphics{fig_one.pdf}
\caption{A figure.}
\label{fig:one}
\end{figure}
\begin{thebibliography}{9}
\bibitem{bert} A reference.
\end{thebibliography}
\end{document}
"""

MACROS = r"\newcommand{\MedPct}{0.50}" + "\n"
TAB_ONE = ("\\begin{tabular}{rr}\n"
           "$\\sigma_{\\mathrm{block}}$ & $\\sigma_{\\mathrm{token}}$ \\\\\n"
           "0.1 & 0.2 \\\\\n\\end{tabular}\n")


def build(tmp, tex=GOOD_TEX, macros=MACROS, tab=TAB_ONE, glossary=None,
          figure=True):
    root = tempfile.mkdtemp(dir=tmp)
    os.makedirs(os.path.join(root, "tables"))
    os.makedirs(os.path.join(root, "figures"))
    open(os.path.join(root, "main.tex"), "w").write(tex)
    open(os.path.join(root, "tables", "macros.tex"), "w").write(macros)
    open(os.path.join(root, "tables", "tab_one.tex"), "w").write(tab)
    if figure:
        open(os.path.join(root, "figures", "fig_one.pdf"), "w").write("%PDF")
    if glossary is not None:
        open(os.path.join(root, "glossary.txt"), "w").write(glossary)
    return root


def run(root):
    r = subprocess.run(
        [sys.executable, "-I", CHECKER, "--tex", os.path.join(root, "main.tex"),
         "--tables", os.path.join(root, "tables"),
         # these fixtures have no built PDF; the float check must then warn
         # and step aside rather than fail, or every case below fails for the
         # wrong reason
         "--pdf", "no-such.pdf"],
        capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def expect_pass(root, what):
    code, out = run(root)
    if code != 0:
        print(out)
        raise SystemExit(f"FAILED: {what} should pass and did not")
    print(f"  pass: {what}")


def expect_fail(root, what, needle):
    code, out = run(root)
    if code == 0:
        print(out)
        raise SystemExit(f"FAILED: {what} should fail and did not")
    if needle not in out:
        print(out)
        raise SystemExit(f"FAILED: {what} failed without mentioning {needle!r}")
    print(f"  catch: {what}")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        print("check_paper selftest")

        # the repaired document, which every defect below is a mutation of
        expect_pass(build(tmp), "a document with nothing wrong")

        # 1. a reference nothing cites.  thebibliography prints it regardless,
        #    so the PDF's reference list looks complete.
        expect_fail(build(tmp, tex=GOOD_TEX.replace(r"\cite{bert}", "")),
                    "a reference nothing cites", "bibliography")

        # 2. a citation with no entry
        expect_fail(build(tmp, tex=GOOD_TEX.replace(
                        r"\bibitem{bert} A reference.", "")),
                    "a citation with no entry", "bibliography")

        # 3. a float the text never points at.  It still appears in the PDF.
        expect_fail(build(tmp, tex=GOOD_TEX.replace(
                        r"Table~\ref{tab:one} and ", "")),
                    "a table nothing references", "never referenced")
        expect_fail(build(tmp, tex=GOOD_TEX.replace(
                        r" and Figure~\ref{fig:one}", "")),
                    "a figure nothing references", "never referenced")

        # 4. a quantity the prose names and no table reports -- the sigma_token
        #    case: the sentence promising it reads perfectly well alone.
        expect_fail(build(tmp, tab=TAB_ONE.replace(
                        r"$\sigma_{\mathrm{token}}$", "x")),
                    "a named quantity no table reports", "quantities")

        # 4b. and the exemption, written down in the source, lets it through
        expect_pass(build(tmp,
                          tex=GOOD_TEX.replace(
                              r"\newcommand{\sigtok}{\sigma_{\mathrm{token}}}",
                              "\\newcommand{\\sigtok}{\\sigma_{\\mathrm{token}}}"
                              "\n% check_paper: \\sigtok reported in Figure 2"),
                          tab=TAB_ONE.replace(r"$\sigma_{\mathrm{token}}$", "x")),
                    "the same, with the exemption declared")

        # 5. an unresolved number
        expect_fail(build(tmp, macros=r"\newcommand{\MedPct}{[TODO:MedPct]}"),
                    "a TODO left in a generated macro", "TODO")

        # 6. a stub table standing in for a missing measurement
        expect_fail(build(tmp, tab="no measurements for this table\n"),
                    "a stub table", "stub")

        # 7. a file the document includes and does not have
        expect_fail(build(tmp, figure=False),
                    "a missing figure file", "does not exist")

        # 8. a macro the prose uses and nothing defines
        expect_fail(build(tmp, macros="% empty\n"),
                    "a macro nothing defines", "nothing defines it")

        # 9. no built PDF: the float check steps aside with a warning
        code, out = run(build(tmp))
        assert code == 0 and "not built" in out, \
            "a missing PDF should warn, not fail"
        print("  pass: a missing PDF skips the float check")

        # 10. a banned near-synonym, reintroduced
        gl = "masked language model | bidirectional model\n"
        expect_pass(build(tmp, glossary=gl), "prose that keeps to the glossary")
        expect_fail(build(tmp, glossary=gl,
                          tex=GOOD_TEX.replace("masked language models",
                                               "bidirectional models")),
                    "a banned near-synonym", "glossary")

    print("check_paper selftest: OK -- every defect class is caught")


if __name__ == "__main__":
    main()


def check_self_reference_rule():
    """A section citing itself is a reference to its neighbour.

    Section 5.4 wrote "the cell tests of Section 5.4 are corrected over
    25" while contrasting them with its own correlations; the cell tests
    are Section 5.3's and the rendered number looked plausible.
    """
    import os, sys, tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_paper as C

    d = tempfile.mkdtemp()
    bad = os.path.join(d, "bad.tex")
    with open(bad, "w") as f:
        f.write("\\subsection{A}\n\\label{sec:aa}\n"
                "text text\n"
                "\\subsection{B}\n\\label{sec:bb}\n"
                "the cell tests of Section~\\ref{sec:bb} are corrected\n")
    del C.WARN[:]
    C.check_self_reference([bad])
    msgs = [m for _, m in C.WARN]
    assert msgs and "sec:bb" in msgs[0], msgs

    good = os.path.join(d, "good.tex")
    with open(good, "w") as f:
        f.write("\\subsection{A}\n\\label{sec:aa}\n"
                "text text\n"
                "\\subsection{B}\n\\label{sec:bb}\n"
                "the cell tests of Section~\\ref{sec:aa} are corrected\n")
    del C.WARN[:]
    C.check_self_reference([good])
    assert not C.WARN, [m for _, m in C.WARN]

    # a caption naming its own section is ordinary and must not warn
    cap = os.path.join(d, "cap.tex")
    with open(cap, "w") as f:
        f.write("\\subsection{B}\n\\label{sec:bb}\n"
                "\\caption{the series Section~\\ref{sec:bb} reads}\n")
    del C.WARN[:]
    C.check_self_reference([cap])
    assert not C.WARN, [m for _, m in C.WARN]
    print("  warn: a section that cites itself, captions exempt")


def check_dtok_scope_rule():
    """The token quantity must stay in the section that sets it aside."""
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_paper as C
    good = r"""Both are written $\Dtok$ and $\Dblock$ here.
\section{Methods}
The component is $\Delta$ throughout."""
    bad = r"""Both are written $\Dtok$ and $\Dblock$ here.
\section{Methods}
The component is $\Dtok$ throughout."""
    del C.FAIL[:]
    C.check_dtok_scope(good)
    assert not C.FAIL, [m for _, m in C.FAIL]
    del C.FAIL[:]
    C.check_dtok_scope(bad)
    msgs = [m for _, m in C.FAIL]
    assert msgs and "Dtok" in msgs[0], msgs
    print("  catch: the token quantity used after it was set aside")


def check_param_spelling_rule():
    """One model may not be printed with two parameter counts.

    tab_saturation used p//1000 and printed gpt2-xl as 1B where every
    other table printed 1.6B.  One quantity, two formatters.
    """
    import os, sys, tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_paper as C

    d = tempfile.mkdtemp()
    with open(os.path.join(d, "tab_a.tex"), "w") as f:
        f.write("gpt2-xl & AR & 1.6B & $+0.396$ \\\\\n")
    with open(os.path.join(d, "tab_b.tex"), "w") as f:
        f.write("gpt2-xl & AR & 1B & 40\\% \\\\\n")
    del C.FAIL[:]
    C.check_param_strings(d)
    bad = [m for _, m in C.FAIL]
    assert bad and "gpt2-xl" in bad[0], bad

    # and agreement is not flagged
    with open(os.path.join(d, "tab_b.tex"), "w") as f:
        f.write("gpt2-xl & AR & 1.6B & 40\\% \\\\\n")
    del C.FAIL[:]
    C.check_param_strings(d)
    assert not C.FAIL, [m for _, m in C.FAIL]
    print("  catch: one model printed with two parameter counts")


def check_trend_verb_rule():
    """A non-significant correlation must not be given a verb.

    Both directions are errors and the paper made both in one paragraph:
    "rises" for p = 0.058 and "does not vary" for p = 0.559.  The rule has
    to catch the second as readily as the first, because an absence
    asserted from a failure to reject reads like a finding.
    """
    import os, re, sys, tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_paper as C

    d = tempfile.mkdtemp()
    with open(os.path.join(d, "macros.tex"), "w") as f:
        f.write(r"\newcommand{\TailTrendRho}{+0.90}" "\n"
                r"\newcommand{\TailTrendP}{0.083}" "\n"
                r"\newcommand{\TrendCeilP}{0.033}" "\n"
                r"\newcommand{\TrendCeilRho}{+0.97}" "\n"
                r"\newcommand{\TrendCausalP}{0.559}" "\n"
                r"\newcommand{\TrendCausalRho}{-0.35}" "\n"
                r"\newcommand{\TrendAuthoredP}{0.200}" "\n"
                r"\newcommand{\TrendAuthoredRho}{+0.87}" "\n"
                r"\newcommand{\ShareFormRho}{+0.30}" "\n"
                r"\newcommand{\ShareFormP}{0.683}" "\n")

    def run(src):
        del C.FAIL[:]
        C.check_trend_verbs(src, d)
        return [m for _, m in C.FAIL]

    # the significant one may have a verb
    assert not run(r"The fraction rises with capacity ($\rho = "
                   r"\TrendCeilRho$, $p = \TrendCeilP$)."), "false positive"
    # asserting an effect that is not significant
    bad = run(r"The authored component rises in midrank units, $\rho = "
              r"\TrendAuthoredRho$ ($p = \TrendAuthoredP$).")
    assert bad and "rises" in bad[0], bad
    # asserting an absence from a failure to reject
    bad = run(r"It does not vary with capacity ($\rho = \TrendCausalRho$, "
              r"$p = \TrendCausalP$).")
    assert bad and "does not vary" in bad[0], bad
    # a level statement in the same sentence is fine
    assert not run(r"It is one or two grid steps at every rung ($\rho = "
                   r"\TrendCausalRho$, $p = \TrendCausalP$)."), \
        "a level must not be flagged"
    # and a word that merely CONTAINS a verb is not one.  "characterised"
    # contains "rise"; matching by substring reported five sentences that
    # say "establishes no trend" as though they claimed one, and the single
    # true positive in that batch was nearly thrown out with them.
    assert not run(r"The sets were never characterised ($\rho = "
                   r"\TrendCausalRho$, $p = \TrendCausalP$)."), \
        "'characterised' is not 'rise'"
    # The same error about a relation between two series.  Section 5.3 and
    # the Table 2 caption both read rho = +0.30 at p = 0.68 over five
    # evaluators as "the two forms do not track each other", and Section
    # 6.1 said it of a second pair -- an absence asserted three times from
    # two correlations that establish nothing either way.
    bad = run(r"The two forms do not track each other ($\rho = "
              r"\ShareFormRho$, $p = \ShareFormP$).")
    assert bad and "do not track" in bad[0], bad
    # but naming the question without answering it is what replaced them
    assert not run(r"Whether they track each other is not a question five "
                   r"points can settle either way ($\rho = \ShareFormRho$, "
                   r"$p = \ShareFormP$)."), \
        "raising the question is not claiming the answer"
    assert not run(r"A surprise, and comprised of two parts ($p = "
                   r"\TrendCausalP$)."), "substrings are not words"
    # a correlation whose name is not Trend<X>P must be caught too: this
    # check matched the Trend prefix alone and let "rises too" stand beside
    # \TailTrendP = 0.083 through two builds
    bad = run(r"The bounded form rises too, $\rho = \TailTrendRho$ "
              r"($p = \TailTrendP$).")
    assert bad and "rises" in bad[0], bad
    del C.FAIL[:]
    print("  catch: a verb on any correlation that does not reach 0.05, "
          "whatever its macro is called")


check_self_reference_rule()
check_dtok_scope_rule()
check_param_spelling_rule()
check_trend_verb_rule()


def check_sigep_scope_rule():
    """sigma_EP's magnitude may not be quoted in the body of the paper.

    Section 6.3 said: "the capacity sweep reports sigma_EP rising by a
    factor of 4.1, so the compatible limit in which sigma vanishes is not
    one these models are approaching."  The appendix measures that the two
    do not track each other and says so; the main text then reasoned from
    one to the other anyway.  The rule is positional because the claim is:
    those readings belong to the system that defines them.
    """
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_paper as C

    def run(src):
        del C.FAIL[:]
        C.check_sigep_scope(src)
        return [m for _, m in C.FAIL]

    body_use = (r"so the compatible limit is not approached, since $\sigEP$"
                r" rises by $\ToyCapRatio$." "\n"
                r"\appendix" "\n"
                r"The sweep gives $\ToySpanRatio$.")
    bad = run(body_use)
    assert bad and "ToyCapRatio" in bad[0], bad

    # inside the appendix it is the appendix's own number and is fine
    assert not run(r"\appendix" "\n"
                   r"$\sigEP$ grows by $\ToyCapRatio$ over the sweep."), \
        "the appendix must be allowed its own quantity"

    # the cross-correlation is how the body BLOCKS the inference, not makes it
    assert not run(r"They do not track each other ($\rho = \CtrlRhoXS$)."
                   "\n" r"\appendix"), "CtrlRhoXS must stay permitted"
    del C.FAIL[:]
    print("  catch: sigma_EP's magnitude quoted outside the appendix")


check_sigep_scope_rule()


def check_narrowing_rule():
    """The word "narrows" needs a measurement behind it.

    Figure 1's caption asserted that the separation between the two series
    narrows and, in the same caption, that the statistic on the figure's own
    axis does not narrow at all.  The separation is the causal component,
    measured at one or two grid steps at every evaluator including the least
    saturated, so the first half was simply false.
    """
    import os, sys, tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_paper as C

    d = tempfile.mkdtemp()
    with open(os.path.join(d, "macros.tex"), "w") as f:
        f.write(r"\newcommand{\CausalGPTtwo}{+0.042}" "\n"
                r"\newcommand{\CausalQwen}{+0.042}" "\n")

    def run(src):
        del C.FAIL[:]
        C.check_narrowing(src, d)
        return [m for _, m in C.FAIL]

    bad = r"""\begin{figure}
\caption{The vertical separation between the two series narrows as that
happens.}
\label{fig:blkord}
\end{figure}"""
    assert run(bad), "a false narrowing claim must be caught"

    ok = r"""\begin{figure}
\caption{The separation does not close; what closes is the room above the
lower series.}
\label{fig:blkord}
\end{figure}"""
    assert not run(ok), "naming the room must be allowed"

    # a caption in another figure is not this rule's business
    other = r"""\begin{figure}
\caption{The band narrows.}
\label{fig:other}
\end{figure}"""
    assert not run(other), "only Figure 1 is checked"
    del C.FAIL[:]
    print("  catch: a narrowing asserted where the measurement does not narrow")


check_narrowing_rule()


def check_share_form_rule():
    """The disowned share form may not appear without the endorsed one.

    Section 5.3 declines to read the midrank causal component as a size and
    says only the ceiling-free z form can carry one; the abstract and five
    other passages then quoted the midrank share alone.
    """
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_paper as C

    def run(src):
        del C.FAIL[:]
        C.check_share_form(src)
        return [m for _, m in C.FAIL]

    assert run(r"Between $\ShareEvalMin\%$ and $\ShareEvalMax\%$ is causal."), \
        "the midrank share alone must be caught"
    assert not run(r"In $z$ it is $\ShareZMin\%$ to $\ShareZMax\%$."
                   "\n" r"On the midrank, $\ShareEvalMin\%$."), \
        "the pair in one paragraph must pass"
    assert run(r"In $z$ it is $\ShareZMin\%$." "\n\n"
               r"On the midrank, $\ShareEvalMin\%$."), \
        "a paragraph break between them must be caught"
    assert not run(r"The ceiling-free share is $\ShareZMin\%$ to "
                   r"$\ShareZMax\%$."), "the z form alone is fine"
    del C.FAIL[:]
    print("  catch: the midrank share quoted without the ceiling-free one")


check_share_form_rule()


def check_ref_subject_rule():
    """A section cited for sigma must be a section that discusses sigma.

    "Section 3.3 exhibits a model for which sigma vanishes identically"
    appeared twice; Section 3.3 is the permutation set and has no sigma in
    it.  \\ref resolved, so every existing check passed.
    """
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_paper as C

    doc = (r"\section{Permutations}" "\n" r"\label{sec:blkord}" "\n"
           r"The $n!$ arrangements are symmetric about zero." "\n\n"
           r"\section{The entropy production}" "\n" r"\label{sec:fbdef}" "\n"
           r"Here $\sigma$ is identically zero when the conditionals come "
           r"from a joint." "\n\n")

    def run(tail):
        del C.FAIL[:]
        C.check_ref_subject(doc + tail)
        return [m for _, m in C.FAIL]

    bad = run(r"Section~\ref{sec:blkord} exhibits a model for which "
              r"$\sigma$ vanishes identically.")
    assert bad and "sec:blkord" in bad[0], bad

    assert not run(r"Section~\ref{sec:fbdef} proves that $\sigma$ vanishes."), \
        "the right target must pass"

    # sigma named BEFORE the reference, about something else, is not this
    assert not run(r"It supplies a sign, $\sigma \geq 0$, and "
                   r"Section~\ref{sec:blkord} shows the values symmetric "
                   r"about zero."), "sigma before the verb is not the pattern"
    del C.FAIL[:]
    print("  catch: a section cited for a quantity it never mentions")


check_ref_subject_rule()


def check_duplicate_equation_rule():
    """One equation, one number.

    sigma was displayed in the introduction and again in Section 6.1, so it
    was Eq. (3) in two places and Eq. (12) in a third.  Both labels
    resolved; no existing check compares what they point at.
    """
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_paper as C

    def run(src):
        del C.FAIL[:]
        C.check_duplicate_equations(src)
        return [m for _, m in C.FAIL]

    dup = (r"\begin{equation}\sigma = a - b\label{eq:one}\end{equation}"
           "\n"
           r"\begin{equation}" "\n" r"\sigma = a - b" "\n"
           r"\label{eq:two}\end{equation}")
    bad = run(dup)
    assert bad and "eq:two" in bad[0] and "eq:one" in bad[0], bad

    ok = (r"\begin{equation}\sigma = a - b\label{eq:one}\end{equation}"
          r"\begin{equation}\Delta = a + b\label{eq:two}\end{equation}")
    assert not run(ok), "different equations must pass"

    # an unnumbered display is not a second number for anything
    un = (r"\begin{equation}\sigma = a - b\label{eq:one}\end{equation}"
          r"\begin{equation*}\sigma = a - b\end{equation*}")
    assert not run(un), "an unlabelled display carries no number"
    del C.FAIL[:]
    print("  catch: one equation displayed under two numbers")


check_duplicate_equation_rule()


def check_tolerance_wording_rule():
    """A deviation macro must be introduced as a deviation.

    "the self-test verifies that it normalises to $\\AoarNormDev$" reads as
    though the sum comes to 4.4e-16.  It comes to 1.
    """
    import os, sys, tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_paper as C

    d = tempfile.mkdtemp()
    with open(os.path.join(d, "macros.tex"), "w") as f:
        f.write(r"\newcommand{\AoarNormDev}{4.4\times10^{-16}}" "\n"
                r"\newcommand{\ReproMaxErr}{1e-12}" "\n"
                r"\newcommand{\ShareEvalMin}{10}" "\n")

    def run(src):
        del C.FAIL[:]
        C.check_tolerance_wording(src, d)
        return [m for _, m in C.FAIL]

    bad = run(r"The self-test verifies that it normalises to $\AoarNormDev$.")
    assert bad and "AoarNormDev" in bad[0], bad

    assert not run(r"It departs from $1$ by at most $\AoarNormDev$."), \
        "a named tolerance must pass"
    assert not run(r"The recomputation agrees to within $\ReproMaxErr$."), \
        "'to within' must pass"
    # a macro that is not a deviation is not this rule's business
    assert not run(r"The share is $\ShareEvalMin\%$."), "not a Dev/Err macro"
    del C.FAIL[:]
    print("  catch: a deviation quoted as though it were the value")


check_tolerance_wording_rule()


def check_glossary_linebreak():
    """A banned term must be caught even when it wraps across a line.

    "permutation construction" and "permutation range" both sat in main.tex
    against a rule that names the first, and neither this check nor grep
    found them: the term was split by a line break.  Any multi-word rule
    could be defeated by the line length of whoever typed it, which is to
    say by nothing.
    """
    import os, sys, tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_paper as C

    d = tempfile.mkdtemp()
    g = os.path.join(d, "glossary.txt")
    with open(g, "w") as f:
        f.write("permutation set | permutation construction\n")

    del C.FAIL[:]
    C.check_glossary("The permutation\nconstruction supplies one.", g)
    assert C.FAIL, "a wrapped banned term must be caught"

    del C.FAIL[:]
    C.check_glossary("The permutation set supplies one.", g)
    assert not C.FAIL, "the preferred term must pass"
    del C.FAIL[:]
    print("  catch: a banned term broken across a line")


check_glossary_linebreak()


def check_table_math_rule():
    """A generated table cell must wrap what tex_sci returns.

    tex_sci gives "2.5\\times10^{-3}" with no delimiters because the prose
    wraps it; one cell passed it through bare and the document stopped with
    four errors per row, none naming the generator.
    """
    import os, sys, tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_paper as C

    d = tempfile.mkdtemp()

    def run(name, body):
        with open(os.path.join(d, name), "w") as f:
            f.write(body)
        del C.FAIL[:]
        C.check_table_math(d)
        out = [m for _, m in C.FAIL]
        os.remove(os.path.join(d, name))
        return out

    assert run("tab_x.tex", r"a & b & 2.5\times10^{-3} \\"), \
        "bare math in a cell must be caught"
    assert not run("tab_x.tex", r"a & b & $2.5\times10^{-3}$ \\"), \
        "wrapped math must pass"
    # a macro body is math without delimiters on purpose
    assert not run("macros.tex", r"\newcommand{\P}{2.5\times10^{-3}}"), \
        "macros.tex is excluded by design"
    del C.FAIL[:]
    print("  catch: generated math outside math mode in a table cell")


check_table_math_rule()


def check_appendix_float_rule():
    """A float in the appendix may be cited long before it is printed.

    Table 8 is declared in the appendix and cited from Section 6.  The
    check called that a nine-page drift and two rounds of float tuning went
    into a layout that was already correct -- the second of them loosened
    settings that were not the problem.  The appendix is read from the
    source, where \\appendix says exactly where it starts, and the numbers
    from main.aux, where LaTeX has already resolved every label.
    """
    import os, sys, tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_paper as C

    d = tempfile.mkdtemp()
    with open(os.path.join(d, "main.aux"), "w") as f:
        f.write(r"\newlabel{tab:body}{{2}{5}}" "\n"
                r"\newlabel{tab:inappx}{{8}{28}}" "\n"
                r"\newlabel{fig:inappx}{{3}{27}}" "\n")
    src = (r"\section{Body}" "\n" r"\label{tab:body}" "\n"
           r"\appendix" "\n" r"\label{tab:inappx}" "\n"
           r"\label{fig:inappx}" "\n")
    got = C.appendix_float_numbers(src, d)
    assert got == {"Table 8", "Figure 3"}, got

    # a document with no appendix exempts nothing
    assert C.appendix_float_numbers(r"\label{tab:body}", d) == set()
    print("  pass: a float in the appendix is not a drifting float")


check_appendix_float_rule()


def check_orphan_rule():
    """An undeclared orphan fails; a declared one does not.

    As a warning this listed 152 names and nobody read it, which is how
    \\BlkNSepCausal sat unused while three sentences asserted in prose the
    thing it counts, and how \\TailSweepLoSixty sat unused while Section 5.3
    claimed to report the whole sweep.
    """
    import os, sys, tempfile
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_paper as C

    d = tempfile.mkdtemp()

    def write(retired):
        with open(os.path.join(d, "macros.tex"), "w") as f:
            f.write(r"\newcommand{\Quoted}{1}" "\n"
                    r"\newcommand{\Dropped}{2}" "\n"
                    r"\newcommand{\Declared}{3}" "\n")
            if retired:
                f.write("% retired: " + " ".join(retired) + "\n")

    src = r"\input{tables/macros} The value is $\Quoted$."

    write(["Declared"])
    del C.FAIL[:]; del C.WARN[:]
    C.check_macros(src, d)
    bad = [m for _, m in C.FAIL]
    assert bad and "Dropped" in bad[0], bad
    assert "Declared" not in bad[0], bad

    write(["Declared", "Dropped"])
    del C.FAIL[:]; del C.WARN[:]
    C.check_macros(src, d)
    assert not C.FAIL, [m for _, m in C.FAIL]

    # a retired name the prose has started using again is a stale declaration
    write(["Declared", "Dropped", "Quoted"])
    del C.FAIL[:]; del C.WARN[:]
    C.check_macros(src, d)
    assert any("declared retired and the prose uses them" in m
               for _, m in C.FAIL), [m for _, m in C.FAIL]
    del C.FAIL[:]; del C.WARN[:]
    print("  catch: a macro the prose dropped, and a stale retirement")


check_orphan_rule()


def check_percentile_rule():
    """The ordinal is the only permitted spelling; the rest must fail."""
    import check_paper as C
    ok = [r"above the non-causal group's own $\TailZQ$th percentile",
          r"the non-causal $90$th percentile (null $10\%$)",
          "causal texts above the non-causal group's own\n$\\TailZQ$th "
          "percentile, so its null"]
    bad = [r"the percentile of the authored arrangement",
           r"the authored arrangement's percentile",
           r"its percentile among the $n!$ arrangements",
           r"the percentile rank of the written order",
           r"percentile within its permutation set"]
    for s in ok:
        C.FAIL[:] = []
        C.check_percentile_sense(s)
        assert not C.FAIL, (s, [m for _, m in C.FAIL])
    for s in bad:
        C.FAIL[:] = []
        C.check_percentile_sense(s)
        assert C.FAIL, s
    C.FAIL[:] = []
    del C.WARN[:]
    print("  catch: percentile written for a midrank, in any construction")


check_percentile_rule()


def check_corpus_order_rule():
    """A table whose corpora are permuted must be caught."""
    import check_paper as C
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "corpus_order.txt"), "w") as fh:
            fh.write("Opus46 GPT54 GPT56\n")

        def table(seq):
            with open(os.path.join(d, "tab_x.tex"), "w") as fh:
                fh.write("\n".join(r + " & 1 \\\\" for r in seq) + "\n")

        table(["Opus46", "GPT54", "GPT56"])
        C.FAIL[:] = []
        C.check_corpus_order(d)
        assert not C.FAIL, [m for _, m in C.FAIL]

        # two evaluator blocks, each in order: still fine
        table(["Opus46", "GPT54", "GPT56", "Opus46", "GPT54", "GPT56"])
        C.FAIL[:] = []
        C.check_corpus_order(d)
        assert not C.FAIL, [m for _, m in C.FAIL]

        # one block permuted
        table(["Opus46", "GPT56", "GPT54"])
        C.FAIL[:] = []
        C.check_corpus_order(d)
        assert any("out of the canonical order" in m for _, m in C.FAIL), \
            [m for _, m in C.FAIL]
        C.FAIL[:] = []
        del C.WARN[:]
    print("  catch: a generated table that permutes the corpus axis")


check_corpus_order_rule()


def check_sigma_prime_rule():
    """The working name must not come back."""
    import check_paper as C
    for s in (r"and $\sigma'$ is a function",
              r"its $\sigma^{\prime}(x) = 0$ is a measurement"):
        C.FAIL[:] = []
        C.check_sigma_prime(s)
        assert C.FAIL, s
    C.FAIL[:] = []
    C.check_sigma_prime(r"the quantity $\Dblock$ is a function")
    assert not C.FAIL, [m for _, m in C.FAIL]
    del C.WARN[:]
    print("  catch: a sigma-shaped symbol standing for Ref. [1]'s quantity")


check_sigma_prime_rule()


def check_between_sign_rule():
    """An agreement in sign must be reported, not printed over."""
    import check_paper as C
    with tempfile.TemporaryDirectory() as d:
        src = "on \\FbBetweenNOpposite of the corpora they do not agree"
        for v, want in (("2", False), ("0", True)):
            with open(os.path.join(d, "macros.tex"), "w") as fh:
                fh.write("\\newcommand{\\FbBetweenNOpposite}{" + v + "}\n")
            C.check_between_sign(src, d)
            got = any("agree in sign on every corpus" in m for _, m in C.FAIL)
            assert got is want, (v, [m for _, m in C.FAIL])
            del C.FAIL[:]
            del C.WARN[:]
    print("  catch: the evaluators agreeing where the prose says they do not")

def check_flat_rule():
    """"flat" only in the negative."""
    import check_paper as C
    ok = [r"the contrast is neither at the floor nor flat",
          r"read there it is not flat along the ladder",
          r"it is never flat on this set"]
    bad = [r"a reader can see the flat series",
           r"the non-causal column is flat",
           r"the fraction at the extreme arrangement being flat"]
    for s in ok:
        del C.FAIL[:]
        C.check_flat_sense(s)
        assert not C.FAIL, (s, [m for _, m in C.FAIL])
    for s in bad:
        del C.FAIL[:]
        C.check_flat_sense(s)
        assert C.FAIL, s
    del C.FAIL[:]
    del C.WARN[:]
    print("  catch: a series called flat without the measurement")


def check_double_superscript_rule():
    """A star on a p-value already in exponent form."""
    import check_paper as C
    with tempfile.TemporaryDirectory() as d:
        for body, want in (
                (r"a & $+0.311$ & $1\times10^{-4}^{*}$ \\", True),
                (r"a & $+0.311$ & $1\times10^{-4}{}^{*}$ \\", False),
                (r"a & $+0.311$ & $0.004^{*}$ \\", False),
                (r"a & $x^{2}$ and $y^{3}$ \\", False)):
            with open(os.path.join(d, "tab_x.tex"), "w") as fh:
                fh.write(body + "\n")
            del C.FAIL[:]
            C.check_double_superscript(d)
            assert bool(C.FAIL) is want, (body, [m for _, m in C.FAIL])
    del C.FAIL[:]
    del C.WARN[:]
    print("  catch: a superscript written on a superscript")


def check_model_inventory_rule():
    """A model named in the prose with no row in the evaluator table."""
    import check_paper as C
    table = (r"\begin{tabular}{llll}"
             r"model & parameters & direction & role \\"
             r"\texttt{gpt2} & 124M & autoregressive & x \\"
             r"\texttt{bert-base-uncased} & 110M & masked & y \\"
             r"\texttt{GSAI-ML/LLaDA-8B-Base} & 8B & masked & z \\"
             r"\end{tabular}")
    for prose, want in (
            (r"we scored with \texttt{bert-base} and \texttt{LLaDA}", False),
            (r"\texttt{gpt2} is the published evaluator", False),
            (r"we also ran \texttt{bert-large} and withdrew it", True),
            (r"write to \texttt{tag@granular.com}", False)):
        del C.FAIL[:]
        C.check_model_inventory(table + " " + prose)
        assert bool(C.FAIL) is want, (prose, [m for _, m in C.FAIL])
    del C.FAIL[:]
    C.check_model_inventory("no table here")
    assert C.FAIL, "a missing table should be reported, not passed"
    del C.FAIL[:]
    del C.WARN[:]
    print("  catch: a model named in prose and absent from the inventory")


def check_withdrawn_words_rule():
    """A word a withdrawal removed, still in the prose."""
    import check_paper as C
    decl = ("% withdrawn-prose: bert-large|0|the PLL comparison|it was here "
            "only for that\n"
            "% withdrawn-prose: pseudo-log-likelihood|1|the PLL comparison|"
            "the appendix computes it once\n"
            "% withdrawn-prose: flat|-|the saturation argument|"
            "check_flat_sense carries it\n")
    cases = [
        (r"we used \texttt{bert-base} throughout", False),
        (r"we also ran \texttt{bert-large}", True),
        (r"a pseudo-log-likelihood is computed in the appendix", False),
        (r"a pseudo-log-likelihood here and a pseudo-log-likelihood there",
         True),
        (r"the series is flat and flat and flat", False),   # delegated
        (r"% bert-large in a comment does not count", False),
    ]
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "macros.tex"), "w") as fh:
            fh.write(decl)
        for prose, want in cases:
            del C.FAIL[:]
            C.check_withdrawn_words(prose, d)
            assert bool(C.FAIL) is want, (prose, [m for _, m in C.FAIL])
    del C.FAIL[:]
    C.check_withdrawn_words(r"\texttt{bert-large}", "/nonexistent")
    assert not C.FAIL, "no macros.tex means nothing to enforce"
    del C.FAIL[:]
    del C.WARN[:]
    print("  catch: a word a withdrawal removed, still in the prose")


check_withdrawn_words_rule()


check_model_inventory_rule()


check_double_superscript_rule()


def check_absence_scope_rule():
    """A claim of absence that does not say in which reading."""
    import check_paper as C
    ok = [r"on a fixed text no identity is available",
          r"its central quantity is unanchored in the fixed-text reading",
          r"the quantity has no zero that holds on the text being read",
          r"it has no origin, and no theorem reaches a single fixed text"]
    bad = [r"Nothing in that is an identity, and no identity is available",
           r"Its central quantity is unanchored, and the quantity it was",
           r"there is no limit in which it becomes zero and no identity to",
           r"There is no limit in which $\Delta$ becomes zero, and it is a"]
    for s in ok:
        del C.FAIL[:]
        C.check_absence_scope(s)
        assert not C.FAIL, (s, [m for _, m in C.FAIL])
    for s in bad:
        del C.FAIL[:]
        C.check_absence_scope(s)
        assert C.FAIL, s
    del C.FAIL[:]
    del C.WARN[:]
    print("  catch: an absence claim that does not name its reading")


def check_bare_floor_rule():
    """"the floor" with nothing attached."""
    import check_paper as C
    ok = [r"it is not at the grid floor", r"the exact floor of 0.017",
          r"the masked floor is characterised", r"gives it its floor",
          r"which is not a floor", r"the floor of that instrument",
          r"the floor imposed by conditionals", r"the size of that floor"]
    bad = [r"Read in the upper tail it leaves the floor and moves",
           r"so that the floor is not mistaken for an artefact"]
    for s in ok:
        del C.FAIL[:]
        C.check_bare_floor(s)
        assert not C.FAIL, (s, [m for _, m in C.FAIL])
    for s in bad:
        del C.FAIL[:]
        C.check_bare_floor(s)
        assert C.FAIL, s
    del C.FAIL[:]
    del C.WARN[:]
    print("  catch: a floor with nothing saying which floor")


check_bare_floor_rule()


check_absence_scope_rule()


check_flat_rule()


check_between_sign_rule()
