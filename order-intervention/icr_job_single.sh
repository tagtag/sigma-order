#!/bin/sh
#=====================================================================
# Kyoto University ICR Supercomputer (化研スパコン)
#   scheduler : Altair PBS Professional 2022.1   (qsub / qdel / qstat)
#   GPU queue : APG   -- max 2 GPUs per job, 4 GPUs per user
#   GPU node  : DL380G11, NVIDIA H100 PCIe 80GB x2, Xeon Platinum 8462Y+
#               64 cores / 1024 GB host memory, 9 nodes
#   walltime  : APG has no hard cap (default 120 days)
#
#   An 8B masked diffusion model in bf16 is ~16 GB, so one H100 is ample;
#   ngpus=1 is requested here and 2 GPUs per job is the ceiling if needed.
#
# Submit one task per (corpus x order):
#     qsub -v CORPUS=Opus46,ORDER=l2r icr_job_single.sh
#
# Or loop over the grid from the login node (see icr_submit_all.sh).
#=====================================================================
#PBS -q APG
#PBS -l select=1:ncpus=8:mem=64gb:ngpus=1:Qlist=APG
#PBS -N aoar
#PBS -j oe

set -e

# ---- Python environment --------------------------------------------
# Pick ONE of these with PYENV; mixing a module and a conda env breaks the
# torch/CUDA pairing.  Default is conda, since that is what the login shell
# was using.
#   PYENV=conda  CONDA_ENV=r44           activate a conda environment
#   PYENV=module MODULE=pytorch/2.4.1    use the site module
#   PYENV=venv   VENV=$HOME/venv-aoar    use a virtualenv
: "${PYENV:=conda}"
: "${CONDA_ENV:=r44}"
: "${MODULE:=pytorch/2.4.1}"
: "${VENV:=$HOME/venv-aoar}"

source /etc/profile.d/modules.sh
case "$PYENV" in
  conda)
    # `conda activate` needs the shell hook; `source activate` alone is not
    # reliable in a non-interactive PBS shell.
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
  module) module load "$MODULE" ;;
  venv)   module load Python/3.13.7; . "$VENV/bin/activate" ;;
  *) echo "ERROR: unknown PYENV=$PYENV"; exit 1 ;;
esac

cd "$PBS_O_WORKDIR"

# ---- paths (edit these once) ---------------------------------------
# Disk policy, per the ICR documentation:
#   home 100 GB / 2,000,000 files by default -- exceeding it blocks ALL writes
#   /aptmp/$USER shared, unbilled, but may be purged without notice
#   ${TMPDIR} per-job, deleted at job end; on APG it is on Lustre, not a fast
#             node-local SSD, so there is nothing to gain by staging through it
# Weights (~16 GB, re-downloadable) live on /aptmp; results (small, must
# persist) go to home.  This job writes one JSON of a few hundred kB.
: "${APTMP:=/aptmp/$USER}"
# MODEL_ID is a Hugging Face repo id read straight from the hub cache under
# HF_HOME (populated by icr_prefetch_model.sh).  Passing a repo id rather than a
# --local-dir path is what keeps a SINGLE copy of the ~16 GB of weights.
: "${MODEL_ID:=GSAI-ML/LLaDA-8B-Base}"
: "${REPO:=$HOME/Paper2026}"

# These models do not expose tokenizer.mask_token_id, so it must be supplied.
# Verified for LLaDA-8B-Base: vocab 126346, mask id 126336.
if [ -z "${MASK_ID:-}" ]; then
  case "$MODEL_ID" in
    *LLaDA*) MASK_ID=126336 ;;
    *Dream*) MASK_ID=151666 ;;
  esac
fi
: "${OUTDIR:=$PBS_O_WORKDIR/results}"
: "${CORPUS:?set CORPUS, e.g. -v CORPUS=Opus46}"
: "${ORDER:?set ORDER, e.g. -v ORDER=l2r}"

# Compute nodes have no outbound network: run fully offline.
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME="$APTMP/hf"
export TOKENIZERS_PARALLELISM=false
# Keep every transient cache off the home quota.
export TORCH_HOME="$APTMP/torch"
export XDG_CACHE_HOME="${TMPDIR:-$APTMP}/xdg"
export TRITON_CACHE_DIR="${TMPDIR:-$APTMP}/triton"
export PYTHONPYCACHEPREFIX="${TMPDIR:-$APTMP}/pycache"
mkdir -p "$TORCH_HOME" "$XDG_CACHE_HOME" "$TRITON_CACHE_DIR" "$PYTHONPYCACHEPREFIX"

TEXTS="$REPO/gpt2/text_sets2/fixed_text_${CORPUS}.json"
[ -f "$TEXTS" ] || TEXTS="$REPO/gpt2/text_sets/texts_gpt_exp_${CORPUS}.json"

mkdir -p "$OUTDIR"
TAG="${CORPUS}__$(echo "$ORDER" | tr ':' '-')"

echo "=== $(date) host=$(hostname) ==="
nvidia-smi || true
echo "MODEL_ID=$MODEL_ID"
echo "HF_HOME=$HF_HOME"
echo "TEXTS=$TEXTS"
echo "ORDER=$ORDER"

# ---- disk preflight -------------------------------------------------
# Fail early and loudly rather than part-way through a long grid.
echo "--- disk ---"
echo "home quota (kbytes):"; quota -v 2>/dev/null || echo "  (quota unavailable)"
echo "TMPDIR=${TMPDIR:-unset}"
df -h "$APTMP" 2>/dev/null | tail -1
CACHED="$HF_HOME/hub/models--$(echo "$MODEL_ID" | sed 's|/|--|')"
[ -d "$CACHED" ] || { echo "ERROR: $MODEL_ID is not in the cache at $CACHED"; \
    echo "run 'sh icr_prefetch_model.sh' on the LOGIN node first"; exit 1; }
[ -f "$TEXTS" ] || { echo "ERROR: corpus not found: $TEXTS"; exit 1; }
echo "cached weights: $(du -sh "$CACHED" 2>/dev/null | cut -f1)"

# ---- environment preflight -----------------------------------------
echo "--- python env ---"
echo "PYENV=$PYENV  python=$(command -v python3)"
python3 - <<'PY' || { echo "ERROR: python environment is not usable"; exit 1; }
import torch, transformers
print(f"  torch        {torch.__version__}  cuda={torch.cuda.is_available()}"
      f"  devices={torch.cuda.device_count()}")
print(f"  transformers {transformers.__version__}")
if torch.cuda.is_available():
    p = torch.cuda.get_device_properties(0)
    print(f"  gpu0         {p.name}  {p.total_memory/1024**3:.0f} GiB")
else:
    raise SystemExit("no CUDA device visible -- check the APG request and PYENV")
PY

python3 order_intervention.py \
    --model  "$MODEL_ID" \
    --texts  "$TEXTS" \
    --order  "$ORDER" \
    --out    "$OUTDIR/${TAG}.json" \
    --dtype  bfloat16 \
    --max-batch 64 \
    ${MASK_ID:+--mask-token-id "$MASK_ID"} \
    ${FOLLOW:+--order-follows-text}

echo "=== done $(date) ==="
