# Authored order dominates fixed-text entropy production

Code and measurements for the paper *Authored order dominates fixed-text
entropy production: a measure without a zero, and a contrast without a
criterion*.

The paper re-examines a quantity that has been read as an entropy production
for a fixed text,

```
sigma = [ log P(x) - log P(x~) ] / L
```

where `x~` is `x` with its order reversed. The published measurements are
reproduced here, independently, to 1e-13 on the released per-text values.
What this work adds is an instrument and two negative results.

## The instrument

Score the same sentences in **all `n!` orders**. Writing `x_pi` for the blocks
concatenated in the order `pi`, block reversal of `x_pi` is exactly
`x_{pi o rev}`, so

```
sigma(pi) = [ S(x_pi) - S(x_{pi o rev}) ] / L  =  - sigma(pi o rev)
```

identically, for any score `S`. The map `pi -> pi o rev` is a
measure-preserving involution on the symmetric group, so the set of `sigma`
values over a uniformly drawn `pi` is **exactly symmetric about zero** — as an
identity, not as an empirical finding. The position of the written order
within its own permutation set is therefore unitless, bounded, equal to 0.50
for any score blind to sentence order, and comparable across scorer types that
`sigma` itself cannot be compared across. Each text becomes its own control.

Two consequences of the same identity are worth stating, because both are easy
to get wrong:

* Comparing the written order against a **shuffled** one compares it against
  the *centre* of a symmetric set, which is zero by construction. Such a
  comparison can only restate `sigma(id) > 0`. It carries no information, and
  an earlier version of this work drew a conclusion from it before noticing.
* The rank must **split ties**. A score that cannot distinguish the
  arrangements gives `sigma(pi) = 0` for every `pi`, and a count of
  `#{sigma <= sigma(id)}` then reports `n!/n! = 1.00` — "the most
  forward-costly arrangement there is" — for a model that cannot tell them
  apart. The midrank puts that case at exactly 0.50. Both behaviours are
  asserted in `order-intervention/block_order_selftest.py`.

## The results

Five evaluators, five corpora, 200 texts each, all `4! = 24` orders enumerated
exactly.

| evaluator | params | direction | authored | causal | causal share |
|---|---|---|---|---|---|
| `bert-base-uncased`     | 110M | masked | +0.000 | +0.208 | 100% |
| `gpt2`                  | 117M | causal | +0.354 | +0.042 |  11% |
| `bert-large-uncased`    | 340M | masked | +0.062 | +0.208 |  77% |
| `Qwen/Qwen3-4B-Base`    |   4B | causal | +0.396 | +0.042 |  10% |
| `GSAI-ML/LLaDA-8B-Base` |   8B | masked | +0.354 | +0.083 |  19% |

`authored` is the median distance of the **non-causal** texts' written order
from the 0.50 null: what any authored order earns. It uses no causal
judgement. `causal` is what the causally labelled texts show beyond that.

**First result, requiring no judgement about causality.** The written order of
a text whose sentence order is *arbitrary* is already far from the null for any
capable evaluator, and the effect grows monotonically with capacity: +0.000 at
110M, +0.062 at 340M, +0.354 at 8B within one masked family. An
autoregressive model reaches the same level at 117M, about 68 times less
capacity, because its factorisation already runs in the order under test.
Together with the fact that `sigma` is not commensurable between scorer types,
grows with capacity, and has no reference configuration for a single text, a
bare `sigma` cannot be read as a quantity of causal structure.

**Second result, and the limit on it.** The labelled contrast is robust — it
appears in both model classes and does not decay with capacity — but the labels
record only that a language model, asked for a passage whose sentences stand in
a causal sequence, produced one. No independent criterion is applied. The five
corpora vary the *generating model* while holding one prompt pair fixed, so
their agreement rules out generator idiosyncrasy and not construct validity.
What the contrast is a contrast *of* is not established by these data, and no
refinement of the measurement supplies it.

## Reproducing

Nothing here needs a GPU except the two largest evaluators, and those took
about 25 minutes each on one A100. Everything else runs on CPU.

