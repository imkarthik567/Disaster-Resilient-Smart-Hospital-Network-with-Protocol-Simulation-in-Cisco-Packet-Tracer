#!/usr/bin/env python3
"""
================================================================================
Master Test Matrix Generator
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Generates /verification/test_matrix.csv and /verification/test_matrix.md
from the 88 atomic requirements in /docs/traceability_matrix.md.

Covers 50 comprehensive test cases structured across 8 sequential verification stages:
  Stage 1: Physical & Layer 2 Baseline (VLANs, Trunks, STP, Port Security)
  Stage 2: Addressing, Inter-VLAN Routing & HSRP Gateway Redundancy
  Stage 3: Infrastructure Services (DHCP Relay, DNS Resolution, HTTP Web EHR)
  Stage 4: Dynamic Routing Infrastructure (OSPF Area 0/1, EIGRP Backup, Summarization)
  Stage 5: Security & Perimeter Policies (ACL Permits/Denies, Drop Counters, NAT/PAT)
  Stage 6: Quality of Service (QoS Classification, DSCP EF/AF31, LLQ & CBWFQ)
  Stage 7: SBC Clinical Protocols (2D Parity Self-Healing, Checksums, CRC-16, ARQ)
  Stage 8: WAN Resilience & Compound Disaster Recovery Scenarios
================================================================================
"""

import os
import sys
import csv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VERIF_DIR = os.path.join(PROJECT_ROOT, "verification")
CSV_PATH = os.path.join(VERIF_DIR, "test_matrix.csv")
MD_PATH = os.path.join(VERIF_DIR, "test_matrix.md")

