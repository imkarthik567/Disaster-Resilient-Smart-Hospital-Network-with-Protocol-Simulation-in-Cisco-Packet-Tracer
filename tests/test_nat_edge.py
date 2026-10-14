#!/usr/bin/env python3
"""
================================================================================
Unit Test Suite: Internet Edge, NAT/PAT Overload, Port-Forwarding & ISP Gateway
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Validates Prompt 5.2 requirements:
- R1 Dynamic PAT overload for authorized client VLANs (Admin & Guest)
- R1 Static NAT port-forwarding for Central EHR Web Portal (ports 80 & 443)
- Inside vs. Outside interface role assignments on R1
- Default routing to ISP gateway and dynamic injection via OSPF
- NAT-ACL subnet whitelisting and zero-trust exclusion of ICU/Surgery/Voice/Mgmt
- Simulated ISP router (EDGE-ISP) configuration with public DNS, web server & return route
- Comprehensive documentation and viva exam defense notes
================================================================================
"""

import os
import re
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIGS_DIR = os.path.join(PROJECT_ROOT, "configs")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")

def load_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def test_nat_documentation_and_viva_note():
    """Verify /docs/nat_internet_edge.md exists and covers all required edge architecture topics."""
    doc_path = os.path.join(DOCS_DIR, "nat_internet_edge.md")
    assert os.path.isfile(doc_path), f"NAT documentation missing at {doc_path}"
    doc = load_file(doc_path)
    
    # Core technical requirements in documentation
    assert "PAT Overload" in doc or "overload" in doc, "PAT overload description missing"
    assert "extendable" in doc, "Static NAT extendable explanation missing"
    assert "ip nat inside" in doc and "ip nat outside" in doc, "Interface role explanation missing"
    assert "default-information originate" in doc, "Default route distribution missing"
    assert "show ip nat translations" in doc, "Translation table verification missing"
    assert "show ip nat statistics" in doc, "NAT statistics verification missing"
    assert "Why NAT is NOT a Security Feature" in doc, "Viva defense note missing"
    assert "RFC 1631" in doc or "IPv4 address exhaustion" in doc, "RFC 1631 historical intent missing"
    assert "IPv6" in doc, "IPv6 paradigm discussion missing in viva note"
    print("  [PASS] test_nat_documentation_and_viva_note (All sections & viva defense verified)")

def test_r1_nat_configuration():
    """Verify R1 has dynamic PAT overload, static port-forwarding, default route and OSPF injection."""
    r1_cfg = load_file(os.path.join(CONFIGS_DIR, "R1", "R1.cfg"))
    
    # 1. Dynamic PAT Overload
    pat_pattern = r"ip\s+nat\s+inside\s+source\s+list\s+NAT-ACL\s+interface\s+GigabitEthernet0/2\s+overload"
    assert re.search(pat_pattern, r1_cfg, re.IGNORECASE), "PAT overload command missing on R1"
    
    # 2. Static NAT Port-Forwarding (ports 80 & 443 with extendable)
    pf_http = r"ip\s+nat\s+inside\s+source\s+static\s+tcp\s+172\.16\.7\.4\s+80\s+172\.16\.8\.102\s+80\s+extendable"
    pf_https = r"ip\s+nat\s+inside\s+source\s+static\s+tcp\s+172\.16\.7\.4\s+443\s+172\.16\.8\.102\s+443\s+extendable"
    assert re.search(pf_http, r1_cfg, re.IGNORECASE), "Port 80 static NAT port-forward missing on R1"
    assert re.search(pf_https, r1_cfg, re.IGNORECASE), "Port 443 static NAT port-forward missing on R1"
    
    # 3. Default route to ISP gateway
    def_route = r"ip\s+route\s+0\.0\.0\.0\s+0\.0\.0\.0\s+172\.16\.8\.101"
    assert re.search(def_route, r1_cfg), "Default route to ISP 172.16.8.101 missing on R1"
    
    # 4. OSPF Default Information Originate
    ospf_def = r"router\s+ospf\s+1[\s\S]*?default-information\s+originate"
    assert re.search(ospf_def, r1_cfg, re.IGNORECASE), "OSPF default-information originate missing on R1"
    print("  [PASS] test_r1_nat_configuration (PAT overload, static port forwarding, default route verified)")

def test_r1_nat_interface_roles():
    """Verify R1 correctly configures inside and outside NAT interfaces."""
    r1_cfg = load_file(os.path.join(CONFIGS_DIR, "R1", "R1.cfg"))
    
    # Outside: Gi0/2 (facing ISP)
    outside_pattern = r"interface\s+GigabitEthernet0/2[\s\S]*?ip\s+nat\s+outside[\s\S]*?exit"
    assert re.search(outside_pattern, r1_cfg, re.IGNORECASE), "Gi0/2 missing 'ip nat outside'"
    
    # Inside: Gi0/0 (SW-D1), Gi0/1 (SW-D2), Se0/0/0 (Primary WAN), Se0/0/1 (Standby WAN)
    inside_interfaces = ["GigabitEthernet0/0", "GigabitEthernet0/1", "Serial0/0/0", "Serial0/0/1"]
    for intf in inside_interfaces:
        pattern = rf"interface\s+{re.escape(intf)}[\s\S]*?ip\s+nat\s+inside[\s\S]*?exit"
        assert re.search(pattern, r1_cfg, re.IGNORECASE), f"{intf} missing 'ip nat inside' on R1"
    print("  [PASS] test_r1_nat_interface_roles (1 Outside & 4 Inside interfaces verified on R1)")

