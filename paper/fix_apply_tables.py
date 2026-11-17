#!/usr/bin/env python3
"""The generator-side changes: make_tables.py for #82, #129, #151.

  #82   Equation (rb) gives n_1 and n_2 as "the group sizes" and never their
        values.  They are in the measurements -- the causal and non-causal
        counts of every (evaluator, corpus) cell -- so NPerGroup is read off
        those and defined only when every cell agrees, on the same rule
        enumeration_macros() already uses for the block count.

  #129  Section 5.4 says the rise in the causal strict-maximum fraction is
        carried by the smallest evaluator alone.  That is a claim about what
        survives its removal, so the remainder is measured:
        TrendCeilNDropRho is the same rank correlation with the
        smallest-parameter rung dropped.

  #151  Table 7's caption and the Section 6.3 text both say the table holds
        a signed-rank test of each label group against the 0.50 null.  It
        does not: its p column is the Mann--Whitney p between the two
        groups, and the Wilcoxon distance-from-null p values go only into
        macros.  table_fbrank() already computes them into all_disp, so they
        are printed as two columns.  The table then has the ten rows and two
        columns that FbNTestsDisp counts, and the prose's 10/10, 1/10 and
        max p can point at it.  Column order follows #171: evaluator,
        corpus, n, degen, causal, non-causal, p(c vs 0.50), p(nc vs 0.50),
        r, p(c vs nc).

Idempotent.  Run from the directory holding make_tables.py.

    python3 -I fix_apply_tables.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #151 (a): the column specification and the header ---------------
    ("make_tables.py",
     '        r"\\begin{tabular}{llrrrrrr}",\n'
     '        r"\\toprule",\n'
     '        r"evaluator & corpus & $n$ & degen & causal & non-causal & $r$ & $p$ \\\\",',
     '        r"\\begin{tabular}{llrrrrrrrr}",\n'
     '        r"\\toprule",\n'
     '        r"evaluator & corpus & $n$ & degen & causal & non-causal & "\n'
     '        r"$p_{c}$ & $p_{nc}$ & $r$ & $p$ \\\\",',
     "151a header"),

    # ---- #151 (b): keep the two p values instead of discarding them ------
    ("make_tables.py",
     "            # Is each set displaced from the null at all?  r is silent\n"
     "            # on this: both sets could sit at 0.50 and still differ.\n"
     "            for v in (pc, pn):\n"
     "                dd = np.asarray(v, float) - 0.5\n"
     "                if (dd != 0).sum() >= 6:\n"
     "                    try:\n"
     "                        q = float(wilcoxon(dd, alternative='two-sided').pvalue)\n"
     "                    except ValueError:\n"
     "                        continue\n"
     "                    all_disp.append(q)\n"
     "                    disp_by_model[model].append(q)",
     "            # Is each set displaced from the null at all?  r is silent\n"
     "            # on this: both sets could sit at 0.50 and still differ.\n"
     "            # These were computed and then thrown away, while the\n"
     "            # caption and Section 6.3 both said the table showed them.\n"
     "            # Keep them per group so the row can print both.\n"
     "            qdisp = {}\n"
     "            for side, v in ((\"c\", pc), (\"n\", pn)):\n"
     "                dd = np.asarray(v, float) - 0.5\n"
     "                if (dd != 0).sum() >= 6:\n"
     "                    try:\n"
     "                        q = float(wilcoxon(dd, alternative='two-sided').pvalue)\n"
     "                    except ValueError:\n"
     "                        continue\n"
     "                    qdisp[side] = q\n"
     "                    all_disp.append(q)\n"
     "                    disp_by_model[model].append(q)",
     "151b compute"),

    # ---- #151 (c): print them --------------------------------------------
    ("make_tables.py",
     '            lines.append(\n'
     '                f"{model.split(\'/\')[-1]} & {corpus.replace(\'fixed_text_\', \'\')}"\n'
     '                f" & {len(recs)} & {degen} & ${mc:.3f}$ & ${mn:.3f}$ & "\n'
     '                f"${r_rb:+.3f}$ & {tex_p(p_val)} \\\\\\\\")',
     '            lines.append(\n'
     '                f"{model.split(\'/\')[-1]} & {corpus.replace(\'fixed_text_\', \'\')}"\n'
     '                f" & {len(recs)} & {degen} & ${mc:.3f}$ & ${mn:.3f}$ & "\n'
     '                f"{tex_p(qdisp[\'c\']) if \'c\' in qdisp else \'---\'} & "\n'
     '                f"{tex_p(qdisp[\'n\']) if \'n\' in qdisp else \'---\'} & "\n'
     '                f"${r_rb:+.3f}$ & {tex_p(p_val)} \\\\\\\\")',
     "151c print"),

    # ---- #82: the group sizes --------------------------------------------
    ("make_tables.py",
     "    mac(\"NEval\", str(len(ar_only({m for m, _ in blk}, kinds))))\n"
     "    mac(\"NCorp\", str(len({c for _, c in blk})))",
     "    mac(\"NEval\", str(len(ar_only({m for m, _ in blk}, kinds))))\n"
     "    mac(\"NCorp\", str(len({c for _, c in blk})))\n"
     "    # Equation (rb) names n_1 and n_2 and the paper never gave their\n"
     "    # values.  They are in the measurements.  Define the macro only if\n"
     "    # every cell agrees, on the rule enumeration_macros() uses for the\n"
     "    # block count: a disagreement would make the sentence false, and an\n"
     "    # undefined macro prints as a TODO that make_arxiv.sh refuses.\n"
     "    sizes = set()\n"
     "    for recs in blk.values():\n"
     "        for cat in (\"causal\", \"noncausal\"):\n"
     "            sizes.add(sum(1 for q in recs if q[0] == cat))\n"
     "    sizes.discard(0)\n"
     "    if len(sizes) == 1:\n"
     "        mac(\"NPerGroup\", str(sizes.pop()))\n"
     "    else:\n"
     "        print(f\"  WARNING: label groups differ in size {sorted(sizes)}; \"\n"
     "              f\"the sentence giving n_1 = n_2 is false as written\")",
     "82 NPerGroup"),

    # ---- #129: the correlation with the smallest rung dropped ------------
    ("make_tables.py",
     '        mac(f"Trend{tag}NDistinct", str(len(set(yq.tolist()))))\n'
     '        mac(f"Trend{tag}Rho", f"{rho:+.2f}")\n'
     '        mac(f"Trend{tag}P", f"{pv:.3f}")',
     '        mac(f"Trend{tag}NDistinct", str(len(set(yq.tolist()))))\n'
     '        mac(f"Trend{tag}Rho", f"{rho:+.2f}")\n'
     '        mac(f"Trend{tag}P", f"{pv:.3f}")\n'
     '    # Section 5.4 says the rise in the causal strict-maximum fraction is\n'
     '    # carried by the smallest evaluator on its own.  That is a claim\n'
     '    # about what is left when it goes, so measure the remainder instead\n'
     '    # of describing it.\n'
     '    yc = series.get("ceiling")\n'
     '    if yc and len(yc) > 3 and np.all(np.isfinite(yc)):\n'
     '        yq = np.round(np.asarray(yc, float), 12)\n'
     '        i = int(np.argmin(par))\n'
     '        keep = [j for j in range(len(par)) if j != i]\n'
     '        rho_d, p_d, _ = spearman([par[j] for j in keep],\n'
     '                                 [yq[j] for j in keep])\n'
     '        mac("TrendCeilNDropRho", f"{rho_d:+.2f}")\n'
     '        mac("TrendCeilNDropP", f"{p_d:.3f}")\n'
     '        mac("TrendCeilNDropNEval", str(len(keep)))',
     "129 TrendCeilNDropRho"),

    # ---- make the three new macros TODO-able -----------------------------
    ("make_tables.py",
     '    expected = ["FbNTestsCausal", "FbBonferroni", "FbNSurviving",',
     '    expected = ["NPerGroup",\n'
     '                "TrendCeilNDropRho", "TrendCeilNDropP",\n'
     '                "TrendCeilNDropNEval",\n'
     '                "FbNTestsCausal", "FbBonferroni", "FbNSurviving",',
     "expected list"),

    # ---- #173 names the one positive cell, so FbRMax is in the prose -----
    ("make_tables.py",
     '    "FbRBertBase", "FbRLLaDA", "FbRMax", "FbRMin", "ToyCapMonotone",',
     '    "FbRBertBase", "FbRLLaDA", "FbRMin", "ToyCapMonotone",\n'
     '    # FbRMax came off this list when Section 6.3 began naming the one\n'
     '    # cell where r is positive (#173).  The retirement was right while\n'
     '    # the prose only said "one cell below".',
     "173 un-retire FbRMax"),

    # ---- #166 puts the two causal components back in the prose -----------
    ("make_tables.py",
     '    "FbCausalLLaDA", "FbCausalStepsBertBase", "FbCausalStepsLLaDA",',
     '    # FbCausalBertBase, FbCausalLLaDA and their step forms came off this\n'
     '    # list with #166: Section 6.3 now gives both readings\' causal\n'
     '    # components side by side, to show that they agree in direction and\n'
     '    # are not in the same units.',
     "166 un-retire the causal components"),

    ("make_tables.py",
     '"CtrlSigMedian", "CtrlSigMin", "CtrlSigmaHead", "FbCausalBertBase",',
     '"CtrlSigMedian", "CtrlSigMin", "CtrlSigmaHead",',
     "166 un-retire FbCausalBertBase"),

    # ---- #178 names the two ends of the Appendix A sweep -----------------
    ("make_tables.py",
     '    "CtrlDMax", "CtrlDMin", "CtrlSigMax", "CtrlSigMeanAbs",',
     '    "CtrlSigMax", "CtrlSigMeanAbs",',
     "178 un-retire CtrlDMin/CtrlDMax"),
]

FILES = sorted({e[0] for e in EDITS})


def apply_edits(root, dry_run=False):
    cache = {}
    for name in FILES:
        with open(os.path.join(root, name), encoding="utf-8") as fh:
            cache[name] = fh.read()
    made = skipped = passed = 0
    for edit in EDITS:
        name, old, new, label = edit[:4]
        later = edit[4] if len(edit) > 4 else None
        text = cache[name]
        # Which test means "already applied" depends on how the two
        # strings nest.  If old is a substring of new (an insertion), old
        # survives the edit, so only the presence of new can decide; if new
        # is a substring of old (a deletion), new is there before the edit,
        # so old has to be looked for first.
        done = (new in text) if old in new else (old not in text and new in text)
        if done:
            print(f"  skip  {label:<24} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                # A later batch rewrote this passage, so on a re-run neither
                # the old text nor this batch's own replacement is here.
                print(f"  pass  {label:<24} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<24} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<24} {name}")
        made += 1
    if not dry_run:
        for name, text in cache.items():
            with open(os.path.join(root, name), "w", encoding="utf-8") as fh:
                fh.write(text)
    return made, skipped, passed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    print("generator changes: make_tables.py for #82, #129, #151")
    print("-" * 60)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 60)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 60)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
