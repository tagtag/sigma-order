#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Does the capacity table's non-zero sigma_EP come from the model, or from
the way its transition rates were built?

The Glauber rate is

    w(x -> y) = (1/L) p_theta(y_k | x_{-k})      x, y differing at site k only

and the table builds p_theta(. | x_{-k}) differently for the two model
classes, because only one of them has a choice:

  * an autoregressive model emits no such conditional -- no head of it sees
    both sides of a position -- so the only route is to recover it from the
    joint: score the V complete sequences that differ at site k alone and
    normalise;

  * a masked model emits it directly, in one forward pass, which is what it
    was trained to do and what sampling from it uses.  It can ALSO be given
    the first route, by first choosing a joint.

The table reports the masked models on the second route and the
autoregressive one on the first.  That asymmetry is forced -- there is no
other route for the autoregressive model -- but it leaves a question the
table cannot answer on its own: is 0.0259 a property of the masked model, or
of having used the direct route?

This script answers it.  It takes one trained masked model and builds w both
ways, from three different joints, on the same 4096 states.  If the direct
route is what produces the number, the recovered routes will not reproduce
it; and if they return zero, that zero is not evidence about the model, since
Eq. (14) makes any joint-derived set of conditionals reversible.  What is
evidence is the distance between the two sets of conditionals, which is
reported as a Jeffreys divergence -- the quantity Section 4.3 says the floor
equals.

The three joints are the ones a reader would propose:

    pll   exp(PLL(x)) normalised over the state space
    l2r   the any-order chain rule, unmasking left to right
    r2l   the same, right to left

The last two are the two terms of the sigma of Section 6, so this run also
reports that quantity in the exactly solvable system, where the model's
incompatibility is known exactly rather than inferred.

    python3 bayes_route_control.py --d 160 --nlayer 3

