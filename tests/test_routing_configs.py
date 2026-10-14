#!/usr/bin/env python3
"""
================================================================================
Dynamic Routing Configurations & Expected State Verification Suite
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Validates router and L3 switch configuration files (R1, R2, SW-D1, SW-D2, SW-D3)
and the golden expected routing state baseline (/verification/routing_expected.md).
"""

import os
import re
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIGS_DIR = os.path.join(PROJECT_ROOT, "configs")
VERIF_DIR = os.path.join(PROJECT_ROOT, "verification")

def load_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def test_router_ids_match_loopbacks():
    """Verify that OSPF router IDs match configured Loopback0 IPs on all devices."""
    expected_ids = {
        "R1": "172.16.8.104",
        "R2": "172.16.8.105",
        "SW-D1": "172.16.8.106",
        "SW-D2": "172.16.8.107",
        "SW-D3": "172.16.8.108",
    }
    for dev, expected_ip in expected_ids.items():
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        # Check Loopback0
        m_lb = re.search(r"interface\s+Loopback0[\s\S]*?ip\s+address\s+([0-9.]+)\s+255\.255\.255\.255", cfg, re.IGNORECASE)
        assert m_lb, f"Loopback0 IP missing in {dev}.cfg"
        assert m_lb.group(1) == expected_ip, f"Loopback0 IP mismatch on {dev}: {m_lb.group(1)} != {expected_ip}"
        
        # Check router-id under router ospf 1
        m_rid = re.search(r"router\s+ospf\s+1[\s\S]*?router-id\s+([0-9.]+)", cfg, re.IGNORECASE)
        assert m_rid, f"OSPF router-id missing in {dev}.cfg"
        assert m_rid.group(1) == expected_ip, f"OSPF router-id mismatch on {dev}: {m_rid.group(1)} != {expected_ip}"

    print("  [PASS] test_router_ids_match_loopbacks (R1, R2, SW-D1, SW-D2, SW-D3 verified)")

def test_passive_interface_default_policy():
    """Verify passive-interface default is enforced with explicit no passive-interface on routed links."""
    devices = {
        "R1": ["GigabitEthernet0/0", "GigabitEthernet0/1", "Serial0/0/0"],
        "R2": ["GigabitEthernet0/0", "Serial0/0/0"],
        "SW-D1": ["GigabitEthernet0/2"],
        "SW-D2": ["GigabitEthernet0/2"],
        "SW-D3": ["GigabitEthernet0/1"],
    }
    for dev, active_ports in devices.items():
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        assert re.search(r"router\s+ospf\s+1[\s\S]*?passive-interface\s+default", cfg, re.IGNORECASE), \
            f"passive-interface default missing under router ospf 1 on {dev}"
        for port in active_ports:
            pattern = rf"no\s+passive-interface\s+{re.escape(port)}"
            assert re.search(pattern, cfg, re.IGNORECASE), \
                f"Missing 'no passive-interface {port}' on {dev}"

    print("  [PASS] test_passive_interface_default_policy (passive-default + explicit no-passive verified)")

def test_point_to_point_network_types():
    """Verify that all /30 routed transit links configure 'ip ospf network point-to-point'."""
    p2p_links = {
        ("R1", "GigabitEthernet0/0"),
        ("R1", "GigabitEthernet0/1"),
        ("R1", "Serial0/0/0"),
        ("R2", "GigabitEthernet0/0"),
        ("R2", "Serial0/0/0"),
        ("SW-D1", "GigabitEthernet0/2"),
        ("SW-D2", "GigabitEthernet0/2"),
        ("SW-D3", "GigabitEthernet0/1"),
    }
    for dev, port in p2p_links:
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        pattern = rf"interface\s+{re.escape(port)}[\s\S]*?ip\s+ospf\s+network\s+point-to-point"
        assert re.search(pattern, cfg, re.IGNORECASE), \
            f"Missing 'ip ospf network point-to-point' on {dev} {port}"

    print("  [PASS] test_point_to_point_network_types (DR/BDR elimination verified on all 8 ports)")

def test_primary_secondary_wan_routing_and_ad():
    """Verify primary OSPF parameters, secondary EIGRP AD tuning (120 170), and cryptographic authentication."""
    for dev in ["R1", "R2"]:
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        # Primary WAN Se0/0/0: OSPF fast timers & MD5 auth
        assert re.search(r"interface\s+Serial0/0/0[\s\S]*?ip\s+ospf\s+hello-interval\s+1", cfg, re.IGNORECASE), \
            f"Fast hello timer 1 missing on {dev} Se0/0/0"
        assert re.search(r"interface\s+Serial0/0/0[\s\S]*?ip\s+ospf\s+dead-interval\s+4", cfg, re.IGNORECASE), \
            f"Fast dead timer 4 missing on {dev} Se0/0/0"
        assert re.search(r"interface\s+Serial0/0/0[\s\S]*?ip\s+ospf\s+authentication\s+message-digest", cfg, re.IGNORECASE), \
            f"OSPF MD5 auth missing on {dev} Se0/0/0"
        assert re.search(r"interface\s+Serial0/0/0[\s\S]*?ip\s+ospf\s+message-digest-key\s+1\s+md5\s+CiscoHospital2026", cfg, re.IGNORECASE), \
            f"OSPF MD5 key missing on {dev} Se0/0/0"
        
        # Secondary WAN Se0/0/1: EIGRP key-chain & AD tuning
        assert re.search(r"key\s+chain\s+EIGRP_AUTH[\s\S]*?key-string\s+CiscoHospital2026", cfg, re.IGNORECASE), \
            f"EIGRP key chain missing on {dev}"
        assert re.search(r"interface\s+Serial0/0/1[\s\S]*?ip\s+authentication\s+mode\s+eigrp\s+100\s+md5", cfg, re.IGNORECASE), \
            f"EIGRP MD5 mode missing on {dev} Se0/0/1"
        assert re.search(r"router\s+eigrp\s+100[\s\S]*?distance\s+eigrp\s+120\s+170", cfg, re.IGNORECASE), \
            f"AD tuning 'distance eigrp 120 170' missing on {dev}"

    print("  [PASS] test_primary_secondary_wan_routing_and_ad (OSPF fast timers, MD5 auth, and AD 120 verified)")

