r"""Four checks for the four shapes a Japanese rendering kept stopping at.

The abstract was rendered into Japanese one sentence at a time, because the
author cannot read the English closely enough to check it.  Rendering is a
harsher reader than proofreading: it will not let a pointer through without
a referent, a count through without a noun, or a comparative through
without the thing compared.  Seventeen sentences could not be rendered, and
three of those were wrong rather than merely unclear.

The shapes repeat, so three of them get a rule.  Each is an allow-list, the
form that has worked in this file before: the expected sites are named and
silent, anything new speaks up.

  ONE.  A definite article on an abstract noun this paper uses for more
  than one thing.  "the quantity" appears 18 times and the paper has
  three; "the labels", "the measurement", "the comparison" the same.  This
  is check_bare_floor generalised from one noun to the family.

  TWO.  A count written as a word.  "for three masked evaluators" stood in
  Section 3.2 while results_pll/ held two, and no check could see it:
  check_macros compares macros, and "three" is not one.  check_step_gap
  already says this in its docstring -- "written as a word, the number was
  outside everything that checks numbers" -- and the same hole swallowed a
  second number.

  THREE.  A comparative with no stated baseline.  "the causal group reaches
  it +13 to +22 points more often" -- more often than what?  The answer is
  the non-causal group and the sentence does not say so.

  FOUR.  A count that is a product of two others.  \ContrastNCells is 25
  because five evaluators meet five corpora, and nothing checked that it
  still is.  fix_ar01 emits the two factors; this multiplies them.

Run:  python fix_ar04.py <paper dir>
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


CHECKS = r'''# Nouns this paper uses for more than one thing, so that a bare definite
# article on one of them asks a reader to pick.  The qualifier list is what
# makes the rule usable: "the quantity of Eq. (1)", "the labels that
# experiment turns on", "the comparison between the two classes" all carry
# their own referent and never match.  A noun is added here when a reader
# asks "which one?"; it is removed when the paper stops having two.
AMBIGUOUS_NOUNS = ("quantity", "labels", "measurement", "comparison",
                   "reading", "distance", "statistic", "contrast")
NOUN_QUALIFIERS = (r"of\b", r"in\b", r"that\b", r"which\b", r"this\b",
                   r"above\b", r"below\b", r"here\b", r"itself\b",
                   r"record\b", r"records\b", r"is\b", r"are\b", r"was\b",
                   r"were\b", r"it\b", r"they\b", r"and\b", r"or\b")
# Frozen at what the build reported when the rule went in, one entry per
# noun, in the project's usual form: the expected case is silent and a
# RISE is loud.  These are not targets to keep.  Every one of the 59 is a
# sentence where a reader picks a referent, and the number comes down as
# the sections are gone through.  Lower an entry when you fix a site;
# never raise one to make a build pass.
BARE_NOUN_BUDGET = {
    "quantity": 16, "labels": 9, "measurement": 11, "comparison": 2,
    "reading": 0, "distance": 3, "statistic": 9, "contrast": 9,
}


def check_bare_definite(src):
    """A definite article on a noun this paper uses for several things.

    check_bare_floor is this rule for one word.  Rendering the abstract
    into Japanese ran into the same shape four more times, and the first
    one the author hit was "the quantity": the paper has Delta, sigma and
    sigma_EP, and the sentence names none of them.

    The budget is not a style limit.  Every site it counts is a sentence
    where a reader has to guess, and the guess is sometimes wrong: the
    abstract's "about the quantity rather than about the corpora" means
    Delta, and a reader who takes it for sigma reads the paragraph
    backwards.
    """
    body = strip_comments(src)
    flat = re.sub(r"\s+", " ", body)
    counts = {}
    first = {}
    for noun in AMBIGUOUS_NOUNS:
        pat = r"\bthe %s\b(?!\s+(?:%s))" % (noun, "|".join(NOUN_QUALIFIERS))
        for m in re.finditer(pat, flat):
            counts[noun] = counts.get(noun, 0) + 1
            first.setdefault(noun, flat[max(0, m.start() - 60):m.end() + 60])
    for noun, n in sorted(counts.items()):
        budget = BARE_NOUN_BUDGET.get(noun)
        if budget is None:
            fail("referent",
                 "bare \"the %s\" %d time(s) and no budget for it; this "
                 "paper uses the word for more than one thing, so name "
                 "which or attach a phrase that does: ...%s..."
                 % (noun, n, first[noun]))
        elif n > budget:
            fail("referent",
                 "bare \"the %s\" %d times, budget %d; a new one is a "
                 "sentence a reader has to guess at: ...%s..."
                 % (noun, n, budget, first[noun]))


# Counts the prose spells out.  Frozen at the build's own number for the
# same reason as the nouns above: the hole that let "three masked
# evaluators" through is open at 17 other sites, and the rule is here to
# stop an 18th while they are worked through.
SPELLED_COUNT_BUDGET = 17
COUNT_WORDS = ("two", "three", "four", "five", "six", "seven", "eight",
               "nine", "ten")
COUNT_NOUNS = ("evaluator", "evaluators", "corpus", "corpora", "cell",
               "cells", "model", "models", "text", "texts", "step",
               "steps", "block", "blocks", "corpora,")


def check_spelled_counts(src):
    """A count of something the tables count, written as a word.

    Section 3.2 said the substitution was run "for three masked
    evaluators".  results_pll/ holds two.  Nothing could see it: the
    number is not a macro, so check_macros never compared it with
    anything, and no table prints a three to disagree with.

    check_step_gap found the same hole once already, on a number spelled
    "thirteen", and wrote the lesson in its own docstring.  This is that
    lesson as a rule.  A spelled count either becomes a macro, or is
    listed here with a reason -- "two label groups" is a definition and
    not a measurement, so it belongs on the list.
    """
    body = strip_comments(src)
    flat = re.sub(r"\s+", " ", body)
    pat = r"\b(%s)\s+(?:[a-z-]+\s+){0,2}(%s)\b" % (
        "|".join(COUNT_WORDS), "|".join(COUNT_NOUNS))
    hits = [re.sub(r"\s+", " ", m.group(0)).lower()
            for m in re.finditer(pat, flat, re.I)]
    if len(hits) > SPELLED_COUNT_BUDGET:
        fail("spelled-count",
             "%d counts written as words, budget %d; a count as a word is "
             "outside everything that checks numbers, which is how "
             "\"three masked evaluators\" stood against data holding two. "
             "Make the new one a macro: %s"
             % (len(hits), SPELLED_COUNT_BUDGET, ", ".join(sorted(set(hits)))))


# Comparatives with no baseline in their own sentence.  Frozen, like the
# two above.  Some of the 14 are fine -- a baseline one sentence back is
# readable -- and some are the shape that hid "more often than what?" in
# the abstract.  They are separated by reading them, not by a regex.
COMPARATIVE_BUDGET = 14


def check_comparison_target(src):
    """A comparative with nothing in the sentence to compare against.

    "the causal group reaches it +13 to +22 points more often as a median
    over corpora" -- more often than the non-causal group, which the
    sentence does not say.  The reader supplies it, and supplies it
    correctly here, which is exactly why the shape survives: it reads
    fine until someone tries to state the claim exactly and finds they
    cannot.

    The rule is narrow on purpose.  It looks only for "more <adverb>" and
    "<adjective>er" in a sentence with no "than", no "against", and no
    "compared", which is the shape that leaves the baseline out
    altogether rather than putting it somewhere awkward.
    """
    hits = []
    for sent in prose_sentences(src):
        if re.search(r"\b(?:than|against|compared|relative to|versus)\b",
                     sent, re.I):
            continue
        m = re.search(r"\bmore (?:often|frequently)\b"
                      r"|\b(?:higher|larger|smaller|lower|further|greater)\b",
                      sent, re.I)
        if not m:
            continue
        hits.append((m.group(0).lower(), sent[:130]))
    if len(hits) > COMPARATIVE_BUDGET:
        fail("comparison",
             "%d comparatives with no baseline in their own sentence, "
             "budget %d; name what the new one is compared with: %s"
             % (len(hits), COMPARATIVE_BUDGET,
                "; ".join(s for _, s in hits[-3:])))


def check_cell_product(tables_dir):
    """A cell count that is a product, against its two factors.

    \\ContrastNCells is 25 because five autoregressive evaluators meet
    five corpora.  The abstract now prints it that way, so the three
    numbers have to agree, and a run that drops a corpus must not leave
    the prose saying otherwise.
    """
    mpath = os.path.join(tables_dir, "macros.tex")
    if not os.path.isfile(mpath):
        return
    gen = newcommands(open(mpath, encoding="utf-8").read())
    for total, a, b in (("ContrastNCells", "ContrastNEval",
                         "ContrastNCorpora"),):
        if not all(k in gen for k in (total, a, b)):
            continue
        try:
            t, x, y = int(gen[total]), int(gen[a]), int(gen[b])
        except ValueError:
            continue
        if t != x * y:
            fail("cells",
                 "\\%s = %d but \\%s x \\%s = %d x %d = %d; the prose "
                 "prints the product, so the three have to agree"
                 % (total, t, a, b, x, y, x * y))


def check_bare_floor(src):'''

rep("check_paper.py", "def check_bare_floor(src):", CHECKS,
    "1: four checks, each an allow-list",
    marker="def check_bare_definite")

rep("check_paper.py",
    """    check_bare_floor(src)
    check_absence_scope(src)""",
    """    check_bare_floor(src)
    check_bare_definite(src)
    check_spelled_counts(src)
    check_comparison_target(src)
    check_cell_product(args.tables)
    check_absence_scope(src)""",
    "2: invoked",
    marker="check_bare_definite(src)")

print(f"done: {N} edits")
print()
print()
print("  The three budgets are frozen at what the paper has now:")
print("    bare definite nouns   59  (quantity 16, measurement 11,")
print("                               labels 9, statistic 9, contrast 9,")
print("                               distance 3, comparison 2)")
print("    counts written as words   17")
print("    comparatives with no baseline in the sentence   14")
print("  So this build passes and the next new one fails.  The numbers")
print("  come down as the sections are rendered; they are never raised.")
