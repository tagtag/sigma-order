r"""Every symbol the maths uses, and where it is first used.

Written after $\sigma'$ was found in two sentences with no definition
anywhere: the existing checks look at macros that are generated and not
quoted, and at words the glossary governs, and neither of them asks whether
a symbol appearing in the text was ever introduced.

This does not decide.  It inventories: each distinct symbol-like token in
maths mode, how often it occurs, and the sentence its first occurrence sits
in, grouped so that the ones worth looking at come first.  A symbol used
twice in sixty pages is the shape $\sigma'$ had.

  python audit_symbols.py <paper dir> [--all]

Without --all, tokens that are plainly structure (\frac, \left, \text) or
that resolve to a \newcommand in main.tex are summarised rather than
listed.
"""
import io
import os
import re
import sys

PAPER = sys.argv[1] if len(sys.argv) > 1 else "."
SHOW_ALL = "--all" in sys.argv
os.chdir(PAPER)

# LaTeX machinery: present in maths, never a quantity of the paper's own.
STRUCTURE = set("""
frac dfrac tfrac sqrt left right big Big bigg Bigg langle rangle lvert rvert
lVert rVert vert Vert lfloor rfloor lceil rceil quad qquad , ; ! : space
text textrm textit textbf emph mathrm mathit mathbf mathcal mathbb mathsf
operatorname log exp ln sin cos tan max min sup inf lim argmax argmin
sum prod int oint partial nabla cdot cdots ldots dots vdots ddots
times div pm mp leq geq neq approx equiv sim simeq propto ll gg
in notin subset subseteq supset cup cap setminus emptyset forall exists
to rightarrow leftarrow mapsto Rightarrow Leftarrow iff circ
begin end label ref eqref cite texttt textsc hspace vspace
displaystyle scriptstyle limits nolimits overline underline widehat hat
tilde bar vec dot ddot prime ast star dagger colon mid
array matrix pmatrix bmatrix cases aligned align split equation
nonumber notag qedhere square blacksquare
middle bigl bigr biggl biggr Bigl Bigr le ge ne lt gt neg land lor
mathopen mathclose mathrel mathbin phantom hphantom vphantom rule
newcommand renewcommand DeclareMathOperator ensuremath
""".split())


def expand(text, depth=0):
    if depth > 6:
        return text
    def sub(m):
        f = m.group(1)
        p = f if f.endswith(".tex") else f + ".tex"
        try:
            return expand(strip_comments(io.open(p, encoding="utf-8").read()),
                          depth + 1)
        except Exception:
            return ""
    return re.sub(r"\\input\{([^}]+)\}", sub, text)


def strip_comments(t):
    return re.sub(r"(?<!\\)%.*", "", t)


def math_spans(src):
    """(start, end) of every maths segment: $...$, \\[...\\], equation envs."""
    spans = []
    for m in re.finditer(r"(?<!\\)\$(.+?)(?<!\\)\$", src, re.S):
        spans.append((m.start(1), m.end(1)))
    for env in ("equation", "equation\\*", "align", "align\\*", "gather"):
        for m in re.finditer(r"\\begin\{%s\}(.*?)\\end\{%s\}" % (env, env),
                             src, re.S):
            spans.append((m.start(1), m.end(1)))
    return spans


