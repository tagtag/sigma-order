r"""The last known-shape site, and a budget so the shapes cannot come back.

Nine shapes of ellipsis and deixis were found over one reading session,
each one by a reader stopping at it.  Run over the whole paper they give
80 sites, of which 79 are legitimate -- parallels with both arms present,
restrictive relatives, idioms, colons that supply what was elided -- and
one is not:

    "The second of those three, the labelling, is of a different kind,
     and Ref. [1] says it of its own corpora before we do."

"those three" are named 160 lines earlier, and the paragraph in between
names TWO reasons, so a reader resolving locally resolves wrongly.  "of a
different kind" does not say different how, and "says it" elides what is
said.  All three are supplied from the paper's own contrast: the first
question gets "a statement about the quantity rather than about these
corpora".

THE BUDGET.  Every patch written today introduced a fresh instance of one
of these shapes -- "come from one", "both quantities" -- and the self-scan
added after the first could only catch shapes already on the list.  The
real fix is not a better self-scan but a count the build enforces: the
number of sites of each shape is frozen here, and check_paper fails if any
count rises.  A legitimate new sentence that trips it is a one-line
baseline edit with a reason; an accidental one is caught before a reader
has to find it.

It does not catch a NEW shape.  Nothing can, until someone stops at one --
and then the shape joins the list and never costs a reader twice.

Run:  python fix_ellipsis_check.py <paper dir>
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


# ------------------------------------------------------- the last site
rep("sec_intro.tex",
    r"""The second of those three, the labelling, is of a different kind, and
Ref.~\cite{sagawa2026} says it of its own corpora before we
do~\cite[Sec.~V~B]{sagawa2026}.""",
    r"""The labelling is a question about the corpora rather than about the
quantity, and Ref.~\cite{sagawa2026} raises it about its own corpora before
we do~\cite[Sec.~V~B]{sagawa2026}.""",
    "1: which three, different how, and what is said")

# ------------------------------------------------------- the budget
CHECK = '''ELLIPSIS_SHAPES = {
    # shape -> (pattern, budget).  The budget is the number of sites that
    # survived a reading in which every one of these shapes was found by a
    # reader stopping at it.  Those survivors are legitimate: parallels
    # with both arms present, restrictive relatives, idioms, and colons
    # that supply what was elided.  A count that RISES is a new instance,
    # and new instances have come from patches, not from drafting.
    "possessive with the noun elided":
        (r"\\b[a-z]+'s (?=(?:need|do|does|is|are|was|were|can|cannot|will|"
         r"would|must|has|have)\\b)", 0),
    "modal with the verb elided":
        (r"\\b(?:need not|does not|do not|cannot|can|could|would|did)[.,;:]", 8),
    "predicate with the head noun elided":
        (r"\\bis (?:not )?of (?:the|a|an|its|their)\\b", 1),
    "ordinal used as a noun":
        (r"\\bthe (?:first|second|third|former|latter)(?:'s)?\\b"
         r"(?! \\w+ (?:of|in|is a))", 18),
    "bare both / one / ones":
        (r"\\bboth\\b(?! [a-z])|\\bthe ones?\\b(?! of the)", 28),
    "deictic kind / form / sense":
        (r"\\bof (?:that|this) kind\\b|\\bin (?:this|that) sense\\b|"
         r"\\b(?:that|this) form\\b|\\bof a kind\\b", 1),
    "demonstrative + abstract noun":
        (r"\\b(?:that|this|these|those) (?:identity|difference|distinction|"
         r"quantity|comparison|contrast|construction|reading|claim|argument|"
         r"fact|point|step|route|side|choice|zero|origin|separation|account|"
         r"part)\\b", 19),
    "'such a X'":
        (r"\\bsuch (?:a|an) [a-z]+\\b", 4),
    "stand-in noun":
        (r"\\b(?:a|the) (?:thing|notion|object)\\b", 0),
}


def check_ellipsis_budget(src):
    """Ellipsis and deixis: a frozen count per shape, not a per-site list.

    Nine shapes, each found by a reader stopping at it.  What the reader
    could not do was find the ones further on, and what the patches that
    fixed them kept doing was introduce fresh ones -- "come from one" for
    "come from a joint", "both quantities" for "both reversals".  A
    self-scan inside a patch only knows the shapes already on the list, so
    the count is enforced here instead, over the whole paper, at build
    time.

    Raising a budget is fine when a new sentence genuinely needs the
    construction; the point is that it is a decision someone makes, not a
    thing that happens.
    """
    body = re.sub(r"\\\\begin\\{(table|figure|tabular|center)\\*?\\}.*?"
                  r"\\\\end\\{\\1\\*?\\}", " ", src, flags=re.S)
    flat = re.sub(r"\\s+", " ", body)
    for name, (pat, budget) in sorted(ELLIPSIS_SHAPES.items()):
        hits = re.findall(pat, flat)
        if len(hits) > budget:
            fail("ellipsis",
                 "%s: %d sites, budget %d.  Either name what the new one "
                 "elides, or raise the budget in ELLIPSIS_SHAPES with a "
                 "reason." % (name, len(hits), budget))


def check_quantities(src, tables_dir):'''

rep("check_paper.py",
    "def check_quantities(src, tables_dir):",
    CHECK,
    "2: the budget check",
    marker="def check_ellipsis_budget")

rep("check_paper.py",
    "    check_sigma_prime(src)",
    "    check_sigma_prime(src)\n    check_ellipsis_budget(src)",
    "3: invoked",
    marker="check_ellipsis_budget(src)\n")

print(f"done: {N} edits")