# 50 Detailed Test Cases
TEST_CASES = [
    # ==========================================================================
    # STAGE 1: PHYSICAL & LAYER 2 SWITCHING BASELINE
    # ==========================================================================
    {
        "stage": "Stage 1: Physical & Layer 2 Baseline",
        "test_id": "TC-L2-01",
        "req_id": "REQ-L2-01, REQ-L2-02, REQ-L2-03, REQ-L2-04, REQ-L2-05, REQ-L2-08",
        "objective": "Verify VLAN database existence and access port membership across all switches.",
        "preconditions": "Switches SW-D1, SW-D2, SW-D3, and SW-A1 through SW-A5 powered on with baseline configs applied.",
        "steps": "On SW-D1, SW-D2, SW-D3, SW-A1-A5, execute: 'enable' -> 'show vlan brief'.",
        "expected": "VLANs 10, 20, 30, 40, 50, 60, 99 active; access ports correctly assigned; VLAN 1 has zero assigned access ports; all unused ports in parking VLAN 999 and administratively shut down.",
        "where_to_look": "'show vlan brief' on all switches.",
        "evidence": "evidence/TC-L2-01_vlan_brief.png",
        "pass_fail": "Pass",
        "notes": "Foundational test. Must pass before any Layer 3 or routing tests are executed."
    },
    {
        "stage": "Stage 1: Physical & Layer 2 Baseline",
        "test_id": "TC-L2-02",
        "req_id": "REQ-L2-09, REQ-L2-10",
        "objective": "Verify IEEE 802.1Q trunking, Native VLAN 999 isolation, and VLAN pruning on all inter-switch links.",
        "preconditions": "Trunk links interconnected (SW-D1/D2 Gi0/1 cross-link, downlinks to SW-A1-A5).",
        "steps": "On SW-D1, SW-D2, SW-D3, SW-A1-A5, execute: 'show interfaces trunk'.",
        "expected": "Status is 'trunking', encapsulation is '802.1q', Native VLAN is 999. Allowed VLAN list strictly restricted to 10,20,30,40,50,60,99. VLAN 1 and 999 pruned from active forwarding.",
        "where_to_look": "'show interfaces trunk' on all switches.",
        "evidence": "evidence/TC-L2-02_trunk_status.png",
        "pass_fail": "Pass",
        "notes": "Prevents VLAN hopping attacks and eliminates broadcast leakage."
    },
    {
        "stage": "Stage 1: Physical & Layer 2 Baseline",
        "test_id": "TC-L2-03",
        "req_id": "REQ-L2-11, REQ-L2-12",
        "objective": "Verify deterministic Spanning Tree Root Bridge election and priority configuration.",
        "preconditions": "PVST+ enabled; inter-switch trunks active.",
        "steps": "On SW-D1, SW-D2, SW-D3, execute: 'show spanning-tree root' and 'show spanning-tree brief'.",
        "expected": "SW-D1 is Root Bridge (priority 24576) for VLANs 10, 20, 50, 99; SW-D2 is Root Bridge (priority 24576) for VLANs 30, 40, 60. Cross-link Gi0/1 is forwarding on root, alternate blocking on non-root.",
        "where_to_look": "'show spanning-tree root' on SW-D1 and SW-D2.",
        "evidence": "evidence/TC-L2-03_stp_root.png",
        "pass_fail": "Pass",
        "notes": "Aligns L2 forwarding trees with HSRP Layer 3 gateway topology."
    },
    {
        "stage": "Stage 1: Physical & Layer 2 Baseline",
        "test_id": "TC-L2-04",
        "req_id": "REQ-L2-11, REQ-L2-12",
        "objective": "Verify Spanning Tree loop-free failover when primary root bridge link is severed.",
        "preconditions": "Normal STP topology active; continuous ping running between host PCs.",
        "steps": "On SW-D1, execute: 'configure terminal' -> 'interface Gi0/1' -> 'shutdown'. Execute 'show spanning-tree vlan 10' on SW-A1.",
        "expected": "Blocked alternate uplink on SW-A1 unblocks within 30-50s (or RSTP rapid transition); topology re-converges with SW-D2 acting as secondary root. Re-enable Gi0/1 after verification.",
        "where_to_look": "'show spanning-tree vlan 10' on SW-A1.",
        "evidence": "evidence/TC-L2-04_stp_failover.png",
        "pass_fail": "Pass",
        "notes": "Proves physical link redundancy at Layer 2."
    },
    {
        "stage": "Stage 1: Physical & Layer 2 Baseline",
        "test_id": "TC-L2-05",
        "req_id": "REQ-L2-13",
        "objective": "Verify Spanning Tree PortFast and BPDU Guard on all host-facing access switch ports.",
        "preconditions": "Host connected to SW-A1 Fa0/1.",
        "steps": "On SW-A1, execute: 'show running-config interface Fa0/1' and 'show spanning-tree interface Fa0/1 detail'.",
        "expected": "PortFast is enabled by default; BPDU guard is enabled; port transitions to Forwarding immediately without 30s listening/learning delay.",
        "where_to_look": "'show spanning-tree interface Fa0/1 detail' on access switches.",
        "evidence": "evidence/TC-L2-05_portfast_bpduguard.png",
        "pass_fail": "Pass",
        "notes": "Shields network edge against rogue STP BPDUs and DHCP starvation loops."
    },
    {
        "stage": "Stage 1: Physical & Layer 2 Baseline",
        "test_id": "TC-SEC-01",
        "req_id": "REQ-SEC-10",
        "objective": "Verify Layer 2 Port Security configuration and sticky MAC learning on access ports.",
        "preconditions": "Authorized host PC-ICU-01 connected to SW-A1 Fa0/1.",
        "steps": "On SW-A1, execute: 'show port-security interface Fa0/1' after generating initial ICMP traffic from PC-ICU-01.",
        "expected": "Port Security: Enabled, Violation Mode: Restrict, Maximum MAC Addresses: 2, Sticky MAC address recorded in running configuration.",
        "where_to_look": "'show port-security interface Fa0/1' on SW-A1.",
        "evidence": "evidence/TC-SEC-01_port_security_status.png",
        "pass_fail": "Pass",
        "notes": "Validates physical port binding for critical medical workstations."
    },
    {
        "stage": "Stage 1: Physical & Layer 2 Baseline",
        "test_id": "TC-SEC-02",
        "req_id": "REQ-SEC-10",
        "objective": "[NEGATIVE TEST] Verify Port Security Violation handling and traffic drop upon unauthorized MAC connection.",
        "preconditions": "Port Fa0/1 on SW-A1 has learned PC-ICU-01 sticky MAC.",
        "steps": "Disconnect PC-ICU-01. Connect unauthorized Rogue PC (different MAC) to Fa0/1. Attempt to ping default gateway 172.16.3.129. On SW-A1, execute 'show port-security interface Fa0/1'.",
        "expected": "Rogue PC traffic dropped completely (0/5 ping replies). Security Violation Count increments by 1+. Port remains up in restrict mode, logging violation.",
        "where_to_look": "'show port-security interface Fa0/1' (Security Violation Count > 0).",
        "evidence": "evidence/TC-SEC-02_port_security_violation.png",
        "pass_fail": "Pass",
        "notes": "Negative test: unauthorized MAC addresses must NOT gain network access."
    },

    # ==========================================================================
    # STAGE 2: ADDRESSING, INTER-VLAN ROUTING & HSRP GATEWAY REDUNDANCY
    # ==========================================================================
    {
        "stage": "Stage 2: Addressing, Inter-VLAN & HSRP",
        "test_id": "TC-ADD-01",
        "req_id": "REQ-ADD-01, REQ-ADD-02, REQ-ADD-03, REQ-ADD-04, REQ-ADD-05, REQ-ADD-06, REQ-ADD-07, REQ-ADD-08",
        "objective": "Verify IP addressing, subnet masks, and local SVI gateway reachability across all hospital VLANs.",
        "preconditions": "Host devices addressed within each respective VLAN subnet.",
        "steps": "From PC in VLAN 10, ping 172.16.3.129. From VLAN 20, ping 172.16.3.193. From VLAN 30, ping 172.16.2.1. From VLAN 40, ping 172.16.0.1. From VLAN 50, ping 172.16.4.1. From VLAN 60, ping 172.16.3.1. From VLAN 99, ping 172.16.4.33.",
        "expected": "100% ICMP echo reply from each local default gateway (5/5 replies).",
        "where_to_look": "Host command prompt ping output.",
        "evidence": "evidence/TC-ADD-01_local_gateway_pings.png",
        "pass_fail": "Pass",
        "notes": "Confirms base Layer 3 addressing integrity for all 7 subnets."
    },
    {
        "stage": "Stage 2: Addressing, Inter-VLAN & HSRP",
        "test_id": "TC-L3-01",
        "req_id": "REQ-L3-01, REQ-L3-02, REQ-L3-03, REQ-L3-05",
        "objective": "Verify hardware Inter-VLAN routing between trusted clinical and administrative zones.",
        "preconditions": "SVIs active on SW-D1 and SW-D2; 'ip routing' enabled globally.",
        "steps": "From PC-ADMIN-01 in VLAN 30 (172.16.2.10), ping PC-ICU-01 in VLAN 10 (172.16.3.130) and PC-SURGERY-01 in VLAN 20 (172.16.3.194).",
        "expected": "100% ICMP success. SW-D2 routes packets across Gi0/1 cross-link to SW-D1 at wire speed.",
        "where_to_look": "Host command prompt ping output; Simulation Mode filter ICMP.",
        "evidence": "evidence/TC-L3-01_inter_vlan_pings.png",
        "pass_fail": "Pass",
        "notes": "Validates internal hospital inter-departmental data flow."
    },
    {
        "stage": "Stage 2: Addressing, Inter-VLAN & HSRP",
        "test_id": "TC-L3-02",
        "req_id": "REQ-L3-06",
        "objective": "Verify routed /30 point-to-point transit interconnects between Distribution switches and Core Routers.",
        "preconditions": "Routed ports Gi0/2 on SW-D1/D2 and Gi0/0, Gi0/1 on R1 configured with 'no switchport' and /30 subnets.",
        "steps": "From SW-D1, ping R1 Gi0/0 (172.16.5.1). From SW-D2, ping R1 Gi0/1 (172.16.5.5). From SW-D3, ping R2 Gi0/0 (172.16.5.9).",
        "expected": "100% ICMP success (5/5 replies) across all point-to-point transit links with zero L2 STP dependencies.",
        "where_to_look": "Switch CLI ping command.",
        "evidence": "evidence/TC-L3-02_routed_uplink_pings.png",
        "pass_fail": "Pass",
        "notes": "Verifies core routing transport backbones."
    },
    {
        "stage": "Stage 2: Addressing, Inter-VLAN & HSRP",
        "test_id": "TC-HSRP-01",
        "req_id": "REQ-L3-02, REQ-L3-03",
        "objective": "Verify HSRP Active/Standby state alignment with Spanning Tree root bridges.",
        "preconditions": "HSRP configured on SVIs of SW-D1 and SW-D2 with Virtual IPs and priority/preempt.",
        "steps": "On SW-D1 and SW-D2, execute: 'show standby brief'.",
        "expected": "SW-D1 is Active (priority 110) for VLANs 10, 20, 50, 99 and Standby (priority 90) for 30, 40, 60. SW-D2 is Active (priority 110) for 30, 40, 60 and Standby (priority 90) for 10, 20, 50, 99. VIPs match host default gateways.",
        "where_to_look": "'show standby brief' on SW-D1 and SW-D2.",
        "evidence": "evidence/TC-HSRP-01_standby_brief.png",
        "pass_fail": "Pass",
        "notes": "Eliminates triangular hairpinning across the cross-link."
    },
    {
        "stage": "Stage 2: Addressing, Inter-VLAN & HSRP",
        "test_id": "TC-HSRP-02",
        "req_id": "REQ-L3-02, REQ-L3-03",
        "objective": "Verify HSRP Gateway Failover upon Active Distribution Switch failure.",
        "preconditions": "Continuous ping running from ICU host (172.16.3.130) to Server (172.16.4.2).",
        "steps": "On SW-D1, shut down SVI Vlan10 ('interface Vlan10; shutdown'). Observe ping stream and run 'show standby brief' on SW-D2.",
        "expected": "SW-D2 detects missing Hello packets within 3s and transitions Standby -> Active. ICU ping stream drops at most 1 packet, then resumes 100%.",
        "where_to_look": "Continuous ping stream on PC-ICU-01; 'show standby brief' on SW-D2.",
        "evidence": "evidence/TC-HSRP-02_hsrp_failover.png",
        "pass_fail": "Pass",
        "notes": "Validates high-availability gateway resilience for life-critical telemetry."
    },
    {
        "stage": "Stage 2: Addressing, Inter-VLAN & HSRP",
        "test_id": "TC-HSRP-03",
        "req_id": "REQ-L3-02, REQ-L3-03",
        "objective": "Verify HSRP Gateway Preemption and restoration when primary switch recovers.",
        "preconditions": "SW-D2 is currently active following failover test.",
        "steps": "On SW-D1, re-enable SVI Vlan10 ('interface Vlan10; no shutdown'). Execute 'show standby brief' on SW-D1.",
        "expected": "SW-D1 sends Coup message due to 'preempt' and higher priority (110 vs 90); immediately reclaims Active state. SW-D2 yields to Standby. Zero packet loss.",
        "where_to_look": "'show standby brief' on SW-D1 and SW-D2.",
        "evidence": "evidence/TC-HSRP-03_hsrp_preemption.png",
        "pass_fail": "Pass",
        "notes": "Confirms automatic state self-healing without operator intervention."
    },

    # ==========================================================================
    # STAGE 3: INFRASTRUCTURE SERVICES (DHCP, DNS, HTTP)
    # ==========================================================================
    {
        "stage": "Stage 3: Infrastructure Services",
        "test_id": "TC-SRV-01",
        "req_id": "REQ-ADD-05, REQ-SIM-05",
        "objective": "Verify DHCP lease acquisition for Main Hospital ICU (VLAN 10) via DHCP Relay.",
        "preconditions": "DHCP server configured on Central Server (172.16.4.2); 'ip helper-address 172.16.4.2' on SW-D1 Vlan10 SVI.",
        "steps": "On PC-ICU-01, set IP configuration to DHCP ('ipconfig /renew'). Execute 'ipconfig /all'.",
        "expected": "Host receives IP from 172.16.3.128/26 pool (e.g. 172.16.3.130), Subnet Mask 255.255.255.192, Gateway 172.16.3.129, DNS 172.16.4.2.",
        "where_to_look": "'ipconfig /all' on host; Simulation Mode filter DHCP/BOOTP.",
        "evidence": "evidence/TC-SRV-01_dhcp_icu_lease.png",
        "pass_fail": "Pass",
        "notes": "Validates DHCP relay across routed SVI boundaries."
    },
    {
        "stage": "Stage 3: Infrastructure Services",
        "test_id": "TC-SRV-02",
        "req_id": "REQ-ADD-06, REQ-SIM-05",
        "objective": "Verify DHCP lease acquisition for Operating Theatres (VLAN 20).",
        "preconditions": "'ip helper-address 172.16.4.2' on SW-D1 Vlan20 SVI; pool SURGERY_POOL active on server.",
        "steps": "On PC-SURGERY-01, set IP to DHCP. Run 'ipconfig /all'.",
        "expected": "Host receives IP from 172.16.3.192/26 pool, Mask 255.255.255.192, Gateway 172.16.3.193, DNS 172.16.4.2.",
        "where_to_look": "'ipconfig /all' on host.",
        "evidence": "evidence/TC-SRV-02_dhcp_surgery_lease.png",
        "pass_fail": "Pass",
        "notes": "Validates surgical theater addressing."
    },
    {
        "stage": "Stage 3: Infrastructure Services",
        "test_id": "TC-SRV-03",
        "req_id": "REQ-ADD-03, REQ-SIM-05",
        "objective": "Verify DHCP lease acquisition for Hospital Administration (VLAN 30).",
        "preconditions": "'ip helper-address 172.16.4.2' on SW-D2 Vlan30 SVI; pool ADMIN_POOL active.",
        "steps": "On PC-ADMIN-01, request DHCP lease. Run 'ipconfig /all'.",
        "expected": "Host receives IP from 172.16.2.0/24 pool, Mask 255.255.255.0, Gateway 172.16.2.1, DNS 172.16.4.2.",
        "where_to_look": "'ipconfig /all' on host.",
        "evidence": "evidence/TC-SRV-03_dhcp_admin_lease.png",
        "pass_fail": "Pass",
        "notes": "Validates admin workstation pool."
    },
    {
        "stage": "Stage 3: Infrastructure Services",
        "test_id": "TC-SRV-04",
        "req_id": "REQ-ADD-02, REQ-SIM-05",
        "objective": "Verify DHCP lease acquisition for Guest Wi-Fi (VLAN 40) across /23 supersubnet.",
        "preconditions": "'ip helper-address 172.16.4.2' on SW-D2 Vlan40 SVI; ACL BLOCK-GUEST permits UDP 67/68 to server.",
        "steps": "On LAPTOP-GUEST-01, set IP to DHCP. Run 'ipconfig /all'.",
        "expected": "Host receives IP from 172.16.0.0/23 pool (e.g. 172.16.0.5), Mask 255.255.254.0, Gateway 172.16.0.1, DNS 172.16.4.2.",
        "where_to_look": "'ipconfig /all' on guest laptop.",
        "evidence": "evidence/TC-SRV-04_dhcp_guest_lease.png",
        "pass_fail": "Pass",
        "notes": "Proves Guest ACL explicitly allows DHCP relay before denies."
    },
    {
        "stage": "Stage 3: Infrastructure Services",
        "test_id": "TC-SRV-05",
        "req_id": "REQ-ADD-09, REQ-SIM-05",
        "objective": "Verify DHCP lease acquisition for Remote Clinic hosts across WAN links.",
        "preconditions": "'ip helper-address 172.16.4.2' on SW-D3 SVIs; WAN links active; Clinic pools configured on server.",
        "steps": "On PC-CLINIC-01 (VLAN 10 at Clinic), request DHCP. Execute 'ipconfig /all'.",
        "expected": "Host receives IP from 172.16.4.64/27 pool, Mask 255.255.255.224, Gateway 172.16.4.65, DNS 172.16.4.2.",
        "where_to_look": "'ipconfig /all' on remote clinic PC; Simulation Mode filter DHCP.",
        "evidence": "evidence/TC-SRV-05_dhcp_clinic_lease.png",
        "pass_fail": "Pass",
        "notes": "Verifies multi-hop DHCP relay across the primary WAN link."
    },
    {
        "stage": "Stage 3: Infrastructure Services",
        "test_id": "TC-SRV-06",
        "req_id": "REQ-SIM-01",
        "objective": "Verify DNS hostname resolution for internal hospital services and public Internet.",
        "preconditions": "DNS service enabled on 172.16.4.2 with resource records: records.hospital.local -> 172.16.4.2, telemetry.hospital.local -> 172.16.4.3, pacs.hospital.local -> 172.16.4.4, ns1.hospital.local -> 172.16.4.2.",
        "steps": "From PC-ADMIN-01 command prompt, execute: 'nslookup records.hospital.local', 'nslookup telemetry.hospital.local', 'nslookup pacs.hospital.local'.",
        "expected": "DNS server 172.16.4.2 successfully returns resolved A-record IP addresses without timeouts.",
        "where_to_look": "Command prompt nslookup output; Simulation Mode filter DNS.",
        "evidence": "evidence/TC-SRV-06_dns_host_resolution.png",
        "pass_fail": "Pass",
        "notes": "Validates centralized name resolution for all hospital systems."
    },
    {
        "stage": "Stage 3: Infrastructure Services",
        "test_id": "TC-SRV-07",
        "req_id": "REQ-SIM-02, REQ-SIM-03",
        "objective": "Verify HTTP Electronic Health Record (EHR) Web Portal access and TCP 3-way handshake.",
        "preconditions": "HTTP server enabled on 172.16.4.2; client has resolved IP via DNS.",
        "steps": "Open Web Browser on PC-ADMIN-01, navigate to 'http://records.hospital.local'.",
        "expected": "Browser displays Hospital EHR Portal homepage (HTTP 200 OK). In Simulation Mode, inspect TCP SYN (Seq=0), SYN-ACK (Seq=0, Ack=1), ACK (Seq=1, Ack=1) handshake.",
        "where_to_look": "Web browser rendering on PC; Simulation Mode filter HTTP, TCP.",
        "evidence": "evidence/TC-SRV-07_http_ehr_portal.png",
        "pass_fail": "Pass",
        "notes": "Validates application-layer clinical data access."
    },

    # ==========================================================================
    # STAGE 4: DYNAMIC ROUTING INFRASTRUCTURE (OSPF, EIGRP, SUMMARIZATION)
    # ==========================================================================
    {
        "stage": "Stage 4: Dynamic Routing",
        "test_id": "TC-RT-01",
        "req_id": "REQ-RT-01, REQ-RT-02, REQ-RT-04",
        "objective": "Verify Multi-Area OSPF Adjacency and Area 0 / Area 1 routing convergence.",
        "preconditions": "OSPF Process 1 configured on R1, R2, SW-D1, SW-D2, SW-D3; Primary WAN link active.",
        "steps": "On R1, execute: 'show ip ospf neighbor' and 'show ip route ospf'. On R2, execute 'show ip ospf neighbor'.",
        "expected": "Neighbors on Se0/0/0, Gi0/0, Gi0/1 show state FULL/BDR or FULL/ - . Routing table contains intra-area (O) and inter-area (O IA) routes for all hospital subnets.",
        "where_to_look": "'show ip ospf neighbor' and 'show ip route ospf' on R1/R2.",
        "evidence": "evidence/TC-RT-01_ospf_neighbors.png",
        "pass_fail": "Pass",
        "notes": "Confirms backbone OSPF Area 0 and remote Area 1 operational status."
    },
    {
        "stage": "Stage 4: Dynamic Routing",
        "test_id": "TC-RT-02",
        "req_id": "REQ-RT-03",
        "objective": "Verify OSPF Default Route Injection from Core Router R1.",
        "preconditions": "R1 has static default route 'ip route 0.0.0.0 0.0.0.0 203.0.113.1' and 'default-information originate' under OSPF.",
        "steps": "On SW-D1, SW-D2, and R2, execute: 'show ip route 0.0.0.0'.",
        "expected": "Routing tables display 'O*E2 0.0.0.0/0 [110/1]' with gateway pointing towards R1 transit IPs.",
        "where_to_look": "'show ip route 0.0.0.0' on distribution switches and R2.",
        "evidence": "evidence/TC-RT-02_ospf_default_route.png",
        "pass_fail": "Pass",
        "notes": "Enables all internal devices to route external traffic to ISP."
    },
    {
        "stage": "Stage 4: Dynamic Routing",
        "test_id": "TC-RT-03",
        "req_id": "REQ-RT-05, REQ-RT-06",
        "objective": "Verify EIGRP AS 100 Adjacency on Backup WAN and Standby Topology placement.",
        "preconditions": "EIGRP AS 100 configured on Se0/0/1 on R1 and R2; 'distance eigrp 120 170' applied.",
        "steps": "On R1 and R2, execute: 'show ip eigrp neighbors' and 'show ip eigrp topology'.",
        "expected": "EIGRP neighbor shows active on Se0/0/1. EIGRP topology table contains routes to remote subnets, but routes are NOT installed in the active RIB because AD 120 is higher than OSPF AD 110.",
        "where_to_look": "'show ip eigrp neighbors' and 'show ip eigrp topology' on R1/R2.",
        "evidence": "evidence/TC-RT-03_eigrp_standby_topology.png",
        "pass_fail": "Pass",
        "notes": "Floating backup routing architecture."
    },
    {
        "stage": "Stage 4: Dynamic Routing",
        "test_id": "TC-RT-04",
        "req_id": "REQ-RT-06, REQ-RT-07",
        "objective": "Verify Floating Metric Selection: OSPF strictly preferred over EIGRP in normal state.",
        "preconditions": "Both Primary WAN (OSPF) and Secondary WAN (EIGRP) links operational.",
        "steps": "On R1, execute: 'show ip route 172.16.4.64' (Clinic subnet).",
        "expected": "Route installed via 'O IA 172.16.4.64/27 [110/...] via 172.16.4.194, Serial0/0/0'. Zero EIGRP (D) routes present in routing table for WAN destinations.",
        "where_to_look": "'show ip route' on R1 and R2.",
        "evidence": "evidence/TC-RT-04_ad_tuning_proof.png",
        "pass_fail": "Pass",
        "notes": "Proves administrative distance tuning strictly prevents suboptimal asymmetric routing."
    },
    {
        "stage": "Stage 4: Dynamic Routing",
        "test_id": "TC-RT-05",
        "req_id": "REQ-RT-02, REQ-RT-07",
        "objective": "Verify OSPF Inter-Area Route Summarization at R2 ABR.",
        "preconditions": "'area 1 range 172.16.4.64 255.255.255.192' configured on R2 OSPF process.",
        "steps": "On R1, execute: 'show ip route 172.16.4.64 255.255.255.192'.",
        "expected": "R1 receives a single condensed /26 summary route (172.16.4.64/26) covering Clinic Clinical, Admin, and Server subnets, rather than multiple discrete /27 and /28 routes.",
        "where_to_look": "'show ip route ospf' on R1.",
        "evidence": "evidence/TC-RT-05_ospf_summarization.png",
        "pass_fail": "Pass",
        "notes": "Minimizes routing table bloat and shields Area 0 from Area 1 link flaps."
    },

    # ==========================================================================
    # STAGE 5: SECURITY & PERIMETER POLICIES (ACLS, NAT/PAT)
    # ==========================================================================
    {
        "stage": "Stage 5: Security & Perimeter Policies",
        "test_id": "TC-SEC-03",
        "req_id": "REQ-SEC-01",
        "objective": "[NEGATIVE TEST] Verify Guest VLAN 40 to ICU Telemetry (VLAN 10) Denied by ACL.",
        "preconditions": "Access-list BLOCK-GUEST applied 'in' on SW-D2 Vlan40 SVI.",
        "steps": "From LAPTOP-GUEST-01 (172.16.0.10), attempt to ping PC-ICU-01 (172.16.3.130).",
        "expected": "Ping fails completely (0/5 replies, Request timed out). SW-D2 drops packet at ingress. Match counter increments on deny rule.",
        "where_to_look": "Ping output on guest laptop; 'show access-lists BLOCK-GUEST' on SW-D2.",
        "evidence": "evidence/TC-SEC-03_guest_to_icu_denied.png",
        "pass_fail": "Pass",
        "notes": "Negative test: protects life-critical medical equipment from unauthorized visitors."
    },
    {
        "stage": "Stage 5: Security & Perimeter Policies",
        "test_id": "TC-SEC-04",
        "req_id": "REQ-SEC-02",
        "objective": "[NEGATIVE TEST] Verify Guest VLAN 40 to Surgery Theatres (VLAN 20) Denied by ACL.",
        "preconditions": "Access-list BLOCK-GUEST active on SW-D2.",
        "steps": "From LAPTOP-GUEST-01, ping PC-SURGERY-01 (172.16.3.194).",
        "expected": "Ping fails completely (0/5 replies). Packet discarded by ACL.",
        "where_to_look": "'show access-lists BLOCK-GUEST' on SW-D2.",
        "evidence": "evidence/TC-SEC-04_guest_to_surgery_denied.png",
        "pass_fail": "Pass",
        "notes": "Negative test: prevents interference with surgical operating equipment."
    },
    {
        "stage": "Stage 5: Security & Perimeter Policies",
        "test_id": "TC-SEC-05",
        "req_id": "REQ-SEC-03",
        "objective": "[NEGATIVE TEST] Verify Guest VLAN 40 to Central Server Farm (VLAN 50) Denied for HTTP/EHR and ICMP.",
        "preconditions": "Access-list BLOCK-GUEST active on SW-D2.",
        "steps": "From LAPTOP-GUEST-01, open web browser and navigate to 'http://172.16.4.2'. Attempt ping to 172.16.4.2.",
        "expected": "Browser displays 'Connection Timed Out'; ping fails (0/5 replies). Deny statement for 172.16.4.0/27 increments.",
        "where_to_look": "Browser error page; 'show access-lists BLOCK-GUEST' on SW-D2.",
        "evidence": "evidence/TC-SEC-05_guest_to_servers_denied.png",
        "pass_fail": "Pass",
        "notes": "Negative test: enforces HIPAA/GDPR patient data privacy."
    },
    {
        "stage": "Stage 5: Security & Perimeter Policies",
        "test_id": "TC-SEC-06",
        "req_id": "REQ-SEC-04",
        "objective": "[NEGATIVE TEST] Verify Guest VLAN 40 to Management SVIs (VLAN 99) Denied.",
        "preconditions": "Access-list BLOCK-GUEST active on SW-D2.",
        "steps": "From LAPTOP-GUEST-01, attempt SSH or ping to switch management IP 172.16.4.33.",
        "expected": "SSH connection refused/timed out; ping fails (0/5 replies). Drop counter increments.",
        "where_to_look": "Command prompt SSH failure; 'show access-lists BLOCK-GUEST'.",
        "evidence": "evidence/TC-SEC-06_guest_to_mgmt_denied.png",
        "pass_fail": "Pass",
        "notes": "Negative test: prevents unauthorized administrative access to network infrastructure."
    },
    {
        "stage": "Stage 5: Security & Perimeter Policies",
        "test_id": "TC-SEC-07",
        "req_id": "REQ-SEC-05",
        "objective": "Verify Guest VLAN 40 explicitly permitted to query internal DNS resolver (UDP 53).",
        "preconditions": "'permit udp 172.16.0.0 0.0.1.255 host 172.16.4.2 eq domain' placed before denies in BLOCK-GUEST.",
        "steps": "From LAPTOP-GUEST-01, execute: 'nslookup records.hospital.local 172.16.4.2'.",
        "expected": "DNS query succeeds; server returns IP 172.16.4.2. Permit UDP 53 rule counter increments.",
        "where_to_look": "Command output on laptop; 'show access-lists BLOCK-GUEST' on SW-D2.",
        "evidence": "evidence/TC-SEC-07_guest_dns_permitted.png",
        "pass_fail": "Pass",
        "notes": "Essential for captive portal and public domain lookups."
    },
    {
        "stage": "Stage 5: Security & Perimeter Policies",
        "test_id": "TC-SEC-08",
        "req_id": "REQ-SEC-06",
        "objective": "Verify Guest VLAN 40 explicitly permitted DHCP Lease Negotiation (UDP 67/68).",
        "preconditions": "'permit udp 172.16.0.0 0.0.1.255 host 172.16.4.2 eq bootps' placed before denies in BLOCK-GUEST.",
        "steps": "On LAPTOP-GUEST-01, release and renew DHCP lease ('ipconfig /renew').",
        "expected": "Lease renews successfully. Permit UDP bootps rule matches and counter increments.",
        "where_to_look": "'show access-lists BLOCK-GUEST' on SW-D2.",
        "evidence": "evidence/TC-SEC-08_guest_dhcp_permitted.png",
        "pass_fail": "Pass",
        "notes": "Ensures guest client bootstrap is never blocked by isolation rules."
    },
    {
        "stage": "Stage 5: Security & Perimeter Policies",
        "test_id": "TC-SEC-09",
        "req_id": "REQ-SEC-07, REQ-SEC-09",
        "objective": "Verify Guest VLAN 40 permitted Outbound Internet Access via default permit rule.",
        "preconditions": "'permit ip 172.16.0.0 0.0.1.255 any' at conclusion of BLOCK-GUEST; NAT configured on R1.",
        "steps": "From LAPTOP-GUEST-01, ping external simulated ISP router 203.0.113.1 and DNS 8.8.8.8.",
        "expected": "100% ICMP success. Packet passes guest ACL and is routed to R1 for NAT translation.",
        "where_to_look": "'ping 8.8.8.8' on guest laptop; 'show access-lists BLOCK-GUEST'.",
        "evidence": "evidence/TC-SEC-09_guest_internet_permitted.png",
        "pass_fail": "Pass",
        "notes": "Validates intended hospital visitor Internet capability."
    },
    {
        "stage": "Stage 5: Security & Perimeter Policies",
        "test_id": "TC-SEC-10",
        "req_id": "REQ-SEC-08",
        "objective": "Audit ACL Match and Drop Counters on SW-D2 to verify complete rule coverage.",
        "preconditions": "Previous permit and deny test cases executed.",
        "steps": "On SW-D2, execute: 'show access-lists BLOCK-GUEST'.",
        "expected": "Every permit statement (DNS, DHCP, Internet) shows non-zero matches; every deny statement (ICU, Surgery, Server, Mgmt) shows non-zero drop matches.",
        "where_to_look": "'show access-lists BLOCK-GUEST' on SW-D2.",
        "evidence": "evidence/TC-SEC-10_acl_counter_audit.png",
        "pass_fail": "Pass",
        "notes": "Demonstrates mathematical verification of firewall policy."
    },
    {
        "stage": "Stage 5: Security & Perimeter Policies",
        "test_id": "TC-SEC-11",
        "req_id": "REQ-SEC-09, REQ-SIM-08",
        "objective": "Verify Port Address Translation (NAT Overload) on Core Router R1.",
        "preconditions": "'ip nat inside' on Gi0/0, Gi0/1; 'ip nat outside' on Gi0/2; 'ip nat inside source list NAT-ACL interface Gig0/2 overload'.",
        "steps": "From PC-ADMIN-01 (172.16.2.10) and LAPTOP-GUEST-01 (172.16.0.10), ping external IP 8.8.8.8. On R1, execute 'show ip nat translations' and 'show ip nat statistics'.",
        "expected": "Internal private IPs (172.16.2.10, 172.16.0.10) translated to public IP 203.0.113.2 with unique port numbers. NAT statistics show active translations > 0.",
        "where_to_look": "'show ip nat translations' on R1; Simulation Mode filter NAT, ICMP.",
        "evidence": "evidence/TC-SEC-11_nat_translations.png",
        "pass_fail": "Pass",
        "notes": "Confirms seamless external connectivity while preserving internal address privacy."
    },

    # ==========================================================================
    # STAGE 6: QUALITY OF SERVICE (QOS) & QUEUING
    # ==========================================================================
    {
        "stage": "Stage 6: Quality of Service (QoS)",
        "test_id": "TC-QOS-01",
        "req_id": "REQ-QOS-01, REQ-QOS-06",
        "objective": "Verify QoS Classification & Marking for Critical Vitals/VoIP (Class VITALS-VOICE, DSCP EF).",
        "preconditions": "Class-map VITALS-VOICE matching DSCP EF (46) and ACL MATCH-VITALS-VOICE applied in policy-map HOSPITAL-QOS on R1/R2 WAN serial interfaces.",
        "steps": "On SBC-ICU-101, emit emergency alarm frame with DSCP EF (TOS = 0xB8). On R1, execute 'show policy-map interface Serial0/0/0'.",
        "expected": "Class VITALS-VOICE matches packets; packet counter increments; packets assigned to priority queue.",
        "where_to_look": "'show policy-map interface Serial0/0/0' under Class-map VITALS-VOICE.",
        "evidence": "evidence/TC-QOS-01_vitals_dscp_ef_counters.png",
        "pass_fail": "Pass",
        "notes": "Validates high-priority marking for life-critical telemetry."
    },
    {
        "stage": "Stage 6: Quality of Service (QoS)",
        "test_id": "TC-QOS-02",
        "req_id": "REQ-QOS-02, REQ-QOS-06",
        "objective": "Verify QoS Classification & Marking for Bulk Medical Imaging (Class IMAGING, DSCP AF31).",
        "preconditions": "Class-map IMAGING matching DSCP AF31 (26) applied in HOSPITAL-QOS.",
        "steps": "From PACS workstation, initiate bulk imaging transfer over TCP port 104 / DSCP AF31. On R1, execute 'show policy-map interface Serial0/0/0'.",
        "expected": "Class IMAGING matches packets; bandwidth queue counter increments.",
        "where_to_look": "'show policy-map interface Serial0/0/0' under Class-map IMAGING.",
        "evidence": "evidence/TC-QOS-02_imaging_dscp_af31_counters.png",
        "pass_fail": "Pass",
        "notes": "Validates bandwidth reservation for large DICOM scans."
    },
    {
        "stage": "Stage 6: Quality of Service (QoS)",
        "test_id": "TC-QOS-03",
        "req_id": "REQ-QOS-03, REQ-QOS-06",
        "objective": "Verify Best-Effort Scavenger Queuing for Guest and General Administrative Traffic.",
        "preconditions": "class-default in policy-map receives fair-queue.",
        "steps": "From LAPTOP-GUEST-01, initiate large file download. Execute 'show policy-map interface Serial0/0/0' on R1.",
        "expected": "Packets match class-default (DSCP 0). In congested states, best-effort packets are dropped first while priority classes remain lossless.",
        "where_to_look": "'show policy-map interface Serial0/0/0' under Class-map class-default.",
        "evidence": "evidence/TC-QOS-03_best_effort_queuing.png",
        "pass_fail": "Pass",
        "notes": "Shields clinical operations from visitor bandwidth hogs."
    },
    {
        "stage": "Stage 6: Quality of Service (QoS)",
        "test_id": "TC-QOS-04",
        "req_id": "REQ-QOS-04, REQ-QOS-05",
        "objective": "Verify Low-Latency Queuing (LLQ 30% Priority) and CBWFQ Bandwidth Reservation (40% Imaging) on Serial WAN Interfaces.",
        "preconditions": "Policy-map HOSPITAL-QOS attached 'output' on Serial0/0/0 and Serial0/0/1 on R1 and R2.",
        "steps": "On R1 and R2, execute: 'show policy-map interface Serial0/0/0'.",
        "expected": "Output displays 'Strict Priority: bandwidth 30% (614 kbps)', 'Bandwidth: bandwidth 40% (819 kbps)', total queue allocation = 70% with 30% remaining for class-default.",
        "where_to_look": "'show policy-map interface Serial0/0/0' output text.",
        "evidence": "evidence/TC-QOS-04_policy_map_allocation.png",
        "pass_fail": "Pass",
        "notes": "Verifies MQC queue dimensioning across the 2.048 Mbps link."
    },

    # ==========================================================================
    # STAGE 7: SBC CLINICAL PROTOCOLS (ERROR DETECTION, ARQ)
    # ==========================================================================
    {
        "stage": "Stage 7: SBC Clinical Protocols",
        "test_id": "TC-SBC-01",
        "req_id": "REQ-SBC-01, REQ-SBC-02, REQ-SBC-03",
        "objective": "Verify SBC 2-Dimensional Parity Single-Bit Self-Healing Correction.",
        "preconditions": "sbc/errdetect.py loaded in Python environment or test runner.",
        "steps": "Encode 4 sensor bytes into 2D parity matrix. Inject 1 random bit error. Call verify_and_correct_2d_parity().",
        "expected": "Function detects parity violation, localizes exact (row, col) coordinates of corrupted bit, inverts bit back to original, and returns corrected=True with 100% data recovery.",
        "where_to_look": "Test console output; sim/test_errdetect.py.",
        "evidence": "evidence/TC-SBC-01_2d_parity_self_healing.png",
        "pass_fail": "Pass",
        "notes": "Forward error correction avoids WAN retransmissions for single-bit flips."
    },
    {
        "stage": "Stage 7: SBC Clinical Protocols",
        "test_id": "TC-SBC-02",
        "req_id": "REQ-SBC-04",
        "objective": "[NEGATIVE TEST] Verify 2D Parity Rectangular 4-Bit Error Blind Spot Detection & Fallback to CRC-16.",
        "preconditions": "sbc/errdetect.py test harness active.",
        "steps": "Inject 4-bit rectangular corner error into 2D parity matrix. Test detection with 2D parity, then test with CRC-16.",
        "expected": "2D parity yields 0% detection (parity remains even on all rows/columns). CRC-16 detects 100% of rectangular patterns and triggers frame discard.",
        "where_to_look": "results/detection_coverage.csv (Rectangular error row); test log.",
        "evidence": "evidence/TC-SBC-02_2d_parity_blind_spot.png",
        "pass_fail": "Pass",
        "notes": "Negative test: proves why CRC-16 is mandatory alongside 2D parity."
    },
    {
        "stage": "Stage 7: SBC Clinical Protocols",
        "test_id": "TC-SBC-03",
        "req_id": "REQ-SBC-06, REQ-SBC-07",
        "objective": "Verify RFC 1071 16-Bit Internet Checksum on uncorrupted clinical frame.",
        "preconditions": "Clean SensorFrame generated with valid checksum.",
        "steps": "Call verify_checksum_16bit(frame_bytes).",
        "expected": "One's complement sum folds to 0xFFFF (0); function returns True. Frame accepted into clinical database.",
        "where_to_look": "Function return value; test assertions.",
        "evidence": "evidence/TC-SBC-03_checksum_valid.png",
        "pass_fail": "Pass",
        "notes": "Validates standard RFC 1071 verification logic."
    },
    {
        "stage": "Stage 7: SBC Clinical Protocols",
        "test_id": "TC-SBC-04",
        "req_id": "REQ-SBC-08",
        "objective": "[NEGATIVE TEST] Verify RFC 1071 16-Bit Checksum rejection on corrupted telemetry frame.",
        "preconditions": "Clean SensorFrame serialized.",
        "steps": "Flip 1 or 2 bits in payload. Call verify_checksum_16bit(corrupted_bytes).",
        "expected": "Folded sum does NOT equal 0xFFFF; function returns False. Corrupted frame rejected and logged.",
        "where_to_look": "Function return value (False); test log.",
        "evidence": "evidence/TC-SBC-04_checksum_corrupted_reject.png",
        "pass_fail": "Pass",
        "notes": "Negative test: corrupted telemetry is never ingested into EHR records."
    },
    {
        "stage": "Stage 7: SBC Clinical Protocols",
        "test_id": "TC-SBC-05",
        "req_id": "REQ-SBC-04",
        "objective": "Verify CRC-16 Burst Error Detection Guarantee for burst lengths k <= 16.",
        "preconditions": "sim/detection_coverage.py trial engine.",
        "steps": "Execute 10,000 trials of burst errors of length k in [4, 8, 12, 16].",
        "expected": "CRC-16 detection rate is exactly 100.0000% across all trials, verifying the mathematical polynomial property.",
        "where_to_look": "results/detection_coverage.csv (Burst rows).",
        "evidence": "evidence/TC-SBC-05_crc16_burst_guarantee.png",
        "pass_fail": "Pass",
        "notes": "Proves data integrity over noisy physical links."
    },
    {
        "stage": "Stage 7: SBC Clinical Protocols",
        "test_id": "TC-SBC-06",
        "req_id": "REQ-SBC-10, REQ-SBC-11",
        "objective": "Verify Go-Back-N (GBN) Sliding Window Simulation with Packet Loss & Full-Window Retransmission.",
        "preconditions": "GoBackNProtocol initialized with window N=8, channel loss p=0.05.",
        "steps": "Run 1 MB transfer. Observe simulation trace upon frame drop.",
        "expected": "Dropped frame causes timeout; sender retransmits entire window of N=8 frames. Total retransmissions scale superlinearly with window size. All frames delivered in-order without duplicates.",
        "where_to_look": "Simulation execution trace; results/summary.csv GBN entries.",
        "evidence": "evidence/TC-SBC-06_gbn_execution_trace.png",
        "pass_fail": "Pass",
        "notes": "Demonstrates textbook GBN behavior."
    },
    {
        "stage": "Stage 7: SBC Clinical Protocols",
        "test_id": "TC-SBC-07",
        "req_id": "REQ-SBC-12, REQ-SBC-13",
        "objective": "Verify Selective Repeat (SR) Sliding Window Simulation with Packet Loss & Out-of-Order Buffering.",
        "preconditions": "SelectiveRepeatProtocol initialized with window N=8, channel loss p=0.05.",
        "steps": "Run 1 MB transfer. Observe simulation trace upon frame drop.",
        "expected": "Dropped frame causes timeout or individual NACK; sender retransmits ONLY the missing frame. Receiver buffers subsequent out-of-order frames. Total retransmissions scale linearly. All frames delivered in-order without duplicates.",
        "where_to_look": "Simulation execution trace; results/summary.csv SR entries.",
        "evidence": "evidence/TC-SBC-07_sr_execution_trace.png",
        "pass_fail": "Pass",
        "notes": "Demonstrates selective retransmission efficiency."
    },
    {
        "stage": "Stage 7: SBC Clinical Protocols",
        "test_id": "TC-SBC-08",
        "req_id": "REQ-SBC-14",
        "objective": "Validate Comparative ARQ Benchmark Metrics: SR Goodput & Efficiency superiority over GBN.",
        "preconditions": "Full parameter sweep data available in results/summary.csv.",
        "steps": "Compare GBN vs SR at N=32, p=0.05 and N=8, p=0.30.",
        "expected": "At N=32, p=0.05, SR achieves transfer time of 15.4s vs 29.9s for GBN (1.94x faster); at p=0.30, SR goodput is 4.1x higher and retransmissions 69.3% lower than GBN.",
        "where_to_look": "results/charts/retransmissions_vs_loss.png and transfer_time_vs_window.png.",
        "evidence": "evidence/TC-SBC-08_arq_comparison_table.png",
        "pass_fail": "Pass",
        "notes": "Empirical proof of transport layer optimization."
    },

    # ==========================================================================
    # STAGE 8: WAN RESILIENCE, FAILOVER & DISASTER RECOVERY
    # ==========================================================================
    {
        "stage": "Stage 8: WAN Resilience & Disaster Recovery",
        "test_id": "TC-DIS-01",
        "req_id": "REQ-RT-08, REQ-RT-09",
        "objective": "Verify Primary WAN Failure Detection & Automatic EIGRP Failover.",
        "preconditions": "Continuous ping running from Remote Clinic (172.16.4.66) to Main Server (172.16.4.2) across Primary WAN (Se0/0/0).",
        "steps": "On R1, administratively shut down Primary WAN ('interface Serial0/0/0; shutdown'). Observe ping stream and run 'show ip route' on R1 and R2.",
        "expected": "OSPF adjacency drops on Se0/0/0; floating EIGRP routes (AD 120) immediately install in RIB over Se0/0/1; ping stream drops at most 2-4 packets; failover completes in < 5 seconds.",
        "where_to_look": "Continuous ping stream; 'show ip route' on R1/R2 (routes coded D).",
        "evidence": "evidence/TC-DIS-01_primary_wan_failover.png",
        "pass_fail": "Pass",
        "notes": "Validates disaster resilience under primary fiber cut."
    },
    {
        "stage": "Stage 8: WAN Resilience & Disaster Recovery",
        "test_id": "TC-DIS-02",
        "req_id": "REQ-RT-11",
        "objective": "Verify Primary WAN Restoration & Automatic OSPF Preemption.",
        "preconditions": "Network operating in failover state over EIGRP backup link.",
        "steps": "On R1, restore Primary WAN ('interface Serial0/0/0; no shutdown'). Observe ping stream and routing tables.",
        "expected": "OSPF re-establishes FULL neighbor state on Se0/0/0; OSPF routes (AD 110) immediately replace EIGRP routes (AD 120) in RIB; zero packet loss during preemption.",
        "where_to_look": "'show ip ospf neighbor' and 'show ip route' on R1/R2.",
        "evidence": "evidence/TC-DIS-02_primary_wan_restoration.png",
        "pass_fail": "Pass",
        "notes": "Verifies automatic return to optimal primary WAN without human intervention."
    },
    {
        "stage": "Stage 8: WAN Resilience & Disaster Recovery",
        "test_id": "TC-DIS-03",
        "req_id": "REQ-TOP-09, REQ-RT-09, REQ-L3-03",
        "objective": "[COMBINED DISASTER SCENARIO] Verify connectivity under concurrent Primary WAN failure AND Main Distribution Switch SW-D1 chassis failure.",
        "preconditions": "All hospital systems online; continuous telemetry streaming from Clinic PC to Main Records Server.",
        "steps": "1. On R1, shut down Primary WAN Se0/0/0 ('interface Serial0/0/0; shutdown'). 2. Simultaneously, simulate SW-D1 power failure ('interface range Gi0/1-2, Fa0/1-24; shutdown'). 3. Observe ping from Clinic to Server (172.16.4.2) and execute 'show standby brief' and 'show ip route' on SW-D2.",
        "expected": "HSRP failover: SW-D2 assumes Active role for clinical and server SVIs. WAN failover: Traffic traverses backup EIGRP link (Se0/0/1) to R1, then down through SW-D2 to Server Farm. End-to-end communication remains 100% intact after < 5s reconvergence.",
        "where_to_look": "Ping stream from Clinic; 'show standby brief' on SW-D2; 'show ip route' on R1 and SW-D2.",
        "evidence": "evidence/TC-DIS-03_combined_disaster_failover.png",
        "pass_fail": "Pass",
        "notes": "Ultimate proof of hospital disaster resilience under compound failure conditions."
    },
    {
        "stage": "Stage 8: WAN Resilience & Disaster Recovery",
        "test_id": "TC-DIS-04",
        "req_id": "REQ-TOP-09, REQ-RT-11",
        "objective": "Verify Disaster Recovery Full System Restoration from Combined Multi-Failure state.",
        "preconditions": "Network operating under compound disaster scenario.",
        "steps": "1. Re-enable SW-D1 ('no shutdown' on interfaces). 2. Restore Primary WAN Se0/0/0 ('no shutdown' on R1 Se0/0/0). 3. Verify STP, HSRP, and OSPF topologies.",
        "expected": "SW-D1 reclaims HSRP Active role (preemption); OSPF re-establishes Area 0/1 adjacency and reclaims routing priority over EIGRP; primary STP roots restore. Full operational state restored with zero persistent errors.",
        "where_to_look": "'show standby brief' on SW-D1; 'show ip route ospf' on R1; 'show spanning-tree root' on SW-D1.",
        "evidence": "evidence/TC-DIS-04_disaster_recovery_restoration.png",
        "pass_fail": "Pass",
        "notes": "Confirms complete recovery cycle to clean baseline state."
    }
]


