#!/usr/bin/env python3
"""
Unit Test Suite: Master Verification Test Matrix
Validates verification/test_matrix.csv and verification/test_matrix.md
against project specifications, 10-column schema, 20 mandatory topic areas,
and negative testing requirements.
"""

import os
import sys
import csv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

CSV_PATH = os.path.join(PROJECT_ROOT, "verification", "test_matrix.csv")
MD_PATH = os.path.join(PROJECT_ROOT, "verification", "test_matrix.md")
GEN_SCRIPT = os.path.join(PROJECT_ROOT, "verification", "generate_test_matrix.py")

EXPECTED_HEADERS = [
    "Test-ID",
    "Requirement-ID",
    "Objective",
    "Preconditions",
    "Exact steps (with devices and commands)",
    "Expected result",
    "Where to look (show command or Simulation Mode filter)",
    "Evidence filename",
    "Pass/Fail",
    "Notes"
]


def test_files_exist_and_non_empty():
    """Verify test_matrix.csv, test_matrix.md, and generator script exist and are non-empty."""
    assert os.path.isfile(GEN_SCRIPT), f"Missing generator script: {GEN_SCRIPT}"
    assert os.path.isfile(CSV_PATH), f"Missing CSV matrix: {CSV_PATH}"
    assert os.path.isfile(MD_PATH), f"Missing Markdown matrix: {MD_PATH}"

    assert os.path.getsize(CSV_PATH) > 10_000, "test_matrix.csv is unexpectedly small"
    assert os.path.getsize(MD_PATH) > 15_000, "test_matrix.md is unexpectedly small"
    print("  [PASS] test_files_exist_and_non_empty (CSV and MD files present & populated)")


def test_csv_schema_and_row_count():
    """Verify CSV header has exactly the 10 required columns and contains at least 50 test rows."""
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    assert header == EXPECTED_HEADERS, f"Header mismatch:\nGot: {header}\nExpected: {EXPECTED_HEADERS}"
    assert len(rows) >= 50, f"Expected at least 50 tests, found {len(rows)}"

    for idx, r in enumerate(rows, start=1):
        assert len(r) == 10, f"Row {idx} does not have 10 columns: {r[0] if r else 'empty'}"
        assert r[0].startswith("TC-"), f"Row {idx} Test-ID invalid: {r[0]}"
        assert r[1], f"Row {idx} missing Requirement-ID"
        assert r[7].startswith("evidence/"), f"Row {idx} invalid evidence path: {r[7]}"
        assert r[8] in ["Pass", "Fail", "Pending"], f"Row {idx} invalid Pass/Fail: {r[8]}"

    print(f"  [PASS] test_csv_schema_and_row_count (10 columns, {len(rows)} verified test rows)")


def test_all_20_mandatory_topics_covered():
    """Verify all 20 required topics are covered in the test matrix."""
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tests = list(reader)

    all_text = " ".join([
        f"{t['Test-ID']} {t['Requirement-ID']} {t['Objective']} {t['Exact steps (with devices and commands)']} {t['Expected result']} {t['Where to look (show command or Simulation Mode filter)']} {t['Notes']}"
        for t in tests
    ]).lower()

    required_topics = {
        "addressing and reachability by VLAN": ["vlan 10", "vlan 20", "vlan 30", "172.16.3.129"],
        "inter-VLAN routing": ["inter-vlan", "wire speed", "gi0/1"],
        "STP root election and failover": ["spanning-tree root", "root bridge", "failover"],
        "HSRP failover": ["hsrp", "standby brief", "active", "preemption"],
        "trunk and VLAN pruning": ["trunk", "802.1q", "allowed vlan", "native vlan 999"],
        "port security violation": ["port-security", "violation", "restrict"],
        "DHCP for each VLAN including the clinic": ["dhcp", "ip helper-address", "clinic"],
        "DNS for each hostname": ["dns", "records.hospital.local", "nslookup"],
        "HTTP": ["http", "records.hospital.local", "ehr"],
        "OSPF adjacency and routes": ["ospf", "show ip ospf neighbor", "area 0"],
        "EIGRP adjacency": ["eigrp", "show ip eigrp neighbors", "as 100"],
        "summarisation": ["summarization", "172.16.4.64/26", "area 1 range"],
        "ACL permit and deny cases with counters": ["block-guest", "permit", "deny", "counter"],
        "NAT": ["nat", "overload", "translations", "203.0.113.2"],
        "QoS counters": ["policy-map", "class-map", "dscp ef", "vitals-voice"],
        "SBC error detection cases": ["2d parity", "checksum", "crc-16"],
        "GBN and SR transfer": ["go-back-n", "selective repeat", "sliding window"],
        "WAN failover": ["primary wan", "serial0/0/0", "failover"],
        "WAN restoration and preemption": ["restoration", "preemption", "no shutdown"],
        "combined disaster scenario": ["combined disaster", "compound", "concurrent"]
    }

    for topic, keywords in required_topics.items():
        found = any(k in all_text for k in keywords)
        assert found, f"Topic '{topic}' not adequately covered in test matrix! Searched for {keywords}"

    print("  [PASS] test_all_20_mandatory_topics_covered (All 20 minimum required areas validated)")


def test_negative_testing_explicitly_flagged():
    """Verify negative testing cases exist and are explicitly flagged."""
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tests = list(reader)

    negative_tests = [t for t in tests if "[NEGATIVE TEST]" in t["Objective"] or "negative" in t["Notes"].lower()]
    assert len(negative_tests) >= 5, f"Expected at least 5 negative tests, found {len(negative_tests)}"

    neg_ids = [t["Test-ID"] for t in negative_tests]
    # Must cover port security, ACL drops, parity blind spot, corrupted checksum
    assert "TC-SEC-02" in neg_ids, "Missing port security rogue negative test"
    assert "TC-SEC-03" in neg_ids, "Missing guest to ICU ACL negative test"
    assert "TC-SBC-02" in neg_ids, "Missing 2D parity rectangular blind spot negative test"
    assert "TC-SBC-04" in neg_ids, "Missing corrupted checksum packet drop negative test"

    print(f"  [PASS] test_negative_testing_explicitly_flagged ({len(negative_tests)} negative tests validated)")


def test_markdown_formatting_and_stages():
    """Verify Markdown file has valid mermaid diagram, 8 stages, and links."""
    with open(MD_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "```mermaid" in content, "Missing mermaid diagram in test_matrix.md"
    assert "Stage 1: Physical & Layer 2 Baseline" in content
    assert "Stage 2: Addressing, Inter-VLAN & HSRP" in content
    assert "Stage 3: Infrastructure Services" in content
    assert "Stage 4: Dynamic Routing" in content
    assert "Stage 5: Security & Perimeter Policies" in content
    assert "Stage 6: Quality of Service (QoS)" in content
    assert "Stage 7: SBC Clinical Protocols" in content
    assert "Stage 8: WAN Resilience & Disaster Recovery" in content
    assert "## 3. Negative Testing Summary" in content

    print("  [PASS] test_markdown_formatting_and_stages (8 stages & mermaid flowchart verified)")


def main():
    print("=" * 70)
    print("RUNNING MASTER TEST MATRIX VERIFICATION SUITE")
    print("=" * 70)

    test_files_exist_and_non_empty()
    test_csv_schema_and_row_count()
    test_all_20_mandatory_topics_covered()
    test_negative_testing_explicitly_flagged()
    test_markdown_formatting_and_stages()

    print("=" * 70)
    print("ALL MASTER TEST MATRIX TESTS PASSED (5/5)")
    print("=" * 70)
    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
