r"""Unanchored referents, batch 2.

Four more patterns triaged -- indefinite article + abstract noun (47
sites), bare "the" + abstract noun (59), bare "the two" (3), and
sentence-initial pronoun (88) -- 197 sites read.  Five need the referent
named.  The rest resolve to the subject of the sentence before, or to a
noun inside their own sentence, and are left alone.

The yields differ by pattern, which is worth recording: the indefinite
article was almost entirely clean (it is generic by nature and asks for no
antecedent), "the identity" was clean in all eight uses because the
convention at Eq. (antisym) is actually kept, and the ordinals of batch 1
were the worst.

1 and 2.  The abstract and Section 1 report the causal component the same
   way, one sentence apart in their respective paragraphs:

     abstract: "...is that the two label groups differ and not by how
                much.  IT stays there at every rung of the ladder"
     Section 1: "...differ, not by how much.  IT is \CausalCompStepsMin to
                 \CausalCompStepsMax steps at every size we measured"

   In both, the subject of the sentence before is "what is established",
   not the component, so "It" has to reach past it.  The abstract already
   names the component correctly four lines earlier -- "THAT PART
   separates the two label groups" -- so the fix is its own wording.

3. Section 1 again: "It separates the two label groups in N of M cells",
   where the abstract's twin sentence says "That part separates...".  Two
   sentences doing one job, one named and one not.

4. Section 2.2: "That is THE CONTRAST this paper's subtitle names."  The
   contrast meant is $\Delta$ against $\sigma$; "the contrast" everywhere
   in Sections 5 and 7 is the labelled one.  Fifteen uses of the phrase
   and this is the only one that means something else.

5. Section 2.2: "the answer is not the one THE CONSTRUCTION invites."
   Three constructions are live by this point -- the permutation set, the
   between-set reading, and the masked estimator -- and the sentence means
   none of them in particular: what invites the wrong answer is the name
   "entropy production".  Section 1 already has the phrase for it ("not
   what the name promises").

Run:  python fix_referents2.py <paper dir>
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
    r"""that the two label groups differ and not by how much.  It stays there at every rung of the ladder,""",
    r"""that the two label groups differ and not by how much.  That part stays
there at every rung of the ladder,""",
    "1: the abstract names the component, as it does four lines earlier")

rep("sec_intro.tex",
    r"""measurement establishes is that the two label groups differ, not by how much.  It is \CausalCompStepsMin\ to \CausalCompStepsMax\ steps at every size we""",
    r"""measurement establishes is that the two label groups differ, not by how
much.  That part is \CausalCompStepsMin\ to \CausalCompStepsMax\ steps at
every size we""",
    "2: and so does Section 1, in the same words")

rep("sec_intro.tex",
    r"""ceiling, and $\ShareEvalMin\%$ to $\ShareEvalMax\%$ in midrank units.  It
separates the two label groups in \ContrastNRejecting\ of the""",
    r"""ceiling, and $\ShareEvalMin\%$ to $\ShareEvalMax\%$ in midrank units.  That
part separates the two label groups in \ContrastNRejecting\ of the""",
    "3: the twin of the abstract's sentence is worded like it")

rep("main.tex",
    r"""That is the contrast this paper's subtitle names, and it is why an \emph{entropy""",
    r"""That contrast between the two quantities is what this paper's subtitle
names, and it is why an \emph{entropy""",
    "4: the one use of \"the contrast\" that is not the labelled one says so")

rep("main.tex",
    r"""reports is a separate question, and the answer is not the one the
construction invites: Section~\ref{sec:fbresult} measures it and finds it""",
    r"""reports is a separate question, and the answer is not what the name
promises: Section~\ref{sec:fbresult} measures it and finds it""",
    "5: what invites the wrong answer is the name, in Section 1's words")

print(f"done: {N} edits")
