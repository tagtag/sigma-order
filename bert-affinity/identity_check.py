#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Numerical verification of the identity

    sigma = (1/L) sum_k E_{x_{-k} ~ mu} [ J( mu(.|x_{-k}) || p_theta(.|x_{-k}) ) ]

where J(m,q) = KL(m||q) + KL(q||m) is the Jeffreys divergence, mu is the
stationary distribution of the single-site Glauber chain built from p_theta,
and the left-hand side is the Schnakenberg entropy production computed from
probability fluxes.

Derivation sketch
-----------------
For a single-site move x -> y differing only at site k we have x_{-k} = y_{-k},
so with m(.) = mu(.|x_{-k}), q(.) = p_theta(.|x_{-k}), u = x_k, v = y_k:

    mu(x) P(x->y) / ( mu(y) P(y->x) ) = m(u) q(v) / ( m(v) q(u) )

Putting r(u) = log m(u) - log q(u), the one-step path KL becomes

    sum_{u,v} m(u) q(v) [ r(u) - r(v) ] = E_m[r] - E_q[r] = KL(m||q) + KL(q||m)

The two sides are therefore equal exactly, not up to a bound.

Consequences checked here
-------------------------
  * sigma = 0  <=>  p_theta equals the conditionals of the distribution the
    Glauber sampler actually converges to.  (J = 0 iff the two agree.)
  * sigma is computable from the MODEL ALONE -- no access to the truth pi.
  * By contrast the conditional-loss excess
        eps = (1/L) sum_k E_{x_{-k} ~ pi} [ KL( pi(.|x_{-k}) || p_theta(.|x_{-k}) ) ]
    requires pi.  eps, sigma and KL(mu||pi) are also reported so their sizes
    can be compared.