def test_r1_nat_acl_whitelist_and_exclusion():
    """Verify NAT-ACL whitelists Admin & Guest while strictly excluding ICU, Surgery, Voice, and Mgmt."""
    r1_cfg = load_file(os.path.join(CONFIGS_DIR, "R1", "R1.cfg"))
    
    # Extract NAT-ACL block
    m = re.search(r"ip\s+access-list\s+standard\s+NAT-ACL([\s\S]*?)exit", r1_cfg, re.IGNORECASE)
    assert m, "Standard access-list NAT-ACL missing on R1"
    body = m.group(1)
    
    # Whitelisted subnets
    assert re.search(r"permit\s+172\.16\.0\.0\s+0\.0\.3\.255", body), "Main Guest VLAN 40 not permitted in NAT-ACL"
    assert re.search(r"permit\s+172\.16\.4\.0\s+0\.0\.1\.255", body), "Main Admin VLAN 30 not permitted in NAT-ACL"
    assert re.search(r"permit\s+172\.16\.6\.128\s+0\.0\.0\.127", body), "Clinic Guest VLAN 40 not permitted in NAT-ACL"
    assert re.search(r"permit\s+172\.16\.8\.0\s+0\.0\.0\.31", body), "Clinic Admin VLAN 30 not permitted in NAT-ACL"
    
    # Excluded subnets: ICU, Surgery, Voice, Server Farm, Management must NOT be permitted
    assert not re.search(r"permit\s+172\.16\.7\.128", body), "ICU VLAN 10 illegally permitted in NAT-ACL"
    assert not re.search(r"permit\s+172\.16\.7\.64", body), "Surgery VLAN 20 illegally permitted in NAT-ACL"
    assert not re.search(r"permit\s+172\.16\.7\.0\s+0\.0\.0\.63", body), "Server Farm VLAN 50 illegally permitted in dynamic PAT"
    assert not re.search(r"permit\s+172\.16\.6\.0\s+0\.0\.0\.127", body), "Voice VLAN 60 illegally permitted in NAT-ACL"
    assert not re.search(r"permit\s+172\.16\.7\.192", body), "Management VLAN 99 illegally permitted in NAT-ACL"
    
    # Default drop
    assert re.search(r"deny\s+any(\s+log)?", body), "Default deny rule missing in NAT-ACL"
    print("  [PASS] test_r1_nat_acl_whitelist_and_exclusion (Whitelisted Admin/Guest, excluded ICU/Surgery/Voice/Mgmt)")

def test_edge_isp_router_configuration():
    """Verify EDGE-ISP router has ISP IP, simulated public DNS, external web server, and return route."""
    isp_cfg = load_file(os.path.join(CONFIGS_DIR, "edge-isp", "edge-isp.cfg"))
    
    # WAN link to R1
    wan_pattern = r"interface\s+GigabitEthernet0/0[\s\S]*?ip\s+address\s+172\.16\.8\.101\s+255\.255\.255\.252[\s\S]*?exit"
    assert re.search(wan_pattern, isp_cfg, re.IGNORECASE), "EDGE-ISP Gi0/0 missing 172.16.8.101/30"
    
    # Public DNS loopbacks
    assert re.search(r"interface\s+Loopback0[\s\S]*?ip\s+address\s+8\.8\.8\.8\s+255\.255\.255\.255", isp_cfg), "Google DNS 8.8.8.8 missing on Loopback0"
    assert re.search(r"interface\s+Loopback1[\s\S]*?ip\s+address\s+1\.1\.1\.1\s+255\.255\.255\.255", isp_cfg), "Cloudflare DNS 1.1.1.1 missing on Loopback1"
    
    # Public Web server simulator
    assert re.search(r"interface\s+Loopback2[\s\S]*?ip\s+address\s+203\.0\.113\.80", isp_cfg), "Public Web Server 203.0.113.80 missing on Loopback2"
    
    # HTTP server enabled
    assert "ip http server" in isp_cfg.lower(), "Built-in 'ip http server' missing on EDGE-ISP"
    
    # Static return route to hospital supernet
    assert re.search(r"ip\s+route\s+172\.16\.0\.0\s+255\.255\.0\.0\s+172\.16\.8\.102", isp_cfg), "Return route to 172.16.8.102 missing on EDGE-ISP"
    print("  [PASS] test_edge_isp_router_configuration (WAN IP, 3 Loopbacks, HTTP server & return route verified)")

def test_verification_commands_in_configs():
    """Verify R1.cfg and edge-isp.cfg contain required show commands and expected outputs."""
    r1_cfg = load_file(os.path.join(CONFIGS_DIR, "R1", "R1.cfg"))
    assert "show ip nat translations" in r1_cfg, "'show ip nat translations' missing in R1 verification"
    assert "show ip nat statistics" in r1_cfg, "'show ip nat statistics' missing in R1 verification"
    
    isp_cfg = load_file(os.path.join(CONFIGS_DIR, "edge-isp", "edge-isp.cfg"))
    assert "show ip interface brief" in isp_cfg, "'show ip interface brief' missing in EDGE-ISP verification"
    assert "ping 172.16.8.102" in isp_cfg, "'ping 172.16.8.102' missing in EDGE-ISP verification"
    print("  [PASS] test_verification_commands_in_configs (Verification commands and expected outputs present)")

def run_all_tests():
    print("=" * 80)
    print("  INTERNET EDGE, NAT/PAT OVERLOAD & PORT-FORWARDING TEST SUITE")
    print("=" * 80)
    test_nat_documentation_and_viva_note()
    test_r1_nat_configuration()
    test_r1_nat_interface_roles()
    test_r1_nat_acl_whitelist_and_exclusion()
    test_edge_isp_router_configuration()
    test_verification_commands_in_configs()
    print("\nALL 6 NAT & INTERNET EDGE VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_all_tests()