Writes bayes_route_control.json beside this file.
"""

import argparse
import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mlm_entropy_production as mep  # noqa: E402

L, V, MASK, SEED = mep.L, mep.V, mep.MASK, mep.SEED


@torch.no_grad()
def chain_rule_logp(model, states_t, order, device, chunk=4096):
    """log P_pi(x) for every state, by the any-order chain rule.

    At step t the positions already unmasked carry their own tokens and every
    other position is MASK; the factor is read at position order[t].  Summed
    over t this is a genuine log-probability for the fixed order: it
    normalises to one over sequences, which no sum of p(x_k | x_{-k}) does.
    """
    S = len(states_t)
    out = np.zeros(S, dtype=np.float64)
    for s in range(0, S, chunk):
        x = states_t[s:s + chunk].to(device)
        tot = torch.zeros(len(x), dtype=torch.float64, device=device)
        for t, k in enumerate(order):
            xin = x.clone()
            xin[:, list(order[t:])] = MASK
            lg = model(xin)[:, k, :V].double()
            tot += F.log_softmax(lg, -1).gather(
                -1, x[:, k, None]).squeeze(-1)
        out[s:s + len(x)] = tot.cpu().numpy()
    return out


@torch.no_grad()
def pll_logscore(model, states_t, device, chunk=4096):
    """sum_k log p_theta(x_k | x_{-k}).  Not the log of anything."""
    S = len(states_t)
    out = np.zeros(S, dtype=np.float64)
    for k in range(L):
        xin = states_t.clone()
        xin[:, k] = MASK
        for s in range(0, S, chunk):
            lg = model(xin[s:s + chunk].to(device))[:, k, :V].double()
            lp = F.log_softmax(lg, -1)
            out[s:s + len(lg)] += lp.gather(
                -1, states_t[s:s + len(lg), k, None].to(device)
            ).squeeze(-1).cpu().numpy()
    return out


def normalise(logp):
    v = np.asarray(logp, dtype=np.float64)
    v = v - v.max()
    p = np.exp(v)
    return p / p.sum()


def jeffreys(a, b):
    """Mean symmetrised KL between two (S, L, V) sets of conditionals."""
    a = np.clip(a, 1e-300, None)
    b = np.clip(b, 1e-300, None)
    return float(np.mean(np.sum((a - b) * (np.log(a) - np.log(b)), axis=-1)))


# the capacity grid of capacity_sweep.py, so a sweep here lines up row for
# row with the table the paper already reports
GRID = [(32, 1), (64, 2), (96, 3), (128, 3), (160, 3)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--d", type=int, default=160)
    ap.add_argument("--nlayer", type=int, default=3)
    ap.add_argument("--grid", action="store_true",
                    help="run every width of capacity_sweep.py, and report "
                         "whether the two instruments move together")
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--bs", type=int, default=256)
    ap.add_argument("--n", type=int, default=100000)
    ap.add_argument("--coupling", type=float, default=1.0)
    ap.add_argument("--tol", type=float, default=1e-10,
                    help="a joint-derived route must give |sigma_EP| below this")
    ap.add_argument("--out", default=os.path.join(
        HERE, "bayes_route_control.json"))
    args = ap.parse_args()

    t0 = time.time()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # The same ground truth, the same draw, the same training call as
    # capacity_sweep.py, so the direct route reproduces that table's row
    # rather than measuring a different model.
    rng = np.random.default_rng(SEED)
    torch.manual_seed(SEED)
    h, J = mep.build_truth(rng, coupling=args.coupling)
    states = mep.all_states()
    index = np.full((V,) * L, -1, dtype=np.int64)
    index[tuple(states.T)] = np.arange(len(states))
    lp = mep.truth_logp(states, h, J)
    lp -= lp.max()
    pi = np.exp(lp)
    pi /= pi.sum()
    states_t = torch.tensor(states)
    draw = rng.choice(len(states), size=args.n, p=pi)
    data = torch.tensor(states[draw])
    print(f"# device={device}  L={L} V={V}  states={V**L}  "
          f"d={args.d} nlayer={args.nlayer}", flush=True)

    widths = GRID if args.grid else [(args.d, args.nlayer)]
    sweep = []
    for width_d, width_nl in widths:
        sweep.append(one_width(width_d, width_nl, args, device, data,
                               states, index, pi, states_t))
    if args.grid:
        report_sweep(sweep)
    out = {"states": int(len(states)), "train_n": args.n,
           "steps": args.steps, "rows": sweep,
           "wall_sec": time.time() - t0}
    json.dump(out, open(args.out, "w"), indent=1)
    print(f"\n# wrote {args.out}  [{time.time() - t0:.0f}s]")
    print("# Every route through a joint returned zero; the model's own "
          "conditionals did not.")
    print("# The number in the capacity table is a property of the "
          "conditionals the model emits,")
    print("# not of the route chosen to turn them into rates.")


def report_sweep(rows):
    from scipy.stats import spearmanr
    d = [r["d"] for r in rows]
    se = [r["head"]["sigma"] for r in rows]
    sg = [r["sigma_l2r_r2l"]["mean_abs"] for r in rows]
    print()
    print(f"{'d':>5}{'params':>9}{'loss':>9}{'sigma_EP':>12}{'mean|sigma|':>13}")
    for r in rows:
        print(f"{r['d']:>5}{r['params']:>9}{r['final_loss']:>9.4f}"
              f"{r['head']['sigma']:>12.4e}"
              f"{r['sigma_l2r_r2l']['mean_abs']:>13.4f}")
    rho_e, p_e = spearmanr(d, se)
    rho_g, p_g = spearmanr(d, sg)
    rho_x, p_x = spearmanr(se, sg)
    print(f"\n# sigma_EP against width      rho = {rho_e:+.2f}  p = {p_e:.3f}")
    print(f"# mean|sigma| against width   rho = {rho_g:+.2f}  p = {p_g:.3f}")
    print(f"# the two against each other  rho = {rho_x:+.2f}  p = {p_x:.3f}")


def one_width(d, nlayer, args, device, data, states, index, pi, states_t):
    t1 = time.time()
    model, loss = mep.train_mlm(data, args.steps, args.bs, device,
                                seed=SEED, d=d, nlayer=nlayer)
    model.eval()
    nparams = sum(q.numel() for q in model.parameters())
    print(f"# d={d} nlayer={nlayer} params={nparams} loss={loss:.4f}  "
          f"[{time.time() - t1:.0f}s]", flush=True)

    # ---- route 1: what the model emits -------------------------------
    cond_head = mep.mlm_conditionals(model, states_t, device)
    r_head = mep.analyse("MLM (head)", cond_head, states, index,
                         np.random.default_rng(1), pi)
    print(f"# head route : sigma_EP = {r_head['sigma']:.4e}   "
          f"rms|A| = {r_head['affinity_rms']:.4f}", flush=True)

    # ---- route 2: recovered from a joint, three ways -----------------
    l2r = list(range(L))
    r2l = list(range(L - 1, -1, -1))
    # computed once: the two chain-rule scores are also the two terms of the
    # sigma of Section 6, read off below
    lp_l2r = chain_rule_logp(model, states_t, l2r, device)
    lp_r2l = chain_rule_logp(model, states_t, r2l, device)
    joints = {
        "pll": normalise(pll_logscore(model, states_t, device)),
        "l2r": normalise(lp_l2r),
        "r2l": normalise(lp_r2l),
    }

    rows = []
    for name, P in joints.items():
        cond = mep.conditionals_from_joint(np.log(np.clip(P, 1e-300, None)),
                                           states, index)
        r = mep.analyse(f"MLM (joint: {name})", cond, states, index,
                        np.random.default_rng(1), pi)
        d_j = jeffreys(cond_head, cond)
        rows.append({"route": name, "sigma": r["sigma"],
                     "affinity_rms": r["affinity_rms"],
                     "jeffreys_vs_head": d_j})
        print(f"# joint {name:<4}: sigma_EP = {r['sigma']:+.3e}   "
              f"rms|A| = {r['affinity_rms']:.2e}   "
              f"Jeffreys(head || joint) = {d_j:.4f}", flush=True)

    # ---- the sigma of Section 6, in the solvable system ---------------
    sig = (lp_l2r - lp_r2l) / float(L)
    print(f"# sigma (l2r - r2l)/L over all {len(states)} states: "
          f"median {np.median(sig):+.4f}  min {sig.min():+.4f}  "
          f"max {sig.max():+.4f}  mean|.| {np.abs(sig).mean():.4f}", flush=True)

    # ---- what the run has to establish --------------------------------
    bad = [r for r in rows if abs(r["sigma"]) > args.tol]
    assert not bad, (
        "a conditional set recovered from a joint must be reversible: "
        + ", ".join(f"{r['route']} gave {r['sigma']:.3e}" for r in bad))
    assert abs(r_head["sigma"]) > 1e3 * args.tol, (
        "the head route gave no entropy production, so this run says nothing "
        f"about the two routes: {r_head['sigma']:.3e}")
    assert all(r["jeffreys_vs_head"] > 0 for r in rows), \
        "the recovered conditionals are identical to the model's own"

    return {
        "d": d, "nlayer": nlayer, "params": nparams, "final_loss": loss,
        "head": {"sigma": r_head["sigma"],
                 "affinity_rms": r_head["affinity_rms"]},
        "joint_routes": rows,
        "sigma_l2r_r2l": {"median": float(np.median(sig)),
                          "min": float(sig.min()), "max": float(sig.max()),
                          "mean_abs": float(np.abs(sig).mean())},
        "wall_sec": time.time() - t1,
    }


if __name__ == "__main__":
    main()
