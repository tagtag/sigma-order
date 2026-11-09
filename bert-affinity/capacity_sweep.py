#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Capacity sweep: is the plateau of sigma in mlm_entropy_production.py caused by
finite DATA or by finite MODEL CAPACITY?

Training-set size is fixed at the largest value used before (N = 100,000) and
the model capacity (width d, depth nlayer) is varied.  Everything else -- data,
seed, optimizer, steps, masking scheme (exactly one masked token) -- is held
identical to the main run, so the only moving part is capacity.

Reading of the result:
  * sigma falls steadily with capacity  -> the plateau was capacity-limited,
    i.e. "the model had not learned enough".
  * sigma plateaus in capacity too      -> the residual is structural: the MLM
    parameterisation has no mechanism to make its conditionals mutually
    compatible, and throwing parameters at it does not install one.

One AR point is included as a control.  It must give sigma = 0 at ANY capacity,
since the chain rule makes its conditionals compatible by construction.
"""

import argparse
import importlib.util
import json
import os
import time

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("mep", os.path.join(HERE, "mlm_entropy_production.py"))
mep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mep)

# (d, nlayer) grid for the MLM, plus the AR control configs
MLM_GRID = [(32, 1), (64, 2), (96, 3), (128, 3), (160, 3)]
AR_GRID = [(32, 1)]


def nparams(m):
    return sum(p.numel() for p in m.parameters())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--bs", type=int, default=256)
    ap.add_argument("--n", type=int, default=100000)
    ap.add_argument("--coupling", type=float, default=1.0)
    ap.add_argument("--out", default=os.path.join(HERE, "capacity_results.json"))
    args = ap.parse_args()

    t0 = time.time()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    rng = np.random.default_rng(mep.SEED)
    torch.manual_seed(mep.SEED)
    print(f"# device={device}  L={mep.L} V={mep.V} states={mep.V**mep.L} "
          f"N={args.n} steps={args.steps}", flush=True)

    # ---- identical ground truth and data as the main run ----
    h, J = mep.build_truth(rng, coupling=args.coupling)
    states = mep.all_states()
    index = np.full((mep.V,) * mep.L, -1, dtype=np.int64)
    index[tuple(states.T)] = np.arange(len(states))
    lp = mep.truth_logp(states, h, J); lp -= lp.max()
    pi = np.exp(lp); pi /= pi.sum()
    states_t = torch.tensor(states)

    draw = rng.choice(len(states), size=args.n, p=pi)
    data = torch.tensor(states[draw])

    rows = []
    for (d, nl) in MLM_GRID:
        t1 = time.time()
        m, loss = mep.train_mlm(data, args.steps, args.bs, device,
                                seed=mep.SEED, d=d, nlayer=nl)
        m.eval()
        P = nparams(m)
        cond = mep.mlm_conditionals(m, states_t, device)
        r = mep.analyse("MLM", cond, states, index, np.random.default_rng(1), pi)
        r.update({"kind": "MLM", "d": d, "nlayer": nl, "params": P,
                  "final_loss": loss, "train_n": args.n,
                  "wall_sec": time.time() - t1})
        rows.append(r)
        print(f"# MLM d={d:<4d} L={nl}  params={P:<8d} loss={loss:.4f}  "
              f"sigma={r['sigma']:.4e}  rms|A|={r['affinity_rms']:.4f}  "
              f"KL={r['kl_mu_pi']:.4e}  [{r['wall_sec']:.0f}s]", flush=True)
        del m

    for (d, nl) in AR_GRID:
        t1 = time.time()
        m, loss = mep.train_ar(data, args.steps, args.bs, device,
                               seed=mep.SEED, d=d, nlayer=nl)
        m.eval()
        P = nparams(m)
        lp_ar = mep.ar_joint_logp(m, states_t, device)
        cond = mep.conditionals_from_joint(lp_ar, states, index)
        r = mep.analyse("AR", cond, states, index, np.random.default_rng(1), pi)
        r.update({"kind": "AR", "d": d, "nlayer": nl, "params": P,
                  "final_loss": loss, "train_n": args.n,
                  "wall_sec": time.time() - t1})
        rows.append(r)
        print(f"# AR  d={d:<4d} L={nl}  params={P:<8d} loss={loss:.4f}  "
              f"sigma={r['sigma']:.4e}  rms|A|={r['affinity_rms']:.4f}  "
              f"KL={r['kl_mu_pi']:.4e}  [{r['wall_sec']:.0f}s]", flush=True)
        del m

    hdr = (f"{'kind':<5}{'d':>5}{'L':>3}{'params':>9}{'loss':>9}"
           f"{'sigma':>12}{'rms|A|':>9}{'max|A|':>9}{'KL(mu||pi)':>12}")
    print(); print("=" * len(hdr)); print(hdr); print("=" * len(hdr))
    for r in rows:
        print(f"{r['kind']:<5}{r['d']:>5}{r['nlayer']:>3}{r['params']:>9}"
              f"{r['final_loss']:>9.4f}{r['sigma']:>12.4e}"
              f"{r['affinity_rms']:>9.4f}{r['affinity_max_abs']:>9.4f}"
              f"{r['kl_mu_pi']:>12.4e}")
    print("=" * len(hdr))

    with open(args.out, "w") as f:
        json.dump({"L": mep.L, "V": mep.V, "N": args.n, "steps": args.steps,
                   "bs": args.bs, "coupling": args.coupling, "device": device,
                   "elapsed_sec": time.time() - t0, "rows": rows}, f, indent=1)
    print(f"\n# elapsed {time.time()-t0:.1f}s   wrote {args.out}")


if __name__ == "__main__":
    main()
