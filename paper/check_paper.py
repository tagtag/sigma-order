#!/usr/bin/env python3
"""Check the relations a reader cannot see, before the paper is packaged.

Every defect this script looks for has the same shape: the document compiles,
the PDF looks right, and the error exists only in a relation between two
distant parts of the source.  A reference list prints in full whether or not
anything cites it.  A figure appears whether or not a sentence points at it.
A sentence can promise that a quantity is reported and no table report it.
None of these produce a symptom in the output, so reading the PDF does not
find them; each one in this paper was found by someone asking a question.

This script asks those questions mechanically.  It is not a style checker and
has no opinion about prose.

    python3 -I check_paper.py                 # from paper/
    python3 -I check_paper.py --tex main.tex --tables tables --figures figures

Exit status is 1 if any check fails.  Warnings never fail the run: they are
things worth a look that are legitimately common in a working draft.

A quantity macro that is genuinely not reported in a table -- one shown only
in a figure, say -- is declared in main.tex with a line of the form

    % check_paper: \\sigEP reported in Figure 2

so that the exemption is written down where the macro is, and has to be
written deliberately.
"""

import argparse
import glob
import os
import re
import subprocess
import sys

FAIL, WARN = [], []


def fail(check, msg):
    FAIL.append((check, msg))


def warn(check, msg):
    WARN.append((check, msg))


# LaTeX commands with an initial capital that are not this paper's generated
# macros.  The generated ones are all CamelCase names from make_tables.py.
LATEX_CAPS = {
    "LaTeX", "TeX", "Roman", "Alph", "Big", "Bigg", "Biggl", "Biggr",
    "Bigl", "Bigr", "Large", "LARGE", "Huge", "Delta", "Sigma", "Omega",
    "Gamma", "Lambda", "Phi", "Pi", "Psi", "Theta", "Upsilon", "Xi",
    "DeclareMathOperator", "Vert", "Leftarrow", "Rightarrow", "Longrightarrow",
    "Leftrightarrow", "Pr", "Re", "Im",
    # url.sty, which hyperref loads; \DeclareUrlCommand defines the file-name
    # command the preamble uses.  This list is what the undefined-macro check
    # knows is not ours to define, and a package command missing from it is
    # reported as a missing definition -- a true statement about this file and
    # a false one about the document.
    "DeclareUrlCommand",
    # The lineno block in the preamble; \AtBeginDocument is the only
    # CamelCase command it uses, since the patch macros it defines are
    # lowercase and are caught by the local-definition half of the check.
    "AtBeginDocument",
}


def strip_comments(s):
    """Remove TeX comments, keeping escaped percent signs."""
    out = []
    for line in s.split("\n"):
        i, esc = 0, False
        cut = len(line)
        while i < len(line):
            c = line[i]
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == "%":
                cut = i
                break
            i += 1
        out.append(line[:cut])
    return "\n".join(out)


def brace_body(s, i):
    """Read a balanced {...} starting at s[i] == '{'; return (body, end)."""
    assert s[i] == "{"
    depth, j = 0, i
    while j < len(s):
        if s[j] == "\\":
            j += 2
            continue
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    raise ValueError("unbalanced braces")


def newcommands(src):
    """Every macro definition in the source, as name -> body.

    \\newcommand, \\renewcommand and amsmath's \\DeclareMathOperator all define
    a name; a checker that knows only the first reports the others as
    undefined, which trains the reader to ignore it.
    """
    out = {}
    for m in re.finditer(r"\\(?:(?:re)?newcommand|DeclareMathOperator\*?)"
                         r"\s*\{\\([A-Za-z]+)\}", src):
        j = m.end()
        # skip an optional [n] argument count
        while j < len(src) and src[j] in " \t":
            j += 1
        if j < len(src) and src[j] == "[":
            j = src.index("]", j) + 1
            while j < len(src) and src[j] in " \t":
                j += 1
        if j < len(src) and src[j] == "{":
            body, _ = brace_body(src, j)
            out[m.group(1)] = body
    return out


def float_blocks(src):
    """(kind, label) for every figure/table environment carrying a label."""
    out = []
    for kind in ("figure", "table"):
        for m in re.finditer(r"\\begin\{" + kind + r"\*?\}(.*?)\\end\{"
                             + kind + r"\*?\}", src, re.S):
            for lab in re.findall(r"\\label\{([^}]*)\}", m.group(1)):
                out.append((kind, lab))
    return out


# ---------------------------------------------------------------- checks
def check_bibliography(src):
    keys = re.findall(r"\\bibitem\{([^}]*)\}", src)
    cited = set()
    for m in re.findall(r"\\cite[tp]?\*?(?:\[[^\]]*\])*\{([^}]*)\}", src):
        cited.update(k.strip() for k in m.split(","))
    for k in keys:
        if k not in cited:
            fail("bibliography",
                 f"[{k}] is in the reference list and nothing cites it "
                 f"(thebibliography prints it anyway, so the PDF looks right)")
    for k in sorted(cited - set(keys)):
        fail("bibliography", f"\\cite{{{k}}} has no \\bibitem")
    if len(keys) != len(set(keys)):
        fail("bibliography", "duplicate \\bibitem keys")
    return len(keys)


def check_crossrefs(src):
    refs = set(re.findall(r"\\(?:ref|eqref|autoref)\{([^}]*)\}", src))
    labels = re.findall(r"\\label\{([^}]*)\}", src)
    if len(labels) != len(set(labels)):
        seen, dup = set(), set()
        for l in labels:
            (dup if l in seen else seen).add(l)
        fail("crossrefs", f"duplicate \\label: {', '.join(sorted(dup))}")
    for kind, lab in float_blocks(src):
        if lab not in refs:
            fail("crossrefs",
                 f"{kind} {{{lab}}} is never referenced in the text "
                 f"(it still appears in the PDF, so nothing looks wrong)")
    for r in sorted(refs - set(labels)):
        fail("crossrefs", f"\\ref{{{r}}} has no \\label")
    for lab in labels:
        if lab.startswith("eq:") and lab not in refs:
            warn("crossrefs", f"equation {{{lab}}} is numbered but never cited")
    return len(float_blocks(src))


def check_files_exist(src, base):
    n = 0
    for m in re.findall(r"\\input\{([^}]*)\}", src):
        p = m if m.endswith(".tex") else m + ".tex"
        if not os.path.isfile(os.path.join(base, p)):
            fail("files", f"\\input{{{m}}} does not exist")
        n += 1
    for m in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", src):
        hits = glob.glob(os.path.join(base, "figures", m)) or \
            glob.glob(os.path.join(base, "figures", m + ".*")) or \
            glob.glob(os.path.join(base, m))
        if not hits:
            fail("files", f"\\includegraphics{{{m}}} does not exist")
        n += 1
    return n


def check_todo(tables_dir):
    n = 0
    for p in sorted(glob.glob(os.path.join(tables_dir, "*.tex"))):
        body = open(p, encoding="utf-8").read()
        for t in sorted(set(re.findall(r"TODO:([A-Za-z_\\]+)", body))):
            fail("todo", f"{os.path.basename(p)} still carries [TODO:{t}]")
        if "no measurements for this table" in body:
            fail("todo", f"{os.path.basename(p)} is a stub, not a table")
        n += 1
    if not n:
        fail("todo", f"no generated tables in {tables_dir}/")
    return n


def check_macros(src, tables_dir):
    mpath = os.path.join(tables_dir, "macros.tex")
    generated = newcommands(open(mpath, encoding="utf-8").read()) \
        if os.path.isfile(mpath) else {}
    local = newcommands(src)
    # A definition is not a use.  main.tex inputs tables/macros.tex, so
    # every generated name appears in src inside its own \\newcommand --
    # which made the orphan check below report nothing, ever, while
    # \\Gap*, \\Ratio* and a dozen others sat unused.  The missing-macro
    # half of this function still worked, because a name nothing defines is
    # not in macros.tex either, so the breakage was invisible.
    body = re.sub(r"\\(?:re)?newcommand\s*\{\\[A-Za-z]+\}", " ", src)
    used = set()
    for m in re.finditer(r"\\([A-Z][A-Za-z]*)", body):
        if m.group(1) not in LATEX_CAPS:
            used.add(m.group(1))
    for u in sorted(used):
        if u not in generated and u not in local:
            fail("macros", f"\\{u} is used and nothing defines it")
    # An orphan is one of two things and they are not the same thing: a
    # measurement the paper deliberately does not quote, or a number the
    # prose dropped.  make_tables.py declares the first kind in RETIRED and
    # writes it into macros.tex; anything else is the second kind and
    # fails.  As a warning this was a list of 152 names that nobody read,
    # and \\BlkNSepCausal sat in it while three sentences asserted in prose
    # what it counts.
    retired = set()
    for line in open(mpath, encoding="utf-8") if os.path.isfile(mpath) else []:
        if line.startswith("% retired:"):
            retired.update(line.split(":", 1)[1].split())
    orphans = sorted(g for g in generated if g not in used)
    undeclared = [o for o in orphans if o not in retired]
    if undeclared:
        fail("macros",
             f"{len(undeclared)} generated macro(s) the prose does not use "
             f"and make_tables.RETIRED does not declare: "
             + ", ".join("\\" + o for o in undeclared)
             + " -- either quote them or retire them explicitly")
    stale = sorted(r for r in retired if r in used)
    if stale:
        fail("macros",
             f"{len(stale)} macro(s) are declared retired and the prose "
             f"uses them: " + ", ".join("\\" + r for r in stale))
    absent = sorted(r for r in retired if r not in generated)
    if absent:
        warn("macros",
             f"{len(absent)} retired name(s) no longer generated: "
             + ", ".join("\\" + r for r in absent))
    return len(generated)


