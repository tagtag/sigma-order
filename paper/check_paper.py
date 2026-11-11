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
    used = set()
    for m in re.finditer(r"\\([A-Z][A-Za-z]*)", src):
        if m.group(1) not in LATEX_CAPS:
            used.add(m.group(1))
    for u in sorted(used):
        if u not in generated and u not in local:
            fail("macros", f"\\{u} is used and nothing defines it")
    # Orphaned macros are reported as one line, not fifty.  They accumulate
    # whenever the prose is rewritten around a number, and a wall of warnings
    # is a wall the reader stops reading.
    orphans = sorted(g for g in generated if g not in used)
    if orphans:
        warn("macros",
             f"{len(orphans)} generated macro(s) the prose no longer uses: "
             + ", ".join("\\" + o for o in orphans))
    return len(generated)


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
    bodies = {"the text": re.sub(r"\\(?:sub)*section\*?\{", " ", src)}
    for p in also:
        if os.path.isfile(p):
            bodies[os.path.basename(p)] = open(p, encoding="utf-8").read()
    n = 0
    for raw in open(path, encoding="utf-8"):
        line = raw.split("#")[0].strip()
        if not line or "|" not in line:
            continue
        pref, alts = line.split("|", 1)
        pref = pref.strip()
        for alt in (a.strip() for a in alts.split(",")):
            if not alt:
                continue
            n += 1
            for where, body in bodies.items():
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


def check_float_placement(pdf):
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
    for page, txt in enumerate(pages, 1):
        if bib_page is None and re.search(r"^\[1\]\s", txt, re.M):
            bib_page = page
        for m in re.finditer(r"^(Figure|Table) (\d+):", txt, re.M):
            caption_page.setdefault((m.group(1), m.group(2)), page)
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
        if rp is not None and cpage - rp > 2:
            warn("floats",
                 f"{name} is first cited on page {rp} and printed on "
                 f"page {cpage}")
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
    nflt = check_float_placement(os.path.join(base, args.pdf))
    ngls = check_glossary(
        src, os.path.join(base, args.glossary),
        also=[os.path.join(base, f) for f in args.also.split(",") if f])
    print(f"  {nbib} references, {nflo} floats, {nfil} included files, "
          f"{ntab} tables, {nmac} generated macros, {nqty} quantities, "
          f"{ngls} glossary rules, {nflt} typeset floats")

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
