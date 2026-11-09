#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exact Schnakenberg entropy production of the single-site Glauber dynamics
induced by a masked language model, on a system with a KNOWN ground-truth
joint distribution.

Why this design
---------------
Iterative masked-token resampling on an MLM defines a Markov chain on token
sequences (Glauber dynamics).  For a move that changes exactly one site k,

    P(x -> y) = (1/L) * p_theta(y_k | x_{-k}).

If the conditionals p_theta come from a consistent joint pi, this chain is
reversible w.r.t. pi and its entropy production vanishes.  MLM conditionals
are generally NOT compatible with any joint, so the chain is a nonequilibrium
steady state with sigma > 0.  The question this script answers is: how large
is sigma, and what does it depend on?

We take L=6 sites and alphabet size V=4, so the state space is 4^6 = 4096.
Everything is then exactly enumerable:

  * the ground-truth pairwise MRF pi(x) and its exact conditionals,
  * the full 4096 x 4096 Glauber transition matrix for any model,
  * its stationary distribution mu (dominant left eigenvector),
  * the exact entropy production rate

        sigma = sum_{x != y} mu(x) P(x->y) log [ mu(x) P(x->y) /
                                                 ( mu(y) P(y->x) ) ]

  * and the Kolmogorov cycle affinities A_c on every 4-cycle.

No estimator, no sampling error, no Monte Carlo.

Models compared
---------------
  TRUE : exact conditionals of the ground-truth MRF.
         Detailed balance holds => sigma = 0 (numerical floor).
  AR   : a small autoregressive transformer.  It defines a consistent joint
         p_theta(x) by construction, so its induced Glauber chain is
         reversible and sigma = 0 EXACTLY, regardless of how badly it fits.
         This is the key control: the test measures CONSISTENCY, not accuracy.
  MLM  : a small masked transformer trained with single-token masking
         (the masking scheme that exactly matches single-site Glauber, i.e.
         the most favourable case for the MLM).  sigma > 0 is the result.

Sweeping the training-set size separates two contributions to sigma:
finite-data error, and the irreducible incompatibility of the objective.