TREND_VERBS = (
    "rises", "rise", "rising", "grows", "growing", "increases", "increasing",
    "falls", "fall", "falling", "shrinks", "shrinking", "decreases",
    "declines", "declining",
    "does not vary", "does not change", "is flat", "stays constant",
    "is constant", "unchanged with capacity",
    # The same error about a relation between two series rather than a
    # trend along one: a non-significant rho read as "they do not track
    # each other".  Three places said it, in two different sections, from
    # two different rho's.  Only assertive forms are listed -- "whether
    # they track each other is not something five points can settle"
    # mentions the relation without claiming it, and must not fire.
    "do not track", "does not track", "do not agree", "does not agree",
    "do not move together", "move together",
)


PARAM_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s*([MB])\b")


def check_param_strings(tables_dir):
    """One model, one parameter spelling, across every generated table.

    tab_saturation formatted the count with p//1000 and printed 1B for
    gpt2-xl while every other table printed 1.6B -- and Section 3.1's
    13-fold span is 1.6B/124M, so the odd one out was also the wrong one.
    params_str() had been written for exactly this and one call site did
    not use it.  Two formatters for one quantity is the defect; this finds
    it by comparing what the tables actually print.
    """
    seen = {}
    for fn in sorted(os.listdir(tables_dir)):
        if not (fn.startswith("tab_") and fn.endswith(".tex")):
            continue
        for line in open(os.path.join(tables_dir, fn), encoding="utf-8"):
            if "&" not in line:
                continue
            name = line.split("&")[0].strip().strip("$").strip()
            name = re.sub(r"\\[a-zA-Z]+|[{}\\]", "", name).strip()
            if not name or " " in name:
                continue
            for num, unit in PARAM_RE.findall(line):
                seen.setdefault(name, {}).setdefault(num + unit, set()).add(fn)
                break
    n = 0
    for name, spellings in sorted(seen.items()):
        if len(spellings) > 1:
            where = "; ".join(f"{k} in {','.join(sorted(v))}"
                              for k, v in sorted(spellings.items()))
            fail("params",
                 f"{name} is printed with more than one parameter count "
                 f"({where}) -- one formatter, not two")
            n += 1
    return n


def check_self_reference(paths):
    """A section may not cite itself.

    Section 5.4 said "the cell tests of Section 5.4 are corrected over 25"
    in a sentence contrasting those tests with the correlations Section 5.4
    itself runs -- the cell tests are Section 5.3's.  A reference that
    resolves to the section it sits in is almost always a reference to the
    neighbouring one, and the rendered number looks right, so it survives
    proofreading.

    Files are scanned one at a time and the current \\label{sec:...} is
    tracked as it goes, so a subsection's own label governs its body.
    """
    n = 0
    for path in paths:
        if not os.path.isfile(path):
            continue
        cur, incap, depth = None, False, 0
        for i, line in enumerate(open(path, encoding="utf-8"), 1):
            if line.lstrip().startswith("%"):
                continue
            # brace depth from \\caption{, not "the next line with a }":
            # a caption holding \\ref{...} closes a brace on its first
            # line and the crude version left the caption at once.
            j = line.find("\\caption{")
            if j >= 0:
                incap, depth = True, 0
                line_from = line[j + len("\\caption"):]
            elif incap:
                line_from = line
            else:
                line_from = ""
            if incap:
                depth += line_from.count("{") - line_from.count("}")
                if depth <= 0:
                    endcap = True
                else:
                    endcap = False
            else:
                endcap = False
            for m in re.finditer(r"\\ref\{(sec:[A-Za-z0-9_]+)\}", line):
                if cur and m.group(1) == cur and not incap:
                    # WARN, not FAIL.  Naming your own section is poor
                    # writing far more often than it is an error, and a
                    # check that fails the build on three such sentences
                    # buries the one that pointed at the wrong section.
                    warn("selfref",
                         f"{os.path.basename(path)}:{i} cites "
                         f"\\ref{{{cur}}} from inside the section that "
                         f"label names -- check it was not the "
                         f"neighbouring section that was meant")
                    n += 1
            if endcap:
                incap = False
            lm = re.search(r"\\label\{(sec:[A-Za-z0-9_]+)\}", line)
            if lm:
                cur = lm.group(1)
    return n


def check_dtok_scope(src):
    """The token-reversal quantity may not appear after it is set aside.

    Section 2.1 measures both reversals, shows the token one has the wrong
    sign on the contrast, and states that "the block-level analysis is the
    one followed from here on, and \\Dtok appears only in that table".
    Everything after it writes the block quantity as a bare \\Delta, which
    is only safe while that promise holds.

    The abstract broke the same promise in the other direction: it defined
    \\Delta on the token reversal and then quoted every block number under
    the same symbol, with no sentence between them.  The body has half a
    page bridging the two; the abstract had nothing, because the bridge is
    a paragraph that compresses to nothing.  This enforces the body half.
    """
    cut = src.find("\\section{Methods}")
    if cut < 0:
        return 0
    n = 0
    for m in re.finditer(r"\\Dtok\b", src[cut:]):
        line = src.count("\n", 0, cut + m.start()) + 1
        fail("dtok",
             f"line {line}: \\Dtok appears after Section 2.1 set it aside; "
             f"everything from there writes the block quantity as a bare "
             f"\\Delta, which that promise is what makes unambiguous")
        n += 1
    return n


# Quantities whose trend is not significant, written as the prose names
# them rather than as a macro.  check_trend_verbs() anchors on the macro
# being in the sentence, so a claim that states the trend and leaves the
# number to a figure goes straight past it -- which is how "it rises with
# capacity rather than falling" stood in Figure 2's caption.
#
# This is a list and not a rule.  Knowing that "it rises" is about
# sigma_EP needs the referent, and nothing here can supply one.  A new
# entry is a decision someone makes after a reader finds the next escape.
TREND_SUBJECTS = (
    (r"\\sigEP\b|\bmasked values\b|\bmasked rows\b", "CtrlPEP"),
)


def check_trend_verbs(src, tables_dir):
    """A correlation that does not reach 0.05 may not be given a verb.

    Section 5.4 once called rho = +0.97 "the only component with a
    significant trend" and, in the same paragraph, called rho = +0.87
    "rises" and rho = -0.35 "does not vary".  Two of the three went past
    what the ladder carries, in opposite directions: one asserted an effect
    that was not significant, the other asserted an absence from a failure
    to reject.  With n = 5 the exact null floors at 2/5! = 0.0167, so this
    ladder can establish a trend and cannot establish the absence of one.

    This reads each Trend<X>P out of macros.tex and, for the ones above
    0.05, refuses a trend verb in the same sentence as that component's
    macros.  It is deliberately narrow: it does not try to parse the claim,
    only to stop the two words that state one.  Levels are unaffected --
    "it is one or two grid steps at every rung" names no trend and is the
    form this paper uses instead.
    """
    mpath = os.path.join(tables_dir, "macros.tex")
    if not os.path.isfile(mpath):
        return 0
    gen = newcommands(open(mpath, encoding="utf-8").read())
    weak = []
    # Any correlation, not only the ones named Trend<X>P.  A correlation
    # macro is one whose name contains Rho and has a sibling with P in the
    # same place, which is the convention every pair here follows.  The
    # first version matched the Trend prefix alone; the second matched a P
    # suffix and silently excluded \\CtrlRhoEP/\\CtrlPEP, the pair behind
    # the only trend claim that has got past this check.
    # Pair by replacing Rho with P, not by stripping a suffix.  The
    # suffix rule read \TrendCausalRho/\TrendCausalP and missed
    # \CtrlRhoEP/\CtrlPEP, where Rho and P are infixed before a shared
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
            continue                      # still TODO
    if not weak:
        return 0
    # sentences, roughly: LaTeX has no full stops of its own here
    for sent in re.split(r"(?<=[.!?])\s+", src):
        for rname, pname in weak:
            if not re.search(r"\\(?:%s|%s)\b" % (rname, pname), sent):
                continue
            flat = " ".join(sent.split()).lower()
            # Word boundaries, not substrings.  "characterised" contains
            # "rise", so the first real run of this reported five sentences
            # that say "establishes no trend" as though they claimed one --
            # a checker that cries wolf is worse than none, because the one
            # true positive in the batch was nearly discarded with them.
            hit = [v for v in TREND_VERBS
                   if re.search(r"\b" + re.escape(v) + r"\b", flat)]
            if hit:
                fail("trend",
                     f"\\{pname} is above 0.05 and its sentence says "
                     f"\"{hit[0]}\"; this ladder cannot establish a trend "
                     f"or its absence at that p -- state the level instead")

    # The other half: a trend claim that cites no number at all.
    for sent in re.split(r"(?<=[.!?])\s+", src):
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
                   if re.search(r"\b" + re.escape(v) + r"\b", flat.lower())]
            if hit:
                fail("trend",
                     f"a sentence about a quantity whose trend is not "
                     f"significant (\\{pname} = {gen[pname]}) says "
                     f"\"{hit[0]}\" without quoting it: ...{flat[:110]}...")
    return len(weak)


