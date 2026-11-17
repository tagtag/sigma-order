r"""Section 2.1's two-levels sentence: a circular clause, and two bare nouns.

    "This paper leans on that identity as heavily as it leans on the
     difference, and the two are not in competition: as sequences the pair
     are distinct, which is why what $\Delta$ reverses is the text; as
     material they are matched, which is why what remains between them is
     arrangement and nothing else."

Two faults.

1. The opening leans on "that identity" and "the difference": bare
   abstractions whose referents are, respectively, the previous sentence
   and an argument several pages back.  The colon then says both of them
   again, concretely.  The opening is the colon's work done in advance and
   in worse words -- and "identity" collides with this paper's own
   convention, recorded at Eq. (antisym), that the word without
   qualification means $\sigma = 0$.

2. "as material they are matched, which is why what remains between them
   is arrangement and nothing else" is circular.  Material is what the two
   share once arrangement is set aside, so "matched in material, therefore
   only arrangement differs" restates its own premise.

   The substance is not in the word.  It is in the MAP: reversal permutes
   tokens and adds, removes and alters nothing, which a paraphrase or a
   truncation would not -- and the sentence before says exactly that
   ("$\tilde{x}$ is $x$ read backwards, SO the tokens, the length and the
   vocabulary are identical").  What the clause should carry is not that
   premise again but what follows from it: a difference between the two
   can be attributed to order.  That is the step Section 5's decomposition
   stands on, and the restatement supports nothing.

Fixed, the two halves become parallel: distinct as sequences, so the
comparison has no origin; matched as material, so what it does show can be
attributed.

Run:  python fix_material.py <paper dir>
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
    r"""This paper leans
on that identity as heavily as it leans on the difference, and the two are
not in competition: as sequences the pair are distinct, which is why
what $\Delta$ reverses is the text; as material they are matched, which is
why what remains between them is arrangement and nothing else.""",
    r"""The pair stand in
two relations at once and this paper uses both, which is why they do not
compete: as sequences they are distinct, which is why what $\Delta$
reverses is the text; as
material they are matched, which is why a difference between them can be
attributed to order and to nothing else.""",
    "the opening drops, and the second half states what follows "
    "rather than its own premise")

print(f"done: {N} edits")
