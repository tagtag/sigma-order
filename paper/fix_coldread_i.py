r"""The ninth read's three decisions, and the last seam.

 1. The definite-article family, last two members.  Both are of the type
    "this quantity IS the stochastic-thermodynamic one" -- a statement of
    agreement with the textbook definition, not a statement about Ref. [1],
    which is why they were allowed to stand.  What makes them wrong is
    internal: Section 2.2 p.7 writes the same object as "an *entropy
    production* with a zero on a single text", indefinite and italic,
    precisely to avoid the exclusivity.  A reader who has met the careful
    indefinite first hears the definite as exclusive.  The two sites are
    each other's pair, so they move together or not at all.

 2. The Section 6 title stays as changed.  Every forward reference was
    checked against it and none depended on the old claim.

 3. Section 5 is the last seam.  The paper tells the reader three times
    that Section 5 reads what Ref. [1]'s own first step found (Section 1's
    two-question paragraph, Section 1's close, Section 2.2's end), and
    Section 5 opens on its subsection with no preamble at all.  Section 6
    receives its handoff explicitly; Section 5 is the one section outside
    the chain.  Two sentences close it.

    NOTE on the proposed wording.  The reader's draft read "on a ladder of
    evaluators rather than one".  Ref. [1] Sec. V B uses TWO evaluators,
    GPT-2 and Qwen3-4B -- which are the two ends of this paper's ladder --
    so "rather than one" is false.  The count comparison is dropped and the
    ladder's size is taken from \TrendNEval rather than typed.

 4. Section 7's "either", lowest priority: the antecedent negation it wants
    is about the theorem, and the preceding sentence negates something else.
    Rewritten so no antecedent is needed.

Run:  python fix_coldread_i.py <paper dir>
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


# ============================== 1a: Section 1, paired with 1b below
rep("sec_intro.tex",
    r"""This is the entropy production of the stochastic-thermodynamic
definition~\cite{jarzynski1997, crooks1999, seifert2012}: one trajectory
weighed against its own reversal under the dynamics that produced it.""",
    r"""This is an entropy production in the sense
of~\cite{jarzynski1997, crooks1999, seifert2012}: one trajectory
weighed against its own reversal under the dynamics that produced it.""",
    "1a: indefinite, as Section 2.2 p.7 writes the same object")

# ============================== 1b: Section 6.1, the pair
rep("sec_truesigma.tex",
    r"""That is the forward path
against its reverse, which is what the stochastic-thermodynamic $\sigma$ is.""",
    r"""That is the forward path
against its reverse, which is what the stochastic-thermodynamic definition
asks for.""",
    "1b: the definition stays definite; the quantity stops being the only one")

# ============================== 3: the handoff Section 5 never received
rep("main.tex",
    r"""\section{Results II: the labelled contrast}
\label{sec:causal}

\subsection{What the labels record, and what they do not}""",
    r"""\section{Results II: the labelled contrast}
\label{sec:causal}

Reference~\cite{sagawa2026} presents the labelled contrast as a first step
toward saying what the entropy production means once it is applied to a real
language model~\cite[Sec.~V~B]{sagawa2026}.  This section is that step
re-measured, across a ladder of \TrendNEval\ evaluators.  What decides what
the step can mean is the labelling, which comes first.

\subsection{What the labels record, and what they do not}""",
    "3: the chain closes; Section 5 now receives what three places hand it")

# ============================== 4: no antecedent negation required
rep("main.tex",
    r"""so the theorem does not reach the average here either, and
Ref.~\cite{sagawa2026} states for that case that the averages are not
guaranteed to be non-negative.""",
    r"""so here the theorem does not reach even that average, and
Ref.~\cite{sagawa2026} states for that case that the averages are not
guaranteed to be non-negative.""",
    "4: the escalation carries itself")

print(f"done: {N} edits")
