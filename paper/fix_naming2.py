r"""Naming instead of pointing, batch 2.

The remaining pointing constructions, after the ellipses of batch 1.  Most
of the twenty-five "the one"s are ordinary restrictive relatives ("the one
below it", "the one followed from here on") and are left alone; what is
fixed here is the handful where a pro-form stands in for a noun the reader
has to go and fetch.

  1. "What a masked model does supply is THE THING $\Delta$ was standing
     in for."  The thing has a name two pages earlier and in the section
     this sentence points at: $\sigma$.

  2. "Eq. (3) is not of THIS FORM."  The form is the one Eq.
     (anybijection) has just defined -- a score against the image of a
     bijection.  The sentence after explains it; the sentence itself can
     say it.

  3. "We supply a zero from an exact symmetry of ANOTHER KIND."  The kind
     is named two paragraphs later and in the subtitle: an antisymmetry of
     the permutation set.

  4. "selecting THE OTHER ONE is a different measurement."  The other one
     is the causal group, named in the sentence before as one of the two
     label groups.

  5. "nor the saturation of a component defined on THE OTHER ONE."  Same
     pair, same fix.

  6. "Section 3.3 supplies ONE by another route."  "one" is an origin,
     three words back, and "another route" is the antisymmetry.

Each replacement is wording the paper already uses elsewhere.  And, after
batch 1 put a fresh pro-form ("come from one") into a patch whose purpose
was to remove them, this one ends by scanning its own replacement text for
new pronouns, demonstratives and bare modals.  The scan is at the bottom
and runs on every application.

Run:  python fix_naming2.py <paper dir>
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
    r"""What a masked model does supply is the thing $\Delta$ was standing in for.""",
    r"""What a masked model does supply is $\sigma$, the quantity $\Delta$ was
standing in for.""",
    "1: the thing is named")

rep("main.tex",
    r"""Equation~\eqref{eq:fb} is not of this form, which is the reason it needs a
different class of evaluator.""",
    r"""Equation~\eqref{eq:fb} is not a score against the image of a bijection,
which is the reason it needs a different class of evaluator.""",
    "2: the form is stated instead of pointed at")

rep("main.tex",
    r"""We supply a zero from an exact symmetry of another kind.  Score a text's $n$""",
    r"""We supply a zero from an exact antisymmetry of the permutation set
instead.  Score a text's $n$""",
    "3: the kind of symmetry is named")

rep("main.tex",
    r"""selecting the other one is a different measurement: with the two labels""",
    r"""selecting the causal group instead is a different measurement: with the
two labels""",
    "4: the other group is named")

rep("sec_decomp.tex",
    r"""difference between the two groups, nor the saturation of a component
defined on the other one.""",
    r"""difference between the two groups, nor the saturation of a component
defined on the non-causal group.""",
    "5: the other group is named")

rep("main.tex",
    r"""comparison therefore has no origin; Section~\ref{sec:blkord} supplies one by another route, and""",
    r"""comparison therefore has no origin; Section~\ref{sec:blkord} supplies an
origin by the antisymmetry instead, and""",
    "6: what is supplied, and by what, are both named")

# ------------------------------------------------------------------
# The check batch 1 did not have.  A patch whose purpose is to remove
# pro-forms must not introduce them: batch 1 replaced "a joint" with
# "one" in two places and nothing noticed until a reader asked what
# "one" meant.
SUSPECT = re.compile(
    r"\b(?:the one|the ones|that kind|this kind|that form|this form|"
    r"of that|of this|the thing|in this sense|the other one|"
    r"need not\b(?!\s+\w)|does not\.|do not\.|cannot\.)",
    re.I)
bad = [(lab, m.group(0)) for lab, b in WROTE for m in SUSPECT.finditer(b)]
if bad:
    print("\n  !! replacement text contains new pointing constructions:")
    for lab, hit in bad:
        print("     %-40s %r" % (lab, hit))
    raise SystemExit("fix the replacements before shipping this patch")
print(f"done: {N} edits (replacement text clean)")
