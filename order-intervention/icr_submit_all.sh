#!/bin/sh
#=====================================================================
# Submit the whole (corpus x order) grid on the ICR supercomputer.
# Run this ON THE LOGIN NODE.  It only calls qsub; no computation here
# (the login node is limited to 30 min CPU and 8 GB).
#
#   sh icr_submit_all.sh            # submit
#   sh icr_submit_all.sh --dry      # print the qsub lines without submitting
#
# PBS Professional supports job arrays (qsub -J 0-N), but the ICR
# documentation gives no array example, so this uses one qsub per task:
# the grid is small (5 corpora x 5 orders = 25 jobs) and per-task files
# make reruns trivial.  The 4-GPU-per-user cap means about 4 run at once.
#=====================================================================

DRY=0
[ "$1" = "--dry" ] && DRY=1

# Weights stay as ONE copy in the hub cache on /aptmp (re-downloadable, keeps
# the 100 GB home quota clear); results go to home.  Override with
#   MODEL_ID=Dream-org/Dream-v0-Base-7B sh icr_submit_all.sh
: "${APTMP:=/aptmp/$USER}"
: "${HF_HOME:=$APTMP/hf}"
: "${MODEL_ID:=GSAI-ML/LLaDA-8B-Base}"
: "${PYENV:=conda}"
: "${CONDA_ENV:=r44}"
export MODEL_ID APTMP HF_HOME PYENV CONDA_ENV

CACHED="$HF_HOME/hub/models--$(echo "$MODEL_ID" | sed 's|/|--|')"
if [ $DRY -eq 0 ] && [ ! -d "$CACHED" ]; then
  echo "ERROR: $MODEL_ID is not cached at $CACHED"
  echo "On the LOGIN node run:  sh icr_prefetch_model.sh --check   (then without --check)"
  exit 1
fi

CORPORA="Opus46 Fable5 Gemini31 GPT54 GPT56"
ORDERS="l2r r2l random:1 random:2 confidence"

for c in $CORPORA; do
  for o in $ORDERS; do
    cmd="qsub -v CORPUS=$c,ORDER=$o,MODEL_ID=$MODEL_ID,APTMP=$APTMP,HF_HOME=$HF_HOME,PYENV=$PYENV,CONDA_ENV=$CONDA_ENV -N aoar_${c}_$(echo "$o" | tr ':' '-') icr_job_single.sh"
    if [ $DRY -eq 1 ]; then echo "$cmd"; else eval "$cmd"; sleep 1; fi
  done
done

# Diagnostic arm: mirror the order with the text (Bayesian-retrodiction
# flavoured) instead of keeping it fixed in position space.  Only the
# left-to-right order is needed to make the point.
for c in $CORPORA; do
  cmd="qsub -v CORPUS=$c,ORDER=l2r,FOLLOW=1,MODEL_ID=$MODEL_ID,APTMP=$APTMP,HF_HOME=$HF_HOME,PYENV=$PYENV,CONDA_ENV=$CONDA_ENV -N aoar_${c}_follow icr_job_single.sh"
  if [ $DRY -eq 1 ]; then echo "$cmd"; else eval "$cmd"; sleep 1; fi
done

echo
echo "watch with:  qstat -u \$USER"
echo "then:        python3 aggregate_orders.py --glob 'results/*.json'"