# Macros that report how large sigma_EP is or how it moves.  sigma_EP is the
# entropy production of the induced Glauber chain in the solvable system of
# the appendix; sigma is the quantity of Eq. (1) measured on text.  They are
# different functionals of one failure and the appendix measures that they do
# not track each other, so a reading of one licenses nothing about the other.
# Section 6.3 nevertheless argued from sigma_EP's rise that sigma is not
# approaching its compatible limit -- the one inference the appendix states
# three times must not be made.  Keeping these macros inside the appendix is
# the mechanical form of that rule.  CtrlRhoXS is deliberately absent: it is
# the correlation BETWEEN the two, and citing it is how the main text blocks
# the inference rather than making it.
SIGEP_MAGNITUDE = (
    "ToyCapRatio", "ToySpanRatio", "ToyCapMonotone",
    "ToySigmaMin", "ToySigmaMax", "ToySigmaAR", "ToyRmsAR",
    "CtrlRhoEP", "CtrlPEP", "CtrlSigmaHeadMax", "CtrlSigmaJointMax",
)


def check_sigep_scope(src):
    """sigma_EP's size stays in the appendix that defines it.

    The scan runs on the prose only.  main.tex inputs tables/macros.tex,
    whose \\newcommand lines contain every macro NAME, all of them before
    \\appendix -- so a positional rule reads the definitions as uses and
    reports the whole list.  That is what the first run of this did.
    """
    src = re.sub(r"\\(?:re)?newcommand\s*\{[^}]*\}\s*\{[^}]*\}", "", src)
    cut = src.find(r"\appendix")
    body = src if cut < 0 else src[:cut]
    n = 0
    for name in SIGEP_MAGNITUDE:
        if re.search(r"\\%s\b" % name, body):
            fail("sigep",
                 f"\\{name} reports sigma_EP's size and is used outside the "
                 f"appendix; sigma_EP and sigma do not track each other, so "
                 f"it licenses nothing about sigma")
            n += 1
    return len(SIGEP_MAGNITUDE) - n


def check_narrowing(src, tables_dir):
    """Nothing may be said to narrow unless it is measured to narrow.

    Figure 1's caption said "the vertical separation between the two series
    narrows as that happens" and then, four lines later, that "the rank
    statistic computed on the same data does not narrow at all" -- while the
    axis of the figure IS that statistic.  The separation is the causal
    component, and it is one or two grid steps at every evaluator including
    the least saturated one, so it does not narrow at either end.

    Two quantities are easy to confuse here and the paper confused them: the
    separation between the series, which stays, and the room above the lower
    series, which closes.  This compares the measured separation at the ends
    of the ladder and refuses the word where the numbers do not support it.
    """
    mpath = os.path.join(tables_dir, "macros.tex")
    if not os.path.isfile(mpath):
        return 0
    gen = newcommands(open(mpath, encoding="utf-8").read())
    try:
        lo = float(gen["CausalGPTtwo"])
        hi = float(gen["CausalQwen"])
    except (KeyError, ValueError):
        return 0                      # still TODO, or renamed
    if hi < lo - 1e-9:
        return 1                      # it really does narrow; the word is fine
    body = re.sub(r"\\(?:re)?newcommand\s*\{[^}]*\}\s*\{[^}]*\}", "", src)
    for env in re.findall(r"\\begin\{figure\}.*?\\end\{figure\}", body,
                          re.S):
        if "fig:blkord" not in env:
            continue
        if re.search(r"\bnarrow(?:s|ing|ed)?\b", env):
            if not re.search(r"does not (?:close|narrow)|room", env):
                fail("narrowing",
                     f"Figure 1's caption says something narrows, but the "
                     f"measured separation is {lo:+.3f} at the smallest "
                     f"evaluator and {hi:+.3f} at the largest; name the room "
                     f"if that is what closes")
    return 1


def check_share_form(src):
    """The paper may not headline the share form it disowns.

    Section 5.3 says the midrank causal component is one grid step, that its
    size is not a measured quantity, and that only the ceiling-free z form
    can carry a size.  Six passages elsewhere quoted the midrank share on
    its own as the headline figure.  The rule: wherever ShareEval is
    quoted, ShareZ must appear in the same paragraph, so the reader is
    never given the disowned number alone.  Section 5.3's own paragraph,
    which quotes the z form alone, is unaffected.

    The window is the paragraph, not the sentence.  Sentence scope was
    tried first and rejected two passages where the ceiling-free figure is
    in the sentence immediately before -- which is exactly the pairing this
    rule exists to require, so the rule was wrong and not the prose.
    """
    body = re.sub(r"\\(?:re)?newcommand\s*\{[^}]*\}\s*\{[^}]*\}", "", src)
    n = 0
    for para in re.split(r"\n\s*\n", body):
        if not re.search(r"\\ShareEval(?:Min|Max)\b", para):
            continue
        n += 1
        if not re.search(r"\\ShareZ(?:Min|Max)\b", para):
            fail("shareform",
                 "a paragraph quotes the midrank share with no ceiling-free "
                 "figure beside it; Section 5.3 declines to read the midrank "
                 "component as a size, so it may not stand alone")
    return n


def check_ref_subject(src):
    """"Section X shows ... sigma" requires X to be about sigma.

    Two passages said "Section 3.3 exhibits a model for which sigma vanishes
    identically while Delta does not".  Section 3.3 is the permutation set
    and contains no sigma at all; the identity is Section 6.1.  \\ref
    resolved, the PDF printed a number, and nothing noticed -- a resolved
    cross-reference says the label exists, not that the target says what the
    sentence claims.

    The rule is narrow on purpose, and aimed at the construction where the
    error lives: a section cited as the SUBJECT of a verb, with the quantity
    named after it.  "...and Section 3.3 shows the n! values to be symmetric
    about zero" in a sentence that mentioned sigma earlier is not that
    construction and is not flagged; the quantity has to follow the verb.
    """
    body = re.sub(r"\\(?:re)?newcommand\s*\{[^}]*\}\s*\{[^}]*\}", "", src)

    # what each section's own text contains
    parts = re.split(r"\\(?:sub)*section\*?\{", body)
    has = {}
    for part in parts[1:]:
        for lab in re.findall(r"\\label\{(sec:[^}]*)\}", part):
            has.setdefault(lab, set())
            if re.search(r"\\sigma\b|\\sigEP\b", part):
                has[lab].add("sigma")

    verbs = ("exhibits", "shows", "proves", "gives", "reports", "measures",
             "makes", "establishes", "defines", "derives")
    pat = re.compile(
        r"Section~\\ref\{(sec:[^}]*)\}\s+(?:%s)\b([^.]*)" % "|".join(verbs))
    n = 0
    for lab, tail in pat.findall(body):
        n += 1
        if not re.search(r"\\sigma\b|\\sigEP\b", tail):
            continue
        if lab in has and "sigma" not in has[lab]:
            fail("refsubject",
                 f"a sentence says Section \\ref{{{lab}}} does something "
                 f"with sigma, but that section's text never mentions sigma")
    return n


def check_duplicate_equations(src):
    """No two numbered displays may have the same body.

    Three equations were displayed twice, once in the introduction and once
    in Section 6.1, so each carried two numbers: sigma was Eq. (3) on page 3
    and Eq. (12) on page 6, and a comparison table cited the second while
    the prose cited the first.  Both \\ref targets resolved, so nothing
    complained.

    Normalising whitespace and stripping the label is enough to catch it:
    the duplicates were copies, not paraphrases.
    """
    bodies = {}
    n = 0
    for env in ("equation", "align"):
        for m in re.finditer(r"\\begin\{%s\*?\}(.*?)\\end\{%s\*?\}"
                             % (env, env), src, re.S):
            raw = m.group(1)
            labs = re.findall(r"\\label\{([^}]*)\}", raw)
            if not labs:
                continue                       # unnumbered display
            n += 1
            key = " ".join(re.sub(r"\\label\{[^}]*\}", "", raw).split())
            if key in bodies:
                fail("dupeq",
                     f"\\label{{{labs[0]}}} displays the same equation as "
                     f"\\label{{{bodies[key]}}}; one equation, one number")
            else:
                bodies[key] = labs[0]
    return n


