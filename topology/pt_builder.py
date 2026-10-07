#!/usr/bin/env python3
"""
================================================================================
Packet Tracer Topology Builder & Cabling Verification Tool
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Generates a structured device-build blueprint and cabling schedule to guide
accurate topology construction in Cisco Packet Tracer 8.x.
"""

import sys
import os

DEVICES = [
    {"name": "R1",          "model": "Cisco 2911",       "role": "Core Router (Main Hospital)", "slots": ["HWIC-2T (Slot 0)"]},
    {"name": "R2",          "model": "Cisco 2911",       "role": "Core Router (Remote Clinic ABR)", "slots": ["HWIC-2T (Slot 0)"]},
    {"name": "EDGE-ISP",    "model": "Cisco 2911",       "role": "Simulated ISP Public Internet", "slots": []},
    {"name": "SW-D1",       "model": "Catalyst 3560-24PS","role": "Multilayer L3 Distribution (Main)", "slots": []},
    {"name": "SW-D2",       "model": "Catalyst 3560-24PS","role": "Multilayer L3 Distribution (Main)", "slots": []},
    {"name": "SW-D3",       "model": "Catalyst 3560-24PS","role": "Multilayer L3 Distribution (Clinic)", "slots": []},
    {"name": "SW-A1",       "model": "Catalyst 2960-24TT","role": "Access Layer (ICU Floor)", "slots": []},
    {"name": "SW-A2",       "model": "Catalyst 2960-24TT","role": "Access Layer (Surgery Floor)", "slots": []},
    {"name": "SW-A3",       "model": "Catalyst 2960-24TT","role": "Access Layer (Admin Floor)", "slots": []},
    {"name": "SW-A4",       "model": "Catalyst 2960-24TT","role": "Access Layer (Guest Wi-Fi)", "slots": []},
    {"name": "SW-A5",       "model": "Catalyst 2960-24TT","role": "Access Layer (Remote Clinic)", "slots": []},
    {"name": "SRV-CENTRAL", "model": "Server-PT",        "role": "Central Server Farm (DNS, HTTP, DHCP)", "slots": []},
    {"name": "SRV-CACHE",   "model": "Server-PT",        "role": "Remote Clinic Local Cache Server", "slots": []},
]

CABLING = [
    ("R1", "Serial0/0/0", "R2", "Serial0/0/0", "Serial DCE", "Primary WAN (OSPF Area 0)"),
    ("R1", "Serial0/0/1", "R2", "Serial0/0/1", "Serial DCE", "Backup WAN (EIGRP AS 100)"),
    ("R1", "Gig0/0", "SW-D1", "Gig0/2", "Straight-Through", "Transit Link 172.16.5.0/30"),
    ("R1", "Gig0/1", "SW-D2", "Gig0/2", "Straight-Through", "Transit Link 172.16.5.4/30"),
    ("R1", "Gig0/2", "EDGE-ISP", "Gig0/0", "Cross-Over", "Internet Edge 203.0.113.0/30"),
    ("R2", "Gig0/0", "SW-D3", "Gig0/1", "Straight-Through", "Transit Link 172.16.5.8/30 (Area 1)"),
    ("SW-D1", "Gig0/1", "SW-D2", "Gig0/1", "Cross-Over", "Inter-Distribution 802.1Q Trunk"),
    ("SW-D1", "Fa0/1", "SW-A1", "Fa0/24", "Straight-Through", "802.1Q Trunk Uplink"),
    ("SW-D1", "Fa0/3", "SW-A2", "Fa0/24", "Straight-Through", "802.1Q Trunk Uplink"),
    ("SW-D1", "Fa0/10", "SRV-CENTRAL", "Fa0", "Straight-Through", "Access VLAN 50"),
    ("SW-D2", "Fa0/1", "SW-A3", "Fa0/24", "Straight-Through", "802.1Q Trunk Uplink"),
    ("SW-D2", "Fa0/3", "SW-A4", "Fa0/24", "Straight-Through", "802.1Q Trunk Uplink"),
    ("SW-D3", "Fa0/1", "SW-A5", "Fa0/24", "Straight-Through", "802.1Q Trunk Uplink"),
]

def print_build_sheet():
    print("=" * 80)
    print("  CISCO PACKET TRACER 8.x TOPOLOGY BUILD SHEET")
    print("  Disaster-Resilient Smart Hospital Network")
    print("=" * 80)
    print("\n1. REQUIRED DEVICE INVENTORY & MODULE INSTALLATIONS:")
    print("-" * 80)
    for dev in DEVICES:
        slots_str = f" | Add Modules: {', '.join(dev['slots'])}" if dev['slots'] else ""
        print(f"  [{dev['name']:<12}] Model: {dev['model']:<18} ({dev['role']}){slots_str}")

    print("\n2. CABLING & PORT INTERCONNECT SCHEDULE:")
    print("-" * 80)
    print(f"  {'Source':<10} {'Port':<14} {'Target':<10} {'Target Port':<14} {'Media':<18} {'Role'}")
    print("  " + "-" * 76)
    for src, sport, dst, dport, media, role in CABLING:
        print(f"  {src:<10} {sport:<14} {dst:<10} {dport:<14} {media:<18} {role}")

    print("\n3. HARDWARE PREPARATION RULES:")
    print("-" * 80)
    print("  * For Routers R1 & R2: In PT Physical View, toggle power OFF, drag 'HWIC-2T' into slot 0, then power ON.")
    print("  * For Serial Links: Select 'Serial DCE' cable. Click R1 first so R1 is DCE and generates clocking.")
    print("  * For Distribution Switches: Use '3560-24PS' (Multilayer) to support 'ip routing' and SVIs.")
    print("=" * 80)

if __name__ == "__main__":
    print_build_sheet()
