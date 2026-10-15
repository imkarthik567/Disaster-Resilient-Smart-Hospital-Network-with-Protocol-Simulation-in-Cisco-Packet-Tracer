#!/usr/bin/env bash
# ==============================================================================
# run_e5.sh - Automated Experiment 5 Runner (WAN Failover & Dynamic Reconvergence)
# Disaster-Resilient Smart Hospital Network (NS-3 Discrete-Event Phase)
# Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
# SCOPE, VIT Vellore
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RESULTS_DIR="${REPO_ROOT}/results/e5_failover"
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
echo "  EXPERIMENT E5: HOSPITAL WAN FAILOVER, DYNAMIC RECONVERGENCE & RESTORATION"
echo "  Routing Modes : [static, ospf_tuned, rip, ospf_default]"
echo "  Failure Time  : 15.0 s (Primary WAN Cut)"
echo "  Restore Time  : 45.0 s (Primary WAN Restored)"
echo "  Repetitions   : $( [ "$QUICK_MODE" = true ] && echo "2 Seeds per mode (Smoke Test)" || echo "20 Seeds per mode (Full Scientific Sweep = 80 runs)" )"
echo "================================================================================"
echo "  Repository Root : ${REPO_ROOT}"
echo "  NS-3 Root       : ${NS3_EXE_DIR}"
echo "  Results Dir     : ${RESULTS_DIR}"
echo "================================================================================"

# Step 1: Sync e5_failover.cc to NS-3 scratch and build
echo ">>> [STEP 1/3] Syncing e5_failover.cc to NS-3 scratch & building..."
"${SCRIPT_DIR}/setup_scratch.sh" --ns3-dir "${NS3_EXE_DIR}"

cd "${NS3_EXE_DIR}"

if [[ "$QUICK_MODE" = true ]]; then
    MODES=("static" "ospf_tuned")
    SEEDS=(1 2)
    SIM_TIME=30.0
    FAIL_AT=10.0
    RESTORE_AT=20.0
else
    MODES=("static" "ospf_tuned" "rip" "ospf_default")
    SEEDS=(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20)
    SIM_TIME=60.0
    FAIL_AT=15.0
    RESTORE_AT=45.0
fi

SUMMARY_CSV="${RESULTS_DIR}/e5_summary.csv"
rm -f "${SUMMARY_CSV}"

TOTAL_RUNS=$(( ${#MODES[@]} * ${#SEEDS[@]} ))
CURRENT=0

echo ">>> [STEP 2/3] Executing ${TOTAL_RUNS} resilience simulation runs..."

SAMPLE_TS_FILE="${TRACES_DIR}/timeseries.csv"

for mode in "${MODES[@]}"; do
    for seed in "${SEEDS[@]}"; do
        CURRENT=$(( CURRENT + 1 ))
        TS_FILE="${TRACES_DIR}/timeseries_${mode}_s${seed}.csv"

        echo "  [RUN ${CURRENT}/${TOTAL_RUNS}] Mode=${mode} | Seed=${seed} | Fail=${FAIL_AT}s | Restore=${RESTORE_AT}s"
        ./ns3 run "e5_failover --routing=${mode} --seed=${seed} --run=1 --simTime=${SIM_TIME} --failAt=${FAIL_AT} --restoreAt=${RESTORE_AT} --timeseriesTrace=${TS_FILE} --csvSummary=${SUMMARY_CSV} --expId=E5-${mode}-s${seed}"

        # Keep representative trace for plotting
        if [[ "$seed" -eq 1 && "$mode" == "ospf_tuned" ]]; then
            cp "${TS_FILE}" "${SAMPLE_TS_FILE}"
        fi
    done
done

# Step 3: Run Python post-processing and charting pipeline
echo ">>> [STEP 3/3] Running Python statistical analysis & generating publication charts..."
python3 "${REPO_ROOT}/analysis/e5_analysis.py" --csv-file "${SUMMARY_CSV}" --timeseries-file "${SAMPLE_TS_FILE}" --outdir "${RESULTS_DIR}"

echo "================================================================================"
echo "[SUCCESS] Experiment E5 completed successfully!"
echo "Artifacts generated in ${RESULTS_DIR}:"
echo "  - e5_summary.csv"
echo "  - e5_outage_comparison_bars.png (and .pdf)"
echo "  - e5_throughput_timeseries.png (and .pdf)"
echo "  - e5_findings.md"
echo "================================================================================"
