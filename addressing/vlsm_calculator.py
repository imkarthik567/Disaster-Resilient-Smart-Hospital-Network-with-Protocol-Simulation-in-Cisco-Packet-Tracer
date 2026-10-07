#!/usr/bin/env python3
"""
================================================================================
VLSM Addressing Plan Calculator & Table Generator
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Computes all subnet allocations from 172.16.0.0/16 using VLSM rules.
Generates:
  - addressing_table.csv
  - addressing_table.md
  - vlsm_allocations.json
"""

import csv
import ipaddress
import json
import math
import os
import sys

def required_prefix(hosts: int) -> int:
    """Return the smallest prefix length accommodating `hosts` usable addresses."""
    if hosts <= 1:
        return 32          # Host / Loopback
    if hosts <= 2:
        return 30          # Point-to-point /30
    bits_needed = math.ceil(math.log2(hosts + 2))  # +2 for network & broadcast
    return 32 - bits_needed

def allocate_vlsm(base_cidr: str, requirements: list[dict]) -> list[dict]:
    """Allocates subnets from base_cidr using largest-first VLSM sorting."""
    base = ipaddress.IPv4Network(base_cidr, strict=True)
    reqs = sorted(requirements, key=lambda r: r["min_hosts"], reverse=True)

    current_addr = int(base.network_address)
    allocations = []

    for req in reqs:
        prefix = required_prefix(req["min_hosts"])
        subnet_size = 2 ** (32 - prefix)

        # Align to subnet boundary
        if current_addr % subnet_size != 0:
            current_addr = ((current_addr // subnet_size) + 1) * subnet_size

        network = ipaddress.IPv4Network(f"{ipaddress.IPv4Address(current_addr)}/{prefix}", strict=True)

        if not network.subnet_of(base):
            raise ValueError(f"Subnet {network} for '{req['name']}' exceeds {base_cidr}!")

        if prefix == 32:
            first = last = gw = str(network.network_address)
            bcast = "N/A"
            usable = 1
        elif prefix >= 31:
            hosts = list(network.hosts())
            first, last = str(hosts[0]), str(hosts[-1])
            bcast = str(network.broadcast_address)
            gw = str(hosts[0])
            usable = len(hosts)
        else:
            first = str(network.network_address + 1)
            last  = str(network.broadcast_address - 1)
            bcast = str(network.broadcast_address)
            gw    = str(network.network_address + 1)
            usable = subnet_size - 2

        allocations.append({
            "name":               req["name"],
            "site":               req["site"],
            "vlan_id":            req["vlan_id"],
            "description":        req["description"],
            "network":            str(network.network_address),
            "prefix":             prefix,
            "cidr":               str(network),
            "subnet_mask":        str(network.netmask),
            "wildcard_mask":      str(network.hostmask),
            "broadcast":          bcast,
            "gateway":            gw,
            "usable_first":       first,
            "usable_last":        last,
            "usable_hosts":       usable,
            "min_hosts_required": req["min_hosts"],
        })

        current_addr += subnet_size

    return allocations

# Additional /30 transit links for distribution-to-core interconnection
TRANSIT_LINKS = [
    {
        "name": "Transit-SW-D1-R1",
        "site": "Main Hospital",
        "vlan_id": 0,
        "description": "Routed /30 point-to-point link (SW-D1 Gi0/2 <-> R1 Gi0/0)",
        "network": "172.16.5.0",
        "prefix": 30,
        "cidr": "172.16.5.0/30",
        "subnet_mask": "255.255.255.252",
        "wildcard_mask": "0.0.0.3",
        "broadcast": "172.16.5.3",
        "gateway": "172.16.5.1",
        "usable_first": "172.16.5.1",
        "usable_last": "172.16.5.2",
        "usable_hosts": 2,
        "min_hosts_required": 2
    },
    {
        "name": "Transit-SW-D2-R1",
        "site": "Main Hospital",
        "vlan_id": 0,
        "description": "Routed /30 point-to-point link (SW-D2 Gi0/2 <-> R1 Gi0/1)",
        "network": "172.16.5.4",
        "prefix": 30,
        "cidr": "172.16.5.4/30",
        "subnet_mask": "255.255.255.252",
        "wildcard_mask": "0.0.0.3",
        "broadcast": "172.16.5.7",
        "gateway": "172.16.5.5",
        "usable_first": "172.16.5.5",
        "usable_last": "172.16.5.6",
        "usable_hosts": 2,
        "min_hosts_required": 2
    },
    {
        "name": "Transit-SW-D3-R2",
        "site": "Remote Clinic",
        "vlan_id": 0,
        "description": "Routed /30 point-to-point link (SW-D3 Gi0/1 <-> R2 Gi0/0)",
        "network": "172.16.5.8",
        "prefix": 30,
        "cidr": "172.16.5.8/30",
        "subnet_mask": "255.255.255.252",
        "wildcard_mask": "0.0.0.3",
        "broadcast": "172.16.5.11",
        "gateway": "172.16.5.9",
        "usable_first": "172.16.5.9",
        "usable_last": "172.16.5.10",
        "usable_hosts": 2,
        "min_hosts_required": 2
    }
]

REQUIREMENTS = [
    # Main Hospital Campus
    {"name": "Main-VLAN40-Guest",     "site": "Main Hospital",  "vlan_id": 40,  "min_hosts": 500, "description": "Guest Wi-Fi - untrusted visitor devices"},
    {"name": "Main-VLAN30-Admin",     "site": "Main Hospital",  "vlan_id": 30,  "min_hosts": 200, "description": "Administration - staff workstations"},
    {"name": "Main-VLAN60-Voice",     "site": "Main Hospital",  "vlan_id": 60,  "min_hosts": 100, "description": "Voice - IP phones / VoIP"},
    {"name": "Main-VLAN10-ICU",       "site": "Main Hospital",  "vlan_id": 10,  "min_hosts": 50,  "description": "ICU - bedside monitors, telemetry SBCs"},
    {"name": "Main-VLAN20-Surgery",   "site": "Main Hospital",  "vlan_id": 20,  "min_hosts": 40,  "description": "Surgery - operating theatre devices"},
    {"name": "Main-VLAN50-Servers",   "site": "Main Hospital",  "vlan_id": 50,  "min_hosts": 20,  "description": "Server Farm - DNS, HTTP, DHCP, PACS"},
    {"name": "Main-VLAN99-Mgmt",      "site": "Main Hospital",  "vlan_id": 99,  "min_hosts": 20,  "description": "Management - switch/AP out-of-band"},

    # Remote Clinic
    {"name": "Remote-VLAN10-Clinical", "site": "Remote Clinic", "vlan_id": 10,  "min_hosts": 20,  "description": "Clinical - patient monitoring"},
    {"name": "Remote-VLAN30-Admin",    "site": "Remote Clinic", "vlan_id": 30,  "min_hosts": 20,  "description": "Administration - clinic staff PCs"},
    {"name": "Remote-VLAN60-Voice",    "site": "Remote Clinic", "vlan_id": 60,  "min_hosts": 15,  "description": "Voice - IP phones"},
    {"name": "Remote-VLAN50-Servers",  "site": "Remote Clinic", "vlan_id": 50,  "min_hosts": 10,  "description": "Local server cache"},
    {"name": "Remote-VLAN99-Mgmt",     "site": "Remote Clinic", "vlan_id": 99,  "min_hosts": 10,  "description": "Management - switch/AP OOB"},

    # WAN Point-to-Point
    {"name": "WAN-Primary-Serial",     "site": "WAN",           "vlan_id": 0,   "min_hosts": 2,   "description": "Primary WAN - R1 <-> R2 Serial (OSPF)"},
    {"name": "WAN-Secondary",          "site": "WAN",           "vlan_id": 0,   "min_hosts": 2,   "description": "Secondary WAN - R1 <-> R2 Backup (EIGRP)"},

    # Loopback Router-IDs
    {"name": "R1-Loopback0",           "site": "Main Hospital", "vlan_id": 0,   "min_hosts": 1,   "description": "R1 OSPF Router-ID"},
    {"name": "R2-Loopback0",           "site": "Remote Clinic", "vlan_id": 0,   "min_hosts": 1,   "description": "R2 OSPF Router-ID"},
]

def generate_csv(allocations, filepath):
    fieldnames = [
        "name", "site", "vlan_id", "cidr", "subnet_mask", "wildcard_mask",
        "gateway", "usable_first", "usable_last", "usable_hosts", "description"
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for a in allocations:
            writer.writerow(a)

def generate_markdown(allocations, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# VLSM Addressing Plan Table\n\n")
        f.write("**Base Block:** `172.16.0.0/16`  \n")
        f.write("**Automated Generation:** Generated by `addressing/vlsm_calculator.py`\n\n")
        f.write("| Subnet Name | Site | VLAN | Network CIDR | Subnet Mask | Wildcard Mask | Gateway | Usable Range | Usable Hosts |\n")
        f.write("| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- | :---: |\n")
        for a in allocations:
            vlan_str = str(a["vlan_id"]) if a["vlan_id"] > 0 else "-"
            f.write(f"| **{a['name']}** | {a['site']} | {vlan_str} | `{a['cidr']}` | `{a['subnet_mask']}` | `{a['wildcard_mask']}` | `{a['gateway']}` | `{a['usable_first']} - {a['usable_last']}` | {a['usable_hosts']} |\n")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    addressing_dir = os.path.join(project_root, "addressing")
    os.makedirs(addressing_dir, exist_ok=True)

    allocations = allocate_vlsm("172.16.0.0/16", REQUIREMENTS)
    # Append transit links
    all_allocations = allocations + TRANSIT_LINKS

    json_path = os.path.join(addressing_dir, "vlsm_allocations.json")
    csv_path  = os.path.join(addressing_dir, "addressing_table.csv")
    md_path   = os.path.join(addressing_dir, "addressing_table.md")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_allocations, f, indent=2)

    generate_csv(all_allocations, csv_path)
    generate_markdown(all_allocations, md_path)

    print(f"[OK] Generated {json_path}")
    print(f"[OK] Generated {csv_path}")
    print(f"[OK] Generated {md_path}")

if __name__ == "__main__":
    main()
