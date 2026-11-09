#!/bin/sh
#=====================================================================
# Five-minute canary: verify ONLY that the GPU environment works, so a
# driver/CUDA mismatch costs five minutes instead of a day of queue wait.
#
# Submit this ALONGSIDE the real job.  A 5-minute request is the most
# schedulable thing there is, and the user cap is 4 GPUs, so it does not
# block the grid job.
#
#   qsub icr_job_canary.sh
#   cat aoar_canary.o<jobid>
#
# If it reports PASS, the grid job will get past its own preflight.
# If it reports a driver mismatch, reinstall torch before the grid job
# ever starts:
#   pip install -U torch --index-url https://download.pytorch.org/whl/cu128
#=====================================================================
#PBS -q APG
#PBS -l select=1:ncpus=2:mem=16gb:ngpus=1:Qlist=APG
#PBS -l walltime=00:05:00
#PBS -N aoar_canary
#PBS -j oe

: "${PYENV:=module}"
: "${MODULE:=pytorch/2.4.1}"
: "${CONDA_ENV:=base}"
: "${APTMP:=/aptmp/$USER}"
: "${MODEL_ID:=GSAI-ML/LLaDA-8B-Base}"
: "${MASK_ID:=126336}"

source /etc/profile.d/modules.sh
case "$PYENV" in
  conda)
    if command -v conda >/dev/null 2>&1; then
        eval "$(conda shell.bash hook)"
    elif [ -f "$HOME/miniforge3/etc/profile.d/conda.sh" ]; then
        . "$HOME/miniforge3/etc/profile.d/conda.sh"
    elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
        . "$HOME/miniconda3/etc/profile.d/conda.sh"
    fi
    conda activate "$CONDA_ENV" || echo "WARN: conda activate failed"
    ;;
  module)
    if [ -n "${CONDA_PREFIX:-}" ] && command -v conda >/dev/null 2>&1; then
        eval "$(conda shell.bash hook)"
        while [ -n "${CONDA_PREFIX:-}" ]; do conda deactivate || break; done
    fi
    module load "${MODULE:-pytorch/2.4.1}"
    ;;
esac

cd "$PBS_O_WORKDIR" 2>/dev/null || cd "$HOME"

export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export HF_HOME="${HF_HOME:-$HOME/.cache/huggingface}"
export TOKENIZERS_PARALLELISM=false
export XDG_CACHE_HOME="${TMPDIR:-$APTMP}/xdg"
export TRITON_CACHE_DIR="${TMPDIR:-$APTMP}/triton"
export PYTHONPYCACHEPREFIX="${TMPDIR:-$APTMP}/pycache"
mkdir -p "$XDG_CACHE_HOME" "$TRITON_CACHE_DIR" "$PYTHONPYCACHEPREFIX"

echo "=== canary $(date) host=$(hostname) job=$PBS_JOBID ==="
echo "--- driver ---"
nvidia-smi || echo "nvidia-smi failed"
cat /proc/driver/nvidia/version 2>/dev/null || true

echo
echo "--- torch / cuda ---"
python3 - <<'PY'
import sys
try:
    import torch
except Exception as e:
    sys.exit(f"FAIL: cannot import torch: {e}")
print(f"  torch {torch.__version__}  built for CUDA {torch.version.cuda}")
if not torch.cuda.is_available():
    sys.exit("FAIL: torch sees no CUDA device.\n"
             "  If nvidia-smi above worked, the wheel's CUDA is newer than the\n"
             "  driver. Reinstall:\n"
             "    pip install -U torch --index-url https://download.pytorch.org/whl/cu128")
p = torch.cuda.get_device_properties(0)
print(f"  gpu0 {p.name}  {p.total_memory/1024**3:.0f} GiB")
# A real kernel launch: availability alone does not prove the driver works.
x = torch.randn(2048, 2048, device="cuda", dtype=torch.bfloat16)
y = (x @ x).float().sum().item()
print(f"  bf16 matmul on device OK  (checksum {y:.3e})")
PY
rc=$?
[ $rc -ne 0 ] && { echo "=== CANARY FAILED (torch/cuda) ==="; exit $rc; }

echo
echo "--- model load (skipped unless the weights are already cached) ---"
python3 - "$MODEL_ID" "$MASK_ID" <<'PY'
import sys, time, torch
from huggingface_hub import snapshot_download
try:
    snapshot_download(repo_id=sys.argv[1], local_files_only=True)
except Exception:
    print(f"  {sys.argv[1]} is not in the cache -- skipping the load test.")
    print("  This does NOT fail the canary: the GPU checks above are what it")
    print("  is for.  Prefetch on the login node when the model is needed.")
    raise SystemExit(0)
from transformers import AutoModel, AutoTokenizer
rid, mid = sys.argv[1], int(sys.argv[2])
t0 = time.time()
tok = AutoTokenizer.from_pretrained(rid, trust_remote_code=True)
m = AutoModel.from_pretrained(rid, trust_remote_code=True,
                              torch_dtype=torch.bfloat16).cuda().eval()
print(f"  loaded in {time.time()-t0:.0f}s  vocab={len(tok)}  mask_id={mid}")
ids = tok("The glass slipped from her hand. It fell to the floor.",
          add_special_tokens=False)["input_ids"]
print(f"  tokenised T={len(ids)}")
x = torch.tensor([ids], device="cuda")
x[0, 3] = mid
with torch.no_grad():
    o = m(x)
    lg = o.logits if hasattr(o, "logits") else o[0]
print(f"  forward OK  logits {tuple(lg.shape)}")
top = lg[0, 3].float().topk(3).indices.tolist()
print(f"  top-3 at the masked position: {[tok.decode([t]) for t in top]}")
PY
rc=$?
[ $rc -ne 0 ] && { echo "=== CANARY FAILED (model load) ==="; exit $rc; }

echo
echo "=== CANARY PASS: the grid job will get past its preflight ==="
echo "=== done $(date) ==="