Outputs results.json and prints a table.  CPU-only, a few minutes.
"""

import argparse
import itertools
import json
import math
import os
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

L = 6          # number of sites
V = 4          # alphabet size
MASK = V       # id of the [MASK] token (MLM vocab is V+1)
BOS = V        # id of the BOS token (AR vocab is V+1)
SEED = 0


# ----------------------------------------------------------------------
# Ground-truth pairwise MRF
# ----------------------------------------------------------------------
def build_truth(rng, coupling=1.0):
    """Random pairwise MRF on L sites: fields h[k,v], couplings J[k,l,v,w].

    Couplings are dense (all pairs) so that every site pair is genuinely
    coupled and no cycle is trivially zero.
    """
    h = rng.normal(0.0, 0.5, size=(L, V))
    J = np.zeros((L, L, V, V))
    for k, l in itertools.combinations(range(L), 2):
        # decay with distance so the model is not fully degenerate
        scale = coupling / (1.0 + (l - k))
        M = rng.normal(0.0, scale, size=(V, V))
        J[k, l] = M
        J[l, k] = M.T          # symmetric by construction
    return h, J


def all_states():
    return np.array(list(itertools.product(range(V), repeat=L)), dtype=np.int64)


def truth_logp(states, h, J):
    """Unnormalised log pi(x) for every state."""
    e = np.zeros(len(states))
    for k in range(L):
        e += h[k, states[:, k]]
    for k, l in itertools.combinations(range(L), 2):
        e += J[k, l, states[:, k], states[:, l]]
    return e


def truth_conditionals(states, h, J):
    """Exact p(x_k = v | x_{-k}) for every state and site.  (S, L, V)."""
    S = len(states)
    out = np.zeros((S, L, V))
    for k in range(L):
        logits = np.tile(h[k][None, :], (S, 1))          # (S,V)
        for l in range(L):
            if l == k:
                continue
            logits += J[k, l, :, states[:, l]].T if False else J[k, l][:, states[:, l]].T
        logits -= logits.max(axis=1, keepdims=True)
        p = np.exp(logits)
        out[:, k, :] = p / p.sum(axis=1, keepdims=True)
    return out


# ----------------------------------------------------------------------
# Tiny transformers
# ----------------------------------------------------------------------
class Tiny(nn.Module):
    def __init__(self, vocab, d=96, nlayer=3, nhead=4, causal=False):
        super().__init__()
        self.causal = causal
        self.emb = nn.Embedding(vocab, d)
        self.pos = nn.Parameter(torch.zeros(1, L + 1, d))
        layer = nn.TransformerEncoderLayer(
            d_model=d, nhead=nhead, dim_feedforward=4 * d,
            batch_first=True, dropout=0.0, norm_first=True,
            activation="gelu")
        self.enc = nn.TransformerEncoder(layer, nlayer)
        self.ln = nn.LayerNorm(d)
        self.head = nn.Linear(d, vocab)

    def forward(self, x):
        n = x.shape[1]
        z = self.emb(x) + self.pos[:, :n]
        mask = None
        if self.causal:
            mask = torch.triu(torch.ones(n, n, dtype=torch.bool, device=x.device), 1)
        z = self.enc(z, mask=mask)
        return self.head(self.ln(z))


def train_mlm(data, steps, bs, device, seed=0, d=96, nlayer=3):
    torch.manual_seed(seed)
    m = Tiny(V + 1, d=d, nlayer=nlayer, causal=False).to(device)
    opt = torch.optim.AdamW(m.parameters(), lr=3e-3, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps)
    N = len(data)
    g = torch.Generator(device="cpu").manual_seed(seed + 1)
    for t in range(steps):
        idx = torch.randint(0, N, (bs,), generator=g)
        x = data[idx].to(device)
        pos = torch.randint(0, L, (bs,), generator=g).to(device)   # exactly one mask
        tgt = x.gather(1, pos[:, None]).squeeze(1)
        xin = x.clone()
        xin.scatter_(1, pos[:, None], MASK)
        logits = m(xin)
        lg = logits.gather(1, pos[:, None, None].expand(-1, 1, V + 1)).squeeze(1)
        loss = F.cross_entropy(lg[:, :V], tgt)
        opt.zero_grad(); loss.backward(); opt.step(); sched.step()
    return m, loss.item()


def train_ar(data, steps, bs, device, seed=0, d=96, nlayer=3):
    torch.manual_seed(seed)
    m = Tiny(V + 1, d=d, nlayer=nlayer, causal=True).to(device)
    opt = torch.optim.AdamW(m.parameters(), lr=3e-3, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps)
    N = len(data)
    g = torch.Generator(device="cpu").manual_seed(seed + 1)
    bos = torch.full((bs, 1), BOS, dtype=torch.long)
    for t in range(steps):
        idx = torch.randint(0, N, (bs,), generator=g)
        x = data[idx]
        inp = torch.cat([bos, x], 1).to(device)
        logits = m(inp)[:, :-1, :V]
        loss = F.cross_entropy(logits.reshape(-1, V), x.reshape(-1).to(device))
        opt.zero_grad(); loss.backward(); opt.step(); sched.step()
    return m, loss.item()


# ----------------------------------------------------------------------
# Conditionals from the trained models, for every state
# ----------------------------------------------------------------------
@torch.no_grad()
def mlm_conditionals(m, states_t, device, chunk=4096):
    """(S, L, V) array of p_theta(x_k = v | x_{-k})."""
    S = len(states_t)
    out = np.zeros((S, L, V), dtype=np.float64)
    for k in range(L):
        xin = states_t.clone()
        xin[:, k] = MASK
        ps = []
        for s in range(0, S, chunk):
            lg = m(xin[s:s + chunk].to(device))[:, k, :V].double()
            ps.append(F.softmax(lg, -1).cpu().numpy())
        out[:, k, :] = np.concatenate(ps, 0)
    return out


@torch.no_grad()
def ar_joint_logp(m, states_t, device, chunk=4096):
    """Exact log p_theta(x) for every state under the AR model."""
    S = len(states_t)
    res = np.zeros(S, dtype=np.float64)
    for s in range(0, S, chunk):
        x = states_t[s:s + chunk].to(device)
        bos = torch.full((len(x), 1), BOS, dtype=torch.long, device=device)
        lg = m(torch.cat([bos, x], 1))[:, :-1, :V].double()
        lp = F.log_softmax(lg, -1)
        res[s:s + len(x)] = lp.gather(-1, x[..., None]).squeeze(-1).sum(-1).cpu().numpy()
    return res


def conditionals_from_joint(logp, states, index):
    """Exact p(x_k|x_{-k}) derived from a full joint over all states."""
    S = len(states)
    out = np.zeros((S, L, V))
    for k in range(L):
        cols = np.zeros((S, V))
        for v in range(V):
            alt = states.copy()
            alt[:, k] = v
            cols[:, v] = logp[index[tuple(alt.T)]]
        cols -= cols.max(1, keepdims=True)
        p = np.exp(cols)
        out[:, k, :] = p / p.sum(1, keepdims=True)
    return out


# ----------------------------------------------------------------------
# Glauber chain: stationary distribution and exact entropy production
# ----------------------------------------------------------------------
def glauber_edges(cond, states, index):
    """Return arrays (src, dst, rate) for all single-site moves."""
    S = len(states)
    src, dst, rate = [], [], []
    for k in range(L):
        for v in range(V):
            alt = states.copy()
            alt[:, k] = v
            j = index[tuple(alt.T)]
            keep = j != np.arange(S)
            src.append(np.arange(S)[keep])
            dst.append(j[keep])
            rate.append(cond[keep, k, v] / L)
    return (np.concatenate(src), np.concatenate(dst), np.concatenate(rate))


def stationary(src, dst, rate, S, iters=20000, tol=1e-14):
    mu = np.full(S, 1.0 / S)
    stay = 1.0 - np.bincount(src, weights=rate, minlength=S)
    for t in range(iters):
        new = np.bincount(dst, weights=mu[src] * rate, minlength=S) + mu * stay
        new /= new.sum()
        d = np.abs(new - mu).sum()
        mu = new
        if d < tol:
            break
    return mu, t, d


def entropy_production(mu, src, dst, rate, S):
    """sigma = sum_{x!=y} mu(x)P(x->y) log[ mu(x)P(x->y) / (mu(y)P(y->x)) ]."""
    # build reverse-rate lookup
    key = src.astype(np.int64) * S + dst.astype(np.int64)
    rkey = dst.astype(np.int64) * S + src.astype(np.int64)
    order = np.argsort(key)
    ks, rs = key[order], rate[order]
    pos = np.searchsorted(ks, rkey)
    pos = np.clip(pos, 0, len(ks) - 1)
    ok = ks[pos] == rkey
    rev = np.where(ok, rs[pos], 0.0)

    f = mu[src] * rate            # forward probability flux
    b = mu[dst] * rev             # backward probability flux
    m = (f > 1e-300) & (b > 1e-300)
    return float(np.sum(f[m] * np.log(f[m] / b[m])))


def cycle_affinities(cond, states, index, rng, n_cycles=4000):
    """Kolmogorov affinities on random 4-cycles (two sites, two tokens each)."""
    out = []
    S = len(states)
    pairs = list(itertools.combinations(range(L), 2))
    for _ in range(n_cycles):
        x = states[rng.integers(S)].copy()
        i, j = pairs[rng.integers(len(pairs))]
        a, b = x[i], x[j]
        ap = rng.integers(V)
        bp = rng.integers(V)
        if ap == a or bp == b:
            continue
        def c(site, val_i, val_j, tok):
            y = x.copy(); y[i] = val_i; y[j] = val_j
            return cond[index[tuple(y[:, None])][0], site, tok]
        # log-odds at site i with j=b and j=b'
        D_i_b = math.log(c(i, a, b, ap)) - math.log(c(i, a, b, a))
        D_i_bp = math.log(c(i, a, bp, ap)) - math.log(c(i, a, bp, a))
        D_j_a = math.log(c(j, a, b, bp)) - math.log(c(j, a, b, b))
        D_j_ap = math.log(c(j, ap, b, bp)) - math.log(c(j, ap, b, b))
        C_i = D_i_bp - D_i_b
        C_j = D_j_ap - D_j_a
        out.append({"i": int(i), "j": int(j), "gap": int(j - i),
                    "C_i": C_i, "C_j": C_j, "A": C_j - C_i})
    return out


# ----------------------------------------------------------------------
def analyse(name, cond, states, index, rng, pi):
    src, dst, rate = glauber_edges(cond, states, index)
    S = len(states)
    mu, it, resid = stationary(src, dst, rate, S)
    sigma = entropy_production(mu, src, dst, rate, S)
    aff = cycle_affinities(cond, states, index, rng)
    A = np.array([r["A"] for r in aff])
    m = pi > 0
    kl = float(np.sum(mu[m] * np.log(np.maximum(mu[m], 1e-300) / pi[m])))
    return {
        "model": name,
        "sigma": sigma,
        "sigma_per_site": sigma / L,
        "kl_mu_pi": kl,
        "affinity_mean_abs": float(np.abs(A).mean()),
        "affinity_rms": float(np.sqrt((A ** 2).mean())),
        "affinity_max_abs": float(np.abs(A).max()),
        "n_cycles": int(len(A)),
        "power_iters": int(it),
        "residual": float(resid),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--bs", type=int, default=256)
    ap.add_argument("--sizes", type=int, nargs="+", default=[1000, 10000, 100000])
    ap.add_argument("--coupling", type=float, default=1.0)
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "results.json"))
    args = ap.parse_args()

    t0 = time.time()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    rng = np.random.default_rng(SEED)
    torch.manual_seed(SEED)
    print(f"# device={device}  L={L} V={V}  states={V**L}", flush=True)

    # ---- ground truth ------------------------------------------------
    h, J = build_truth(rng, coupling=args.coupling)
    states = all_states()
    index = np.full((V,) * L, -1, dtype=np.int64)
    index[tuple(states.T)] = np.arange(len(states))
    lp = truth_logp(states, h, J)
    lp -= lp.max()
    pi = np.exp(lp); pi /= pi.sum()
    print(f"# truth entropy = {-np.sum(pi*np.log(pi)):.4f} nats "
          f"(uniform = {L*math.log(V):.4f})", flush=True)

    cond_true = truth_conditionals(states, h, J)
    states_t = torch.tensor(states)

    results = []
    r = analyse("TRUE (exact MRF conditionals)", cond_true, states, index,
                np.random.default_rng(1), pi)
    r["train_n"] = None; r["final_loss"] = None
    results.append(r)
    print(f"# TRUE sigma = {r['sigma']:.3e}  (detailed balance => 0)", flush=True)

    # ---- sample training data once at the largest size ---------------
    big = max(args.sizes)
    draw = rng.choice(len(states), size=big, p=pi)
    data_all = torch.tensor(states[draw])

    for N in args.sizes:
        data = data_all[:N]

        mlm, l_m = train_mlm(data, args.steps, args.bs, device, seed=SEED)
        mlm.eval()
        cond_mlm = mlm_conditionals(mlm, states_t, device)
        rm = analyse(f"MLM", cond_mlm, states, index, np.random.default_rng(1), pi)
        rm["train_n"] = N; rm["final_loss"] = l_m
        results.append(rm)
        print(f"# MLM N={N:<7d} loss={l_m:.4f}  sigma={rm['sigma']:.4e}  "
              f"rms|A|={rm['affinity_rms']:.4f}  KL(mu||pi)={rm['kl_mu_pi']:.4e}",
              flush=True)

        ar, l_a = train_ar(data, args.steps, args.bs, device, seed=SEED)
        ar.eval()
        lp_ar = ar_joint_logp(ar, states_t, device)
        cond_ar = conditionals_from_joint(lp_ar, states, index)
        ra = analyse(f"AR", cond_ar, states, index, np.random.default_rng(1), pi)
        ra["train_n"] = N; ra["final_loss"] = l_a
        results.append(ra)
        print(f"# AR  N={N:<7d} loss={l_a:.4f}  sigma={ra['sigma']:.4e}  "
              f"rms|A|={ra['affinity_rms']:.4f}  KL(mu||pi)={ra['kl_mu_pi']:.4e}",
              flush=True)

    # ---- report ------------------------------------------------------
    print()
    hdr = (f"{'model':<8}{'N':>8}{'loss':>9}{'sigma':>13}{'sigma/site':>13}"
           f"{'rms|A|':>10}{'max|A|':>10}{'KL(mu||pi)':>13}")
    print("=" * len(hdr)); print(hdr); print("=" * len(hdr))
    for r in results:
        nm = r["model"].split()[0]
        N = "-" if r["train_n"] is None else str(r["train_n"])
        ls = "-" if r["final_loss"] is None else f"{r['final_loss']:.4f}"
        print(f"{nm:<8}{N:>8}{ls:>9}{r['sigma']:>13.4e}"
              f"{r['sigma_per_site']:>13.4e}{r['affinity_rms']:>10.4f}"
              f"{r['affinity_max_abs']:>10.4f}{r['kl_mu_pi']:>13.4e}")
    print("=" * len(hdr))

    with open(args.out, "w") as f:
        json.dump({"L": L, "V": V, "steps": args.steps, "bs": args.bs,
                   "coupling": args.coupling, "device": device,
                   "elapsed_sec": time.time() - t0,
                   "results": results}, f, indent=1)
    print(f"\n# elapsed {time.time()-t0:.1f}s   wrote {args.out}")


if __name__ == "__main__":
    main()
