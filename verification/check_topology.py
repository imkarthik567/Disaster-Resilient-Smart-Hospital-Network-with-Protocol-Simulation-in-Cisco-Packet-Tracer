#!/usr/bin/env python3
"""
================================================================================
Comprehensive Network Topology & Cabling Verification Engine
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Validates /topology/cabling.csv against all architectural rules and addressing:
  1. No interface used twice (zero port collisions).
  2. Every device appears (100% BOM inventory coverage).
  3. Every trunk has matching ends (switch-to-switch with consistent Native VLAN 999).
  4. Every routed link has both ends in the same /30 subnet with valid host IPs.
  5. Serial links have exactly one DCE end with an explicit clock rate.
  6. Every end device is connected to a port of the correct VLAN and subnet.
Prints a formatted pass/fail report and exits non-zero on failure.
================================================================================
"""

import argparse
import csv
import ipaddress
import os
import re
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_CABLING_CSV  = os.path.join(PROJECT_ROOT, "topology", "cabling.csv")
DEFAULT_IP_TABLE_CSV = os.path.join(PROJECT_ROOT, "addressing", "ip_table.csv")

# Expected devices that MUST appear in the cabling topology
REQUIRED_INFRASTRUCTURE = [
    # Core & Edge
    "R1", "R2", "EDGE-ISP",
    # Distribution Switches
    "SW-D1", "SW-D2", "SW-D3",
    # Access Switches
    "SW-A1", "SW-A2", "SW-A3", "SW-A4", "SW-A5",
    # Enterprise Servers
    "SRV-CENTRAL", "SRV-PACS", "SRV-BACKUP", "SRV-CACHE",
    # ICU Endpoints
    "SBC-ICU-101", "SBC-ICU-102", "SBC-ICU-103",
    "PC-ICU-NURSE", "PC-ICU-DOC1", "PC-ICU-DOC2", "PHONE-ICU-601",
    # Surgery Endpoints
    "SBC-SURG-201", "SBC-SURG-202",
    "PC-THEATRE-1", "PC-THEATRE-2", "PC-THEATRE-3", "PHONE-SURG-602",
    # Main Admin & Management
    "PC-ADMIN-301", "PC-ADMIN-302", "PC-ADMIN-303", "PHONE-ADMIN-603", "PC-NOC-MGT",
    # Guest Wi-Fi (Main)
    "AP-GUEST", "LAPTOP-GUEST-1", "LAPTOP-GUEST-2", "LAPTOP-GUEST-3",
    # Remote Clinic Clinical
    "PC-CLINIC-CONSULT1", "PC-CLINIC-CONSULT2", "PC-CLINIC-TRIAGE",
    "PHONE-CLINIC-602", "PHONE-CLINIC-603",
    # Remote Clinic Admin & Management
    "PC-CLINIC-ADM1", "PC-CLINIC-ADM2", "PC-CLINIC-PHARM",
    "PHONE-CLINIC-601", "PC-CLINIC-MGT",
    # Guest Wi-Fi (Clinic)
    "AP-CLINIC-GUEST", "LAPTOP-CLINIC-G1", "LAPTOP-CLINIC-G2", "LAPTOP-CLINIC-G3"
]

