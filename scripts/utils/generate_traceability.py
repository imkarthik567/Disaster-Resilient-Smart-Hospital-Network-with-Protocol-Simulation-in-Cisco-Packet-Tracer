#!/usr/bin/env python3
"""
================================================================================
Requirements Traceability Matrix Generator
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Generates /docs/traceability_matrix.md and /docs/traceability_matrix.csv.
Decomposes Review-1 Section 4.2 Objectives and Section 6.2 Validation Strategy
into 80+ testable atomic requirements.
"""

import csv
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")

REQUIREMENTS = [
    # -------------------------------------------------------------------------
    # DOMAIN 1: TOPOLOGY & PHYSICAL HIERARCHY (Section 4.2 Objective 1)
    # -------------------------------------------------------------------------
    {
        "id": "REQ-TOP-01",
        "domain": "Topology & Hierarchy",
        "req": "Design three-tier hierarchical architecture (Core, Distribution, Access) in Cisco Packet Tracer 8.x.",
        "design": "Three-tier Cisco design: R1/R2 core, SW-D1/D2/D3 distribution, SW-A1-A5 access",
        "configs": "configs/R1/R1.txt, configs/SW-D1/SW-D1.txt, configs/SW-A1/SW-A1.txt",
        "test_id": "TC-TOP-01",
        "evidence": "evidence/phase1_TC-TOP-01_three_tier_diagram.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-TOP-02",
        "domain": "Topology & Hierarchy",
        "req": "Deploy Core Router R1 at Main Hospital campus with HWIC-2T serial modules.",
        "design": "Cisco 2911 ISR with HWIC-2T module installed in Slot 0",
        "configs": "configs/R1/R1.txt",
        "test_id": "TC-TOP-02",
        "evidence": "evidence/phase1_TC-TOP-02_r1_inventory.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-TOP-03",
        "domain": "Topology & Hierarchy",
        "req": "Deploy Core Router R2 at Remote Clinic campus with HWIC-2T serial modules.",
        "design": "Cisco 2911 ISR with HWIC-2T module installed in Slot 0",
        "configs": "configs/R2/R2.txt",
        "test_id": "TC-TOP-03",
        "evidence": "evidence/phase1_TC-TOP-03_r2_inventory.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-TOP-04",
        "domain": "Topology & Hierarchy",
        "req": "Deploy Main Hospital Distribution Switch SW-D1 for Clinical and Server farm aggregation.",
        "design": "Cisco Catalyst 3560-24PS Multilayer Switch",
        "configs": "configs/SW-D1/SW-D1.txt",
        "test_id": "TC-TOP-04",
        "evidence": "evidence/phase1_TC-TOP-04_sw_d1_status.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-TOP-05",
        "domain": "Topology & Hierarchy",
        "req": "Deploy Main Hospital Distribution Switch SW-D2 for Admin, Guest, and Voice aggregation.",
        "design": "Cisco Catalyst 3560-24PS Multilayer Switch",
        "configs": "configs/SW-D2/SW-D2.txt",
        "test_id": "TC-TOP-05",
        "evidence": "evidence/phase1_TC-TOP-05_sw_d2_status.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-TOP-06",
        "domain": "Topology & Hierarchy",
        "req": "Deploy Remote Clinic Distribution Switch SW-D3 for Clinic access aggregation.",
        "design": "Cisco Catalyst 3560-24PS Multilayer Switch",
        "configs": "configs/SW-D3/SW-D3.txt",
        "test_id": "TC-TOP-06",
        "evidence": "evidence/phase1_TC-TOP-06_sw_d3_status.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-TOP-07",
        "domain": "Topology & Hierarchy",
        "req": "Deploy Access Switches SW-A1 through SW-A4 across Main Hospital floor zones.",
        "design": "Cisco Catalyst 2960-24TT Layer 2 Switches",
        "configs": "configs/SW-A1/SW-A1.txt, configs/SW-A2/SW-A2.txt, configs/SW-A3/SW-A3.txt, configs/SW-A4/SW-A4.txt",
        "test_id": "TC-TOP-07",
        "evidence": "evidence/phase1_TC-TOP-07_main_access_switches.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-TOP-08",
        "domain": "Topology & Hierarchy",
        "req": "Deploy Access Switch SW-A5 at Remote Clinic campus.",
        "design": "Cisco Catalyst 2960-24TT Layer 2 Switch",
        "configs": "configs/SW-A5/SW-A5.txt",
        "test_id": "TC-TOP-08",
        "evidence": "evidence/phase1_TC-TOP-08_remote_access_switch.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-TOP-09",
        "domain": "Topology & Hierarchy",
        "req": "Establish redundant dual WAN serial links between R1 and R2.",
        "design": "Primary Serial Se0/0/0 and Secondary Serial Se0/0/1 with DCE clocking on R1",
        "configs": "configs/R1/R1.txt, configs/R2/R2.txt",
        "test_id": "TC-TOP-09",
        "evidence": "evidence/phase1_TC-TOP-09_dual_serial_status.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-TOP-10",
        "domain": "Topology & Hierarchy",
        "req": "Establish simulated upstream Internet Service Provider (EDGE-ISP) connected to R1.",
        "design": "Cisco 2911 Router simulating public ISP with Loopback DNS",
        "configs": "configs/edge-isp/edge-isp.txt, configs/R1/R1.txt",
        "test_id": "TC-TOP-10",
        "evidence": "evidence/phase1_TC-TOP-10_isp_edge_status.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },

    # -------------------------------------------------------------------------
    # DOMAIN 2: VLSM ADDRESSING SCHEME (Section 4.2 Objective 2)
    # -------------------------------------------------------------------------
    {
        "id": "REQ-ADD-01",
        "domain": "VLSM Addressing",
        "req": "Subdivide private network block 172.16.0.0/16 using classless VLSM without overlapping.",
        "design": "Algorithmic VLSM allocation engine sorted by host demand",
        "configs": "addressing/vlsm_calculator.py, addressing/vlsm_allocations.json",
        "test_id": "TC-ADD-01",
        "evidence": "evidence/phase1_TC-ADD-01_vlsm_no_overlaps.txt",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-ADD-02",
        "domain": "VLSM Addressing",
        "req": "Allocate compact /23 subnet (172.16.0.0/23, 510 hosts) for Main Hospital Guest Wi-Fi.",
        "design": "Subnet 172.16.0.0/23, Mask 255.255.254.0, Gateway 172.16.0.1",
        "configs": "configs/SW-D2/SW-D2.txt, addressing/addressing_table.csv",
        "test_id": "TC-ADD-02",
        "evidence": "evidence/phase1_TC-ADD-02_guest_subnet.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-ADD-03",
        "domain": "VLSM Addressing",
        "req": "Allocate /24 subnet (172.16.2.0/24, 254 hosts) for Main Hospital Administration workstations.",
        "design": "Subnet 172.16.2.0/24, Mask 255.255.255.0, Gateway 172.16.2.1",
        "configs": "configs/SW-D2/SW-D2.txt, addressing/addressing_table.csv",
        "test_id": "TC-ADD-03",
        "evidence": "evidence/phase1_TC-ADD-03_admin_subnet.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-ADD-04",
        "domain": "VLSM Addressing",
        "req": "Allocate /25 subnet (172.16.3.0/25, 126 hosts) for Main Hospital VoIP Voice endpoints.",
        "design": "Subnet 172.16.3.0/25, Mask 255.255.255.128, Gateway 172.16.3.1",
        "configs": "configs/SW-D2/SW-D2.txt, addressing/addressing_table.csv",
        "test_id": "TC-ADD-04",
        "evidence": "evidence/phase1_TC-ADD-04_voice_subnet.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-ADD-05",
        "domain": "VLSM Addressing",
        "req": "Allocate /26 subnet (172.16.3.128/26, 62 hosts) for Main Hospital ICU bedside IoT sensors.",
        "design": "Subnet 172.16.3.128/26, Mask 255.255.255.192, Gateway 172.16.3.129",
        "configs": "configs/SW-D1/SW-D1.txt, addressing/addressing_table.csv",
        "test_id": "TC-ADD-05",
        "evidence": "evidence/phase1_TC-ADD-05_icu_subnet.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-ADD-06",
        "domain": "VLSM Addressing",
        "req": "Allocate /26 subnet (172.16.3.192/26, 62 hosts) for Main Hospital Operating Theatre devices.",
        "design": "Subnet 172.16.3.192/26, Mask 255.255.255.192, Gateway 172.16.3.193",
        "configs": "configs/SW-D1/SW-D1.txt, addressing/addressing_table.csv",
        "test_id": "TC-ADD-06",
        "evidence": "evidence/phase1_TC-ADD-06_surgery_subnet.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-ADD-07",
        "domain": "VLSM Addressing",
        "req": "Allocate /27 subnet (172.16.4.0/27, 30 hosts) for Main Hospital Central Server Farm.",
        "design": "Subnet 172.16.4.0/27, Mask 255.255.255.224, Gateway 172.16.4.1",
        "configs": "configs/SW-D1/SW-D1.txt, addressing/addressing_table.csv",
        "test_id": "TC-ADD-07",
        "evidence": "evidence/phase1_TC-ADD-07_server_farm_subnet.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-ADD-08",
        "domain": "VLSM Addressing",
        "req": "Allocate /27 subnet (172.16.4.32/27, 30 hosts) for Main Hospital Out-of-Band Management.",
        "design": "Subnet 172.16.4.32/27, Mask 255.255.255.224, Gateway 172.16.4.33",
        "configs": "configs/SW-D1/SW-D1.txt, addressing/addressing_table.csv",
        "test_id": "TC-ADD-08",
        "evidence": "evidence/phase1_TC-ADD-08_mgmt_subnet.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-ADD-09",
        "domain": "VLSM Addressing",
        "req": "Allocate discrete subnets for Remote Clinic (Clinical /27, Admin /27, Voice /27, Server /28, Mgmt /28).",
        "design": "Allocations from 172.16.4.64 through 172.16.4.191",
        "configs": "configs/SW-D3/SW-D3.txt, addressing/addressing_table.csv",
        "test_id": "TC-ADD-09",
        "evidence": "evidence/phase1_TC-ADD-09_remote_subnets.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-ADD-10",
        "domain": "VLSM Addressing",
        "req": "Allocate point-to-point /30 subnets for Primary WAN, Secondary WAN, and Distribution transit links.",
        "design": "Subnets 172.16.4.192/30 (Primary), 172.16.4.196/30 (Backup), 172.16.5.0/30, .4/30, .8/30",
        "configs": "configs/R1/R1.txt, configs/R2/R2.txt, configs/SW-D1/SW-D1.txt, configs/SW-D2/SW-D2.txt, configs/SW-D3/SW-D3.txt",
        "test_id": "TC-ADD-10",
        "evidence": "evidence/phase1_TC-ADD-10_wan_transit_subnets.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },

    # -------------------------------------------------------------------------
    # DOMAIN 3: LAYER 2 SWITCHING, VLANS & STP (Section 4.2 Objective 3)
    # -------------------------------------------------------------------------
    {
        "id": "REQ-L2-01",
        "domain": "Layer 2 Switching",
        "req": "Create VLAN 10 (ICU_Clinical) on all switches and map access ports on SW-A1.",
        "design": "VLAN 10 declared; Fa0/1-10 on SW-A1 configured as access ports in VLAN 10",
        "configs": "configs/SW-A1/SW-A1.txt, configs/SW-D1/SW-D1.txt",
        "test_id": "TC-L2-01",
        "evidence": "evidence/phase1_TC-L2-01_vlan10_status.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-L2-02",
        "domain": "Layer 2 Switching",
        "req": "Create VLAN 20 (Surgery_Theatre) on all switches and map access ports on SW-A2.",
        "design": "VLAN 20 declared; Fa0/1-10 on SW-A2 configured as access ports in VLAN 20",
        "configs": "configs/SW-A2/SW-A2.txt, configs/SW-D1/SW-D1.txt",
        "test_id": "TC-L2-02",
        "evidence": "evidence/phase1_TC-L2-02_vlan20_status.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-L2-03",
        "domain": "Layer 2 Switching",
        "req": "Create VLAN 30 (Administration) on all switches and map access ports on SW-A3.",
        "design": "VLAN 30 declared; Fa0/1-16 on SW-A3 configured as access ports in VLAN 30",
        "configs": "configs/SW-A3/SW-A3.txt, configs/SW-D2/SW-D2.txt",
        "test_id": "TC-L2-03",
        "evidence": "evidence/phase1_TC-L2-03_vlan30_status.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-L2-04",
        "domain": "Layer 2 Switching",
        "req": "Create VLAN 40 (Guest_WiFi) on all switches and map access ports on SW-A4.",
        "design": "VLAN 40 declared; Fa0/1-16 on SW-A4 configured as access ports in VLAN 40",
        "configs": "configs/SW-A4/SW-A4.txt, configs/SW-D2/SW-D2.txt",
        "test_id": "TC-L2-04",
        "evidence": "evidence/phase1_TC-L2-04_vlan40_status.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-L2-05",
        "domain": "Layer 2 Switching",
        "req": "Create VLAN 50 (Server_Farm) on all switches and assign port Fa0/10 on SW-D1.",
        "design": "VLAN 50 declared; Fa0/10 on SW-D1 assigned to VLAN 50 for Central Server",
        "configs": "configs/SW-D1/SW-D1.txt",
        "test_id": "TC-L2-05",
        "evidence": "evidence/phase1_TC-L2-05_vlan50_status.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-L2-06",
        "domain": "Layer 2 Switching",
        "req": "Create Voice VLAN 60 and configure auxiliary voice encapsulation on access switches.",
        "design": "VLAN 60 voice vlan tagging configured on IP phone ports (Fa0/11-15, etc.)",
        "configs": "configs/SW-A1/SW-A1.txt, configs/SW-A2/SW-A2.txt, configs/SW-A3/SW-A3.txt",
        "test_id": "TC-L2-06",
        "evidence": "evidence/phase1_TC-L2-06_voice_vlan.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-L2-07",
        "domain": "Layer 2 Switching",
        "req": "Configure Management VLAN 99 with static SVI addresses on all switches.",
        "design": "Interface Vlan99 configured with IP on 172.16.4.32/27 and default-gateway 172.16.4.33",
        "configs": "configs/SW-D1/SW-D1.txt, configs/SW-A1/SW-A1.txt, configs/SW-A2/SW-A2.txt",
        "test_id": "TC-L2-07",
        "evidence": "evidence/phase1_TC-L2-07_mgmt_svis.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-L2-08",
        "domain": "Layer 2 Switching",
        "req": "Assign all unused ports to isolated parking VLAN 999 and administratively shut them down.",
        "design": "Unused interfaces configured for switchport access vlan 999 and shutdown",
        "configs": "configs/SW-A1/SW-A1.txt, configs/SW-A2/SW-A2.txt, configs/SW-A3/SW-A3.txt, configs/SW-A4/SW-A4.txt, configs/SW-A5/SW-A5.txt",
        "test_id": "TC-L2-08",
        "evidence": "evidence/phase1_TC-L2-08_parking_vlan.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-L2-09",
        "domain": "Layer 2 Switching",
        "req": "Configure IEEE 802.1Q trunking on all inter-switch downlinks and uplinks with Native VLAN 999.",
        "design": "Trunks configured with switchport trunk encapsulation dot1q and native vlan 999",
        "configs": "configs/SW-D1/SW-D1.txt, configs/SW-D2/SW-D2.txt, configs/SW-D3/SW-D3.txt, configs/SW-A1/SW-A1.txt through SW-A5.txt",
        "test_id": "TC-L2-09",
        "evidence": "evidence/phase1_TC-L2-09_trunk_native_vlan.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-L2-10",
        "domain": "Layer 2 Switching",
        "req": "Configure inter-distribution 802.1Q trunk cross-link between SW-D1 and SW-D2.",
        "design": "Gi0/1 to Gi0/1 cross-link trunk carrying VLANs 10,20,30,40,50,60,99",
        "configs": "configs/SW-D1/SW-D1.txt, configs/SW-D2/SW-D2.txt",
        "test_id": "TC-L2-10",
        "evidence": "evidence/phase1_TC-L2-10_inter_distro_trunk.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-L2-11",
        "domain": "Layer 2 Switching",
        "req": "Designate SW-D1 as Primary STP Root for VLANs 10, 20, 50, 99 and Secondary for 30, 40, 60.",
        "design": "spanning-tree vlan 10,20,50,99 root primary and spanning-tree vlan 30,40,60 root secondary",
        "configs": "configs/SW-D1/SW-D1.txt",
        "test_id": "TC-L2-11",
        "evidence": "evidence/phase1_TC-L2-11_sw_d1_stp_root.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-L2-12",
        "domain": "Layer 2 Switching",
        "req": "Designate SW-D2 as Primary STP Root for VLANs 30, 40, 60 and Secondary for 10, 20, 50, 99.",
        "design": "spanning-tree vlan 30,40,60 root primary and spanning-tree vlan 10,20,50,99 root secondary",
        "configs": "configs/SW-D2/SW-D2.txt",
        "test_id": "TC-L2-12",
        "evidence": "evidence/phase1_TC-L2-12_sw_d2_stp_root.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-L2-13",
        "domain": "Layer 2 Switching",
        "req": "Enable Spanning Tree PortFast and BPDU Guard on all host-facing access switch ports.",
        "design": "spanning-tree portfast and spanning-tree bpduguard enable on access ranges",
        "configs": "configs/SW-A1/SW-A1.txt through configs/SW-A5/SW-A5.txt",
        "test_id": "TC-L2-13",
        "evidence": "evidence/phase1_TC-L2-13_portfast_bpduguard.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },

    # -------------------------------------------------------------------------
    # DOMAIN 4: LAYER 3 INTER-VLAN ROUTING & SVIs (Section 4.2 Objective 3)
    # -------------------------------------------------------------------------
    {
        "id": "REQ-L3-01",
        "domain": "Layer 3 Routing",
        "req": "Enable hardware Layer-3 IP routing globally on SW-D1, SW-D2, and SW-D3.",
        "design": "Global ip routing command on Cisco Catalyst 3560 Multilayer switches",
        "configs": "configs/SW-D1/SW-D1.txt, configs/SW-D2/SW-D2.txt, configs/SW-D3/SW-D3.txt",
        "test_id": "TC-L3-01",
        "evidence": "evidence/phase2_TC-L3-01_ip_routing_enabled.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-L3-02",
        "domain": "Layer 3 Routing",
        "req": "Configure Switched Virtual Interfaces (SVIs) on SW-D1 as default gateways for VLANs 10, 20, 50, 99.",
        "design": "Interface Vlan10 (172.16.3.129/26), Vlan20 (.193/26), Vlan50 (.1/27), Vlan99 (.33/27)",
        "configs": "configs/SW-D1/SW-D1.txt",
        "test_id": "TC-L3-02",
        "evidence": "evidence/phase2_TC-L3-02_sw_d1_svis.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-L3-03",
        "domain": "Layer 3 Routing",
        "req": "Configure Switched Virtual Interfaces (SVIs) on SW-D2 as default gateways for VLANs 30, 40, 60.",
        "design": "Interface Vlan30 (172.16.2.1/24), Vlan40 (172.16.0.1/23), Vlan60 (172.16.3.1/25)",
        "configs": "configs/SW-D2/SW-D2.txt",
        "test_id": "TC-L3-03",
        "evidence": "evidence/phase2_TC-L3-03_sw_d2_svis.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-L3-04",
        "domain": "Layer 3 Routing",
        "req": "Configure Switched Virtual Interfaces (SVIs) on SW-D3 as default gateways for Remote Clinic subnets.",
        "design": "Interface Vlan10 (.65/27), Vlan30 (.97/27), Vlan50 (.161/28), Vlan60 (.129/27), Vlan99 (.177/28)",
        "configs": "configs/SW-D3/SW-D3.txt",
        "test_id": "TC-L3-04",
        "evidence": "evidence/phase2_TC-L3-04_sw_d3_svis.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-L3-05",
        "domain": "Layer 3 Routing",
        "req": "Route bidirectional IP traffic between trusted clinical (VLAN 10/20) and admin (VLAN 30) zones at wire speed.",
        "design": "Hardware inter-VLAN routing across distribution tier SVIs",
        "configs": "configs/SW-D1/SW-D1.txt, configs/SW-D2/SW-D2.txt",
        "test_id": "TC-L3-05",
        "evidence": "evidence/phase2_TC-L3-05_inter_vlan_pings.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-L3-06",
        "domain": "Layer 3 Routing",
        "req": "Configure routed point-to-point links (no switchport) between distribution switches and core routers.",
        "design": "Gi0/2 on SW-D1/D2 and Gi0/1 on SW-D3 configured as no switchport /30 routed links",
        "configs": "configs/SW-D1/SW-D1.txt, configs/SW-D2/SW-D2.txt, configs/SW-D3/SW-D3.txt, configs/R1/R1.txt, configs/R2/R2.txt",
        "test_id": "TC-L3-06",
        "evidence": "evidence/phase2_TC-L3-06_routed_uplinks.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },

    # -------------------------------------------------------------------------
    # DOMAIN 5: DYNAMIC ROUTING & WAN FAILOVER (Section 4.2 Objective 4 & Section 6.2)
    # -------------------------------------------------------------------------
    {
        "id": "REQ-RT-01",
        "domain": "Dynamic Routing",
        "req": "Configure multi-area OSPF Process 1 with R1 anchoring Backbone Area 0.",
        "design": "OSPF process 1, router-id 172.16.4.200, advertising LAN and primary WAN into Area 0",
        "configs": "configs/R1/R1.txt",
        "test_id": "TC-RT-01",
        "evidence": "evidence/phase4_TC-RT-01_r1_ospf_area0.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-RT-02",
        "domain": "Dynamic Routing",
        "req": "Configure R2 as an OSPF Area Border Router (ABR) bridging Area 0 and Area 1.",
        "design": "OSPF process 1 on R2 with Se0/0/0 in Area 0 and Gi0/0 in Area 1",
        "configs": "configs/R2/R2.txt",
        "test_id": "TC-RT-02",
        "evidence": "evidence/phase4_TC-RT-02_r2_abr_status.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-RT-03",
        "domain": "Dynamic Routing",
        "req": "Originate default route from R1 into OSPF topology via default-information originate.",
        "design": "R1 default-information originate propagating 0.0.0.0/0 to SW-D1, SW-D2, and R2",
        "configs": "configs/R1/R1.txt",
        "test_id": "TC-RT-03",
        "evidence": "evidence/phase4_TC-RT-03_ospf_default_route.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-RT-04",
        "domain": "Dynamic Routing",
        "req": "Establish OSPF neighbor adjacency over Primary WAN link (Serial0/0/0) between R1 and R2.",
        "design": "OSPF Hello/Dead timers on 172.16.4.192/30; show ip ospf neighbor reaching FULL state",
        "configs": "configs/R1/R1.txt, configs/R2/R2.txt",
        "test_id": "TC-RT-04",
        "evidence": "evidence/phase4_TC-RT-04_ospf_neighbor_full.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-RT-05",
        "domain": "Dynamic Routing",
        "req": "Configure EIGRP AS 100 on Secondary WAN link (Serial0/0/1) as backup path.",
        "design": "router eigrp 100 on 172.16.4.196/30 between R1 and R2",
        "configs": "configs/R1/R1.txt, configs/R2/R2.txt",
        "test_id": "TC-RT-05",
        "evidence": "evidence/phase4_TC-RT-05_eigrp_neighbor.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-RT-06",
        "domain": "Dynamic Routing",
        "req": "Raise EIGRP Internal Administrative Distance to 120 so OSPF (AD 110) is strictly preferred.",
        "design": "distance eigrp 120 170 configured under router eigrp 100 on R1 and R2",
        "configs": "configs/R1/R1.txt, configs/R2/R2.txt",
        "test_id": "TC-RT-06",
        "evidence": "evidence/phase4_TC-RT-06_ad_tuning_proof.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-RT-07",
        "domain": "Dynamic Routing",
        "req": "Verify normal routing state installs OSPF inter-area routes (O IA) in R1 and R2 routing tables.",
        "design": "show ip route shows O IA via Se0/0/0, not D via Se0/0/1",
        "configs": "configs/R1/R1.txt, configs/R2/R2.txt",
        "test_id": "TC-RT-07",
        "evidence": "evidence/phase4_TC-RT-07_ospf_routes_installed.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-RT-08",
        "domain": "Dynamic Routing",
        "req": "Induce primary WAN link failure via administrative shutdown of Serial0/0/0.",
        "design": "Simulate fiber/cable cut: interface Serial0/0/0 shutdown on R1",
        "configs": "configs/R1/R1.txt",
        "test_id": "TC-RT-08",
        "evidence": "evidence/phase4_TC-RT-08_primary_link_shutdown.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-RT-09",
        "domain": "Dynamic Routing",
        "req": "Verify automatic rerouting onto backup EIGRP path (Serial0/0/1) upon primary failure.",
        "design": "EIGRP routes installed with AD 120 (code D in show ip route) without manual intervention",
        "configs": "configs/R1/R1.txt, configs/R2/R2.txt",
        "test_id": "TC-RT-09",
        "evidence": "evidence/phase4_TC-RT-09_failover_eigrp_installed.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-RT-10",
        "domain": "Dynamic Routing",
        "req": "Measure routing convergence time during induced primary link failure using timed ICMP echo streams.",
        "design": "Continuous ping -t from Remote Clinic to Main Server during shutdown; count lost packets",
        "configs": "configs/R1/R1.txt, docs/simulation_guide.md",
        "test_id": "TC-RT-10",
        "evidence": "evidence/phase4_TC-RT-10_convergence_timing_log.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-RT-11",
        "domain": "Dynamic Routing",
        "req": "Verify automatic restoration and preemption of OSPF routes when Serial0/0/0 is brought back up.",
        "design": "no shutdown on Serial0/0/0; OSPF routes automatically replace EIGRP routes in RIB",
        "configs": "configs/R1/R1.txt",
        "test_id": "TC-RT-11",
        "evidence": "evidence/phase4_TC-RT-11_ospf_restoration.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },

    # -------------------------------------------------------------------------
    # DOMAIN 6: SECURITY POLICIES, ACLs & NAT (Section 4.2 Objective 5 & Section 6.2)
    # -------------------------------------------------------------------------
    {
        "id": "REQ-SEC-01",
        "domain": "Security & ACLs",
        "req": "Enforce ACL blocking Guest VLAN 40 traffic from reaching ICU bedside monitors (VLAN 10).",
        "design": "deny ip 172.16.0.0 0.0.1.255 172.16.3.128 0.0.0.63 in BLOCK-GUEST ACL on SW-D2 Vlan40",
        "configs": "configs/SW-D2/SW-D2.txt",
        "test_id": "TC-SEC-01",
        "evidence": "evidence/phase3_TC-SEC-01_guest_to_icu_denied.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-SEC-02",
        "domain": "Security & ACLs",
        "req": "Enforce ACL blocking Guest VLAN 40 traffic from reaching Operating Theatres (VLAN 20).",
        "design": "deny ip 172.16.0.0 0.0.1.255 172.16.3.192 0.0.0.63 in BLOCK-GUEST ACL on SW-D2 Vlan40",
        "configs": "configs/SW-D2/SW-D2.txt",
        "test_id": "TC-SEC-02",
        "evidence": "evidence/phase3_TC-SEC-02_guest_to_surgery_denied.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-SEC-03",
        "domain": "Security & ACLs",
        "req": "Enforce ACL blocking Guest VLAN 40 traffic from reaching Server Farm EHR records (VLAN 50).",
        "design": "deny ip 172.16.0.0 0.0.1.255 172.16.4.0 0.0.0.31 in BLOCK-GUEST ACL on SW-D2 Vlan40",
        "configs": "configs/SW-D2/SW-D2.txt",
        "test_id": "TC-SEC-03",
        "evidence": "evidence/phase3_TC-SEC-03_guest_to_servers_denied.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-SEC-04",
        "domain": "Security & ACLs",
        "req": "Enforce ACL blocking Guest VLAN 40 traffic from reaching Management SVI (VLAN 99).",
        "design": "deny ip 172.16.0.0 0.0.1.255 172.16.4.32 0.0.0.31 in BLOCK-GUEST ACL on SW-D2 Vlan40",
        "configs": "configs/SW-D2/SW-D2.txt",
        "test_id": "TC-SEC-04",
        "evidence": "evidence/phase3_TC-SEC-04_guest_to_mgmt_denied.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-SEC-05",
        "domain": "Security & ACLs",
        "req": "Explicitly permit Guest VLAN 40 devices to query internal DNS resolver on UDP port 53.",
        "design": "permit udp 172.16.0.0 0.0.1.255 host 172.16.4.2 eq domain placed before denies in ACL",
        "configs": "configs/SW-D2/SW-D2.txt",
        "test_id": "TC-SEC-05",
        "evidence": "evidence/phase3_TC-SEC-05_guest_dns_permitted.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-SEC-06",
        "domain": "Security & ACLs",
        "req": "Explicitly permit Guest VLAN 40 devices to lease IP addresses via DHCP (UDP 67/68).",
        "design": "permit udp 172.16.0.0 0.0.1.255 host 172.16.4.2 eq bootps placed before denies in ACL",
        "configs": "configs/SW-D2/SW-D2.txt",
        "test_id": "TC-SEC-06",
        "evidence": "evidence/phase3_TC-SEC-06_guest_dhcp_permitted.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-SEC-07",
        "domain": "Security & ACLs",
        "req": "Permit Guest VLAN 40 traffic outbound to the external Internet via default permit entry.",
        "design": "permit ip 172.16.0.0 0.0.1.255 any at the conclusion of BLOCK-GUEST ACL",
        "configs": "configs/SW-D2/SW-D2.txt",
        "test_id": "TC-SEC-07",
        "evidence": "evidence/phase3_TC-SEC-07_guest_internet_permitted.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-SEC-08",
        "domain": "Security & ACLs",
        "req": "Validate Guest isolation enforcement using Cisco IOS ACL match and drop counters.",
        "design": "show access-lists BLOCK-GUEST verifying increments on deny statements",
        "configs": "configs/SW-D2/SW-D2.txt",
        "test_id": "TC-SEC-08",
        "evidence": "evidence/phase3_TC-SEC-08_acl_drop_counters.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-SEC-09",
        "domain": "Security & ACLs",
        "req": "Configure Port Address Translation (NAT Overload) on R1 translating 172.16.0.0/16 to public IP.",
        "design": "ip nat inside source list NAT-ACL interface Gig0/2 overload on R1",
        "configs": "configs/R1/R1.txt",
        "test_id": "TC-SEC-09",
        "evidence": "evidence/phase3_TC-SEC-09_nat_translations.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-SEC-10",
        "domain": "Security & ACLs",
        "req": "Enforce Layer 2 port security with MAC limiting and restrict violation on access switches.",
        "design": "switchport port-security maximum 2, violation restrict, mac-address sticky on access ports",
        "configs": "configs/SW-A1/SW-A1.txt, configs/SW-A2/SW-A2.txt, configs/SW-A3/SW-A3.txt",
        "test_id": "TC-SEC-10",
        "evidence": "evidence/phase3_TC-SEC-10_port_security_status.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },

    # -------------------------------------------------------------------------
    # DOMAIN 7: QUALITY OF SERVICE (QoS) POLICIES (Section 4.2 Objective 6)
    # -------------------------------------------------------------------------
    {
        "id": "REQ-QOS-01",
        "domain": "Quality of Service",
        "req": "Classify and mark real-time patient telemetry (UDP) and VoIP traffic with DSCP EF (Expedited Forwarding, 46).",
        "design": "Class-map VITALS-VOICE matching dscp ef applied on Core Routers",
        "configs": "configs/R1/R1.txt, configs/R2/R2.txt",
        "test_id": "TC-QOS-01",
        "evidence": "evidence/phase3_TC-QOS-01_vitals_dscp_ef.png",
        "status": "Not started",
        "pt_flag": "PDU TOS byte inspectable in PT (0xB8). Simulated in Python benchmark."
    },
    {
        "id": "REQ-QOS-02",
        "domain": "Quality of Service",
        "req": "Classify and mark bulk medical imaging transfers (TCP MRI/CT) with DSCP AF31 (Assured Forwarding, 26).",
        "design": "Class-map IMAGING matching dscp af31 applied on Core Routers",
        "configs": "configs/R1/R1.txt, configs/R2/R2.txt",
        "test_id": "TC-QOS-02",
        "evidence": "evidence/phase3_TC-QOS-02_imaging_dscp_af31.png",
        "status": "Not started",
        "pt_flag": "PDU TOS byte inspectable in PT (0x68). Simulated in Python benchmark."
    },
    {
        "id": "REQ-QOS-03",
        "domain": "Quality of Service",
        "req": "Classify Guest Wi-Fi and general admin web browsing as Best-Effort (DSCP 0).",
        "design": "Default class class-default in policy-map HOSPITAL-QOS receiving fair-queue",
        "configs": "configs/R1/R1.txt, configs/R2/R2.txt",
        "test_id": "TC-QOS-03",
        "evidence": "evidence/phase3_TC-QOS-03_best_effort_class.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer."
    },
    {
        "id": "REQ-QOS-04",
        "domain": "Quality of Service",
        "req": "Configure strict priority queuing reserving 30% bandwidth for DSCP EF traffic across WAN links.",
        "design": "priority percent 30 under class VITALS-VOICE in policy-map HOSPITAL-QOS",
        "configs": "configs/R1/R1.txt, configs/R2/R2.txt",
        "test_id": "TC-QOS-04",
        "evidence": "evidence/phase3_TC-QOS-04_priority_queue_config.png",
        "status": "Not started",
        "pt_flag": "PT CLI accepts syntax; real queue scheduling verified via Python harness."
    },
    {
        "id": "REQ-QOS-05",
        "domain": "Quality of Service",
        "req": "Configure bandwidth guarantee reserving 40% bandwidth for DSCP AF31 imaging transfers across WAN links.",
        "design": "bandwidth percent 40 under class IMAGING in policy-map HOSPITAL-QOS",
        "configs": "configs/R1/R1.txt, configs/R2/R2.txt",
        "test_id": "TC-QOS-05",
        "evidence": "evidence/phase3_TC-QOS-05_bandwidth_imaging_config.png",
        "status": "Not started",
        "pt_flag": "PT CLI accepts syntax; real queue scheduling verified via Python harness."
    },
    {
        "id": "REQ-QOS-06",
        "domain": "Quality of Service",
        "req": "Attach QoS service-policy egress on Serial0/0/0 and Serial0/0/1 WAN interfaces.",
        "design": "service-policy output HOSPITAL-QOS on WAN serial interfaces",
        "configs": "configs/R1/R1.txt, configs/R2/R2.txt",
        "test_id": "TC-QOS-06",
        "evidence": "evidence/phase3_TC-QOS-06_service_policy_applied.png",
        "status": "Not started",
        "pt_flag": "Verified via show policy-map interface."
    },

    # -------------------------------------------------------------------------
    # DOMAIN 8: DATA-LINK PROTOCOL SIMULATION ON SBC-PT (Section 4.2 Objective 7 & 6.2)
    # -------------------------------------------------------------------------
    {
        "id": "REQ-SBC-01",
        "domain": "SBC Data-Link Protocol",
        "req": "Program Packet Tracer SBC-PT in Python 3 to simulate 2-Dimensional parity matrix encoding for ICU vitals.",
        "design": "scripts/sbc/parity_2d.py encoding 4 sensor bytes into 8x4 data matrix with row/col parities",
        "configs": "sbc/parity_2d.py",
        "test_id": "TC-SBC-01",
        "evidence": "evidence/phase5_TC-SBC-01_2d_parity_matrix.png",
        "status": "Not started",
        "pt_flag": "Runs inside PT SBC Programming tab / Terminal."
    },
    {
        "id": "REQ-SBC-02",
        "domain": "SBC Data-Link Protocol",
        "req": "Demonstrate single-bit error detection and exact (row, column) coordinate localization in 2-D parity.",
        "design": "verify_and_correct() pinpointing intersecting parity violations",
        "configs": "sbc/parity_2d.py",
        "test_id": "TC-SBC-02",
        "evidence": "evidence/phase5_TC-SBC-02_single_bit_detection.png",
        "status": "Not started",
        "pt_flag": "Runs inside PT SBC Programming tab / Terminal."
    },
    {
        "id": "REQ-SBC-03",
        "domain": "SBC Data-Link Protocol",
        "req": "Demonstrate automatic single-bit error correction (self-healing) using geometric intersection on SBC.",
        "design": "Inverting corrupted bit (0 -> 1 or 1 -> 0) and recovering original vital sign reading",
        "configs": "sbc/parity_2d.py",
        "test_id": "TC-SBC-03",
        "evidence": "evidence/phase5_TC-SBC-03_single_bit_correction.png",
        "status": "Not started",
        "pt_flag": "Runs inside PT SBC Programming tab / Terminal."
    },
    {
        "id": "REQ-SBC-04",
        "domain": "SBC Data-Link Protocol",
        "req": "Demonstrate multi-bit burst error detection and ARQ retransmission trigger in 2-D parity simulation.",
        "design": "Detecting multiple parity violations and triggering retransmission request",
        "configs": "sbc/parity_2d.py",
        "test_id": "TC-SBC-04",
        "evidence": "evidence/phase5_TC-SBC-04_burst_error_detection.png",
        "status": "Not started",
        "pt_flag": "Runs inside PT SBC Programming tab / Terminal."
    },
    {
        "id": "REQ-SBC-05",
        "domain": "SBC Data-Link Protocol",
        "req": "Calculate and report bit overhead ratio for 2-D parity transmission (parity bits / total bits).",
        "design": "Overhead ratio computation: 13 parity bits / 45 total bits = 28.9% overhead",
        "configs": "sbc/parity_2d.py",
        "test_id": "TC-SBC-05",
        "evidence": "evidence/phase5_TC-SBC-05_parity_overhead_log.png",
        "status": "Not started",
        "pt_flag": "Runs inside PT SBC Programming tab / Terminal."
    },
    {
        "id": "REQ-SBC-06",
        "domain": "SBC Data-Link Protocol",
        "req": "Program SBC-PT to compute 16-bit 1's complement Internet Checksum (RFC 1071) for telemetry packets.",
        "design": "compute_checksum_16bit() folding 32-bit addition with end-around carries and bitwise NOT",
        "configs": "sbc/checksum.py",
        "test_id": "TC-SBC-06",
        "evidence": "evidence/phase5_TC-SBC-06_checksum_computation.png",
        "status": "Not started",
        "pt_flag": "Runs inside PT SBC Programming tab / Terminal."
    },
    {
        "id": "REQ-SBC-07",
        "domain": "SBC Data-Link Protocol",
        "req": "Validate error-free telemetry packet at receiver yielding folded sum of 0xFFFF.",
        "design": "verify_checksum_16bit() confirming sum equals 0xFFFF and passing packet to EHR database",
        "configs": "sbc/checksum.py",
        "test_id": "TC-SBC-07",
        "evidence": "evidence/phase5_TC-SBC-07_checksum_valid_pass.png",
        "status": "Not started",
        "pt_flag": "Runs inside PT SBC Programming tab / Terminal."
    },
    {
        "id": "REQ-SBC-08",
        "domain": "SBC Data-Link Protocol",
        "req": "Demonstrate corruption detection and packet rejection when RF noise flips a bit in patient vitals.",
        "design": "verify_checksum_16bit() failing on pulse rate bit-flip and discarding corrupted packet",
        "configs": "sbc/checksum.py",
        "test_id": "TC-SBC-08",
        "evidence": "evidence/phase5_TC-SBC-08_checksum_corrupt_reject.png",
        "status": "Not started",
        "pt_flag": "Runs inside PT SBC Programming tab / Terminal."
    },
    {
        "id": "REQ-SBC-09",
        "domain": "SBC Data-Link Protocol",
        "req": "Benchmark protocol overhead of 16-bit Checksum (14.3%) against 2-D parity (28.9%).",
        "design": "Comparative overhead calculation logged to console",
        "configs": "sbc/checksum.py",
        "test_id": "TC-SBC-09",
        "evidence": "evidence/phase5_TC-SBC-09_checksum_vs_parity_overhead.png",
        "status": "Not started",
        "pt_flag": "Runs inside PT SBC Programming tab / Terminal."
    },
    {
        "id": "REQ-SBC-10",
        "domain": "SBC Data-Link Protocol",
        "req": "Program SBC-PT to simulate Go-Back-N (GBN) sliding window protocol with cumulative ACKs.",
        "design": "GoBackNSimulator class with window size N=4, sliding send_base, and timer timeout",
        "configs": "sbc/go_back_n.py",
        "test_id": "TC-SBC-10",
        "evidence": "evidence/phase5_TC-SBC-10_gbn_execution.png",
        "status": "Not started",
        "pt_flag": "Runs inside PT SBC Programming tab / Terminal."
    },
    {
        "id": "REQ-SBC-11",
        "domain": "SBC Data-Link Protocol",
        "req": "Simulate frame loss in Go-Back-N and verify full-window retransmission from the lost frame.",
        "design": "Simulating frame 3 drop; verifying sender retransmits frames 3, 4, 5, 6 upon timeout",
        "configs": "sbc/go_back_n.py",
        "test_id": "TC-SBC-11",
        "evidence": "evidence/phase5_TC-SBC-11_gbn_retransmission_trace.png",
        "status": "Not started",
        "pt_flag": "Runs inside PT SBC Programming tab / Terminal."
    },
    {
        "id": "REQ-SBC-12",
        "domain": "SBC Data-Link Protocol",
        "req": "Program SBC-PT to simulate Selective Repeat (SR) sliding window protocol with out-of-order buffering.",
        "design": "SelectiveRepeatSimulator class with individual ACKs and receiver buffer window N=4",
        "configs": "sbc/selective_repeat.py",
        "test_id": "TC-SBC-12",
        "evidence": "evidence/phase5_TC-SBC-12_sr_execution.png",
        "status": "Not started",
        "pt_flag": "Runs inside PT SBC Programming tab / Terminal."
    },
    {
        "id": "REQ-SBC-13",
        "domain": "SBC Data-Link Protocol",
        "req": "Simulate frame loss in Selective Repeat and verify that ONLY the lost frame is retransmitted.",
        "design": "Simulating frame 3 drop; verifying only frame 3 is resent while 4, 5, 6 remain buffered",
        "configs": "sbc/selective_repeat.py",
        "test_id": "TC-SBC-13",
        "evidence": "evidence/phase5_TC-SBC-13_sr_selective_retx.png",
        "status": "Not started",
        "pt_flag": "Runs inside PT SBC Programming tab / Terminal."
    },
    {
        "id": "REQ-SBC-14",
        "domain": "SBC Data-Link Protocol",
        "req": "Quantitatively compare GBN vs SR: total transmissions, retransmissions, and transfer efficiency.",
        "design": "Comparative table: GBN 70.59% efficiency (5 retx) vs SR 85.71% efficiency (2 retx)",
        "configs": "sbc/selective_repeat.py, sim/benchmark_harness.py",
        "test_id": "TC-SBC-14",
        "evidence": "evidence/phase5_TC-SBC-14_comparative_benchmark_table.png",
        "status": "Not started",
        "pt_flag": "Runs inside PT SBC and host-side harness."
    },

    # -------------------------------------------------------------------------
    # DOMAIN 9: TRANSPORT & APPLICATION SIMULATION ANALYSIS (Section 4.2 Objective 8 & 6.2)
    # -------------------------------------------------------------------------
    {
        "id": "REQ-SIM-01",
        "domain": "Simulation Mode Analysis",
        "req": "Capture and inspect DNS resolution sequence for records.hospital.local in Simulation Mode.",
        "design": "DNS query (UDP port 53) from client to Central Server 172.16.4.2; PDU envelope inspection",
        "configs": "docs/simulation_guide.md, configs/services/server_setup.md",
        "test_id": "TC-SIM-01",
        "evidence": "evidence/phase5_TC-SIM-01_dns_resolution_pdu.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer Simulation Mode."
    },
    {
        "id": "REQ-SIM-02",
        "domain": "Simulation Mode Analysis",
        "req": "Inspect TCP three-way handshake (SYN, SYN-ACK, ACK) during EHR portal HTTP connection establishment.",
        "design": "PDU inspection: Client SYN (Seq=0) -> Server SYN-ACK (Seq=0, Ack=1) -> Client ACK (Seq=1, Ack=1)",
        "configs": "docs/simulation_guide.md",
        "test_id": "TC-SIM-02",
        "evidence": "evidence/phase5_TC-SIM-02_tcp_handshake_pdu.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer Simulation Mode."
    },
    {
        "id": "REQ-SIM-03",
        "domain": "Simulation Mode Analysis",
        "req": "Inspect TCP sequence numbers, acknowledgements, and window sizing progression during HTTP data transfer.",
        "design": "HTTP GET / HTTP/1.1 request followed by 200 OK HTML payload and ACK sequence tracking",
        "configs": "docs/simulation_guide.md",
        "test_id": "TC-SIM-03",
        "evidence": "evidence/phase5_TC-SIM-03_tcp_windowing_pdu.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer Simulation Mode."
    },
    {
        "id": "REQ-SIM-04",
        "domain": "Simulation Mode Analysis",
        "req": "Contrast UDP connectionless vitals streaming against TCP bulk transfer in Simulation Mode.",
        "design": "Inspect PDU headers: UDP has zero connection handshake and 8-byte header; TCP has 20-byte header with ACKs",
        "configs": "docs/simulation_guide.md",
        "test_id": "TC-SIM-04",
        "evidence": "evidence/phase5_TC-SIM-04_tcp_vs_udp_headers.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer Simulation Mode."
    },
    {
        "id": "REQ-SIM-05",
        "domain": "Simulation Mode Analysis",
        "req": "Verify DHCP DORA exchange (Discover, Offer, Request, ACK) across DHCP Relay helper addresses.",
        "design": "UDP 67/68 broadcast converted to unicast to 172.16.4.2 via ip helper-address",
        "configs": "docs/simulation_guide.md, configs/distribution/SW-D1.txt, configs/distribution/SW-D2.txt",
        "test_id": "TC-SIM-05",
        "evidence": "evidence/phase5_TC-SIM-05_dhcp_dora_relay_pdu.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer Simulation Mode."
    },
    {
        "id": "REQ-SIM-06",
        "domain": "Simulation Mode Analysis",
        "req": "Inspect PDU envelope drop event at SW-D2 when Guest client attempts prohibited connection to ICU.",
        "design": "Layer 3 PDU Details showing: 'The packet matches criteria of BLOCK-GUEST ACL. Switch drops packet.'",
        "configs": "docs/simulation_guide.md, configs/SW-D2/SW-D2.txt",
        "test_id": "TC-SIM-06",
        "evidence": "evidence/phase5_TC-SIM-06_acl_pdu_drop_event.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer Simulation Mode."
    },
    {
        "id": "REQ-SIM-07",
        "domain": "Simulation Mode Analysis",
        "req": "Capture OSPF Hello timeout and LSA flooding during induced link failure in Simulation Mode.",
        "design": "Filter for OSPF; step through Hello timeout on Serial0/0/0 and topology update to EIGRP",
        "configs": "docs/simulation_guide.md",
        "test_id": "TC-SIM-07",
        "evidence": "evidence/phase5_TC-SIM-07_ospf_lsa_failover_pdu.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer Simulation Mode."
    },
    {
        "id": "REQ-SIM-08",
        "domain": "Simulation Mode Analysis",
        "req": "Inspect NAT PAT packet translation across R1 Gig0/2 in Simulation Mode.",
        "design": "Inbound PDU shows 172.16.x.x; Outbound PDU shows translated source IP 203.0.113.2 with unique port",
        "configs": "docs/simulation_guide.md, configs/R1/R1.txt",
        "test_id": "TC-SIM-08",
        "evidence": "evidence/phase5_TC-SIM-08_nat_pat_pdu_translation.png",
        "status": "Not started",
        "pt_flag": "Fully supported in Packet Tracer Simulation Mode."
    }
]

def generate_csv(requirements, filepath):
    fieldnames = [
        "Req-ID",
        "Requirement",
        "Design element that satisfies it",
        "Config file(s)",
        "Verification test ID",
        "Evidence file",
        "Status"
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in requirements:
            writer.writerow({
                "Req-ID": r["id"],
                "Requirement": r["req"],
                "Design element that satisfies it": r["design"],
                "Config file(s)": r["configs"],
                "Verification test ID": r["test_id"],
                "Evidence file": r["evidence"],
                "Status": r["status"]
            })

def generate_markdown(requirements, filepath):
    total = len(requirements)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Requirements Traceability Matrix\n\n")
        f.write("**Project:** Disaster-Resilient Smart Hospital Network with Protocol Simulation in Cisco Packet Tracer  \n")
        f.write("**Course:** Computer Networks — VIT Vellore, SCOPE  \n")
        f.write("**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  \n")
        f.write(f"**Total Atomic Requirements:** {total} (Decomposed from Review-1 Report Sections 4.2 & 6.2)  \n\n")

        f.write("## 1. Traceability Matrix Table\n\n")
        f.write("| Req-ID | Requirement | Design element that satisfies it | Config file(s) | Verification test ID | Evidence file | Status |\n")
        f.write("| :--- | :--- | :--- | :--- | :---: | :--- | :---: |\n")

        current_domain = None
        for r in requirements:
            if r["domain"] != current_domain:
                current_domain = r["domain"]
                f.write(f"| **--** | **SECTION: {current_domain.upper()}** | -- | -- | -- | -- | -- |\n")
            f.write(f"| **{r['id']}** | {r['req']} | {r['design']} | `{r['configs']}` | `{r['test_id']}` | `{r['evidence']}` | {r['status']} |\n")

        f.write("\n---\n\n")
        f.write("## 2. Packet Tracer Simulation Limitations & Demonstration Strategy\n\n")
        f.write("The following requirements involve protocols or features with known emulation constraints in Cisco Packet Tracer 8.x. The table below details the constraint and the hybrid demonstration strategy used to rigorously validate each requirement:\n\n")

        f.write("| Req-ID | Area | Packet Tracer 8.x Limitation | Proposed Demonstration Strategy |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        f.write("| **REQ-QOS-01** to **REQ-QOS-06** | Quality of Service (QoS) & Queuing | Cisco Packet Tracer's software emulator accepts MQC CLI syntax (`priority percent`, `bandwidth percent`, `class-map`, `policy-map`), but its event engine does not enforce true hardware Low-Latency Queuing (LLQ) or CBWFQ packet drops during heavy link saturation. | **Dual Verification:**<br>1. Cisco IOS verification: Execute `show policy-map interface Serial0/0/0` and `show class-map` on R1/R2.<br>2. PDU Envelope inspection: Inspect the Type of Service (TOS) / DSCP byte in Simulation Mode (displays `0xB8` for EF, `0x68` for AF31).<br>3. Host-Side Simulation: Execute `sim/benchmark_harness.py` to mathematically evaluate and chart bandwidth reservation curves under simulated congestion. |\n")
        f.write("| **REQ-SBC-01** to **REQ-SBC-14** | SBC Protocol Simulations | Cisco Packet Tracer's SBC-PT embedded Python environment does not support standard Berkeley socket networking (`import socket` is restricted/missing in PT MicroPython). Direct socket-to-socket socket transmission cannot be performed between two SBC devices across the topology. | **Embedded Terminal Demonstration:**<br>1. Embedded execution: Scripts (`parity_2d.py`, `checksum.py`, `go_back_n.py`, `selective_repeat.py`) are loaded into the SBC-PT **Programming** tab and executed natively. Logs and protocol state matrices are captured in the SBC **Terminal** tab.<br>2. Host-Side Test Harness: The identical protocol engines are tested and benchmarked on a standard workstation using `sim/test_protocols.py` and `sim/benchmark_harness.py`. |\n")
        f.write("| **REQ-SEC-01** to **REQ-SEC-04** | Stateful Deep Packet Inspection | Cisco Packet Tracer does not support Cisco Zone-Based Policy Firewall (ZFW) Layer 7 stateful inspection of healthcare-specific protocols (DICOM, HL7). | **Stateless ACL Enforcement:**<br>1. Extended Access Control Lists (`BLOCK-GUEST`) are applied at the Layer 3 Distribution switch SVIs.<br>2. Enforcement is verified via Cisco IOS ACL match/drop counters (`show access-lists BLOCK-GUEST`) and Simulation Mode PDU drop envelopes showing red discard indicators. |\n")

def main():
    os.makedirs(DOCS_DIR, exist_ok=True)
    csv_file = os.path.join(DOCS_DIR, "traceability_matrix.csv")
    md_file  = os.path.join(DOCS_DIR, "traceability_matrix.md")

    generate_csv(REQUIREMENTS, csv_file)
    generate_markdown(REQUIREMENTS, md_file)

    print(f"[OK] Generated {csv_file} ({len(REQUIREMENTS)} requirements)")
    print(f"[OK] Generated {md_file}")

if __name__ == "__main__":
    main()
