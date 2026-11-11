# Authored order dominates fixed-text entropy production

Code and measurements for the paper *Authored order dominates fixed-text
entropy production: a measure without a zero, and a contrast without a
criterion*.

The paper re-examines a quantity that has been read as an entropy production
for a fixed text,

```
Delta = [ log P(x) - log P(x~) ] / L
```

where `x~` is `x` with its order reversed. The published measurements are
reproduced here, independently, to 8.5e-14 on the released per-text values of
all 14 corpora, and every Mann-Whitney statistic and rank-biserial effect size
the source repository ships is recovered (`bert-affinity/compare_repro.log`).

What this work adds is **two instruments and one identity**. The identity is
the point, so it comes first.

## Three symbols, three quantities

They were confused for one another repeatedly while this was written, in both
directions, so the separation is stated once and then kept:

| symbol | what it compares | is it an entropy production? |
|---|---|---|
| `Delta` | a text with a **different** text | no |
| `sigma` | the **same** text, assembled in two directions | yes |
| `sigma_EP` | a Glauber chain with its reverse (toy system) | yes, of that chain |

`Delta` is the published quantity. `sigma` is the one the thermodynamic
reading names.

## The identity

For a masked model, fix an unmasking order `pi` and the any-order chain rule

```
log P_pi(x) = sum_t log p_theta( x_{pi(t)} | positions revealed before t )
```

is a genuine log-probability. Taking `pi` to be left-to-right and then
right-to-left **for the same text** gives the forward path against its reverse:

```
sigma(x) = [ log P_l2r(x) - log P_r2l(x) ] / L
```

If the model's conditionals come from a joint `P`, every term telescopes,
`log P_pi(x) = log P(x)` for every `pi`, and therefore

```
sigma(x) = 0   for every x, causal or not.
```

**The value range of `sigma` contains no property of the text.** Two things
follow at once.

An autoregressive evaluator cannot be placed here at all: it has a joint, so
its `sigma` is zero by construction, and the backward term asks for
`P(x_1 | x_2..x_L)`, which causal attention cannot supply. For the evaluators
of the work re-examined, the quantity its thermodynamic reading names is
simultaneously trivial and unevaluable. `Delta` is what can be computed in its
place.

A masked evaluator can be placed here, and is the only kind that can. Its
conditionals come from no joint, so a non-zero reading exists — and what it
measures is that incompatibility, not the text.

`order-intervention/block_vs_fb_selftest.py` exhibits a model for which
`sigma` vanishes to 1e-16 while `Delta` does not, over every sequence of a
system small enough to enumerate.

## Instrument 1: where the authored arrangement ranks under `Delta`

Score the same sentences in **all `n!` orders**. Writing `x_pi` for the blocks
concatenated in the order `pi`, block reversal of `x_pi` is exactly
`x_{pi o rev}`, so

```
Delta(pi) = [ S(x_pi) - S(x_{pi o rev}) ] / L  =  - Delta(pi o rev)
```

identically, for any score `S`. The map `pi -> pi o rev` is a
measure-preserving involution on the symmetric group, so the set of `Delta`
values over a uniformly drawn `pi` is **exactly symmetric about zero** — as an
identity, not as an empirical finding. The position of the authored order
within its own permutation set is therefore unitless, bounded, equal to 0.50
for any score blind to sentence order, and comparable across scorer types that
`Delta` itself cannot be compared across. Each text becomes its own control.

Two consequences of the same identity are worth stating, because both are easy
to get wrong:

* Comparing the authored order against a **shuffled** one compares it against
  the *centre* of a symmetric set, which is zero by construction. Such a
  comparison can only restate `Delta(id) > 0`. It carries no information, and
  an earlier version of this work drew a conclusion from it before noticing.
* The rank must **split ties**. A score that cannot distinguish the
  arrangements gives `Delta(pi) = 0` for every `pi`, and a count of
  `#{Delta <= Delta(id)}` then reports `n!/n! = 1.00` — "the most
  forward-costly arrangement there is" — for a model that cannot tell them
  apart. The midrank puts that case at exactly 0.50. Both behaviours are
  asserted in `order-intervention/block_order_selftest.py`.

## Instrument 2: the same rank under `sigma`

The construction is reused with `f(pi) = sigma(x_pi)` in place of
`Delta(pi)`, and two things change.