def check_tolerance_wording(src, tables_dir):
    """A deviation must be introduced as one.

    "the self-test verifies that it normalises to $\\AoarNormDev$" reads as
    though the sum comes to 4.4e-16.  It comes to 1; 4.4e-16 is how far it
    missed.  Every macro whose name ends in Dev or Err is a deviation or a
    tolerance, and the prose has to say so -- the number alone cannot,
    because a reader meets it as a value.

    The window is the clause: the macro must sit near one of a short list
    of markers.  This cannot judge whether the sentence is true, only
    whether it names the quantity, which is the defect that occurred.
    """
    mpath = os.path.join(tables_dir, "macros.tex")
    if not os.path.isfile(mpath):
        return 0
    gen = newcommands(open(mpath, encoding="utf-8").read())
    tol = [g for g in gen if re.search(r"(?:Dev|Err)(?:[A-Z][a-z]*)?$", g)]
    if not tol:
        return 0
    body = re.sub(r"\\(?:re)?newcommand\s*\{[^}]*\}\s*\{[^}]*\}", "", src)
    markers = (r"to within", r"within", r"at most", r"no more than",
               r"departs?", r"differ", r"deviat", r"tolerance",
               r"\\bigl\|", r"\\le\b", r"\\leq\b", r"error")
    n = 0
    for name in tol:
        for m in re.finditer(r"\\%s\b" % name, body):
            n += 1
            lo = body.rfind(".", 0, max(0, m.start() - 1)) + 1
            hi = body.find(".", m.end())
            clause = body[lo:hi if hi > 0 else len(body)]
            if not any(re.search(k, clause) for k in markers):
                fail("tolerance",
                     f"\\{name} is a deviation and its sentence does not "
                     f"say so; it reads as the value rather than the error")
    return n


def check_table_math(tables_dir):
    """Generated tables must not emit math outside math mode.

    tex_sci() returns "2.5\\times10^{-3}" with no delimiters, because every
    caller but one wraps it: the prose writes $\\TailPMax$.  One table cell
    passed it through bare and the document stopped with four errors per
    row, none of which named the generator.  A table file is not math mode,
    and nothing checked that.
    """
    if not os.path.isdir(tables_dir):
        return 0
    n = 0
    # macros.tex is excluded by design: a macro BODY is math without
    # delimiters and the prose wraps it, which is the whole convention.
    # The rule is about table cells, which are typeset where they sit.
    for path in sorted(glob.glob(os.path.join(tables_dir, "tab_*.tex"))):
        src = open(path, encoding="utf-8").read()
        n += 1
        for m in re.finditer(r"\\times|\^\{|_\{", src):
            # a dollar count that is even means we are outside math
            if src.count("$", 0, m.start()) % 2 == 0:
                fail("tablemath",
                     f"{os.path.basename(path)} has {m.group(0)!r} outside "
                     f"math mode; a generated cell must wrap what tex_sci "
                     f"returns in $...$")
                break
    return n


def check_between_sign(src, tables_dir):
    """Section 6.3 reports that the two masked evaluators disagree in sign.

    That is a measured claim.  For several revisions the macros behind the
    paragraph came from a single-evaluator file, and one sentence asserted
    an agreement the data contradicts; nothing caught it because the
    reading had no table and the macros had no evaluator dimension.
    """
    mpath = os.path.join(tables_dir, "macros.tex")
    if not os.path.isfile(mpath) or "FbBetweenNOpposite" not in src:
        return
    v = newcommands(open(mpath, encoding="utf-8").read()).get(
        "FbBetweenNOpposite")
    if v is None or "TODO" in v:
        return
    try:
        n = int(v)
    except ValueError:
        return
    if n < 1:
        fail("between",
             "the two masked evaluators agree in sign on every corpus "
             "(FbBetweenNOpposite = " + v + "); Section 6.3 reports that "
             "they do not, and has to be rewritten")


PERCENTILE_OK = re.compile(r"(\d+|\\[A-Za-z]+)\$?\s*th\s*$")


FLAT_NEGATED = re.compile(r"\b(?:not|nor|never|hardly)\b[^.;:]{0,24}$",
                          re.I)


# Deliberately narrow.  "no origin" was tried here and taken out: this
# paper says it of several different objects -- the set of $f(p)$, the
# comparison, the expression -- and six of the seven sites were about
# something other than Ref. [1]'s quantity.  A check that cries wolf six
# times to catch one is how the LaTeX errors went unread for weeks.
ABSENCE_CLAIMS = (
    r"\bno identity\b",
    r"\bunanchored\b",
    r"\bhas no zero\b",
    r"\bno zero that\b",
    r"\bno limit in which\b",
)
# AUDITED ONCE, NOT CHECKED: the "origin" family, 2026-11-15, eight
# occurrences.  Only Section 1's "Eq. (1) lacks an origin" needed a
# qualifier; two carry one already, and five are about something other
# than Ref. [1]'s quantity -- the set of f(p), the comparison, the
# expression, and the origin this paper supplies.  Adding the family here
# would fail six true sentences to catch one false one.  Re-audit by hand
# if the family grows; do not widen this tuple to cover it.
# A claim of absence is scoped if any of these stands near it.
ABSENCE_SCOPED = re.compile(
    r"fixed[- ]text|on the text being read|single (?:fixed )?text|"
    r"one text|a single reading|for a single|a text the evaluator|"
    r"on the text it is read from",
    re.I)


def check_absence_scope(src):
    """A claim that something is absent has to say where it is absent.

    "No identity is available", "its central quantity is unanchored", "it
    has no zero" are true of the fixed-text reading and false of the
    ensemble one, where Ref. [1]'s Eq. (34) is exactly such an identity.
    Three sentences of this family were live at once, in Sections 1, 6.3
    and 7, and nothing here could have caught them: each is internally
    consistent, cites nothing, breaks no budget, and contradicts no other
    sentence in this paper.  They are wrong only against Ref. [1].

    So this does not look for the contradiction.  It requires the claim to
    name its setting, which is a shape -- a qualifier naming the
    fixed-text reading within a sentence's reach.  A claim that genuinely
    holds in both settings is phrased without these words, or says so and
    adds a qualifier here.
    """
    body = strip_comments(src)
    body = re.sub(r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}",
                  " ", body, flags=re.S)
    flat = re.sub(r"\s+", " ", body)
    for pat in ABSENCE_CLAIMS:
        for m in re.finditer(pat, flat, re.I):
            near = flat[max(0, m.start() - 170):m.end() + 170]
            if not ABSENCE_SCOPED.search(near):
                fail("absence",
                     "\"%s\" with no setting named: ...%s... --- the "
                     "ensemble reading of Ref. [1] has an identity and a "
                     "zero (its Eq. (34)), so a claim that there is none "
                     "has to say it is about the fixed-text reading"
                     % (m.group(0), flat[max(0, m.start() - 70):m.end() + 70]))


