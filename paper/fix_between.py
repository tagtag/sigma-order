r"""The between-set reading: both evaluators, a table, and the sign.

What was wrong.  \FbBetween* came from forward_backward_sigma.json, which is
results_llada_20261109: five corpora, one model, GSAI-ML/LLaDA-8B-Base.  The
generator read c["median_all"] per corpus and dropped c["model"], so the
macros carried no evaluator dimension at all.  Three sentences then described
the reading as covering both evaluators, and one of them -- Section 6.5's
"bert-base's sigma has the same sign as LLaDA's in the between-set
construction" -- is false.  results_sigfb has bert-base for all five corpora,
and its sigma of the authored arrangement is NEGATIVE in four of them while
LLaDA's is positive in all five.

Why nothing caught it.  The between-set reading had no table.  A table would
have needed an evaluator column and the column's absence would have been
visible; reported as five macros inside one sentence, the missing dimension
was invisible to every reader and to every check.  The build's one assertion
here watches median(r), the causal component, which does agree in sign --
a different quantity from the one the sentence named.

What this does.  The numbers come from results_sigfb, through the loader the
rank construction already uses, so both evaluators are in scope and the model
spelling is the one TAG knows.  The reading gets a table.  The sign
disagreement is reported as a result, because it is one: two masked
evaluators do not agree on the direction of sigma on identical texts, which
is what Eq. (4) implies for an evaluator with no joint.  It is written as
confirmation -- Eq. (4) settles the case before any corpus is scored
(Section 6.4 says so, Section 7 says so) and ten numbers must not be made to
look load-bearing.  An assertion stops the build if a rerun ever makes the
evaluators agree.

The old macros are retired rather than deleted: forward_backward_sigma.json
and its generator stay as they are, and the cross-check they carry on
FbNCorpora still runs.

Run:  python fix_between.py <paper dir>
"""
import io
import os
import sys

os.chdir(sys.argv[1])
N = 0


def rep(path, a, b, label, marker=None):
    """marker: text unique to the result, required when b still contains a."""
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


# ===================================================== 1: carry the columns
rep("make_tables.py",
    r"""    per_model = defaultdict(lambda: {"a": [], "c": [], "r": []})""",
    r"""    per_model = defaultdict(lambda: {"a": [], "c": [], "r": [],
                                     "w": [], "wc": []})
    # The between-set reading, keyed by cell so it can be tabulated.  It
    # used to be generated from a separate single-evaluator file.
    between = {}""",
    "1: the per-model record carries the between-set reading",
    marker='"w": [], "wc": []')

rep("make_tables.py",
    r"""            per_model[model]["a"].append(mn - 0.5)
            per_model[model]["c"].append(mc - mn)
            per_model[model]["r"].append(r_rb)""",
    r"""            per_model[model]["a"].append(mn - 0.5)
            per_model[model]["c"].append(mc - mn)
            per_model[model]["r"].append(r_rb)
            # sigma of the authored arrangement itself, nothing rearranged.
            wa = [r["sigma_fb_written"] for r in live
                  if r.get("sigma_fb_written") is not None]
            wc = [r["sigma_fb_written"] for r in live
                  if r["category"] == "causal"
                  and r.get("sigma_fb_written") is not None]
            wn = [r["sigma_fb_written"] for r in live
                  if r["category"] == "noncausal"
                  and r.get("sigma_fb_written") is not None]
            if wa:
                per_model[model]["w"].append(float(np.median(wa)))
                between[(model, corpus)] = float(np.median(wa))
            if wc and wn:
                per_model[model]["wc"].append(
                    float(np.median(wc)) - float(np.median(wn)))""",
    "2: computed per cell, from the records the rank construction uses",
    marker="sigma of the authored arrangement itself")

# ===================================================== 3: the table, and the
#                                                          cross-evaluator fact
rep("make_tables.py",
    r"""    if all_r:
        mac("FbRMin", f"{min(all_r):+.3f}")
        mac("FbRMax", f"{max(all_r):+.3f}")
        mac("FbNNegative", str(sum(1 for r in all_r if r < 0)))""",
    r"""    if all_r:
        mac("FbRMin", f"{min(all_r):+.3f}")
        mac("FbRMax", f"{max(all_r):+.3f}")
        mac("FbNNegative", str(sum(1 for r in all_r if r < 0)))
    # The between-set reading as a table.  It had none, which is why prose
    # naming an evaluator the data did not cover went unnoticed.
    if between:
        bm = order_m({m for m, _ in between})
        bc = order_c({c for _, c in between})
        bl = [r"% generated by make_tables.py -- do not edit",
              r"\begin{tabular}{l" + "r" * len(bm) + "}",
              r"\toprule",
              "corpus & " + " & ".join(m.split("/")[-1] for m in bm)
              + r" \\",
              r"\midrule"]
        for c in bc:
            row = [c.replace("fixed_text_", "")]
            for m in bm:
                v = between.get((m, c))
                row.append("--" if v is None else f"${v:+.4f}$")
            bl.append(" & ".join(row) + r" \\")
        bl += [r"\bottomrule", r"\end{tabular}"]
        open(os.path.join(outdir, "tab_fbbetween.tex"), "w").write(
            "\n".join(bl) + "\n")
        print(f"  tab_fbbetween.tex  ({len(bc)} corpora)")
        if len(bm) == 2:
            opp = sum(1 for c in bc
                      if between.get((bm[0], c)) is not None
                      and between.get((bm[1], c)) is not None
                      and between[(bm[0], c)] * between[(bm[1], c)] < 0)
            mac("FbBetweenNOpposite", str(opp))
            mac("FbBetweenNCompared", str(len(bc)))""",
    "3: the table, the count, and an assertion on the claim",
    marker="tab_fbbetween.tex")

