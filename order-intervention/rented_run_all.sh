#!/bin/bash
#=====================================================================
# One-shot runbook for a rented GPU instance (RunPod / Vast.ai / Lambda).
#
# Why this exists: the whole measurement is about 1-2 GPU-hours.  Waiting
# for a slot on a saturated cluster can cost days; renting the same work
# costs a few dollars.
#
# REQUIREMENTS
#   VRAM   >= 24 GB   (bf16 weights 16.0 GB + ~3 GB transient at --max-batch 32)
#   disk   >= 50 GB   (15 GB of weights plus the image)
#   time   ~1-2 h     for 4 orders x 5 corpora + the diagnostic arm
#
# A 24 GB card (RTX 4090) is enough and is the cheapest option by a wide
# margin.  48 GB (L40S) or 80 GB (A100/H100) let you raise --max-batch and
# finish sooner, which may or may not be cheaper overall.
#
# USAGE on a fresh pod, from the directory holding the six project files:
#   bash rented_run_all.sh
#
# The six files that must be present:
#   aoar_core.py  order_intervention.py  aggregate_orders.py
#   aoar_selftest.py  make_mock_results.py  (the last two are optional)
#=====================================================================

set -euo pipefail

MODEL_ID="${MODEL_ID:-GSAI-ML/LLaDA-8B-Base}"
MASK_ID="${MASK_ID:-126336}"
ORDERS="${ORDERS:-l2r,r2l,random:1,random:2}"
CORPORA="${CORPORA:-Opus46 Fable5 Gemini31 GPT54 GPT56}"
MAX_BATCH="${MAX_BATCH:-32}"
WORK="${WORK:-$PWD}"
OUTDIR="$WORK/results"

echo "=== 0. what we are on ==="
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv || {
    echo "no GPU visible; stop here"; exit 1; }
df -h "$WORK" | tail -1
python3 -c "import sys; print('python', sys.version.split()[0])"

echo
echo "=== 1. dependencies ==="
# torch is usually preinstalled on GPU images; only add what is missing.
python3 - <<'PY' || pip install --quiet -U torch
import torch; print("torch present:", torch.__version__, torch.version.cuda)
PY
pip install --quiet -U transformers huggingface_hub scipy numpy
python3 - <<'PY'
import torch, transformers
print(f"  torch {torch.__version__} cuda={torch.cuda.is_available()}")
print(f"  transformers {transformers.__version__}")
assert torch.cuda.is_available(), "no CUDA device"
p = torch.cuda.get_device_properties(0)
print(f"  gpu0 {p.name} {p.total_memory/1024**3:.0f} GiB")
assert p.total_memory/1024**3 > 22, "need at least 24 GB of VRAM"
PY

echo
echo "=== 2. verify the implementation before spending GPU time ==="
# Costs seconds, needs no weights, and catches a broken copy of the code.
python3 -I aoar_selftest.py | tail -3

echo
echo "=== 3. corpora ==="
[ -d "$WORK/Paper2026" ] || git clone --depth 1 \
    https://github.com/taksagawa/Paper2026.git "$WORK/Paper2026"
ls "$WORK/Paper2026/gpt2/text_sets2/" | head -5

echo
echo "=== 4. weights (15 GB; one copy in the hub cache, no --local-dir) ==="
export HF_HOME="$WORK/hf"
mkdir -p "$HF_HOME"
python3 - "$MODEL_ID" <<'PY'
import sys, time
from huggingface_hub import snapshot_download
t0 = time.time()
p = snapshot_download(repo_id=sys.argv[1], max_workers=8)
print(f"  {p}\n  downloaded in {time.time()-t0:.0f}s")
PY

echo
echo "=== 5. the grid ==="
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
mkdir -p "$OUTDIR"

TEXT_ARGS=()
for c in $CORPORA; do
    t="$WORK/Paper2026/gpt2/text_sets2/fixed_text_${c}.json"
    [ -f "$t" ] || t="$WORK/Paper2026/gpt2/text_sets/texts_gpt_exp_${c}.json"
    [ -f "$t" ] && TEXT_ARGS+=("$t") || echo "  WARN: no corpus for $c"
done
echo "  ${#TEXT_ARGS[@]} corpora, orders: $ORDERS, max-batch $MAX_BATCH"

# A 3-text smoke run first: if anything is wrong it shows in under a minute,
# before the model is asked to do an hour of work.
python3 order_intervention.py --model "$MODEL_ID" --mask-token-id "$MASK_ID" \
    --texts "${TEXT_ARGS[0]}" --order l2r --out /tmp/smoke.json \
    --max-batch "$MAX_BATCH" --limit 3
echo "  smoke run OK"

python3 order_intervention.py --model "$MODEL_ID" --mask-token-id "$MASK_ID" \
    --texts "${TEXT_ARGS[@]}" --order "$ORDERS" --outdir "$OUTDIR" \
    --max-batch "$MAX_BATCH"

python3 order_intervention.py --model "$MODEL_ID" --mask-token-id "$MASK_ID" \
    --texts "${TEXT_ARGS[@]}" --order l2r --outdir "$OUTDIR" \
    --max-batch "$MAX_BATCH" --order-follows-text

echo
echo "=== 6. aggregate ==="
python3 aggregate_orders.py --glob "$OUTDIR/*.json" \
    --out "$OUTDIR/order_intervention_summary.json" | tee "$OUTDIR/aggregate.log"

echo
echo "=== 7. pack the results (download this, then destroy the pod) ==="
tar czf "$WORK/order_intervention_results.tgz" -C "$WORK" results
ls -la "$WORK/order_intervention_results.tgz"
echo
echo "The tarball is the deliverable: a few hundred kB. Everything else on"
echo "this pod is reproducible, so terminate it once the file is downloaded."
