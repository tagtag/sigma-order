#!/bin/sh
#=====================================================================
# SINGLE-JOB variant: the whole (corpus x order) grid in one PBS job.
#
# Prefer this over icr_submit_all.sh whenever the APG queue is busy.  Observed
# 2026-11-09:  comment = "Not Running: Insufficient amount of resource:
# ngpus (R: 1 A: 0 ...)" -- every GPU on the machine was in use, and APG
# has no walltime cap (default 120 days), so a holder can sit for a long
# time.  Under contention one allocation beats 30 queue waits.
#
# It also avoids reloading ~15 GB of weights from Lustre 30 times: the
# model is loaded once and reused for every (corpus, order).
#
#   qsub icr_job_grid.sh
#   qsub -v ORDERS=l2r,r2l icr_job_grid.sh          # narrower grid
#
# Resources: 1 GPU is enough (an 8B model in bf16 is ~15 GB on an 80 GB
# H100).  walltime is set explicitly so the scheduler can backfill the job
# into a gap instead of treating it as open ended.
#=====================================================================
#PBS -q APG
#PBS -l select=1:ncpus=8:mem=64gb:ngpus=1:Qlist=APG
#PBS -l walltime=12:00:00
#PBS -N aoar_grid
#PBS -j oe

set -e

# ---- Python environment (see icr_job_single.sh for the alternatives) --------
: "${PYENV:=conda}"
: "${CONDA_ENV:=r44}"
: "${MODULE:=pytorch/2.4.1}"
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
  module) module load "$MODULE" ;;
  venv)   module load Python/3.13.7; . "$VENV/bin/activate" ;;
  *) echo "ERROR: unknown PYENV=$PYENV"; exit 1 ;;
esac

cd "$PBS_O_WORKDIR"

# ---- paths ----------------------------------------------------------
: "${APTMP:=/aptmp/$USER}"
: "${MODEL_ID:=GSAI-ML/LLaDA-8B-Base}"
: "${REPO:=$HOME/Paper2026}"
: "${OUTDIR:=$PBS_O_WORKDIR/results}"
: "${CORPORA:=Opus46 Fable5 Gemini31 GPT54 GPT56}"
: "${ORDERS:=l2r,r2l,random:1,random:2,confidence}"

# `qsub -v` treats commas as VARIABLE separators, so
#     -v ORDERS=l2r,r2l,random:1
# is parsed as three variables and fails with
#     qsub: cannot send environment with the job
# Either quote the value --  -v "ORDERS='l2r,r2l'"  -- or use '+' as the
# separator, which needs no quoting at all:
#     -v ORDERS=l2r+r2l+random:1+random:2
ORDERS=$(echo "$ORDERS" | tr '+' ',')
# Same trap for CORPORA, which is space separated; '+' works there too.
CORPORA=$(echo "$CORPORA" | tr '+' ' ')

if [ -z "${MASK_ID:-}" ]; then
  case "$MODEL_ID" in
    *LLaDA*) MASK_ID=126336 ;;
    *Dream*) MASK_ID=151666 ;;
  esac
fi

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME="$APTMP/hf"
export TOKENIZERS_PARALLELISM=false
export TORCH_HOME="$APTMP/torch"
export XDG_CACHE_HOME="${TMPDIR:-$APTMP}/xdg"
export TRITON_CACHE_DIR="${TMPDIR:-$APTMP}/triton"
export PYTHONPYCACHEPREFIX="${TMPDIR:-$APTMP}/pycache"
mkdir -p "$TORCH_HOME" "$XDG_CACHE_HOME" "$TRITON_CACHE_DIR" \
         "$PYTHONPYCACHEPREFIX" "$OUTDIR"

echo "=== $(date) host=$(hostname) job=$PBS_JOBID ==="
nvidia-smi || true
echo "MODEL_ID=$MODEL_ID  MASK_ID=${MASK_ID:-auto}"
echo "HF_HOME=$HF_HOME   TMPDIR=${TMPDIR:-unset}"
echo "ORDERS=$ORDERS"
echo "CORPORA=$CORPORA"

# ---- preflight ------------------------------------------------------
CACHED="$HF_HOME/hub/models--$(echo "$MODEL_ID" | sed 's|/|--|')"
[ -d "$CACHED" ] || { echo "ERROR: $MODEL_ID not cached at $CACHED"; \
    echo "run 'sh icr_prefetch_model.sh' on the LOGIN node first"; exit 1; }

TEXT_ARGS=""
for c in $CORPORA; do
    t="$REPO/gpt2/text_sets2/fixed_text_${c}.json"
    [ -f "$t" ] || t="$REPO/gpt2/text_sets/texts_gpt_exp_${c}.json"
    [ -f "$t" ] || { echo "ERROR: corpus not found for $c"; exit 1; }
    TEXT_ARGS="$TEXT_ARGS $t"
done
echo "corpora resolved:$TEXT_ARGS"

python3 - <<'PY' || { echo "ERROR: python environment is not usable"; exit 1; }
import torch, transformers
print(f"  torch        {torch.__version__}  cuda={torch.cuda.is_available()}")
print(f"  transformers {transformers.__version__}")
if not torch.cuda.is_available():
    raise SystemExit("no CUDA device visible -- wrong PYENV, or the torch "
                     "wheel's CUDA version is newer than the driver "
                     "(cu13x needs a 580+ driver; fall back to cu128/cu124)")
p = torch.cuda.get_device_properties(0)
print(f"  gpu0         {p.name}  {p.total_memory/1024**3:.0f} GiB")
PY

# ---- the grid, one model load -----------------------------------------
python3 order_intervention.py \
    --model   "$MODEL_ID" \
    --texts  $TEXT_ARGS \
    --order   "$ORDERS" \
    --outdir  "$OUTDIR" \
    --dtype   bfloat16 \
    --max-batch 64 \
    ${MASK_ID:+--mask-token-id "$MASK_ID"}

# ---- diagnostic arm: order mirrored with the text ----------------------
python3 order_intervention.py \
    --model   "$MODEL_ID" \
    --texts  $TEXT_ARGS \
    --order   l2r \
    --outdir  "$OUTDIR" \
    --dtype   bfloat16 \
    --max-batch 64 \
    --order-follows-text \
    ${MASK_ID:+--mask-token-id "$MASK_ID"}

echo
echo "=== aggregating ==="
python3 aggregate_orders.py --glob "$OUTDIR/*.json" \
    --out "$OUTDIR/order_intervention_summary.json"

echo "=== done $(date) ==="