def test_abr_summarization_and_default_origination():
    """Verify ABR R2 route summarisation and R1 default route origination."""
    cfg_r2 = load_file(os.path.join(CONFIGS_DIR, "R2", "R2.cfg"))
    assert re.search(r"area\s+1\s+range\s+172\.16\.8\.0\s+255\.255\.255\.0", cfg_r2, re.IGNORECASE), \
        "Missing area 1 range 172.16.8.0 255.255.255.0 on ABR R2"
    assert re.search(r"area\s+1\s+range\s+172\.16\.6\.128\s+255\.255\.255\.128", cfg_r2, re.IGNORECASE), \
        "Missing area 1 range 172.16.6.128 255.255.255.128 on ABR R2"
    assert re.search(r"area\s+1\s+range\s+172\.16\.7\.224\s+255\.255\.255\.224", cfg_r2, re.IGNORECASE), \
        "Missing area 1 range 172.16.7.224 255.255.255.224 on ABR R2"
        
    cfg_r1 = load_file(os.path.join(CONFIGS_DIR, "R1", "R1.cfg"))
    assert re.search(r"router\s+ospf\s+1[\s\S]*?default-information\s+originate", cfg_r1, re.IGNORECASE), \
        "Missing default-information originate on Core Router R1"
    assert re.search(r"ip\s+route\s+0\.0\.0\.0\s+0\.0\.0\.0\s+172\.16\.8\.101", cfg_r1, re.IGNORECASE), \
        "Missing static default route to EDGE-ISP on R1"

    print("  [PASS] test_abr_summarization_and_default_origination (ABR ranges and Type-5 default verified)")

def test_floating_static_default_routes_on_switches():
    """Verify switches SW-D1, SW-D2, SW-D3 configure floating static default routes with AD 200."""
    expected_gw = {
        "SW-D1": "172.16.8.90",
        "SW-D2": "172.16.8.94",
        "SW-D3": "172.16.8.98",
    }
    for sw, gw in expected_gw.items():
        cfg = load_file(os.path.join(CONFIGS_DIR, sw, f"{sw}.cfg"))
        pattern = rf"ip\s+route\s+0\.0\.0\.0\s+0\.0\.0\.0\s+{re.escape(gw)}\s+200"
        assert re.search(pattern, cfg, re.IGNORECASE), \
            f"Missing floating static default route with AD 200 on {sw} pointing to {gw}"

    print("  [PASS] test_floating_static_default_routes_on_switches (AD 200 fallback verified on all switches)")

def test_routing_expected_document_structure():
    """Verify that /verification/routing_expected.md exists and contains all required golden states."""
    filepath = os.path.join(VERIF_DIR, "routing_expected.md")
    assert os.path.exists(filepath), "routing_expected.md missing"
    content = load_file(filepath)
    
    # Check all target devices covered
    for dev in ["R1", "R2", "SW-D1", "SW-D2", "SW-D3"]:
        assert dev in content, f"Device {dev} not covered in routing_expected.md"
        
    # Check route codes present
    for code in ["O", "O IA", "O*E2", "S*", "D"]:
        assert code in content, f"Route code {code} missing in routing_expected.md"
        
    # Check neighbor verification outputs
    assert "show ip ospf neighbor" in content, "show ip ospf neighbor missing"
    assert "show ip eigrp neighbors" in content, "show ip eigrp neighbors missing"
    
    # Check end-to-end traceroute
    assert "PC-ICU-NURSE" in content, "ICU source missing in traceroute"
    assert "SRV-CACHE" in content, "Clinic cache server destination missing in traceroute"
    assert "172.16.7.129" in content and "172.16.8.82" in content, "Expected hops missing in traceroute"
    
    # Check failure and reconvergence drill
    assert "Before vs. After Failure" in content or "Before and After Failure" in content, "Failure comparison missing"
    assert "Serial0/0/1" in content, "Failover to Serial0/0/1 missing"

    print("  [PASS] test_routing_expected_document_structure (Golden tables, diffs, traceroute verified)")

if __name__ == "__main__":
    print("Executing Dynamic Routing Configurations & Verification Test Suite...")
    test_router_ids_match_loopbacks()
    test_passive_interface_default_policy()
    test_point_to_point_network_types()
    test_primary_secondary_wan_routing_and_ad()
    test_abr_summarization_and_default_origination()
    test_floating_static_default_routes_on_switches()
    test_routing_expected_document_structure()
    print("\nALL 7 ROUTING CONFIGURATION TESTS PASSED SUCCESSFULLY!")
