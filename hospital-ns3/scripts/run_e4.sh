#!/usr/bin/env bash
# ==============================================================================
# run_e4.sh - Automated Experiment 4 Runner (TCP Congestion Control & 50 MB PACS Bulk Transfer)
# Disaster-Resilient Smart Hospital Network (NS-3 Discrete-Event Phase)
# Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
# SCOPE, VIT Vellore
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RESULTS_DIR="${REPO_ROOT}/results/e4_tcp"
TRACES_DIR="${RESULTS_DIR}/traces"

mkdir -p "${TRACES_DIR}"

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
echo "  EXPERIMENT E4: TCP CONGESTION CONTROL DYNAMICS & 50 MB BULK PACS TRANSFER"
echo "  Variants      : [TcpNewReno, TcpCubic, TcpBbr]"
echo "  Error Rates   : [0.0%, 0.1%, 0.5%, 1.0%]"
echo "  Cross-Traffic : With and Without 500 kbps Guest Cross-Traffic"
echo "  Study Size    : 50 Megabytes Medical DICOM Study"
echo "================================================================================"
echo "  Repository Root : ${REPO_ROOT}"
echo "  NS-3 Root       : ${NS3_EXE_DIR}"
echo "  Results Dir     : ${RESULTS_DIR}"
echo "  Mode            : $( [ "$QUICK_MODE" = true ] && echo "Quick Smoke Test (3 variants, 2 error rates, 1 seed)" || echo "Full Scientific Sweep (3 variants, 4 error rates, 2 cross-traffic modes)" )"
echo "================================================================================"

# Step 1: Sync e4_tcp.cc to NS-3 scratch and build
echo ">>> [STEP 1/3] Syncing e4_tcp.cc to NS-3 scratch & building..."
"${SCRIPT_DIR}/setup_scratch.sh" --ns3-dir "${NS3_EXE_DIR}"

cd "${NS3_EXE_DIR}"

if [[ "$QUICK_MODE" = true ]]; then
    VARIANTS=("TcpNewReno" "TcpCubic")
    ERROR_RATES=("0.0" "0.005")
    GUEST_MODES=(0)
    SEEDS=(1)
    TRANSFER_MB=5 # Faster test for smoke mode
else
    VARIANTS=("TcpNewReno" "TcpCubic" "TcpBbr")
    ERROR_RATES=("0.0" "0.001" "0.005" "0.01")
    GUEST_MODES=(0 1)
    SEEDS=(1)
    TRANSFER_MB=50
fi

SUMMARY_CSV="${RESULTS_DIR}/e4_summary.csv"
rm -f "${SUMMARY_CSV}"

TOTAL_RUNS=$(( ${#VARIANTS[@]} * ${#ERROR_RATES[@]} * ${#GUEST_MODES[@]} * ${#SEEDS[@]} ))
CURRENT=0

echo ">>> [STEP 2/3] Executing ${TOTAL_RUNS} bulk transfer simulation runs..."

for var in "${VARIANTS[@]}"; do
    for err in "${ERROR_RATES[@]}"; do
        for guest in "${GUEST_MODES[@]}"; do
            for seed in "${SEEDS[@]}"; do
                CURRENT=$(( CURRENT + 1 ))
                CWND_FILE="${TRACES_DIR}/cwnd_${var}_err${err}_g${guest}.dat"

                echo "  [RUN ${CURRENT}/${TOTAL_RUNS}] Variant=${var} | Loss=${err} | Guest=${guest} | Seed=${seed}"
                ./ns3 run "e4_tcp --tcpVariant=${var} --errorRate=${err} --competingGuest=${guest} --imagingSize=${TRANSFER_MB} --seed=${seed} --run=1 --cwndTrace=${CWND_FILE} --csvSummary=${SUMMARY_CSV} --expId=E4-${var}-err${err}-g${guest}"
            done
        done
    done
done

# Step 3: Run Python post-processing and charting pipeline
echo ">>> [STEP 3/3] Running Python statistical analysis & generating publication charts..."
python3 "${REPO_ROOT}/analysis/e4_analysis.py" --csv-file "${SUMMARY_CSV}" --outdir "${RESULTS_DIR}"

echo "================================================================================"
echo "[SUCCESS] Experiment E4 completed successfully!"
echo "Artifacts generated in ${RESULTS_DIR}:"
echo "  - e4_summary.csv"
echo "  - e4_cwnd_vs_time.png (and .pdf)"
echo "  - e4_completion_time.png (and .pdf)"
echo "  - e4_throughput_retx.png (and .pdf)"
echo "  - e4_findings.md"
echo "================================================================================"