# Nouns this paper uses for more than one thing, so that a bare definite
# article on one of them asks a reader to pick.  The qualifier list is what
# makes the rule usable: "the quantity of Eq. (1)", "the labels that
# experiment turns on", "the comparison between the two classes" all carry
# their own referent and never match.  A noun is added here when a reader
# asks "which one?"; it is removed when the paper stops having two.
AMBIGUOUS_NOUNS = ("quantity", "labels", "measurement", "comparison",
                   "reading", "distance", "statistic", "contrast",
                   "choice")
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
# Counted on main.tex with its \input files expanded AFTER comments are
# stripped, which is the string check_paper.py itself checks.  A count made
# the other way round expands a commented-out \input and inflates this by
# half; that is where 79 came from, and 79 made the rule unable to fail.
BARE_NOUN_BUDGET = {
    "quantity": 16, "labels": 9, "measurement": 11, "comparison": 2,
    "reading": 0, "distance": 3, "statistic": 9, "contrast": 9,
    # Zero since fix_ar11.  The last one was "requires choosing $\\pi$, and
    # nothing in the model makes the choice", now "the model does not
    # single out one"; the two before it were "the fact that settles the
    # choice", in Section 1 and in Section 2.1.
    "choice": 0,
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


def check_bare_floor(src):
    """"the floor", with nothing attached to say which floor.

    This paper calls three things a floor: the resolution of the $1/2n!$
    grid, the attainable minimum of an exact $p$, and the part of $\\sigma$
    that no ordering explains.  Banning the word would fail four true
    sentences -- "its floor", "a floor", "that floor", "the floor of that
    instrument" all carry their own antecedent -- to catch none.  What
    carries no antecedent is the bare definite article with nothing after
    it, which asks a reader to supply a unique referent where there are
    three.

    A qualifier before the noun needs no rule: "the grid floor" does not
    match this pattern at all.
    """
    body = strip_comments(src)
    flat = re.sub(r"\s+", " ", body)
    for m in re.finditer(r"\bthe floor\b(?!\s+(?:of|imposed|that|which|in)\b)",
                         flat, re.I):
        fail("floor",
             "bare \"the floor\": ...%s... --- this paper has a grid floor, "
             "an exact floor and a masked floor, so say which, or attach a "
             "phrase that does (\"the floor of ...\", \"its floor\")"
             % flat[max(0, m.start() - 70):m.end() + 70])


def check_flat_sense(src):
    """"flat" is permitted only in the negative.

    Three sites called a series flat that runs 20.0, 15.0, 16.0, 16.0,
    15.0 -- a drop of five of its own steps at the first rung, which this
    paper calls resolved everywhere else, and which ceiling_resolution.py
    has been printing as WRONG SIGN on every build.  The body text had it
    right and the summaries did not, which is the shape this file keeps
    finding: the careful statement is made once and a loose one is made
    three times.

    A negated use -- "neither at the floor nor flat", "it is not flat" --
    says a series FAILS to be level.  That is weak and safe.  A positive
    use asserts a shape, and a shape is a measurement: it belongs in the
    sentence as one, with the span and the trend that back it.

    Raising this is a one-line decision with a reason, like any other
    allow-list here.  What it stops is the word going back in as a
    summary of a series someone has not re-read.
    """
    body = re.sub(r"(?<!\\)%.*", " ", src)
    flat = re.sub(r"\s+", " ", body)
    for m in re.finditer(r"\bflat\b", flat):
        before = flat[max(0, m.start() - 40):m.start()]
        if not FLAT_NEGATED.search(before):
            fail("flat",
                 "\"flat\" asserted of a series: ..." + before[-40:]
                 + "flat... -- say the span and the trend instead, or "
                 "negate it; a series called flat has to be level, and "
                 "the one this rule was written for falls five of its "
                 "own steps")


def check_percentile_sense(src):
    """One permitted spelling of "percentile": an ordinal.

    glossary.txt bans phrases, which works where the misuse has a fixed
    shape.  This one does not: the midrank called a percentile can be
    written with any preposition or with a possessive, and this paper
    writes possessives throughout, so a banned-form list cannot close.
    The permitted form is fixed instead -- "<number>th percentile", which
    is how all of the text's uses and tab_tail's header write the quantile
    -- and everything else fails.

    The two senses are not distinguishable by string: "sits at the 85th
    percentile" passes this and would mean the midrank.  glossary.txt
    carries the sense, this carries the spelling.
    """
    # Not the paper's own prose: a reference title, a verbatim block.
    # Neither is in the source today; excluded before one arrives.
    body = re.sub(r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}",
                  " ", src, flags=re.S)
    body = re.sub(r"\\begin\{verbatim\}.*?\\end\{verbatim\}", " ", body,
                  flags=re.S)
    body = re.sub(r"\\verb\|[^|]*\|", " ", body)
    flat = re.sub(r"\s+", " ", body)
    # The plural is permitted exactly where the singular is: "the 10th and
    # 90th percentiles" is a form this paper may need, "its percentiles" is
    # not, and which way the plural fell was an accident of word boundary.
    for m in re.finditer(r"percentiles?", flat):
        before = flat[max(0, m.start() - 48):m.start()]
        if not PERCENTILE_OK.search(before):
            fail("percentile",
                 "\"percentile\" without an ordinal: ..."
                 + before[-40:] + "percentile... -- this paper says "
                 "\"midrank\" for a position in a permutation set, and "
                 "spells the quantile \"<number>th percentile\"")


def check_double_superscript(tables_dir):
    """A second superscript on an atom that already has one.

    "$1\\times10^{-4}^{*}$" -- a significance star appended to a p-value
    that tex_p_bare already wrote in exponent form.  TeX refuses it, says
    so in the log, and carries on, so the PDF is built and seventeen cells
    of it are wrong.

    The log said this 51 times a build and nothing read the log.  Caught
    here it names the file and the line, which is what makes it a
    one-minute fix instead of a grep through three pdflatex passes.
    """
    pat = re.compile(r"\^\{[^{}]*\}\s*\^")
    for fn in sorted(os.listdir(tables_dir)):
        if not fn.endswith(".tex"):
            continue
        with open(os.path.join(tables_dir, fn), encoding="utf-8") as fh:
            body = fh.readlines()
        for i, line in enumerate(body, 1):
            m = pat.search(line)
            if m:
                fail("texmath",
                     "%s line %d: a superscript on a superscript, "
                     "...%s... -- TeX refuses this and typesets something "
                     "else; give the second one an empty group, {}^{*}"
                     % (fn, i, line[max(0, m.start() - 24):m.end() + 8]
                        .strip()))


# \texttt{} spans that are not model names.  The author block's address is
# the only one today; a new entry here is a decision, like every other
# allow-list in this file.
TEXTTT_NOT_A_MODEL = {
    "tag@granular.com",
}


def check_withdrawn_words(src, tables_dir):
    """A word a withdrawal removed, still in the prose.

    make_tables.py declares what each withdrawal takes out of the text,
    beside the macros it retires, and writes both into macros.tex.  This
    reads the prose half back.

    The failure it is built for is not a slip.  It is a decision taken
    once and carried out only where something was watching: the macro goes
    because the orphan check would catch it, and the word stays because
    nothing would.  Three of those were live in this paper at once.
    """
    mpath = os.path.join(tables_dir, "macros.tex")
    if not os.path.isfile(mpath):
        return
    rules = []
    for line in open(mpath, encoding="utf-8"):
        m = re.match(r"%\s*withdrawn-prose:\s*(.+?)\|(.*?)\|(.*?)\|(.*)$",
                     line)
        if m:
            rules.append(tuple(g.strip() for g in m.groups()))
    body = strip_comments(src)
    body = re.sub(r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}",
                  " ", body, flags=re.S)
    flat = re.sub(r"\s+", " ", body)
    for word, budget, group, why in rules:
        if budget == "-":
            continue          # governed by a check of its own
        n = len(re.findall(r"\b" + re.escape(word) + r"\b", flat, re.I))
        if n > int(budget):
            fail("withdrawn",
                 "\"%s\" appears %d time(s) in the prose.  %s withdrew it "
                 "and allows %s: %s.  Either that withdrawal is not "
                 "finished, or the budget in WITHDRAWN_FROM_PROSE "
                 "(make_tables.py) has to move, with a reason."
                 % (word, n, group[0].upper() + group[1:], budget, why))


def check_model_inventory(src):
    """Every model the prose names has a row in the evaluator table.

    The Section 3.1 table is the paper's inventory of evaluators.
    \\texttt{bert-large} sat in Section 3.2 with no row in it: its
    parameter macro had been retired with the pseudo-log-likelihood
    comparison and the name had not, so the prose named a model the paper
    did not otherwise admit to using.  Nothing else in the build could
    notice, because a retired macro is retired correctly and a word in
    prose is just a word.

    Names are matched by containment against the table's own spellings, so
    \\texttt{bert-base} resolves to \\texttt{bert-base-uncased} and
    \\texttt{LLaDA} to \\texttt{GSAI-ML/LLaDA-8B-Base} without a second
    list of aliases to keep in step.
    """
    tab = re.search(r"model & parameters & direction & role.*?"
                    r"\\end\{tabular\}", src, re.S)
    if not tab:
        fail("inventory", "the evaluator table of Section 3.1 was not "
             "found; check_model_inventory keys on its header row")
        return
    listed = re.findall(r"\\texttt\{([^{}]*)\}", tab.group(0))
    if not listed:
        fail("inventory", "the evaluator table names no models")
        return
    body = src[:tab.start()] + src[tab.end():]
    for name in sorted(set(re.findall(r"\\texttt\{([^{}]*)\}", body))):
        if name.startswith("\\") or name in TEXTTT_NOT_A_MODEL:
            continue
        if not any(name.lower() in row.lower() for row in listed):
            fail("inventory",
                 "\\texttt{%s} is named in the prose and has no row in the "
                 "evaluator table of Section 3.1 --- either it belongs in "
                 "the table, or it is a name left behind by a removal "
                 "(check the RETIRED list in make_tables.py)" % name)


def _numtext(cell):
    """A printed number, comparable across tables that delimit it
    differently: one prints 0.3182 and the other $+0.3182$."""
    return re.sub(r"[$+\s]", "", cell)


