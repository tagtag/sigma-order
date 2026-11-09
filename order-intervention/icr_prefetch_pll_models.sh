#!/bin/sh
#=====================================================================
# Fetch the small evaluators on the LOGIN node (compute nodes have no net).
#
# These are small enough that the disk worry which applied to LLaDA-8B
# (~15 GB) does not apply here:
#
#     bert-base-uncased     ~0.44 GB
#     bert-large-uncased    ~1.3  GB
#     gpt2                  ~0.55 GB
#     ------------------------------
#     total                 ~2.3  GB
#
# Everything lands in the shared HF cache (HF_HOME), referenced later by repo
# id with HF_HUB_OFFLINE=1.  No --local-dir: that makes a SECOND copy of every
# weight file beside the cache, which is what nearly filled the quota last
# time.
#
#   sh icr_prefetch_pll_models.sh --check     report sizes, transfer nothing
#   sh icr_prefetch_pll_models.sh             fetch
#   sh icr_prefetch_pll_models.sh --purge     delete just these from the cache
#=====================================================================

set -e

: "${HF_HOME:=$HOME/.cache/huggingface}"
export HF_HOME
: "${MODELS:=bert-base-uncased bert-large-uncased gpt2}"

mkdir -p "$HF_HOME"

# ---- fail fast on a missing client ---------------------------------
# Without this the script reaches the heredoc and dies on
# "ModuleNotFoundError: No module named 'huggingface_hub'" AFTER printing the
# disk report, which reads like the fetch succeeded.  Worse, a job submitted
# afterwards then fails on an empty cache with HF_HUB_OFFLINE=1, far from the
# real cause.
if ! python3 -c "import huggingface_hub" 2>/dev/null; then
    echo "ERROR: huggingface_hub is not available to this python3."
    echo
    echo "  python3 : $(command -v python3)"
    python3 -c "import sys; print('  version :', sys.version.split()[0])"
    echo
    echo "Install it in the environment this shell is using, on the LOGIN"
    echo "node (compute nodes have no internet):"
    echo
    echo "    pip install huggingface_hub transformers scipy"
    echo
    echo "then re-run this script.  Whatever environment you install into is"
    echo "the one icr_job_pll.sh must activate -- pass it as"
    echo "    qsub -v PYENV=conda,CONDA_ENV=<name> icr_job_pll.sh"
    exit 1
fi

case "${1:-}" in
  --check)
    echo "=== free space on the filesystem holding HF_HOME ==="
    df -h "$HF_HOME"
    echo
    echo "=== quota, if the site reports one ==="
    (quota -s 2>/dev/null || lfs quota -h "$HOME" 2>/dev/null \
        || echo "  no quota command available") | head -20
    echo
    echo "=== what each repo would cost (metadata only, no file transfer) ==="
    python3 - $MODELS <<'PY'
import sys
from huggingface_hub import HfApi
api = HfApi()
total = 0
for rid in sys.argv[1:]:
    try:
        info = api.model_info(rid, files_metadata=True)
    except Exception as e:
        print(f"  {rid}: could not query ({e})")
        continue
    # Only the weight format actually loaded is counted: safetensors when the
    # repo has it, otherwise the .bin files.  Counting both would roughly
    # double the estimate for repos that ship each format.
    files = [s for s in info.siblings if s.size]
    st = [s for s in files if s.rfilename.endswith(".safetensors")]
    use = st if st else [s for s in files if s.rfilename.endswith(".bin")]
    other = [s for s in files
             if not s.rfilename.endswith((".safetensors", ".bin", ".h5",
                                          ".msgpack", ".ot"))]
    n = sum(s.size for s in use + other)
    total += n
    print(f"  {rid:<26} {n/1e9:6.2f} GB  ({len(use)} weight file(s), "
          f"{'safetensors' if st else 'bin'})")
print(f"  {'TOTAL':<26} {total/1e9:6.2f} GB")
PY
    echo
    echo "=== already in the cache ==="
    du -sh "$HF_HOME" 2>/dev/null || true
    python3 - <<'PY'
try:
    from huggingface_hub import scan_cache_dir
    c = scan_cache_dir()
    for r in sorted(c.repos, key=lambda r: -r.size_on_disk):
        print(f"  {r.repo_id:<30} {r.size_on_disk/1e9:6.2f} GB")
    print(f"  {'cache total':<30} {c.size_on_disk/1e9:6.2f} GB")
except Exception as e:
    print(f"  (scan failed: {e})")
PY
    exit 0
    ;;
  --purge)
    echo "Deleting only these repos from the cache: $MODELS"
    python3 - $MODELS <<'PY'
import sys
from huggingface_hub import scan_cache_dir
want = set(sys.argv[1:])
c = scan_cache_dir()
hashes = [rev.commit_hash for r in c.repos if r.repo_id in want
          for rev in r.revisions]
if not hashes:
    print("  nothing to delete")
else:
    s = c.delete_revisions(*hashes)
    print(f"  freeing {s.expected_freed_size_str}")
    s.execute()
    print("  done")
PY
    du -sh "$HF_HOME" 2>/dev/null || true
    exit 0
    ;;
esac

echo "=== fetching into $HF_HOME ==="
python3 - $MODELS <<'PY'
import sys, time
from huggingface_hub import HfApi, snapshot_download
api = HfApi()
for rid in sys.argv[1:]:
    t0 = time.time()
    # Allowing BOTH *.safetensors and *.bin downloads the same weights twice
    # for every repo that ships both -- which bert-base, bert-large and gpt2
    # all do, turning a 2.3 GB fetch into 4.6 GB.  Ask the repo which formats
    # it has and take exactly one: safetensors when available (transformers
    # prefers it anyway), the .bin files only as a fallback.
    try:
        files = api.list_repo_files(rid)
    except Exception as e:
        print(f"  {rid}: could not list files ({e}); skipping")
        continue
    fmt = "*.safetensors" if any(f.endswith(".safetensors") for f in files) \
        else "*.bin"
    p = snapshot_download(
        repo_id=rid, max_workers=8,
        allow_patterns=["*.json", "*.txt", "*.model", fmt],
        ignore_patterns=["*.h5", "*.msgpack", "*.ot", "*onnx*"])
    print(f"  {rid:<26} ready in {time.time()-t0:5.0f}s  [{fmt}]  -> {p}")
PY

echo
echo "=== cache after ==="
du -sh "$HF_HOME" 2>/dev/null || true
echo
echo "Now:  qsub icr_job_pll.sh"
