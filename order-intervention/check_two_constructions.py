#!/usr/bin/env python3
"""The two constructions of sigma agree on the authored arrangement.

Section 6.3 of the paper states that the rank construction and the direct
construction give the same sigma on the authored arrangement, "to the printed
precision in all 5 corpora".  Nothing in the paper prints both, so this
script is where that claim is checked.

  direct   forward_backward_sigma.py reads the per-text log P_pi(x) that
           order_intervention.py wrote for pi = l2r and pi = r2l, and forms
           sigma = [log P_l2r(x) - log P_r2l(x)] / L.  Its per-corpus median
           is forward_backward_sigma.json -> corpora[c]["median_all"].

  rank     block_sigma_fb.py scores the n! arrangements of each text and
           records sigma of the identity arrangement as sigma_fb_written.
           make_tables.py takes the median over texts and prints it as the
           upper block of tab_fbbetween.tex.

Both are medians over the same 200 texts of a corpus, so they are comparable
directly.  "Printed precision" is the 4 decimals of tab_fbbetween.tex, so
the test is that the two agree after rounding to 4 decimals.

    python3 -I check_two_constructions.py
    python3 -I check_two_constructions.py --json forward_backward_sigma.json \
                                          --table ../paper/tables/tab_fbbetween.tex

Exit status 0 if every corpus agrees, 1 otherwise.  No model, no network.
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON = os.path.join(HERE, "forward_backward_sigma.json")
DEFAULT_TABLE = os.path.join(HERE, os.pardir, "paper", "tables",
                             "tab_fbbetween.tex")
PRINTED_DECIMALS = 4


def read_direct(path):
    """{corpus: median sigma} from forward_backward_sigma.py's output."""
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    out, model = {}, None
    for corpus, rec in doc["corpora"].items():
        out[corpus] = float(rec["median_all"])
        model = rec.get("model", model)
    return out, model, doc.get("dir", "")


def read_table(path):
    """{corpus: {column: value}} from the upper block of tab_fbbetween.tex.

    The upper block is everything between the header row and the \\midrule
    that introduces the causal component; rows below it are a different
    quantity and must not be read here.
    """
    with open(path, encoding="utf-8") as fh:
        lines = [ln.strip() for ln in fh]
    body = [ln for ln in lines
            if ln.endswith(r"\\") and "&" in ln and "multicolumn" not in ln]
    if not body:
        raise SystemExit(f"no table rows found in {path}")
    header = [c.strip() for c in body[0].rstrip("\\").split("&")]
    columns = header[1:]
    rows, seen = {}, set()
    for ln in body[1:]:
        cells = [c.strip() for c in ln.rstrip("\\").split("&")]
        corpus = cells[0]
        if corpus in seen:      # second block: the causal component
            break
        seen.add(corpus)
        vals = {}
        for name, cell in zip(columns, cells[1:]):
            m = re.fullmatch(r"\$([-+]?[0-9.]+)\$", cell)
            if m:
                vals[name] = float(m.group(1))
        rows[corpus] = vals
    return rows


def pick_column(table, model):
    """The table column written by the evaluator the JSON was produced on."""
    if not table:
        raise SystemExit("empty table")
    leaf = (model or "").split("/")[-1]
    for name in next(iter(table.values())):
        if leaf and (name == leaf or leaf.startswith(name)
                     or name.startswith(leaf)):
            return name
    raise SystemExit(f"no column for model {model!r} in "
                     f"{sorted(next(iter(table.values())))}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=DEFAULT_JSON)
    ap.add_argument("--table", default=DEFAULT_TABLE)
    args = ap.parse_args()

    direct, model, rundir = read_direct(args.json)
    table = read_table(args.table)
    column = pick_column(table, model)

    print(f"direct   {os.path.basename(args.json)}  ({model})")
    print(f"         from {rundir}")
    print(f"rank     {os.path.relpath(args.table, HERE)}  column {column!r}")
    print(f"agreement tested at {PRINTED_DECIMALS} decimals, "
          f"the precision the table prints")
    print("=" * 62)
    print(f"{'corpus':<12}{'direct':>12}{'rank':>12}"
          f"{'|diff|':>14}  verdict")
    print("-" * 62)

    missing = sorted(set(direct) - set(table))
    bad = 0
    for corpus in sorted(table):
        if corpus not in direct:
            print(f"{corpus:<12}{'--':>12}{table[corpus][column]:>+12.4f}"
                  f"{'':>14}  NOT IN JSON")
            bad += 1
            continue
        a, b = direct[corpus], table[corpus][column]
        ok = round(a, PRINTED_DECIMALS) == round(b, PRINTED_DECIMALS)
        bad += not ok
        print(f"{corpus:<12}{a:>+12.6f}{b:>+12.4f}{abs(a - b):>14.2e}"
              f"  {'agree' if ok else 'DIFFER'}")
    for corpus in missing:
        print(f"{corpus:<12}{direct[corpus]:>+12.6f}{'--':>12}"
              f"{'':>14}  NOT IN TABLE")
        bad += 1
    print("=" * 62)

    if bad:
        print(f"FAIL  {bad} corpus/corpora do not agree.")
        return 1
    print(f"PASS  all {len(table)} corpora agree to {PRINTED_DECIMALS} "
          f"decimals.  The rank construction and the direct one")
    print("      return the same sigma on the authored arrangement.")
    print()
    print("Note: the two are not independent implementations.  "
          "block_sigma_fb.py imports")
    print("      load_texts and HFMaskedProvider from order_intervention.py; "
          "what they share")
    print("      is the text loader and the masked-model provider, "
          "not only the chain rule.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
