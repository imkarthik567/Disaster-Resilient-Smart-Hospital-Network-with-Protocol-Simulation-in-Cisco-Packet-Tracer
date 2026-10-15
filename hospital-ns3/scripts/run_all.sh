#!/usr/bin/env bash
# ==============================================================================
# run_all.sh - Execute Full NS-3 Hospital Simulation Suite & Analytics
# Disaster-Resilient Smart Hospital Network (NS-3 Extension)
# Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
# SCOPE, VIT Vellore
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RESULTS_ROOT="${REPO_ROOT}/results"

echo "================================================================================"
echo "  DISASTER-RESILIENT SMART HOSPITAL NETWORK - NS-3 SIMULATION SUITE"
echo "================================================================================"

# Step 1: Sync scenarios into NS-3 scratch and build
echo ">>> [STEP 1/3] Syncing C++ Scenarios to NS-3 scratch & building..."
"${SCRIPT_DIR}/setup_scratch.sh" "$@"

# Determine NS-3 executable directory
NS3_EXE_DIR="${NS3_DIR:-${HOME}/ns-3}"
if [[ ! -x "${NS3_EXE_DIR}/ns3" ]]; then
    # Look for fallback
    for cand in "${HOME}/ns-3" "${HOME}/ns-3-dev" "${HOME}/ns-allinone-3."*"/ns-3."*; do
        if [[ -x "${cand}/ns3" ]]; then
            NS3_EXE_DIR="${cand}"
            break
        fi
    done
fi

cd "${NS3_EXE_DIR}"

# Step 2: Run Experiment 1 - Normal Baseline Operation
EXP1_DIR="${RESULTS_ROOT}/exp1_baseline"
mkdir -p "${EXP1_DIR}"
echo ">>> [STEP 2/3] Executing Experiment 1: Normal Multi-Zone Hospital Operation..."
./ns3 run "hospital_baseline --enableFailure=false --simTime=30.0 --xmlTrace=${EXP1_DIR}/flowmon.xml --csvSummary=${EXP1_DIR}/summary.csv --expId=EXP-01-BASELINE"

echo "[ANALYSIS] Processing FlowMonitor XML for Experiment 1..."
python3 "${REPO_ROOT}/analysis/parse_flowmon.py" "${EXP1_DIR}/flowmon.xml" -o "${EXP1_DIR}/flow_metrics.csv"
python3 "${REPO_ROOT}/analysis/plot_metrics.py" "${EXP1_DIR}/flow_metrics.csv" -o "${EXP1_DIR}"

# Step 3: Run Experiment 2 - Primary WAN Disaster Failure & Dynamic Convergence
EXP2_DIR="${RESULTS_ROOT}/exp2_wan_failover"
mkdir -p "${EXP2_DIR}"
echo ">>> [STEP 3/3] Executing Experiment 2: Primary WAN Fiber Cut & Dynamic Failover..."
./ns3 run "hospital_baseline --enableFailure=true --failureTime=10.0 --recoveryTime=22.0 --simTime=30.0 --xmlTrace=${EXP2_DIR}/flowmon.xml --csvSummary=${EXP2_DIR}/summary.csv --expId=EXP-02-WAN-FAILOVER"

echo "[ANALYSIS] Processing FlowMonitor XML for Experiment 2..."
python3 "${REPO_ROOT}/analysis/parse_flowmon.py" "${EXP2_DIR}/flowmon.xml" -o "${EXP2_DIR}/flow_metrics.csv"
python3 "${REPO_ROOT}/analysis/plot_metrics.py" "${EXP2_DIR}/flow_metrics.csv" -o "${EXP2_DIR}"

echo "================================================================================"
echo "[SUCCESS] All NS-3 simulation experiments completed successfully!"
echo "Results and publication charts available in:"
echo "  - ${EXP1_DIR}"
echo "  - ${EXP2_DIR}"
echo "================================================================================"