The null is still 0.50, but for a different reason. There it followed from the
antisymmetry; `f` has none, because reversing the block order changes which
text is scored and does not negate `sigma`. The null here is the ordinary
permutation-test null: under the hypothesis that the authored order is one
arrangement among `n!`, its rank is uniform.

And a rank exists at all only because the evaluator is incompatible. Where the
`n!` values coincide — a compatible model, or a text whose sentences are the
same string — the text is flagged degenerate, reported at the null and
excluded from the effect size. Values within 1e-12 count as tied, because in
floating point a mathematically exact tie differs in the sixteenth decimal and
ranking that is ranking noise.

## The results

### What `Delta` measures: autoregressive ladder, no PLL anywhere

Five evaluators, five corpora, 200 texts each, all `4! = 24` orders enumerated
exactly. Scores are exact autoregressive log-likelihoods.

| evaluator | params | authored | causal | share | share (z) | at ceiling |
|---|---|---|---|---|---|---|
| `gpt2`              |  124M | +0.354 | +0.042 | 11% | 15% | 32% |
| `gpt2-medium`       |  355M | +0.354 | +0.083 | 19% |  8% | 32% |
| `gpt2-large`        |  774M | +0.354 | +0.042 | 11% | 10% | 33% |
| `gpt2-xl`           | 1558M | +0.396 | +0.042 | 10% | 13% | 36% |
| `Qwen/Qwen3-4B-Base`|   4B  | +0.396 | +0.042 | 10% | 14% | 40% |

`authored` is the median distance of the **non-causal** texts' authored order
from the 0.50 null: what any authored order earns. It uses no causal
judgement. `causal` is what the causally labelled texts show beyond that.

**First result.** Between a tenth and a fifth of the measured distance is
attributable to the labelled contrast, and the rest to the arrangement simply
being the one a writer chose.

**Second result, and the limit on it.** The causal component is **one or two
steps of the 1/24 midrank grid in every evaluator** — the smallest non-zero
reading the statistic can express. Its value is not a measured size. Against
capacity, over a 32x span:

| component | rho | p |
|---|---|---|
| fraction at the ceiling | **+0.97** | **0.005** |
| authored | +0.87 | 0.058 |
| causal | -0.35 | 0.559 |
| ceiling-free `z` share | +0.00 | 1.000 |

Only the ceiling moves. **The instrument loses headroom, not signal** — and
the signal was at the resolution floor from the smallest evaluator onwards.
"The causal contribution shrinks with capacity" would be a different claim and
is not what these data say.

The correlations are taken after rounding to 1e-12. Left unrounded, four
values that are all exactly 1/24 differ in the sixteenth decimal, and the rank
correlation reports -0.79 instead of -0.35 by ordering that noise.

### What `sigma` measures: masked evaluators only

Five corpora, 200 texts each, both evaluators.

| evaluator | authored | in grid steps | causal | sign of `r` | sign test |
|---|---|---|---|---|---|
| `bert-base-uncased`     | +0.0208 | **+0.5** | -0.1042 | 5/5 negative | p = 0.0625 |
| `GSAI-ML/LLaDA-8B-Base` | -0.2708 | **-6.5** | -0.0208 | 4/5 negative | p = 0.375  |

**The same 1000 texts, read thirteen grid steps apart.** Under `LLaDA` the
authored arrangement sits far below the null and does so in every corpus and
both label groups — all ten displacement tests reject at `p < 6e-6`. Under
`bert-base` it sits at the null and no corpus rejects after correction.
Nothing about the texts changed between the two readings; only the evaluator
did.

**The causal label does essentially nothing.** Of the ten evaluator-corpus
tests of causal against non-causal, **one** survives a Bonferroni threshold of
0.005; two fall below 0.05 on their own, against 0.5 expected by chance. The
sign is not consistent within either evaluator. The one surviving cell is
`bert-base` on `Gemini31`, which is also the corpus where `LLaDA`'s
displacement from the null is largest — more plausibly a property of that
corpus than of the label.

This is the identity seen from the measurement side. It says the value range
of `sigma` carries no property of the text; what the measurement adds is that
the range it *does* carry — the evaluator's incompatibility — is large enough
to dominate everything else.

### Does the number belong to the model, or to how its rates were built?

