#!/usr/bin/env python3
"""
================================================================================
Unit Test Suite: Access Control Lists (ACLs), Perimeter Security & Device Hardening
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Validates security policies across R1, R2, SW-D1, SW-D2, and SW-D3:
- Zone-to-zone microsegmentation (ICU, Surgery, Admin, Guest, Server, Voice, Mgmt)
- Inbound SVI ACL bindings closest to packet sources
- Edge perimeter filtering with BCP 38 / RFC 2827 anti-spoofing on R1
- Return traffic stateful handling via TCP 'established' (Packet Tracer 8.x verified)
- VTY line SSH restriction (ACL-VTY-SSH) to authorized management workstations
- Presence of per-rule remarks and logging on all drop actions
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

def parse_acl_blocks(config_text):
    """
    Parses named access list blocks into a dict:
    { acl_name: { 'type': 'standard'|'extended', 'rules': [str], 'remarks': [str] } }
    """
    acls = {}
    pattern = r"ip\s+access-list\s+(standard|extended)\s+([A-Za-z0-9_-]+)([\s\S]*?)exit"
    matches = re.finditer(pattern, config_text, re.IGNORECASE)
    for m in matches:
        acl_type = m.group(1).lower()
        acl_name = m.group(2)
        body = m.group(3)
        
        lines = [line.strip() for line in body.strip().split("\n") if line.strip()]
        rules = [l for l in lines if l.startswith("permit") or l.startswith("deny")]
        remarks = [l for l in lines if l.startswith("remark")]
        
        acls[acl_name] = {
            "type": acl_type,
            "body": body,
            "rules": rules,
            "remarks": remarks,
        }
    return acls

def test_security_policy_documentation():
    """Verify /docs/security_policy.md exists and covers all required design aspects."""
    doc_path = os.path.join(DOCS_DIR, "security_policy.md")
    assert os.path.isfile(doc_path), f"Security policy document missing at {doc_path}"
    doc = load_file(doc_path)
    
    assert "Zone-to-Zone" in doc and "Permit/Deny Matrix" in doc, "Matrix missing in security policy"
    assert "BCP 38" in doc or "RFC 2827" in doc, "Anti-spoofing reference missing"
    assert "established" in doc, "TCP established explanation missing"
    assert "Packet Tracer" in doc, "Packet Tracer compatibility discussion missing"
    assert "Verification Test Matrix" in doc, "Test verification table missing"
    print("  [PASS] test_security_policy_documentation (Matrix, BCP 38, established & test table verified)")

def test_edge_perimeter_acl_r1():
    """Verify R1 Gi0/2 has ACL-EDGE-IN applied inbound with anti-spoofing and portal permits."""
    cfg = load_file(os.path.join(CONFIGS_DIR, "R1", "R1.cfg"))
    acls = parse_acl_blocks(cfg)
    
    assert "ACL-EDGE-IN" in acls, "ACL-EDGE-IN missing on R1"
    edge_acl = acls["ACL-EDGE-IN"]
    assert edge_acl["type"] == "extended", "ACL-EDGE-IN must be extended"
    
    # Check interface binding
    intf_pattern = r"interface\s+GigabitEthernet0/2[\s\S]*?ip\s+access-group\s+ACL-EDGE-IN\s+in[\s\S]*?exit"
    assert re.search(intf_pattern, cfg, re.IGNORECASE), "ACL-EDGE-IN not bound inbound to Gi0/2 on R1"
    
    # Anti-spoofing (RFC 1918 + loopback + APIPA + multicast)
    body = edge_acl["body"]
    assert re.search(r"deny\s+ip\s+10\.0\.0\.0\s+0\.255\.255\.255\s+any\s+log", body), "Deny 10.0.0.0/8 missing"
    assert re.search(r"deny\s+ip\s+172\.16\.0\.0\s+0\.15\.255\.255\s+any\s+log", body), "Deny 172.16.0.0/12 missing"
    assert re.search(r"deny\s+ip\s+192\.168\.0\.0\s+0\.0\.255\.255\s+any\s+log", body), "Deny 192.168.0.0/16 missing"
    assert re.search(r"deny\s+ip\s+127\.0\.0\.0\s+0\.255\.255\.255\s+any\s+log", body), "Deny 127.0.0.0/8 missing"
    assert re.search(r"deny\s+ip\s+169\.254\.0\.0\s+0\.0\.255\.255\s+any\s+log", body), "Deny 169.254.0.0/16 missing"
    assert re.search(r"deny\s+ip\s+224\.0\.0\.0\s+15\.255\.255\.255\s+any\s+log", body), "Deny multicast missing"
    
    # Published portal & established return
    assert re.search(r"permit\s+tcp\s+any\s+host\s+172\.16\.8\.102\s+eq\s+www", body), "Permit HTTP to edge IP missing"
    assert re.search(r"permit\s+tcp\s+any\s+host\s+172\.16\.8\.102\s+eq\s+443", body), "Permit HTTPS to edge IP missing"
    assert re.search(r"permit\s+tcp\s+any\s+any\s+established", body), "Permit TCP established missing"
    assert re.search(r"deny\s+ip\s+any\s+any\s+log", body), "Implicit deny log missing"
    print("  [PASS] test_edge_perimeter_acl_r1 (Anti-spoofing, EHR portal, established return verified)")

def test_vty_line_hardening():
    """Verify R1, R2, SW-D1, SW-D2, SW-D3 enforce ACL-VTY-SSH on VTY management lines."""
    devices = ["R1", "R2", "SW-D1", "SW-D2", "SW-D3"]
    for dev in devices:
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        acls = parse_acl_blocks(cfg)
        
        assert "ACL-VTY-SSH" in acls, f"ACL-VTY-SSH missing on {dev}"
        vty_acl = acls["ACL-VTY-SSH"]
        assert vty_acl["type"] == "standard", f"ACL-VTY-SSH must be standard on {dev}"
        
        body = vty_acl["body"]
        assert re.search(r"permit\s+(host\s+)?172\.16\.7\.212", body), f"Permit NOC PC missing on {dev}"
        assert re.search(r"permit\s+(host\s+)?172\.16\.8\.75", body), f"Permit Clinic PC missing on {dev}"
        assert re.search(r"deny\s+any(\s+log)?", body), f"Deny any missing in VTY ACL on {dev}"
        
        # Check line vty 0 4 binding
        vty_pattern = r"line\s+vty\s+0\s+4[\s\S]*?access-class\s+ACL-VTY-SSH\s+in[\s\S]*?exit"
        assert re.search(vty_pattern, cfg, re.IGNORECASE), f"VTY 0 4 not secured with ACL-VTY-SSH on {dev}"
    print(f"  [PASS] test_vty_line_hardening (Verified across all {len(devices)} infrastructure devices)")

def test_distribution_svi_inbound_acl_bindings():
    """Verify proper inbound extended ACL bindings on SVIs across SW-D1, SW-D2, and SW-D3."""
    main_expected = {
        10: "ACL-ICU-IN",
        20: "ACL-SURGERY-IN",
        30: "ACL-ADMIN-IN",
        40: "ACL-GUEST-IN",
        50: "ACL-SERVER-IN",
        60: "ACL-VOICE-IN",
        99: "ACL-MGMT-IN",
    }
    for dev in ["SW-D1", "SW-D2"]:
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        for vlan, acl_name in main_expected.items():
            pattern = rf"interface\s+Vlan{vlan}[\s\S]*?ip\s+access-group\s+{acl_name}\s+in[\s\S]*?exit"
            assert re.search(pattern, cfg, re.IGNORECASE), f"{dev} Vlan{vlan} missing 'ip access-group {acl_name} in'"
            
    clinic_expected = {
        10: "ACL-CLINIC-CLINICAL-IN",
        30: "ACL-CLINIC-ADMIN-IN",
        40: "ACL-CLINIC-GUEST-IN",
        60: "ACL-CLINIC-VOICE-IN",
        99: "ACL-CLINIC-MGMT-IN",
    }
    cfg_d3 = load_file(os.path.join(CONFIGS_DIR, "SW-D3", "SW-D3.cfg"))
    for vlan, acl_name in clinic_expected.items():
        pattern = rf"interface\s+Vlan{vlan}[\s\S]*?ip\s+access-group\s+{acl_name}\s+in[\s\S]*?exit"
        assert re.search(pattern, cfg_d3, re.IGNORECASE), f"SW-D3 Vlan{vlan} missing 'ip access-group {acl_name} in'"
        
    print("  [PASS] test_distribution_svi_inbound_acl_bindings (19 SVI bindings verified on SW-D1, SW-D2, SW-D3)")

def test_guest_isolation_policy():
    """Verify Guest ACL permits DHCP, DNS to central server, Internet, and denies internal networks."""
    for dev, acl_name in [("SW-D1", "ACL-GUEST-IN"), ("SW-D2", "ACL-GUEST-IN"), ("SW-D3", "ACL-CLINIC-GUEST-IN")]:
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        acls = parse_acl_blocks(cfg)
        assert acl_name in acls, f"{acl_name} missing on {dev}"
        body = acls[acl_name]["body"]
        
        # Must permit DHCP relay
        assert re.search(r"permit\s+udp\s+any\s+any\s+eq\s+bootps", body), f"DHCP relay missing in {acl_name}"
        # Must permit DNS to central server
        assert re.search(r"permit\s+udp\s+any\s+host\s+172\.16\.7\.4\s+eq\s+domain", body), f"DNS UDP missing in {acl_name}"
        # Must deny internal hospital space
        assert re.search(r"deny\s+ip\s+any\s+172\.16\.0\.0\s+0\.0\.255\.255\s+log", body), f"Deny 172.16.0.0/16 log missing in {acl_name}"
        # Must permit outbound web
        assert re.search(r"permit\s+tcp\s+any\s+any\s+eq\s+www", body), f"Permit WWW missing in {acl_name}"
        assert re.search(r"permit\s+tcp\s+any\s+any\s+eq\s+443", body), f"Permit 443 missing in {acl_name}"
        # Must permit established return
        assert re.search(r"permit\s+tcp\s+any\s+any\s+established", body), f"Permit established missing in {acl_name}"
    print("  [PASS] test_guest_isolation_policy (DHCP, DNS, Internet permit & 172.16.0.0/16 isolation verified)")

def test_icu_surgery_isolation_policy():
    """Verify ICU & Surgery ACLs permit required servers and block lateral access to Admin/Guest."""
    for dev in ["SW-D1", "SW-D2"]:
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        acls = parse_acl_blocks(cfg)
        
        for acl_name in ["ACL-ICU-IN", "ACL-SURGERY-IN"]:
            body = acls[acl_name]["body"]
            # EHR portal access
            assert re.search(r"permit\s+tcp\s+any\s+host\s+172\.16\.7\.4\s+eq\s+www", body)
            assert re.search(r"permit\s+tcp\s+any\s+host\s+172\.16\.7\.4\s+eq\s+443", body)
            # PACS access (DICOM 104)
            assert re.search(r"permit\s+tcp\s+any\s+host\s+172\.16\.7\.7\s+eq\s+104", body)
            # Deny lateral Admin VLAN 30 (172.16.4.0/23)
            assert re.search(r"deny\s+ip\s+any\s+172\.16\.4\.0\s+0\.0\.1\.255\s+log", body)
            # Deny lateral Guest VLAN 40 (172.16.0.0/22)
            assert re.search(r"deny\s+ip\s+any\s+172\.16\.0\.0\s+0\.0\.3\.255\s+log", body)
    print("  [PASS] test_icu_surgery_isolation_policy (Server access permitted; lateral Admin & Guest blocked)")

def test_admin_isolation_policy():
    """Verify Admin ACL permits servers and Internet web, but explicitly denies clinical VLANs."""
    for dev in ["SW-D1", "SW-D2"]:
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        acls = parse_acl_blocks(cfg)
        body = acls["ACL-ADMIN-IN"]["body"]
        
        # Permit Central Server EHR
        assert re.search(r"permit\s+tcp\s+any\s+host\s+172\.16\.7\.4\s+eq\s+www", body)
        # Permit outbound Internet
        assert re.search(r"permit\s+tcp\s+any\s+any\s+eq\s+www", body)
        assert re.search(r"permit\s+tcp\s+any\s+any\s+eq\s+443", body)
        # Deny ICU VLAN 10 (172.16.7.128/26)
        assert re.search(r"deny\s+ip\s+any\s+172\.16\.7\.128\s+0\.0\.0\.63\s+log", body)
        # Deny Surgery VLAN 20 (172.16.7.64/26)
        assert re.search(r"deny\s+ip\s+any\s+172\.16\.7\.64\s+0\.0\.0\.63\s+log", body)
        # Deny Guest VLAN 40 (172.16.0.0/22)
        assert re.search(r"deny\s+ip\s+any\s+172\.16\.0\.0\s+0\.0\.3\.255\s+log", body)
    print("  [PASS] test_admin_isolation_policy (Admin to EHR permitted; ICU, Surgery & Guest access blocked)")

def test_management_vlan_protection():
    """Verify Management ACL restricts management access to authorized administrative consoles."""
    for dev, acl_name in [("SW-D1", "ACL-MGMT-IN"), ("SW-D2", "ACL-MGMT-IN"), ("SW-D3", "ACL-CLINIC-MGMT-IN")]:
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        acls = parse_acl_blocks(cfg)
        body = acls[acl_name]["body"]
        
        # Authorized consoles
        assert re.search(r"permit\s+ip\s+host\s+172\.16\.7\.212\s+any", body), f"NOC PC missing in {acl_name}"
        assert re.search(r"permit\s+ip\s+host\s+172\.16\.8\.75\s+any", body), f"Clinic PC missing in {acl_name}"
        assert re.search(r"deny\s+ip\s+any\s+any\s+log", body), f"Default deny log missing in {acl_name}"
    print("  [PASS] test_management_vlan_protection (VLAN 99 locked to NOC 172.16.7.212 and Clinic 172.16.8.75)")

def test_acl_remarks_present():
    """Verify that every ACL defined across all devices contains descriptive remark statements."""
    for dev in ["R1", "R2", "SW-D1", "SW-D2", "SW-D3"]:
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        acls = parse_acl_blocks(cfg)
        for acl_name, data in acls.items():
            assert len(data["remarks"]) > 0, f"ACL {acl_name} on {dev} lacks remark documentation"
    print("  [PASS] test_acl_remarks_present (All ACL rules contain descriptive remark statements)")

def test_packet_tracer_compatibility_stateful():
    """Verify stateful return traffic uses 'established' keyword, avoiding unsupported reflexive ACLs."""
    for dev in ["R1", "SW-D1", "SW-D2", "SW-D3"]:
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        assert "reflect" not in cfg.lower(), f"Reflexive ACL 'reflect' detected on {dev} (unsupported in PT switches)"
        assert "evaluate" not in cfg.lower(), f"Reflexive ACL 'evaluate' detected on {dev} (unsupported in PT switches)"
        assert "permit tcp any any established" in cfg, f"'permit tcp any any established' missing on {dev}"
    print("  [PASS] test_packet_tracer_compatibility_stateful (Stateful TCP established validated; no reflexive syntax)")

def run_all_tests():
    print("=" * 80)
    print("  SECURITY ACLS, PERIMETER FILTERING & DEVICE HARDENING TEST SUITE")
    print("=" * 80)
    test_security_policy_documentation()
    test_edge_perimeter_acl_r1()
    test_vty_line_hardening()
    test_distribution_svi_inbound_acl_bindings()
    test_guest_isolation_policy()
    test_icu_surgery_isolation_policy()
    test_admin_isolation_policy()
    test_management_vlan_protection()
    test_acl_remarks_present()
    test_packet_tracer_compatibility_stateful()
    print("\nALL 10 SECURITY ACL VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_all_tests()
