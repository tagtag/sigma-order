#!/bin/sh
#=====================================================================
# Fetch masked-diffusion model weights for the Kyoto ICR supercomputer
# WITHOUT duplicating them and WITHOUT touching the home quota.
#
# Why this script exists
# ----------------------
# `huggingface-cli download --local-dir DIR` can materialise TWO copies --
# one in the shared blob cache and one in DIR -- depending on the
# huggingface_hub version.  For an 8B bf16 model that is ~32 GB instead of
# ~16 GB.  We therefore do NOT use --local-dir.  One copy goes into the hub
# cache under $HF_HOME, and transformers reads it straight from there with
# HF_HUB_OFFLINE=1 using the plain repo id -- no second copy, no path juggling.
#
# Disk policy (https://www.scl.kyoto-u.ac.jp/Attention/quota.html,
#              https://www.scl.kyoto-u.ac.jp/Attention/aptmp.html):
#   home          100 GB / 2,000,000 files by default; EXCEEDING IT BLOCKS
#                 ALL WRITES TO HOME
#   /aptmp/$USER  shared across compute servers, unbilled, no stated quota,
#                 but files MAY BE PURGED WITHOUT NOTICE and the area is not
#                 to be monopolised
#   ${TMPDIR}     per job, deleted at job end; on APC/APG it sits on Lustre
#
# Usage
# -----
#   sh icr_prefetch_model.sh --check     # sizes and free space only, NO download
#   sh icr_prefetch_model.sh             # download after the check passes
#   sh icr_prefetch_model.sh --purge     # delete the cached model again
#
#   MODEL_ID=Dream-org/Dream-v0-Base-7B sh icr_prefetch_model.sh --check
#
# Nothing is downloaded until --check has reported the real figures.
#=====================================================================

set -e

: "${MODEL_ID:=GSAI-ML/LLaDA-8B-Base}"
: "${APTMP:=/aptmp/$USER}"
: "${HF_HOME:=$APTMP/hf}"
: "${MARGIN_GB:=20}"      # free space required on top of the model itself

export HF_HOME
export HF_HUB_DISABLE_TELEMETRY=1
export TOKENIZERS_PARALLELISM=false
CACHE="$HF_HOME/hub"

MODE="${1:-download}"

repo_slug=$(echo "$MODEL_ID" | tr '/' '-')
REPO_DIR="$CACHE/models--$(echo "$MODEL_ID" | sed 's|/|--|')"

# ---------------------------------------------------------------- purge
# huggingface_hub >= 2.x uses Xet storage: the snapshot under hub/ holds
# pointers and the actual bytes live in $HF_HOME/xet/.  So `du -sh` on the
# model dir can report a few MB while $HF_HOME holds ~15 GB, and deleting the
# model dir alone frees almost nothing.  The xet cache is SHARED across every
# model, so it is only safe to wipe when no other model is wanted.
if [ "$MODE" = "--purge" ] || [ "$MODE" = "--purge-all" ]; then
    echo "--- sizes ---"
    for d in "$REPO_DIR" "$HF_HOME/xet" "$HF_HOME"; do
        [ -e "$d" ] && echo "  $(du -sh "$d" 2>/dev/null)"
    done
    if [ -d "$REPO_DIR" ]; then
        echo "deleting $REPO_DIR"
        rm -rf "$REPO_DIR"
    else
        echo "nothing cached at $REPO_DIR"
    fi
    if [ "$MODE" = "--purge-all" ]; then
        echo "deleting the shared Xet cache $HF_HOME/xet"
        rm -rf "$HF_HOME/xet"
        echo "done."
    else
        cat <<EOF

NOTE: the model directory held only pointers if Xet storage is in use.
The bytes are in $HF_HOME/xet (shared by ALL models).  To reclaim them:
    sh icr_prefetch_model.sh --purge-all
Do that only when no other cached model is still needed.
EOF
    fi
    exit 0
fi

# ------------------------------------------------------------- figures
echo "=== model: $MODEL_ID ==="
echo "=== cache: $CACHE ==="
echo

echo "--- real download size (metadata only, nothing transferred) ---"
python3 - "$MODEL_ID" <<'PY'
import sys
try:
    import huggingface_hub
    from huggingface_hub import HfApi
except ImportError:
    sys.exit("huggingface_hub is not installed: pip install -U huggingface_hub")
