#!/bin/sh
#=====================================================================
# Kyoto University ICR Supercomputer (化研スパコン) -- CPU, SMALL queue
#   scheduler : Altair PBS Professional 2022.1   (qsub / qdel / qstat)
#   SMALL     : max 12 cores, 48 GB, 12 h walltime (defaults 1 core / 4 GB / 6 h)
#               96 cores per user in total, no job-count cap
#   chosen over APC because APC's wait is long; this job needs no GPU and
#   fits SMALL's limits with room to spare.
#
# What this runs
# --------------
# The direction-neutral evaluator test.  Sagawa's sigma is measured with an
# autoregressive model, which is trained in one direction only, so sigma > 0
# cannot be separated into "the text has an arrow" and "the evaluator only
# runs forward".  A masked (bidirectional) model removes the second.  The
# comparison that carries the argument is SCALE MATCHED:
#
#     bert-base-uncased   110M  masked    <-- direction neutral
#     gpt2                117M  causal    <-- same scale, one direction
#
# plus bert-large-uncased (340M) to show the masked result is not an artefact
# of the smallest model.  LLaDA-8B by PLL is the large-scale control and goes
# in a separate, sharded submission (see icr_submit_pll.sh).
#
# Cost: BERT-base is about 5 min per corpus on 12 cores, BERT-large about
# 20 min, GPT-2 seconds.  Five corpora, three models: under two hours, well
# inside SMALL's 12 h.
#
# Submit:
#     qsub icr_job_pll.sh                       # all three models, 5 corpora
#     qsub -v MODELS="bert-base-uncased:masked" icr_job_pll.sh
#     qsub -v CORPORA="Opus46 GPT54" icr_job_pll.sh
#
# MODELS is a space-separated list of name:kind pairs.  Because qsub -v
# treats commas as variable separators, never put a comma in these values.
#=====================================================================
#PBS -q SMALL
#PBS -l select=1:ncpus=8:mem=12gb:Qlist=SMALL
#PBS -l walltime=03:00:00
#PBS -N pllsigma
#PBS -j oe

set -e

# ---- Python environment --------------------------------------------
# Default is the site module: no conda environment on this account carries
# torch (checked 2026-11-09: drs39, macs3, r_env, r_tdcharm all lack it), so
# the module is the only place it lives.
: "${PYENV:=module}"
: "${MODULE:=pytorch/2.4.1}"
: "${CONDA_ENV:=base}"
: "${VENV:=$HOME/venv-aoar}"

source /etc/profile.d/modules.sh
case "$PYENV" in
  conda)
    if command -v conda >/dev/null 2>&1; then
        eval "$(conda shell.bash hook)"
    elif [ -f "$HOME/miniforge3/etc/profile.d/conda.sh" ]; then
        . "$HOME/miniforge3/etc/profile.d/conda.sh"
    elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
        . "$HOME/miniconda3/etc/profile.d/conda.sh"
    else
        echo "ERROR: conda not found; set PYENV=module or PYENV=venv"; exit 1
    fi
    conda activate "$CONDA_ENV"
    ;;
  module)
    # The login profile activates conda base, and a PBS job inherits that, so
    # base's python3 would shadow the module's.  Step out of conda first.
    if [ -n "${CONDA_PREFIX:-}" ] && command -v conda >/dev/null 2>&1; then
        eval "$(conda shell.bash hook)"
        while [ -n "${CONDA_PREFIX:-}" ]; do conda deactivate || break; done
    fi
    module load "$MODULE"
    ;;
  venv)   module load Python/3.13.7; . "$VENV/bin/activate" ;;
  *) echo "ERROR: unknown PYENV=$PYENV"; exit 1 ;;
esac

cd "$PBS_O_WORKDIR"

# ---- paths ----------------------------------------------------------
: "${WORK:=$PBS_O_WORKDIR}"
: "${TEXTS_DIR:=$WORK/Paper2026/gpt2/text_sets2}"
: "${OUTDIR:=$WORK/results_pll}"
: "${MODELS:=bert-base-uncased:masked bert-large-uncased:masked gpt2:causal}"
: "${CORPORA:=Opus46 GPT54 GPT56 Gemini31 Fable5}"
: "${SHARD:=0/1}"
: "${THREADS:=8}"

# Weights were fetched on the login node by icr_prefetch_pll_models.sh.  The
# compute nodes have no internet, so the cache must already be populated and
# the hub must be told not to phone home.
export HF_HOME="${HF_HOME:-$HOME/.cache/huggingface}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="$THREADS" MKL_NUM_THREADS="$THREADS"

mkdir -p "$OUTDIR"

echo "=== environment ==="
python3 - <<'PY'
import torch, transformers, scipy, numpy
print(f"  torch {torch.__version__}  threads={torch.get_num_threads()}")
print(f"  transformers {transformers.__version__}  scipy {scipy.__version__}")
print(f"  numpy {numpy.__version__}")
PY
echo "  HF_HOME=$HF_HOME"
nproc

echo
echo "=== preflight: are the evaluators actually in the cache? ==="
# A compute node has no internet, so an empty cache plus HF_HUB_OFFLINE=1 fails
# deep inside transformers with a message about the hub being unreachable.
# Checking here names the real cause -- the login-node prefetch never ran.
python3 - $MODELS <<'PY' || exit 1
import os, sys
from huggingface_hub import snapshot_download
missing = []
for spec in sys.argv[1:]:
    rid = spec.split(":")[0]
    try:
        p = snapshot_download(repo_id=rid, local_files_only=True)
        print(f"  ok      {rid:<26} {p}")
    except Exception:
        missing.append(rid)
        print(f"  MISSING {rid}")
if missing:
    print()
    print("ERROR: " + ", ".join(missing) + " not in " + os.environ.get("HF_HOME", "?"))
    print("Run this on the LOGIN node first:")
    print("    sh icr_prefetch_pll_models.sh --check")
    print("    sh icr_prefetch_pll_models.sh")
    sys.exit(1)
PY

echo
echo "=== verify the implementation (no weights needed) ==="
python3 -I pll_selftest.py | tail -4

echo
echo "=== run ==="
for spec in $MODELS; do
    name=$(echo "$spec" | cut -d: -f1)
    kind=$(echo "$spec" | cut -d: -f2)
    tag=$(echo "$name" | tr '/' '_')
    for c in $CORPORA; do
        t="$TEXTS_DIR/fixed_text_${c}.json"
        if [ ! -f "$t" ]; then
            echo "  WARN: no corpus file $t -- skipped"
            continue
        fi
        sh_tag=$(echo "$SHARD" | tr '/' '-')
        out="$OUTDIR/pll_${tag}__${c}__${sh_tag}.json"
        if [ -f "$out" ]; then
            echo "  exists, skipping: $out"
            continue
        fi
        echo
        echo "--- $name ($kind) x $c  shard $SHARD ---"
        python3 pll_sigma.py \
            --model "$name" --kind "$kind" \
            --texts "$t" --device cpu --dtype float32 \
            --max-batch 64 --threads "$THREADS" --shard "$SHARD" \
            --out "$out"
    done
done

echo
echo "=== merge and compare ==="
python3 merge_pll.py --dir "$OUTDIR" --out "$OUTDIR/pll_comparison.json"

echo
echo "done: $(date)"
