#!/usr/bin/env python3
"""
================================================================================
Test Suite: Cisco IOS Route Checker & Differential Verification Tool
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Validates route parsing, protocol normalization, diff categorization
(missing, unexpected, wrong-next-hop, wrong-protocol), and sample test files.
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from verification.route_checker import (
    Route,
    normalize_interface,
    parse_show_ip_route,
    load_expected_routes_yaml,
    compare_routes
)

SAMPLES_DIR = os.path.join(PROJECT_ROOT, "verification", "samples")
YAML_PATH = os.path.join(PROJECT_ROOT, "verification", "expected_routes.yaml")


def load_sample(filename):
    with open(os.path.join(SAMPLES_DIR, filename), "r", encoding="utf-8") as f:
        return f.read()


def test_interface_normalization():
    """Verify interface normalization converts full Cisco names to standard shorthand."""
    assert normalize_interface("GigabitEthernet0/1") == "Gi0/1"
    assert normalize_interface("Gig0/2") == "Gi0/2"
    assert normalize_interface("Serial0/0/0") == "Se0/0/0"
    assert normalize_interface("Se0/0/1") == "Se0/0/1"
    assert normalize_interface("FastEthernet0/24") == "Fa0/24"
    assert normalize_interface("Port-channel1") == "Po1"
    assert normalize_interface("Vlan10") == "Vl10"
    assert normalize_interface("Loopback0") == "Lo0"
    assert normalize_interface("") == ""
    print("  [PASS] test_interface_normalization")


def test_parse_show_ip_route_protocols():
    """Verify parsing of all required route codes: O, O IA, O*E2, D, D EX, C, L, S* and ECMP."""
    sample_text = """
R1# show ip route
Gateway of last resort is 172.16.8.101 to network 0.0.0.0

S*   0.0.0.0/0 [1/0] via 172.16.8.101, GigabitEthernet0/2
O*E2 0.0.0.0/0 [110/20] via 172.16.8.81, Serial0/0/0
O    172.16.0.0/22 [110/2] via 172.16.8.93, GigabitEthernet0/1
                   [110/2] via 172.16.8.89, GigabitEthernet0/0
