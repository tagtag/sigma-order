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
