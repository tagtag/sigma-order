r"""The fourth read: title, abstract, Section 1, Discussion.

3b. The Discussion's second paragraph says "the sets differ, not by how
    much, and even taken at face value the separation does not quantify
    anything", one paragraph after reporting that the tail separation is
    +13 to +22 points and grows with capacity.  Section 5.3 forbids this
    generalisation in as many words: the resolution statement is about the
    MEDIAN difference and is not a statement about the contrast.  The
    sentence before it keeps the scope ("the component is 1--2 steps") and
    the two after it drop it.

3a. The Discussion declares its conclusion negative in two ways, and
    neither is the title's.  The subtitle's second half survives into the
    last paragraph; the main title's claim appears nowhere in the section.
    Four places now offer four different pairs of conclusions.

1.  The abstract argues the title's claim from "x-tilde is a different
    text", which reads as though scoring one text twice would make the
    comparison a path reversal -- true of sigma only, and only with
    Section 6.1's argument that the path is the assembly order.  Section
    2.2 argues it from protocol reversal.  The abstract keeps the claim
    and the contrast that carries it, and leaves the argument to 2.2.
    Also: "its reversal" is the token reversal, two sentences before
    "reversal" is used in the theorems' sense; and a quantity is not a
    reversal, it is built on one.

2.  Section 1's "The distinction is not notational fastidiousness: the two
    quantities behave differently" sits directly after the title's claim
    and reads as support for it.  It supports something else -- that the
    distinction matters -- and says so now.
"""
import io
import os
import sys

os.chdir(sys.argv[1])
N = 0


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
    print(f"  {label}")
    N += 1


# ======================================================== 3b, first
rep("main.tex",
    r"""What
is established is that the sets differ, not by how much, and even taken at
face value the separation does not quantify anything.  This is not a weakness of the statistic.  It is a missing construct,
and no refinement of the measurement supplies one.""",
    r"""What
the median establishes is that the sets differ and not by how much.  The
tail is a different statistic of the same contrast and does give a size,
which is why Section~\ref{sec:window} reports it; the resolution argument is
about the median and we do not extend it past that.  What neither statistic
supplies is a referent for the difference.  This is not a weakness of the
statistic.  It is a missing construct, and no refinement of the measurement
supplies one.""",
    "3b: the resolution claim keeps the scope Section 5.3 gave it")

# ======================================================== 3a
rep("main.tex",
    r"""Our conclusion is negative in two independent ways, and the two should not be
conflated.

As a \emph{quantity}, $\Delta$ cannot be interpreted,""",
    r"""Our conclusion is negative in three ways.  The first settles the
thermodynamic reading on its own, before any measurement; the other two are
independent of it and of each other.  The three should not be conflated.

As a \emph{reversal}, Eq.~\eqref{eq:delta} is not one.  The fluctuation
theorems weigh a trajectory against its own reverse, and $x$ and $\tilde{x}$
are two states --- the second is a different text, not the first one run
backwards (Section~\ref{sec:notareversal}).  Nothing about the evaluator or
the corpus bears on this, and no measurement can repair it: what the
thermodynamic reading names is not what Eq.~\eqref{eq:delta} computes.  The
quantity it names does exist for a masked model, and
Section~\ref{sec:truesigma} measures it.

As a \emph{quantity}, $\Delta$ cannot be interpreted,""",
    "3a: the title's claim is the Discussion's first conclusion")

# ======================================================== 1
rep("main.tex",
    r"""A single
text is neither a distribution over trajectories nor a dynamics, and the
comparison is not a reversal in the sense the theorems use: $\tilde{x}$ is a
different text, so Eq.~\eqref{eq:delta} weighs one text against another and
never a path against its own reverse.  No theorem fixes where the zero of
such a quantity lies.""",
    r"""A single
text is neither a distribution over trajectories nor a dynamics, and the
comparison is not a reversal in the sense the theorems use: those weigh a
trajectory against its own reverse, while $x$ and $\tilde{x}$ are two states
(Section~\ref{sec:notareversal}).  No theorem fixes where the zero of such a
quantity lies.""",
    "1a: the abstract states the contrast and leaves the argument to 2.2")

rep("main.tex",
    r"""its reversal $\tilde{x}$ --- and read as an entropy production separating""",
    r"""its token reversal $\tilde{x}$ --- and read as an entropy production
separating""",
    "1b: which reversal, two sentences before the other sense of the word")

rep("main.tex",
    r"""$\Delta$ is not a path reversal, and what it does
separate is mostly the order the passage was produced in.  $\sigma$ is a path reversal,
and its value is set by the evaluator's incompatibility rather than by the
text.""",
    r"""$\Delta$ is not built on a path reversal, and what it
does separate is mostly the order the passage was produced in.  $\sigma$ is
built on one, and its value is set by the evaluator's incompatibility rather
than by the text.""",
    "1c: a number is not an operation")

rep("sec_intro.tex",
    r"""Take a fixed text $x$ of $L$ tokens, reverse it to obtain
$\tilde{x}$, score both with a language model, and form""",
    r"""Take a fixed text $x$ of $L$ tokens, reverse its token
order to obtain $\tilde{x}$, score both with a language model, and form""",
    "1d: the same, in the introduction")

# ======================================================== 2
rep("sec_intro.tex",
    r"""We therefore write it $\Delta$
throughout and reserve $\sigma$ for Eq.~\eqref{eq:fb}.  The
distinction is not notational fastidiousness: the two quantities behave
differently under the very operation that defines them.""",
    r"""We therefore write it $\Delta$
throughout and reserve $\sigma$ for Eq.~\eqref{eq:fb}.  Keeping the two
apart matters for a second reason, independent of the first: they behave
differently under the very operation that defines them.""",
    "2: the sentence says which claim it supports")

print(f"done: {N} edits")
