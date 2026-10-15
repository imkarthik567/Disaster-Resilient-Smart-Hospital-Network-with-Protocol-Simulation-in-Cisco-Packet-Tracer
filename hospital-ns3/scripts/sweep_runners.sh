#!/usr/bin/env bash
# ==============================================================================
# sweep_runners.sh - Multi-Seed & Parametric Sweep Runner for NS-3
# Disaster-Resilient Smart Hospital Network (NS-3 Extension)
# Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
# SCOPE, VIT Vellore
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SWEEP_DIR="${REPO_ROOT}/results/exp3_sweeps"
mkdir -p "${SWEEP_DIR}"

NS3_EXE_DIR="${NS3_DIR:-${HOME}/ns-3}"
if [[ ! -x "${NS3_EXE_DIR}/ns3" ]]; then
    for cand in "${HOME}/ns-3" "${HOME}/ns-3-dev" "${HOME}/ns-allinone-3."*"/ns-3."*; do
        if [[ -x "${cand}/ns3" ]]; then
            NS3_EXE_DIR="${cand}"
            break
        fi
    done
fi

cd "${NS3_EXE_DIR}"

echo "================================================================================"
echo "  NS-3 PARAMETRIC REPEATABILITY & TCP CONGESTION SWEEP"
echo "================================================================================"

SWEEP_CSV="${SWEEP_DIR}/sweep_summary.csv"
rm -f "${SWEEP_CSV}"

SEEDS=(1 2 3 4 5)
TCP_VARIANTS=("TcpNewReno" "TcpCubic")

TOTAL_RUNS=$(( ${#SEEDS[@]} * ${#TCP_VARIANTS[@]} ))
CURRENT=0

for tcp in "${TCP_VARIANTS[@]}"; do
    for seed in "${SEEDS[@]}"; do
        CURRENT=$(( CURRENT + 1 ))
        echo ">>> [RUN ${CURRENT}/${TOTAL_RUNS}] TCP=${tcp} | Seed=${seed} | FailureTime=12.0s..."
        ./ns3 run "hospital_baseline --seed=${seed} --run=1 --tcpVariant=${tcp} --enableFailure=true --failureTime=12.0 --simTime=25.0 --xmlTrace=${SWEEP_DIR}/flowmon_s${seed}_${tcp}.xml --csvSummary=${SWEEP_CSV} --expId=SWEEP-${tcp}-S${seed}"
    done
done

echo "================================================================================"
echo "[SUCCESS] Multi-seed sweep completed! Results compiled in:"
echo "  ${SWEEP_CSV}"
echo "================================================================================"
