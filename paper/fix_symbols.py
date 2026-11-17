r"""Two symbols used without introduction, found by audit_symbols.py.

$\mathcal{S}$ -- ONCE, in Section 2.2, never introduced anywhere:

    "its $\mathcal{S} \geq 0$ is a statement about an average under
     $P_\to$, with equality when the law is invariant under $R$"

Exactly the shape $\sigma'$ had: a symbol for Ref. [1]'s functional,
appearing in one sentence, with no definition in this paper.  The sentence
does not need it -- what it asserts is the non-negativity, and the clause
that follows ("with equality when...") attaches to that just as well.  The
paragraph four pages earlier already says the same thing in words: "The
non-negativity and the fluctuation theorem are statements about an average
under $P_\to$."

$J$ -- used at its first appearance as though already defined:

    "how far the recovered conditionals are from the model's own: $J$ runs
     from \CtrlJeffreysMin to \CtrlJeffreysMax"

It is a Jeffreys divergence, and the appendix says so -- thirty-five lines
later, about a different quantity.  Named where it is first used.

Three further symbols the audit lists are conventional and left alone, but
recorded here so the decision is not re-made from scratch: $\theta$ for
model parameters in $p_\theta$; $\rho$ for a rank correlation, first used
in the abstract and tied to Spearman in Section 5.4; and $\pi'$, used once
for a second unmasking order in a sentence that says "every pair of
orders".

Run:  python fix_symbols.py <paper dir>
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


rep("main.tex",
    r"""not the value a quantity takes when there is nothing to report; its
$\mathcal{S} \geq 0$ is a statement about an average under $P_\to$, with
equality when the law is invariant under $R$.""",
    r"""not the value a quantity takes when there is nothing to report; its
non-negativity is a statement about an average under $P_\to$, with
equality when the law is invariant under $R$.""",
    "1: the undefined functional goes; the claim it carried stays")

rep("main.tex",
    r"""the model's own: $J$ runs from $\CtrlJeffreysMin$ to $\CtrlJeffreysMax$ at""",
    r"""the model's own: a Jeffreys divergence $J$ runs from $\CtrlJeffreysMin$ to
$\CtrlJeffreysMax$ at""",
    "2: J is named where it is first used")

print(f"done: {N} edits")