`sigma_EP` needs `p(x_k | x_-k)`. A masked model emits it; an autoregressive
model has no head that does, so for that class it is recovered from the
joint. The capacity table therefore uses two different constructions on its
two kinds of row. That is forced -- one class has no second option -- but it
leaves the question open, so `bayes_route_control.py` gives one masked model
both routes at every width.

| d | params | sigma_EP emitted | sigma_EP recovered | J(emitted \|\| recovered) | mean\|sigma\| |
|---|---|---|---|---|---|
|  32 |  13317 | 0.0074 | 4.2e-19 | 0.19-0.20 | 0.2261 |
|  64 | 101189 | 0.0063 | 5.0e-19 | 0.12-0.26 | 0.2169 |
|  96 | 337349 | 0.0144 | 5.3e-19 | 0.20-0.36 | 0.2130 |
| 128 | 597253 | 0.0253 | 3.0e-19 | 0.22-0.55 | 0.2508 |
| 160 | 930885 | 0.0259 | 2.2e-19 | 0.21-0.46 | 0.2169 |

The `emitted` column reproduces `capacity_results.json` exactly -- same seed,
same draw, same training call -- so this is one model read two ways, not two
models.

Three joints were tried: `exp(PLL)` normalised over the 4096 states, and the
any-order chain rule left to right and right to left. **Every one returns
zero.** That zero is not evidence about the model: the identity makes any
joint-derived set of conditionals reversible. It is what makes the asymmetry
harmless -- the two routes coincide exactly when a joint exists, so the
difference in construction can only show up where the property under test
fails.

What the control does measure is `J`, the distance between the emitted
conditionals and the recovered ones. It depends on **which** joint was
recovered from. There is no canonical one, so "normalise it and the problem
goes away" names a different model rather than repairing this one.

The last column is `sigma` -- the quantity the paper measures on real text --
read on the same models, since the two chain-rule joints are its two terms.
Both quantities are non-zero at every width. **Their sizes do not track each
other**: `sigma_EP` rises with capacity (rho = +0.90, p = 0.037) and
mean`|sigma|` does not (rho = +0.10, p = 0.873); against each other,
rho = +0.30, p = 0.624. Two different functionals of one failure, and
neither magnitude is the amount of it.

### The mask rate BERT was trained at

`BERT` is trained at a single masking rate, 0.15, while the chain rule sweeps
the rate from 1 down to `1/L`. Most terms therefore ask it for a conditional
at a rate it never saw, and the natural worry is that the chain rule collapses
there.

It does not. Across all **2000 texts and both evaluators, 0 were degenerate**:
the chain rule returns a distinct, ordered value for every arrangement of
every text, at every mask rate it is asked for. This is measured rather than
assumed, and it is reported in the build log of every run.

### Two implementations, one number

`order_intervention.py` scores a text once in each direction; `block_sigma_fb.py`
scores it in each direction for all `n!` arrangements. They share no code
beyond the chain rule. On the authored arrangement they agree to the printed
precision in all five corpora:

```
          between-set   within-text
Fable5      +0.0552       +0.0552
GPT54       +0.0753       +0.0753
GPT56       +0.1088       +0.1088
Gemini31    +0.0161       +0.0161
Opus46      +0.0574       +0.0574
```

## Reproducing

Nothing here needs a GPU except `LLaDA`, which took 2.16 h for all five
corpora on one RTX 4090. Everything else runs on CPU; `bert-base` takes about
52 minutes per corpus for the `sigma` instrument.

```bash
git clone https://github.com/<your-login>/sigma-order.git
cd sigma-order
pip install "transformers<5" huggingface_hub scipy numpy torch pypdfium2

# the corpora
git clone --depth 1 https://github.com/taksagawa/Paper2026.git

# verify every instrument before spending any compute (no weights needed)
python3 -I order-intervention/block_order_selftest.py
python3 -I order-intervention/block_sigma_fb_selftest.py
python3 -I order-intervention/block_vs_fb_selftest.py
python3 -I order-intervention/aoar_selftest.py

# Delta: where the authored order ranks, one autoregressive evaluator
python3 order-intervention/block_order_pll.py \
    --model gpt2 --kind causal \
    --texts Paper2026/gpt2/text_sets2/fixed_text_Opus46.json \
    --max-perms 24 --out results_blkord/blkord_gpt2__Opus46__0-1.json

# sigma: the same rank under the forward/backward entropy production
python3 order-intervention/block_sigma_fb.py \
    --model bert-base-uncased \
    --texts Paper2026/gpt2/text_sets2/fixed_text_Opus46.json \
    --max-perms 24 --out results_sigfb/sigfb_bert-base-uncased__Opus46__0-1.json

# aggregate, then rebuild the paper from the JSONs
python3 -I order-intervention/merge_blkord.py --dir results_blkord
python3 -I order-intervention/merge_sigfb.py  --dir results_sigfb
python3 -I order-intervention/forward_backward_sigma.py
python3 -I order-intervention/forward_backward_decomposition.py
cd paper && sh build_paper.sh
```

