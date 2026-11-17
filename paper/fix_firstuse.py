r"""The name, glossed where a reader first meets it in the body.

fix_readings.py introduced "the fixed-text reading" and defined it in the
Section 2.2 display.  Section 1 then uses it two pages earlier, bare: no
gloss, no pointer.  That is the ceiling-free defect, committed in a patch
written an hour after diagnosing it, which is a fair measure of how little
the diagnosis protects anyone by itself.

The abstract's use is glossed in place ("on texts prepared by other
models"), so the body's first use is the one that needed fixing.  It gets
the gloss and the cross-reference, and the sentence splits rather than
growing past the length budget, which has no headroom.

Run:  python fix_firstuse.py <paper dir>
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


rep("sec_intro.tex",
    r"""first is a question about what the entropy production of
Ref.~\cite{sagawa2026} means in its fixed-text reading, and answering it
needs a comparison whose zero holds on that text --- which the model class
Ref.~\cite{sagawa2026} uses cannot supply.""",
    r"""first is a question about what the entropy production of
Ref.~\cite{sagawa2026} means in its fixed-text reading: the setting in
which the text was produced by another model
(Section~\ref{sec:notareversal}).  Answering it needs a comparison whose
zero holds on that text, which the model class Ref.~\cite{sagawa2026} uses
cannot supply.""",
    "the body's first use says what the name means")


def _budget_shapes():
    try:
        src = io.open("check_paper.py", encoding="utf-8").read()
        m = re.search(r"ELLIPSIS_SHAPES = \{.*?\n\}", src, re.S)
        ns = {}
        exec(m.group(0), ns)
        return ns["ELLIPSIS_SHAPES"]
    except Exception as exc:
        print(f"  (no shape self-scan: {exc})")
        return {}


shaped = []
for _name, (_pat, _budget) in sorted(_budget_shapes().items()):
    for _lab, _b in WROTE:
        for _m in re.finditer(_pat, re.sub(r"\s+", " ", _b)):
            shaped.append((_name, _lab, _m.group(0)))
if shaped:
    print("\n  !! replacement text uses shapes the build budgets:")
    for _name, _lab, _hit in shaped:
        print("     %-34s %-30s %r" % (_name, _lab[:28], _hit))

SUSPECT = re.compile(
    r"\bthe ones?\s*(?=[.,;:]|\b(?:that|which|it|we|they|the|is|are)\b)|"
    r"\bof (?:that|this)\s*(?=[.,;:]|\b(?:is|are|was|were|and|or|we|it|they)\b)|"
    r"\b(?:that kind|this kind|a kind|that form|this form|"
    r"the thing|in this sense|this reading|the other one|"
    r"such a|that of|need not\b(?!\s+\w)|does not\.|do not\.|cannot\.|"
    r"\bis of the\b|\bis of a\b|\band not of\b|\bbut not of\b)", re.I)
bad = [(lab, m.group(0)) for lab, b in WROTE for m in SUSPECT.finditer(b)]
if bad:
    print("\n  !! replacement text contains new pointing constructions:")
    for lab, hit in bad:
        print("     %-40s %r" % (lab, hit))
    raise SystemExit("fix the replacements before shipping this patch")
print(f"done: {N} edits (replacement text clean)")
