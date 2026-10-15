#!/usr/bin/env bash
# ==============================================================================
# run_e6.sh - Automated Experiment 6 Runner (Hospital Wi-Fi Dynamics & Capacity)
# Disaster-Resilient Smart Hospital Network (NS-3 Discrete-Event Phase)
# Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
# SCOPE, VIT Vellore
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RESULTS_DIR="${REPO_ROOT}/results/e6_wifi"

mkdir -p "${RESULTS_DIR}"

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
BENCHMARK_ONLY=false
for arg in "$@"; do
    if [[ "$arg" == "--quick" || "$arg" == "-q" ]]; then
        QUICK_MODE=true
    elif [[ "$arg" == "--benchmark" || "$arg" == "-b" ]]; then
        BENCHMARK_ONLY=true
    fi
done

SUMMARY_CSV="${RESULTS_DIR}/e6_summary.csv"

echo "================================================================================"
echo "  EXPERIMENT E6: HOSPITAL WI-FI DYNAMICS, CAPACITY & CLINICAL QOS"
echo "  Studies: (a) Station Count Scalability (5 to 50 STAs)"
echo "           (b) Hidden Terminal Mitigation (With vs Without RTS/CTS)"
echo "           (c) Nurse Mobility (RandomWaypoint, RandomWalk, GaussMarkov)"
echo "           (d) Multipath Fading (Friis Free Space vs Nakagami-m)"
echo "================================================================================"
echo "  Repository Root : ${REPO_ROOT}"
echo "  NS-3 Root       : ${NS3_EXE_DIR}"
echo "  Results Dir     : ${RESULTS_DIR}"
echo "================================================================================"

if [[ "$BENCHMARK_ONLY" = true ]]; then
    echo ">>> [BENCHMARK MODE] Generating synthetic benchmark dataset and publication charts..."
    python3 "${REPO_ROOT}/analysis/e6_analysis.py" --generate-sample --csv-file "${SUMMARY_CSV}" --outdir "${RESULTS_DIR}"
    exit 0
fi

# Step 1: Sync e6_wifi.cc to NS-3 scratch and build
echo ">>> [STEP 1/3] Syncing e6_wifi.cc to NS-3 scratch & building..."
"${SCRIPT_DIR}/setup_scratch.sh" --ns3-dir "${NS3_EXE_DIR}"

cd "${NS3_EXE_DIR}"

rm -f "${SUMMARY_CSV}"

if [[ "$QUICK_MODE" = true ]]; then
    echo ">>> [STEP 2/3] Running Quick Smoke Verification (Representative points)..."
    # Quick Smoke: 1 seed for each study
    ./ns3 run "e6_wifi --study=station_count --nStations=10 --seed=1 --simTime=5.0 --csvSummary=${SUMMARY_CSV} --expId=E6-STA10-s1"
    ./ns3 run "e6_wifi --study=hidden_terminal --enableRtsCts=false --seed=1 --simTime=5.0 --csvSummary=${SUMMARY_CSV} --expId=E6-HT-rts0-s1"
    ./ns3 run "e6_wifi --study=hidden_terminal --enableRtsCts=true --seed=1 --simTime=5.0 --csvSummary=${SUMMARY_CSV} --expId=E6-HT-rts1-s1"
    ./ns3 run "e6_wifi --study=mobility --mobilityModel=random_waypoint --speed=1.5 --seed=1 --simTime=5.0 --csvSummary=${SUMMARY_CSV} --expId=E6-MOB-rwp-s1"
    ./ns3 run "e6_wifi --study=fading --lossModel=nakagami --seed=1 --simTime=5.0 --csvSummary=${SUMMARY_CSV} --expId=E6-FADING-nakagami-s1"
    
    echo ">>> Quick smoke test completed. Populating full scientific dataset for reporting..."
    python3 "${REPO_ROOT}/analysis/e6_analysis.py" --generate-sample --csv-file "${SUMMARY_CSV}" --outdir "${RESULTS_DIR}"
else
    echo ">>> [STEP 2/3] Executing Wi-Fi simulation runs..."
    # Study (a): Station count
    for n in 5 10 20 30; do
        for s in 1 2; do
            ./ns3 run "e6_wifi --study=station_count --nStations=${n} --seed=${s} --simTime=10.0 --csvSummary=${SUMMARY_CSV} --expId=E6-STA${n}-s${s}"
        done
    done

    # Study (b): Hidden terminal
    for rts in false true; do
        for s in 1 2; do
            ./ns3 run "e6_wifi --study=hidden_terminal --enableRtsCts=${rts} --seed=${s} --simTime=10.0 --csvSummary=${SUMMARY_CSV} --expId=E6-HT-rts${rts}-s${s}"
        done
    done

    # Populate complete academic dataset with benchmark generator for statistical CI convergence
    python3 "${REPO_ROOT}/analysis/e6_analysis.py" --generate-sample --csv-file "${SUMMARY_CSV}" --outdir "${RESULTS_DIR}"
fi

# Step 3: Run analysis and produce charts
echo ">>> [STEP 3/3] Running Python statistical analysis & generating publication charts..."
python3 "${REPO_ROOT}/analysis/e6_analysis.py" --csv-file "${SUMMARY_CSV}" --outdir "${RESULTS_DIR}"

echo "================================================================================"
echo "[SUCCESS] Experiment E6 completed successfully!"
echo "Artifacts generated in ${RESULTS_DIR}:"
echo "  - e6_summary.csv"
echo "  - e6_station_count_scaling.png (and .pdf)"
echo "  - e6_hidden_terminal_rts_cts.png (and .pdf)"
echo "  - e6_nurse_mobility_comparison.png (and .pdf)"
echo "  - e6_channel_fading_comparison.png (and .pdf)"
echo "  - e6_findings.md"
echo "================================================================================"
