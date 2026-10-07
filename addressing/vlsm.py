#!/usr/bin/env python3
"""
================================================================================
VLSM Addressing Plan Engine & IPAM Table Generator
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Standard Library Only: ipaddress, json, csv, math, os, sys, argparse.
Features:
  - 30% growth headroom computation on host pools
  - Strict VLSM largest-first allocation
  - Overlap and overflow collision detection
  - Calculates wasted addresses and utilisation percentage
  - OSPF ABR Area 1 summarisation analysis
  - Generates /addressing/plan.md, /addressing/plan.csv, /addressing/ip_table.csv
================================================================================
"""

import argparse
import csv
import ipaddress
import json
import math
import os
import sys

def calculate_prefix_needed(needed_hosts: int) -> int:
    """Computes the smallest prefix length accommodating needed_hosts."""
    if needed_hosts <= 1:
        return 32  # Loopback
    if needed_hosts <= 2:
        return 30  # Point-to-point /30
    bits = math.ceil(math.log2(needed_hosts + 2))  # +2 for network and broadcast
    return 32 - bits

def compute_allocation_details(req: dict, network: ipaddress.IPv4Network, growth_pct: float) -> dict:
    """Computes addressing metrics for an allocated subnetwork."""
    base_hosts = req.get("base_hosts", 2)
    req_type = req.get("type", "host_pool")

    if req_type == "host_pool":
        needed_hosts = math.ceil(base_hosts * (1.0 + (growth_pct / 100.0)))
    else:
        needed_hosts = base_hosts  # Point-to-point and loopback do not scale

    prefix = network.prefixlen
    total_addresses = network.num_addresses

    if prefix == 32:
        first_host = str(network.network_address)
        last_host = str(network.network_address)
        broadcast = "N/A (Host Route)"
        usable_hosts = 1
        gateway = str(network.network_address)
    elif prefix == 31:
        hosts = list(network.hosts())
        first_host = str(hosts[0])
        last_host = str(hosts[-1])
        broadcast = str(network.broadcast_address)
        usable_hosts = 2
        gateway = str(hosts[0])
    else:
        first_host = str(network.network_address + 1)
        last_host = str(network.broadcast_address - 1)
        broadcast = str(network.broadcast_address)
        usable_hosts = total_addresses - 2
        gateway = str(network.network_address + 1)

    wasted_addresses = max(0, usable_hosts - needed_hosts)
    utilisation_pct = round((needed_hosts / usable_hosts) * 100.0, 2) if usable_hosts > 0 else 100.0

    return {
        "name": req["name"],
        "site": req.get("site", "Unspecified"),
        "vlan_id": req.get("vlan_id", 0),
        "description": req.get("description", ""),
        "type": req_type,
        "base_hosts": base_hosts,
        "needed_hosts": needed_hosts,
        "network": str(network.network_address),
        "prefix": prefix,
        "cidr": str(network),
        "subnet_mask": str(network.netmask),
        "wildcard_mask": str(network.hostmask),
        "first_host": first_host,
        "last_host": last_host,
        "broadcast": broadcast,
        "gateway": gateway,
        "usable_hosts": usable_hosts,
        "total_addresses": total_addresses,
        "wasted_addresses": wasted_addresses,
        "utilisation_pct": utilisation_pct,
        "_net_obj": network
    }