```bash
git clone https://github.com/<your-login>/sigma-order.git
cd sigma-order
pip install "transformers<5" huggingface_hub scipy numpy torch

# the corpora
git clone --depth 1 https://github.com/taksagawa/Paper2026.git

# verify the implementation before spending any compute (no weights needed)
python3 -I order-intervention/block_order_selftest.py
python3 -I order-intervention/pll_selftest.py

# one evaluator, one corpus: the within-text permutation test
python3 order-intervention/block_order_pll.py \
    --model bert-base-uncased --kind masked \
    --texts Paper2026/gpt2/text_sets2/fixed_text_Opus46.json \
    --max-perms 24 --out results_blkord/blkord_bert-base-uncased__Opus46__0-1.json

# the original between-set protocol
python3 order-intervention/pll_sigma.py \
    --model bert-base-uncased --kind masked \
    --texts Paper2026/gpt2/text_sets2/fixed_text_Opus46.json \
    --out results_pll/pll_bert-base-uncased__Opus46__0-1.json

# aggregate, then rebuild the paper from the JSONs
python3 order-intervention/merge_blkord.py --dir results_blkord
python3 order-intervention/merge_pll.py    --dir results_pll
cd paper && sh build_paper.sh
```

For a GPU evaluator add `--device cuda --dtype bfloat16`, and for LLaDA also
`--mask-token-id 126336 --max-batch 32`.

Every number in the paper, in the tables and in the running text alike, is
generated by `paper/make_tables.py` from these JSON files, and every figure by
`paper/make_figures.py`. No figure is typed into the LaTeX source, so
rerunning the measurements regenerates the prose.

## Layout

```
order-intervention/
  block_order_pll.py        the within-text permutation test (the main instrument)
  block_order_selftest.py   its correctness checks, no weights required
  pll_sigma.py              the original between-set protocol, both scorer types
  pll_selftest.py           its correctness checks, no weights required
  aoar_core.py              any-order log-likelihood, reversals, order generation
  aoar_selftest.py          order-independence and normalisation checks
  order_intervention.py     any-order runner for masked diffusion models
  merge_blkord.py           aggregation and the decomposition
  merge_pll.py              aggregation for the between-set protocol
  results_*/                measured JSON, one file per (evaluator, corpus)
  README.md                 working notes, including what was retracted and why
bert-affinity/
  mlm_entropy_production.py exact Schnakenberg entropy production on a known joint
  capacity_sweep.py         the capacity sweep in that system
  identity_check.py         a Jeffreys-divergence identity, verified numerically
  reproduce_sagawa_stats.py independent reproduction of the published statistics
paper/
  main.tex                  the paper
  make_tables.py            every table and every quoted number
  make_figures.py           every figure
  build_paper.sh            measurements -> tables -> figures -> PDF
  make_arxiv.sh             assemble the arXiv bundle and verify it builds alone
```

## Self-tests

Each instrument carries checks that run without model weights, and they are
the reason to trust the numbers rather than the code's appearance:

* `block_order_selftest.py` — the permutation set is closed under reversal and
  contains the identity; the `n!` values of `sigma` sum to zero; the midrank is
  free to take any value in its range under an arbitrary score (so the test is
  not degenerate); an order-blind score yields exactly 0.50 while a naive `<=`
  count would yield 1.00.
* `pll_selftest.py` — each content token is masked exactly once and no special
  token is ever masked or scored; both reversals are involutions; a
  direction-neutral score gives `sigma = 0` exactly, which is the null the real
  measurement reads against.
* `aoar_selftest.py` — order-independence of the any-order chain rule to
  1.8e-15 and normalisation to 4.4e-16.

## What this work got wrong on the way

Kept here because the record is part of the method, and because both mistakes
are ones a reader might repeat:

1. A **shuffle control** was run and produced `r = 0.9857, p = 1e-17`, which
   looks decisive and is empty: the antisymmetry above forces it. See
   `order-intervention/shuffle_control.py`, retained and marked as retracted.
2. On the scale-matched pair alone (`bert-base` 110M vs `gpt2` 117M) the
   authored component reads as a property of the **autoregressive class**. An
   8B masked model reaches the same level, so it is a property of capability,
   and the class only sets how cheaply it is obtained. The capacity series is
   what distinguishes the two, and it was necessary.

## References

* T. Sagawa, *Stochastic Thermodynamics for Autoregressive Generative Models:
  A Non-Markovian Perspective*, arXiv:2604.07867 — the work re-examined here.
  Its corpora and released per-text values are at
  <https://github.com/taksagawa/Paper2026>.
* S. Sana et al., *Mixing Times of Glauber Dynamics on Masked Language
  Models*, arXiv:2605.16378 — the incompatibility of masked-model conditionals
  with any joint distribution.
* V. Papadopoulos, J. Wenger, C. Hongler, *Arrows of Time for Large Language
  Models*, arXiv:2401.17505.
* S. Nie et al., *Large Language Diffusion Models*, arXiv:2502.09992 — LLaDA.

## License

MIT for the code. The corpora are not redistributed here; they come from the
repository linked above under its own terms.