def main():
    raw = strip_comments(io.open("main.tex", encoding="utf-8").read())
    src = expand(raw)

    defined = set(re.findall(r"\\(?:re)?newcommand\*?\{\\([A-Za-z]+)\}", src))
    defined |= set(re.findall(r"\\DeclareMathOperator\*?\{\\([A-Za-z]+)\}", src))
    mp = os.path.join("tables", "macros.tex")
    if os.path.isfile(mp):
        defined |= set(re.findall(r"\\(?:re)?newcommand\*?\{\\([A-Za-z]+)\}",
                                  io.open(mp, encoding="utf-8").read()))

    # token -> list of absolute positions
    hits = {}
    for a, b in math_spans(src):
        seg = src[a:b]
        for m in re.finditer(r"\\[A-Za-z]+\s*(?:\^\{?\\?prime\}?|')?|"
                             r"(?<![A-Za-z\\])[A-Za-z]'", seg):
            tok = re.sub(r"\s+", "", m.group(0))
            base = tok.lstrip("\\").rstrip("'").split("^")[0]
            if base in STRUCTURE:
                continue
            hits.setdefault(tok, []).append(a + m.start())

    def context(pos, w=90):
        lo = max(0, pos - w)
        s = re.sub(r"\s+", " ", src[lo:pos + w]).strip()
        return s

    # Single letters and \mathcal{X}.  Without this pass the tool misses
    # exactly what it was written to find: $\mathcal{S}$ was used once,
    # defined nowhere, and the command-token pass above cannot see it
    # because \mathcal is structure.  A letter used two or three times in
    # sixty pages is the shape to look at; the workhorses are listed by
    # name only.
    letters = {}
    for a, b in math_spans(src):
        seg = src[a:b]
        for m in re.finditer(r"\\math(?:cal|bb|frak|scr)\{([A-Za-z])\}", seg):
            letters.setdefault("mathcal " + m.group(1), []).append(a + m.start())
        # \mathrm{l2r} and friends are words, not variables: a letter
        # inside \mathrm/\text/\texttt is spelling, and counting it put
        # a spurious "l(9x)" in the list.
        plain = re.sub(r"\\(?:mathrm|text|texttt|textsc|mathsf|operatorname)"
                       r"\{[^{}]*\}", " ", seg)
        for m in re.finditer(r"(?<![A-Za-z\\])([A-Za-z])(?![A-Za-z])", plain):
            letters.setdefault(m.group(1), []).append(a + m.start())

    own, std, primed = [], [], []
    for tok, pos in sorted(hits.items(), key=lambda kv: len(kv[1])):
        base = tok.lstrip("\\").rstrip("'").split("^")[0]
        if "'" in tok or "prime" in tok:
            primed.append((tok, pos))
        elif base in defined:
            own.append((tok, pos))
        else:
            std.append((tok, pos))

    def show(title, items, note=""):
        print("\n" + "=" * 70)
        print(title, note)
        print("=" * 70)
        for tok, pos in items:
            print("\n%-24s %dx   first at char %d" % (tok, len(pos), pos[0]))
            print("    ..." + context(pos[0]) + "...")

    rare = sorted(((k, v) for k, v in letters.items() if len(v) <= 12),
                  key=lambda kv: len(kv[1]))
    common = sorted(((k, v) for k, v in letters.items() if len(v) > 12),
                    key=lambda kv: -len(kv[1]))

    show("PRIMED SYMBOLS",
         primed, "-- the shape sigma' had; a prime is rarely introduced")
    show("NOT A \\newcommand OF THIS PAPER", std,
         "-- Greek letters and plain symbols; each needs a sentence that "
         "introduces it")
    show("SINGLE LETTERS AND CALLIGRAPHIC, 12 USES OR FEWER", rare,
         "-- the shape \\mathcal{S} had: used once or twice, introduced "
         "nowhere")
    print("\n" + "=" * 70)
    print("SINGLE LETTERS IN HEAVY USE (>12x) -- names only")
    print("=" * 70)
    print("  " + "  ".join("%s(%d)" % (k, len(v)) for k, v in common))

    if SHOW_ALL:
        show("PAPER MACROS", own, "-- defined in main.tex")
    else:
        print("\n" + "=" * 70)
        print("PAPER MACROS (defined in main.tex): %d distinct, "
              "%d uses -- pass --all to list"
              % (len(own), sum(len(p) for _, p in own)))
        print("=" * 70)
        print("  " + "  ".join(t for t, _ in sorted(own)))


main()