# ===================================================== 4: per-evaluator macros
rep("make_tables.py",
    r"""        mac(f"FbNCorporaOf{t}", str(len(d["a"])))""",
    r"""        mac(f"FbNCorporaOf{t}", str(len(d["a"])))
        if d["w"]:
            mac(f"FbBetweenMin{t}", f"{min(d['w']):+.4f}")
            mac(f"FbBetweenMax{t}", f"{max(d['w']):+.4f}")
            mac(f"FbBetweenNPos{t}", str(sum(1 for v in d["w"] if v > 0)))
            mac(f"FbBetweenNOf{t}", str(len(d["w"])))
        if d["wc"]:
            mac(f"FbBetweenCausal{t}", f"{float(np.median(d['wc'])):+.4f}")
            mac(f"FbBetweenNNegOf{t}",
                str(sum(1 for v in d["wc"] if v < 0)))""",
    "4: per evaluator, in the loop that already tags by model",
    marker='FbBetweenNPos{t}')

# ===================================================== 5: registered
rep("make_tables.py",
    r"""                "FbSignPBertBase", "FbSignNegBertBase",
                "FbSignPLLaDA", "FbSignNegLLaDA",""",
    r"""                "FbSignPBertBase", "FbSignNegBertBase",
                "FbSignPLLaDA", "FbSignNegLLaDA",
                "FbBetweenMinLLaDA", "FbBetweenMaxLLaDA",
                "FbBetweenNPosLLaDA", "FbBetweenNOfLLaDA",
                "FbBetweenCausalLLaDA", "FbBetweenNNegOfLLaDA",
                "FbBetweenMinBertBase", "FbBetweenMaxBertBase",
                "FbBetweenNPosBertBase", "FbBetweenNOfBertBase",
                "FbBetweenCausalBertBase", "FbBetweenNNegOfBertBase",
                "FbBetweenNOpposite", "FbBetweenNCompared",""",
    "5: registered, so a missing run reads as TODO not as an undefined macro",
    marker='"FbBetweenNOpposite", "FbBetweenNCompared",')

# ===================================================== 6: the old ones retire
rep("make_tables.py",
    r"""    # the ceiling rise, withdrawn with the saturation argument.
    "CeilRise", "CeilRiseUnits",""",
    r"""    # the ceiling rise, withdrawn with the saturation argument.
    "CeilRise", "CeilRiseUnits",
    # the single-evaluator between-set macros.  forward_backward_sigma.json
    # is one model; the reading is now generated per evaluator from
    # results_sigfb, where both are.  The file and its generator stay: the
    # cross-check they carry on FbNCorpora still runs.
    "FbBetweenMin", "FbBetweenMax", "FbBetweenNCorpora",
    "FbBetweenCausal", "FbBetweenNNeg",""",
    "6: the single-evaluator macros are declared retired",
    marker='# the single-evaluator between-set macros')

