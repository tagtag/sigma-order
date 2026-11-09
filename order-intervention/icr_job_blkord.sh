#!/bin/sh
#=====================================================================
# Kyoto University ICR Supercomputer -- CPU, SMALL queue, no GPU
#
# The decisive test: where does the WRITTEN sentence order rank among all
# sentence orders of the same text?
#
# Every result so far compares the causal text set against the non-causal set,
# and those differ in more than causal order (token counts differ significantly
# in 4 of 5 corpora, and the non-causal texts are still coherent discourse).
# This test is WITHIN each text -- the same sentences in all 4! = 24 orders --
# so length, vocabulary, style and topic are identical by construction.
#
#   causal ranks high, non-causal mid   sigma tracks causal order
#   both rank equally high              sigma tracks the text being in its
#                                       written order, not causal structure
#
# Run on the SCALE-MATCHED PAIR so the same statistic answers the
# directionality question too:
#
#     bert-base-uncased   110M  masked   direction neutral
#     gpt2                117M  causal   one direction
#
# Cost: 24 scores per text instead of 3.  bert-base ran ~6 min per corpus in
# pll_sigma.py, so ~48 min per corpus here; gpt2 is seconds.  Two corpora on
# both models is about 1.7 h, inside SMALL's limits.
#
#   qsub icr_job_blkord.sh
#   qsub -v CORPORA="Opus46 GPT54 GPT56 Gemini31 Fable5" icr_job_blkord.sh
#
# Qlist is a NODE resource and must sit inside the select chunk; without it
# the job waits for ever with
#   comment = Not Running: Insufficient amount of resource: Qlist
#=====================================================================
#PBS -q SMALL
#PBS -l select=1:ncpus=8:mem=12gb:Qlist=SMALL
#PBS -l walltime=06:00:00
#PBS -N blkord
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
: "${OUTDIR:=$WORK/results_blkord}"
: "${MODELS:=gpt2:causal bert-base-uncased:masked}"
: "${CORPORA:=Opus46 GPT54}"
: "${SHARD:=0/1}"
: "${THREADS:=8}"

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

echo
echo "=== preflight: evaluators in the cache? ==="
python3 - $MODELS <<'PY' || exit 1
import os, sys
from huggingface_hub import snapshot_download
missing = []
for spec in sys.argv[1:]:
    rid = spec.split(":")[0]
    try:
        snapshot_download(repo_id=rid, local_files_only=True)
        print(f"  ok      {rid}")
    except Exception:
        missing.append(rid); print(f"  MISSING {rid}")
if missing:
    print("\nERROR: " + ", ".join(missing) + " not in "
          + os.environ.get("HF_HOME", "?"))
    print("Run on the LOGIN node:  sh icr_prefetch_pll_models.sh")
    sys.exit(1)
PY

echo
echo "=== verify the statistic (no weights needed) ==="
python3 -I block_order_selftest.py | tail -4

echo
echo "=== run ==="
# gpt2 first: it finishes in seconds, so a mistake in the pipeline shows up
# immediately instead of after an hour of BERT.
for spec in $MODELS; do
    name=$(echo "$spec" | cut -d: -f1)
    kind=$(echo "$spec" | cut -d: -f2)
    tag=$(echo "$name" | tr '/' '_')
    for c in $CORPORA; do
        t="$TEXTS_DIR/fixed_text_${c}.json"
        if [ ! -f "$t" ]; then
            echo "  WARN: no corpus file $t -- skipped"; continue
        fi
        out="$OUTDIR/blkord_${tag}__${c}__$(echo "$SHARD" | tr '/' '-').json"
        if [ -f "$out" ]; then
            echo "  exists, skipping: $out"; continue
        fi
        echo
        echo "--- $name ($kind) x $c ---"
        python3 block_order_pll.py \
            --model "$name" --kind "$kind" --texts "$t" \
            --device cpu --dtype float32 --max-batch 64 \
            --threads "$THREADS" --shard "$SHARD" --max-perms 24 \
            --out "$out"
    done
done

echo
echo "done: $(date)"
echo "Compare the two evaluators with:"
echo "  python3 merge_blkord.py --dir $OUTDIR"