Note on what sigma does NOT say: sigma > 0 does not imply mu is far from pi.
If mu happened to equal pi, sigma would still be the Jeffreys error of p_theta
against pi's conditionals.  sigma measures disagreement between the trained
conditionals and the sampled distribution, not distance from the truth.
"""

import argparse
import importlib.util
import json
import os
import time

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "mep", os.path.join(HERE, "mlm_entropy_production.py"))
mep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mep)

L, V = mep.L, mep.V
EPS = 1e-300


def grid(vec):
    """length V^L vector -> (V,)*L array indexed [x_1,...,x_L]."""
    return vec.reshape((V,) * L)


def site_views(mu, cond, k):
    """Return mu(x_{-k}), mu(.|x_{-k}), p_theta(.|x_{-k}) aligned on x_{-k}."""
    MU = grid(mu)
    Amu = np.moveaxis(MU, k, -1)                       # (V,)*(L-1) + (V,)
    marg = Amu.sum(-1)
    mcond = Amu / np.maximum(marg, EPS)[..., None]

    Ck = cond[:, k, :].reshape((V,) * L + (V,))
    q = np.take(Ck, 0, axis=k)                         # same x_{-k} ordering
    return marg, mcond, q


def jeffreys_sigma(mu, cond):
    """RHS of the identity."""
    tot = 0.0
    per_site = []
    for k in range(L):
        marg, m, q = site_views(mu, cond, k)
        m = np.maximum(m, EPS); q = np.maximum(q, EPS)
        J = ((m - q) * (np.log(m) - np.log(q))).sum(-1)
        s = float((marg * J).sum())
        per_site.append(s)
        tot += s
    return tot / L, per_site


def site_divergences(mu, pi, cond_model, cond_true):
    """All per-site divergences taken under mu, summed over sites.

    Tests the approximate-tensorization shape

        KL(mu||pi) <= C * sum_k E_{mu}[ KL( mu(.|x_-k) || pi(.|x_-k) ) ]

    and the triangle that splits that sum through the learned conditionals:
        mu_k  --(A, part of sigma)--  p_theta_k  --(B, model error)--  pi_k
    """
    T = A = B = Bp = 0.0
    tvT = tvA = tvB = 0.0
    for k in range(L):
        marg, m, q = site_views(mu, cond_model, k)      # m = mu_k, q = p_theta_k
        _, _, p = site_views(mu, cond_true, k)          # p = pi_k  (same x_-k grid)
        m = np.maximum(m, EPS); q = np.maximum(q, EPS); p = np.maximum(p, EPS)
        T += float((marg * (m * (np.log(m) - np.log(p))).sum(-1)).sum())
        A += float((marg * (m * (np.log(m) - np.log(q))).sum(-1)).sum())
        B += float((marg * (q * (np.log(q) - np.log(p))).sum(-1)).sum())
        # B' = E_{mu_k}[ log(p_theta_k / pi_k) ]: a cross term, not a KL.
        # Computed INDEPENDENTLY of A and T so that T = A + B' is a real check.
        Bp += float((marg * (m * (np.log(q) - np.log(p))).sum(-1)).sum())
        tvT += float((marg * 0.5 * np.abs(m - p).sum(-1)).sum())
        tvA += float((marg * 0.5 * np.abs(m - q).sum(-1)).sum())
        tvB += float((marg * 0.5 * np.abs(q - p).sum(-1)).sum())
    return {"T_sum_KL_mu_pi": T, "A_sum_KL_mu_ptheta": A, "B_sum_KL_ptheta_pi": B,
            "Bprime_cross_term": Bp, "T_minus_A_minus_Bp": T - A - Bp,
            "TV_mu_pi": tvT, "TV_mu_ptheta": tvA, "TV_ptheta_pi": tvB}


def conditional_excess(pi, cond_model, cond_true):
    """eps = (1/L) sum_k E_{x ~ pi}[ KL( pi(.|x_-k) || p_theta(.|x_-k) ) ]."""
    tot = 0.0
    for k in range(L):
        marg, _, q = site_views(pi, cond_model, k)
        _, pt, _ = site_views(pi, cond_true, k)        # pi(.|x_-k) via grid
        pt = np.maximum(pt, EPS); q = np.maximum(q, EPS)
        kl = (pt * (np.log(pt) - np.log(q))).sum(-1)
        tot += float((marg * kl).sum())
    return tot / L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--bs", type=int, default=256)
    ap.add_argument("--n", type=int, default=100000)
    ap.add_argument("--configs", type=str, default="32:1,96:3",
                    help="comma separated d:nlayer")
    ap.add_argument("--coupling", type=float, default=1.0)
    ap.add_argument("--out", default=os.path.join(HERE, "identity_results.json"))
    args = ap.parse_args()

    t0 = time.time()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    rng = np.random.default_rng(mep.SEED)
    torch.manual_seed(mep.SEED)

    h, J = mep.build_truth(rng, coupling=args.coupling)
    states = mep.all_states()
    index = np.full((V,) * L, -1, dtype=np.int64)
    index[tuple(states.T)] = np.arange(len(states))
    lp = mep.truth_logp(states, h, J); lp -= lp.max()
    pi = np.exp(lp); pi /= pi.sum()
    cond_true = mep.truth_conditionals(states, h, J)
    states_t = torch.tensor(states)
    print(f"# device={device} L={L} V={V} states={V**L} N={args.n}", flush=True)

    rows = []

    def report(name, cond, extra):
        src, dst, rate = mep.glauber_edges(cond, states, index)
        mu, it, resid = mep.stationary(src, dst, rate, len(states))
        sig_flux = mep.entropy_production(mu, src, dst, rate, len(states))
        sig_jeff, per_site = jeffreys_sigma(mu, cond)
        eps = conditional_excess(pi, cond, cond_true)
        m = pi > 0
        kl_mu_pi = float(np.sum(mu[m] * np.log(np.maximum(mu[m], EPS) / pi[m])))
        rel = abs(sig_flux - sig_jeff) / max(abs(sig_flux), 1e-300)
        sd = site_divergences(mu, pi, cond, cond_true)
        C_emp = kl_mu_pi / sd["T_sum_KL_mu_pi"] if sd["T_sum_KL_mu_pi"] > 1e-18 else float("nan")
        r = {"name": name, "sigma_flux": sig_flux, "sigma_jeffreys": sig_jeff,
             "rel_err": rel, "eps_cond_excess": eps, "kl_mu_pi": kl_mu_pi,
             "per_site_jeffreys": per_site, "power_iters": it,
             "residual": float(resid), "C_empirical": C_emp}
        r.update(sd); r.update(extra)
        rows.append(r)
        print(f"\n--- {name} ---")
        print(f"  sigma (flux formula)      = {sig_flux:.12e}")
        print(f"  sigma (Jeffreys identity) = {sig_jeff:.12e}")
        print(f"  relative difference       = {rel:.3e}")
        print(f"  eps  (cond. loss excess)  = {eps:.6e}")
        print(f"  KL(mu||pi)                = {kl_mu_pi:.6e}")
        print(f"  T = sum_k E_mu KL(mu_k||pi_k)      = {sd['T_sum_KL_mu_pi']:.6e}")
        print(f"  C_empirical = KL(mu||pi)/T         = {C_emp:.4f}")
        print(f"  A = sum_k E_mu KL(mu_k||p_theta_k) = {sd['A_sum_KL_mu_ptheta']:.6e}"
              f"   (<= L*sigma = {L*sig_flux:.6e})")
        print(f"  B'= sum_k E_mu[log(p_theta_k/pi_k)] = {sd['Bprime_cross_term']:.6e}")
        print(f"  identity check  T - A - B'          = {sd['T_minus_A_minus_Bp']:+.3e}"
              f"   (must be 0)")
        print(f"  B = sum_k E_mu KL(p_theta_k||pi_k) = {sd['B_sum_KL_ptheta_pi']:.6e}")
        print(f"  TV triangle: TV(mu,pi)={sd['TV_mu_pi']:.4e} <= "
              f"TV(mu,p)+TV(p,pi)={sd['TV_mu_ptheta']+sd['TV_ptheta_pi']:.4e}"
              f"  [{'OK' if sd['TV_mu_pi'] <= sd['TV_mu_ptheta']+sd['TV_ptheta_pi']+1e-12 else 'VIOLATED'}]")
        print(f"  per-site Jeffreys         = "
              + " ".join(f"{v:.4e}" for v in per_site), flush=True)

    # ---- the exact truth: sigma must be 0 both ways -------------------
    report("TRUE (exact MRF conditionals)", cond_true, {"d": None, "nlayer": None})

    draw = rng.choice(len(states), size=args.n, p=pi)
    data = torch.tensor(states[draw])

    for spec_ in args.configs.split(","):
        d, nl = (int(v) for v in spec_.split(":"))
        m, loss = mep.train_mlm(data, args.steps, args.bs, device,
                                seed=mep.SEED, d=d, nlayer=nl)
        m.eval()
        cond = mep.mlm_conditionals(m, states_t, device)
        report(f"MLM d={d} layers={nl}", cond,
               {"d": d, "nlayer": nl, "final_loss": loss})
        del m

    # AR control: sigma = 0, and then eps alone carries all the error
    m, loss = mep.train_ar(data, args.steps, args.bs, device,
                           seed=mep.SEED, d=32, nlayer=1)
    m.eval()
    lp_ar = mep.ar_joint_logp(m, states_t, device)
    cond = mep.conditionals_from_joint(lp_ar, states, index)
    report("AR d=32 layers=1", cond, {"d": 32, "nlayer": 1, "final_loss": loss})

    print()
    hdr = (f"{'model':<30}{'sigma_flux':>15}{'sigma_Jeff':>15}"
           f"{'rel.diff':>11}{'eps':>12}{'KL(mu||pi)':>13}")
    print("=" * len(hdr)); print(hdr); print("=" * len(hdr))
    for r in rows:
        print(f"{r['name']:<30}{r['sigma_flux']:>15.6e}{r['sigma_jeffreys']:>15.6e}"
              f"{r['rel_err']:>11.2e}{r['eps_cond_excess']:>12.4e}"
              f"{r['kl_mu_pi']:>13.4e}")
    print("=" * len(hdr))

    with open(args.out, "w") as f:
        json.dump({"L": L, "V": V, "N": args.n, "steps": args.steps,
                   "elapsed_sec": time.time() - t0, "rows": rows}, f, indent=1)
    print(f"\n# elapsed {time.time()-t0:.1f}s   wrote {args.out}")


if __name__ == "__main__":
    main()