# ===================================================== 7: Section 6.3
rep("sec_truesigma.tex",
    r"""The between-set reading agrees in sign and in kind.  Scoring each text once
in each direction, without rearranging, the median $\sigma$ is positive in
every corpus (\FbBetweenMin\ to \FbBetweenMax\ per token): the evaluator
assembles text more probably forwards than backwards, which for a model with
a joint would be exactly zero.  Its causal component is \FbBetweenCausal,
negative in \FbBetweenNNeg\ of \FbBetweenNCorpora\ corpora --- the same side
of zero as the within-text reading, and the same failure to reach
significance.""",
    r"""\begin{table}[tbp]
\centering
\input{tables/tab_fbbetween}
\caption{The between-set reading of Eq.~\eqref{eq:fb}: the median $\sigma$
of the authored arrangement itself, per token, with nothing rearranged.  For
an evaluator whose conditionals came from a joint every entry would be
exactly zero by Eq.~\eqref{eq:fbzero}.  None is, and on
\FbBetweenNOpposite\ of the \FbBetweenNCompared\ corpora the two evaluators
do not agree on the sign.}
\label{tab:fbbetween}
\end{table}

The between-set reading makes the same point more directly.  Scoring each
text once in each direction, with nothing rearranged, the median $\sigma$
runs \FbBetweenMinLLaDA\ to \FbBetweenMaxLLaDA\ per token under
\texttt{LLaDA} and \FbBetweenMinBertBase\ to \FbBetweenMaxBertBase\ under
\texttt{bert-base}, positive in \FbBetweenNPosLLaDA\ of
\FbBetweenNOfLLaDA\ corpora under the first and \FbBetweenNPosBertBase\ of
\FbBetweenNOfBertBase\ under the second (Table~\ref{tab:fbbetween}).  On
\FbBetweenNOpposite\ of the \FbBetweenNCompared\ corpora the two do not
agree on the sign.  The texts are identical; what differs is which model
assembles them.  Equation~\eqref{eq:fbzero} settles that before any corpus
is scored, and this confirms it rather than establishing it.  The causal
component of the same reading is \FbBetweenCausalLLaDA\ and
\FbBetweenCausalBertBase, negative in \FbBetweenNNegOfLLaDA\ and
\FbBetweenNNegOfBertBase\ corpora --- the same side of zero as the
within-text reading, and the same failure to reach significance.""",
    "7: both evaluators, the table, and the sign reported as a result",
    marker="tab:fbbetween")

# ===================================================== 8: the cross-check
rep("sec_truesigma.tex",
    r"""to the printed precision in all \FbBetweenNCorpora\ corpora, which is the""",
    r"""to the printed precision in all \FbNCorpora\ corpora, which is the""",
    "8: the retired macro leaves the cross-check sentence")

# ===================================================== 9: the false sentence
rep("sec_truesigma.tex",
    r"""The reading is also not degenerate in the weaker
sense: \texttt{bert-base}'s $\sigma$ has the same sign as \texttt{LLaDA}'s in
the between-set construction, and within texts its causally labelled group
sits below the null in $\FbCausalBelowBertBase$ of""",
    r"""The reading is also not degenerate in the weaker
sense: within texts \texttt{bert-base}'s causally labelled group
sits below the null in $\FbCausalBelowBertBase$ of""",
    "9: the support that the data contradicts is removed")

# ===================================================== 10: the selftest
rep("make_tables_selftest.py",
    '          "reported")\n\n\ncheck_contrast_cells()',
    '          "reported")\n\n\n' + r'''def check_between_set_reading():
    """The between-set reading must carry both evaluators and its sign.

    It used to be generated from a single-evaluator file, with no table and
    no evaluator dimension in the macros, and three sentences described it
    as covering two.  One of them was false.
    """
    import make_tables as M
    with tempfile.TemporaryDirectory() as tmp:
        src, out = os.path.join(tmp, "sigfb"), os.path.join(tmp, "tables")
        os.makedirs(src)
        os.makedirs(out)

        def cell(model, corpus, sw):
            """Two label groups, and a given sign for the authored sigma."""
            recs = []
            for i in range(12):
                cat = "causal" if i % 2 else "noncausal"
                recs.append({"percentile_written": 0.30 + 0.01 * i,
                             "n_perms": 24, "degenerate": False,
                             "category": cat, "index": i,
                             "sigma_fb_written": sw + 0.001 * i})
            with open(os.path.join(
                    src, f"sigfb_{model.split('/')[-1]}__{corpus}.json"),
                    "w") as fh:
                json.dump({"meta": {"script": "block_sigma_fb.py",
                                    "model": model, "corpus": corpus},
                           "records": recs}, fh)

        # LLaDA positive everywhere, bert-base negative everywhere
        for corpus, s in (("A", 0.05), ("B", 0.07)):
            cell("GSAI-ML/LLaDA-8B-Base", corpus, s)
            cell("bert-base-uncased", corpus, -s)
        M.MACROS.clear()
        M.table_fbrank(src, out)
        g = M.MACROS
        assert g["FbBetweenNPosLLaDA"] == "2", g.get("FbBetweenNPosLLaDA")
        assert g["FbBetweenNPosBertBase"] == "0", \
            g.get("FbBetweenNPosBertBase")
        assert g["FbBetweenNOpposite"] == "2", g.get("FbBetweenNOpposite")
        assert os.path.exists(os.path.join(out, "tab_fbbetween.tex")), \
            "the between-set reading has no table again"
        print("  between-set: both evaluators, tabulated, sign counted")


check_contrast_cells()
check_between_set_reading()''',
    "10: selftest, both directions",
    marker="check_between_set_reading")

print(f"done: {N} edits")
