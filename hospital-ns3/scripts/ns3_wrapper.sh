#!/usr/bin/env bash
# ==============================================================================
# ns3 - Standard NS-3 CLI build & runner wrapper for system libns3 installation
# Disaster-Resilient Smart Hospital Network
# Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
# SCOPE, VIT Vellore
# ==============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRATCH_DIR="${ROOT_DIR}/scratch"
BUILD_DIR="${ROOT_DIR}/build"
mkdir -p "${BUILD_DIR}"

CFLAGS="$(pkg-config --cflags ns3-internet ns3-point-to-point ns3-flow-monitor ns3-traffic-control ns3-applications ns3-netanim 2>/dev/null || true)"
LIBS="$(pkg-config --libs ns3-internet ns3-point-to-point ns3-flow-monitor ns3-traffic-control ns3-applications ns3-netanim 2>/dev/null || true)"

cmd="${1:-help}"
shift || true

if [[ "$cmd" == "build" ]]; then
    for src in "${SCRATCH_DIR}"/*.cc; do
        if [[ -f "$src" ]]; then
            base="$(basename "$src" .cc)"
            echo ">>> Building ${base}..."
            g++ -std=c++20 -O2 "$src" -o "${BUILD_DIR}/${base}" $CFLAGS $LIBS
        fi
    done
    echo "[OK] Build complete."
elif [[ "$cmd" == "run" ]]; then
    run_arg="$1"
    read -r prog args <<< "$run_arg"
    src="${SCRATCH_DIR}/${prog}.cc"
    bin="${BUILD_DIR}/${prog}"
    if [[ ! -f "$src" && -f "${ROOT_DIR}/${prog}.cc" ]]; then
        src="${ROOT_DIR}/${prog}.cc"
    fi
    if [[ -f "$src" ]]; then
        if [[ ! -x "$bin" || "$src" -nt "$bin" ]]; then
            echo ">>> Compiling ${prog}..."
            g++ -std=c++20 -O2 "$src" -o "$bin" $CFLAGS $LIBS
        fi
        exec "$bin" $args
    else
        echo "[ERROR] Source for ${prog} not found in ${SCRATCH_DIR}" >&2
        exit 1
    fi
elif [[ "$cmd" == "--version" || "$cmd" == "version" ]]; then
    echo "ns-3.46 (system libns3-dev)"
else
    echo "NS-3 System Runner"
    echo "Usage: ./ns3 [build | run \"<program> <args>\" | --version]"
fi
