#!/usr/bin/env python3
"""
================================================================================
Cisco IOS Configuration Linter & Policy Auditor
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Audits all device configuration files in /configs/ against best practices,
packet tracer compatibility rules, and academic project standards.
"""

import os
import re
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIGS_DIR = os.path.join(PROJECT_ROOT, "configs")

RULES = [
    {"id": "RULE-01", "name": "Device Header Comment", "pattern": r"!\s*DEVICE:\s+[A-Za-z0-9_-]+", "desc": "File must include structured device header with DEVICE: field"},
    {"id": "RULE-02", "name": "Disable DNS Lookup", "pattern": r"no ip domain-lookup", "desc": "Prevent CLI DNS broadcast lockups"},
    {"id": "RULE-03", "name": "Enable Secret Configured", "pattern": r"enable secret", "desc": "Privileged exec secret must be defined"},
    {"id": "RULE-04", "name": "Console Line Security", "pattern": r"line con 0", "desc": "Console line must be secured"},
    {"id": "RULE-05", "name": "VTY Line Security", "pattern": r"line vty 0", "desc": "Telnet/SSH VTY lines must be secured"},
    {"id": "RULE-06", "name": "Verification Section Included", "pattern": r"VERIFICATION COMMANDS", "desc": "Must include show commands and expected output (Rule 2)"},
]

SWITCH_RULES = [
    {"id": "SW-RULE-01", "name": "Native VLAN 999", "pattern": r"native vlan 999", "desc": "Trunks must set native VLAN 999 for security"},
    {"id": "SW-RULE-02", "name": "Management VLAN 99", "pattern": r"(vlan 99|interface Vlan99)", "desc": "Management VLAN 99 must be declared"},
]

ROUTER_RULES = [
    {"id": "RT-RULE-01", "name": "Loopback Router-ID", "pattern": r"interface Loopback0", "desc": "Core routers must configure Loopback0 for OSPF ID"},
    {"id": "RT-RULE-02", "name": "OSPF Configured", "pattern": r"router ospf", "desc": "Dynamic routing OSPF must be configured"},
    {"id": "RT-RULE-03", "name": "EIGRP Configured", "pattern": r"router eigrp", "desc": "Standby routing EIGRP must be configured"},
]

def lint_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    dev_name = os.path.basename(os.path.dirname(filepath))
    filename = os.path.basename(filepath)
    is_switch = dev_name.startswith("SW-")
    is_router = dev_name in ["R1", "R2"]

    failures = []
    passes = []

    # General rules
    for r in RULES:
        if re.search(r["pattern"], content, re.MULTILINE | re.IGNORECASE):
            passes.append(r["id"])
        else:
            failures.append((r["id"], r["name"], r["desc"]))

    # Switch-specific
    if is_switch:
        for r in SWITCH_RULES:
            if re.search(r["pattern"], content, re.MULTILINE | re.IGNORECASE):
                passes.append(r["id"])
            else:
                failures.append((r["id"], r["name"], r["desc"]))

    # Router-specific
    if is_router:
        for r in ROUTER_RULES:
            if re.search(r["pattern"], content, re.MULTILINE | re.IGNORECASE):
                passes.append(r["id"])
            else:
                failures.append((r["id"], r["name"], r["desc"]))

    return dev_name, filename, passes, failures

def run_linter():
    print("=" * 80)
    print("  CISCO IOS CONFIGURATION LINTER & POLICY AUDITOR")
    print("=" * 80)

    total_files = 0
    total_violations = 0

    for root, dirs, files in os.walk(CONFIGS_DIR):
        for f in files:
            if f.endswith(".txt") or f.endswith(".ios"):
                total_files += 1
                filepath = os.path.join(root, f)
                dev_name, filename, passes, failures = lint_file(filepath)
                
                status_str = "[PASS]" if not failures else "[FAIL]"
                print(f"\n{status_str} Device: {dev_name:<10} File: {filename}")
                if failures:
                    total_violations += len(failures)
                    for fid, name, desc in failures:
                        print(f"       ! {fid}: {name} - {desc}")
                else:
                    print(f"       All {len(passes)} policy checks passed.")

    print("\n" + "=" * 80)
    print(f"  LINTER AUDIT SUMMARY: {total_files} Config Files Checked | {total_violations} Violations Found")
    print("=" * 80)

    return total_violations == 0

if __name__ == "__main__":
    success = run_linter()
    sys.exit(0 if success else 1)
