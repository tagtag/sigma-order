r"""A term used six times by a paper that uses the quantity once.

"pseudo-log-likelihood" appears six times and is never defined.  Asked what
it meant, the reader then asked the better question: why is it here at all?

Counted by role, five of the six are not doing work.

  Section 3.2, the argument.  "A pseudo-log-likelihood sums exactly these,
  which is why it is not the logarithm of anything."  The argument is
  complete two sentences earlier: Eq. (1) needs log P from one
  distribution, and a masked model supplies one per unmasking order, not
  one distribution.  Nothing after this sentence uses it.  (It is also
  wrong as written -- a PLL sums the LOGARITHMS of those conditionals --
  and fixing that would have kept a sentence that should go.)

  Section 3.2, the withdrawal.  "; a pseudo-log-likelihood is the usual
  choice."  The paragraph's two jobs are to forestall "why not evaluate
  Delta on a masked model" and to record that we did and withdrew it.  The
  name does neither.  What was substituted is in the repository.

  Limitations, the unit.  "that ratio is between a pseudo-log-likelihood
  and a log-probability" restates "the ratio between a masked evaluator's
  score and an autoregressive one's" from the same sentence.

  Limitations, the counterpart.  "The pseudo-log-likelihood is not a
  log-probability, so Delta has no masked counterpart" gives the wrong
  reason.  Delta has no masked counterpart because a masked model supplies
  no single joint.  That holds whether or not anyone computes a PLL, and
  it is what the next sentence contrasts the any-order chain rule against.

  Figure 2's caption.  "is a pseudo-log-likelihood difference rather than
  Delta" -- "is not Delta" says what the caption needs.

The sixth is a real use: the appendix exponentiates and normalises it as
one of three candidate joints.  It survives, spelled out rather than
abbreviated, since it is now the only occurrence.

Naming the substitute invites a reader to evaluate the substitute, and the
paper's position is that the substitution means nothing.  Six mentions
built a thread the paper then has to keep answering.  One mention, where
the quantity is actually computed, ends it.

AND LINE NUMBERS.  Every item sent for the read-through so far has carried
a main.tex line number, which is useless to someone reading the PDF.  The
draft now prints line numbers, so a stumble can be named by where it is
seen.  \draftlinestrue at the top turns them on; the submission build
turns them off, and make_arxiv.sh will refuse to package while they are on
(that half lands with the $PY fix already queued for it).

Run:  python fix_pll.py <paper dir>
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


# ------------------------------------------- 1 the argument does not need it
rep("main.tex",
    r"""compatibility conditions for that are restrictive.  A pseudo-log-likelihood
sums exactly these, which is why it is not the logarithm of anything.""",
    r"""compatibility conditions for that are restrictive.""",
    "1: Section 3.2's argument, which was complete without it")

# ------------------------------------------------- 2 the withdrawal record
rep("main.tex",
    r"""masked model by substituting some other number for $\log P$; a
pseudo-log-likelihood is the usual choice.  We did exactly that, for three""",
    r"""masked model by substituting some other number for $\log P$.  We did
exactly that, for three""",
    "2: the withdrawal says what was done, not what it was called")

# ------------------------------------------------------- 3 the common unit
rep("main.tex",
    r"""score and an autoregressive one's, and that ratio is between a
pseudo-log-likelihood and a log-probability --- between a number and a
different number (Section~\ref{sec:scope}).""",
    r"""score and an autoregressive one's, which is a ratio between a number and a
different number (Section~\ref{sec:scope}).""",
    "3: the sentence already said it in its first clause")

# ------------------------------------------------- 4 the reason, corrected
rep("main.tex",
    r"""\emph{The pseudo-log-likelihood is not a log-probability}
(Section~\ref{sec:scope}), so $\Delta$ has no masked counterpart and none is
reported here.""",
    r"""\emph{A masked model supplies no single joint}
(Section~\ref{sec:scope}), so $\Delta$ has no masked counterpart and none is
reported here.""",
    "4: the reason Delta has no masked counterpart")

# ------------------------------------------------------- 5 Figure 2's caption
rep("main.tex",
    r"""What was measured
for the masked evaluators in that comparison is a pseudo-log-likelihood
difference rather than $\Delta$ (Section~\ref{sec:scope}), so it is""",
    r"""What was measured
