#!/bin/bash
#=====================================================================
# Follow-up run: many random unmasking orders on the two corpora whose
# effect size varied, to separate two explanations.
#
# What the first run left open
# ----------------------------
# Paired bootstrap (B=10000) found a genuine difference between orders in
# 2 of 5 corpora, surviving Holm:
#     GPT54   r2l vs random:1   diff 0.324  CI [0.146, 0.507]  p_holm 0.0024
#     Opus46  l2r vs random:2   diff 0.275  CI [0.101, 0.449]  p_holm 0.0048
# but the differing pairs follow no common pattern, and in GPT54 the two
# RANDOM orders nearly differ from each other (diff -0.191, p_boot 0.041).
# Two readings remain:
#     (a) the order matters structurally (left-to-right vs right-to-left
#         vs scrambled carry different information), or
#     (b) any particular permutation adds idiosyncratic variation, and two
#         random draws were simply not enough to see its size.
# Two random seeds cannot tell these apart.
#
# The design
# ----------
# Ten random seeds give the EMPIRICAL null for "an arbitrary order": the
# spread of r among them is permutation idiosyncrasy, measured rather than
# assumed.  l2r and r2l are then tested against that cloud.  If they sit
# inside it, reading (b) wins and the effect size is order invariant in any
# meaningful sense.  If they sit outside, reading (a) wins and the structured
# orders really do carry different information.
#
# This replaces all-pairs testing, which with twelve orders would mean
# 66 comparisons per corpus and no power after correction.
#
# Scope: 2 corpora x 12 orders.  At the first run's per-task times
# (Opus46 128 s, GPT54 68 s) that is about 40 minutes, roughly $0.6 on a
# 4090.  Everything else is unchanged from rented_run_all.sh.
#
#   bash rented_run_seeds.sh
#=====================================================================

set -euo pipefail

MODEL_ID="${MODEL_ID:-GSAI-ML/LLaDA-8B-Base}"
MASK_ID="${MASK_ID:-126336}"
# l2r and r2l are the structured anchors; the ten seeds are the null cloud.
ORDERS="${ORDERS:-l2r,r2l,random:1,random:2,random:3,random:4,random:5,random:6,random:7,random:8,random:9,random:10}"
CORPORA="${CORPORA:-Opus46 GPT54}"
MAX_BATCH="${MAX_BATCH:-32}"
WORK="${WORK:-$PWD}"
OUTDIR="$WORK/results_seeds"

echo "=== 0. what we are on ==="
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv || {
    echo "no GPU visible; stop here"; exit 1; }

echo
echo "=== 1. dependencies ==="
python3 - <<'PY' || pip install --quiet -U torch
import torch; print("torch present:", torch.__version__, torch.version.cuda)
PY
# transformers 5.x rewrote the loading path and LLaDA's remote code (written
# for 4.x) fails on it with
#   AttributeError: 'LLaDAModelLM' object has no attribute 'all_tied_weights_keys'
# so the 4.x line is pinned.  4.57.6 was verified working.
pip install --quiet -U "transformers<5" huggingface_hub scipy numpy
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
echo "=== 2. verify the implementation ==="
python3 -I aoar_selftest.py | tail -3

echo
echo "=== 3. corpora ==="
[ -d "$WORK/Paper2026" ] || git clone --depth 1 \
    https://github.com/taksagawa/Paper2026.git "$WORK/Paper2026"

echo
echo "=== 4. weights ==="
export HF_HOME="$WORK/hf"
mkdir -p "$HF_HOME"
python3 - "$MODEL_ID" <<'PY'
import sys, time
from huggingface_hub import snapshot_download
t0 = time.time()
p = snapshot_download(repo_id=sys.argv[1], max_workers=8)
print(f"  {p}\n  ready in {time.time()-t0:.0f}s")
PY

echo
echo "=== 5. the seed sweep ==="
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
mkdir -p "$OUTDIR"

TEXT_ARGS=()
for c in $CORPORA; do
    t="$WORK/Paper2026/gpt2/text_sets2/fixed_text_${c}.json"
    [ -f "$t" ] && TEXT_ARGS+=("$t") || echo "  WARN: no corpus for $c"
done
echo "  ${#TEXT_ARGS[@]} corpora x $(echo "$ORDERS" | tr ',' '\n' | wc -l) orders"

python3 order_intervention.py --model "$MODEL_ID" --mask-token-id "$MASK_ID" \
    --texts "${TEXT_ARGS[@]}" --order "$ORDERS" --outdir "$OUTDIR" \
    --max-batch "$MAX_BATCH"

echo
echo "=== 6. pack ==="
tar czf "$WORK/order_seeds_results.tgz" -C "$WORK" results_seeds
ls -la "$WORK/order_seeds_results.tgz"
echo
echo "Analyse with:  python3 random_cloud_test.py --dir results_seeds"
echo "Then terminate the pod."
