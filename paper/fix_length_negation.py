r"""Two more shapes in the build: sentence length, and nested negation.

Both were found the same way as the first nine -- a reader stopped at one.

LENGTH.  656 sentences, median 26 words.  The distribution is fine; the
tail is not.  123 run over 40 words, 54 over 50.  Length alone is not the
defect -- some are long because they carry a list of generated numbers,
and splitting those gains nothing -- but every sentence a reader has
stopped at today was in the tail.  The budget is set at the current count
over 50 words, so it cannot grow, and comes down as the tail is worked
through.

NESTED NEGATION.  "a text the evaluator did not produce is not a draw from
that distribution": a negation inside the subject, then a negated main
verb, with nothing between them to mark the boundary.  The reader has to
resolve both scopes at once.

The count matters less than the shape.  Five sentences carry two
negations within seventy characters, and all five are coordinations --
"their lengths are not controlled, AND the non-causal passages are not
incoherent" -- where the comma and conjunction do the work.  Requiring no
break between the two leaves zero sites, which is the right budget: the
one that existed has been fixed, and the next one will be caught.

Neither check can say whether a long sentence or a negation is EARNED.
That stays a judgement.  What they do is make the decision happen at build
time instead of in a reader's head twenty pages later.

Run:  python fix_length_negation.py <paper dir>
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


CHECK = '''def prose_sentences(src):
    """The body text as sentences, with floats, maths and macros removed."""
    t = re.sub(r"\\\\begin\\{(table|figure|equation|align|tabular|center)\\*?\\}"
               r".*?\\\\end\\{\\1\\*?\\}", " ", src, flags=re.S)
    t = re.sub(r"\\\\caption\\{[^{}]*(\\{[^{}]*\\}[^{}]*)*\\}", " ", t)
    t = re.sub(r"\\$[^$]*\\$", " X ", t)
    t = re.sub(r"\\\\[a-zA-Z]+\\*?(\\[[^\\]]*\\])?(\\{[^{}]*\\})?", " ", t)
    t = re.sub(r"\\s+", " ", t)
    return [s.strip() for s in re.split(r"(?<=[.!?]) (?=[A-Z])", t)
            if 3 < len(s.split()) < 200]


SENTENCE_WORDS = 50
SENTENCE_BUDGET = 54


def check_sentence_length(src):
    """How many sentences run past SENTENCE_WORDS.

    The median is 26 and the distribution is healthy; what a reader stops
    at is the tail.  Length is not itself the defect -- a sentence can be
    long because it lists generated numbers -- so this is a budget and not
    a ban: it cannot grow, and it comes down as the tail is split.
    """
    long = [s for s in prose_sentences(src) if len(s.split()) > SENTENCE_WORDS]
    if len(long) > SENTENCE_BUDGET:
        worst = max(long, key=lambda s: len(s.split()))
        fail("length",
             "%d sentences over %d words, budget %d.  Longest is %d words: "
             "%s..." % (len(long), SENTENCE_WORDS, SENTENCE_BUDGET,
                        len(worst.split()), worst[:120]))


NESTED_NEGATION = re.compile(
    r"\\b(?:did|does|do|could|can|would|will|has|have)\\s+not\\s+"
    r"(?:[a-z]+\\s+){0,6}?(?:is|are|was|were)\\s+not\\b", re.I)


def check_nested_negation(src):
    """A negation inside the subject, then a negated main verb.

    "a text the evaluator did not produce is not a draw from that
    distribution" asks the reader to hold two scopes at once.  The pattern
    requires no comma, dash or conjunction between the two negations, so
    ordinary coordination -- "their lengths are not controlled, and the
    non-causal passages are not incoherent" -- does not trip it.
    """
    t = re.sub(r"\\s+", " ", src)
    for m in NESTED_NEGATION.finditer(t):
        fail("negation",
             "a negated clause inside a negated clause: ..."
             + t[max(0, m.start() - 60):m.end() + 40] + "...")


def check_quantities(src, tables_dir):'''

rep("check_paper.py",
    "def check_quantities(src, tables_dir):",
    CHECK,
    "1: the two checks",
    marker="def check_sentence_length")

rep("check_paper.py",
    "    check_ellipsis_budget(src)",
    "    check_ellipsis_budget(src)\n"
    "    check_sentence_length(src)\n"
    "    check_nested_negation(src)",
    "2: invoked",
    marker="\n    check_nested_negation(src)")

print(f"done: {N} edits")
