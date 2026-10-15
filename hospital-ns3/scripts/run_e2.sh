#!/usr/bin/env bash
# ==============================================================================
# run_e2.sh - Automated Experiment 2 Runner (Queue Comparison & 20 Seeds)
# Disaster-Resilient Smart Hospital Network (NS-3 Extension)
# Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
# SCOPE, VIT Vellore
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RESULTS_DIR="${REPO_ROOT}/results/e2_queue"
XML_DIR="${RESULTS_DIR}/xml"

mkdir -p "${XML_DIR}"

NS3_EXE_DIR="${NS3_DIR:-${HOME}/ns-3}"
if [[ ! -x "${NS3_EXE_DIR}/ns3" ]]; then
    for cand in "${HOME}/ns-3" "${HOME}/ns-3-dev" "${HOME}/ns-allinone-3."*"/ns-3."*; do
        if [[ -x "${cand}/ns3" ]]; then
            NS3_EXE_DIR="${cand}"
            break
        fi
    done
fi

QUICK_MODE=false
for arg in "$@"; do
    if [[ "$arg" == "--quick" || "$arg" == "-q" ]]; then
        QUICK_MODE=true
    fi
done

echo "================================================================================"
echo "  EXPERIMENT E2: ACTIVE QUEUE MANAGEMENT & QOS COMPARISON"
echo "  DropTail (FIFO) vs. RED vs. PrioQueueDisc (DSCP EF / AF31 / BE)"
echo "================================================================================"
echo "  Repository Root : ${REPO_ROOT}"
echo "  NS-3 Root       : ${NS3_EXE_DIR}"
echo "  Results Dir     : ${RESULTS_DIR}"
echo "  Mode            : $( [ "$QUICK_MODE" = true ] && echo "Quick Smoke Test (2 loads, 3 queues, 2 seeds)" || echo "Full Scientific Sweep (2 loads, 3 queues, 20 seeds = 120 runs)" )"
echo "================================================================================"

# Step 1: Sync e2_queue.cc to NS-3 scratch and build
echo ">>> [STEP 1/3] Syncing e2_queue.cc to NS-3 scratch & building..."
"${SCRIPT_DIR}/setup_scratch.sh" --ns3-dir "${NS3_EXE_DIR}"

cd "${NS3_EXE_DIR}"

LOADS=(100 120)
QUEUES=("DropTail" "Red" "Prio")

if [[ "$QUICK_MODE" = true ]]; then
    SEEDS=(1 2)
else
    SEEDS=(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20)
fi

SUMMARY_CSV="${RESULTS_DIR}/e2_summary.csv"
rm -f "${SUMMARY_CSV}"

TOTAL_RUNS=$(( ${#LOADS[@]} * ${#QUEUES[@]} * ${#SEEDS[@]} ))
CURRENT=0

echo ">>> [STEP 2/3] Executing ${TOTAL_RUNS} queue simulation runs..."

for load in "${LOADS[@]}"; do
    for q in "${QUEUES[@]}"; do
        for seed in "${SEEDS[@]}"; do
            CURRENT=$(( CURRENT + 1 ))
            XML_PATH="${XML_DIR}/flowmon_load${load}_${q}_seed${seed}.xml"

            echo "  [RUN ${CURRENT}/${TOTAL_RUNS}] Load=${load}% | Queue=${q} | Seed=${seed}"
            ./ns3 run "e2_queue --loadPct=${load} --queue=${q} --seed=${seed} --run=1 --simTime=20.0 --xmlTrace=${XML_PATH} --csvSummary=${SUMMARY_CSV} --expId=E2-L${load}-${q}-S${seed}"
        done
    done
done

# Step 3: Run Python post-processing and charting pipeline
echo ">>> [STEP 3/3] Running Python statistical analysis & generating publication charts..."
python3 "${REPO_ROOT}/analysis/e2_analysis.py" --csv-file "${SUMMARY_CSV}" --outdir "${RESULTS_DIR}"

echo "================================================================================"
echo "[SUCCESS] Experiment E2 completed successfully!"
echo "Artifacts generated in ${RESULTS_DIR}:"
echo "  - e2_summary.csv"
echo "  - e2_queue_comparison_bars.png (and .pdf)"
echo "  - e2_icu_delay_cdf.png (and .pdf)"
echo "  - e2_findings.md"
echo "================================================================================"
