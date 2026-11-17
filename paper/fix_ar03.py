r"""One object, three names, and a fourth phrase that means something else.

The five autoregressive evaluators in order of parameter count are called
"the ladder" 51 times, "the autoregressive ladder" 6 times and "the $\Delta$
ladder" once.  Every one of the 58 refers to the same five evaluators; there
is no masked ladder and no toy ladder, so the rename is safe to do by rule.

The reason to do it is not tidiness.  Two different axes are described with
phrases one word apart:

    higher up the range   -- a high midrank, within one text's n! values
    higher up the ladder  -- a large evaluator, across the five

A reader who swaps them reads a statement about model size as a statement
about where in a distribution it was read, which is the distinction
Section 5.4 is built on.  Putting AR in the name of one of them makes the
pair visibly different, and the author asked for it after being unable to
tell, from the name alone, whether masked evaluators were in the ladder.

Run:  python fix_ar03.py <paper dir>
"""
import glob
import io
import os
import re
import sys

os.chdir(sys.argv[1])

FILES = sorted(glob.glob("*.tex"))
before = {f: io.open(f, encoding="utf-8").read() for f in FILES}

if any("AR ladder" in s for s in before.values()):
    print("  (already) ladder is already AR ladder somewhere; nothing done")
    raise SystemExit(0)

total = {}
for f, s in before.items():
    n0 = len(re.findall(r"\bladder\b", s))
    if not n0:
        continue
    # 1. the qualified forms collapse first, so the bare rule cannot
    #    double-qualify them into "autoregressive AR ladder".
    s = s.replace("autoregressive ladder", "AR ladder")
    s = re.sub(r"\$\\Delta\$\s*\n?\s*ladder", "AR ladder", s)
    # 2. every remaining bare ladder, including possessives and compounds
    #    ("ladder order", "the ladder's top rung").
    s = re.sub(r"(?<!AR )\bladder\b", "AR ladder", s)
    # 3. the article that the new initial sound changes
    s = re.sub(r"\ba AR ladder\b", "an AR ladder", s)
    s = re.sub(r"\bA AR ladder\b", "An AR ladder", s)
    io.open(f, "w", encoding="utf-8").write(s)
    total[f] = (n0, len(re.findall(r"\bAR ladder\b", s)))

for f, (a, b) in total.items():
    print(f"  {f}: {a} ladder -> {b} AR ladder")

# 4. the abbreviation is stood up once, at its first use in the abstract,
#    so that a reader meeting "the AR ladder" in Section 5 has been told
#    what AR is without having to find it in a table.
s = io.open("main.tex", encoding="utf-8").read()
anchor = r"""the decomposition runs across an AR ladder of
\TrendNEval\ evaluators"""
if "autoregressive (AR) ladder" in s:
    print("  (already) the abbreviation is introduced")
elif anchor in s:
    s = s.replace(anchor, r"""the decomposition runs across an autoregressive
(AR) ladder of \TrendNEval\ evaluators""")
    io.open("main.tex", "w", encoding="utf-8").write(s)
    print("  main.tex: AR introduced at its first use in the abstract")
else:
    print("  !! could not find the abstract's first use; introduce AR by hand")

left = sum(len(re.findall(r"(?<!AR )\bladder\b", io.open(f, encoding="utf-8").read()))
           for f in FILES)
print(f"done: {sum(a for a, _ in total.values())} renamed, {left} bare ladder left")
