r"""The half of the between-set reading that still has no table, and the minus signs.

THE MISSING HALF.  tab_fbbetween was added because the between-set reading
was reported only as macros in prose, and prose naming an evaluator the
data did not cover went unnoticed.  It covers the authored $\sigma$.  The
causal component of the same reading -- four numbers, two evaluators by
two counts -- is still prose only, and the sentence says so itself:
"summarised rather than printed".

It is also the same defect twice over, because the two numbers are given
as a bare pair and so are the two counts: which evaluator each belongs to
is carried by the order alone, and the sentence before it had a device for
that ("under the first ... under the second") which this one drops.

The component is already computed per cell, one line above the place it
is not stored.  It becomes the lower block of the table, with the same
columns, and the prose points at it instead of summarising it.

THE MINUS SIGNS.  tab_token prints its numbers outside math mode, so
every negative value in it is a hyphen while the same number in Table 3 is
a minus.  The two tables sit on facing pages.  Section 6.3's two macro
pairs are used bare in text for the same reason.

Run:  python fix_tables3.py <paper dir>
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


# --------------------------------------------- 1 keep the component per cell
rep("make_tables.py",
    r'''            if wc and wn:
                per_model[model]["wc"].append(
                    float(np.median(wc)) - float(np.median(wn)))''',
    r'''            if wc and wn:
                comp = float(np.median(wc)) - float(np.median(wn))
                per_model[model]["wc"].append(comp)
                # Kept per cell as well, so the lower block of
                # tab_fbbetween can print what the prose used to
                # summarise.
                between_c[(model, corpus)] = comp''',
    "1a: the causal component is kept per cell")

# the dict has to exist; find where `between` is initialised
src = io.open("make_tables.py", encoding="utf-8").read()
m = re.search(r"^(\s*)between = \{\}\s*$", src, re.M)
assert m, "could not find where `between` is initialised"
if "between_c = {}" not in src:
    src = src[:m.end()] + "\n" + m.group(1) + "between_c = {}" + src[m.end():]
    io.open("make_tables.py", "w", encoding="utf-8").write(src)
    print("  1c: and the dict that holds it")
    N += 1
else:
    print("  (already) 1c: and the dict that holds it")

# --------------------------------------------- 2 the lower block
rep("make_tables.py",
    r'''        for c in bc:
            row = [c.replace("fixed_text_", "")]
            for m in bm:
                v = between.get((m, c))
                row.append("--" if v is None else f"${v:+.4f}$")
            bl.append(" & ".join(row) + r" \\")
        bl += [r"\bottomrule", r"\end{tabular}"]''',
    r'''        for c in bc:
            row = [c.replace("fixed_text_", "")]
            for m in bm:
                v = between.get((m, c))
                row.append("--" if v is None else f"${v:+.4f}$")
            bl.append(" & ".join(row) + r" \\")
        if any(between_c.get((m, c)) is not None for m in bm for c in bc):
            bl += [r"\midrule",
                   r"\multicolumn{%d}{l}{\emph{causal component}} \\"
                   % (len(bm) + 1)]
            for c in bc:
                row = [c.replace("fixed_text_", "")]
                for m in bm:
                    v = between_c.get((m, c))
                    row.append("--" if v is None else f"${v:+.4f}$")
                bl.append(" & ".join(row) + r" \\")
        bl += [r"\bottomrule", r"\end{tabular}"]''',
    "2: the lower block, same columns, from the same cells")

# --------------------------------------------- 3 the prose points at it
rep("sec_truesigma.tex",
    r'''is scored, and this confirms it rather than establishing it.  The causal
component of the same reading is \FbBetweenCausalLLaDA\ and
\FbBetweenCausalBertBase, negative in \FbBetweenNNegOfLLaDA\ and
\FbBetweenNNegOfBertBase\ corpora, summarised rather than printed --- the
same side of zero as the
within-text reading, and the same failure to reach significance.''',
    r'''is scored, and this confirms it rather than establishing it.  The causal
component of the same reading is the lower block of
Table~\ref{tab:fbbetween}: a median of $\FbBetweenCausalLLaDA$ under
\texttt{LLaDA} and $\FbBetweenCausalBertBase$ under \texttt{bert-base},
negative in \FbBetweenNNegOfLLaDA\ and \FbBetweenNNegOfBertBase\ corpora
respectively --- the same side of zero as the within-text reading, and the
same failure to reach significance.''',
    "3: printed, and each number tied to its evaluator")

rep("sec_truesigma.tex",
    r'''\caption{The between-set reading of Eq.~\eqref{eq:fb}: the median $\sigma$
of the authored arrangement itself, per token, with nothing rearranged.  For''',
    r'''\caption{The between-set reading of Eq.~\eqref{eq:fb}.  \emph{Upper block}:
the median $\sigma$ of the authored arrangement itself, per token, with
nothing rearranged.  \emph{Lower block}: the causal component of the same
reading, the median $\sigma$ of the causally labelled texts less that of
the non-causal ones, in the same cells.  For''',
    "4: the caption names both blocks")

# --------------------------------------------- 5 the minus signs
rep("make_tables.py",
    r'''            rcol = f"{t_rb:+.3f}" if np.isfinite(t_rb) else "--"
            lines.append(f"{name} & {corpus} & {len(tall)} & "
                         f"{t_med:.4f} & {b_med:.4f} & {rcol} \\\\")''',
    r'''            # In math mode, like every other generated table: outside it
            # a negative value prints a hyphen, and Table 1 sits beside
            # Table 3 where the same number carries a minus.
            rcol = f"${t_rb:+.3f}$" if np.isfinite(t_rb) else "--"
            lines.append(f"{name} & {corpus} & {len(tall)} & "
                         f"${t_med:.4f}$ & ${b_med:.4f}$ & {rcol} \\\\")''',
    "5a: Table 1's numbers in math mode")

rep("sec_truesigma.tex",
    r'''runs \FbBetweenMinLLaDA\ to \FbBetweenMaxLLaDA\ per token under
\texttt{LLaDA} and \FbBetweenMinBertBase\ to \FbBetweenMaxBertBase\ under''',
    r'''runs $\FbBetweenMinLLaDA$ to $\FbBetweenMaxLLaDA$ per token under
\texttt{LLaDA} and $\FbBetweenMinBertBase$ to $\FbBetweenMaxBertBase$ under''',
    "5b: and the macros the prose uses bare")

print(f"done: {N} edits")
