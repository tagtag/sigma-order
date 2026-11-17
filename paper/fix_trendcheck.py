r"""The check that exists to stop this did not cover the pair that got through.

Figure 2's caption says the masked values "rise with capacity rather than
falling".  That is a trend claim on $\rho = +0.90$, $p = 0.083$, and
Section 5.4's rule -- which the body, the appendix and Section 6.3 all
keep -- is that nothing above 0.05 may be given a trend verb.
check_trend_verbs() exists for exactly this.  It missed, for two reasons,
and the second is worse than the first.

ONE.  It pairs a correlation with its $p$ by SUFFIX: \Tag P beside \Tag
Rho.  The pair behind this claim is named \CtrlRhoEP and \CtrlPEP, with
Rho and P infixed before a shared suffix, so "CtrlPEP"[:-1] + "Rho" is
"CtrlPERho", which does not exist, and the pair was never in the weak
list.  Its own docstring says "\CtrlPEP are caught like the rest".  It is
not, and was not.  Pairing by replacing Rho with P covers both
conventions and is the rule the names actually follow.

TWO.  Even paired, it would not have fired: the check requires the
sentence to carry the macro, and the caption states the trend without
quoting the number.  That is the harder half and it has no general rule --
knowing that "it rises" is about $\sigma_{\mathrm{EP}}$ needs the referent.
What it has instead is a list: the few quantities whose trend is not
significant, written as a reader names them.  Seeded with the one that got
through, and honest about being a list.

Run:  python fix_trendcheck.py <paper dir>
"""
import io
import os
import re
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


# ------------------------------------------------------- 1 the pairing rule
rep("check_paper.py",
    '''    for name, body in gen.items():
        if not name.endswith("P") or (name[:-1] + "Rho") not in gen:
            continue
        try:
            if float(body) > 0.05:
                weak.append(name[:-1])
        except ValueError:
            continue                      # still TODO''',
    '''    # Pair by replacing Rho with P, not by stripping a suffix.  The
    # suffix rule read \\TrendCausalRho/\\TrendCausalP and missed
    # \\CtrlRhoEP/\\CtrlPEP, where Rho and P are infixed before a shared
    # suffix -- and the pair it missed is the one behind the trend claim
    # in Figure 2's caption, which stood for two builds while the
    # docstring above said it was covered.
    for name, body in gen.items():
        if "Rho" not in name:
            continue
        pname = name.replace("Rho", "P", 1)
        if pname not in gen:
            continue
        try:
            if float(gen[pname]) > 0.05:
                weak.append((name, pname))
        except ValueError:
            continue                      # still TODO''',
    "1a: pairs are found by the convention the names use")

rep("check_paper.py",
    '''    for sent in re.split(r"(?<=[.!?])\\s+", src):
        for tag in weak:
            if not re.search(r"\\\\%s(?:Rho|P)\\b" % tag, sent):
                continue''',
    '''    for sent in re.split(r"(?<=[.!?])\\s+", src):
        for rname, pname in weak:
            if not re.search(r"\\\\(?:%s|%s)\\b" % (rname, pname), sent):
                continue''',
    "1b: and matched by their own names")

rep("check_paper.py",
    '''            if hit:
                fail("trend",
                     f"\\\\{tag}P is above 0.05 and its sentence says "''',
    '''            if hit:
                fail("trend",
                     f"\\\\{pname} is above 0.05 and its sentence says "''',
    "1c: the message names the macro that exists")

rep("check_paper.py",
    '''    # Any correlation, not only the ones named Trend<X>P.  A p-value macro
    # is one whose name ends in P and has a sibling ending in Rho, so
    # \\\\TailTrendP and \\\\CtrlPEP are caught like the rest.  The first
    # version matched the Trend prefix alone, and "rises too" stood beside
    # \\\\TailTrendP = 0.083 through two builds.''',
    '''    # Any correlation, not only the ones named Trend<X>P.  A correlation
    # macro is one whose name contains Rho and has a sibling with P in the
    # same place, which is the convention every pair here follows.  The
    # first version matched the Trend prefix alone; the second matched a P
    # suffix and silently excluded \\\\CtrlRhoEP/\\\\CtrlPEP, the pair behind
    # the only trend claim that has got past this check.''',
    "1d: and the comment says what the rule is, and what it was")