For a GPU evaluator add `--device cuda --dtype bfloat16`, and for LLaDA also
`--mask-token-id 126336 --max-batch 32`. Batch scripts are provided:
`icr_job_blkord.sh` and `icr_job_sigfb.sh` for a PBS cluster,
`rented_run_all.sh` and `rented_run_sigfb.sh` for a rented GPU.

Every number in the paper, in the tables and in the running text alike, is
generated by `paper/make_tables.py` from these JSON files, and every figure by
`paper/make_figures.py`. No figure is typed into the LaTeX source, so
rerunning the measurements regenerates the prose.

## Layout

```
order-intervention/
  aoar_core.py              any-order chain rule, reversals, block arrangements
  aoar_selftest.py          order-independence and normalisation checks

  block_order_pll.py        instrument 1: the authored order's rank under Delta
  block_order_selftest.py   its correctness checks, no weights required
  merge_blkord.py           its aggregation and decomposition
  results_blkord/           measured JSON, one file per (evaluator, corpus)

  block_sigma_fb.py         instrument 2: the same rank under the true sigma
  block_sigma_fb_selftest.py  its correctness checks, no weights required
  merge_sigfb.py            its aggregation, sign test and decomposition
  results_sigfb/            measured JSON, one file per (evaluator, corpus)
  icr_job_sigfb.sh          PBS job for it
  rented_run_sigfb.sh       rented-GPU runbook for it

  block_vs_fb_selftest.py   proof that the two instruments measure different
                            quantities: sigma vanishes identically for a model
                            with a joint, Delta does not

  order_intervention.py     the between-set runner for masked models
  forward_backward_sigma.py     sigma between the two text sets, from stored runs
  forward_backward_decomposition.py  its authored / causal split
  order_dependence.py       how much a reading moves when only pi does
  results_llada_*/          4 unmasking orders x 5 corpora
  results_seeds_*/          12 unmasking orders x 2 corpora

  pll_sigma.py              the original between-set protocol, both scorer types
  pll_selftest.py           its correctness checks
  merge_pll.py              its aggregation
  results_pll/              measured JSON.  The autoregressive files hold
                            exact log-likelihoods, so they are Delta and the
                            paper reports them (the between-set table and the
                            token-reversal table).  The masked files hold
                            pseudo-log-likelihoods -- RETAINED, NOT REPORTED;
                            see "What this work got wrong on the way".

  block_split_selftest.py   what the sentence splitter does, and where it is wrong
  bundle_check.py           a shipped tarball must stand up in an empty directory
  README.md                 working notes, including what was retracted and why
bert-affinity/
  mlm_entropy_production.py exact Schnakenberg entropy production on a known joint
  cycle_affinity.py         Kolmogorov cycle affinities: the incompatibility,
                            enumerated, that instrument 2 reads off real text
  capacity_sweep.py         the capacity sweep in that system
  bayes_route_control.py    the control that separates the model from the
                            route: one masked model per width, with its
                            Glauber rates built from the conditionals it
                            emits and from conditionals recovered out of
                            three different joints.  Reproduces the
                            capacity sweep's sigma_EP bit for bit, so the
                            comparison is within one model.  Carries its own
                            assertions; ~15 min on CPU, not part of the
                            self-test set because it trains
  bayes_route_control.json  its measured values
  bayes_route_control.log   its output
  identity_check.py         a Jeffreys-divergence identity, verified numerically
  reproduce_sagawa_stats.py independent reproduction of the published statistics
  compare_repro.py          checks that reproduction against the shipped values
check_readme.py             this README against the repository it describes
paper/
  main.tex                  the paper
  sec_intro.tex             Section 1
  sec_decomp.tex            Sections 5.2-5.4
  sec_truesigma.tex         Section 6, the entropy production itself
  make_tables.py            every table and every quoted number
  make_tables_selftest.py   its checks, no measurements required
  check_paper.py            the relations a built PDF cannot show
  check_paper_selftest.py   proof that it catches each of them
  glossary.txt              terms this paper settled on, and the banned ones
  make_figures.py           every figure
  build_paper.sh            measurements -> tables -> figures -> PDF
  make_arxiv.sh             assemble the arXiv bundle and verify it builds alone
```