for the masked evaluators in that comparison is not $\Delta$
(Section~\ref{sec:scope}), so it is""",
    "5: the caption needs only that it is not Delta")

# --------------------------------------- 6 the one real use, spelled out
rep("main.tex",
    r"""joints are used --- $\exp(\mathrm{PLL})$ normalised over the state space, and
the any-order chain rule taken left to right and right to left --- and the
\emph{recovered} column is the largest $|\sigEP|$ of the three.""",
    r"""joints are used --- the exponentiated pseudo-log-likelihood normalised over
the state space, and the any-order chain rule taken left to right and right
to left --- and the \emph{recovered} column is the largest $|\sigEP|$ of the
three.  Normalising it is possible here and not for text, because it needs a
sum over every state and this system has $\ToyStates$ of them; it enters as a
candidate joint to recover conditionals from, and not as a score.""",
    "6: the only place the quantity is computed says why it is available",
    marker="it enters as a\ncandidate joint")

# ----------------------------------------------------- 7 line numbers
rep("main.tex",
    r"""\usepackage{microtype}""",
    r"""\usepackage{microtype}

% Line numbers for the read-through.  Every revision item so far has been
% addressed by a main.tex line number, which is not visible to anyone
% reading the PDF.  \draftlinesfalse before submission; make_arxiv.sh
% refuses to package while this is true.  The amsmath environments are
% patched because lineno otherwise loses their numbering.
\newif\ifdraftlines \draftlinestrue
\ifdraftlines
  \usepackage[mathlines]{lineno}
  \linenumbers
  \newcommand*\patchAmsMathEnvironmentForLineno[1]{%
    \expandafter\let\csname old#1\expandafter\endcsname\csname #1\endcsname
    \expandafter\let\csname oldend#1\expandafter\endcsname\csname end#1\endcsname
    \renewenvironment{#1}%
       {\linenomath\csname old#1\endcsname}%
       {\csname oldend#1\endcsname\endlinenomath}}%
  \newcommand*\patchBothAmsMathEnvironmentsForLineno[1]{%
    \patchAmsMathEnvironmentForLineno{#1}%
    \patchAmsMathEnvironmentForLineno{#1*}}%
  \AtBeginDocument{%
    \patchBothAmsMathEnvironmentsForLineno{equation}%
    \patchBothAmsMathEnvironmentsForLineno{align}%
    \patchBothAmsMathEnvironmentsForLineno{gather}%
    \patchBothAmsMathEnvironmentsForLineno{multline}%
    \patchBothAmsMathEnvironmentsForLineno{flalign}%
    \patchBothAmsMathEnvironmentsForLineno{alignat}}
\fi""",
    "7: the PDF carries line numbers while the draft is being read",
    marker=r"\newif\ifdraftlines")

# -------------------------------------------- 8 the state of the toggle
rep("check_paper.py",
    '''          f"{NLONG} sentence(s) over {SENTENCE_WORDS} words (budget "
          f"{SENTENCE_BUDGET})")''',
    '''          f"{NLONG} sentence(s) over {SENTENCE_WORDS} words (budget "
          f"{SENTENCE_BUDGET})")
    # Stated, not warned: line numbers in the draft are deliberate, and a
    # standing warning about a deliberate thing is how a real one gets
    # skipped.  make_arxiv.sh is what refuses to package with them on.
    print("  draft line numbers: "
          + ("ON (\\\\draftlinesfalse before submitting)"
             if re.search(r"\\\\draftlinestrue", src) else "off"))''',
    "8: the build states whether line numbers are on",
    marker="draft line numbers:")

SUSPECT = re.compile(
    r"\bthe ones?\s*(?=[.,;:]|\b(?:that|which|it|we|they|the|is|are)\b)|"
    r"\b(?:that kind|this kind|a kind|that form|this form|"
    r"of that|of this|the thing|in this sense|this reading|the other one|"
    r"such a|that of|need not\b(?!\s+\w)|does not\.|do not\.|cannot\.|"
    r"\bis of the\b|\bis of a\b|\band not of\b|\bbut not of\b)", re.I)
bad = [(lab, m.group(0)) for lab, b in WROTE
       if lab[0] in "123456" for m in SUSPECT.finditer(b)]
if bad:
    print("\n  !! replacement text contains new pointing constructions:")
    for lab, hit in bad:
        print("     %-40s %r" % (lab, hit))
    raise SystemExit("fix the replacements before shipping this patch")
print(f"done: {N} edits (replacement text clean)")