def check_token_block_agree(tables_dir):
    """Table 1's block column against Table 3's, cell by cell.

    The two come from different measurement files -- tab_token from the
    pll records, tab_blkcells from the blkord ones -- and the prose has
    been asserting that they agree on the \\texttt{gpt2} cells without
    anything checking it.  Now that both are printed, they can be read
    against each other, which is the only reason it is safe to delete the
    sentence that used to point one at the other.

    Corpus order is already enforced across generated tables; this is the
    value check that goes with it.
    """
    tok = os.path.join(tables_dir, "tab_token.tex")
    blk = os.path.join(tables_dir, "tab_blkcells.tex")
    if not (os.path.isfile(tok) and os.path.isfile(blk)):
        return

    def rows(path, model_col, corpus_col, value_col, want_model=None):
        out = []
        for line in open(path, encoding="utf-8"):
            if not line.rstrip().endswith(r"\\") or "evaluator" in line:
                continue
            c = [x.strip() for x in line.split("&")]
            if len(c) <= max(model_col, corpus_col, value_col):
                continue
            model = c[model_col].split("(")[0].strip()
            if want_model and want_model not in model and model:
                continue
            out.append((model, c[corpus_col], c[value_col]))
        return out

    # tab_token: evaluator | corpus | n | Dtok | Dblk | r   (one evaluator,
    # whose name is printed on its first row only)
    t = [(c, v) for _, c, v in rows(tok, 0, 1, 4)]
    # tab_blkcells: evaluator | corpus | median Dblock | r | p
    b = [(c, v) for m, c, v in rows(blk, 0, 1, 2) if m.startswith("gpt2")
         and m == "gpt2"]
    if not t or not b:
        return
    if len(t) != len(b):
        fail("tokenblock",
             "Table 1 has %d rows and Table 3 has %d \\texttt{gpt2} rows; "
             "they are meant to be the same cells" % (len(t), len(b)))
        return
    for (ct, vt), (cb, vb) in zip(t, b):
        if ct != cb:
            fail("tokenblock",
                 "Table 1 and Table 3 disagree on corpus order: %s vs %s"
                 % (ct, cb))
        elif _numtext(vt) != _numtext(vb):
            fail("tokenblock",
                 "median $\\Delta_{block}$ for %s is %s in Table 1 and %s in "
                 "Table 3.  The two are computed from different measurement "
                 "files, and Section 2.1 reads the ratio as though they were "
                 "the same number." % (ct, vt, vb))


def check_corpus_order(tables_dir):
    """Every generated table names corpora in the canonical order.

    Section 2.1 asserts that Table 1 and Table 3 share it, and no number
    carries an ordering, so nothing else would notice a divergence: both
    tables would stay correct and one sentence would quietly stop being
    true.  The evaluator axis has had this check for longer; this is its
    twin.

    Read off the table bodies rather than the inputs -- an order agreed
    upstream and disturbed by a renderer passes an input-side check.
    Corpora appear as rows in some tables and as columns in others, so
    what is tested is each RUN: a sequence of corpus names ends when one
    repeats, and every run must agree with the canonical order restricted
    to the names it contains.
    """
    opath = os.path.join(tables_dir, "corpus_order.txt")
    if not os.path.isfile(opath):
        return
    canon = open(opath, encoding="utf-8").read().split()
    if not canon:
        return
    rank = {c: i for i, c in enumerate(canon)}
    pat = re.compile("|".join(re.escape(c) for c in canon))
    for p in sorted(glob.glob(os.path.join(tables_dir, "*.tex"))):
        if os.path.basename(p) == "macros.tex":
            continue
        if os.path.basename(p) == "corpus_order.txt":
            continue
        seen, runs, cur = set(), [], []
        for m in pat.finditer(open(p, encoding="utf-8").read()):
            c = m.group(0)
            if c in seen:
                runs.append(cur)
                seen, cur = set(), []
            seen.add(c)
            cur.append(c)
        runs.append(cur)
        for run in runs:
            if len(run) < 2:
                continue
            if [rank[c] for c in run] != sorted(rank[c] for c in run):
                fail("order",
                     os.path.basename(p) + " names corpora out of the "
                     "canonical order: " + " ".join(run) + " (canonical: "
                     + " ".join(canon) + ")")
                break


def check_sigma_prime(src):
    r"""No sigma-shaped symbol stands for Ref. [1]'s quantity.

    Section 2.1 states the rule -- "this paper reserves $\sigma$ for
    Eq. (3) ... a statement made about $\sigma$ here is never a statement
    about $\sigma_{block}$ there" -- and $\sigma'$ broke it twice, with
    no definition anywhere, left over from the revision in which Section
    2.2 was rebuilt.

    Not a glossary rule: glossary.txt matches on word boundaries, so a
    term beginning with a backslash can be written there and never fire,
    which is worse than not writing it.
    """
    for form in (r"\sigma'", r"\sigma^{\prime}", r"\sigma^\prime"):
        n = src.count(form)
        if n:
            fail("notation",
                 "%s appears %dx: a sigma-shaped symbol for Ref. [1]'s "
                 "quantity is what Section 2.1 forbids, and this one has "
                 "no definition.  It is written \\Dblock here." % (form, n))


ELLIPSIS_SHAPES = {
    # shape -> (pattern, budget).  The budget is the number of sites that
    # survived a reading in which every one of these shapes was found by a
    # reader stopping at it.  Those survivors are legitimate: parallels
    # with both arms present, restrictive relatives, idioms, and colons
    # that supply what was elided.  A count that RISES is a new instance,
    # and new instances have come from patches, not from drafting.
    "possessive with the noun elided":
        (r"\b[a-z]+'s (?=(?:need|do|does|is|are|was|were|can|cannot|will|"
         r"would|must|has|have)\b)", 0),
    "modal with the verb elided":
        # 9 and not 8 since fix_split2: splitting Section 5.4's threshold
        # sentence turned a dash into a comma, and the pattern keys on the
        # punctuation after the modal.  The construction is unchanged --
        # "which the table shows and this threshold does not [show]", a
        # parallel with its verb one clause back, like the other eight.
        (r"\b(?:need not|does not|do not|cannot|can|could|would|did)[.,;:]", 9),
    "predicate with the head noun elided":
        (r"\bis (?:not )?of (?:the|a|an|its|their)\b", 1),
    "ordinal used as a noun":
        (r"\bthe (?:first|second|third|former|latter)(?:'s)?\b"
         r"(?! \w+ (?:of|in|is a))", 18),
    "bare both / one / ones":
        (r"\bboth\b(?! [a-z])|\bthe ones?\b(?! of the)", 28),
    "deictic kind / form / sense":
        (r"\bof (?:that|this) kind\b|\bin (?:this|that) sense\b|"
         r"\b(?:that|this) form\b|\bof a kind\b", 1),
    "demonstrative + abstract noun":
        (r"\b(?:that|this|these|those) (?:identity|difference|distinction|"
         r"quantity|comparison|contrast|construction|reading|claim|argument|"
         r"fact|point|step|route|side|choice|zero|origin|separation|account|"
         r"part)\b", 19),
    "'such a X'":
        (r"\bsuch (?:a|an) [a-z]+\b", 4),
    "stand-in noun":
        (r"\b(?:a|the) (?:thing|notion|object)\b", 0),
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
    body = re.sub(r"\\begin\{(table|figure|tabular|center)\*?\}.*?"
                  r"\\end\{\1\*?\}", " ", src, flags=re.S)
    flat = re.sub(r"\s+", " ", body)
    for name, (pat, budget) in sorted(ELLIPSIS_SHAPES.items()):
        hits = list(re.finditer(pat, flat))
        if len(hits) > budget:
            # Print the sites.  A count alone sends the reader back to the
            # source to find which one is new, which is the work the check
            # exists to remove.
            where = "; ".join(
                "..." + flat[max(0, m.start() - 55):m.end() + 35] + "..."
                for m in hits[:12])
            fail("ellipsis",
                 "%s: %d sites, budget %d.  Either name what the new one "
                 "elides, or raise the budget in ELLIPSIS_SHAPES with a "
                 "reason.  Sites: %s" % (name, len(hits), budget, where))


def prose_sentences(src):
    """The body text as sentences, with floats, maths and macros removed."""
    # Start at the abstract: the author block is not prose, and its
    # affiliation line was being counted as a 57-word sentence.
    i = src.find(r"\begin{abstract}")
    t = src[i:] if i > 0 else src
    t = re.sub(r"\\begin\{(table|figure|equation|align|tabular|center)\*?\}"
               r".*?\\end\{\1\*?\}", " ", t, flags=re.S)
    t = re.sub(r"\\caption\{[^{}]*(\{[^{}]*\}[^{}]*)*\}", " ", t)
    t = re.sub(r"\$[^$]*\$", " X ", t)
    t = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^{}]*\})?", " ", t)
    t = re.sub(r"\s+", " ", t)
    return [s.strip() for s in re.split(r"(?<=[.!?]) (?=[A-Z])", t)
            if 3 < len(s.split()) < 200]


SENTENCE_WORDS = 50
# The budget is lowered to the number the build reports, never to a
# number guessed here: a guess that is one too low fails a build for a
# reason that has nothing to do with the paper.
SENTENCE_BUDGET = 39   # fix_ar10 took it to 40, this patch to 39
NLONG = 0


def check_sentence_length(src):
    """How many sentences run past SENTENCE_WORDS.

    The median is 26 and the distribution is healthy; what a reader stops
    at is the tail.  Length is not itself the defect -- a sentence can be
    long because it lists generated numbers -- so this is a budget and not
    a ban: it cannot grow, and it comes down as the tail is split.
    """
    long = [s for s in prose_sentences(src) if len(s.split()) > SENTENCE_WORDS]
    globals()["NLONG"] = len(long)   # reported in the summary line
    if len(long) > SENTENCE_BUDGET:
        worst = max(long, key=lambda s: len(s.split()))
        fail("length",
             "%d sentences over %d words, budget %d.  Longest is %d words: "
             "%s..." % (len(long), SENTENCE_WORDS, SENTENCE_BUDGET,
                        len(worst.split()), worst[:120]))