## Self-tests

Each instrument carries checks that run without model weights, and they are
the reason to trust the numbers rather than the code's appearance:

* `block_order_selftest.py` — the permutation set is closed under reversal and
  contains the identity; the `n!` values of `Delta` sum to zero; the midrank is
  free to take any value in its range under an arbitrary score (so the test is
  not degenerate); an order-blind score yields exactly 0.50 while an unadjusted `<=`
  count would yield 1.00.
* `block_sigma_fb_selftest.py` — a compatible model gives `f(pi) = 0` for every
  arrangement, which in floating point differ by 1e-16, and the runner must
  report the midrank as exactly 0.50 rather than ranking that noise; a text
  whose blocks are identical stays tied whatever the model; off the compatible
  manifold the midrank's mean over many texts sits at 0.50, so the null is
  calibrated; and `f(pi o rev)` is **not** `-f(pi)`, the antisymmetry the other
  instrument has and this one does not.
* `block_vs_fb_selftest.py` — over all 64 sequences of a toy system with an
  exactly consistent model, `max|sigma|` is 3e-16 and `max|Delta|` is 1.70.
  If the two were the same quantity the autoregressive half of the paper would
  be measuring exactly zero.
* `pll_selftest.py` — each content token is masked exactly once and no special
  token is ever masked or scored; both reversals are involutions; a
  direction-neutral score gives zero exactly.
* `block_split_selftest.py` — what the sentence splitter does, including
  where it is wrong. A block ends at any token whose decoded text ends in
  `.`, `!` or `?`, which divides an abbreviation or a decimal and misses a
  stop inside a closing quotation mark. None of the three fired on these
  corpora — every text split into exactly 4 blocks and none was dropped — but
  the rule had no test at all, and a mis-split is silent: it only changes the
  size of the permutation set.
* `aoar_selftest.py` — order-independence of the any-order chain rule to
  1.8e-15 and normalisation to 4.4e-16. It writes those two tolerances to
  `aoar_selftest.json`, which is where the paper's text gets them; they used
  to be typed in.
* `bundle_check.py` — a tarball that is about to be sent somewhere is
  extracted into an **empty** directory and every self-test and every module
  in it is run with `python3 -I`, so nothing can be satisfied by a file that
  happens to sit in the source tree. Twice a bundle reached a remote machine
  and failed on an import that could not fail at home; each cost a round trip.
* `check_readme.py` — this file is read by more people than the paper
  is, and it drifts: it named the retired instrument as the main one
  for a day after it stopped being that. The check verifies that every
  file the Layout block names exists, that the prose keeps to
  `paper/glossary.txt` (it caught a banned term on the first run), and
  that the numbers quoted here match the measured JSON.
* `bert-affinity/compare_repro.py` — the paper says every effect size and rank
  statistic in the work it re-examines is recovered. That comparison used to be
  left to the eye: `reproduce_sagawa_stats.py` printed our values and the
  repository's own `mann_whitney_results_*.csv` one after the other. This pairs
  them by corpus and reports the worst disagreement — U exactly, r to 3.3e-07,
  p within the convention difference the source documents. Run it after
  `reproduce_sagawa_stats.py`; every self-test here writes its `.log` beside it.
* `paper/check_paper.py` — the relations a reader cannot see. A reference
  list prints whether or not anything cites it; a figure appears whether or
  not a sentence points at it; a sentence can promise that a quantity is
  reported and no table report it. Each of those shipped here at least once,
  in a PDF that looked correct, and each was found by a person asking a
  question rather than by reading. This asks those questions mechanically,
  and `check_paper_selftest.py` rebuilds every one of the defects in a
  minimal document and requires the checker to fail on it. `build_paper.sh`
  reports a failure; `make_arxiv.sh` refuses to package on one. Given the
  built PDF it also checks where the floats actually landed: in one build
  every figure was deferred past the bibliography, with Figure 1 printing two
  pages after the reference list, and nothing noticed because the source was
  correct. It expands `\input` before checking, so a body split across files
  is checked as the reader gets it, and it reads the PDF through any of
  pdftotext, pypdfium2, PyMuPDF, pdfminer.six or pypdf.
