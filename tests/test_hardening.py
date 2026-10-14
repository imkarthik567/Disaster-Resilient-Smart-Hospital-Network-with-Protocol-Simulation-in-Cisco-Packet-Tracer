#!/usr/bin/env python3
"""
================================================================================
Unit Test Suite: Device Hardening, Management Security & Service Suppression
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Validates Prompt 5.3 requirements:
- Service password-encryption, enable secret & local admin user with privilege 15
- SSH Version 2 enforcement, 1024-bit RSA keys & transport input ssh
- VTY access-class restriction to management consoles (ACL-VTY-SSH)
- Inactivity exec-timeout & security warning motd banner
- Insecure service suppression (no ip http server, no ip http secure-server)
- Disabling CDP on edge and untrusted guest-facing access ports
- Centralized NTP client (ntp server 172.16.7.4) and Syslog (logging host 172.16.7.4)
- Shutting down & parking unused physical switchports in VLAN 999
- Existence and completeness of /verification/hardening_checklist.md
================================================================================
"""

import os
import re
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIGS_DIR = os.path.join(PROJECT_ROOT, "configs")
VERIFICATION_DIR = os.path.join(PROJECT_ROOT, "verification")

HOSPITAL_DEVICES = ["R1", "R2", "SW-D1", "SW-D2", "SW-D3", "SW-D4", "SW-A1", "SW-A2", "SW-A3", "SW-A4", "SW-A5"]
SWITCHES = ["SW-D1", "SW-D2", "SW-D3", "SW-D4", "SW-A1", "SW-A2", "SW-A3", "SW-A4", "SW-A5"]

def load_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def test_hardening_checklist_document():
    """Verify /verification/hardening_checklist.md exists and contains verification commands for all items."""
    checklist_path = os.path.join(VERIFICATION_DIR, "hardening_checklist.md")
    assert os.path.isfile(checklist_path), f"Hardening checklist missing at {checklist_path}"
    doc = load_file(checklist_path)
    
    assert "service password-encryption" in doc, "password-encryption control missing in checklist"
    assert "enable secret" in doc, "enable secret control missing in checklist"
    assert "show ip ssh" in doc, "show ip ssh verification command missing"
    assert "ACL-VTY-SSH" in doc, "ACL-VTY-SSH missing in checklist"
    assert "exec-timeout" in doc, "exec-timeout control missing in checklist"
    assert "no ip http server" in doc, "HTTP server suppression missing in checklist"
    assert "no cdp enable" in doc, "CDP disabling control missing in checklist"
    assert "ntp server" in doc, "NTP client control missing in checklist"
    assert "logging host" in doc, "Syslog client control missing in checklist"
    assert "Packet Tracer 8.x" in doc, "Packet Tracer compatibility analysis missing"
    print("  [PASS] test_hardening_checklist_document (Checklist verified with commands & PT notes)")

def test_service_password_encryption_on_all_devices():
    """Verify 'service password-encryption' is configured across all hospital devices."""
    for dev in HOSPITAL_DEVICES:
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        assert "service password-encryption" in cfg, f"'service password-encryption' missing in {dev}"
    print(f"  [PASS] test_service_password_encryption_on_all_devices (Verified across {len(HOSPITAL_DEVICES)} devices)")

def test_enable_secret_and_admin_user():
    """Verify 'enable secret' and 'username admin privilege 15 secret' on all hospital devices."""
    for dev in HOSPITAL_DEVICES:
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        assert re.search(r"enable\s+secret\s+class123", cfg), f"'enable secret class123' missing in {dev}"
        assert re.search(r"username\s+admin\s+privilege\s+15\s+secret\s+class123", cfg), f"Admin priv 15 user missing in {dev}"
    print(f"  [PASS] test_enable_secret_and_admin_user (Verified on all {len(HOSPITAL_DEVICES)} devices)")

def test_ssh_version_2_and_crypto_keys():
    """Verify RSA key generation, SSH Version 2, domain name, and timeouts on all devices."""
    for dev in HOSPITAL_DEVICES:
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        assert "ip domain-name hospital.local" in cfg, f"Domain name missing in {dev}"
        assert re.search(r"crypto\s+key\s+generate\s+rsa\s+modulus\s+1024", cfg), f"RSA key 1024 missing in {dev}"
        assert "ip ssh version 2" in cfg, f"SSH version 2 missing in {dev}"
        assert "ip ssh time-out 60" in cfg, f"SSH time-out 60 missing in {dev}"
        assert "ip ssh authentication-retries 3" in cfg, f"SSH retries 3 missing in {dev}"
    print(f"  [PASS] test_ssh_version_2_and_crypto_keys (SSH v2, RSA 1024 & timeouts verified on {len(HOSPITAL_DEVICES)} devices)")