print(f"  huggingface_hub  : {huggingface_hub.__version__}")
info = HfApi().model_info(sys.argv[1], files_metadata=True)
tot = 0
big = []
for s in info.siblings:
    n = s.size or 0
    tot += n
    if n > 100 * 1024**2:
        big.append((n, s.rfilename))
print(f"  files            : {len(info.siblings)}")
print(f"  total            : {tot/1024**3:.2f} GiB")
for n, f in sorted(big, reverse=True)[:6]:
    print(f"    {n/1024**3:7.2f} GiB  {f}")
pys = [s.rfilename for s in info.siblings if s.rfilename.endswith('.py')]
print(f"  modeling .py     : {len(pys)}  {pys[:4]}")
print(f"  SIZE_GIB={tot/1024**3:.3f}")
PY

SIZE_GIB=$(python3 - "$MODEL_ID" <<'PY'
from huggingface_hub import HfApi
import sys
info = HfApi().model_info(sys.argv[1], files_metadata=True)
print(f"{sum(s.size or 0 for s in info.siblings)/1024**3:.3f}")
PY
)

echo
echo "--- free space ---"
mkdir -p "$APTMP" 2>/dev/null || true
df -h "$APTMP" 2>/dev/null || df -h /aptmp || true
AVAIL_GB=$(df -BG "$APTMP" 2>/dev/null | tail -1 | awk '{gsub("G","",$4); print $4}')
echo "  /aptmp available : ${AVAIL_GB:-unknown} GB"
echo "  already cached   : $([ -d "$REPO_DIR" ] && du -sh "$REPO_DIR" | cut -f1 || echo none)"

echo
echo "--- home quota (kbytes; the model does NOT go here) ---"
quota -v 2>/dev/null || echo "  (quota unavailable on this host)"

NEED=$(python3 -c "import math;print(math.ceil($SIZE_GIB)+$MARGIN_GB)")
echo
echo "=== verdict ==="
echo "  model needs ~${SIZE_GIB} GiB; requiring ${NEED} GB free (model + ${MARGIN_GB} GB margin)"
if [ -n "$AVAIL_GB" ] && [ "$AVAIL_GB" -lt "$NEED" ] 2>/dev/null; then
    echo "  INSUFFICIENT: only ${AVAIL_GB} GB free on /aptmp"
    echo "  options: free space, ask staff, or pick a smaller model"
    [ "$MODE" = "--check" ] || exit 1
else
    echo "  OK"
fi

if [ "$MODE" = "--check" ]; then
    cat <<EOF

--check only; nothing was downloaded.
To proceed:   sh icr_prefetch_model.sh
To remove:    sh icr_prefetch_model.sh --purge
EOF
    exit 0
fi

# ------------------------------------------------------------ download
echo
echo "=== downloading into the hub cache (single copy, no --local-dir) ==="
# The Python API is used rather than the console script: `huggingface-cli` may
# be missing from PATH (pip --user puts it in ~/.local/bin) and recent
# huggingface_hub versions renamed it to `hf`.  snapshot_download is exactly
# what the CLI calls, it writes ONE copy into the hub cache under HF_HOME, and
# it resumes an interrupted transfer on rerun.
python3 - "$MODEL_ID" <<'PY'
import sys
from huggingface_hub import snapshot_download
# No resume_download kwarg: it was deprecated and then removed (resume is
# always on now), and passing it raises TypeError on recent versions.
p = snapshot_download(
    repo_id=sys.argv[1],
    max_workers=4,            # modest: the login node is CPU-time limited
)
print(f"\n  snapshot: {p}")
PY

echo
echo "=== after ==="
du -sh "$REPO_DIR" 2>/dev/null || true
du -sh "$HF_HOME" 2>/dev/null || true
df -h "$APTMP" 2>/dev/null | tail -1

echo
echo "=== offline load check (no network) ==="
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python3 - "$MODEL_ID" <<'PY'
import sys
from transformers import AutoConfig, AutoTokenizer
rid = sys.argv[1]
c = AutoConfig.from_pretrained(rid, trust_remote_code=True)
t = AutoTokenizer.from_pretrained(rid, trust_remote_code=True)
print(f"  config loaded offline : {type(c).__name__}")
print(f"  tokenizer vocab       : {len(t)}")
print(f"  tokenizer.mask_token_id: {getattr(t,'mask_token_id',None)}")
PY

cat <<EOF

Done.  Jobs read the cache by repo id, so pass the ID, not a path:

    MODEL_ID=$MODEL_ID sh icr_submit_all.sh

Remove the weights when the grid is finished:

    sh icr_prefetch_model.sh --purge
EOF
