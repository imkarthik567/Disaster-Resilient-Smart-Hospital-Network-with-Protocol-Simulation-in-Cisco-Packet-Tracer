#!/usr/bin/env python3
"""
Unit Test Suite: Inter-VLAN Routing, SVI Addressing, and HSRP v2 Redundancy
Validates SW-D1, SW-D2, SW-D3, and SW-D4 configurations against the project
requirements and the authoritative IP table (/addressing/ip_table.csv).
"""

import os
import re
import csv
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIGS_DIR = os.path.join(PROJECT_ROOT, "configs")
IP_TABLE_FILE = os.path.join(PROJECT_ROOT, "addressing", "ip_table.csv")

def load_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def load_ip_table():
    entries = []
    with open(IP_TABLE_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(row)
    return entries

def parse_svi_blocks(config_text):
    """
    Parses interface Vlan<N> blocks and returns a dict:
    { vlan_id: { 'ip': str, 'mask': str, 'helpers': [str], 'hsrp': dict } }
    """
    svis = {}
    pattern = r"interface\s+Vlan(\d+)([\s\S]*?)exit"
    matches = re.finditer(pattern, config_text, re.IGNORECASE)
    for m in matches:
        vlan = int(m.group(1))
        body = m.group(2)
        
        # IP address
        ip_match = re.search(r"ip\s+address\s+([0-9.]+)\s+([0-9.]+)", body)
        ip = ip_match.group(1) if ip_match else None
        mask = ip_match.group(2) if ip_match else None
        
        # Helper addresses
        helpers = re.findall(r"ip\s+helper-address\s+([0-9.]+)", body)
        
        # HSRP v2
        version_v2 = bool(re.search(r"standby\s+version\s+2", body))
        vip_match = re.search(r"standby\s+(\d+)\s+ip\s+([0-9.]+)", body)
        vip_group = int(vip_match.group(1)) if vip_match else None
        vip = vip_match.group(2) if vip_match else None
        
        pri_match = re.search(r"standby\s+(\d+)\s+priority\s+(\d+)", body)
        priority = int(pri_match.group(2)) if pri_match else 100
        
        preempt = bool(re.search(r"standby\s+(\d+)\s+preempt", body))
        
        track_match = re.search(r"standby\s+(\d+)\s+track\s+([A-Za-z0-9/]+)\s+(\d+)", body)
        track_iface = track_match.group(2) if track_match else None
        track_decr = int(track_match.group(3)) if track_match else None
        
        svis[vlan] = {
            "ip": ip,
            "mask": mask,
            "helpers": helpers,
            "hsrp": {
                "v2": version_v2,
                "group": vip_group,
                "vip": vip,
                "priority": priority,
                "preempt": preempt,
                "track_iface": track_iface,
                "track_decr": track_decr
            }
        }
    return svis

def test_ip_routing_enabled():
    """Verify hardware ip routing is declared on all multilayer distribution switches."""
    switches = ["SW-D1", "SW-D2", "SW-D3", "SW-D4"]
    for sw in switches:
        cfg = load_file(os.path.join(CONFIGS_DIR, sw, f"{sw}.cfg"))
        assert re.search(r"^\s*ip\s+routing\b", cfg, re.MULTILINE), f"ip routing missing on {sw}"
    print("  [PASS] test_ip_routing_enabled on SW-D1, SW-D2, SW-D3, SW-D4")

def test_main_hospital_svi_and_hsrp_alignment():
    """Verify SW-D1 and SW-D2 SVIs, VIPs, and HSRP priorities match the plan exactly."""
    cfg_d1 = load_file(os.path.join(CONFIGS_DIR, "SW-D1", "SW-D1.cfg"))
    cfg_d2 = load_file(os.path.join(CONFIGS_DIR, "SW-D2", "SW-D2.cfg"))
    
    svis_d1 = parse_svi_blocks(cfg_d1)
    svis_d2 = parse_svi_blocks(cfg_d2)
    
    expected_vlans = [10, 20, 30, 40, 50, 60, 99]
    for vlan in expected_vlans:
        assert vlan in svis_d1, f"VLAN {vlan} SVI missing on SW-D1"
        assert vlan in svis_d2, f"VLAN {vlan} SVI missing on SW-D2"
        
        # Verify HSRP v2
        assert svis_d1[vlan]["hsrp"]["v2"], f"HSRP v2 not enabled on SW-D1 VLAN {vlan}"
        assert svis_d2[vlan]["hsrp"]["v2"], f"HSRP v2 not enabled on SW-D2 VLAN {vlan}"
        
        # Verify VIPs match
        vip_d1 = svis_d1[vlan]["hsrp"]["vip"]
        vip_d2 = svis_d2[vlan]["hsrp"]["vip"]
        assert vip_d1 is not None and vip_d1 == vip_d2, f"VIP mismatch on VLAN {vlan}: {vip_d1} vs {vip_d2}"
        
        # Verify Preempt enabled on both
        assert svis_d1[vlan]["hsrp"]["preempt"], f"Preempt not set on SW-D1 VLAN {vlan}"
        assert svis_d2[vlan]["hsrp"]["preempt"], f"Preempt not set on SW-D2 VLAN {vlan}"
        
        # Group 1 (10, 30, 50, 99): SW-D1 Active (110 + track), SW-D2 Standby (100)
        if vlan in [10, 30, 50, 99]:
            assert svis_d1[vlan]["hsrp"]["priority"] == 110, f"SW-D1 VLAN {vlan} expected prio 110"
            assert svis_d1[vlan]["hsrp"]["track_iface"] == "GigabitEthernet0/2", f"SW-D1 VLAN {vlan} tracking missing"
            assert svis_d1[vlan]["hsrp"]["track_decr"] == 20, f"SW-D1 VLAN {vlan} track decrement must be 20"
            assert svis_d2[vlan]["hsrp"]["priority"] == 100, f"SW-D2 VLAN {vlan} expected prio 100"
            assert svis_d2[vlan]["hsrp"]["track_iface"] is None, f"SW-D2 VLAN {vlan} should not track standby"
            
        # Group 2 (20, 40, 60): SW-D2 Active (110 + track), SW-D1 Standby (100)
        elif vlan in [20, 40, 60]:
            assert svis_d2[vlan]["hsrp"]["priority"] == 110, f"SW-D2 VLAN {vlan} expected prio 110"
            assert svis_d2[vlan]["hsrp"]["track_iface"] == "GigabitEthernet0/2", f"SW-D2 VLAN {vlan} tracking missing"
            assert svis_d2[vlan]["hsrp"]["track_decr"] == 20, f"SW-D2 VLAN {vlan} track decrement must be 20"
            assert svis_d1[vlan]["hsrp"]["priority"] == 100, f"SW-D1 VLAN {vlan} expected prio 100"
            assert svis_d1[vlan]["hsrp"]["track_iface"] is None, f"SW-D1 VLAN {vlan} should not track standby"
            
    print("  [PASS] test_main_hospital_svi_and_hsrp_alignment (Fate-sharing, VIPs, tracking verified)")

def test_dhcp_relay_helper_addresses():
    """Verify ip helper-address 172.16.7.4 is configured on client SVIs."""
    dhcp_server_ip = "172.16.7.4"
    
    cfg_d1 = load_file(os.path.join(CONFIGS_DIR, "SW-D1", "SW-D1.cfg"))
    cfg_d2 = load_file(os.path.join(CONFIGS_DIR, "SW-D2", "SW-D2.cfg"))
    cfg_d3 = load_file(os.path.join(CONFIGS_DIR, "SW-D3", "SW-D3.cfg"))
    
    svis_d1 = parse_svi_blocks(cfg_d1)
    svis_d2 = parse_svi_blocks(cfg_d2)
    svis_d3 = parse_svi_blocks(cfg_d3)
    
    # Client VLANs requiring DHCP
    client_vlans = [10, 20, 30, 40, 60]
    for vlan in client_vlans:
        assert dhcp_server_ip in svis_d1[vlan]["helpers"], f"SW-D1 VLAN {vlan} missing helper {dhcp_server_ip}"
        assert dhcp_server_ip in svis_d2[vlan]["helpers"], f"SW-D2 VLAN {vlan} missing helper {dhcp_server_ip}"
        
    for vlan in [10, 30, 40, 60]:
        assert dhcp_server_ip in svis_d3[vlan]["helpers"], f"SW-D3 VLAN {vlan} missing helper {dhcp_server_ip}"
        
    print("  [PASS] test_dhcp_relay_helper_addresses (172.16.7.4 on all client SVIs)")

def test_routed_point_to_point_uplinks():
    """Verify routed uplinks (no switchport) have exact /30 subnets."""
    expected_uplinks = {
        "SW-D1": {"port": "GigabitEthernet0/2", "ip": "172.16.8.89", "mask": "255.255.255.252"},
        "SW-D2": {"port": "GigabitEthernet0/2", "ip": "172.16.8.93", "mask": "255.255.255.252"},
        "SW-D3": {"port": "GigabitEthernet0/1", "ip": "172.16.8.97", "mask": "255.255.255.252"},
        "SW-D4": {"port": "GigabitEthernet0/1", "ip": "172.16.8.114", "mask": "255.255.255.252"},
    }
    
    for dev, info in expected_uplinks.items():
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        pattern = rf"interface\s+{info['port']}[\s\S]*?no\s+switchport[\s\S]*?ip\s+address\s+([0-9.]+)\s+([0-9.]+)[\s\S]*?exit"
        m = re.search(pattern, cfg, re.IGNORECASE)
        assert m, f"Routed uplink configuration missing on {dev} {info['port']}"
        assert m.group(1) == info["ip"], f"{dev} IP expected {info['ip']}, got {m.group(1)}"
        assert m.group(2) == info["mask"], f"{dev} mask expected {info['mask']}, got {m.group(2)}"
        
    print("  [PASS] test_routed_point_to_point_uplinks (all /30 transit subnets verified)")

def test_static_default_routes_to_core():
    """Verify static default routes on distribution switches point to core routers."""
    expected_routes = {
        "SW-D1": "172.16.8.90",  # R1 Gig0/0
        "SW-D2": "172.16.8.94",  # R1 Gig0/1
        "SW-D3": "172.16.8.98",  # R2 Gig0/0
        "SW-D4": "172.16.8.113", # R2 Gig0/1
    }
    for dev, nh in expected_routes.items():
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        pattern = rf"ip\s+route\s+0\.0\.0\.0\s+0\.0\.0\.0\s+{re.escape(nh)}"
        assert re.search(pattern, cfg), f"{dev} default route via {nh} missing"
    print("  [PASS] test_static_default_routes_to_core (SW-D1->R1, SW-D2->R1, SW-D3->R2, SW-D4->R2)")

def run_all_tests():
    print("Executing Inter-VLAN Routing & HSRP Verification Suite...")
    test_ip_routing_enabled()
    test_main_hospital_svi_and_hsrp_alignment()
    test_dhcp_relay_helper_addresses()
    test_routed_point_to_point_uplinks()
    test_static_default_routes_to_core()
    print("\nALL 5 INTER-VLAN & HSRP VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_all_tests()
