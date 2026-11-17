r"""count_ar.py counted Section 6 six times, so the three budgets are loose.

count_ar.py expanded \input and stripped comments afterwards.  Line 6 of
sec_truesigma.tex is a note to a human:

    % \input{sec_truesigma} after Section "Results II".

It is a comment, and a comment is invisible to LaTeX.  It was not invisible
to count_ar.py, which saw an \input, pulled sec_truesigma.tex in, found the
same comment again inside it, and went round five more times before the
depth limit stopped it.  That is where "expanded source: 280,511 chars"
came from.  The paper is 146,543.

check_paper.py does it the other way round -- strip_comments first, expand
second -- so its own counts never saw those copies.  The budgets fix_ar05
froze were therefore set from a string with six Section 6s in it and are
being compared against a string with one.  They pass, and they would pass
through a great deal more.  A budget that cannot fail is the same as no
budget, which is what count_ar.py's own docstring said it was there to
prevent.

The shape of the mistake is the one this paper keeps finding: a number
produced by one reading of the source, used to guard another reading of the
source, with nothing checking that the two readings agree.

This script expands the way check_paper.py expands, and prints what the
three budgets should be.  It writes nothing.

Run:  python3 count_ar2.py .
"""
import importlib.util
import io
import os
import re
import sys
from collections import Counter

os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")

spec = importlib.util.spec_from_file_location("cp", "check_paper.py")
cp = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(cp)
except SystemExit:
    pass

for need in ("AMBIGUOUS_NOUNS", "BARE_NOUN_BUDGET", "SPELLED_COUNT_BUDGET",
             "COMPARATIVE_BUDGET"):
    if not hasattr(cp, need):
        sys.exit("check_paper.py has no %s; apply fix_ar04 and fix_ar05 first"
                 % need)


def expand(text, depth=0):
    """check_paper.py's own order: comments out, then \\input in."""
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


raw = io.open("main.tex", encoding="utf-8").read()
src = expand(cp.strip_comments(raw))
naive = len(re.sub(r"\\input\{([^}]*)\}", "", raw))
print("expanded as check_paper.py does it: %d chars" % len(src))
print("count_ar.py reported:               280511 chars\n")

flat = re.sub(r"\s+", " ", src)

print("bare definite + ambiguous noun      real  frozen")
tot = 0
for noun in cp.AMBIGUOUS_NOUNS:
    pat = r"\bthe %s\b(?!\s+(?:%s))" % (noun, "|".join(cp.NOUN_QUALIFIERS))
    n = len(re.findall(pat, flat))
    tot += n
    b = cp.BARE_NOUN_BUDGET.get(noun)
    print("  %-32s %4d  %4s%s"
          % (noun, n, b, "   <-- loose" if b is not None and b > n else ""))
print("  %-32s %4d\n" % ("TOTAL", tot))

pat = r"\b(%s)\s+(?:[a-z-]+\s+){0,2}(%s)\b" % (
    "|".join(cp.COUNT_WORDS), "|".join(cp.COUNT_NOUNS))
hits = [re.sub(r"\s+", " ", m.group(0)).lower()
        for m in re.finditer(pat, flat, re.I)]
print("counts written as words: %d (frozen at %d)"
      % (len(hits), cp.SPELLED_COUNT_BUDGET))
for p, n in Counter(hits).most_common():
    print("    %2d  %s" % (n, p))

c = []
for sent in cp.prose_sentences(src):
    if re.search(r"\b(?:than|against|compared|relative to|versus)\b", sent, re.I):
        continue
    m = re.search(r"\bmore (?:often|frequently)\b"
                  r"|\b(?:higher|larger|smaller|lower|further|greater)\b",
                  sent, re.I)
    if m:
        c.append(sent[:120])
print("\ncomparatives with no baseline: %d (frozen at %d)"
      % (len(c), cp.COMPARATIVE_BUDGET))

print("\n----- paste these three lines back -----")
print("BARE_NOUN_BUDGET = {")
items = []
for noun in cp.AMBIGUOUS_NOUNS:
    pat = r"\bthe %s\b(?!\s+(?:%s))" % (noun, "|".join(cp.NOUN_QUALIFIERS))
    items.append('"%s": %d' % (noun, len(re.findall(pat, flat))))
print("    " + ", ".join(items[:4]) + ",")
print("    " + ", ".join(items[4:]) + ",")
print("}")
print("SPELLED_COUNT_BUDGET = %d" % len(hits))
print("COMPARATIVE_BUDGET = %d" % len(c))
