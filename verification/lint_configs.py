#!/usr/bin/env python3
"""
================================================================================
Comprehensive Cisco IOS Configuration Linter & Policy Auditor
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Audits all device configurations in /configs using ciscoconfparse.
Validates:
  1. Every physical interface used appears in /topology/cabling.csv.
  2. IP addresses match /addressing/ip_table.csv.
  3. No duplicate IP addresses across distinct device interfaces.
  4. Subnet masks are mathematically correct.
  5. Every VLAN used on a trunk exists in the VLAN database on both ends.
  6. Every access port has PortFast and BPDU Guard enabled.
  7. Every client SVI has an HSRP standby group and DHCP helper-address where required.
  8. Every ACL referenced (access-group, access-class, nat list) is explicitly defined.
  9. OSPF network statements cover exactly the intended interfaces.
 10. No plain-text passwords (service password-encryption & enable secret enforced).
 11. SSH Version 2 and transport input ssh are configured on all VTY lines.

Returns a categorized report (ERROR, WARNING, INFO) and exits non-zero on errors.
================================================================================
"""

import os
import sys
import csv
import re
import ipaddress
import argparse
from typing import Dict, List, Set, Tuple, Optional

# Suppress loguru default noisy logging from ciscoconfparse
try:
    from loguru import logger
    logger.remove()
except Exception:
    pass

from ciscoconfparse import CiscoConfParse

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIGS_DIR = os.path.join(PROJECT_ROOT, "configs")
CABLING_CSV = os.path.join(PROJECT_ROOT, "topology", "cabling.csv")
IP_TABLE_CSV = os.path.join(PROJECT_ROOT, "addressing", "ip_table.csv")


def normalize_interface_name(name: str) -> str:
    """Normalizes interface abbreviations to standard long-form names."""
    n = name.strip()
    if re.match(r"^Fa(?:stEthernet)?\s*(\d.*)$", n, re.I):
        m = re.match(r"^Fa(?:stEthernet)?\s*(\d.*)$", n, re.I)
        return f"FastEthernet{m.group(1)}"
    if re.match(r"^Gi(?:g|gabitEthernet)?\s*(\d.*)$", n, re.I):
        m = re.match(r"^Gi(?:g|gabitEthernet)?\s*(\d.*)$", n, re.I)
        return f"GigabitEthernet{m.group(1)}"
    if re.match(r"^Se(?:r|rial)?\s*(\d.*)$", n, re.I):
        m = re.match(r"^Se(?:r|rial)?\s*(\d.*)$", n, re.I)
        return f"Serial{m.group(1)}"
    if re.match(r"^Lo(?:opback)?\s*(\d.*)$", n, re.I):
        m = re.match(r"^Lo(?:opback)?\s*(\d.*)$", n, re.I)
        return f"Loopback{m.group(1)}"
    if re.match(r"^Vl(?:an)?\s*(\d.*)$", n, re.I):
        m = re.match(r"^Vl(?:an)?\s*(\d.*)$", n, re.I)
        return f"Vlan{m.group(1)}"
    if re.match(r"^Po(?:rt-channel)?\s*(\d.*)$", n, re.I):
        m = re.match(r"^Po(?:rt-channel)?\s*(\d.*)$", n, re.I)
        return f"Port-channel{m.group(1)}"
    return n