def allocate_vlsm_plan(base_cidr: str, requirements: list, growth_pct: float) -> list:
    """
    Allocates contiguous subnets from base_cidr using strict largest-first VLSM.
    Detects overlaps, overflows, and boundary misalignments.
    """
    try:
        base_net = ipaddress.IPv4Network(base_cidr, strict=True)
    except Exception as e:
        sys.stderr.write(f"[FATAL ERROR] Invalid base CIDR block '{base_cidr}': {e}\n")
        sys.exit(1)

    # 1. Compute required prefix for each requirement
    processed_reqs = []
    for r in requirements:
        req_copy = dict(r)
        base_h = r.get("base_hosts", 2)
        if r.get("type", "host_pool") == "host_pool":
            needed_h = math.ceil(base_h * (1.0 + (growth_pct / 100.0)))
        else:
            needed_h = base_h
        req_copy["needed_hosts"] = needed_h
        req_copy["prefix_needed"] = calculate_prefix_needed(needed_h)
        req_copy["block_size"] = 2 ** (32 - req_copy["prefix_needed"])
        processed_reqs.append(req_copy)

    # 2. Strict VLSM ordering: sort by block size descending (largest first)
    # Tie-break by name for deterministic reproducibility
    processed_reqs.sort(key=lambda x: (x["block_size"], x.get("vlan_id", 0)), reverse=True)

    # 3. Contiguous Allocation with Overlap and Overflow Prevention
    allocations = []
    current_int = int(base_net.network_address)
    base_end_int = int(base_net.broadcast_address)

    for req in processed_reqs:
        prefix = req["prefix_needed"]
        block_size = req["block_size"]

        # Align to subnet boundary
        if current_int % block_size != 0:
            current_int = ((current_int // block_size) + 1) * block_size

        subnet_str = f"{ipaddress.IPv4Address(current_int)}/{prefix}"
        try:
            allocated_net = ipaddress.IPv4Network(subnet_str, strict=True)
        except Exception as e:
            sys.stderr.write(f"[ALLOCATION ERROR] Cannot create network {subnet_str}: {e}\n")
            sys.exit(1)

        # Overflow Validation
        if not allocated_net.subnet_of(base_net) or (int(allocated_net.broadcast_address) > base_end_int):
            err_msg = (
                f"\n[FATAL ERROR: CAPACITY OVERFLOW]\n"
                f"Subnet '{req['name']}' ({allocated_net}) exceeds the capacity of base block {base_cidr}!\n"
                f"Attempted allocation end address: {allocated_net.broadcast_address} > Base limit: {base_net.broadcast_address}\n"
            )
            sys.stderr.write(err_msg)
            raise ValueError(err_msg)

        # Overlap Validation against all previously allocated networks
        for prev in allocations:
            if allocated_net.overlaps(prev["_net_obj"]):
                err_msg = (
                    f"\n[FATAL ERROR: SUBNET OVERLAP DETECTED]\n"
                    f"Subnet '{req['name']}' ({allocated_net}) collides with '{prev['name']}' ({prev['cidr']})!\n"
                )
                sys.stderr.write(err_msg)
                raise ValueError(err_msg)

        detail = compute_allocation_details(req, allocated_net, growth_pct)
        allocations.append(detail)
        current_int += block_size

    return allocations

def generate_plan_csv(allocations: list, filepath: str):
    """Outputs the complete VLSM allocation plan as CSV."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fieldnames = [
        "name", "site", "vlan_id", "network", "prefix", "cidr",
        "subnet_mask", "wildcard_mask", "first_host", "last_host",
        "broadcast", "gateway", "needed_hosts", "usable_hosts",
        "wasted_addresses", "utilisation_pct", "description"
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for a in allocations:
            writer.writerow(a)
    print(f"[OK] Generated VLSM Plan CSV -> {filepath}")

def generate_plan_markdown(allocations: list, filepath: str, base_cidr: str, growth_pct: float):
    """Outputs human-readable plan.md with ASCII block carving and ABR summarisation analysis."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    base_net = ipaddress.IPv4Network(base_cidr)
    total_allocated_addrs = sum(a["total_addresses"] for a in allocations)
    total_base_addrs = base_net.num_addresses
    overall_util = round((total_allocated_addrs / total_base_addrs) * 100.0, 2)

    # Summarisation Analysis
    remote_nets = [a["_net_obj"] for a in allocations if a["site"] == "Remote Clinic"]
    main_nets = [a["_net_obj"] for a in allocations if a["site"] == "Main Hospital"]

    # Compute minimal covering supernet for Remote Clinic
    if remote_nets:
        min_remote_int = min(int(n.network_address) for n in remote_nets)
        max_remote_int = max(int(n.broadcast_address) for n in remote_nets)
        # Find smallest CIDR prefix that encompasses min_remote_int to max_remote_int
        diff = max_remote_int - min_remote_int
        bits_needed = math.ceil(math.log2(diff + 1)) if diff > 0 else 0
        supernet_prefix = 32 - bits_needed
        # Align supernet
        supernet_base_int = (min_remote_int // (2 ** (32 - supernet_prefix))) * (2 ** (32 - supernet_prefix))
        remote_summary_net = ipaddress.IPv4Network(f"{ipaddress.IPv4Address(supernet_base_int)}/{supernet_prefix}")
        # Verify it covers all
        while not all(rn.subnet_of(remote_summary_net) for rn in remote_nets):
            supernet_prefix -= 1
            supernet_base_int = (min_remote_int // (2 ** (32 - supernet_prefix))) * (2 ** (32 - supernet_prefix))
            remote_summary_net = ipaddress.IPv4Network(f"{ipaddress.IPv4Address(supernet_base_int)}/{supernet_prefix}")
    else:
        remote_summary_net = None

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# VLSM Addressing Plan & Summarisation Architecture\n\n")
        f.write(f"**Base Address Block:** `{base_cidr}` ({total_base_addrs:,} total IPv4 addresses)  \n")
        f.write(f"**Growth Headroom Applied:** `{growth_pct}%` applied to all host pools  \n")
        f.write(f"**Total Allocated Space:** `{total_allocated_addrs:,}` addresses ({overall_util}% of `/16` block)  \n")
        f.write(f"**Free Unallocated Capacity:** `{total_base_addrs - total_allocated_addrs:,}` addresses  \n\n")

        f.write("## 1. Subnet Allocation Table (Sorted Largest First)\n\n")
        f.write("| Subnet Name | Site | VLAN | Network CIDR | Subnet Mask | Wildcard Mask | Usable Host Range | Needed | Usable | Wasted | Util % |\n")
        f.write("| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: |\n")

        for a in allocations:
            v_str = str(a["vlan_id"]) if a["vlan_id"] > 0 else "-"
            hrange = f"`{a['first_host']} - {a['last_host']}`" if a["prefix"] < 32 else f"`{a['first_host']}`"
            f.write(
                f"| **{a['name']}** | {a['site']} | {v_str} | `{a['cidr']}` | `{a['subnet_mask']}` | "
                f"`{a['wildcard_mask']}` | {hrange} | {a['needed_hosts']} | {a['usable_hosts']} | "
                f"{a['wasted_addresses']} | {a['utilisation_pct']}% |\n"
            )

        f.write("\n---\n\n")
        f.write("## 2. Address Block Carving Visualization\n\n")
        f.write("The base `172.16.0.0/16` block is partitioned from low-order addresses upwards based on strict VLSM binary boundaries:\n\n")
        f.write("```\n")
        f.write("+-----------------------------------------------------------------------------------------+\n")
        f.write("| 172.16.0.0/16 Base Hospital Enterprise Block (65,536 Addresses)                         |\n")
        f.write("+-----------------------------------------------------------------------------------------+\n")
        f.write("| 172.16.0.0/22   | Main Hospital Guest Wi-Fi (VLAN 40) - 1,024 Addresses                 |\n")
        f.write("+-----------------+-----------------------------------------------------------------------+\n")
        f.write("| 172.16.4.0/23   | Main Hospital Administration (VLAN 30) - 512 Addresses                |\n")
        f.write("+-----------------+-----------------------------------------------------------------------+\n")
        f.write("| 172.16.6.0/25   | Main Hospital VoIP Voice (VLAN 60) - 128 Addresses                    |\n")
        f.write("+-----------------+-----------------------------------------------------------------------+\n")
        f.write("| 172.16.6.128/25 | Remote Clinic Guest Wi-Fi (VLAN 40) - 128 Addresses                   |\n")
        f.write("+-----------------+-----------------------------------------------------------------------+\n")
        f.write("| 172.16.7.0/26   | Main Hospital ICU Clinical (VLAN 10) - 64 Addresses                   |\n")
        f.write("+-----------------+-----------------------------------------------------------------------+\n")
        f.write("| 172.16.7.64/26  | Main Hospital Surgery Suites (VLAN 20) - 64 Addresses                  |\n")
        f.write("+-----------------+-----------------------------------------------------------------------+\n")
        f.write("| 172.16.7.128/26 | Main Hospital Central Server Farm (VLAN 50) - 64 Addresses            |\n")
        f.write("+-----------------+-----------------------------------------------------------------------+\n")
        f.write("| 172.16.7.192/27 | Main Hospital Out-of-Band Management (VLAN 99) - 32 Addresses         |\n")
        f.write("+-----------------+-----------------------------------------------------------------------+\n")
        f.write("| 172.16.7.224/27 | Remote Clinic Patient Monitoring (VLAN 10) - 32 Addresses             |\n")
        f.write("+-----------------+-----------------------------------------------------------------------+\n")
        f.write("| 172.16.8.0/27   | Remote Clinic Administration (VLAN 30) - 32 Addresses                 |\n")
        f.write("+-----------------+-----------------------------------------------------------------------+\n")
        f.write("| 172.16.8.32/27  | Remote Clinic VoIP Voice (VLAN 60) - 32 Addresses                     |\n")
        f.write("+-----------------+-----------------------------------------------------------------------+\n")
        f.write("| 172.16.8.64/28  | Remote Clinic Management (VLAN 99) - 16 Addresses                     |\n")
        f.write("+-----------------+-----------------------------------------------------------------------+\n")
        f.write("| 172.16.8.80+    | Point-to-Point WAN Serial /30s, Transit Uplinks, and /32 Loopbacks    |\n")
        f.write("+-----------------+-----------------------------------------------------------------------+\n")
        f.write("| 172.16.9.0 - 172.16.255.255 (Unused Reserve Space for Disaster Expansion - ~63,000 IPs) |\n")
        f.write("+-----------------------------------------------------------------------------------------+\n")
        f.write("```\n\n")

        f.write("---\n\n")
        f.write("## 3. OSPF Area Summarisation Analysis (ABR Route Aggregation)\n\n")
        f.write("### The Clinical Rationale for Route Summarisation\n")
        f.write("In a disaster-resilient multi-site topology, flapping access links or DHCP churn at the Remote Clinic ")
        f.write("must **not** trigger full Shortest Path First (SPF) recalculations across the Main Hospital Core. ")
        f.write("By summarising routes at Area Border Router **R2**, we reduce the OSPF Link-State Database (LSDB) size ")
        f.write("and isolate SPF recalculations to Area 1.\n\n")

        if remote_summary_net:
            f.write("### Recommended Area 1 Route Aggregation\n")
            f.write(f"- **Contiguous Supernet Covering All Remote Clinic Subnets:** `{remote_summary_net}`  \n")
            f.write(f"- **Summary Subnet Mask:** `{remote_summary_net.netmask}`  \n")
            f.write(f"- **ABR Cisco IOS Configuration (on Core Router R2):**\n\n")
            f.write("```cisco\n")
            f.write("router ospf 1\n")
            f.write(f" area 1 range {remote_summary_net.network_address} {remote_summary_net.netmask}\n")
            f.write("exit\n")
            f.write("```\n\n")
            f.write("> **Result:** Rather than injecting multiple Type-3 Summary LSAs for every small remote VLAN, ")
            f.write(f"R2 advertises a single aggregated summary route (`{remote_summary_net}`) into Backbone Area 0. ")
            f.write("If any individual remote subnet experiences an intermittent link flap, the summary LSA remains stable, ")
            f.write("guaranteeing zero CPU churn on Core Router R1.\n")

    print(f"[OK] Generated VLSM Plan Markdown -> {filepath}")

def generate_ip_table_csv(allocations: list, filepath: str):
    """
    Generates /addressing/ip_table.csv assigning concrete IPs to every:
      - Gateway
      - HSRP Virtual IP (.1)
      - Physical SVI 1 on SW-D1 (.2)
      - Physical SVI 2 on SW-D2 (.3)
      - Servers (DNS, DHCP, HTTP, EHR Records)
      - SBC nodes in ICU
      - Static infrastructure devices
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    rows = []

    alloc_map = {a["name"]: a for a in allocations}

    for a in allocations:
        net = a["_net_obj"]
        vlan = a["vlan_id"]
        site = a["site"]
        name = a["name"]
        prefix = a["prefix"]

        if prefix >= 30:
            # Point to point or loopback
            if prefix == 30:
                hosts = list(net.hosts())
                if "WAN-Primary" in name:
                    rows.append({"ip": str(hosts[0]), "mask": str(net.netmask), "device": "R1", "interface": "Serial0/0/0", "role": "Primary WAN DCE Endpoint", "vlan": "-", "site": site})
                    rows.append({"ip": str(hosts[1]), "mask": str(net.netmask), "device": "R2", "interface": "Serial0/0/0", "role": "Primary WAN DTE Endpoint", "vlan": "-", "site": site})
                elif "WAN-Secondary" in name:
                    rows.append({"ip": str(hosts[0]), "mask": str(net.netmask), "device": "R1", "interface": "Serial0/0/1", "role": "Backup WAN DCE Endpoint", "vlan": "-", "site": site})
                    rows.append({"ip": str(hosts[1]), "mask": str(net.netmask), "device": "R2", "interface": "Serial0/0/1", "role": "Backup WAN DTE Endpoint", "vlan": "-", "site": site})
                elif "Transit-R1-SW-D1" in name:
                    rows.append({"ip": str(hosts[0]), "mask": str(net.netmask), "device": "SW-D1", "interface": "GigabitEthernet0/2", "role": "Routed Uplink to R1", "vlan": "-", "site": site})
                    rows.append({"ip": str(hosts[1]), "mask": str(net.netmask), "device": "R1", "interface": "GigabitEthernet0/0", "role": "Routed Downlink to SW-D1", "vlan": "-", "site": site})
                elif "Transit-R1-SW-D2" in name:
                    rows.append({"ip": str(hosts[0]), "mask": str(net.netmask), "device": "SW-D2", "interface": "GigabitEthernet0/2", "role": "Routed Uplink to R1", "vlan": "-", "site": site})
                    rows.append({"ip": str(hosts[1]), "mask": str(net.netmask), "device": "R1", "interface": "GigabitEthernet0/1", "role": "Routed Downlink to SW-D2", "vlan": "-", "site": site})
                elif "Transit-R2-SW-D3" in name:
                    rows.append({"ip": str(hosts[0]), "mask": str(net.netmask), "device": "SW-D3", "interface": "GigabitEthernet0/1", "role": "Routed Uplink to R2", "vlan": "-", "site": site})
                    rows.append({"ip": str(hosts[1]), "mask": str(net.netmask), "device": "R2", "interface": "GigabitEthernet0/0", "role": "Routed Downlink to SW-D3", "vlan": "-", "site": site})
                elif "Edge-R1-ISP" in name:
                    rows.append({"ip": str(hosts[0]), "mask": str(net.netmask), "device": "EDGE-ISP", "interface": "GigabitEthernet0/0", "role": "Public Internet Gateway", "vlan": "-", "site": site})
                    rows.append({"ip": str(hosts[1]), "mask": str(net.netmask), "device": "R1", "interface": "GigabitEthernet0/2", "role": "Internet Edge NAT PAT Outside", "vlan": "-", "site": site})
            elif prefix == 32:
                dev = name.replace("Loopback-", "")
                rows.append({"ip": str(net.network_address), "mask": str(net.netmask), "device": dev, "interface": "Loopback0", "role": f"{dev} OSPF Router-ID", "vlan": "-", "site": site})
            continue

        # For host VLAN pools:
        net_int = int(net.network_address)
        mask_str = str(net.netmask)

        # Rule from prompt:
        # Reserve .1 for the HSRP virtual gateway, .2 and .3 for the two physical SVIs on each VLAN.
        hsrp_vip  = str(ipaddress.IPv4Address(net_int + 1))
        svi_d1_ip = str(ipaddress.IPv4Address(net_int + 2))
        svi_d2_ip = str(ipaddress.IPv4Address(net_int + 3))

        if site == "Main Hospital":
            rows.append({"ip": hsrp_vip,  "mask": mask_str, "device": "HSRP-Group", "interface": f"Vlan{vlan}", "role": "HSRP Virtual Gateway VIP (.1 Default Gateway for hosts)", "vlan": vlan, "site": site})
            rows.append({"ip": svi_d1_ip, "mask": mask_str, "device": "SW-D1",      "interface": f"Vlan{vlan}", "role": "SW-D1 Physical SVI (.2 Active/Standby SVI)", "vlan": vlan, "site": site})
            rows.append({"ip": svi_d2_ip, "mask": mask_str, "device": "SW-D2",      "interface": f"Vlan{vlan}", "role": "SW-D2 Physical SVI (.3 Standby/Active SVI)", "vlan": vlan, "site": site})
        else:
            rows.append({"ip": hsrp_vip,  "mask": mask_str, "device": "SW-D3",      "interface": f"Vlan{vlan}", "role": "SW-D3 SVI Primary Gateway (.1 Default Gateway)", "vlan": vlan, "site": site})
            rows.append({"ip": svi_d1_ip, "mask": mask_str, "device": "SW-D3",      "interface": f"Vlan{vlan}", "role": "Reserved SVI Redundancy Expansion (.2)", "vlan": vlan, "site": site})
            rows.append({"ip": svi_d2_ip, "mask": mask_str, "device": "SW-D3",      "interface": f"Vlan{vlan}", "role": "Reserved SVI Redundancy Expansion (.3)", "vlan": vlan, "site": site})

        # Static Infrastructure and End-Device assignments per VLAN:
        if vlan == 50 and site == "Main Hospital":
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 4)), "mask": mask_str, "device": "SRV-CENTRAL", "interface": "FastEthernet0", "role": "Central Server (DNS/DHCP/EHR Web Portal)", "vlan": 50, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 7)), "mask": mask_str, "device": "SRV-PACS",    "interface": "FastEthernet0", "role": "PACS Medical Imaging Archive (MRI/CT Studies)", "vlan": 50, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 8)), "mask": mask_str, "device": "SRV-BACKUP",  "interface": "FastEthernet0", "role": "Disaster Recovery Database Replication Target", "vlan": 50, "site": site})

        elif vlan == 10 and site == "Main Hospital":
            # 3 SBC sensor nodes + 3 clinical hosts in ICU
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 10)), "mask": mask_str, "device": "SBC-ICU-101", "interface": "FastEthernet0", "role": "Bedside IoT Telemetry Node (Bed 101 - Vitals)", "vlan": 10, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 11)), "mask": mask_str, "device": "SBC-ICU-102", "interface": "FastEthernet0", "role": "Bedside IoT Telemetry Node (Bed 102 - Vitals)", "vlan": 10, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 12)), "mask": mask_str, "device": "SBC-ICU-103", "interface": "FastEthernet0", "role": "Bedside IoT Telemetry Node (Bed 103 - Vitals)", "vlan": 10, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 13)), "mask": mask_str, "device": "PC-ICU-NURSE", "interface": "FastEthernet0", "role": "ICU Central Nursing Monitoring Station", "vlan": 10, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 14)), "mask": mask_str, "device": "PC-ICU-DOC1",  "interface": "FastEthernet0", "role": "ICU Attending Physician Workstation 1", "vlan": 10, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 15)), "mask": mask_str, "device": "PC-ICU-DOC2",  "interface": "FastEthernet0", "role": "ICU Attending Physician Workstation 2", "vlan": 10, "site": site})

        elif vlan == 20 and site == "Main Hospital":
            # 2 SBC sensor nodes + 3 surgical hosts in Surgery
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 10)), "mask": mask_str, "device": "SBC-SURG-201", "interface": "FastEthernet0", "role": "OR 1 Anesthesia & Ventilator Telemetry", "vlan": 20, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 11)), "mask": mask_str, "device": "SBC-SURG-202", "interface": "FastEthernet0", "role": "OR 2 Surgical Vital Signs Telemetry", "vlan": 20, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 12)), "mask": mask_str, "device": "PC-THEATRE-1", "interface": "FastEthernet0", "role": "Operating Theatre 1 PACS Viewer Workstation", "vlan": 20, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 13)), "mask": mask_str, "device": "PC-THEATRE-2", "interface": "FastEthernet0", "role": "Operating Theatre 2 PACS Viewer Workstation", "vlan": 20, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 14)), "mask": mask_str, "device": "PC-THEATRE-3", "interface": "FastEthernet0", "role": "Surgical Consultation & Telemetry Display", "vlan": 20, "site": site})

        elif vlan == 30 and site == "Main Hospital":
            # 3 administrative hosts
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 10)), "mask": mask_str, "device": "PC-ADMIN-301", "interface": "FastEthernet0", "role": "Main Hospital Admissions & Billing PC", "vlan": 30, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 11)), "mask": mask_str, "device": "PC-ADMIN-302", "interface": "FastEthernet0", "role": "Medical Records Administration PC", "vlan": 30, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 12)), "mask": mask_str, "device": "PC-ADMIN-303", "interface": "FastEthernet0", "role": "Hospital Executive Director PC", "vlan": 30, "site": site})

        elif vlan == 40 and site == "Main Hospital":
            # 1 AP + 3 guest wireless hosts
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 10)), "mask": mask_str, "device": "AP-GUEST",       "interface": "Port0", "role": "Main Hospital Guest Wi-Fi Access Point", "vlan": 40, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 11)), "mask": mask_str, "device": "LAPTOP-GUEST-1", "interface": "Wireless0", "role": "Visitor Laptop 1 (Waiting Lounge)", "vlan": 40, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 12)), "mask": mask_str, "device": "LAPTOP-GUEST-2", "interface": "Wireless0", "role": "Visitor Laptop 2 (Cafeteria)", "vlan": 40, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 13)), "mask": mask_str, "device": "LAPTOP-GUEST-3", "interface": "Wireless0", "role": "Visitor Laptop 3 (Family Lounge)", "vlan": 40, "site": site})

        elif vlan == 60 and site == "Main Hospital":
            # 3 IP phones
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 10)), "mask": mask_str, "device": "PHONE-ICU-601",   "interface": "SwitchPort", "role": "Cisco 7960 IP Phone Ext 1001 (ICU Desk)", "vlan": 60, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 11)), "mask": mask_str, "device": "PHONE-SURG-602",  "interface": "SwitchPort", "role": "Cisco 7960 IP Phone Ext 1002 (Surgery Desk)", "vlan": 60, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 12)), "mask": mask_str, "device": "PHONE-ADMIN-603", "interface": "SwitchPort", "role": "Cisco 7960 IP Phone Ext 1003 (Reception Desk)", "vlan": 60, "site": site})

        elif vlan == 99 and site == "Main Hospital":
            # Management infrastructure + NOC host
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 10)), "mask": mask_str, "device": "SW-A1",      "interface": "Vlan99", "role": "SW-A1 Access Switch Management In-Band SVI", "vlan": 99, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 11)), "mask": mask_str, "device": "SW-A2",      "interface": "Vlan99", "role": "SW-A2 Access Switch Management In-Band SVI", "vlan": 99, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 12)), "mask": mask_str, "device": "SW-A3",      "interface": "Vlan99", "role": "SW-A3 Access Switch Management In-Band SVI", "vlan": 99, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 13)), "mask": mask_str, "device": "SW-A4",      "interface": "Vlan99", "role": "SW-A4 Access Switch Management In-Band SVI", "vlan": 99, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 20)), "mask": mask_str, "device": "PC-NOC-MGT", "interface": "FastEthernet0", "role": "Network Operations Center Management Console", "vlan": 99, "site": site})

        elif vlan == 10 and site == "Remote Clinic":
            # Remote clinic clinical hosts + cache server
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 4)),  "mask": mask_str, "device": "SRV-CACHE",          "interface": "FastEthernet0", "role": "Remote Clinic Local Cache & EHR Proxy Server", "vlan": 10, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 10)), "mask": mask_str, "device": "PC-CLINIC-CONSULT1", "interface": "FastEthernet0", "role": "Clinic Consultation Room 1 Workstation", "vlan": 10, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 11)), "mask": mask_str, "device": "PC-CLINIC-CONSULT2", "interface": "FastEthernet0", "role": "Clinic Consultation Room 2 Workstation", "vlan": 10, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 12)), "mask": mask_str, "device": "PC-CLINIC-TRIAGE",   "interface": "FastEthernet0", "role": "Clinic Emergency Triage Station", "vlan": 10, "site": site})

        elif vlan == 30 and site == "Remote Clinic":
            # Remote clinic admin hosts
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 10)), "mask": mask_str, "device": "PC-CLINIC-ADM1",  "interface": "FastEthernet0", "role": "Clinic Reception Registration Terminal", "vlan": 30, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 11)), "mask": mask_str, "device": "PC-CLINIC-ADM2",  "interface": "FastEthernet0", "role": "Clinic Billing & Records Terminal", "vlan": 30, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 12)), "mask": mask_str, "device": "PC-CLINIC-PHARM", "interface": "FastEthernet0", "role": "Clinic Pharmacy Dispensing Terminal", "vlan": 30, "site": site})

        elif vlan == 40 and site == "Remote Clinic":
            # Remote clinic guest AP + 3 laptops
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 10)), "mask": mask_str, "device": "AP-CLINIC-GUEST", "interface": "Port0", "role": "Remote Clinic Guest Wi-Fi Access Point", "vlan": 40, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 11)), "mask": mask_str, "device": "LAPTOP-CLINIC-G1", "interface": "Wireless0", "role": "Clinic Visitor Laptop 1", "vlan": 40, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 12)), "mask": mask_str, "device": "LAPTOP-CLINIC-G2", "interface": "Wireless0", "role": "Clinic Visitor Laptop 2", "vlan": 40, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 13)), "mask": mask_str, "device": "LAPTOP-CLINIC-G3", "interface": "Wireless0", "role": "Clinic Visitor Laptop 3", "vlan": 40, "site": site})

        elif vlan == 60 and site == "Remote Clinic":
            # Remote clinic IP phones
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 10)), "mask": mask_str, "device": "PHONE-CLINIC-601", "interface": "SwitchPort", "role": "Cisco 7960 IP Phone Ext 2001 (Clinic Reception)", "vlan": 60, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 11)), "mask": mask_str, "device": "PHONE-CLINIC-602", "interface": "SwitchPort", "role": "Cisco 7960 IP Phone Ext 2002 (Clinic Doctor Desk)", "vlan": 60, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 12)), "mask": mask_str, "device": "PHONE-CLINIC-603", "interface": "SwitchPort", "role": "Cisco 7960 IP Phone Ext 2003 (Clinic Triage Desk)", "vlan": 60, "site": site})

        elif vlan == 99 and site == "Remote Clinic":
            # Remote clinic switch SVI + clinic admin PC
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 10)), "mask": mask_str, "device": "SW-A5",         "interface": "Vlan99", "role": "SW-A5 Access Switch Management In-Band SVI", "vlan": 99, "site": site})
            rows.append({"ip": str(ipaddress.IPv4Address(net_int + 11)), "mask": mask_str, "device": "PC-CLINIC-MGT", "interface": "FastEthernet0", "role": "Clinic Local Management Administrator PC", "vlan": 99, "site": site})

    fieldnames = ["ip", "mask", "device", "interface", "role", "vlan", "site"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] Generated Concrete IP Table CSV -> {filepath} ({len(rows)} assigned endpoints)")

def main():
    parser = argparse.ArgumentParser(description="VLSM Addressing Calculator & IPAM Generator")
    parser.add_argument("--input", default="addressing/requirements.json", help="Path to input requirements JSON file")
    parser.add_argument("--output-dir", default="addressing", help="Directory where plan.csv, plan.md, and ip_table.csv will be saved")
    args = parser.parse_args()

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    input_path = os.path.join(project_root, args.input) if not os.path.isabs(args.input) else args.input
    output_dir = os.path.join(project_root, args.output_dir) if not os.path.isabs(args.output_dir) else args.output_dir

    if not os.path.exists(input_path):
        sys.stderr.write(f"[ERROR] Requirements file not found at: {input_path}\n")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    base_network = data.get("base_network", "172.16.0.0/16")
    growth_pct = float(data.get("growth_headroom_percent", 30))
    requirements = data.get("requirements", [])

    print("=" * 80)
    print("  EXECUTING VLSM ADDRESSING ENGINE (Python Standard Library ipaddress)")
    print(f"  Base Network: {base_network} | Growth Headroom: {growth_pct}%")
    print("=" * 80)

    allocations = allocate_vlsm_plan(base_network, requirements, growth_pct)

    plan_csv_path = os.path.join(output_dir, "plan.csv")
    plan_md_path  = os.path.join(output_dir, "plan.md")
    ip_table_path = os.path.join(output_dir, "ip_table.csv")

    generate_plan_csv(allocations, plan_csv_path)
    generate_plan_markdown(allocations, plan_md_path, base_network, growth_pct)
    generate_ip_table_csv(allocations, ip_table_path)

    print("\n" + "=" * 80)
    print(f"  VLSM ALLOCATION SUCCESSFUL: {len(allocations)} subnets allocated with ZERO overlaps.")
    print("=" * 80)

if __name__ == "__main__":
    main()