NESTED_NEGATION = re.compile(
    r"\b(?:did|does|do|could|can|would|will|has|have)\s+not\s+"
    r"(?:[a-z]+\s+){0,6}?(?:is|are|was|were)\s+not\b", re.I)


def check_nested_negation(src):
    """A negation inside the subject, then a negated main verb.

    "a text the evaluator did not produce is not a draw from that
    distribution" asks the reader to hold two scopes at once.  The pattern
    requires no comma, dash or conjunction between the two negations, so
    ordinary coordination -- "their lengths are not controlled, and the
    non-causal passages are not incoherent" -- does not trip it.
    """
    t = re.sub(r"\s+", " ", src)
    for m in NESTED_NEGATION.finditer(t):
        fail("negation",
             "a negated clause inside a negated clause: ..."
             + t[max(0, m.start() - 60):m.end() + 40] + "...")


def check_quantities(src, tables_dir):
    """Every named quantity must be reported somewhere, or say where it is.

    A macro whose body is a sigma with a subscript names a measured quantity.
    The paper introduces three, and one of them -- sigma_token -- was defined,
    described, and promised to the reader without any table ever reporting it.
    Nothing in the rendered document showed that, because the sentence making
    the promise reads perfectly well on its own.
    """
    local = newcommands(src)
    exempt = {}
    for m in re.finditer(r"%\s*check_paper:\s*\\([A-Za-z]+)\s+reported in\s+"
                         r"(.+)", src if "%" in src else ""):
        exempt[m.group(1)] = m.group(2).strip()
    tables = ""
    for p in sorted(glob.glob(os.path.join(tables_dir, "*.tex"))):
        tables += open(p, encoding="utf-8").read()
    n = 0
    for name, body in sorted(local.items()):
        # Delta as well as sigma.  The two coarse-grainings of the Sagawa
        # quantity were renamed from \sigma_{token}/\sigma_{block} to
        # \Delta_{...} when Section 2.2 settled the notation, and a check
        # that looked only for sigma would have let a rename be a way out of
        # it.  A named measured quantity has to be reported whatever letter
        # it wears.
        if "\\sigma" not in body and "\\Delta" not in body:
            continue
        n += 1
        needle = re.sub(r"\s+", "", body)
        if re.sub(r"\s+", "", tables).find(needle) >= 0:
            continue
        if name in exempt:
            continue
        fail("quantities",
             f"\\{name} = ${body}$ is named in the text and no generated "
             f"table reports it; if that is intended, add a line\n"
             f"             % check_paper: \\{name} reported in <where>")
    return n


def check_glossary(src, path, also=()):
    """Terms this paper settled on, and the near-synonyms that crept in.

    One earlier revision used two phrases for one thing and then, asked what
    the difference was, invented one.  A glossary is the only defence: the
    choice has to be written down somewhere outside the prose, or it cannot
    be checked.  Format, one rule per line:

        preferred term | banned alternative, another one   # why
    """
    if not os.path.isfile(path):
        warn("glossary", f"{path} does not exist; no terminology check run")
        return 0
    # The prose is not the only place a term reaches the reader.  An axis
    # label lives in the figure script, and a term that was unified
    # everywhere in main.tex survived in a ylabel, printed three times in
    # Figure 1, where nothing searching the LaTeX could see it.
    # Whitespace is collapsed before matching.  A two-word term that
    # happened to wrap across a line was invisible to this check for as long
    # as it has existed: "permutation construction" and "permutation range"
    # both sat in main.tex, against a rule that names them, and grep for
    # them found nothing either.  Any multi-word rule could be defeated by
    # a line break, which is to say by the line length of whoever typed it.
    def flat(t):
        # The title is excluded.  It contrasts "authored order" with "causal
        # order" as ATTRIBUTES of a passage, which is the sense the body
        # keeps in "sentence order" and "causal order"; the object those
        # rules rename is an arrangement, and it always carries a
        # determiner.  A title is also the author's wording and is read by
        # eye every time, so a rule that fires on it reports nothing the
        # author has not already decided.
        t = re.sub(r"\\title\{.*?\n\}", " ", t, flags=re.S)
        return " ".join(re.sub(r"\\(?:sub)*section\*?\{", " ", t).split())

    bodies = {"the text": flat(src)}
    for p in also:
        if os.path.isfile(p):
            bodies[os.path.basename(p)] = flat(
                open(p, encoding="utf-8").read())
    n = 0
    for raw in open(path, encoding="utf-8"):
        line = raw.split("#")[0].strip()
        if not line or "|" not in line:
            continue
        pref, alts = line.split("|", 1)
        pref = pref.strip()
        # A rule may be marked prose-only.  "split" is a near-synonym for
        # "decomposition" in the text and the name of a string method in the
        # scripts; a rule that cannot say which it means has to ban both or
        # neither.
        prose_only = pref.startswith("[tex]")
        if prose_only:
            pref = pref[len("[tex]"):].strip()
        for alt in (a.strip() for a in alts.split(",")):
            if not alt:
                continue
            n += 1
            for where, body in bodies.items():
                if prose_only and where != "the text":
                    continue
                # an optional plural, so a banned term does not slip back in
                # simply by being used of more than one thing
                hits = len(re.findall(r"\b" + re.escape(alt) + r"s?\b",
                                      body, re.I))
                if hits:
                    fail("glossary",
                         f'"{alt}" appears {hits}x in {where}; '
                         f'this paper says "{pref}"')
    return n


def page_texts(pdf):
    """The text of each page, as a list, or None if nothing here can read it.

    Float placement is decided at typesetting time, so this check needs the
    built PDF.  It used to require poppler's pdftotext, which is not on every
    machine the paper is built on -- and where it is missing the check turned
    itself into a warning, which is the same as not having it.  Any one of
    these readers is enough, and at least one is usually already installed
    beside the build.
    """
    import subprocess

    # python3 -I runs isolated, which switches OFF the per-user site
    # directory -- so a reader installed with `pip install --user` is on
    # disk and invisible.  That happened on the first machine this ran on:
    # the install succeeded and the check still reported no reader found.
    # Look there explicitly before giving up.
    d = os.path.expanduser(
        f"~/.local/lib/python{sys.version_info.major}."
        f"{sys.version_info.minor}/site-packages")
    if os.path.isdir(d) and d not in sys.path:
        sys.path.append(d)


    try:
        n = int(re.search(r"Pages:\s+(\d+)",
                          subprocess.run(["pdfinfo", pdf], capture_output=True,
                                         text=True).stdout).group(1))
        out = []
        for page in range(1, n + 1):
            out.append(subprocess.run(
                ["pdftotext", "-f", str(page), "-l", str(page), pdf, "-"],
                capture_output=True, text=True).stdout)
        return out
    except Exception:
        pass

    try:
        import pypdfium2
        doc = pypdfium2.PdfDocument(pdf)
        return [doc[i].get_textpage().get_text_range() for i in range(len(doc))]
    except Exception:
        pass

    try:
        import fitz
        with fitz.open(pdf) as doc:
            return [pg.get_text() for pg in doc]
    except Exception:
        pass

    try:
        from pdfminer.high_level import extract_text
        out, i = [], 0
        while True:
            t = extract_text(pdf, page_numbers=[i])
            if not t:
                break
            out.append(t)
            i += 1
            if i > 500:
                break
        return out or None
    except Exception:
        pass

    try:
        from pypdf import PdfReader
        return [pg.extract_text() or "" for pg in PdfReader(pdf).pages]
    except Exception:
        return None


def appendix_float_numbers(src, base):
    """Which floats live in the appendix, by their printed number.

    A float declared in the appendix and cited from the body is SUPPOSED to
    be far from its citation: that is what an appendix is.  The check
    reported one as drifting nine pages and two rounds of float tuning went
    into a layout that was already right.

    The appendix is found in the SOURCE, where \\appendix says so exactly,
    and the numbers come from main.aux, where LaTeX has already resolved
    every label.  Reading it out of the PDF text means guessing at a
    heading, which in this class is printed as a bare letter.
    """
    cut = src.find(r"\appendix")
    if cut < 0:
        return set()
    labels = set(re.findall(r"\\label\{((?:tab|fig):[^}]*)\}", src[cut:]))
    aux = os.path.join(base, "main.aux")
    if not labels or not os.path.isfile(aux):
        return set()
    out = set()
    for m in re.finditer(r"\\newlabel\{([^}]*)\}\{\{([^}]*)\}",
                         open(aux, encoding="utf-8").read()):
        if m.group(1) in labels:
            kind = "Table" if m.group(1).startswith("tab:") else "Figure"
            out.add(f"{kind} {m.group(2)}")
    return out


