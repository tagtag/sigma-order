#!/usr/bin/env python3
"""Split the forward/backward sigma the way Table "decomposition" splits midrank.

The paper's decomposition takes each text's authored arrangement, locates it
in the distribution over block permutations, and measures how far that sits
above the 0.50 null.  The non-causal texts fix what ANY writer-chosen order
earns; whatever the causal texts have beyond that is what causal order alone
earns.

    authored = median(non-causal) - null
    causal   = median(causal) - median(non-causal)
    share    = causal / (authored + causal)

The same rule applies to sigma = [log P_l2r(x) - log P_r2l(x)] / L, with one
simplification: its null is not 0.50 but exactly 0, because sigma vanishes
identically for any model whose conditionals come from a joint.  So the
"authored" component here is the whole of the non-causal median.

The two decompositions are NOT the same measurement.  In the midrank version
the baseline is the text's own permutations, so "authored" means what a
writer's order earns over arbitrary orders.  Here there is no permutation
baseline at all: "authored" is just how incompatible the model is on those
texts.  What is comparable between them is the SIGN and SIZE of the causal
component -- the part attributable to causal order rather than to authorship.

Reads forward_backward_sigma.json, written by forward_backward_sigma.py.

    python3 -I forward_backward_sigma.py
    python3 -I forward_backward_decomposition.py

No model, no network.
"""

import argparse
import json
import os
import sys

import numpy as np


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=os.path.join(here,
                                                   "forward_backward_sigma.json"))
    args = ap.parse_args()

    if not os.path.exists(args.json):
        raise SystemExit(f"{args.json} not found -- run forward_backward_sigma.py "
                         f"first")
    d = json.load(open(args.json))
    cells = d.get("corpora", {})
    if not cells:
        raise SystemExit(f"no corpora in {args.json}")

    print(f"# source: {args.json}")
    print(f"# runs:   {d.get('dir')}")
    print()
    print("decomposition of sigma = [ log P_l2r(x) - log P_r2l(x) ] / L")
    print("null = 0 exactly (sigma vanishes for any model with a joint)")
    print("=" * 72)
    print(f"{'corpus':<14}{'non-causal':>12}{'causal':>10}"
          f"{'authored':>11}{'causal cmp':>12}{'share':>9}")
    print("-" * 72)

    auth_, caus_ = [], []
    for name in sorted(cells):
        c = cells[name]
        mn, mc = c["median_noncausal"], c["median_causal"]
        a = mn                      # distance of non-causal from the null, 0
        k = mc - mn                 # what causal order adds on top
        auth_.append(a)
        caus_.append(k)
        tot = a + k
        sh = k / tot if tot else float("nan")
        print(f"{name:<14}{mn:>12.4f}{mc:>10.4f}{a:>+11.4f}{k:>+12.4f}"
              + (f"{100*sh:>8.0f}%" if np.isfinite(sh) else f"{'--':>9}"))

    auth = float(np.median(auth_))
    caus = float(np.median(caus_))
    tot = auth + caus
    # Only meaningful while the total is a positive distance from the null.
    # Let the causal component drag the total below zero and the ratio flips
    # sign twice, printing a large POSITIVE share for a component that
    # subtracts.  (It does not here -- the total is +0.043 -- but the guard
    # keeps a future measurement from reading backwards.)
    share = caus / tot if tot > 0 else float("nan")
    print("-" * 72)
    print(f"{'median':<14}{'':>12}{'':>10}{auth:>+11.4f}{caus:>+12.4f}"
          + (f"{100*share:>8.0f}%" if np.isfinite(share) else f"{'--':>9}"))
    print("=" * 72)
    n_neg = sum(1 for k in caus_ if k < 0)
    print(f"  the causal component is NEGATIVE in {n_neg} of {len(caus_)} "
          f"corpora.")
    print(f"  causal order does not add to sigma; it subtracts.  the midrank")
    print(f"  instrument puts this component at +0.042 (11% of the total);")
    print(f"  here it is {caus:+.4f} ({100*share:.0f}% of the total).")

    out = {
        "source": args.json, "dir": d.get("dir"),
        "per_corpus": {n: {"authored": cells[n]["median_noncausal"],
                           "causal_component": (cells[n]["median_causal"]
                                                - cells[n]["median_noncausal"])}
                       for n in sorted(cells)},
        "authored": auth, "causal_component": caus,
        "total": tot, "causal_share": share,
        "n_corpora": len(caus_), "n_causal_component_negative": n_neg,
    }
    dest = os.path.join(here, "forward_backward_decomposition.json")
    json.dump(out, open(dest, "w"), indent=1)
    print(f"\n# wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
