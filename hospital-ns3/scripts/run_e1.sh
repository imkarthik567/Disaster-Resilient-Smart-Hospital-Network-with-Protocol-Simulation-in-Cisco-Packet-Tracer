#!/usr/bin/env bash
# ==============================================================================
# run_e1.sh - Automated Experiment 1 Runner (Load Sweep & 20 Seed Repetitions)
# Disaster-Resilient Smart Hospital Network (NS-3 Extension)
# Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
# SCOPE, VIT Vellore
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RESULTS_DIR="${REPO_ROOT}/results/e1_tcp_udp"
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
echo "  EXPERIMENT E1: TCP VS. UDP WAN CAPACITY & CONGESTION SWEEP"
echo "================================================================================"
echo "  Repository Root : ${REPO_ROOT}"
echo "  NS-3 Root       : ${NS3_EXE_DIR}"
echo "  Results Dir     : ${RESULTS_DIR}"
echo "  Mode            : $( [ "$QUICK_MODE" = true ] && echo "Quick Smoke Test (3 loads, 3 seeds)" || echo "Full Scientific Sweep (8 loads, 20 seeds)" )"
echo "================================================================================"

# Step 1: Sync C++ scenario to scratch and build
echo ">>> [STEP 1/3] Syncing e1_tcp_udp.cc to NS-3 scratch & building..."
"${SCRIPT_DIR}/setup_scratch.sh" --ns3-dir "${NS3_EXE_DIR}"

cd "${NS3_EXE_DIR}"

# Define parameter sweep
if [[ "$QUICK_MODE" = true ]]; then
    LOADS=(25 75 110)
    SEEDS=(1 2 3)
else
    LOADS=(10 25 50 75 90 100 110 120)
    SEEDS=(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20)
fi

SUMMARY_CSV="${RESULTS_DIR}/e1_summary.csv"
rm -f "${SUMMARY_CSV}"

TOTAL_RUNS=$(( ${#LOADS[@]} * ${#SEEDS[@]} ))
CURRENT=0

echo ">>> [STEP 2/3] Executing ${TOTAL_RUNS} simulation runs..."

for load in "${LOADS[@]}"; do
    for seed in "${SEEDS[@]}"; do
        CURRENT=$(( CURRENT + 1 ))
        XML_PATH="${XML_DIR}/flowmon_load${load}_seed${seed}.xml"

        echo "  [RUN ${CURRENT}/${TOTAL_RUNS}] Load=${load}% | Seed=${seed} -> ${XML_PATH}"
        ./ns3 run "e1_tcp_udp --loadPct=${load} --seed=${seed} --run=1 --simTime=20.0 --xmlTrace=${XML_PATH} --csvSummary=${SUMMARY_CSV} --expId=E1-L${load}-S${seed}"
    done
done

# Step 3: Run Python post-processing and charting pipeline
echo ">>> [STEP 3/3] Running Python statistical analysis & generating publication charts..."
python3 "${REPO_ROOT}/analysis/e1_analysis.py" --xml-dir "${XML_DIR}" --outdir "${RESULTS_DIR}"

echo "================================================================================"
echo "[SUCCESS] Experiment E1 completed successfully!"
echo "Artifacts generated in ${RESULTS_DIR}:"
echo "  - e1_tidy_flows.csv"
echo "  - e1_throughput_vs_load.png (and .pdf)"
echo "  - e1_delay_vs_load.png (and .pdf)"
echo "  - e1_loss_vs_load.png (and .pdf)"
echo "  - e1_findings.md"
echo "================================================================================"
