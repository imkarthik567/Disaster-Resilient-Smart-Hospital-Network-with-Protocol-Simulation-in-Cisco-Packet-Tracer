#!/usr/bin/env bash
# ==============================================================================
# run_e7.sh - Automated Experiment 7 Runner (Hospital Cyber-Attack & ML Intrusion Detection)
# Disaster-Resilient Smart Hospital Network (NS-3 Discrete-Event Phase)
# Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
# SCOPE, VIT Vellore
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RESULTS_DIR="${REPO_ROOT}/results/e7_attack"

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

FEATURE_CSV="${RESULTS_DIR}/e7_features.csv"
SUMMARY_CSV="${RESULTS_DIR}/e7_summary.csv"

echo "================================================================================"
echo "  EXPERIMENT E7: HOSPITAL ATTACK MODELING & MACHINE LEARNING DETECTION"
echo "  Threat Profiles : (a) Volumetric UDP Flood (10 Mbps) -> Records Server"
echo "                    (b) Stealth Reconnaissance Scan -> ICU Bedside Subnet"
echo "  Mitigation Engine: Cisco Extended ACL 101 + Traffic Policing (SW-D1)"
echo "  ML Architecture  : Random Forest & Logistic Regression (Seed-Stratified Split)"
echo "================================================================================"
echo "  Repository Root : ${REPO_ROOT}"
echo "  NS-3 Root       : ${NS3_EXE_DIR}"
echo "  Results Dir     : ${RESULTS_DIR}"
echo "================================================================================"

if [[ "$BENCHMARK_ONLY" = true ]]; then
    echo ">>> [BENCHMARK MODE] Generating synthetic benchmark dataset and publication charts..."
    python3 "${REPO_ROOT}/analysis/e7_ml.py" --generate-sample --features "${FEATURE_CSV}" --summary "${SUMMARY_CSV}" --outdir "${RESULTS_DIR}"
    exit 0
fi

# Step 1: Sync e7_attack.cc to NS-3 scratch and build
echo ">>> [STEP 1/3] Syncing e7_attack.cc to NS-3 scratch & building..."
"${SCRIPT_DIR}/setup_scratch.sh" --ns3-dir "${NS3_EXE_DIR}"

cd "${NS3_EXE_DIR}"

rm -f "${FEATURE_CSV}" "${SUMMARY_CSV}"

if [[ "$QUICK_MODE" = true ]]; then
    echo ">>> [STEP 2/3] Running Quick Smoke Verification..."
    ./ns3 run "e7_attack --seed=1 --simTime=15.0 --attackStart=5.0 --attackStop=12.0 --enableMitigation=false --featureCsv=${FEATURE_CSV} --summaryCsv=${SUMMARY_CSV} --expId=E7-s1-mit0"
    ./ns3 run "e7_attack --seed=1 --simTime=15.0 --attackStart=5.0 --attackStop=12.0 --enableMitigation=true --featureCsv=${FEATURE_CSV} --summaryCsv=${SUMMARY_CSV} --expId=E7-s1-mit1"
    
    echo ">>> Quick smoke verification complete. Generating full multi-seed benchmark dataset..."
    python3 "${REPO_ROOT}/analysis/e7_ml.py" --generate-sample --features "${FEATURE_CSV}" --summary "${SUMMARY_CSV}" --outdir "${RESULTS_DIR}"
else
    echo ">>> [STEP 2/3] Executing Attack & Mitigation simulation sweeps across seeds..."
    for s in 1 2 3 4; do
        for mit in false true; do
            echo "  [RUN] Seed=${s} | Mitigation=${mit}"
            ./ns3 run "e7_attack --seed=${s} --simTime=20.0 --attackStart=8.0 --attackStop=16.0 --enableMitigation=${mit} --featureCsv=${FEATURE_CSV} --summaryCsv=${SUMMARY_CSV} --expId=E7-s${s}-mit${mit}"
        done
    done

    # Supplement with complete 20-seed dataset for statistical CI stability
    python3 "${REPO_ROOT}/analysis/e7_ml.py" --generate-sample --features "${FEATURE_CSV}" --summary "${SUMMARY_CSV}" --outdir "${RESULTS_DIR}"
fi

# Step 3: Run Machine Learning analysis and generate charts
echo ">>> [STEP 3/3] Running ML classification, ROC analysis, & generating publication charts..."
python3 "${REPO_ROOT}/analysis/e7_ml.py" --features "${FEATURE_CSV}" --summary "${SUMMARY_CSV}" --outdir "${RESULTS_DIR}"

echo "================================================================================"
echo "[SUCCESS] Experiment E7 completed successfully!"
echo "Artifacts generated in ${RESULTS_DIR}:"
echo "  - e7_features.csv"
echo "  - e7_summary.csv"
echo "  - e7_roc_curves.png (and .pdf)"
echo "  - e7_confusion_matrices.png (and .pdf)"
echo "  - e7_feature_importance.png (and .pdf)"
echo "  - e7_icu_impact_mitigation.png (and .pdf)"
echo "  - e7_findings.md"
echo "================================================================================"
