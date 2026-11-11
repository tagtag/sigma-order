#!/bin/sh
#=====================================================================
# Kyoto University ICR Supercomputer -- the forward/backward rank test
#
# For each text, score every block arrangement p with
#
#     f(p) = [ log P_l2r(x_p) - log P_r2l(x_p) ] / L
#
# and record where the WRITTEN arrangement sits among the n! values.  Both
# terms score the same text; only the direction of assembly differs, so f
# vanishes identically for any model whose conditionals come from a joint.
# A rank therefore exists only because the model is incompatible, and the
# comparison is within one text, so length, vocabulary, topic and style are
# identical across the arrangements by construction.
#
#   causal ranks differently from non-causal   the incompatibility exposed by
#                                              a text depends on its order
#   both rank at 0.50                          it does not
#
# MASKED EVALUATORS ONLY.  log P_r2l needs P(x_1 | x_2..x_L), which conditions
# on the future; causal attention cannot supply it.  For autoregressive
# evaluators run icr_job_blkord.sh instead, whose score is the exact
# log-likelihood.
#
# Cost: 2 x n! chain-rule passes per text, i.e. 48 for the four-sentence
# texts here -- twice what icr_job_blkord.sh does, since each arrangement is
# assembled in both directions.
#
# ONE CORPUS PER JOB.  At 48 scores per text bert-base takes roughly 1.6 h
# for a 200-text corpus, so five corpora in one job would be about 8 h and
# SMALL allows 12 h at most (6 h by default).  Five separate jobs each sit
# well inside the limit and run at the same time:
#
#   for c in Opus46 GPT54 GPT56 Gemini31 Fable5; do
#       qsub -v CORPORA=$c icr_job_sigfb.sh
#   done
#
# Shorter still with --shard, which splits one corpus across jobs:
#
#   qsub -v CORPORA=Opus46,SHARD=0/4 icr_job_sigfb.sh
#
# ICR IS CPU ONLY HERE.  LLaDA runs on RunPod, not on this machine; the same
# runner works there with --device cuda --dtype bfloat16, outside PBS.
#
# Qlist is a NODE resource and must sit inside the select chunk; without it
# the job waits for ever with
#   comment = Not Running: Insufficient amount of resource: Qlist
#=====================================================================
#PBS -q SMALL
#PBS -l select=1:ncpus=8:mem=12gb:Qlist=SMALL
#PBS -l walltime=12:00:00
#PBS -N sigfb
#PBS -j oe

set -e

: "${PYENV:=module}"
: "${MODULE:=pytorch/2.4.1}"
: "${CONDA_ENV:=base}"
: "${VENV:=$HOME/venv-aoar}"

source /etc/profile.d/modules.sh
case "$PYENV" in
  conda)
    if command -v conda >/dev/null 2>&1; then
        eval "$(conda shell.bash hook)"
    elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
        . "$HOME/miniconda3/etc/profile.d/conda.sh"
    else
        echo "ERROR: conda not found; set PYENV=module"; exit 1
    fi
    conda activate "$CONDA_ENV"
    ;;
  module)
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

: "${WORK:=$PBS_O_WORKDIR}"
: "${TEXTS_DIR:=$WORK/Paper2026/gpt2/text_sets2}"
: "${OUTDIR:=$WORK/results_sigfb}"
: "${MODELS:=bert-base-uncased}"
: "${CORPORA:=Opus46 GPT54}"
: "${SHARD:=0/1}"
: "${THREADS:=8}"
: "${DEVICE:=cpu}"
: "${DTYPE:=float32}"   # CPU here; on RunPod use DEVICE=cuda DTYPE=bfloat16
: "${MAXBATCH:=64}"
: "${LIMIT:=}"

export HF_HOME="${HF_HOME:-$HOME/.cache/huggingface}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="$THREADS" MKL_NUM_THREADS="$THREADS"

mkdir -p "$OUTDIR"