O IA 172.16.6.128/25 [110/49] via 172.16.8.82, Serial0/0/0
D    172.16.8.0/24 [120/2172416] via 172.16.8.86, Serial0/0/1
D EX 10.0.0.0/24 [170/2172416] via 172.16.8.86, Serial0/0/1
C    172.16.8.80/30 is directly connected, Serial0/0/0
L    172.16.8.81/32 is directly connected, Serial0/0/0
"""
    detected_dev, routes = parse_show_ip_route(sample_text)
    assert detected_dev == "R1", f"Device auto-detect failed: {detected_dev}"

    # Check ECMP
    r_guest = routes["172.16.0.0/22"]
    assert r_guest.protocol == "O"
    assert len(r_guest.nexthops) == 2
    assert "172.16.8.93" in r_guest.get_nexthop_ips()
    assert "172.16.8.89" in r_guest.get_nexthop_ips()

    # Check O IA
    r_oia = routes["172.16.6.128/25"]
    assert r_oia.protocol == "O IA"
    assert "172.16.8.82" in r_oia.get_nexthop_ips()

    # Check D & D EX
    r_d = routes["172.16.8.0/24"]
    assert r_d.protocol == "D"
    assert r_d.ad == 120

    r_dex = routes["10.0.0.0/24"]
    assert r_dex.protocol == "D EX"
    assert r_dex.ad == 170

    # Check Connected and Local
    r_c = routes["172.16.8.80/30"]
    assert r_c.protocol == "C"

    r_l = routes["172.16.8.81/32"]
    assert r_l.protocol == "L"

    print("  [PASS] test_parse_show_ip_route_protocols (O, O IA, O*E2, D, D EX, C, L, S* verified)")


def test_golden_sample_r1_normal_passes():
    """Verify that sample_r1_normal.txt passes 100% against R1 expected YAML."""
    raw_text = load_sample("sample_r1_normal.txt")
    dev, routes = parse_show_ip_route(raw_text)
    assert dev == "R1"

    yaml_data = load_expected_routes_yaml(YAML_PATH)
    results = compare_routes(routes, yaml_data["R1"]["routes"])

    assert len(results["missing"]) == 0, f"Unexpected missing: {results['missing']}"
    assert len(results["wrong_protocol"]) == 0, f"Unexpected wrong proto: {results['wrong_protocol']}"
    assert len(results["wrong_nexthop"]) == 0, f"Unexpected wrong NH: {results['wrong_nexthop']}"
    assert len(results["unexpected"]) == 0, f"Unexpected routes: {results['unexpected']}"
    assert len(results["matches"]) == 22, f"Expected 22 matches, got {len(results['matches'])}"

    print("  [PASS] test_golden_sample_r1_normal_passes (22/22 matches, 0 defects)")


def test_golden_sample_r1_failover_passes():
    """Verify that sample_r1_failover.txt passes 100% against R1_failover expected YAML."""
    raw_text = load_sample("sample_r1_failover.txt")
    dev, routes = parse_show_ip_route(raw_text)

    yaml_data = load_expected_routes_yaml(YAML_PATH)
    results = compare_routes(routes, yaml_data["R1_failover"]["routes"])

    assert len(results["missing"]) == 0
    assert len(results["wrong_protocol"]) == 0
    assert len(results["wrong_nexthop"]) == 0
    assert len(results["unexpected"]) == 0
    assert len(results["matches"]) == 20

    print("  [PASS] test_golden_sample_r1_failover_passes (20/20 matches, EIGRP failover verified)")


def test_golden_samples_r2_swd1_swd3_pass():
    """Verify that R2, SW-D1, and SW-D3 golden sample files pass 100%."""
    yaml_data = load_expected_routes_yaml(YAML_PATH)

    # R2
    _, routes_r2 = parse_show_ip_route(load_sample("sample_r2_normal.txt"))
    res_r2 = compare_routes(routes_r2, yaml_data["R2"]["routes"])
    assert len(res_r2["missing"]) == 0 and len(res_r2["unexpected"]) == 0
    assert len(res_r2["matches"]) == 20

    # SW-D1
    _, routes_d1 = parse_show_ip_route(load_sample("sample_sw_d1_normal.txt"))
    res_d1 = compare_routes(routes_d1, yaml_data["SW-D1"]["routes"])
    assert len(res_d1["missing"]) == 0 and len(res_d1["unexpected"]) == 0
    assert len(res_d1["matches"]) == 22

    # SW-D3
    _, routes_d3 = parse_show_ip_route(load_sample("sample_sw_d3_normal.txt"))
    res_d3 = compare_routes(routes_d3, yaml_data["SW-D3"]["routes"])
    assert len(res_d3["missing"]) == 0 and len(res_d3["unexpected"]) == 0
    assert len(res_d3["matches"]) == 21

    print("  [PASS] test_golden_samples_r2_swd1_swd3_pass (R2, SW-D1, SW-D3 verified)")


def test_route_checker_catches_all_four_defect_types():
    """Verify that sample_r1_defects.txt triggers exactly 1 missing, 1 wrong-proto, 1 wrong-NH, 1 unexpected."""
    raw_text = load_sample("sample_r1_defects.txt")
    dev, routes = parse_show_ip_route(raw_text)

    yaml_data = load_expected_routes_yaml(YAML_PATH)
    results = compare_routes(routes, yaml_data["R1"]["routes"])

    # 1. Missing route: 172.16.7.224/27
    assert len(results["missing"]) == 1, f"Expected 1 missing, got {len(results['missing'])}"
    assert results["missing"][0]["network"] == "172.16.7.224/27"

    # 2. Wrong protocol: 172.16.8.0/24 (D instead of O IA)
    assert len(results["wrong_protocol"]) == 1, f"Expected 1 wrong proto, got {len(results['wrong_protocol'])}"
    assert results["wrong_protocol"][0]["network"] == "172.16.8.0/24"
    assert results["wrong_protocol"][0]["actual_protocol"] == "D"
    assert results["wrong_protocol"][0]["expected_protocol"] == "O IA"

    # 3. Wrong next-hop: 172.16.6.128/25 (172.16.8.99 instead of 172.16.8.82)
    assert len(results["wrong_nexthop"]) == 1, f"Expected 1 wrong NH, got {len(results['wrong_nexthop'])}"
    assert results["wrong_nexthop"][0]["network"] == "172.16.6.128/25"
    assert "172.16.8.99" in results["wrong_nexthop"][0]["actual_nexthop"]

    # 4. Unexpected route: 192.168.99.0/24
    assert len(results["unexpected"]) == 1, f"Expected 1 unexpected, got {len(results['unexpected'])}"
    assert results["unexpected"][0]["network"] == "192.168.99.0/24"

    print("  [PASS] test_route_checker_catches_all_four_defect_types (Missing, Wrong Proto, Wrong NH, Unexpected detected)")


if __name__ == "__main__":
    print("Executing Route Checker Tool Test Suite...")
    test_interface_normalization()
    test_parse_show_ip_route_protocols()
    test_golden_sample_r1_normal_passes()
    test_golden_sample_r1_failover_passes()
    test_golden_samples_r2_swd1_swd3_pass()
    test_route_checker_catches_all_four_defect_types()
    print("\nALL 6 ROUTE CHECKER TESTS PASSED SUCCESSFULLY!")