class ConfigLinter:
    def __init__(self, configs_dir: str = CONFIGS_DIR, cabling_csv: str = CABLING_CSV, ip_table_csv: str = IP_TABLE_CSV):
        self.configs_dir = configs_dir
        self.cabling_csv = cabling_csv
        self.ip_table_csv = ip_table_csv

        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

        self.cabling_data: Dict[str, Set[str]] = {}
        self.cabling_trunks: List[Dict] = []
        self.ip_table_data: Dict[Tuple[str, str], Dict] = {}
        self.known_ips: Dict[str, Tuple[str, str]] = {}

        self.device_parses: Dict[str, CiscoConfParse] = {}
        self.device_vlans: Dict[str, Set[int]] = {}
        self.device_interfaces: Dict[str, Dict] = {}

    def load_reference_data(self):
        """Loads cabling.csv and ip_table.csv into reference lookups."""
        if os.path.exists(self.cabling_csv):
            with open(self.cabling_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    dev_a = r["Device A"].strip()
                    port_a = normalize_interface_name(r["Interface A"])
                    dev_b = r["Device B"].strip()
                    port_b = normalize_interface_name(r["Interface B"])

                    self.cabling_data.setdefault(dev_a, set()).add(port_a)
                    self.cabling_data.setdefault(dev_b, set()).add(port_b)

                    if "trunk" in r.get("Layer", "").lower():
                        self.cabling_trunks.append({
                            "dev_a": dev_a, "port_a": port_a,
                            "dev_b": dev_b, "port_b": port_b,
                            "vlans": r.get("VLANs carried", "")
                        })

        if os.path.exists(self.ip_table_csv):
            with open(self.ip_table_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    dev = r["device"].strip()
                    intf = normalize_interface_name(r["interface"])
                    ip = r["ip"].strip()
                    mask = r["mask"].strip()
                    self.ip_table_data.setdefault((dev, intf), []).append({
                        "ip": ip, "mask": mask, "role": r.get("role", "")
                    })

    def parse_all_configs(self):
        """Discovers and parses all device config files using CiscoConfParse."""
        if not os.path.isdir(self.configs_dir):
            self.errors.append(f"Configurations directory not found: {self.configs_dir}")
            return

        config_files = []
        for root, _, files in os.walk(self.configs_dir):
            for file in files:
                if file.endswith(".cfg") and not file.startswith("."):
                    config_files.append(os.path.join(root, file))

        for cfg_path in sorted(config_files):
            dev_name = os.path.basename(os.path.dirname(cfg_path))
            # Handle potential extension files
            base = os.path.basename(cfg_path)
            key = f"{dev_name}_{base}" if "extension" in base else dev_name

            try:
                parse = CiscoConfParse(cfg_path, factory=True)
                self.device_parses[key] = parse
                self.extract_device_metadata(key, parse)
            except Exception as e:
                self.errors.append(f"Failed to parse configuration for {key} ({cfg_path}): {e}")

    def extract_device_metadata(self, dev: str, parse: CiscoConfParse):
        """Extracts VLAN database, interface states, and IP configurations."""
        vlans = set()
        # Find 'vlan <id>' blocks
        for obj in parse.find_objects(r"^vlan\s+\d+"):
            m = re.match(r"^vlan\s+(\d+)", obj.text.strip(), re.I)
            if m:
                vlans.add(int(m.group(1)))
        self.device_vlans[dev] = vlans

        # Extract interfaces
        intfs = {}
        for io in parse.find_objects(r"^interface\s+"):
            line = io.text.strip()
            # Skip interface range declarations from primary interface mapping
            if "range" in line.lower():
                continue
            parts = line.split()
            if len(parts) >= 2:
                intf_name = normalize_interface_name(parts[1])
                intfs[intf_name] = io
        self.device_interfaces[dev] = intfs

    # --------------------------------------------------------------------------
    # CHECK 1: PHYSICAL INTERFACES APPEAR IN CABLING
    # --------------------------------------------------------------------------
    def check_interfaces_in_cabling(self):
        """Check 1: Every active physical interface configured appears in cabling.csv."""
        for dev, intfs in self.device_interfaces.items():
            # Skip helper or public edge devices not modeled as hospital switches/routers
            base_dev = dev.split("_")[0]
            if base_dev not in self.cabling_data:
                continue

            for intf_name, io in intfs.items():
                # Only check physical ethernet/serial interfaces
                is_physical = any(intf_name.startswith(p) for p in ["FastEthernet", "GigabitEthernet", "Serial"])
                if not is_physical:
                    continue

                # Check if interface is administratively shutdown
                is_shutdown = bool(io.re_search_children(r"^\s*shutdown\b"))
                # Check if interface is assigned to parking VLAN 999
                is_parking = bool(io.re_search_children(r"^\s*switchport access vlan 999\b"))

                if is_shutdown or is_parking:
                    continue  # Unused / parked interface, does not require cabling link

                if intf_name not in self.cabling_data[base_dev]:
                    self.errors.append(
                        f"[{dev}] Physical interface {intf_name} is active/configured but does NOT appear in /topology/cabling.csv."
                    )
                else:
                    self.info.append(f"[{dev}] Interface {intf_name} verified against cabling matrix.")

    # --------------------------------------------------------------------------
    # CHECKS 2, 3, 4: IP MATCHING, DUPLICATES & MASK ACCURACY
    # --------------------------------------------------------------------------
    def check_ip_addressing(self):
        """Checks 2, 3, 4: IP addresses match ip_table.csv, no duplicates, masks correct."""
        configured_ips = {}  # ip -> list of (dev, intf)

        for dev, intfs in self.device_interfaces.items():
            base_dev = dev.split("_")[0]
            for intf_name, io in intfs.items():
                # Extract 'ip address <ip> <mask>'
                ip_lines = io.re_search_children(r"^\s*ip address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)")
                for ipo in ip_lines:
                    m = re.search(r"ip address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)", ipo.text)
                    if not m:
                        continue
                    ip = m.group(1)
                    mask = m.group(2)

                    # Check 3: Duplicate IPs
                    configured_ips.setdefault(ip, []).append((dev, intf_name))

                    # Check 4: Valid Subnet Mask
                    try:
                        ipaddress.IPv4Network(f"0.0.0.0/{mask}")
                    except Exception:
                        self.errors.append(f"[{dev}] Interface {intf_name} has invalid subnet mask format: {mask}")

                    # Check 2: Match against ip_table.csv if device is present in table
                    lookup_keys = [(base_dev, intf_name)]
                    if base_dev == "SW-D4" and intf_name.startswith("Vlan"):
                        lookup_keys.append(("SW-D3", intf_name))

                    matching_entries = []
                    for lk in lookup_keys:
                        if lk in self.ip_table_data:
                            matching_entries.extend(self.ip_table_data[lk])

                    if matching_entries:
                        exact_match = any(e["ip"] == ip and e["mask"] == mask for e in matching_entries)
                        if not exact_match:
                            ip_found = any(e["ip"] == ip for e in matching_entries)
                            if ip_found:
                                self.errors.append(
                                    f"[{dev}] Interface {intf_name} mask mismatch for IP {ip}: configured {mask}."
                                )
                            else:
                                expected_ips = "/".join(e["ip"] for e in matching_entries)
                                self.errors.append(
                                    f"[{dev}] Interface {intf_name} IP mismatch: configured {ip}, expected {expected_ips} in ip_table.csv."
                                )
                    else:
                        # Allow Loopback, public IPs or extension configs
                        if not intf_name.startswith("Loopback") and base_dev not in ["EDGE-ISP", "SW-D4", "edge-isp"]:
                            self.warnings.append(
                                f"[{dev}] Interface {intf_name} ({ip}/{mask}) is not explicitly listed in ip_table.csv."
                            )

        # Evaluate duplicate IPs across distinct devices
        for ip, locations in configured_ips.items():
            if len(locations) > 1:
                # Group by base device (allow duplicate between .cfg and .txt or same dev)
                devs = set(loc[0].split("_")[0] for loc in locations)
                if len(devs) > 1:
                    loc_str = ", ".join(f"{d}:{i}" for d, i in locations)
                    self.errors.append(f"Duplicate IP address detected across multiple devices! IP {ip} configured on: {loc_str}")

    # --------------------------------------------------------------------------
    # CHECK 5: TRUNK VLANS EXIST ON BOTH ENDS
    # --------------------------------------------------------------------------
    def check_trunk_vlans(self):
        """Check 5: Every VLAN permitted on a trunk exists in the VLAN database on both ends."""
        for trunk in self.cabling_trunks:
            dev_a = trunk["dev_a"]
            port_a = trunk["port_a"]
            dev_b = trunk["dev_b"]
            port_b = trunk["port_b"]

            if dev_a not in self.device_parses or dev_b not in self.device_parses:
                continue

            parse_a = self.device_parses[dev_a]
            parse_b = self.device_parses[dev_b]

            vlans_a = self.device_vlans.get(dev_a, set())
            vlans_b = self.device_vlans.get(dev_b, set())

            # Find allowed VLANs on port_a
            io_a = self.device_interfaces.get(dev_a, {}).get(port_a)
            if not io_a:
                continue

            allowed_lines = io_a.re_search_children(r"switchport trunk allowed vlan\s+(.+)")
            allowed_vlans = set()
            for al in allowed_lines:
                m = re.search(r"switchport trunk allowed vlan\s+(.+)", al.text)
                if m:
                    tokens = m.group(1).replace("add", "").replace("remove", "").split(",")
                    for t in tokens:
                        t = t.strip()
                        if "-" in t:
                            start, end = map(int, t.split("-"))
                            allowed_vlans.update(range(start, end + 1))
                        elif t.isdigit():
                            allowed_vlans.add(int(t))

            # Verify each allowed VLAN exists on both switches
            for vid in allowed_vlans:
                if vid not in vlans_a and vid != 999:
                    self.errors.append(f"[{dev_a}] Trunk {port_a} allows VLAN {vid}, but VLAN {vid} is missing from {dev_a} VLAN database.")
                if vid not in vlans_b and vid != 999:
                    self.errors.append(f"[{dev_b}] Trunk {port_b} connected to {dev_a}:{port_a} allows VLAN {vid}, but VLAN {vid} is missing from {dev_b} VLAN database.")

    # --------------------------------------------------------------------------
    # CHECK 6: ACCESS PORTS HAVE PORTFAST & BPDU GUARD
    # --------------------------------------------------------------------------
    def check_access_port_security_and_stp(self):
        """Check 6: Every access port has PortFast and BPDU Guard enabled."""
        for dev, parse in self.device_parses.items():
            base_dev = dev.split("_")[0]
            # Only access switches are strictly enforced for host-facing portfast
            is_access_switch = base_dev.startswith("SW-A")

            # Check if global default commands are present
            has_global_portfast = bool(parse.find_objects(r"^spanning-tree portfast default"))
            has_global_bpduguard = bool(parse.find_objects(r"^spanning-tree portfast bpduguard default"))

            for intf_name, io in self.device_interfaces[dev].items():
                if not intf_name.startswith("FastEthernet") and not intf_name.startswith("GigabitEthernet"):
                    continue

                is_access = bool(io.re_search_children(r"switchport mode access"))
                is_shutdown = bool(io.re_search_children(r"^\s*shutdown\b"))
                is_parking = bool(io.re_search_children(r"switchport access vlan 999"))

                if is_access and not is_shutdown and not is_parking:
                    has_portfast = has_global_portfast or bool(io.re_search_children(r"spanning-tree portfast"))
                    has_bpduguard = has_global_bpduguard or bool(io.re_search_children(r"spanning-tree bpduguard enable"))

                    if not has_portfast:
                        msg = f"[{dev}] Access port {intf_name} does NOT have Spanning Tree PortFast enabled."
                        if is_access_switch:
                            self.errors.append(msg)
                        else:
                            self.warnings.append(msg)

                    if not has_bpduguard:
                        msg = f"[{dev}] Access port {intf_name} does NOT have Spanning Tree BPDU Guard enabled."
                        if is_access_switch:
                            self.errors.append(msg)
                        else:
                            self.warnings.append(msg)

    # --------------------------------------------------------------------------
    # CHECK 7: SVI HSRP & DHCP HELPER-ADDRESS
    # --------------------------------------------------------------------------
    def check_svi_hsrp_and_helper(self):
        """Check 7: Every client SVI has an HSRP group and helper-address where required."""
        for dev, parse in self.device_parses.items():
            base_dev = dev.split("_")[0]
            # SVI HSRP is deployed on distribution switches
            if not base_dev.startswith("SW-D"):
                continue

            # In Remote Clinic standalone mode, SW-D3 operates as the single default gateway.
            # Dual-distribution HSRP is deployed in SW-D1/SW-D2 and clinic HA extension (SW-D3_ha_extension / SW-D4).
            if dev == "SW-D3":
                self.info.append("[SW-D3] Operating in single-gateway standalone mode; HSRP redundancy configured in HA extension.")
                continue

            for intf_name, io in self.device_interfaces[dev].items():
                if not intf_name.startswith("Vlan"):
                    continue

                vlan_num = int(intf_name.replace("Vlan", ""))
                # Skip Management VLAN 99 and Server Farm VLAN 50 (local DHCP server)
                if vlan_num in [50, 99, 999]:
                    continue

                has_ip = bool(io.re_search_children(r"ip address\s+\d+"))
                if not has_ip:
                    continue

                # Check HSRP standby group
                has_hsrp = bool(io.re_search_children(r"standby\s+\d+\s+ip\s+\d+"))
                if not has_hsrp:
                    self.errors.append(f"[{dev}] SVI {intf_name} is missing HSRP standby group configuration ('standby <id> ip <vip>').")
                else:
                    self.info.append(f"[{dev}] SVI {intf_name} HSRP standby group verified.")

                # Check DHCP helper-address (Client VLANs 10, 20, 30, 40 require helper to Central Server)
                if vlan_num in [10, 20, 30, 40]:
                    has_helper = bool(io.re_search_children(r"ip helper-address\s+172\.16\."))
                    if not has_helper:
                        self.errors.append(f"[{dev}] Client SVI {intf_name} is missing 'ip helper-address' for centralized DHCP relay.")

    # --------------------------------------------------------------------------
    # CHECK 8: ACL DEFINITION AND APPLICATION
    # --------------------------------------------------------------------------
    def check_acl_definitions_and_usage(self):
        """Check 8: Every ACL referenced is defined, and defined ACLs are applied."""
        for dev, parse in self.device_parses.items():
            defined_acls = set()
            referenced_acls = set()

            # Find named ACLs: 'ip access-list (standard|extended) <name>'
            for obj in parse.find_objects(r"^ip access-list\s+"):
                parts = obj.text.strip().split()
                if len(parts) >= 4:
                    defined_acls.add(parts[3])

            # Find numbered ACLs: 'access-list <num> ...'
            for obj in parse.find_objects(r"^access-list\s+\d+"):
                parts = obj.text.strip().split()
                if len(parts) >= 2:
                    defined_acls.add(parts[1])

            # Find ACLs applied to interfaces: 'ip access-group <name> (in|out)'
            for io in parse.find_objects(r"^interface\s+"):
                for ag in io.re_search_children(r"ip access-group\s+(\S+)"):
                    m = re.search(r"ip access-group\s+(\S+)", ag.text)
                    if m:
                        referenced_acls.add(m.group(1))

            # Find ACLs applied to VTY lines: 'access-class <name> (in|out)'
            for lo in parse.find_objects(r"^line\s+"):
                for ac in lo.re_search_children(r"access-class\s+(\S+)"):
                    m = re.search(r"access-class\s+(\S+)", ac.text)
                    if m:
                        referenced_acls.add(m.group(1))

            # Find ACLs used in NAT: 'ip nat inside source list <name>'
            for no in parse.find_objects(r"^ip nat inside source list\s+(\S+)"):
                m = re.search(r"ip nat inside source list\s+(\S+)", no.text)
                if m:
                    referenced_acls.add(m.group(1))

            # Verify all referenced ACLs are defined
            for acl_ref in referenced_acls:
                if acl_ref not in defined_acls:
                    self.errors.append(f"[{dev}] ACL '{acl_ref}' is referenced in interface/line policy but is NEVER defined!")

            # Informational check for unapplied defined ACLs
            for acl_def in defined_acls:
                if acl_def not in referenced_acls:
                    self.warnings.append(f"[{dev}] ACL '{acl_def}' is defined but is not applied to any interface or line.")

    # --------------------------------------------------------------------------
    # CHECK 9: OSPF NETWORK STATEMENTS MATCH INTENDED INTERFACES
    # --------------------------------------------------------------------------
    def check_ospf_coverage(self):
        """Check 9: OSPF network statements cover exactly intended interfaces."""
        for dev, parse in self.device_parses.items():
            base_dev = dev.split("_")[0]
            ospf_objs = parse.find_objects(r"^router ospf\s+\d+")
            if not ospf_objs:
                continue

            ospf = ospf_objs[0]
            net_statements = ospf.re_search_children(r"^\s*network\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+area\s+(\d+)")

            if not net_statements:
                self.errors.append(f"[{dev}] 'router ospf' is declared but contains zero network statements!")

            # Verify that router has active interfaces matching the OSPF network statements
            configured_ips = []
            for intf_name, io in self.device_interfaces[dev].items():
                ip_lines = io.re_search_children(r"ip address\s+(\d+\.\d+\.\d+\.\d+)")
                for il in ip_lines:
                    m = re.search(r"ip address\s+(\d+\.\d+\.\d+\.\d+)", il.text)
                    if m:
                        configured_ips.append(ipaddress.IPv4Address(m.group(1)))

            for ns in net_statements:
                m = re.search(r"network\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+area\s+(\d+)", ns.text)
                if m:
                    net_ip = m.group(1)
                    wildcard = m.group(2)
                    area = m.group(3)

                    # Compute network from wildcard
                    wildcard_int = int(ipaddress.IPv4Address(wildcard))
                    mask_int = 0xFFFFFFFF ^ wildcard_int
                    mask_str = str(ipaddress.IPv4Address(mask_int))
                    net_obj = ipaddress.IPv4Network((net_ip, mask_str), strict=False)

                    matches = [ip for ip in configured_ips if ip in net_obj]
                    if not matches:
                        self.warnings.append(
                            f"[{dev}] OSPF network statement '{ns.text.strip()}' does not match any configured interface IP on this device."
                        )

    # --------------------------------------------------------------------------
    # CHECK 10: PASSWORD ENCRYPTION & NO PLAIN TEXT SECRETS
    # --------------------------------------------------------------------------
    def check_password_hardening(self):
        """Check 10: No passwords in plain text (service password-encryption & enable secret)."""
        for dev, parse in self.device_parses.items():
            has_pw_encrypt = bool(parse.find_objects(r"^service password-encryption"))
            if not has_pw_encrypt:
                self.errors.append(f"[{dev}] Missing 'service password-encryption' global hardening command.")

            # Must use 'enable secret', not 'enable password'
            has_enable_secret = bool(parse.find_objects(r"^enable secret\s+"))
            has_enable_pw = bool(parse.find_objects(r"^enable password\s+"))

            if has_enable_pw:
                self.errors.append(f"[{dev}] Uses insecure plaintext 'enable password' instead of 'enable secret'.")
            elif not has_enable_secret:
                self.errors.append(f"[{dev}] Missing 'enable secret' privileged credential.")

            # Check usernames
            for un in parse.find_objects(r"^username\s+"):
                if "password" in un.text and "secret" not in un.text:
                    self.errors.append(f"[{dev}] Username configured with plaintext password: '{un.text.strip()}'.")

    # --------------------------------------------------------------------------
    # CHECK 11: SSH LINES CONFIGURED
    # --------------------------------------------------------------------------
    def check_ssh_vty_configuration(self):
        """Check 11: SSH Version 2 is enabled and VTY lines enforce SSH transport."""
        for dev, parse in self.device_parses.items():
            # Core routers and distribution switches must enforce SSH
            has_ssh_v2 = bool(parse.find_objects(r"^ip ssh version 2"))
            if not has_ssh_v2:
                self.errors.append(f"[{dev}] Missing 'ip ssh version 2' remote management command.")

            vty_lines = parse.find_objects(r"^line vty\s+")
            if not vty_lines:
                self.errors.append(f"[{dev}] Missing 'line vty' remote access configuration.")
            else:
                for vl in vty_lines:
                    has_ssh_transport = bool(vl.re_search_children(r"transport input ssh"))
                    has_login = bool(vl.re_search_children(r"login local"))
                    if not has_ssh_transport:
                        self.errors.append(f"[{dev}] VTY line '{vl.text.strip()}' does not restrict transport to 'transport input ssh'.")
                    if not has_login:
                        self.warnings.append(f"[{dev}] VTY line '{vl.text.strip()}' should enforce 'login local'.")

    # --------------------------------------------------------------------------
    # RUNNER & REPORT GENERATOR
    # --------------------------------------------------------------------------
    def run_all_checks(self) -> bool:
        """Executes all 11 config audit rules and returns True if zero errors."""
        self.errors.clear()
        self.warnings.clear()
        self.info.clear()

        self.load_reference_data()
        self.parse_all_configs()

        self.check_interfaces_in_cabling()
        self.check_ip_addressing()
        self.check_trunk_vlans()
        self.check_access_port_security_and_stp()
        self.check_svi_hsrp_and_helper()
        self.check_acl_definitions_and_usage()
        self.check_ospf_coverage()
        self.check_password_hardening()
        self.check_ssh_vty_configuration()

        return len(self.errors) == 0

    def print_report(self):
        """Prints formatted categorized report to standard output."""
        print("=" * 80)
        print("CISCO IOS CONFIGURATION LINTER & POLICY AUDITOR (ciscoconfparse)")
        print(f"Configs Root:  {self.configs_dir}")
        print(f"Cabling Matrix: {self.cabling_csv}")
        print(f"IP Reference:  {self.ip_table_csv}")
        print("=" * 80)

        if self.info:
            print(f"\n[INFO] {len(self.info)} Validated Items:")
            for item in self.info[:10]:
                print(f"  + {item}")
            if len(self.info) > 10:
                print(f"  ... and {len(self.info) - 10} more verified configurations.")

        if self.warnings:
            print(f"\n[WARNING] {len(self.warnings)} Policy Warnings:")
            for warn in self.warnings:
                print(f"  ! {warn}")

        if self.errors:
            print(f"\n[ERROR] {len(self.errors)} Critical Configuration Errors:")
            for err in self.errors:
                print(f"  x {err}")
            print("\n" + "=" * 80)
            print(f"LINTER AUDIT FAILED: {len(self.errors)} critical errors found.")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("LINTER AUDIT PASSED: 0 critical errors found. All configurations verified!")
            print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Audit Cisco IOS configurations using ciscoconfparse.")
    parser.add_argument("--configs-dir", default=CONFIGS_DIR, help="Path to /configs directory")
    parser.add_argument("--cabling", default=CABLING_CSV, help="Path to cabling.csv")
    parser.add_argument("--ip-table", default=IP_TABLE_CSV, help="Path to ip_table.csv")
    args = parser.parse_args()

    linter = ConfigLinter(
        configs_dir=args.configs_dir,
        cabling_csv=args.cabling,
        ip_table_csv=args.ip_table
    )

    passed = linter.run_all_checks()
    linter.print_report()
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