# -------------------------------------------- 2 claims that cite no number
SUBJ = '''# Quantities whose trend is not significant, written as the prose names
# them rather than as a macro.  check_trend_verbs() anchors on the macro
# being in the sentence, so a claim that states the trend and leaves the
# number to a figure goes straight past it -- which is how "it rises with
# capacity rather than falling" stood in Figure 2's caption.
#
# This is a list and not a rule.  Knowing that "it rises" is about
# sigma_EP needs the referent, and nothing here can supply one.  A new
# entry is a decision someone makes after a reader finds the next escape.
TREND_SUBJECTS = (
    (r"\\\\sigEP\\b|\\bmasked values\\b|\\bmasked rows\\b", "CtrlPEP"),
)


def check_trend_verbs(src, tables_dir):'''

rep("check_paper.py",
    "def check_trend_verbs(src, tables_dir):",
    SUBJ,
    "2a: the quantities a claim can name without quoting",
    marker="TREND_SUBJECTS = (")

rep("check_paper.py",
    '''                     f"or its absence at that p -- state the level instead")
    return len(weak)''',
    '''                     f"or its absence at that p -- state the level instead")

    # The other half: a trend claim that cites no number at all.
    for sent in re.split(r"(?<=[.!?])\\s+", src):
        flat = " ".join(sent.split())
        for pat, pname in TREND_SUBJECTS:
            if pname not in gen or not re.search(pat, flat, re.I):
                continue
            try:
                if float(gen[pname]) <= 0.05:
                    continue
            except ValueError:
                continue
            hit = [v for v in TREND_VERBS
                   if re.search(r"\\b" + re.escape(v) + r"\\b", flat.lower())]
            if hit:
                fail("trend",
                     f"a sentence about a quantity whose trend is not "
                     f"significant (\\\\{pname} = {gen[pname]}) says "
                     f"\\"{hit[0]}\\" without quoting it: ...{flat[:110]}...")
    return len(weak)''',
    "2b: checked even when the sentence quotes no statistic",
    marker="The other half: a trend claim that cites no number")


# --------------------------------------- 3 the caption, under the new check
# fix_reader3 replaced "it rises with capacity" with "its endpoints rise
# with capacity", which keeps a trend verb and which the check above now
# refuses -- correctly, because an ordering asserted in words is still an
# assertion.  The appendix's own form states the factor instead.
rep("main.tex",
    r"""and its endpoints rise with capacity rather than falling.  No $\Delta$""",
    r"""and the widest model's value is $\ToyCapRatio$ times the narrowest's.
No $\Delta$""",
    "3: the caption states the factor, which is what the appendix does")


# ------------------------------------------- 4 the third one, in the body
# Found by the check above, by neither reader.  The sentence asserts the
# trend and the NEXT sentence withdraws the basis for it: "it does not
# fall as capacity rises --- it grows ... The 5 widths are not monotone in
# it, so the endpoints are what this ratio compares."  The point it is
# making -- that a better model does not have less incompatibility -- does
# not need a trend verb to land.
rep("main.tex",
    r"""(Figure~\ref{fig:capacity}), and it does not
fall as capacity rises --- it grows, by a factor of $\ToyCapRatio$ from
$d = \ToyDMin$ to $d = \ToyDMax$.""",
    r"""(Figure~\ref{fig:capacity}), and at the widest model it is not
smaller but larger, by a factor of $\ToyCapRatio$ between $d = \ToyDMin$
and $d = \ToyDMax$.""",
    "4: the body states the endpoints, which is what the next sentence says")

print(f"done: {N} edits")