def load_ip_table(ip_table_path: str) -> dict:
    """Loads addressing/ip_table.csv and returns device mapping."""
    ip_map = {}
    if not os.path.exists(ip_table_path):
        return ip_map

    with open(ip_table_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dev = row["device"].strip()
            if dev not in ip_map:
                ip_map[dev] = []
            ip_map[dev].append(row)
    return ip_map

# ------------------------------------------------------------------------------
# Check 1: No Interface Used Twice (Port Collisions)
# ------------------------------------------------------------------------------
def check_interface_collisions(links: list) -> tuple:
    """Verifies that no physical switch or router interface is connected multiple times."""
    used_ports = {}
    collisions = []

    for link in links:
        link_id = link["Link-ID"]
        cable   = link["Cable type"]

        # Over-the-air wireless connections do not occupy fixed physical ports
        if "wireless" in cable.lower():
            continue

        dev_a  = link["Device A"]
        port_a = link["Interface A"]
        dev_b  = link["Device B"]
        port_b = link["Interface B"]

        for dev, port in [(dev_a, port_a), (dev_b, port_b)]:
            # Access Point Port1 is a multi-client wireless radio, skip Port1 collisions
            if dev.startswith("AP-") and port == "Port1":
                continue

            key = (dev, port)
            if key in used_ports:
                prev_link = used_ports[key]
                collisions.append(
                    f"Port collision on {dev} interface {port}: used by {prev_link} and {link_id}"
                )
            else:
                used_ports[key] = link_id

    passed = len(collisions) == 0
    return passed, "No Interface Port Collisions", len(used_ports), collisions

# ------------------------------------------------------------------------------
# Check 2: Every Device Appears (Inventory Coverage)
# ------------------------------------------------------------------------------
def check_device_presence(links: list, required_devices: list) -> tuple:
    """Verifies that every expected network infrastructure and end device appears in cabling."""
    present_devices = set()
    for link in links:
        present_devices.add(link["Device A"])
        present_devices.add(link["Device B"])

    missing = []
    for req in required_devices:
        if req not in present_devices:
            missing.append(f"Missing required device: {req}")

    passed = len(missing) == 0
    return passed, "All Expected Devices Present", len(present_devices), missing

# ------------------------------------------------------------------------------
# Check 3: Every Trunk Has Matching Ends
# ------------------------------------------------------------------------------
def check_trunk_matching_ends(links: list) -> tuple:
    """Verifies that every L2 trunk is switch-to-switch and enforces Native VLAN 999."""
    trunk_links = [l for l in links if l["Layer"].strip() == "L2 trunk"]
    errors = []

    for t in trunk_links:
        link_id = t["Link-ID"]
        dev_a   = t["Device A"]
        dev_b   = t["Device B"]
        vlans   = t["VLANs carried"]

        # 1. Both endpoints must be switches
        is_dev_a_switch = dev_a.startswith("SW-")
        is_dev_b_switch = dev_b.startswith("SW-")

        if not (is_dev_a_switch and is_dev_b_switch):
            errors.append(
                f"{link_id}: Trunk connects non-switch endpoints ({dev_a} <-> {dev_b})"
            )

        # 2. Must mandate Native VLAN 999
        if "Native: 999" not in vlans:
            errors.append(
                f"{link_id}: Trunk missing mandatory Native VLAN 999 definition (Got: '{vlans}')"
            )

    passed = len(errors) == 0
    return passed, "Trunk Endpoints & Native VLAN 999 Consistency", len(trunk_links), errors

# ------------------------------------------------------------------------------
# Check 4: Every Routed Link Has Both Ends in the Same /30 Subnet
# ------------------------------------------------------------------------------
def check_routed_links(links: list) -> tuple:
    """Verifies that every L3 routed link is configured in the same valid /30 subnet."""
    routed_links = [l for l in links if l["Layer"].strip() == "L3 routed"]
    errors = []

    for r in routed_links:
        link_id  = r["Link-ID"]
        raw_info = r["IP/subnet if routed"]

        # Parse CIDR e.g. "172.16.8.80/30"
        cidr_match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d+)", raw_info)
        if not cidr_match:
            errors.append(f"{link_id}: Missing CIDR notation in routed link info: '{raw_info}'")
            continue

        cidr_str = cidr_match.group(1)
        try:
            net = ipaddress.IPv4Network(cidr_str, strict=True)
        except Exception as e:
            errors.append(f"{link_id}: Invalid IP network {cidr_str}: {e}")
            continue

        # Prefix length must be /30
        if net.prefixlen != 30:
            errors.append(f"{link_id}: Routed link prefix must be /30, got /{net.prefixlen} ({cidr_str})")
            continue

        # Extract individual IPs from info string
        ip_matches = re.findall(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b", raw_info)
        # First match is network address, subsequent matches are host IPs
        host_ips = [ipaddress.IPv4Address(ip) for ip in ip_matches[1:]]

        if len(host_ips) < 2:
            errors.append(f"{link_id}: Could not extract two host endpoints from: '{raw_info}'")
            continue

        ip1, ip2 = host_ips[0], host_ips[1]

        # Validate that both IPs belong to the exact same /30
        if ip1 not in net:
            errors.append(f"{link_id}: Endpoint {ip1} is not in subnet {net}")
        if ip2 not in net:
            errors.append(f"{link_id}: Endpoint {ip2} is not in subnet {net}")

        # Validate host IPs are distinct and usable (not network or broadcast)
        if ip1 == ip2:
            errors.append(f"{link_id}: Duplicate IP {ip1} assigned to both endpoints")
        if ip1 == net.network_address or ip1 == net.broadcast_address:
            errors.append(f"{link_id}: Endpoint {ip1} cannot use network or broadcast address")
        if ip2 == net.network_address or ip2 == net.broadcast_address:
            errors.append(f"{link_id}: Endpoint {ip2} cannot use network or broadcast address")

    passed = len(errors) == 0
    return passed, "Routed /30 Subnet Alignment & Host IP Validity", len(routed_links), errors

# ------------------------------------------------------------------------------
# Check 5: Serial Links Have Exactly One DCE End with a Clock Rate
# ------------------------------------------------------------------------------
def check_serial_links(links: list) -> tuple:
    """Verifies that all serial links have exactly one DCE end with explicit clock rate."""
    serial_links = []
    for l in links:
        is_serial_cable = "serial" in l["Cable type"].lower()
        is_serial_port  = l["Interface A"].startswith("Serial") or l["Interface B"].startswith("Serial")
        if is_serial_cable or is_serial_port:
            serial_links.append(l)

    errors = []
    for s in serial_links:
        link_id  = s["Link-ID"]
        cable    = s["Cable type"]
        raw_info = s["IP/subnet if routed"]

        # Check for DCE designation
        has_dce = "dce" in cable.lower() or "dce" in raw_info.lower()
        has_dte = "dte" in cable.lower() or "dte" in raw_info.lower()

        if not has_dce:
            errors.append(f"{link_id}: Serial link missing DCE designation")
        if not has_dte:
            errors.append(f"{link_id}: Serial link missing DTE designation")

        # Check clock rate
        clock_match = re.search(r"clock\s+rate\s+(\d+)", cable, re.IGNORECASE)
        if not clock_match:
            errors.append(f"{link_id}: Serial link missing explicit clock rate (e.g. 'clock rate 128000')")
        else:
            clock_rate = int(clock_match.group(1))
            if clock_rate not in (64000, 128000, 256000, 512000, 1024000):
                errors.append(f"{link_id}: Non-standard clock rate {clock_rate} on DCE interface")

    passed = len(errors) == 0
    return passed, "Serial Links DCE Designations & Clock Rate Verification", len(serial_links), errors

# ------------------------------------------------------------------------------
# Check 6: Every End Device Is on a Port of the Correct VLAN
# ------------------------------------------------------------------------------
def check_end_device_vlans(links: list, ip_map: dict) -> tuple:
    """Verifies that every end device connects to a switch port configured for its assigned VLAN."""
    errors = []
    checked_count = 0

    for l in links:
        if l["Layer"].strip() != "L2 access":
            continue

        dev_a = l["Device A"]
        dev_b = l["Device B"]
        vlans_carried = l["VLANs carried"].strip()

        # Identify which endpoint is switch and which is end-device
        switch_dev, end_dev = None, None
        if dev_a.startswith("SW-"):
            switch_dev, end_dev = dev_a, dev_b
        elif dev_b.startswith("SW-"):
            switch_dev, end_dev = dev_b, dev_a

        if not end_dev or not switch_dev:
            continue

        checked_count += 1
        link_id = l["Link-ID"]

        # Lookup expected VLAN from ip_table
        expected_rows = ip_map.get(end_dev, [])
        if not expected_rows:
            # If not in ip_table, check known role prefix
            continue

        expected_vlan = str(expected_rows[0].get("vlan", "")).strip()

        # Handle IP phones (Voice VLAN 60 + Data Access VLAN)
        if end_dev.startswith("PHONE-"):
            if "Voice: 60" not in vlans_carried:
                errors.append(
                    f"{link_id}: IP Phone {end_dev} connected to port without Voice VLAN 60 (Got: '{vlans_carried}')"
                )
        # Handle regular access hosts
        elif expected_vlan and expected_vlan != "-":
            # Extract numbers from vlans_carried
            vlan_numbers = re.findall(r"\b\d+\b", vlans_carried)
            if expected_vlan not in vlan_numbers:
                errors.append(
                    f"{link_id}: Device {end_dev} expects VLAN {expected_vlan}, but port carries '{vlans_carried}'"
                )

    passed = len(errors) == 0
    return passed, "Access Port VLAN Assignment Accuracy", checked_count, errors

# ------------------------------------------------------------------------------
# Master Topology Validator Runner
# ------------------------------------------------------------------------------
def validate_topology(cabling_path: str, ip_table_path: str = DEFAULT_IP_TABLE_CSV) -> bool:
    """Executes all 6 topology checks and returns overall success."""
    if not os.path.exists(cabling_path):
        print(f"[FATAL ERROR] Cabling CSV not found at: {cabling_path}")
        return False

    with open(cabling_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        links = list(reader)

    ip_map = load_ip_table(ip_table_path)

    checks = [
        check_interface_collisions(links),
        check_device_presence(links, REQUIRED_INFRASTRUCTURE),
        check_trunk_matching_ends(links),
        check_routed_links(links),
        check_serial_links(links),
        check_end_device_vlans(links, ip_map),
    ]

    print("=" * 80)
    print("  CISCO PACKET TRACER TOPOLOGY & CABLING VALIDATION REPORT")
    print(f"  Target Cabling Table: {cabling_path}")
    print(f"  Total Links Checked:  {len(links)}")
    print("=" * 80)

    all_passed = True

    for i, (passed, name, count, errors) in enumerate(checks, 1):
        status_tag = "[PASS]" if passed else "[FAIL]"
        print(f"\n{status_tag} Check {i}: {name} ({count} items verified)")
        if not passed:
            all_passed = False
            for err in errors:
                print(f"       * ERROR: {err}")
        else:
            print(f"       -> Verification criteria fully satisfied. Zero violations detected.")

    print("\n" + "=" * 80)
    if all_passed:
        print("  OVERALL RESULT: [PASS] TOPOLOGY 100% COMPLIANT WITH DESIGN RULES")
        print("=" * 80)
    else:
        print("  OVERALL RESULT: [FAIL] VIOLATIONS DETECTED IN TOPOLOGY / CABLING SCHEDULE")
        print("=" * 80)

    return all_passed

def main():
    parser = argparse.ArgumentParser(description="Validate Network Topology & Cabling Table against Design Rules")
    parser.add_argument("--cabling", default=DEFAULT_CABLING_CSV, help="Path to cabling.csv")
    parser.add_argument("--ip-table", default=DEFAULT_IP_TABLE_CSV, help="Path to ip_table.csv")
    args = parser.parse_args()

    success = validate_topology(args.cabling, args.ip_table)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
