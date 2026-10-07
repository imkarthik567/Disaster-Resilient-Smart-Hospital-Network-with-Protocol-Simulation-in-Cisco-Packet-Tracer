#!/usr/bin/env python3
"""
================================================================================
Project Task Automation Runner
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Usage:
  python tasks.py addressing   # Compute VLSM & regenerate CSV/Markdown tables
  python tasks.py lint         # Audit all device configs against policies
  python tasks.py bench        # Run host-side GBN vs SR benchmark harness
  python tasks.py charts       # Generate comparative visual charts
  python tasks.py docs         # Build all addressing, topology, and doc tables
  python tasks.py all          # Execute full build and verification pipeline
================================================================================
"""

import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def run_command(cmd, desc):
    print(f"\n>>> [TASK] {desc}...")
    res = subprocess.run([sys.executable] + cmd, cwd=PROJECT_ROOT)
    if res.returncode != 0:
        print(f"[FAILED] Task failed with exit code {res.returncode}")
        return False
    print(f"[SUCCESS] {desc} completed successfully.")
    return True

def task_addressing():
    return run_command(["addressing/vlsm.py"], "Regenerating VLSM Addressing Plan & Tables")

def task_test():
    ok1 = run_command(["tests/test_vlsm.py"], "Executing VLSM Unit Tests")
    ok2 = run_command(["tests/test_topology.py"], "Executing Topology & Cabling Verification Suite")
    return ok1 and ok2

def task_lint():
    return run_command(["verification/config_linter.py"], "Auditing Device Configurations via Linter")

def task_bench():
    return run_command(["sim/benchmark_harness.py"], "Running Protocol Benchmark Sweep Harness")

def task_charts():
    return run_command(["sim/benchmark_harness.py"], "Generating Comparative Protocol Charts")

def task_docs():
    ok1 = task_addressing()
    ok2 = run_command(["scripts/utils/generate_traceability.py"], "Regenerating Requirements Traceability Matrix")
    ok3 = run_command(["topology/generate_ptbuilder.py"], "Regenerating PTBuilder Topology Scripts from Cabling Table")
    return ok1 and ok2 and ok3

def task_all():
    print("=" * 70)
    print("  RUNNING COMPLETE PROJECT PIPELINE")
    print("=" * 70)
    steps = [
        ("Addressing", task_addressing),
        ("Linter", task_lint),
        ("Benchmarking & Charts", task_bench),
        ("Documentation Sheets", task_docs),
    ]
    for name, func in steps:
        if not func():
            print(f"\n[PIPELINE ABORTED] Step '{name}' encountered errors.")
            return False
    print("\n" + "=" * 70)
    print("  PIPELINE COMPLETE - ALL TASKS PASSED")
    print("=" * 70)
    return True

def print_help():
    print(__doc__)

def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    target = sys.argv[1].lower()
    targets = {
        "addressing": task_addressing,
        "test": task_test,
        "lint": task_lint,
        "bench": task_bench,
        "charts": task_charts,
        "docs": task_docs,
        "all": task_all,
    }

    if target in targets:
        success = targets[target]()
        sys.exit(0 if success else 1)
    else:
        print(f"[ERROR] Unknown target '{target}'.")
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
