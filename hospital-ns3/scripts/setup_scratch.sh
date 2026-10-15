#!/usr/bin/env bash
# ==============================================================================
# setup_scratch.sh - Setup NS-3 Scratch Directory & Build Simulation Scenarios
# Disaster-Resilient Smart Hospital Network (NS-3 Extension)
# Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
# SCOPE, VIT Vellore
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SIM_DIR="${REPO_ROOT}/sim"

# Default NS-3 search candidates if NS3_DIR is not set
NS3_CANDIDATES=(
    "${NS3_DIR:-}"
    "${HOME}/ns-3"
    "${HOME}/ns-3-dev"
    "${HOME}/ns-allinone-3.43/ns-3.43"
    "${HOME}/ns-allinone-3.42/ns-3.42"
    "${HOME}/ns-allinone-3.41/ns-3.41"
    "${HOME}/ns-allinone-3.40/ns-3.40"
    "/opt/ns-3"
)

TARGET_NS3=""
USE_COPY=false

print_usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  -d, --ns3-dir PATH    Path to NS-3 source root directory (contains ./ns3)
  -c, --copy            Copy files instead of creating symbolic links
  -h, --help            Show this help message

Environment:
  NS3_DIR               Default search directory for NS-3 root
EOF
}

# Parse command line options
while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--ns3-dir)
            TARGET_NS3="$2"
            shift 2
            ;;
        -c|--copy)
            USE_COPY=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo "[ERROR] Unknown option: $1" >&2
            print_usage
            exit 1
            ;;
    esac
done

# Resolve NS-3 root if not specified via CLI
if [[ -z "${TARGET_NS3}" ]]; then
    for cand in "${NS3_CANDIDATES[@]}"; do
        if [[ -n "${cand}" && -d "${cand}" && -x "${cand}/ns3" ]]; then
            TARGET_NS3="${cand}"
            break
        fi
    done
fi

if [[ -z "${TARGET_NS3}" || ! -d "${TARGET_NS3}" || ! -x "${TARGET_NS3}/ns3" ]]; then
    echo "================================================================================" >&2
    echo "[ERROR] Could not locate a valid NS-3 installation with executable './ns3'." >&2
    echo "Please specify your NS-3 root path using:" >&2
    echo "  $(basename "$0") --ns3-dir /path/to/ns-3" >&2
    echo "or set the environment variable:" >&2
    echo "  export NS3_DIR=/path/to/ns-3" >&2
    echo "================================================================================" >&2
    exit 1
fi

SCRATCH_DIR="${TARGET_NS3}/scratch"
mkdir -p "${SCRATCH_DIR}"

echo "================================================================================"
echo "  HOSPITAL NS-3 SCENARIO SYNC & BUILD"
echo "================================================================================"
echo "  Repository Root : ${REPO_ROOT}"
echo "  Scenarios Dir   : ${SIM_DIR}"
echo "  NS-3 Root Dir   : ${TARGET_NS3}"
echo "  NS-3 Scratch    : ${SCRATCH_DIR}"
echo "  Sync Mode       : $( [ "${USE_COPY}" = true ] && echo "Copy" || echo "Symlink (with fallback)" )"
echo "================================================================================"

# Check if any .cc scenarios exist
shopt -s nullglob
CC_FILES=("${SIM_DIR}"/*.cc)
shopt -u nullglob

if [[ ${#CC_FILES[@]} -eq 0 ]]; then
    echo "[WARN] No .cc scenarios found in ${SIM_DIR}. Nothing to link."
    exit 0
fi

for src in "${CC_FILES[@]}"; do
    filename="$(basename "${src}")"
    dst="${SCRATCH_DIR}/${filename}"

    if [[ "${USE_COPY}" = true ]]; then
        echo "  [COPY] ${filename} -> ${dst}"
        cp -f "${src}" "${dst}"
    else
        echo "  [LINK] ${filename} -> ${dst}"
        ln -sf "${src}" "${dst}" || {
            echo "  [FALLBACK] Symlink failed; copying ${filename}"
            cp -f "${src}" "${dst}"
        }
    fi
done

echo "--------------------------------------------------------------------------------"
echo "[BUILD] Invoking './ns3 build' in ${TARGET_NS3}..."
echo "--------------------------------------------------------------------------------"

cd "${TARGET_NS3}"
./ns3 build

echo "================================================================================"
echo "[SUCCESS] NS-3 scratch build completed successfully!"
echo "You can now run your scenarios using:"
for src in "${CC_FILES[@]}"; do
    base="$(basename "${src}" .cc)"
    echo "  ./ns3 run \"${base} --PrintHelp\""
done
echo "================================================================================"
