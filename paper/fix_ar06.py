r"""Put the three budgets back to what the paper has.

fix_ar04 froze them at 59 / 17 / 14, counted from a concatenation of the
.tex files.  fix_ar05 raised them to 79 / 37 / 19 and said in its own
docstring that the seeds "were too low everywhere".  They were not.  They
were right, and the number that said otherwise came from count_ar.py, which
expanded \input before stripping comments and so pulled sec_truesigma.tex
in six times over a commented-out line.

count_ar2.py, expanding the way check_paper.py expands, reports exactly
fix_ar04's numbers:

    bare definite + ambiguous noun     59
    counts written as words            17
    comparatives with no baseline      14

So the rule this project states -- lower a budget when a site is fixed,
never raise one to make a build pass -- was broken by the patch that said
it.  The build has been passing since with 20 bare definites, 20 spelled
counts and 5 comparatives of slack, which is the same as not checking.

This puts the three back.  Nothing in the paper changes; the checks get
their teeth back, and the next new site fails the build as it should.

The inventory is 90 sites, not 135.  Each is a place a reader supplies
something the sentence does not give, and each comes down as the sections
are rendered into Japanese and read back.

Two new shapes turned up while Section 1 was being rendered, and this
script only COUNTS them, because a budget has to be frozen at a number
someone has seen:

  * "the choice" -- Section 1 says "gives the one fact that settles the
    choice" and the choice is not stated.  Same shape as "the quantity".

  * "both readings" -- Section 1 uses "reading" for the two reversals,
    three sentences after using it for the thermodynamic reading.  The
    abstract says "both reversals" for the same claim, so the paper
    already has the right word in one of the two places.
    check_bare_definite's "reading": 0 only sees "the reading".

Run:  python fix_ar06.py <paper dir>
"""
import importlib.util
import io
import os
import re
import sys

os.chdir(sys.argv[1])
N = 0


def rep(path, a, b, label):
    global N
    assert a not in b, f"{label}: b contains a"
    s = io.open(path, encoding="utf-8").read()
    if s.count(a) == 0 and s.count(b) >= 1:
        print(f"  (already) {label}")
        return
    assert s.count(a) == 1, f"{label}: {s.count(a)} in {path}"
    io.open(path, "w", encoding="utf-8").write(s.replace(a, b))
    print(f"  {label}")
    N += 1


rep("check_paper.py",
    """BARE_NOUN_BUDGET = {
    "quantity": 21, "labels": 9, "measurement": 26, "comparison": 2,
    "reading": 0, "distance": 3, "statistic": 9, "contrast": 9,
}""",
    """# Counted on main.tex with its \\input files expanded AFTER comments are
# stripped, which is the string check_paper.py itself checks.  A count made
# the other way round expands a commented-out \\input and inflates this by
# half; that is where 79 came from, and 79 made the rule unable to fail.
BARE_NOUN_BUDGET = {
    "quantity": 16, "labels": 9, "measurement": 11, "comparison": 2,
    "reading": 0, "distance": 3, "statistic": 9, "contrast": 9,
}""",
    "1: 79 -> 59, the number the paper has")

rep("check_paper.py",
    "SPELLED_COUNT_BUDGET = 37",
    "SPELLED_COUNT_BUDGET = 17",
    "2: 37 -> 17")

rep("check_paper.py",
    "COMPARATIVE_BUDGET = 19",
    "COMPARATIVE_BUDGET = 14",
    "3: 19 -> 14")

print(f"done: {N} edits")

# ------------------------------------------------- count, do not yet freeze
spec = importlib.util.spec_from_file_location("cp", "check_paper.py")
cp = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(cp)
except SystemExit:
    pass


def expand(text, depth=0):
    if depth > 5:
        return text
    def sub(mo):
        f = mo.group(1)
        for cand in (f, f + ".tex"):
            if os.path.isfile(cand):
                return expand(cp.strip_comments(
                    io.open(cand, encoding="utf-8").read()), depth + 1)
        return ""
    return re.sub(r"\\input\{([^}]*)\}", sub, text)


flat = re.sub(r"\s+", " ",
              expand(cp.strip_comments(
                  io.open("main.tex", encoding="utf-8").read())))

print()
print("  two shapes Section 1 turned up, counted but not yet frozen:")

pat = r"\bthe choice\b(?!\s+(?:%s))" % "|".join(cp.NOUN_QUALIFIERS)
hits = [flat[max(0, m.start() - 70):m.end() + 70]
        for m in re.finditer(pat, flat)]
print('    bare "the choice": %d' % len(hits))
for h in hits:
    print("        ...%s..." % h)

pat = r"(?<!ensemble )(?<!fixed-text )\breadings?\b"
hits = [flat[max(0, m.start() - 70):m.end() + 70]
        for m in re.finditer(pat, flat)]
print('    "reading" not preceded by ensemble/fixed-text: %d' % len(hits))
for h in hits:
    print("        ...%s..." % h)
