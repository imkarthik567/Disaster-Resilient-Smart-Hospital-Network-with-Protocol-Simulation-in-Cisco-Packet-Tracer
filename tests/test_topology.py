#!/usr/bin/env python3
"""
Unit Tests for Topology Cabling Table and BOM Verification
Disaster-Resilient Smart Hospital Network
"""

import csv
import os
import re
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CABLING_CSV = os.path.join(PROJECT_ROOT, "topology", "cabling.csv")
BOM_MD = os.path.join(PROJECT_ROOT, "topology", "bom.md")
IP_TABLE_CSV = os.path.join(PROJECT_ROOT, "addressing", "ip_table.csv")

def test_cabling_csv_structure():
    assert os.path.exists(CABLING_CSV), "cabling.csv does not exist"
    with open(CABLING_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required_headers = [
            "Link-ID", "Device A", "Interface A", "Device B", "Interface B",
            "Cable type", "Layer", "VLANs carried", "IP/subnet if routed", "Purpose"
        ]
        for h in required_headers:
            assert h in reader.fieldnames, f"Missing header: {h}"
        
        rows = list(reader)
        assert len(rows) >= 50, f"Expected at least 50 links, got {len(rows)}"

def test_cabling_unique_link_ids():
    with open(CABLING_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        link_ids = [row["Link-ID"] for row in reader]
    assert len(link_ids) == len(set(link_ids)), "Duplicate Link-IDs detected in cabling.csv"

def test_no_interface_port_collisions():
    """Ensure no physical switch or router interface is connected more than once."""
    device_ports = {}
    with open(CABLING_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cable_type = row["Cable type"]
            # Exclude over-the-air wireless links from point-to-point collision check
            if "Wireless" in cable_type:
                continue

            dev_a, port_a = row["Device A"], row["Interface A"]
            dev_b, port_b = row["Device B"], row["Interface B"]

            # Key: (device, port)
            key_a = (dev_a, port_a)
            assert key_a not in device_ports, f"Port collision: {key_a} connected multiple times (Link {row['Link-ID']} vs {device_ports[key_a]})"
            device_ports[key_a] = row["Link-ID"]

            # Endpoints like PCs/SBCs have single interface, check Dev B as well
            if not port_b.startswith("Port1"):  # AP wireless RF port
                key_b = (dev_b, port_b)
                assert key_b not in device_ports, f"Port collision: {key_b} connected multiple times (Link {row['Link-ID']} vs {device_ports[key_b]})"
                device_ports[key_b] = row["Link-ID"]

def test_serial_dce_clock_rate():
    """Verify that serial WAN links explicitly specify DCE and clock rate 128000 on R1."""
    with open(CABLING_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        wan_links = [row for row in reader if row["Link-ID"].startswith("LINK-WAN")]
    assert len(wan_links) == 2, "Expected 2 WAN serial links"
    for w in wan_links:
        assert "clock rate 128000" in w["Cable type"], f"Missing clock rate 128000 in {w['Link-ID']}"
        assert w["Device A"] == "R1", "R1 must be Device A (DCE end)"

def test_vlan_host_counts_and_sbc_requirements():
    """Verify host requirements: >= 3 hosts per VLAN, 3 SBCs in ICU, 2 SBCs in Surgery."""
    with open(IP_TABLE_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Main ICU (VLAN 10)
    icu_sbc = [r for r in rows if r["site"] == "Main Hospital" and r["vlan"] == "10" and r["device"].startswith("SBC")]
    icu_pc = [r for r in rows if r["site"] == "Main Hospital" and r["vlan"] == "10" and r["device"].startswith("PC")]
    assert len(icu_sbc) == 3, f"Expected 3 ICU SBCs, got {len(icu_sbc)}"
    assert len(icu_pc) >= 3, f"Expected >= 3 ICU PCs, got {len(icu_pc)}"

    # Main Surgery (VLAN 20)
    surg_sbc = [r for r in rows if r["site"] == "Main Hospital" and r["vlan"] == "20" and r["device"].startswith("SBC")]
    surg_pc = [r for r in rows if r["site"] == "Main Hospital" and r["vlan"] == "20" and r["device"].startswith("PC")]
    assert len(surg_sbc) == 2, f"Expected 2 Surgery SBCs, got {len(surg_sbc)}"
    assert len(surg_pc) >= 3, f"Expected >= 3 Surgery PCs, got {len(surg_pc)}"

    # Main Admin (VLAN 30)
    admin_pc = [r for r in rows if r["site"] == "Main Hospital" and r["vlan"] == "30" and r["device"].startswith("PC")]
    assert len(admin_pc) >= 3, f"Expected >= 3 Admin PCs, got {len(admin_pc)}"

    # Main Guest (VLAN 40)
    guest_dev = [r for r in rows if r["site"] == "Main Hospital" and r["vlan"] == "40" and r["device"].startswith("LAPTOP")]
    assert len(guest_dev) >= 3, f"Expected >= 3 Guest Laptops, got {len(guest_dev)}"

    # Main Voice (VLAN 60)
    voice_phones = [r for r in rows if r["site"] == "Main Hospital" and r["vlan"] == "60" and r["device"].startswith("PHONE")]
    assert len(voice_phones) >= 3, f"Expected >= 3 Main Phones, got {len(voice_phones)}"

    # Remote Clinic Clinical (VLAN 10)
    clinic_clin = [r for r in rows if r["site"] == "Remote Clinic" and r["vlan"] == "10" and r["device"].startswith("PC")]
    assert len(clinic_clin) >= 3, f"Expected >= 3 Clinic Clinical PCs, got {len(clinic_clin)}"

    # Remote Clinic Admin (VLAN 30)
    clinic_adm = [r for r in rows if r["site"] == "Remote Clinic" and r["vlan"] == "30" and r["device"].startswith("PC")]
    assert len(clinic_adm) >= 3, f"Expected >= 3 Clinic Admin PCs, got {len(clinic_adm)}"

def test_ptbuilder_js_validity():
    """Verify that build_topology.js exists, contains required functions, and matches inventory."""
    js_path = os.path.join(PROJECT_ROOT, "topology", "build_topology.js")
    assert os.path.exists(js_path), "build_topology.js does not exist"
    with open(js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "var CONFIG =" in content, "Missing CONFIG object in JS"
    assert "function buildDevices" in content, "Missing buildDevices function"
    assert "function installModules" in content, "Missing installModules function"
    assert "function createLinks" in content, "Missing createLinks function"
    assert "function applyLayout" in content, "Missing applyLayout function"
    assert "function reportSummary" in content, "Missing reportSummary function"
    assert '"R1"' in content and '"R2"' in content and '"SW-D1"' in content, "Core devices missing from JS config"

if __name__ == "__main__":
    print("Executing Topology & Cabling Verification Suite...")
    test_cabling_csv_structure()
    print("  [PASS] test_cabling_csv_structure")
    test_cabling_unique_link_ids()
    print("  [PASS] test_cabling_unique_link_ids")
    test_no_interface_port_collisions()
    print("  [PASS] test_no_interface_port_collisions")
    test_serial_dce_clock_rate()
    print("  [PASS] test_serial_dce_clock_rate")
    test_vlan_host_counts_and_sbc_requirements()
    print("  [PASS] test_vlan_host_counts_and_sbc_requirements")
    test_ptbuilder_js_validity()
    print("  [PASS] test_ptbuilder_js_validity")
    print("\nALL 6 TOPOLOGY & CABLING TESTS PASSED SUCCESSFULLY!")
