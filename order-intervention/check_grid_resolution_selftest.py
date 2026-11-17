#!/usr/bin/env python3
"""check_grid_resolution.py on fixtures whose answer is known.

Three cases, built here rather than taken from the measurements:

  fine    midranks at odd multiples of 1/2n!, which is what Eq.(midrank)
          produces when each authored arrangement is tied only with
          itself, plus a few degenerate texts at exactly 0.50.  Every
          check must pass.
  coarse  midranks at multiples of 1/n!.  Check [2] must fail: if the
          data really lived on the coarse grid, Section 5.3's claim would
          be an overstatement and the script has to say so.
  ragged  one midrank nudged off both grids.  Check [1] must fail.

Needs nothing but numpy and the script beside it.

    python3 -I check_grid_resolution_selftest.py
"""

import json
import os
import subprocess
import sys
import tempfile

NFAC = 24
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "check_grid_resolution.py")


def write_cells(root, values):
    """values: {(model, corpus, category): [midranks]}"""
    os.makedirs(root, exist_ok=True)
    bundles = {}
    for (model, corpus, cat), vals in values.items():
        bundles.setdefault((model, corpus), []).append((cat, vals))
    for (model, corpus), groups in bundles.items():
        records = []
        for cat, vals in groups:
            for i, v in enumerate(vals):
                records.append({"category": cat, "index": i,
                                "percentile_written": v, "n_perms": NFAC})
        path = os.path.join(root, f"blkord_{model}_{corpus}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"model": model, "corpus": corpus, "kind": "causal",
                       "records": records}, fh)


def series(kind, n, shift):
    """n midranks of the requested kind, deterministic."""
    out = []
    for i in range(n):
        a = (i * 7 + shift) % NFAC
        if kind == "fine":
            out.append((2 * a + 1) / (2 * NFAC))
        elif kind == "coarse":
            out.append(a / NFAC)
        else:
            raise ValueError(kind)
    return out


def run(root):
    p = subprocess.run([sys.executable, "-I", SCRIPT, "--blkord", root],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def case(name, kind, mangle=None, degenerate=0):
    with tempfile.TemporaryDirectory() as tmp:
        root = os.path.join(tmp, "results_blkord")
        values = {}
        for m, model in enumerate(("m-small", "m-large")):
            for c, corpus in enumerate(("corpA", "corpB")):
                for k, cat in enumerate(("causal", "noncausal")):
                    v = series(kind, 100, 3 * m + 5 * c + 11 * k)
                    for d in range(degenerate):
                        v[d] = 0.5
                    values[(model, corpus, cat)] = v
        if mangle:
            key = ("m-small", "corpA", "causal")
            values[key] = list(values[key])
            values[key][0] += 0.003
        write_cells(root, values)
        return run(root)


def main():
    bad = 0

    rc, out = case("fine", "fine", degenerate=2)
    if rc == 0 and "PASS" in out:
        print("  pass  fine     every check passes on the 1/48 grid")
    else:
        print(f"  FAIL  fine     exit {rc}")
        print("\n".join("          " + l for l in out.splitlines()[-8:]))
        bad += 1

    rc, out = case("coarse", "coarse")
    if rc == 1 and "multiple of 1/24" in out:
        print("  pass  coarse   check [2] rejects data on the 1/24 grid")
    else:
        print(f"  FAIL  coarse   exit {rc}, expected 1 with the [2] message")
        print("\n".join("          " + l for l in out.splitlines()[-8:]))
        bad += 1

    rc, out = case("ragged", "fine", mangle=True)
    if rc == 1 and "off the 1/48 grid" in out:
        print("  pass  ragged   check [1] catches a midrank off both grids")
    else:
        print(f"  FAIL  ragged   exit {rc}, expected 1 with the [1] message")
        print("\n".join("          " + l for l in out.splitlines()[-8:]))
        bad += 1

    print()
    if bad:
        print(f"FAIL  {bad} of 3 cases")
        return 1
    print("PASS  3 of 3 cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
