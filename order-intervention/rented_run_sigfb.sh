#!/bin/bash
#=====================================================================
# One-shot runbook for a rented GPU instance: the forward/backward rank test.
#
# For each text, every block arrangement p is scored with
#
#     f(p) = [ log P_l2r(x_p) - log P_r2l(x_p) ] / L
#
# and the position of the WRITTEN arrangement among the n! values recorded.
# Both terms score the same text; only the direction of assembly differs, so
# f vanishes identically for any model whose conditionals come from a joint.
# A rank exists only because the model is incompatible.
#
# This is NOT rented_run_all.sh.  That one runs order_intervention.py, which
# scores each text with THREE chain-rule passes per unmasking order (forward,
# token-reversed, block-reversed).  Here each text takes 2 x n! = 48 passes,
# so the cost is 16x that run, not 48x.
#
# Measured from the stored runs, whose elapsed_sec covers 200 texts x 3
# passes: 0.11-0.21 s per pass, giving 18-34 min per corpus and
#
#     5 corpora  ~2.1 h  ~$0.72 on a community-cloud RTX 4090
#
# REQUIREMENTS
#   VRAM   >= 24 GB   (bf16 weights 16.0 GB + ~3 GB transient at --max-batch 32)
#   disk   >= 50 GB   (15 GB of weights plus the image)
#   time   18-34 min per corpus, ~2.1 h for all five
#
# Short enough to run in one go.  To split it anyway, one corpus per pod or
# shards of one corpus across pods:
#   CORPORA=Opus46 SHARD=0/4 bash rented_run_sigfb.sh
# merge_sigfb.py concatenates shards of the same cell automatically.
#
# USAGE on a fresh pod, from the directory holding the project files:
#   bash rented_run_sigfb.sh
#
# The seven files that must be present (block_order_pll.py and pll_sigma.py
# are NOT among them: nothing here scores with a pseudo-log-likelihood):
#   aoar_core.py  order_intervention.py  block_sigma_fb.py
#   block_sigma_fb_selftest.py  block_vs_fb_selftest.py  merge_sigfb.py
#=====================================================================

set -euo pipefail

MODEL_ID="${MODEL_ID:-GSAI-ML/LLaDA-8B-Base}"
MASK_ID="${MASK_ID:-126336}"
CORPORA="${CORPORA:-Opus46 Fable5 Gemini31 GPT54 GPT56}"
MAX_BATCH="${MAX_BATCH:-32}"
SHARD="${SHARD:-0/1}"
WORK="${WORK:-$PWD}"
OUTDIR="$WORK/results_sigfb"

echo "=== 0. what we are on ==="
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv || {
    echo "no GPU visible; stop here"; exit 1; }
df -h "$WORK" | tail -1
python3 -c "import sys; print('python', sys.version.split()[0])"

echo
echo "=== 1. dependencies ==="
python3 - <<'PY' || pip install --quiet -U torch
import torch; print("torch present:", torch.__version__, torch.version.cuda)
PY
# transformers 5.x breaks the trust_remote_code path these masked models
# use; the measured runs were made on the 4.x line.  Pin it.
pip install --quiet -U "transformers>=4.45,<5" huggingface_hub scipy numpy
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
echo "=== 2. verify the statistic before spending GPU time ==="
# Seconds, no weights, and it catches a broken copy of the code.
python3 -I block_sigma_fb_selftest.py | tail -3
echo
# And that this is the forward/backward sigma, not the block-reversal one.
python3 -I block_vs_fb_selftest.py | tail -3

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
echo "=== 5. smoke run: 2 texts per category, under two minutes ==="
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
mkdir -p "$OUTDIR"

first=""
for c in $CORPORA; do
    t="$WORK/Paper2026/gpt2/text_sets2/fixed_text_${c}.json"
    [ -f "$t" ] && { first="$t"; break; }
done
[ -n "$first" ] || { echo "no corpus file found"; exit 1; }

python3 -I block_sigma_fb.py --model "$MODEL_ID" --mask-token-id "$MASK_ID" \
    --texts "$first" --device cuda --dtype bfloat16 \
    --max-batch "$MAX_BATCH" --max-perms 24 --limit 2 --out /tmp/smoke.json
echo "  smoke run OK -- check that it says 0 skipped and 0 degenerate above"

echo
echo "=== 6. the grid ==="
ran=0
for c in $CORPORA; do
    t="$WORK/Paper2026/gpt2/text_sets2/fixed_text_${c}.json"
    if [ ! -f "$t" ]; then echo "  WARN: no corpus for $c"; continue; fi
    out="$OUTDIR/sigfb_$(basename "$MODEL_ID")__fixed_text_${c}__$(echo "$SHARD" | tr '/' '-').json"
    if [ -f "$out" ]; then echo "  exists, skipping: $out"; continue; fi
    echo
    echo "--- $c ---"
    python3 -I block_sigma_fb.py --model "$MODEL_ID" --mask-token-id "$MASK_ID" \
        --texts "$t" --device cuda --dtype bfloat16 \
        --max-batch "$MAX_BATCH" --max-perms 24 --shard "$SHARD" --out "$out"
    ran=$((ran + 1))
done
if [ "$ran" -eq 0 ]; then
    echo "ERROR: nothing ran."; ls "$OUTDIR"; exit 1
fi

echo
echo "=== 7. aggregate ==="
python3 -I merge_sigfb.py --dir "$OUTDIR" | tee "$OUTDIR/merge_sigfb.log"

echo
echo "=== 8. pack the results (download this, then destroy the pod) ==="
tar czf "$WORK/sigfb_results.tgz" -C "$WORK" "$(basename "$OUTDIR")"
ls -la "$WORK/sigfb_results.tgz"
echo
echo "The tarball is the deliverable. Everything else on this pod is"
echo "reproducible, so terminate it once the file is downloaded."
