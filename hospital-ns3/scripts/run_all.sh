#!/usr/bin/env bash
# ==============================================================================
# run_all.sh - Master Orchestrator for All Hospital Network Simulations
# Disaster-Resilient Smart Hospital Network (NS-3 Extension)
# Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
# SCOPE, VIT Vellore
# ==============================================================================
# Executes all experiment suites across seeds, writes structured outputs to
# results/<experiment>/, logs failures without aborting the suite, and summarizes.
# ==============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RESULTS_ROOT="${REPO_ROOT}/results"
LOG_DIR="${RESULTS_ROOT}/logs"
mkdir -p "${LOG_DIR}"

TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
MASTER_LOG="${LOG_DIR}/master_run_${TIMESTAMP}.log"

echo "================================================================================" | tee -a "${MASTER_LOG}"
echo "  DISASTER-RESILIENT SMART HOSPITAL NETWORK - MASTER SIMULATION SUITE" | tee -a "${MASTER_LOG}"
echo "  Repository Root : ${REPO_ROOT}" | tee -a "${MASTER_LOG}"
echo "  Results Root    : ${RESULTS_ROOT}" | tee -a "${MASTER_LOG}"
echo "  Master Log      : ${MASTER_LOG}" | tee -a "${MASTER_LOG}"
echo "================================================================================" | tee -a "${MASTER_LOG}"

# Step 0: Run Unit Tests on FlowMonitor Parser & Stats
echo -e "\n>>> [STEP 0/6] Running Pytest Suite to Verify Parser & Statistical Functions..." | tee -a "${MASTER_LOG}"
if python3 -m pytest "${REPO_ROOT}/tests/test_flowmon_parse.py" -v >> "${MASTER_LOG}" 2>&1; then
    echo "  [PASS] Pytest Suite passed successfully!" | tee -a "${MASTER_LOG}"
else
    echo "  [WARNING] Pytest reported errors. Check ${MASTER_LOG} for details." | tee -a "${MASTER_LOG}"
fi

# Track experiment status
declare -A EXP_STATUS

run_experiment() {
    local exp_name="$1"
    local exp_script="$2"
    shift 2
    local extra_args="$@"

    echo -e "\n================================================================================" | tee -a "${MASTER_LOG}"
    echo ">>> Running Experiment: ${exp_name}" | tee -a "${MASTER_LOG}"
    echo "================================================================================" | tee -a "${MASTER_LOG}"

    local exp_log="${LOG_DIR}/${exp_name}_${TIMESTAMP}.log"

    if [[ -x "${exp_script}" ]]; then
        if "${exp_script}" ${extra_args} >> "${exp_log}" 2>&1; then
            echo "[SUCCESS] ${exp_name} completed cleanly. Log -> ${exp_log}" | tee -a "${MASTER_LOG}"
            EXP_STATUS["${exp_name}"]="SUCCESS"
        else
            echo "[ERROR] ${exp_name} failed. Continuing without stopping... Log -> ${exp_log}" | tee -a "${MASTER_LOG}"
            EXP_STATUS["${exp_name}"]="FAILED"
        fi
    else
        echo "[SKIP] Script ${exp_script} not found or not executable." | tee -a "${MASTER_LOG}"
        EXP_STATUS["${exp_name}"]="NOT_FOUND"
    fi
}

# Run Experiment Suite with CLI flags (e.g. --quick)
EXTRA_FLAGS="$@"

run_experiment "E1_TCP_UDP"       "${SCRIPT_DIR}/run_e1.sh" ${EXTRA_FLAGS}
run_experiment "E2_QUEUE_QOS"     "${SCRIPT_DIR}/run_e2.sh" ${EXTRA_FLAGS}
run_experiment "E3_PACKET_SIZE"   "${SCRIPT_DIR}/run_e3.sh" ${EXTRA_FLAGS}
run_experiment "E4_TCP_DYNAMICS"  "${SCRIPT_DIR}/run_e4.sh" ${EXTRA_FLAGS}
run_experiment "E5_WAN_FAILOVER"  "${SCRIPT_DIR}/run_e5.sh" ${EXTRA_FLAGS}

echo -e "\n================================================================================" | tee -a "${MASTER_LOG}"
echo "  MASTER EXECUTION SUMMARY" | tee -a "${MASTER_LOG}"
echo "================================================================================" | tee -a "${MASTER_LOG}"
for exp in "${!EXP_STATUS[@]}"; do
    printf "  %-25s : [%s]\n" "${exp}" "${EXP_STATUS[$exp]}" | tee -a "${MASTER_LOG}"
done
echo "================================================================================" | tee -a "${MASTER_LOG}"
echo "All outputs and publication charts compiled in: ${RESULTS_ROOT}" | tee -a "${MASTER_LOG}"
echo "================================================================================" | tee -a "${MASTER_LOG}"