* `paper/make_tables_selftest.py` — runs `make_tables.py` on synthetic
  measurements with a known answer and checks that the tables and the macros
  agree with it: that the token-reversal table is written at all, that the
  block-level table keeps its own columns, that every macro the prose quotes
  resolves to the value the input implies rather than to a TODO, and that
  degenerate texts are counted, excluded from the effect size, and not ranked.

## What this work got wrong on the way

Kept here because the record is part of the method, and because every one of
these is a mistake a reader might repeat:

1. A **shuffle control** was run and produced `r = 0.9857, p = 1e-17`, which
   looks decisive and is empty: the antisymmetry above forces it. See
   `order-intervention/shuffle_control.py`, retained and marked as retracted.
2. On the scale-matched pair alone (`bert-base` 110M vs `gpt2` 124M) the
   authored component read as a property of the **autoregressive class**, and
   a capacity series of masked evaluators was built to test that reading
   against a capability one. Both the reading and its test are void, for a
   reason that took longer to see than either: `Delta` is defined only where a
   joint exists, so the masked side of the comparison was never `Delta` at all
   but the pseudo-log-likelihood of the next item. A comparison between a
   quantity and a different quantity concludes about neither. It is withdrawn,
   and what replaced it is a ladder inside one class, where every rung reports
   the same quantity.
3. **The paper was built for weeks on the pseudo-log-likelihood.** `PLL` sums
   `log p(x_k | x_{-k})` over positions, each term conditioning on every other
   token. It is not the logarithm of anything — `sum_x exp(PLL(x))` is 2.27
   even for a model whose conditionals match the true joint exactly — but, more
   to the point here, **it has no generation order in it**. The whole reason to
   bring in a masked model is that the order of assembly becomes a free
   parameter; choosing PLL deletes that parameter, and with it the question the
   project existed to ask. The choice was made by reusing a scorer written for
   the reproduction of the published protocol, and it survived because the
   methods section said, truthfully of the construction's validity and falsely
   of the paper's subject, that *nothing in this depends on what `S` is*. A
   sentence that says a choice does not matter is how a choice stops being
   examined.
4. A rank correlation was computed over a component that is **one grid step
   wide**. Four evaluators returned exactly `1/24`, which floating point
   rendered as two values differing by 1.1e-16, and the correlation ordered
   that noise: `rho = -0.79` where the correct all-tied treatment gives
   `-0.35`. The components are now quantised before ranking. The episode is
   also the clearest illustration of the finding it nearly corrupted.
5. The float-placement check **existed and did not run** on the machine the
   paper was built on, because it required poppler. A check that turns itself
   into a warning when a tool is missing is a check you do not have.

## References

* T. Sagawa, *Stochastic Thermodynamics for Autoregressive Generative Models:
  A Non-Markovian Perspective*, arXiv:2604.07867 — the work re-examined here.
  Its corpora and released per-text values are at
  <https://github.com/taksagawa/Paper2026>.
* C. Jarzynski, *Nonequilibrium equality for free energy differences*,
  Phys. Rev. Lett. 78, 2690 (1997); arXiv:cond-mat/9610209.
* G. E. Crooks, *Entropy production fluctuation theorem and the nonequilibrium
  work relation for free energy differences*, Phys. Rev. E 60, 2721 (1999);
  arXiv:cond-mat/9901352 — the path-against-reverse-path form the identity
  above is read against.
* U. Seifert, *Stochastic thermodynamics, fluctuation theorems and molecular
  machines*, Rep. Prog. Phys. 75, 126001 (2012); arXiv:1205.4176.
* S. Sana et al., *Mixing Times of Glauber Dynamics on Masked Language
  Models*, arXiv:2605.16378 — the incompatibility of masked-model conditionals
  with any joint distribution.
* V. Papadopoulos, J. Wenger, C. Hongler, *Arrows of Time for Large Language
  Models*, ICML 2024, PMLR 235, 39509; arXiv:2401.17505.
* S. Nie et al., *Large Language Diffusion Models*, NeurIPS 2025;
  arXiv:2502.09992 — LLaDA.

## License

MIT for the code. The corpora are not redistributed here; they come from the
repository linked above under its own terms.
