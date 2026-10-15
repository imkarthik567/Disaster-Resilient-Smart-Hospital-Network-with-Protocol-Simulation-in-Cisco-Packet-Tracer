#!/usr/bin/env bash
# ==============================================================================
# run_e3.sh - Automated Experiment 3 Runner (Packet Size & Load Regime Sweep)
# Disaster-Resilient Smart Hospital Network (NS-3 Extension)
# Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
# SCOPE, VIT Vellore
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RESULTS_DIR="${REPO_ROOT}/results/e3_packet_size"
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
echo "  EXPERIMENT E3: PACKET SIZE, PROTOCOL EFFICIENCY & QUEUING DIVERGENCE"
echo "  Payload Sizes: [64, 128, 256, 512, 1024, 1460 bytes]"
echo "  Load Regimes : Light (30%), Near Saturation (90%), Overloaded (120%)"
echo "================================================================================"
echo "  Repository Root : ${REPO_ROOT}"
echo "  NS-3 Root       : ${NS3_EXE_DIR}"
echo "  Results Dir     : ${RESULTS_DIR}"
echo "  Mode            : $( [ "$QUICK_MODE" = true ] && echo "Quick Smoke Test (3 sizes, 3 loads, 2 seeds)" || echo "Full Scientific Sweep (6 sizes, 3 loads, 20 seeds = 360 runs)" )"
echo "================================================================================"

# Step 1: Sync e3_packet_size.cc to NS-3 scratch and build
echo ">>> [STEP 1/3] Syncing e3_packet_size.cc to NS-3 scratch & building..."
"${SCRIPT_DIR}/setup_scratch.sh" --ns3-dir "${NS3_EXE_DIR}"

cd "${NS3_EXE_DIR}"

if [[ "$QUICK_MODE" = true ]]; then
    SIZES=(128 256 1024)
    LOADS=("light" "near_sat" "overloaded")
    SEEDS=(1 2)
else
    SIZES=(64 128 256 512 1024 1460)
    LOADS=("light" "near_sat" "overloaded")
    SEEDS=(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20)
fi

SUMMARY_CSV="${RESULTS_DIR}/e3_summary.csv"
rm -f "${SUMMARY_CSV}"

TOTAL_RUNS=$(( ${#SIZES[@]} * ${#LOADS[@]} * ${#SEEDS[@]} ))
CURRENT=0

echo ">>> [STEP 2/3] Executing ${TOTAL_RUNS} simulation runs..."

for size in "${SIZES[@]}"; do
    for mode in "${LOADS[@]}"; do
        for seed in "${SEEDS[@]}"; do
            CURRENT=$(( CURRENT + 1 ))
            XML_PATH="${XML_DIR}/flowmon_s${size}_${mode}_seed${seed}.xml"

            echo "  [RUN ${CURRENT}/${TOTAL_RUNS}] Size=${size}B | Mode=${mode} | Seed=${seed}"
            ./ns3 run "e3_packet_size --packetSize=${size} --loadMode=${mode} --seed=${seed} --run=1 --simTime=15.0 --xmlTrace=${XML_PATH} --csvSummary=${SUMMARY_CSV} --expId=E3-S${size}-${mode}-seed${seed}"
        done
    done
done

# Step 3: Run Python post-processing and charting pipeline
echo ">>> [STEP 3/3] Running Python statistical analysis & generating publication charts..."
python3 "${REPO_ROOT}/analysis/e3_analysis.py" --csv-file "${SUMMARY_CSV}" --outdir "${RESULTS_DIR}"

echo "================================================================================"
echo "[SUCCESS] Experiment E3 completed successfully!"
echo "Artifacts generated in ${RESULTS_DIR}:"
echo "  - e3_summary.csv"
echo "  - e3_efficiency_overhead.png (and .pdf)"
echo "  - e3_delay_vs_size.png (and .pdf)"
echo "  - e3_goodput_vs_size.png (and .pdf)"
echo "  - e3_findings.md"
echo "================================================================================"