# Floats whose citation-to-print distance is a placement decision rather
# than a defect, keyed by the opening words of the caption so that the
# entry survives renumbering.  The expected case is silent; a distance
# that GROWS past the entry speaks up again.
#
# Table 3 (Every (evaluator, corpus) cell...) is cited in Section 4.2 for
# a range and read row by row in Section 5.3, and the 25-row float has to
# sit beside the section that reads it.  The distance is the cost of that.
# DO NOT close the gap by deleting the Section 4.2 citation: that citation
# is what makes the range of Dblock checkable against the table, which is
# the hole this paper closed once already.
FLOAT_DISTANCE_OK = {
    "Every (evaluator, corpus) cell":
        (6, "read row by row in Section 5.3, cited for a range in 4.2"),
    # Cited in Section 3.4, where Eqs. (12) and (13) define what it
    # decomposes, and printed beside Section 5, which reads it per
    # evaluator.  The gap opened when the abstract grew; the placement
    # was right before and is right now.  DO NOT move the table to the
    # citation: Section 5's reading is what the table is for.
    "Decomposition of the within-text distance":
        (4, "defined in Section 3.4, read per evaluator in Section 5"),
}


def check_float_placement(pdf, appendix_floats=frozenset()):
    """Where the floats actually came out.

    Everything else here reads the source.  This one reads the built PDF,
    because float placement is decided at typesetting time and nothing in the
    source records it.  In one build every figure was deferred past the
    bibliography -- Figure 1, described in the text as the decisive result,
    printed two pages after the reference list -- and no check noticed,
    because the source was correct.

    Needs pdftotext; skipped with a warning if it is missing or the PDF is
    not there.
    """
    if not os.path.isfile(pdf):
        warn("floats", f"{pdf} not built; float placement not checked")
        return 0
    pages = page_texts(pdf)
    if not pages:
        warn("floats", "no PDF text reader found (tried pdftotext, "
                       "pypdfium2, PyMuPDF, pdfminer.six, pypdf); floats "
                       "not checked.  pip install pypdfium2")
        return 0
    caption_page, ref_page, bib_page = {}, {}, None
    caption_text = {}
    for page, txt in enumerate(pages, 1):
        if bib_page is None and re.search(r"^\[1\]\s", txt, re.M):
            bib_page = page

        for m in re.finditer(r"^(Figure|Table) (\d+):", txt, re.M):
            caption_page.setdefault((m.group(1), m.group(2)), page)
            caption_text.setdefault(
                (m.group(1), m.group(2)),
                re.sub(r"\s+", " ", txt[m.end():m.end() + 90]).strip())
        for m in re.finditer(r"\b(Figure|Table)s?~?\s(\d+)\b", txt):
            key = (m.group(1), m.group(2))
            if key not in caption_page or caption_page[key] != page:
                ref_page.setdefault(key, page)
    checked = 0
    for key, cpage in sorted(caption_page.items()):
        checked += 1
        name = f"{key[0]} {key[1]}"
        if bib_page is not None and cpage >= bib_page:
            fail("floats",
                 f"{name} is typeset on page {cpage}, at or after the "
                 f"bibliography (page {bib_page}); the source is fine, the "
                 f"output is not")
        rp = ref_page.get(key)
        if name in appendix_floats:
            continue              # see appendix_float_numbers()
        allowed = 2
        for prefix, (gap, _why) in FLOAT_DISTANCE_OK.items():
            if caption_text.get(key, "").startswith(prefix):
                allowed = gap
                break
        if rp is not None and cpage - rp > allowed:
            warn("floats",
                 f"{name} is first cited on page {rp} and printed on "
                 f"page {cpage}"
                 + (f"; {allowed} pages are accepted for this float, see "
                    f"FLOAT_DISTANCE_OK" if allowed > 2 else ""))
    return checked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tex", default="main.tex")
    ap.add_argument("--tables", default="tables")
    ap.add_argument("--glossary", default="glossary.txt")
    ap.add_argument("--pdf", default="main.pdf",
                    help="the built PDF, for float placement; "
                         "skipped when it is not there")
    ap.add_argument("--also",
                    default="make_figures.py,make_tables.py,"
                            "../order-intervention/block_order_selftest.py,"
                            "../order-intervention/pll_selftest.py,"
                            "../order-intervention/aoar_selftest.py",
                    help="further files the glossary applies to; an axis "
                         "label reaches the reader as surely as a sentence")
    args = ap.parse_args()

    base = os.path.dirname(os.path.abspath(args.tex)) or "."
    raw = open(args.tex, encoding="utf-8").read()

    # Expand \input before anything else.  The checker used to verify only
    # that an \input'd file EXISTS, so once the body was split into
    # sec_intro.tex, sec_decomp.tex and sec_truesigma.tex every label, cite
    # and generated macro in them became invisible: the labels they define
    # looked missing, the works they cite looked uncited, and the macros
    # they use looked unused.  Every check below wants the document the
    # reader gets, which is the expanded one.  check_files_exist still runs
    # on the raw source, because that is where the \input calls are.
    def expand(text, depth=0):
        if depth > 8:
            return text
        def sub(m):
            q = m.group(1)
            q = q if q.endswith(".tex") else q + ".tex"
            f = os.path.join(base, q)
            if not os.path.isfile(f):
                return m.group(0)
            # strip comments BEFORE expanding: a commented-out \input is
            # not an input, and expanding one duplicates a whole file --
            # which is how every label in sec_truesigma.tex came out as a
            # duplicate on the first run of this.
            return expand(strip_comments(
                open(f, encoding="utf-8").read()), depth + 1)
        return re.sub(r"\\input\{([^}]*)\}", sub, text)

    src = expand(strip_comments(raw))
    nexp = len(re.findall(r"\\input\{", strip_comments(raw)))

    print(f"checking {args.tex} ({nexp} \\input expanded)")
    nbib = check_bibliography(src)
    nflo = check_crossrefs(src)
    nfil = check_files_exist(strip_comments(raw), base)
    ntab = check_todo(args.tables)
    nmac = check_macros(src, args.tables)
    # the exemption comments live in the comments, so this one reads the raw
    # source rather than the stripped one
    nqty = check_quantities(raw, args.tables)
    ntrd = check_trend_verbs(src, args.tables)
    nsep = check_sigep_scope(src)
    check_narrowing(src, args.tables)
    check_share_form(src)
    check_ref_subject(src)
    check_duplicate_equations(src)
    check_tolerance_wording(src, args.tables)
    check_table_math(args.tables)
    check_param_strings(args.tables)
    check_between_sign(src, args.tables)
    check_percentile_sense(src)
    check_flat_sense(src)
    check_bare_floor(src)
    check_bare_definite(src)
    check_spelled_counts(src)
    check_comparison_target(src)
    check_cell_product(args.tables)
    check_absence_scope(src)
    check_corpus_order(args.tables)
    check_token_block_agree(args.tables)
    check_double_superscript(args.tables)
    check_model_inventory(src)
    check_withdrawn_words(src, args.tables)
    check_sigma_prime(src)
    check_ellipsis_budget(src)
    check_sentence_length(src)
    check_nested_negation(src)
    check_dtok_scope(src)
    # per file, because a label in main.tex would otherwise still be
    # "current" when an \input file's first lines are read
    check_self_reference(
        [os.path.join(base, args.tex)]
        + [os.path.join(base, f if f.endswith(".tex") else f + ".tex")
           for f in re.findall(r"\\input\{([^}]+)\}", strip_comments(raw))
           if not f.startswith("tables/")])
    nflt = check_float_placement(os.path.join(base, args.pdf),
                                 appendix_float_numbers(src, base))
    ngls = check_glossary(
        src, os.path.join(base, args.glossary),
        also=[os.path.join(base, f) for f in args.also.split(",") if f])
    print(f"  {nbib} references, {nflo} floats, {nfil} included files, "
          f"{ntab} tables, {nmac} generated macros, {nqty} quantities, "
          f"{ngls} glossary rules, {nflt} typeset floats, "
          f"{ntrd} non-significant trend(s), {nsep} appendix-only macro(s), "
          f"{NLONG} sentence(s) over {SENTENCE_WORDS} words (budget "
          f"{SENTENCE_BUDGET})")
    # Stated, not warned: line numbers in the draft are deliberate, and a
    # standing warning about a deliberate thing is how a real one gets
    # skipped.  make_arxiv.sh is what refuses to package with them on.
    print("  draft line numbers: "
          + ("ON (\\draftlinesfalse before submitting)"
             if re.search(r"\\draftlinestrue", src) else "off"))

    for kind, items, head in (("WARN", WARN, "worth a look"),
                              ("FAIL", FAIL, "must be fixed")):
        if not items:
            continue
        print(f"\n{kind} ({head}):")
        for check, msg in items:
            print(f"  [{check}] {msg}")

    if FAIL:
        print(f"\n{len(FAIL)} problem(s).")
        return 1
    print("\nall relation checks pass"
          + (f" ({len(WARN)} warning(s))" if WARN else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
