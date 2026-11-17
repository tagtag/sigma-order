r"""What the three new rules actually count, and where Table 2 stands.

The budgets in check_paper.py were seeded from a concatenation of the .tex
files.  check_paper.py reads main.tex with its \input files expanded, which
is not the same string, so the frozen numbers may be loose.  A budget that
is loose is a budget that catches nothing.

This prints the real counts so they can be set to what the paper has, and
prints Table 2's caption so the float warning can be decided rather than
silenced.

Run:  python3 count_ar.py .
"""
import importlib.util
import io
import os
import re
import sys

os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")

spec = importlib.util.spec_from_file_location("cp", "check_paper.py")
m = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(m)
except SystemExit:
    pass


def expand(path, depth=0):
    s = io.open(path, encoding="utf-8").read()
    if depth > 5:
        return s

    def sub(mo):
        f = mo.group(1)
        for cand in (f, f + ".tex"):
            if os.path.isfile(cand):
                return expand(cand, depth + 1)
        return ""
    return re.sub(r"\\input\{([^}]*)\}", sub, s)


src = expand("main.tex")
flat = re.sub(r"\s+", " ", m.strip_comments(src))
print("expanded source: %d chars\n" % len(src))

print("bare definite + ambiguous noun          count  budget")
tot = 0
for noun in m.AMBIGUOUS_NOUNS:
    pat = r"\bthe %s\b(?!\s+(?:%s))" % (noun, "|".join(m.NOUN_QUALIFIERS))
    n = len(re.findall(pat, flat))
    tot += n
    print("  %-36s %4d  %4s" % (noun, n, m.BARE_NOUN_BUDGET.get(noun)))
print("  %-36s %4d\n" % ("TOTAL", tot))

pat = r"\b(%s)\s+(?:[a-z-]+\s+){0,2}(%s)\b" % (
    "|".join(m.COUNT_WORDS), "|".join(m.COUNT_NOUNS))
hits = [re.sub(r"\s+", " ", x.group(0)).lower() for x in re.finditer(pat, flat, re.I)]
print("counts written as words: %d (budget %d)" % (len(hits), m.SPELLED_COUNT_BUDGET))
from collections import Counter
for p, n in Counter(hits).most_common():
    print("    %2d  %s" % (n, p))

print()
c = 0
for sent in m.prose_sentences(src):
    if re.search(r"\b(?:than|against|compared|relative to|versus)\b", sent, re.I):
        continue
    if re.search(r"\bmore (?:often|frequently)\b"
                 r"|\b(?:higher|larger|smaller|lower|further|greater)\b",
                 sent, re.I):
        c += 1
print("comparatives with no baseline in the sentence: %d (budget %d)"
      % (c, m.COMPARATIVE_BUDGET))

print("\n--- Table 2: where it is declared and what it says ---")
whole = expand("main.tex")
for mo in re.finditer(r"\\begin\{table\*?\}(\[[^\]]*\])?", whole):
    seg = whole[mo.start():mo.start() + 2600]
    cap = re.search(r"\\caption\{(.{0,160})", seg, re.S)
    lab = re.search(r"\\label\{([^}]*)\}", seg)
    print("  %-10s %-26s %s" % (mo.group(1) or "[]",
                                lab.group(1) if lab else "?",
                                re.sub(r"\s+", " ", cap.group(1))[:110] if cap else ""))
