import numpy as np, itertools, math, json
import importlib.util
spec = importlib.util.spec_from_file_location("m", "mlm_entropy_production.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

rng = np.random.default_rng(m.SEED)
h, J = m.build_truth(rng, coupling=1.0)
states = m.all_states()
lp = m.truth_logp(states, h, J); lp -= lp.max()
pi = np.exp(lp); pi /= pi.sum()
cond = m.truth_conditionals(states, h, J)

# MLM floor: average over k of H(x_k | x_{-k})
hk = []
for k in range(m.L):
    p = cond[np.arange(len(states)), k, states[:, k]]
    hk.append(-float(np.sum(pi * np.log(p))))
mlm_floor = float(np.mean(hk))

# AR floor: H(x)/L
Hx = -float(np.sum(pi * np.log(pi)))
ar_floor = Hx / m.L

print(f"H(x)                      = {Hx:.4f} nats")
print(f"AR  floor  H(x)/L         = {ar_floor:.4f} nats   (measured AR  loss 1.1941 -> excess {1.1941-ar_floor:+.4f})")
print(f"MLM floor  mean H(xk|x-k) = {mlm_floor:.4f} nats   (measured MLM loss 1.1360 -> excess {1.1360-mlm_floor:+.4f})")
print(f"per-site H(xk|x-k): " + " ".join(f"{v:.4f}" for v in hk))