# ---- fail fast, and say why -----------------------------------------
# The job runs in PBS_O_WORKDIR, the directory qsub was called from.  If
# that is not the directory holding the runner, every later step fails one
# at a time -- a ModuleNotFoundError here, a missing file there -- and the
# job still exits 0 having done nothing, which reads like success.
for f in block_sigma_fb.py block_sigma_fb_selftest.py block_vs_fb_selftest.py \
         block_order_pll.py aoar_core.py order_intervention.py; do
    if [ ! -f "$PWD/$f" ]; then
        echo "ERROR: $f is not in $PWD"
        echo
        echo "This job runs where qsub was called from.  Submit it from the"
        echo "directory that holds the runner and its imports:"
        echo "    cd <the order-intervention directory>"
        echo "    qsub icr_job_sigfb.sh"
        exit 1
    fi
done

if [ ! -d "$TEXTS_DIR" ]; then
    echo "ERROR: no corpus directory $TEXTS_DIR"
    echo "Set it explicitly:  qsub -v TEXTS_DIR=/path/to/text_sets2 ..."
    exit 1
fi

echo "=== environment ==="
python3 - <<'PY'
import torch, transformers, scipy, numpy
print(f"  torch {torch.__version__}  threads={torch.get_num_threads()}")
print(f"  transformers {transformers.__version__}  scipy {scipy.__version__}")
print(f"  numpy {numpy.__version__}")
print(f"  cuda available: {torch.cuda.is_available()}")
PY

echo
echo "=== preflight: evaluators in the cache? ==="
python3 - $MODELS <<'PY' || exit 1
import os, sys
from huggingface_hub import snapshot_download
missing = []
for rid in sys.argv[1:]:
    try:
        snapshot_download(repo_id=rid, local_files_only=True)
        print(f"  ok      {rid}")
    except Exception:
        missing.append(rid); print(f"  MISSING {rid}")
if missing:
    print("\nERROR: " + ", ".join(missing) + " not in "
          + os.environ.get("HF_HOME", "?"))
    print("Run on the LOGIN node:")
    print('  MODELS="' + " ".join(missing) + '" sh icr_prefetch_pll_models.sh')
    sys.exit(1)
PY

echo
echo "=== verify the statistic (no weights needed) ==="
python3 -I block_sigma_fb_selftest.py | tail -3
echo
echo "=== verify this is not the block-reversal sigma ==="
python3 -I block_vs_fb_selftest.py | tail -3

echo
echo "=== run ==="
ran=0
for name in $MODELS; do
    tag=$(echo "$name" | tr '/' '_')
    for c in $CORPORA; do
        t="$TEXTS_DIR/fixed_text_${c}.json"
        if [ ! -f "$t" ]; then
            echo "  WARN: no corpus file $t -- skipped"; continue
        fi
        out="$OUTDIR/sigfb_${tag}__${c}__$(echo "$SHARD" | tr '/' '-').json"
        if [ -f "$out" ]; then
            echo "  exists, skipping: $out"; continue
        fi
        echo
        echo "--- $name x $c ---"
        python3 -I block_sigma_fb.py \
            --model "$name" --texts "$t" \
            --device "$DEVICE" --dtype "$DTYPE" --max-batch "$MAXBATCH" \
            --shard "$SHARD" --max-perms 24 \
            ${LIMIT:+--limit "$LIMIT"} \
            --out "$out"
        ran=$((ran + 1))
    done
done

if [ "$ran" -eq 0 ]; then
    echo
    echo "ERROR: nothing ran.  No (model, corpus) pair produced a run."
    echo "MODELS=$MODELS"
    echo "CORPORA=$CORPORA"
    echo "TEXTS_DIR=$TEXTS_DIR"
    ls "$TEXTS_DIR" 2>/dev/null | head
    exit 1
fi

echo
echo "done: $(date)   $ran run(s)"
echo "Before trusting a full run, check that a short one works:"
echo "  qsub -v LIMIT=2,CORPORA=Opus46 icr_job_sigfb.sh"
echo "Then one job per corpus, so each stays well inside the 12 h limit."