def test_vty_access_class_and_ssh_transport():
    """Verify ACL-VTY-SSH, access-class binding, transport input ssh, and exec-timeout on VTY lines."""
    for dev in HOSPITAL_DEVICES:
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        
        # Check ACL definition
        assert "ip access-list standard ACL-VTY-SSH" in cfg, f"ACL-VTY-SSH definition missing in {dev}"
        assert "permit host 172.16.7.212" in cfg, f"Permit NOC PC missing in {dev} VTY ACL"
        assert "permit host 172.16.8.75" in cfg, f"Permit Clinic PC missing in {dev} VTY ACL"
        
        # Check VTY 0 4
        m_0_4 = re.search(r"line\s+vty\s+0\s+4([\s\S]*?)exit", cfg, re.IGNORECASE)
        assert m_0_4, f"line vty 0 4 block missing in {dev}"
        b_0_4 = m_0_4.group(1)
        assert "access-class ACL-VTY-SSH in" in b_0_4, f"access-class missing in VTY 0 4 of {dev}"
        assert "transport input ssh" in b_0_4, f"transport input ssh missing in VTY 0 4 of {dev}"
        assert "exec-timeout 15 0" in b_0_4, f"exec-timeout missing in VTY 0 4 of {dev}"
        
        # Check VTY 5 15
        m_5_15 = re.search(r"line\s+vty\s+5\s+15([\s\S]*?)exit", cfg, re.IGNORECASE)
        assert m_5_15, f"line vty 5 15 block missing in {dev}"
        b_5_15 = m_5_15.group(1)
        assert "access-class ACL-VTY-SSH in" in b_5_15, f"access-class missing in VTY 5 15 of {dev}"
        assert "transport input ssh" in b_5_15, f"transport input ssh missing in VTY 5 15 of {dev}"
        assert "exec-timeout 15 0" in b_5_15, f"exec-timeout missing in VTY 5 15 of {dev}"
    print(f"  [PASS] test_vty_access_class_and_ssh_transport (All VTY lines restricted to SSH & NOC/Clinic IPs)")

def test_unused_services_disabled():
    """Verify HTTP servers are disabled on network gear, and CDP is disabled on edge/guest ports."""
    for dev in HOSPITAL_DEVICES:
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        assert "no ip http server" in cfg, f"'no ip http server' missing in {dev}"
        assert "no ip http secure-server" in cfg, f"'no ip http secure-server' missing in {dev}"
        
    # CDP disabled on untrusted / edge interfaces
    r1_cfg = load_file(os.path.join(CONFIGS_DIR, "R1", "R1.cfg"))
    assert re.search(r"interface\s+GigabitEthernet0/2[\s\S]*?no\s+cdp\s+enable[\s\S]*?exit", r1_cfg, re.IGNORECASE), "CDP not disabled on R1 Gi0/2"
    
    swa4_cfg = load_file(os.path.join(CONFIGS_DIR, "SW-A4", "SW-A4.cfg"))
    assert re.search(r"interface\s+FastEthernet0/10[\s\S]*?no\s+cdp\s+enable[\s\S]*?exit", swa4_cfg, re.IGNORECASE), "CDP not disabled on SW-A4 Fa0/10"
    
    swa5_cfg = load_file(os.path.join(CONFIGS_DIR, "SW-A5", "SW-A5.cfg"))
    assert re.search(r"interface\s+FastEthernet0/10[\s\S]*?no\s+cdp\s+enable[\s\S]*?exit", swa5_cfg, re.IGNORECASE), "CDP not disabled on SW-A5 Fa0/10"
    print("  [PASS] test_unused_services_disabled (HTTP disabled on all gear; CDP disabled on edge/guest ports)")

def test_ntp_and_syslog_configuration():
    """Verify NTP client and Syslog forwarding are configured pointing to Central Server 172.16.7.4."""
    for dev in HOSPITAL_DEVICES:
        cfg = load_file(os.path.join(CONFIGS_DIR, dev, f"{dev}.cfg"))
        assert "ntp server 172.16.7.4" in cfg, f"'ntp server 172.16.7.4' missing in {dev}"
        assert "logging host 172.16.7.4" in cfg, f"'logging host 172.16.7.4' missing in {dev}"
        assert "logging trap informational" in cfg, f"'logging trap informational' missing in {dev}"
    print(f"  [PASS] test_ntp_and_syslog_configuration (NTP & Syslog pointing to 172.16.7.4 on {len(HOSPITAL_DEVICES)} devices)")

def test_unused_ports_shutdown_and_parked():
    """Verify all switch configurations shut down unallocated ports and park them in VLAN 999."""
    for sw in SWITCHES:
        cfg = load_file(os.path.join(CONFIGS_DIR, sw, f"{sw}.cfg"))
        pattern = r"interface\s+range\s+[A-Za-z0-9/,\s-]+[\s\S]*?switchport\s+access\s+vlan\s+999[\s\S]*?shutdown"
        assert re.search(pattern, cfg, re.IGNORECASE), f"Unused port shutdown/VLAN 999 parking missing in {sw}"
    print(f"  [PASS] test_unused_ports_shutdown_and_parked (Verified on all {len(SWITCHES)} switches)")

def run_all_tests():
    print("=" * 80)
    print("  INFRASTRUCTURE DEVICE HARDENING & MANAGEMENT SECURITY TEST SUITE")
    print("=" * 80)
    test_hardening_checklist_document()
    test_service_password_encryption_on_all_devices()
    test_enable_secret_and_admin_user()
    test_ssh_version_2_and_crypto_keys()
    test_vty_access_class_and_ssh_transport()
    test_unused_services_disabled()
    test_ntp_and_syslog_configuration()
    test_unused_ports_shutdown_and_parked()
    print("\nALL 8 DEVICE HARDENING VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_all_tests()
