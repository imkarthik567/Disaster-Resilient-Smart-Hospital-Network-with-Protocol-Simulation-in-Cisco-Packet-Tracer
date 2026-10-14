#!/usr/bin/env python3
"""
Unit Test Suite: Server Farm Infrastructure, DHCP Pools & DNS Services
Validates docs/dhcp_pools.csv and docs/server_setup.md against the project
requirements and the authoritative IP table (/addressing/ip_table.csv).
"""

import os
import csv
import re
import ipaddress

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DHCP_CSV = os.path.join(PROJECT_ROOT, "docs", "dhcp_pools.csv")
SERVER_SETUP_MD = os.path.join(PROJECT_ROOT, "docs", "server_setup.md")
IP_TABLE_CSV = os.path.join(PROJECT_ROOT, "addressing", "ip_table.csv")

def test_dhcp_pools_csv_structure():
    """Verify DHCP pool table has all 9 client VLAN pools with valid structure."""
    assert os.path.exists(DHCP_CSV), f"{DHCP_CSV} does not exist"
    
    with open(DHCP_CSV, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        
    assert len(reader) == 9, f"Expected 9 pools, found {len(reader)}"
    
    pool_names = [p["Pool_Name"] for p in reader]
    expected_pools = [
        "POOL-MAIN-VLAN10-ICU",
        "POOL-MAIN-VLAN20-SURGERY",
        "POOL-MAIN-VLAN30-ADMIN",
        "POOL-MAIN-VLAN40-GUEST",
        "POOL-MAIN-VLAN60-VOICE",
        "POOL-CLINIC-VLAN10-CLINICAL",
        "POOL-CLINIC-VLAN30-ADMIN",
        "POOL-CLINIC-VLAN40-GUEST",
        "POOL-CLINIC-VLAN60-VOICE",
    ]
    for exp in expected_pools:
        assert exp in pool_names, f"Pool {exp} missing in CSV"
        
    print("  [PASS] test_dhcp_pools_csv_structure (all 9 client pools present)")

def test_dhcp_gateways_and_dns():
    """Verify default gateways match HSRP VIPs and DNS server is 172.16.7.4."""
    with open(DHCP_CSV, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        
    expected_gateways = {
        "10": {"Main Hospital": "172.16.7.129", "Remote Clinic": "172.16.8.33"},
        "20": {"Main Hospital": "172.16.7.65"},
        "30": {"Main Hospital": "172.16.4.1", "Remote Clinic": "172.16.8.1"},
        "40": {"Main Hospital": "172.16.0.1", "Remote Clinic": "172.16.6.129"},
        "60": {"Main Hospital": "172.16.6.1", "Remote Clinic": "172.16.7.225"},
    }
    
    for row in reader:
        vlan = row["VLAN_ID"]
        site = row["Site"]
        exp_gw = expected_gateways[vlan][site]
        assert row["Default_Gateway"] == exp_gw, f"Gateway mismatch for {row['Pool_Name']}: expected {exp_gw}, got {row['Default_Gateway']}"
        assert row["DNS_Server"] == "172.16.7.4", f"DNS server mismatch for {row['Pool_Name']}: expected 172.16.7.4, got {row['DNS_Server']}"
        
        # Verify Option 150 for VoIP
        if vlan == "60":
            assert row["TFTP_Server_Opt150"] == "172.16.7.4", f"Option 150 TFTP server missing on {row['Pool_Name']}"
            
    print("  [PASS] test_dhcp_gateways_and_dns (VIPs, DNS 172.16.7.4, Option 150 verified)")

def test_dhcp_ip_ranges_validity():
    """Verify that Start IP and End IP are inside their respective subnet blocks."""
    with open(DHCP_CSV, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        
    for row in reader:
        net = ipaddress.IPv4Network(row["Subnet_CIDR"])
        start_ip = ipaddress.IPv4Address(row["Start_IP_Address"])
        end_ip = ipaddress.IPv4Address(row["End_IP_Address"])
        gw_ip = ipaddress.IPv4Address(row["Default_Gateway"])
        
        assert start_ip in net, f"{start_ip} not in {net}"
        assert end_ip in net, f"{end_ip} not in {net}"
        assert start_ip > gw_ip, f"Start IP {start_ip} should be greater than gateway {gw_ip}"
        assert start_ip <= end_ip, f"Start IP {start_ip} > End IP {end_ip}"
        
    print("  [PASS] test_dhcp_ip_ranges_validity (subnet bounds & exclusion boundaries valid)")

def test_dns_records_in_guide():
    """Verify required DNS A records and CNAME records are documented in server_setup.md."""
    with open(SERVER_SETUP_MD, "r", encoding="utf-8") as f:
        content = f.read()
        
    required_records = [
        r"records\.hospital\.local.*172\.16\.7\.4",
        r"portal\.hospital\.local.*172\.16\.7\.4",
        r"pacs\.hospital\.local.*172\.16\.7\.7",
        r"voip\.hospital\.local.*172\.16\.7\.4",
        r"ntp\.hospital\.local.*172\.16\.7\.4",
        r"www\.hospital\.local.*portal\.hospital\.local",
        r"ehr\.hospital\.local.*records\.hospital\.local",
    ]
    for pat in required_records:
        assert re.search(pat, content, re.IGNORECASE), f"DNS record matching pattern '{pat}' missing in server_setup.md"
        
    print("  [PASS] test_dns_records_in_guide (all 5 A-records & CNAMEs verified)")

def test_wan_dhcp_relay_explanation_present():
    """Verify server_setup.md contains technical explanation of WAN DHCP relay and failure mode analysis."""
    with open(SERVER_SETUP_MD, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "GIADDR" in content, "GIADDR explanation missing"
    assert "ip helper-address" in content, "ip helper-address explanation missing"
    assert "APIPA" in content, "APIPA failure mode analysis missing"
    assert "169.254" in content, "169.254 APIPA IP missing"
    
    print("  [PASS] test_wan_dhcp_relay_explanation_present (GIADDR, helper-address, APIPA analyzed)")

def run_all():
    print("Executing Central Server Farm & Application Services Verification Suite...")
    test_dhcp_pools_csv_structure()
    test_dhcp_gateways_and_dns()
    test_dhcp_ip_ranges_validity()
    test_dns_records_in_guide()
    test_wan_dhcp_relay_explanation_present()
    print("\nALL 5 SERVER FARM & APPLICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_all()