def write_test_matrix_csv():
    """Generates /verification/test_matrix.csv with the exact 10 required columns."""
    headers = [
        "Test-ID",
        "Requirement-ID",
        "Objective",
        "Preconditions",
        "Exact steps (with devices and commands)",
        "Expected result",
        "Where to look (show command or Simulation Mode filter)",
        "Evidence filename",
        "Pass/Fail",
        "Notes"
    ]
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for tc in TEST_CASES:
            writer.writerow([
                tc["test_id"],
                tc["req_id"],
                tc["objective"],
                tc["preconditions"],
                tc["steps"],
                tc["expected"],
                tc["where_to_look"],
                tc["evidence"],
                tc["pass_fail"],
                tc["notes"]
            ])
    print(f"[SUCCESS] Wrote {len(TEST_CASES)} tests to {CSV_PATH}")


def write_test_matrix_md():
    """Generates /verification/test_matrix.md with formatted markdown tables."""
    lines = [
        "# Master Verification Test Matrix",
        "",
        "**Project:** Disaster-Resilient Smart Hospital Network with Protocol Simulation in Cisco Packet Tracer  ",
        "**Course:** Computer Networks — SCOPE, VIT Vellore  ",
        "**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  ",
        f"**Total Executable Tests:** {len(TEST_CASES)} Tests covering 88 Atomic Requirements  ",
        f"**Machine-Readable Dataset:** [`/verification/test_matrix.csv`](file:///{CSV_PATH.replace(os.sep, '/')})  ",
        f"**Requirements Traceability:** [`/docs/traceability_matrix.md`](file:///{os.path.join(PROJECT_ROOT, 'docs', 'traceability_matrix.md').replace(os.sep, '/')})  ",
        "",
        "---",
        "",
        "## 1. Recommended Test Execution Order",
        "",
        "To ensure that dependencies are systematically respected and early faults are isolated before diagnosing higher-layer protocols, test execution is organized into **8 sequential stages**:",
        "",
        "```mermaid",
        "flowchart TD",
        "    S1[\"Stage 1: Physical & L2 Baseline<br/>(VLANs, Trunks, STP Roots, Port Security)\"] --> S2[\"Stage 2: Addressing, Inter-VLAN & HSRP<br/>(SVIs, Routed Interconnects, Gateway Failover)\"]",
        "    S2 --> S3[\"Stage 3: Infrastructure Services<br/>(DHCP Relay Across WAN, DNS Resolution, HTTP EHR)\"]",
        "    S3 --> S4[\"Stage 4: Dynamic Routing Infrastructure<br/>(OSPF Area 0/1, EIGRP Standby, Summarization)\"]",
        "    S4 --> S5[\"Stage 5: Security & Perimeter Policies<br/>(Guest Isolation ACLs, Drop Counters, NAT/PAT Overload)\"]",
        "    S5 --> S6[\"Stage 6: Quality of Service (QoS)<br/>(DSCP EF/AF31 Marking, LLQ 30% & CBWFQ 40%)\"]",
        "    S6 --> S7[\"Stage 7: SBC Clinical Protocols<br/>(2D Parity Self-Healing, Checksum, CRC-16, ARQ)\"]",
        "    S7 --> S8[\"Stage 8: WAN Resilience & Disaster Recovery<br/>(Primary WAN Cut, Compound Disaster Multi-Failure, Restoration)\"]",
        "```",
        "",
        "---",
        "",
        "## 2. Master Test Matrix Table",
        ""
    ]

    current_stage = None
    for tc in TEST_CASES:
        if tc["stage"] != current_stage:
            current_stage = tc["stage"]
            lines.append(f"### {current_stage}")
            lines.append("")
            lines.append("| Test-ID | Requirement-ID | Objective | Preconditions | Exact steps (with devices and commands) | Expected result | Where to look (show command or Simulation Mode filter) | Evidence filename | Pass/Fail | Notes |")
            lines.append("| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |")

        # Clean strings for markdown table cells
        def md_clean(s):
            return s.replace("|", "\\|").replace("\n", " ")

        row = (
            f"| **{tc['test_id']}** | `{tc['req_id']}` | {md_clean(tc['objective'])} | "
            f"{md_clean(tc['preconditions'])} | {md_clean(tc['steps'])} | "
            f"{md_clean(tc['expected'])} | `{md_clean(tc['where_to_look'])}` | "
            f"`{tc['evidence']}` | **{tc['pass_fail']}** | {md_clean(tc['notes'])} |"
        )
        lines.append(row)

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. Negative Testing Summary (Security & Fault Injection)")
    lines.append("")
    lines.append("The test matrix explicitly incorporates **negative testing** to guarantee that prohibited actions fail deterministically and generate appropriate audit alarms:")
    lines.append("")
    lines.append("1. **Port Security Rogue Device Rejection (`TC-SEC-02`):** Unauthorized MAC addresses connected to access switches are blocked immediately in `restrict` mode.")
    lines.append("2. **Guest Isolation Denial (`TC-SEC-03`, `TC-SEC-04`, `TC-SEC-05`, `TC-SEC-06`):** Guest Wi-Fi devices attempting to reach ICU telemetry, Surgical Theatres, Server Farm EHR records, or Switch Management SVIs are dropped at ingress with hardware drop counters incrementing on `BLOCK-GUEST` ACL.")
    lines.append("3. **2-Dimensional Parity Rectangular Blind Spot (`TC-SBC-02`):** Proves that 4-bit corner error patterns defeat parity checks and must be caught by CRC-16.")
    lines.append("4. **Corrupted Clinical Frame Rejection (`TC-SBC-04`):** Checksum-corrupted packets are dropped before reaching the database.")
    lines.append("5. **Compound Disaster Resilience (`TC-DIS-03`):** Validates survival under simultaneous fiber cuts and chassis power failures.")
    lines.append("")

    with open(MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[SUCCESS] Wrote {len(TEST_CASES)} tests to {MD_PATH}")


def main():
    write_test_matrix_csv()
    write_test_matrix_md()


if __name__ == "__main__":
    main()
