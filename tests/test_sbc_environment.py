#!/usr/bin/env python3
"""
Unit Test Suite: SBC Environment & Diagnostic Probe Verification
Validates sbc/ENVIRONMENT.md against project requirements, Packet Tracer 8.x
IoT simulation runtime specifications, and tests sbc/probe.py execution.
"""

import os
import subprocess
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

ENV_DOC_PATH = os.path.join(PROJECT_ROOT, "sbc", "ENVIRONMENT.md")
PROBE_SCRIPT_PATH = os.path.join(PROJECT_ROOT, "sbc", "probe.py")

def test_environment_doc_structure():
    """Verify sbc/ENVIRONMENT.md exists and contains all required structural sections."""
    assert os.path.isfile(ENV_DOC_PATH), f"Missing environment doc: {ENV_DOC_PATH}"
    with open(ENV_DOC_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert len(content) > 10000, f"ENVIRONMENT.md is too brief ({len(content)} bytes)"

    required_sections = [
        "## 1. Executive Overview & Runtime Architecture",
        "## 2. Script Lifecycle, Naming, Execution & Console Output",
        "## 3. Available Packet Tracer Built-in Modules",
        "## 4. Standard Library Limitations: Confirmed vs. Uncertain",
        "## 5. Master Feature Matrix: Confirmed, Uncertain & Test Protocol",
        "## 6. Architectural Blueprint for All Later SBC Code",
        "## 7. How to Run `probe.py` in Cisco Packet Tracer"
    ]

    for sec in required_sections:
        assert sec in content, f"Missing required section in ENVIRONMENT.md: {sec}"

    print("  [PASS] test_environment_doc_structure (All 7 required sections present)")

def test_hardware_modules_and_pins():
    """Verify hardware modules, pin mappings, and single-threaded loop constraints are documented."""
    with open(ENV_DOC_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Hardware modules
    assert "gpio" in content
    assert "pinMode" in content and "digitalRead" in content and "analogRead" in content
    assert "digitalWrite" in content and "analogWrite" in content
    assert "IoEClient" in content

    # Sensor & actuator pins
    assert "D0" in content and "Emergency" in content
    assert "D1" in content and "Alarm" in content or "Siren" in content
    assert "A0" in content and ("ECG" in content or "Heart Rate" in content)
    assert "A1" in content and ("SpO2" in content or "Oximeter" in content)

    # Cooperative yielding & GUI freeze warning
    assert "single-threaded" in content.lower() or "single-threaded" in content
    assert "sleep" in content and ("freeze" in content.lower() or "lockup" in content.lower())

    print("  [PASS] test_hardware_modules_and_pins (GPIO, pin map, and cooperative scheduling verified)")

def test_feature_matrix_and_three_tier_architecture():
    """Verify Master Feature Matrix and Three-Tier Architecture are documented."""
    with open(ENV_DOC_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Master Feature Matrix
    assert "MASTER FEATURE STATUS MATRIX" in content or "Master Feature Status Matrix" in content
    assert "CONFIRMED" in content
    assert "UNCERTAIN" in content
    assert "CONFIRMED ABSENT" in content or "UNAVAILABLE" in content

    # Three-Tier Architecture
    assert "THREE-TIER SBC CODE ARCHITECTURE" in content or "Three-Tier" in content
    assert "TIER 1" in content and "CORE" in content
    assert "TIER 2" in content and "ADAPTER" in content
    assert "TIER 3" in content and "HARNESS" in content
    assert "parity_2d" in content
    assert "checksum" in content
    assert "go_back_n" in content
    assert "selective_rep" in content

    print("  [PASS] test_feature_matrix_and_three_tier_architecture (Feature matrix & 3-tier blueprint verified)")

def test_probe_script_syntax_and_execution():
    """Verify sbc/probe.py exists, compiles, and executes cleanly on host PC."""
    assert os.path.isfile(PROBE_SCRIPT_PATH), f"Missing probe script: {PROBE_SCRIPT_PATH}"

    # Import and run probe_environment()
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "sbc"))
    import probe

    res = probe.probe_environment()
    assert isinstance(res, dict)
    assert "available_std" in res
    assert "missing_std" in res
    assert "available_pt" in res
    assert "bitwise_ok" in res
    assert res["bitwise_ok"] is True
    assert "BEGIN PACKET TRACER" in res["raw_report"]
    assert "END PACKET TRACER" in res["raw_report"]

    print("  [PASS] test_probe_script_syntax_and_execution (probe.py ran successfully with valid report)")

def test_probe_subprocess_run():
    """Verify sbc/probe.py runs as a standalone CLI script with exit code 0."""
    result = subprocess.run([sys.executable, PROBE_SCRIPT_PATH], capture_output=True, text=True)
    assert result.returncode == 0, f"probe.py failed with returncode {result.returncode}: {result.stderr}"
    assert "BEGIN PACKET TRACER SBC-PT ENVIRONMENT PROBE REPORT" in result.stdout
    assert "END PACKET TRACER SBC-PT ENVIRONMENT PROBE REPORT" in result.stdout
    assert "[1] SYSTEM & RUNTIME INTROSPECTION" in result.stdout
    assert "[2] STANDARD PYTHON LIBRARY MODULE AVAILABILITY" in result.stdout
    assert "[3] PACKET TRACER EMBEDDED HARDWARE & IOT MODULES" in result.stdout
    assert "[4] FUNCTIONAL PRIMITIVES & OPERATIONAL CHECKS" in result.stdout
    assert "[5] ENVIRONMENT SUMMARY & ARCHITECTURAL VERDICT" in result.stdout

    print("  [PASS] test_probe_subprocess_run (probe.py completed as standalone CLI process)")

def test_sbc_core_pure_python_compliance():
    """Verify existing SBC core algorithms do not import banned modules."""
    sbc_dir = os.path.join(PROJECT_ROOT, "sbc")
    core_scripts = ["parity_2d.py", "checksum.py", "go_back_n.py", "selective_repeat.py"]
    banned_modules = ["struct", "binascii", "zlib", "threading", "numpy", "scipy", "pandas"]

    for script in core_scripts:
        spath = os.path.join(sbc_dir, script)
        if not os.path.isfile(spath):
            continue
        with open(spath, "r", encoding="utf-8") as f:
            code = f.read()
        for banned in banned_modules:
            assert f"import {banned}" not in code, f"{script} illegally imports banned module '{banned}'"
            assert f"from {banned}" not in code, f"{script} illegally imports from banned module '{banned}'"

    print("  [PASS] test_sbc_core_pure_python_compliance (Zero banned imports in SBC core scripts)")

def run_all_tests():
    print("=" * 70)
    print("  RUNNING SBC ENVIRONMENT & PROBE TEST SUITE")
    print("=" * 70)
    test_environment_doc_structure()
    test_hardware_modules_and_pins()
    test_feature_matrix_and_three_tier_architecture()
    test_probe_script_syntax_and_execution()
    test_probe_subprocess_run()
    test_sbc_core_pure_python_compliance()
    print("=" * 70)
    print("  ALL 6 SBC ENVIRONMENT & PROBE TESTS PASSED")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
