#!/usr/bin/env python3
"""
================================================================================
Pytest Unit Tests for Topology Validation Engine (verification/check_topology.py)
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Proves that check_topology.py rigorously catches:
  1. Port collisions (same interface connected twice).
  2. Missing required devices.
  3. Trunk configuration mismatches (non-switch endpoint or missing Native 999).
  4. Routed /30 subnet misalignments (different subnets, wrong prefix, broadcast IP).
  5. Serial links missing DCE designation or clock rate.
  6. End devices plugged into the wrong VLAN.
================================================================================
"""

import copy
import csv
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "verification"))

from check_topology import (
    validate_topology,
    check_interface_collisions,
    check_device_presence,
    check_trunk_matching_ends,
    check_routed_links,
    check_serial_links,
    check_end_device_vlans,
    load_ip_table,
    DEFAULT_CABLING_CSV,
    DEFAULT_IP_TABLE_CSV,
    REQUIRED_INFRASTRUCTURE
)

def get_valid_links():
    """Loads baseline valid cabling.csv rows."""
    with open(DEFAULT_CABLING_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def test_valid_topology_passes():
    """Confirms that the production cabling.csv passes 100% of validation checks."""
    assert os.path.exists(DEFAULT_CABLING_CSV), "cabling.csv must exist"
    assert os.path.exists(DEFAULT_IP_TABLE_CSV), "ip_table.csv must exist"
    result = validate_topology(DEFAULT_CABLING_CSV, DEFAULT_IP_TABLE_CSV)
    assert result is True, "Production cabling table must pass all validation checks"

def test_broken_port_collision_caught():
    """Proves checker catches when a physical interface is used more than once."""
    links = get_valid_links()
    # Introduce deliberate port collision: assign SW-D1 Fa0/10 to a second conflicting link
    broken_link = copy.deepcopy(links[0])
    broken_link["Link-ID"] = "LINK-COLLISION-TEST"
    broken_link["Device A"] = "SW-D1"
    broken_link["Interface A"] = "FastEthernet0/10"  # Already used by SRV-CENTRAL
    broken_link["Cable type"] = "Copper Straight-Through"
    links.append(broken_link)

    passed, name, count, errors = check_interface_collisions(links)
    assert passed is False, "Checker failed to catch port collision"
    assert any("Port collision on SW-D1 interface FastEthernet0/10" in e for e in errors)

def test_broken_missing_device_caught():
    """Proves checker catches when a required infrastructure device is missing."""
    links = get_valid_links()
    # Deliberately remove all links referencing Core Router R2
    filtered_links = [l for l in links if l["Device A"] != "R2" and l["Device B"] != "R2"]

    passed, name, count, errors = check_device_presence(filtered_links, REQUIRED_INFRASTRUCTURE)
    assert passed is False, "Checker failed to catch missing device"
    assert any("Missing required device: R2" in e for e in errors)

def test_broken_trunk_mismatch_caught():
    """Proves checker catches non-switch trunk endpoints and missing Native VLAN 999."""
    links = get_valid_links()

    # Case A: Trunk connected to a PC workstation
    links_bad_a = copy.deepcopy(links)
    links_bad_a[6]["Device B"] = "PC-ICU-NURSE"  # Was SW-D2

    passed_a, _, _, errors_a = check_trunk_matching_ends(links_bad_a)
    assert passed_a is False, "Checker failed to catch trunk connecting non-switch"
    assert any("Trunk connects non-switch endpoints" in e for e in errors_a)

    # Case B: Trunk missing Native VLAN 999
    links_bad_b = copy.deepcopy(links)
    links_bad_b[6]["VLANs carried"] = "10 20 30 40 50 60 99"  # Missing Native: 999

    passed_b, _, _, errors_b = check_trunk_matching_ends(links_bad_b)
    assert passed_b is False, "Checker failed to catch missing Native VLAN 999"
    assert any("missing mandatory Native VLAN 999" in e for e in errors_b)

def test_broken_routed_slash_30_caught():
    """Proves checker catches invalid prefix, mismatched subnets, or broadcast IP usage."""
    links = get_valid_links()

    # Case A: Prefix is /29 instead of mandatory /30
    links_bad_a = copy.deepcopy(links)
    links_bad_a[0]["IP/subnet if routed"] = "172.16.8.80/29 (R1: 172.16.8.81 DCE / R2: 172.16.8.82 DTE)"

    passed_a, _, _, errors_a = check_routed_links(links_bad_a)
    assert passed_a is False, "Checker failed to catch non-/30 prefix"
    assert any("must be /30, got /29" in e for e in errors_a)

    # Case B: Endpoints in different subnets
    links_bad_b = copy.deepcopy(links)
    links_bad_b[0]["IP/subnet if routed"] = "172.16.8.80/30 (R1: 172.16.8.81 DCE / R2: 172.16.8.98 DTE)"

    passed_b, _, _, errors_b = check_routed_links(links_bad_b)
    assert passed_b is False, "Checker failed to catch IP in wrong subnet"
    assert any("Endpoint 172.16.8.98 is not in subnet" in e for e in errors_b)

    # Case C: Endpoint using broadcast address
    links_bad_c = copy.deepcopy(links)
    links_bad_c[0]["IP/subnet if routed"] = "172.16.8.80/30 (R1: 172.16.8.81 DCE / R2: 172.16.8.83 DTE)"

    passed_c, _, _, errors_c = check_routed_links(links_bad_c)
    assert passed_c is False, "Checker failed to catch broadcast IP usage"
    assert any("cannot use network or broadcast address" in e for e in errors_c)

def test_broken_serial_missing_dce_clock_rate_caught():
    """Proves checker catches missing DCE designation or missing clock rate on serial links."""
    links = get_valid_links()

    # Case A: Missing clock rate
    links_bad_a = copy.deepcopy(links)
    links_bad_a[0]["Cable type"] = "Serial DCE"  # Missing clock rate

    passed_a, _, _, errors_a = check_serial_links(links_bad_a)
    assert passed_a is False, "Checker failed to catch missing clock rate"
    assert any("missing explicit clock rate" in e for e in errors_a)

    # Case B: Missing DCE designation (both DTE)
    links_bad_b = copy.deepcopy(links)
    links_bad_b[0]["Cable type"] = "Serial DTE (clock rate 128000 on R1)"
    links_bad_b[0]["IP/subnet if routed"] = "172.16.8.80/30 (R1: 172.16.8.81 DTE / R2: 172.16.8.82 DTE)"

    passed_b, _, _, errors_b = check_serial_links(links_bad_b)
    assert passed_b is False, "Checker failed to catch missing DCE designation"
    assert any("missing DCE designation" in e for e in errors_b)

def test_broken_end_device_wrong_vlan_caught():
    """Proves checker catches when an end device is attached to the wrong VLAN."""
    links = get_valid_links()
    ip_map = load_ip_table(DEFAULT_IP_TABLE_CSV)

    # Misconfigure ICU Telemetry node (VLAN 10) to access VLAN 40 (Guest)
    links_bad = copy.deepcopy(links)
    for l in links_bad:
        if l["Device B"] == "SBC-ICU-101":
            l["VLANs carried"] = "40"  # Wrong VLAN!

    passed, _, _, errors = check_end_device_vlans(links_bad, ip_map)
    assert passed is False, "Checker failed to catch wrong VLAN assignment"
    assert any("Device SBC-ICU-101 expects VLAN 10, but port carries '40'" in e for e in errors)

if __name__ == "__main__":
    print("Running Topology Validation Unit Tests via Python Standard Library...")
    test_valid_topology_passes()
    print("  [PASS] test_valid_topology_passes (Production cabling verified)")
    test_broken_port_collision_caught()
    print("  [PASS] test_broken_port_collision_caught")
    test_broken_missing_device_caught()
    print("  [PASS] test_broken_missing_device_caught")
    test_broken_trunk_mismatch_caught()
    print("  [PASS] test_broken_trunk_mismatch_caught")
    test_broken_routed_slash_30_caught()
    print("  [PASS] test_broken_routed_slash_30_caught")
    test_broken_serial_missing_dce_clock_rate_caught()
    print("  [PASS] test_broken_serial_missing_dce_clock_rate_caught")
    test_broken_end_device_wrong_vlan_caught()
    print("  [PASS] test_broken_end_device_wrong_vlan_caught")
    print("\nALL 7 TOPOLOGY VALIDATOR TESTS PASSED SUCCESSFULLY!")
