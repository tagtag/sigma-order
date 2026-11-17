r"""$\sigma'$ is used twice and defined nowhere.

    main.tex:333  "... and $\sigma'$ is a function on sequence space"
    main.tex:386  "Its $\sigma'(x) = 0$ is a measurement outcome"

Both mean Ref. [1]'s quantity, which this paper calls \Dblock -- and both
break the naming rule Section 2.1 states in as many words: "this paper
reserves $\sigma$ for Eq. (3), which is a different quantity on a different
model class; a statement made about $\sigma$ here is never a statement
about $\sigma_{block}$ there".  A sigma-shaped symbol standing for Ref.
[1]'s quantity is the one thing that paragraph exists to prevent, and a
reader meeting $\sigma'$ has no definition to go to.

Left over from the revision in which Section 2.2 was rebuilt: $\sigma'$ was
the working name there before the $\Delta$/$\sigma$ split was settled.

Both become \Dblock, which is what the surrounding sentences are about: at
333 the function on sequence space whose support condition was just
discussed, at 386 the quantity of Ref. [1] named in the sentence before.

The glossary gains the ban, so the working name cannot come back: a symbol
is a term like any other, and this one has a definition-free past.

Run:  python fix_sigmaprime.py <paper dir>
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
    r"""Ref.~\cite{sagawa2026} states for its theorem is met, and $\sigma'$ is a function on
sequence space, which Ref.~\cite{sagawa2026} reads at the level of a single""",
    r"""Ref.~\cite{sagawa2026} states for its theorem is met, and $\Dblock$ is a
function on
sequence space, which Ref.~\cite{sagawa2026} reads at the level of a single""",
    "1: the function on sequence space is named")

rep("main.tex",
    r"""kind on a single text.  Its $\sigma'(x) = 0$ is a measurement outcome ---""",
    r"""kind on a single text.  Its $\Dblock(x) = 0$ is a measurement outcome ---""",
    "2: the zero belongs to the quantity the sentence before names")

CHECK = '''def check_sigma_prime(src):
    """No sigma-shaped symbol stands for Ref. [1]'s quantity.

    Section 2.1 states the rule -- "this paper reserves $\\sigma$ for
    Eq. (3) ... a statement made about $\\sigma$ here is never a statement
    about $\\sigma_{block}$ there" -- and $\\sigma\'$ broke it twice, with
    no definition anywhere, left over from the revision in which Section
    2.2 was rebuilt.

    Not a glossary rule: glossary.txt matches on word boundaries, so a
    term beginning with a backslash can be written there and never fire,
    which is worse than not writing it.
    """
    for form in (r"\\sigma\'", r"\\sigma^{\\prime}", r"\\sigma^\\prime"):
        n = src.count(form)
        if n:
            fail("notation",
                 "%s appears %dx: a sigma-shaped symbol for Ref. [1]'s "
                 "quantity is what Section 2.1 forbids, and this one has "
                 "no definition.  It is written \\Dblock here." % (form, n))


def check_quantities(src, tables_dir):'''

SELFTEST = '''check_corpus_order_rule()


def check_sigma_prime_rule():
    """The working name must not come back."""
    import check_paper as C
    for s in (r"and $\\sigma\'$ is a function",
              r"its $\\sigma^{\\prime}(x) = 0$ is a measurement"):
        C.FAIL[:] = []
        C.check_sigma_prime(s)
        assert C.FAIL, s
    C.FAIL[:] = []
    C.check_sigma_prime(r"the quantity $\\Dblock$ is a function")
    assert not C.FAIL, [m for _, m in C.FAIL]
    del C.WARN[:]
    print("  catch: a sigma-shaped symbol standing for Ref. [1]'s quantity")


check_sigma_prime_rule()
'''

rep("check_paper.py",
    "def check_quantities(src, tables_dir):",
    CHECK,
    "3: the ban lives where it can fire",
    marker="def check_sigma_prime")

rep("check_paper.py",
    "    check_corpus_order(args.tables)",
    "    check_corpus_order(args.tables)\n"
    "    check_sigma_prime(src)",
    "4: invoked",
    marker="check_sigma_prime(src)\n")

rep("check_paper_selftest.py",
    "\ncheck_corpus_order_rule()\n",
    "\n" + SELFTEST,
    "5: its selftest",
    marker="check_sigma_prime_rule")

print(f"done: {N} edits")
