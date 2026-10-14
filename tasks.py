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
    ok3 = run_command(["tests/test_check_topology.py"], "Executing Topology Validator & Failure-Injection Tests")
    ok4 = run_command(["tests/test_intervlan_hsrp.py"], "Executing Inter-VLAN & HSRP Gateway Redundancy Tests")
    ok5 = run_command(["tests/test_server_setup.py"], "Executing Server Farm, DHCP & DNS Services Tests")
    ok6 = run_command(["tests/test_routing_design.py"], "Executing Dynamic Routing Design & Model Tests")
    ok7 = run_command(["tests/test_routing_configs.py"], "Executing Dynamic Routing Configurations & Expected State Tests")
    ok8 = run_command(["tests/test_route_checker.py"], "Executing Cisco IOS Route Checker Tool Tests")
    ok9 = run_command(["tests/test_security_acls.py"], "Executing Security ACLs, Perimeter & Hardening Tests")
    ok10 = run_command(["tests/test_nat_edge.py"], "Executing Internet Edge, NAT/PAT & Port-Forwarding Tests")
    ok11 = run_command(["tests/test_hardening.py"], "Executing Infrastructure Device Hardening & Security Tests")
    ok12 = run_command(["tests/test_qos_design.py"], "Executing Quality of Service (QoS) Architecture & Design Tests")
    ok13 = run_command(["tests/test_sbc_environment.py"], "Executing SBC-PT Python Environment & Diagnostic Probe Tests")
    ok14 = run_command(["tests/test_errdetect_lib.py"], "Executing Error Detection & Correction Library Tests")
    ok15 = run_command(["tests/test_arq_protocols.py"], "Executing Sliding-Window ARQ Protocol & Adapter Tests")
    ok16 = run_command(["tests/test_medical_sensor_app.py"], "Executing Clinical Sensor Application & Gateway Tests")
    ok17 = run_command(["tests/test_benchmark_sweep.py"], "Executing ARQ Simulation Sweep & Statistics Tests")
    ok18 = run_command(["tests/test_analysis_charts.py"], "Executing Protocol Analysis Charts & Findings Tests")
    ok19 = run_command(["tests/test_test_matrix.py"], "Executing Master Verification Test Matrix Tests")
    return (
        ok1 and ok2 and ok3 and ok4 and ok5 and ok6 and ok7 and ok8 and
        ok9 and ok10 and ok11 and ok12 and ok13 and ok14 and ok15 and ok16 and
        ok17 and ok18 and ok19
    )

def task_lint():
    ok1 = run_command(["verification/check_topology.py"], "Validating Topology & Interconnect Cable Matrix")
    ok2 = run_command(["verification/config_linter.py"], "Auditing Device Configurations via Linter")
    return ok1 and ok2

def task_bench():
    return run_command(["sim/run_benchmarks.py"], "Running Protocol Benchmark Sweep Harness")

def task_charts():
    return run_command(["sim/analysis.py"], "Generating Publication-Quality Protocol & Error Detection Charts")

def task_docs():
    ok1 = task_addressing()
    ok2 = run_command(["scripts/utils/generate_traceability.py"], "Regenerating Requirements Traceability Matrix")
    ok3 = run_command(["topology/generate_ptbuilder.py"], "Regenerating PTBuilder Topology Scripts from Cabling Table")
    ok4 = run_command(["verification/generate_test_matrix.py"], "Regenerating Master Verification Test Matrix")
    return ok1 and ok2 and ok3 and ok4

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
