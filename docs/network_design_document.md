# Disaster-Resilient Smart Hospital Network: Comprehensive Network Design Document
**Document Reference:** NDD-HOSP-2026-v2.0  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  
**Academic Institution:** School of Computer Science and Engineering (SCOPE), VIT Vellore  
**Course Code & Title:** CSE2004 — Computer Networks  
**Submission Date:** October 2026  

---

## 1. Executive Summary

Modern acute healthcare facilities are critically reliant on digital infrastructure for real-time patient physiological monitoring, surgical suite telemetry, and electronic health record (EHR) transmission. Network outages in such environments are life-threatening: a delay of mere seconds in cardiac telemetry or patient alarm delivery can lead to irreversible patient brain damage or death. In accordance with IEC 80001-1 (Application of risk management for IT-networks incorporating medical devices), the hospital communication fabric must be designed for deterministic fault tolerance, sub-second convergence, and strict zero-loss guarantees.

This document details the engineering design of the **Disaster-Resilient Smart Hospital Network**, a multi-site enterprise topology simulated in Cisco Packet Tracer 8.x and validated via hardware-emulated Single-Board Computers (SBCs). The design features a hierarchical three-tier campus switching core (Core, Distribution, Access), dual-homed Hot Standby Router Protocol (HSRP) gateway redundancy, hierarchical multi-area OSPFv2 dynamic routing with unequal-cost serial WAN failover, IEEE 802.1w Rapid-PVST+ loop mitigation, DiffServ 4-class Quality of Service (QoS) prioritization, stateful NAT/PAT perimeter firewalling, and a novel application-layer self-healing telemetry protocol featuring 2D parity error correction and Selective Repeat sliding-window ARQ.

## 2. Glossary & Technical Acronyms

| Acronym | Term & Engineering Definition |
| :--- | :--- |
| **ACE** | Access Control Entry — A single permit or deny statement within an access control list. |
| **ACL** | Access Control List — Packet filtering mechanism operating at Layers 3 and 4. |
| **AIMD** | Additive Increase / Multiplicative Decrease — TCP congestion avoidance algorithm. |
| **ARQ** | Automatic Repeat reQuest — Error control protocol using acknowledgments and timeouts. |
| **BFD** | Bidirectional Forwarding Detection — Sub-second path liveness detection protocol. |
| **BPDU** | Bridge Protocol Data Unit — Spanning Tree management frame exchanged between switches. |
| **CAM** | Content Addressable Memory — Hardware table storing Layer 2 MAC-to-port bindings. |
| **CIDR** | Classless Inter-Domain Routing — Bit-mask based IP address allocation scheme. |
| **CRC** | Cyclic Redundancy Check — Polynomial division checksum for burst error detection. |
| **DHCP** | Dynamic Host Configuration Protocol — Automated network parameter configuration. |
| **DICOM** | Digital Imaging and Communications in Medicine — Standard for medical imaging transmission. |
| **DiffServ** | Differentiated Services — RFC 2474 IP architecture for scalable packet prioritization. |
| **DORA** | Discover, Offer, Request, Acknowledge — Four-way DHCP message exchange sequence. |
| **DSCP** | Differentiated Services Code Point — 6-bit field in IPv4 header for QoS classification. |
| **DUAL** | Diffusing Update Algorithm — Distance-vector routing algorithm used by EIGRP. |
| **EHR** | Electronic Health Records — Centralized patient diagnostic and clinical record database. |
| **HSRP** | Hot Standby Router Protocol — Cisco proprietary first-hop default gateway redundancy protocol. |
| **ISN** | Initial Sequence Number — 32-bit starting sequence number in a TCP socket connection. |
| **LSA** | Link-State Advertisement — Topological link description packet flooded in OSPF. |
| **LSDB** | Link-State Database — Global network topology graph constructed by OSPF routers. |
| **MSS** | Maximum Segment Size — Largest amount of TCP data a device can receive in a single IP packet. |
| **NAT** | Network Address Translation — Remapping private RFC 1918 addresses to public routable IPs. |
| **OSPF** | Open Shortest Path First — Link-state hierarchical interior gateway routing protocol. |
| **PAT** | Port Address Translation — Many-to-one dynamic NAT utilizing Layer 4 source ports. |
| **PDU** | Protocol Data Unit — Unit of data at a specific layer of the OSI reference model. |
| **PQ** | Priority Queuing — QoS queue scheduling mechanism that strictly services high-priority queues first. |
| **Rapid-PVST+** | Rapid Per-VLAN Spanning Tree Plus — Cisco implementation of IEEE 802.1w per VLAN. |
| **RTO** | Retransmission Timeout — Timer after which unacknowledged TCP segments are resent. |
| **SBC** | Single-Board Computer — Microprocessor node running clinical sensor application code. |
| **SLA** | Service Level Agreement — Contractually defined uptime and performance baselines. |
| **SVI** | Switch Virtual Interface — Layer 3 logical VLAN interface on a multilayer switch. |
| **ToS** | Type of Service — 8-bit IPv4 header field containing IP precedence or DSCP bits. |
| **TTL** | Time to Live — 8-bit IPv4 field decremented at each hop to eliminate infinite routing loops. |
| **VIP** | Virtual IP Address — Shared gateway IP address managed by HSRP redundancy groups. |
| **VLSM** | Variable Length Subnet Masking — Subnetting technique maximizing IPv4 address efficiency. |
| **WFQ** | Weighted Fair Queuing — Dynamic scheduling allocating link bandwidth proportional to weights. |

## 3. Project Requirements & Traceability Matrix

The project architecture directly implements all fifteen mandatory requirements stipulated in the Review-1 proposal. The following master traceability matrix cross-references each design requirement with its implemented network configuration, verification test case, and simulation evidence artifact.

| Req ID | Category | Requirement Description | Implementing Configuration | Test Suite | Verification Evidence Artifact |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **REQ-TOP-001** | Topology | Dual-site campus network (Main Hospital & Remote Clinic) | `cabling.csv, pt_builder.py` | `test_topology.py` | [docs/topology_diagram.puml](file:///C:/Users/karth/OneDrive/Desktop/CN_PROJECT/docs/topology_diagram.puml) |
| **REQ-ADD-001** | Addressing | Zero-waste VLSM allocation on 172.16.0.0/16 | `addressing/vlsm.py, plan.csv` | `test_vlsm.py` | [docs/addressing_plan.md](file:///C:/Users/karth/OneDrive/Desktop/CN_PROJECT/docs/addressing_plan.md) |
| **REQ-ADD-002** | DHCP | Centralized DHCP Relay via IP helper-address | `configs/SW-D1, configs/SW-D2` | `test_server_setup.py` | [docs/dhcp_pools.csv](file:///C:/Users/karth/OneDrive/Desktop/CN_PROJECT/docs/dhcp_pools.csv) |
| **REQ-L2-001** | Switching | 802.1Q trunking, access ports, parking VLAN 999 | `configs/SW-A1..A5` | `test_intervlan_hsrp.py` | [docs/intervlan_hsrp_guide.md](file:///C:/Users/karth/OneDrive/Desktop/CN_PROJECT/docs/intervlan_hsrp_guide.md) |
| **REQ-L2-002** | STP | Rapid-PVST+ root bridge priority & BPDU Guard | `configs/SW-D1, configs/SW-D2` | `test_intervlan_hsrp.py` | [docs/intervlan_hsrp_guide.md](file:///C:/Users/karth/OneDrive/Desktop/CN_PROJECT/docs/intervlan_hsrp_guide.md) |
| **REQ-HA-001** | Gateway HA | HSRP dual-distribution active/standby preemption | `configs/SW-D1, configs/SW-D2` | `test_intervlan_hsrp.py` | [docs/failover_experiment.md](file:///C:/Users/karth/OneDrive/Desktop/CN_PROJECT/docs/failover_experiment.md) |
| **REQ-RT-001** | Routing | Hierarchical multi-area OSPFv2 (Area 0, 1, 2) | `configs/R1, configs/R2, SW-D1..D4` | `test_routing_configs.py` | [docs/routing_design.md](file:///C:/Users/karth/OneDrive/Desktop/CN_PROJECT/docs/routing_design.md) |
| **REQ-RT-002** | WAN HA | Primary vs. Backup Serial WAN failover (cost 64 vs 500) | `configs/R1, configs/R2` | `test_routing_configs.py` | [docs/failover_experiment.md](file:///C:/Users/karth/OneDrive/Desktop/CN_PROJECT/docs/failover_experiment.md) |
| **REQ-SEC-001** | Security | Zero-trust clinical inter-VLAN ACL isolation | `configs/SW-D1, configs/SW-D2` | `test_security_acls.py` | [docs/security_policy.md](file:///C:/Users/karth/OneDrive/Desktop/CN_PROJECT/docs/security_policy.md) |
| **REQ-SEC-002** | Perimeter | Internet Edge NAT/PAT with static server port-forward | `configs/R1, configs/edge-isp` | `test_nat_edge.py` | [docs/nat_internet_edge.md](file:///C:/Users/karth/OneDrive/Desktop/CN_PROJECT/docs/nat_internet_edge.md) |
| **REQ-SEC-003** | Hardening | Device hardening (service password-encryption, SSHv2) | `All 13 device configs` | `test_hardening.py` | [verification/lint_configs.py](file:///C:/Users/karth/OneDrive/Desktop/CN_PROJECT/verification/lint_configs.py) |
| **REQ-QOS-001** | QoS | DiffServ 4-class queuing (DSCP EF, Priority Queue PQ) | `configs/R1, R2, SW-D1, SW-D2` | `test_qos_design.py` | [docs/qos_design.md](file:///C:/Users/karth/OneDrive/Desktop/CN_PROJECT/docs/qos_design.md) |
| **REQ-SBC-001** | SBC IoT | Medical sensor telemetry generation & gateway relay | `sbc/sensor_node.py, gateway.py` | `test_medical_sensor_app.py` | [sbc/README.md](file:///C:/Users/karth/OneDrive/Desktop/CN_PROJECT/sbc/README.md) |
| **REQ-ERR-001** | Reliability | 2D Parity 1-bit self-healing & CRC-16 detection | `sbc/errdetect.py` | `test_errdetect_lib.py` | [sim/analysis.py](file:///C:/Users/karth/OneDrive/Desktop/CN_PROJECT/sim/analysis.py) |
| **REQ-ARQ-001** | Transport | Sliding-window ARQ comparison (GBN vs. Selective Repeat) | `sbc/arq_protocols.py` | `test_benchmark_sweep.py` | [docs/tcp_vs_udp_comparison.md](file:///C:/Users/karth/OneDrive/Desktop/CN_PROJECT/docs/tcp_vs_udp_comparison.md) |

## 4. Topology Architecture & Network Hierarchy

The hospital internetwork is architected according to the Cisco Three-Tier Hierarchical Model, divided into two distinct geographical campuses:
1. **Main Hospital Campus:** Houses the Core Router (`R1`), dual Distribution Multilayer Switches (`SW-D1`, `SW-D2`), and five Access Switches (`SW-A1` through `SW-A5`) supporting ICU, Surgical Suites, Radiology, Administration, Guest Wi-Fi, and the Central Server Farm.
2. **Remote Emergency Clinic:** An isolated regional clinic linked via dual redundant Serial WAN links to `R2`, served by distribution switch `SW-D3` (and standby `SW-D4`) supporting outpatient triage and diagnostic telemedicine.
3. **Internet Edge & ISP:** Simulates the public Internet boundary (`EDGE-ISP`) connected to `R1` via NAT/PAT overload.

### Enterprise Topology Mermaid Diagram

```mermaid
flowchart TD
    subgraph Public_Internet [Internet Edge Domain]
        ISP["EDGE-ISP (Internet Gateway)<br/>Gi0/0: 203.0.113.1/30"]
    end
    subgraph Main_Hospital_Campus [Main Hospital Campus Network]
        R1["R1 (Core Router)<br/>Lo0: 172.16.8.106/32"]
        SW_D1["SW-D1 (Primary Dist Switch)<br/>HSRP Active (VLAN 10, 30)<br/>Root Primary (VLAN 10, 30, 50)"]
        SW_D2["SW-D2 (Secondary Dist Switch)<br/>HSRP Active (VLAN 20, 40)<br/>Root Secondary (All VLANs)"]
        SW_A1["SW-A1 (ICU Telemetry)<br/>VLAN 10"]
        SW_A2["SW-A2 (Operating Theatre)<br/>VLAN 20"]
        SW_A3["SW-A3 (General Admin)<br/>VLAN 30"]
        SW_A4["SW-A4 (Guest Wi-Fi)<br/>VLAN 60"]
        SW_A5["SW-A5 (Server Farm)<br/>VLAN 50 (EHR & Telemetry)"]
    end
    subgraph Remote_Clinic_Campus [Remote Emergency Clinic Campus]
        R2["R2 (Clinic Edge Router)<br/>Lo0: 172.16.8.107/32"]
        SW_D3["SW-D3 (Clinic Dist Gateway)<br/>Primary SVI (VLAN 10, 30, 40, 60)"]
        SW_D4["SW-D4 (Clinic HA Standby)<br/>Standby Gateway Extension"]
    end
    ISP === |"NAT Gi0/2: 203.0.113.2/30"| R1
    R1 === |"OSPF Gi0/1: 172.16.8.97/30"| SW_D1
    R1 === |"OSPF Gi0/2: 172.16.8.93/30"| SW_D2
    SW_D1 <=== |"Cross-Connect Po1 / Gi0/2"| ===> SW_D2
    SW_D1 --- |Trunk Fa0/1| SW_A1
    SW_D2 --- |Trunk Fa0/1| SW_A1
    SW_D1 --- |Trunk Fa0/2| SW_A2
    SW_D2 --- |Trunk Fa0/2| SW_A2
    SW_D1 --- |Trunk Fa0/3| SW_A3
    SW_D2 --- |Trunk Fa0/3| SW_A3
    SW_D1 --- |Trunk Fa0/4| SW_A4
    SW_D2 --- |Trunk Fa0/4| SW_A4
    SW_D1 --- |Trunk Fa0/5| SW_A5
    SW_D2 --- |Trunk Fa0/5| SW_A5
    R1 === |"Primary WAN Se0/0/0 (Cost 64)"| ===> R2
    R1 -.-> |"Backup WAN Se0/0/1 (Cost 500)"| -.-> R2
    R2 === |"OSPF Gi0/1: 172.16.8.98/30"| SW_D3
    R2 === |"OSPF Gi0/2: 172.16.8.113/30"| SW_D4
    SW_D3 <=== |"Clinic Trunk Gi0/2"| ===> SW_D4
```

> [!TIP] How to Export Diagrams
> 1. **Mermaid Live Editor:** Copy the code block above into [mermaid.live](https://mermaid.live) and export directly as vector SVG or 300 DPI PNG.
> 2. **PlantUML Vector Diagram:** The exact PlantUML source is located in [`topology/topology_diagram.puml`](file:///{PROJECT_ROOT.replace('\', '/')}/topology/topology_diagram.puml) and can be rendered using the PlantUML CLI or VS Code PlantUML extension.

## 5. Physical Cabling & Interconnect Matrix

The physical and logical connectivity between all thirteen (13) network devices is detailed in the authoritative cabling matrix below:

| Link ID | Device A | Port A | Device B | Port B | Cable Type | Layer | VLANs Carried | Subnet / IP | Purpose |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| **LINK-WAN-01** | R1 | Serial0/0/0 | R2 | Serial0/0/0 | Serial DCE (clock rate 128000 on R1) | L3 routed | - | `172.16.8.80/30 (R1: 172.16.8.81 DCE / R2: 172.16.8.82 DTE)` | Primary Inter-Site WAN Circuit (OSPF Area 0 Backbone) |
| **LINK-WAN-02** | R1 | Serial0/0/1 | R2 | Serial0/0/1 | Serial DCE (clock rate 128000 on R1) | L3 routed | - | `172.16.8.84/30 (R1: 172.16.8.85 DCE / R2: 172.16.8.86 DTE)` | Secondary Standby WAN Circuit (EIGRP AS 100 Floating AD 115) |
| **LINK-CORE-01** | R1 | GigabitEthernet0/0 | SW-D1 | GigabitEthernet0/2 | Copper Straight-Through | L3 routed | - | `172.16.8.88/30 (SW-D1: 172.16.8.89 / R1: 172.16.8.90)` | Main Hospital Distribution SW-D1 Routed Transit Uplink to R1 |
| **LINK-CORE-02** | R1 | GigabitEthernet0/1 | SW-D2 | GigabitEthernet0/2 | Copper Straight-Through | L3 routed | - | `172.16.8.92/30 (SW-D2: 172.16.8.93 / R1: 172.16.8.94)` | Main Hospital Distribution SW-D2 Routed Transit Uplink to R1 |
| **LINK-CORE-03** | R2 | GigabitEthernet0/0 | SW-D3 | GigabitEthernet0/1 | Copper Straight-Through | L3 routed | - | `172.16.8.96/30 (SW-D3: 172.16.8.97 / R2: 172.16.8.98)` | Remote Clinic Distribution SW-D3 Routed Transit Uplink to R2 |
| **LINK-EDGE-01** | R1 | GigabitEthernet0/2 | EDGE-ISP | GigabitEthernet0/0 | Copper Straight-Through | L3 routed | - | `172.16.8.100/30 (EDGE-ISP: 172.16.8.101 / R1: 172.16.8.102)` | Internet Edge NAT/PAT Overload Uplink to Public ISP Gateway |
| **LINK-DIST-01** | SW-D1 | FastEthernet0/23 | SW-D2 | FastEthernet0/23 | Copper Crossover | L2 trunk | 10 20 30 40 50 60 99 (Native: 999) | `-` | Distribution Inter-Switch Trunk LACP Port-Channel 1 Bundle (Member 1) |
| **LINK-DIST-02** | SW-D1 | FastEthernet0/24 | SW-D2 | FastEthernet0/24 | Copper Crossover | L2 trunk | 10 20 30 40 50 60 99 (Native: 999) | `-` | Distribution Inter-Switch Trunk LACP Port-Channel 1 Bundle (Member 2) |
| **LINK-TRUNK-01** | SW-D1 | FastEthernet0/1 | SW-A1 | GigabitEthernet0/1 | Copper Straight-Through | L2 trunk | 10 60 99 (Native: 999) | `-` | ICU Access Switch SW-A1 Primary 802.1Q Trunk Uplink to SW-D1 |
| **LINK-TRUNK-02** | SW-D2 | FastEthernet0/1 | SW-A1 | GigabitEthernet0/2 | Copper Straight-Through | L2 trunk | 10 60 99 (Native: 999) | `-` | ICU Access Switch SW-A1 Secondary 802.1Q Trunk Uplink to SW-D2 (PVST+ Standby) |
| **LINK-TRUNK-03** | SW-D1 | FastEthernet0/2 | SW-A2 | GigabitEthernet0/1 | Copper Straight-Through | L2 trunk | 20 60 99 (Native: 999) | `-` | Surgery Access Switch SW-A2 Primary 802.1Q Trunk Uplink to SW-D1 |
| **LINK-TRUNK-04** | SW-D2 | FastEthernet0/2 | SW-A2 | GigabitEthernet0/2 | Copper Straight-Through | L2 trunk | 20 60 99 (Native: 999) | `-` | Surgery Access Switch SW-A2 Secondary 802.1Q Trunk Uplink to SW-D2 (PVST+ Standby) |
| **LINK-TRUNK-05** | SW-D2 | FastEthernet0/3 | SW-A3 | GigabitEthernet0/1 | Copper Straight-Through | L2 trunk | 30 60 99 (Native: 999) | `-` | Admin Access Switch SW-A3 Primary 802.1Q Trunk Uplink to SW-D2 |
| **LINK-TRUNK-06** | SW-D1 | FastEthernet0/3 | SW-A3 | GigabitEthernet0/2 | Copper Straight-Through | L2 trunk | 30 60 99 (Native: 999) | `-` | Admin Access Switch SW-A3 Secondary 802.1Q Trunk Uplink to SW-D1 (PVST+ Standby) |
| **LINK-TRUNK-07** | SW-D2 | FastEthernet0/4 | SW-A4 | GigabitEthernet0/1 | Copper Straight-Through | L2 trunk | 40 99 (Native: 999) | `-` | Guest Wi-Fi Access Switch SW-A4 Primary 802.1Q Trunk Uplink to SW-D2 |
| **LINK-TRUNK-08** | SW-D1 | FastEthernet0/4 | SW-A4 | GigabitEthernet0/2 | Copper Straight-Through | L2 trunk | 40 99 (Native: 999) | `-` | Guest Wi-Fi Access Switch SW-A4 Secondary 802.1Q Trunk Uplink to SW-D1 (PVST+ Standby) |
| **LINK-TRUNK-09** | SW-D3 | FastEthernet0/23 | SW-A5 | GigabitEthernet0/1 | Copper Straight-Through | L2 trunk | 10 30 40 60 99 (Native: 999) | `-` | Clinic Access Switch SW-A5 Primary 802.1Q Trunk Uplink to SW-D3 |
| **LINK-TRUNK-10** | SW-D3 | FastEthernet0/24 | SW-A5 | GigabitEthernet0/2 | Copper Straight-Through | L2 trunk | 10 30 40 60 99 (Native: 999) | `-` | Clinic Access Switch SW-A5 Redundant 802.1Q Trunk Uplink to SW-D3 (STP Alternate) |
| **LINK-SRV-01** | SW-D1 | FastEthernet0/10 | SRV-CENTRAL | FastEthernet0 | Copper Straight-Through | L2 access | 50 | `172.16.7.4/26 (Gateway: 172.16.7.1)` | Central Hospital Server (DNS / DHCP / Intranet Web Portal) |
| **LINK-SRV-02** | SW-D1 | FastEthernet0/11 | SRV-PACS | FastEthernet0 | Copper Straight-Through | L2 access | 50 | `172.16.7.7/26 (Gateway: 172.16.7.1)` | PACS Medical Imaging Archive Server (DICOM Storage) |
| **LINK-SRV-03** | SW-D2 | FastEthernet0/12 | SRV-BACKUP | FastEthernet0 | Copper Straight-Through | L2 access | 50 | `172.16.7.8/26 (Gateway: 172.16.7.1)` | Disaster Recovery Database Replication Target Server |
| **LINK-SRV-04** | SW-D3 | FastEthernet0/10 | SRV-CACHE | FastEthernet0 | Copper Straight-Through | L2 access | 10 | `172.16.8.36/27 (Gateway: 172.16.8.33)` | Remote Clinic Local EHR Cache & Offline Proxy Server |
| **LINK-ICU-01** | SW-A1 | FastEthernet0/1 | SBC-ICU-101 | FastEthernet0 | Copper Straight-Through | L2 access | 10 | `172.16.7.138/26 (Gateway: 172.16.7.129)` | Bedside IoT Telemetry Node (Bed 101 - Vitals Simulation SBC) |
| **LINK-ICU-02** | SW-A1 | FastEthernet0/2 | SBC-ICU-102 | FastEthernet0 | Copper Straight-Through | L2 access | 10 | `172.16.7.139/26 (Gateway: 172.16.7.129)` | Bedside IoT Telemetry Node (Bed 102 - Vitals Simulation SBC) |
| **LINK-ICU-03** | SW-A1 | FastEthernet0/3 | SBC-ICU-103 | FastEthernet0 | Copper Straight-Through | L2 access | 10 | `172.16.7.140/26 (Gateway: 172.16.7.129)` | Bedside IoT Telemetry Node (Bed 103 - Vitals Simulation SBC) |
| **LINK-ICU-04** | SW-A1 | FastEthernet0/4 | PC-ICU-NURSE | FastEthernet0 | Copper Straight-Through | L2 access | 10 | `172.16.7.141/26 (Gateway: 172.16.7.129)` | ICU Central Nursing Monitoring Station Workstation |
| **LINK-ICU-05** | SW-A1 | FastEthernet0/5 | PC-ICU-DOC1 | FastEthernet0 | Copper Straight-Through | L2 access | 10 | `172.16.7.142/26 (Gateway: 172.16.7.129)` | ICU Attending Physician Clinical Workstation 1 |
| **LINK-ICU-06** | SW-A1 | FastEthernet0/6 | PC-ICU-DOC2 | FastEthernet0 | Copper Straight-Through | L2 access | 10 | `172.16.7.143/26 (Gateway: 172.16.7.129)` | ICU Attending Physician Clinical Workstation 2 |
| **LINK-ICU-07** | SW-A1 | FastEthernet0/7 | PHONE-ICU-601 | SwitchPort | Copper Straight-Through | L2 access | Voice: 60 Data: 10 | `172.16.6.10/25 (Gateway: 172.16.6.1)` | Cisco 7960 IP Phone Ext 1001 (ICU Nursing Desk) |
| **LINK-SURG-01** | SW-A2 | FastEthernet0/1 | SBC-SURG-201 | FastEthernet0 | Copper Straight-Through | L2 access | 20 | `172.16.7.74/26 (Gateway: 172.16.7.65)` | Operating Room 1 Anesthesia & Ventilator Telemetry SBC |
| **LINK-SURG-02** | SW-A2 | FastEthernet0/2 | SBC-SURG-202 | FastEthernet0 | Copper Straight-Through | L2 access | 20 | `172.16.7.75/26 (Gateway: 172.16.7.65)` | Operating Room 2 Surgical Vital Signs Telemetry SBC |
| **LINK-SURG-03** | SW-A2 | FastEthernet0/3 | PC-THEATRE-1 | FastEthernet0 | Copper Straight-Through | L2 access | 20 | `172.16.7.76/26 (Gateway: 172.16.7.65)` | Operating Theatre 1 PACS DICOM Viewer Workstation |
| **LINK-SURG-04** | SW-A2 | FastEthernet0/4 | PC-THEATRE-2 | FastEthernet0 | Copper Straight-Through | L2 access | 20 | `172.16.7.77/26 (Gateway: 172.16.7.65)` | Operating Theatre 2 PACS DICOM Viewer Workstation |
| **LINK-SURG-05** | SW-A2 | FastEthernet0/5 | PC-THEATRE-3 | FastEthernet0 | Copper Straight-Through | L2 access | 20 | `172.16.7.78/26 (Gateway: 172.16.7.65)` | Surgical Head Consultation & Telemetry Display PC |
| **LINK-SURG-06** | SW-A2 | FastEthernet0/7 | PHONE-SURG-602 | SwitchPort | Copper Straight-Through | L2 access | Voice: 60 Data: 20 | `172.16.6.11/25 (Gateway: 172.16.6.1)` | Cisco 7960 IP Phone Ext 1002 (Surgical Suite Reception) |
| **LINK-ADM-01** | SW-A3 | FastEthernet0/1 | PC-ADMIN-301 | FastEthernet0 | Copper Straight-Through | L2 access | 30 | `172.16.4.10/23 (Gateway: 172.16.4.1)` | Admissions & Patient Billing Terminal |
| **LINK-ADM-02** | SW-A3 | FastEthernet0/2 | PC-ADMIN-302 | FastEthernet0 | Copper Straight-Through | L2 access | 30 | `172.16.4.11/23 (Gateway: 172.16.4.1)` | Hospital Medical Records Administration Terminal |
| **LINK-ADM-03** | SW-A3 | FastEthernet0/3 | PC-ADMIN-303 | FastEthernet0 | Copper Straight-Through | L2 access | 30 | `172.16.4.12/23 (Gateway: 172.16.4.1)` | Hospital Executive Director Workstation |
| **LINK-ADM-04** | SW-A3 | FastEthernet0/7 | PHONE-ADMIN-603 | SwitchPort | Copper Straight-Through | L2 access | Voice: 60 Data: 30 | `172.16.6.12/25 (Gateway: 172.16.6.1)` | Cisco 7960 IP Phone Ext 1003 (Admin Front Desk) |
| **LINK-ADM-05** | SW-A3 | FastEthernet0/20 | PC-NOC-MGT | FastEthernet0 | Copper Straight-Through | L2 access | 99 | `172.16.7.212/27 (Gateway: 172.16.7.193)` | Network Operations Center Management Console |
| **LINK-GST-01** | SW-A4 | FastEthernet0/10 | AP-GUEST | Port0 | Copper Straight-Through | L2 access | 40 | `172.16.0.10/22 (Gateway: 172.16.0.1)` | Main Hospital Guest Wi-Fi Access Point Uplink |
| **LINK-GST-02** | AP-GUEST | Port1 | LAPTOP-GUEST-1 | Wireless0 | Wireless (802.11) | L2 access | 40 | `172.16.0.11/22 (DHCP Pool: 172.16.0.0/22)` | Guest Wi-Fi Client Laptop 1 (Waiting Lounge) |
| **LINK-GST-03** | AP-GUEST | Port1 | LAPTOP-GUEST-2 | Wireless0 | Wireless (802.11) | L2 access | 40 | `172.16.0.12/22 (DHCP Pool: 172.16.0.0/22)` | Guest Wi-Fi Client Laptop 2 (Cafeteria) |
| **LINK-GST-04** | AP-GUEST | Port1 | LAPTOP-GUEST-3 | Wireless0 | Wireless (802.11) | L2 access | 40 | `172.16.0.13/22 (DHCP Pool: 172.16.0.0/22)` | Guest Wi-Fi Client Laptop 3 (Family Lounge) |
| **LINK-CLN-01** | SW-A5 | FastEthernet0/1 | PC-CLINIC-CONSULT1 | FastEthernet0 | Copper Straight-Through | L2 access | 10 | `172.16.8.42/27 (Gateway: 172.16.8.33)` | Remote Clinic Consultation Room 1 Terminal |
| **LINK-CLN-02** | SW-A5 | FastEthernet0/2 | PC-CLINIC-CONSULT2 | FastEthernet0 | Copper Straight-Through | L2 access | 10 | `172.16.8.43/27 (Gateway: 172.16.8.33)` | Remote Clinic Consultation Room 2 Terminal |
| **LINK-CLN-03** | SW-A5 | FastEthernet0/3 | PC-CLINIC-TRIAGE | FastEthernet0 | Copper Straight-Through | L2 access | 10 | `172.16.8.44/27 (Gateway: 172.16.8.33)` | Remote Clinic Emergency Triage Station |
| **LINK-CLN-04** | SW-A5 | FastEthernet0/4 | PC-CLINIC-ADM1 | FastEthernet0 | Copper Straight-Through | L2 access | 30 | `172.16.8.10/27 (Gateway: 172.16.8.1)` | Remote Clinic Reception & Registration PC |
| **LINK-CLN-05** | SW-A5 | FastEthernet0/5 | PC-CLINIC-ADM2 | FastEthernet0 | Copper Straight-Through | L2 access | 30 | `172.16.8.11/27 (Gateway: 172.16.8.1)` | Remote Clinic Billing & Records Terminal |
| **LINK-CLN-06** | SW-A5 | FastEthernet0/6 | PC-CLINIC-PHARM | FastEthernet0 | Copper Straight-Through | L2 access | 30 | `172.16.8.12/27 (Gateway: 172.16.8.1)` | Remote Clinic Pharmacy Dispensing PC |
| **LINK-CLN-07** | SW-A5 | FastEthernet0/7 | PHONE-CLINIC-601 | SwitchPort | Copper Straight-Through | L2 access | Voice: 60 Data: 30 | `172.16.7.234/27 (Gateway: 172.16.7.225)` | Cisco 7960 IP Phone Ext 2001 (Reception) |
| **LINK-CLN-08** | SW-A5 | FastEthernet0/8 | PHONE-CLINIC-602 | SwitchPort | Copper Straight-Through | L2 access | Voice: 60 Data: 10 | `172.16.7.235/27 (Gateway: 172.16.7.225)` | Cisco 7960 IP Phone Ext 2002 (Doctor Desk) |
| **LINK-CLN-09** | SW-A5 | FastEthernet0/9 | PHONE-CLINIC-603 | SwitchPort | Copper Straight-Through | L2 access | Voice: 60 Data: 10 | `172.16.7.236/27 (Gateway: 172.16.7.225)` | Cisco 7960 IP Phone Ext 2003 (Triage Desk) |
| **LINK-CLN-10** | SW-A5 | FastEthernet0/10 | AP-CLINIC-GUEST | Port0 | Copper Straight-Through | L2 access | 40 | `172.16.6.138/25 (Gateway: 172.16.6.129)` | Remote Clinic Guest Wi-Fi Access Point Uplink |
| **LINK-CLN-11** | AP-CLINIC-GUEST | Port1 | LAPTOP-CLINIC-G1 | Wireless0 | Wireless (802.11) | L2 access | 40 | `172.16.6.139/25 (DHCP Pool: 172.16.6.128/25)` | Clinic Visitor Laptop 1 |
| **LINK-CLN-12** | AP-CLINIC-GUEST | Port1 | LAPTOP-CLINIC-G2 | Wireless0 | Wireless (802.11) | L2 access | 40 | `172.16.6.140/25 (DHCP Pool: 172.16.6.128/25)` | Clinic Visitor Laptop 2 |
| **LINK-CLN-13** | AP-CLINIC-GUEST | Port1 | LAPTOP-CLINIC-G3 | Wireless0 | Wireless (802.11) | L2 access | 40 | `172.16.6.141/25 (DHCP Pool: 172.16.6.128/25)` | Clinic Visitor Laptop 3 |
| **LINK-CLN-14** | SW-A5 | FastEthernet0/20 | PC-CLINIC-MGT | FastEthernet0 | Copper Straight-Through | L2 access | 99 | `172.16.8.75/28 (Gateway: 172.16.8.65)` | Remote Clinic Local Administrator Console |

## 6. Layer 2 Switching, VLAN & Spanning Tree Design

### 6.1 VLAN Segmentation Architecture
To enforce zero-trust security and limit Layer 2 broadcast domains, clinical functions are segmented into dedicated IEEE 802.1Q VLANs:
- **VLAN 10 (ICU Telemetry):** Life-critical physiological patient sensor traffic (DSCP EF).
- **VLAN 20 (Operating Theatre):** Surgical cameras, anesthesia monitors, and robotic surgical consoles.
- **VLAN 30 (General Ward & Admin):** Staff workstations, nursing stations, and billing terminals.
- **VLAN 40 (Diagnostic Imaging):** PACS DICOM high-resolution CT/MRI scans and ultrasound archives.
- **VLAN 50 (Server Farm):** Electronic Health Record (EHR) database, Telemetry Ingestion Collector, DNS, and DHCP.
- **VLAN 60 (Guest & Visitor Wi-Fi):** Public internet-only untrusted mobile devices (strictly isolated).
- **VLAN 99 (Out-of-Band Management):** Dedicated switch/router SSH management and syslog logging.
- **VLAN 999 (Parking Lot / Unused):** Blackhole VLAN where all inactive access switch ports are parked and shutdown.

### 6.2 Spanning Tree Architecture (Rapid-PVST+)
To eradicate Layer 2 bridging loops while avoiding legacy 802.1D 30-second convergence penalties, the network deploys **IEEE 802.1w Rapid-PVST+**:
- **SW-D1** is configured as `spanning-tree vlan 10,30,50 root primary` (Priority 4096) and secondary for other VLANs (Priority 8192).
- **SW-D2** is configured as `spanning-tree vlan 20,40,60,99 root primary` (Priority 4096) and secondary for other VLANs (Priority 8192).
- **Cisco PortFast & BPDU Guard:** Globally enabled on all access switches (`spanning-tree portfast default`, `spanning-tree portfast bpduguard default`). Any host-facing access port transitions immediately to forwarding state upon link-up, and automatically error-disables if an unauthorized rogue switch injects BPDUs.

## 7. Layer 3 Addressing & VLSM Subnet Allocation Plan

All network subnets are carved from the private Class B allocation `172.16.0.0/16` using Variable Length Subnet Masking (VLSM) to achieve zero address waste:

| Subnet Name | Site | VLAN | Network Address | Prefix | Subnet Mask | Usable Host Range | Broadcast | Needed | Usable | Util % |
| :--- | :--- | :---: | :--- | :---: | :--- | :--- | :--- | :---: | :---: | :---: |
| **Main-VLAN40-Guest** | Main Hospital | 40 | `172.16.0.0` | `/22` | `255.255.252.0` | `172.16.0.1 - 172.16.3.254` | `172.16.3.255` | 520 | 1022 | 50.88% |
| **Main-VLAN30-Admin** | Main Hospital | 30 | `172.16.4.0` | `/23` | `255.255.254.0` | `172.16.4.1 - 172.16.5.254` | `172.16.5.255` | 260 | 510 | 50.98% |
| **Main-VLAN60-Voice** | Main Hospital | 60 | `172.16.6.0` | `/25` | `255.255.255.128` | `172.16.6.1 - 172.16.6.126` | `172.16.6.127` | 78 | 126 | 61.9% |
| **Clinic-VLAN40-Guest** | Remote Clinic | 40 | `172.16.6.128` | `/25` | `255.255.255.128` | `172.16.6.129 - 172.16.6.254` | `172.16.6.255` | 65 | 126 | 51.59% |
| **Main-VLAN50-Servers** | Main Hospital | 50 | `172.16.7.0` | `/26` | `255.255.255.192` | `172.16.7.1 - 172.16.7.62` | `172.16.7.63` | 39 | 62 | 62.9% |
| **Main-VLAN20-Surgery** | Main Hospital | 20 | `172.16.7.64` | `/26` | `255.255.255.192` | `172.16.7.65 - 172.16.7.126` | `172.16.7.127` | 52 | 62 | 83.87% |
| **Main-VLAN10-ICU** | Main Hospital | 10 | `172.16.7.128` | `/26` | `255.255.255.192` | `172.16.7.129 - 172.16.7.190` | `172.16.7.191` | 52 | 62 | 83.87% |
| **Main-VLAN99-Mgmt** | Main Hospital | 99 | `172.16.7.192` | `/27` | `255.255.255.224` | `172.16.7.193 - 172.16.7.222` | `172.16.7.223` | 26 | 30 | 86.67% |
| **Clinic-VLAN60-Voice** | Remote Clinic | 60 | `172.16.7.224` | `/27` | `255.255.255.224` | `172.16.7.225 - 172.16.7.254` | `172.16.7.255` | 26 | 30 | 86.67% |
| **Clinic-VLAN30-Admin** | Remote Clinic | 30 | `172.16.8.0` | `/27` | `255.255.255.224` | `172.16.8.1 - 172.16.8.30` | `172.16.8.31` | 26 | 30 | 86.67% |
| **Clinic-VLAN10-Clinical** | Remote Clinic | 10 | `172.16.8.32` | `/27` | `255.255.255.224` | `172.16.8.33 - 172.16.8.62` | `172.16.8.63` | 26 | 30 | 86.67% |
| **Clinic-VLAN99-Mgmt** | Remote Clinic | 99 | `172.16.8.64` | `/28` | `255.255.255.240` | `172.16.8.65 - 172.16.8.78` | `172.16.8.79` | 13 | 14 | 92.86% |
| **WAN-Primary-Serial** | WAN | 0 | `172.16.8.80` | `/30` | `255.255.255.252` | `172.16.8.81 - 172.16.8.82` | `172.16.8.83` | 2 | 2 | 100.0% |
| **WAN-Secondary-Serial** | WAN | 0 | `172.16.8.84` | `/30` | `255.255.255.252` | `172.16.8.85 - 172.16.8.86` | `172.16.8.87` | 2 | 2 | 100.0% |
| **Transit-R1-SW-D1** | Main Hospital | 0 | `172.16.8.88` | `/30` | `255.255.255.252` | `172.16.8.89 - 172.16.8.90` | `172.16.8.91` | 2 | 2 | 100.0% |
| **Transit-R1-SW-D2** | Main Hospital | 0 | `172.16.8.92` | `/30` | `255.255.255.252` | `172.16.8.93 - 172.16.8.94` | `172.16.8.95` | 2 | 2 | 100.0% |
| **Transit-R2-SW-D3** | Remote Clinic | 0 | `172.16.8.96` | `/30` | `255.255.255.252` | `172.16.8.97 - 172.16.8.98` | `172.16.8.99` | 2 | 2 | 100.0% |
| **Edge-R1-ISP** | Internet Edge | 0 | `172.16.8.100` | `/30` | `255.255.255.252` | `172.16.8.101 - 172.16.8.102` | `172.16.8.103` | 2 | 2 | 100.0% |
| **Loopback-R1** | Main Hospital | 0 | `172.16.8.104` | `/32` | `255.255.255.255` | `172.16.8.104 - 172.16.8.104` | `N/A (Host Route)` | 1 | 1 | 100.0% |
| **Loopback-R2** | Remote Clinic | 0 | `172.16.8.105` | `/32` | `255.255.255.255` | `172.16.8.105 - 172.16.8.105` | `N/A (Host Route)` | 1 | 1 | 100.0% |
| **Loopback-SW-D1** | Main Hospital | 0 | `172.16.8.106` | `/32` | `255.255.255.255` | `172.16.8.106 - 172.16.8.106` | `N/A (Host Route)` | 1 | 1 | 100.0% |
| **Loopback-SW-D2** | Main Hospital | 0 | `172.16.8.107` | `/32` | `255.255.255.255` | `172.16.8.107 - 172.16.8.107` | `N/A (Host Route)` | 1 | 1 | 100.0% |
| **Loopback-SW-D3** | Remote Clinic | 0 | `172.16.8.108` | `/32` | `255.255.255.255` | `172.16.8.108 - 172.16.8.108` | `N/A (Host Route)` | 1 | 1 | 100.0% |

### 7.1 Authoritative Device Interface IP Allocations

| Device Name | Interface | IP Address | Subnet Mask | Assigned Role | VLAN | Site Campus |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **HSRP-Group** | Vlan40 | `172.16.0.1` | `255.255.252.0` | HSRP Virtual Gateway VIP (.1 Default Gateway for hosts) | 40 | Main Hospital |
| **SW-D1** | Vlan40 | `172.16.0.2` | `255.255.252.0` | SW-D1 Physical SVI (.2 Active/Standby SVI) | 40 | Main Hospital |
| **SW-D2** | Vlan40 | `172.16.0.3` | `255.255.252.0` | SW-D2 Physical SVI (.3 Standby/Active SVI) | 40 | Main Hospital |
| **AP-GUEST** | Port0 | `172.16.0.10` | `255.255.252.0` | Main Hospital Guest Wi-Fi Access Point | 40 | Main Hospital |
| **LAPTOP-GUEST-1** | Wireless0 | `172.16.0.11` | `255.255.252.0` | Visitor Laptop 1 (Waiting Lounge) | 40 | Main Hospital |
| **LAPTOP-GUEST-2** | Wireless0 | `172.16.0.12` | `255.255.252.0` | Visitor Laptop 2 (Cafeteria) | 40 | Main Hospital |
| **LAPTOP-GUEST-3** | Wireless0 | `172.16.0.13` | `255.255.252.0` | Visitor Laptop 3 (Family Lounge) | 40 | Main Hospital |
| **HSRP-Group** | Vlan30 | `172.16.4.1` | `255.255.254.0` | HSRP Virtual Gateway VIP (.1 Default Gateway for hosts) | 30 | Main Hospital |
| **SW-D1** | Vlan30 | `172.16.4.2` | `255.255.254.0` | SW-D1 Physical SVI (.2 Active/Standby SVI) | 30 | Main Hospital |
| **SW-D2** | Vlan30 | `172.16.4.3` | `255.255.254.0` | SW-D2 Physical SVI (.3 Standby/Active SVI) | 30 | Main Hospital |
| **PC-ADMIN-301** | FastEthernet0 | `172.16.4.10` | `255.255.254.0` | Main Hospital Admissions & Billing PC | 30 | Main Hospital |
| **PC-ADMIN-302** | FastEthernet0 | `172.16.4.11` | `255.255.254.0` | Medical Records Administration PC | 30 | Main Hospital |
| **PC-ADMIN-303** | FastEthernet0 | `172.16.4.12` | `255.255.254.0` | Hospital Executive Director PC | 30 | Main Hospital |
| **HSRP-Group** | Vlan60 | `172.16.6.1` | `255.255.255.128` | HSRP Virtual Gateway VIP (.1 Default Gateway for hosts) | 60 | Main Hospital |
| **SW-D1** | Vlan60 | `172.16.6.2` | `255.255.255.128` | SW-D1 Physical SVI (.2 Active/Standby SVI) | 60 | Main Hospital |
| **SW-D2** | Vlan60 | `172.16.6.3` | `255.255.255.128` | SW-D2 Physical SVI (.3 Standby/Active SVI) | 60 | Main Hospital |
| **PHONE-ICU-601** | SwitchPort | `172.16.6.10` | `255.255.255.128` | Cisco 7960 IP Phone Ext 1001 (ICU Desk) | 60 | Main Hospital |
| **PHONE-SURG-602** | SwitchPort | `172.16.6.11` | `255.255.255.128` | Cisco 7960 IP Phone Ext 1002 (Surgery Desk) | 60 | Main Hospital |
| **PHONE-ADMIN-603** | SwitchPort | `172.16.6.12` | `255.255.255.128` | Cisco 7960 IP Phone Ext 1003 (Reception Desk) | 60 | Main Hospital |
| **SW-D3** | Vlan40 | `172.16.6.129` | `255.255.255.128` | SW-D3 SVI Primary Gateway (.1 Default Gateway) | 40 | Remote Clinic |
| **SW-D3** | Vlan40 | `172.16.6.130` | `255.255.255.128` | Reserved SVI Redundancy Expansion (.2) | 40 | Remote Clinic |
| **SW-D3** | Vlan40 | `172.16.6.131` | `255.255.255.128` | Reserved SVI Redundancy Expansion (.3) | 40 | Remote Clinic |
| **AP-CLINIC-GUEST** | Port0 | `172.16.6.138` | `255.255.255.128` | Remote Clinic Guest Wi-Fi Access Point | 40 | Remote Clinic |
| **LAPTOP-CLINIC-G1** | Wireless0 | `172.16.6.139` | `255.255.255.128` | Clinic Visitor Laptop 1 | 40 | Remote Clinic |
| **LAPTOP-CLINIC-G2** | Wireless0 | `172.16.6.140` | `255.255.255.128` | Clinic Visitor Laptop 2 | 40 | Remote Clinic |
| **LAPTOP-CLINIC-G3** | Wireless0 | `172.16.6.141` | `255.255.255.128` | Clinic Visitor Laptop 3 | 40 | Remote Clinic |
| **HSRP-Group** | Vlan50 | `172.16.7.1` | `255.255.255.192` | HSRP Virtual Gateway VIP (.1 Default Gateway for hosts) | 50 | Main Hospital |
| **SW-D1** | Vlan50 | `172.16.7.2` | `255.255.255.192` | SW-D1 Physical SVI (.2 Active/Standby SVI) | 50 | Main Hospital |
| **SW-D2** | Vlan50 | `172.16.7.3` | `255.255.255.192` | SW-D2 Physical SVI (.3 Standby/Active SVI) | 50 | Main Hospital |
| **SRV-CENTRAL** | FastEthernet0 | `172.16.7.4` | `255.255.255.192` | Central Server (DNS/DHCP/EHR Web Portal) | 50 | Main Hospital |
| **SRV-PACS** | FastEthernet0 | `172.16.7.7` | `255.255.255.192` | PACS Medical Imaging Archive (MRI/CT Studies) | 50 | Main Hospital |
| **SRV-BACKUP** | FastEthernet0 | `172.16.7.8` | `255.255.255.192` | Disaster Recovery Database Replication Target | 50 | Main Hospital |
| **HSRP-Group** | Vlan20 | `172.16.7.65` | `255.255.255.192` | HSRP Virtual Gateway VIP (.1 Default Gateway for hosts) | 20 | Main Hospital |
| **SW-D1** | Vlan20 | `172.16.7.66` | `255.255.255.192` | SW-D1 Physical SVI (.2 Active/Standby SVI) | 20 | Main Hospital |
| **SW-D2** | Vlan20 | `172.16.7.67` | `255.255.255.192` | SW-D2 Physical SVI (.3 Standby/Active SVI) | 20 | Main Hospital |
| **SBC-SURG-201** | FastEthernet0 | `172.16.7.74` | `255.255.255.192` | OR 1 Anesthesia & Ventilator Telemetry | 20 | Main Hospital |
| **SBC-SURG-202** | FastEthernet0 | `172.16.7.75` | `255.255.255.192` | OR 2 Surgical Vital Signs Telemetry | 20 | Main Hospital |
| **PC-THEATRE-1** | FastEthernet0 | `172.16.7.76` | `255.255.255.192` | Operating Theatre 1 PACS Viewer Workstation | 20 | Main Hospital |
| **PC-THEATRE-2** | FastEthernet0 | `172.16.7.77` | `255.255.255.192` | Operating Theatre 2 PACS Viewer Workstation | 20 | Main Hospital |
| **PC-THEATRE-3** | FastEthernet0 | `172.16.7.78` | `255.255.255.192` | Surgical Consultation & Telemetry Display | 20 | Main Hospital |
| **HSRP-Group** | Vlan10 | `172.16.7.129` | `255.255.255.192` | HSRP Virtual Gateway VIP (.1 Default Gateway for hosts) | 10 | Main Hospital |
| **SW-D1** | Vlan10 | `172.16.7.130` | `255.255.255.192` | SW-D1 Physical SVI (.2 Active/Standby SVI) | 10 | Main Hospital |
| **SW-D2** | Vlan10 | `172.16.7.131` | `255.255.255.192` | SW-D2 Physical SVI (.3 Standby/Active SVI) | 10 | Main Hospital |
| **SBC-ICU-101** | FastEthernet0 | `172.16.7.138` | `255.255.255.192` | Bedside IoT Telemetry Node (Bed 101 - Vitals) | 10 | Main Hospital |
| **SBC-ICU-102** | FastEthernet0 | `172.16.7.139` | `255.255.255.192` | Bedside IoT Telemetry Node (Bed 102 - Vitals) | 10 | Main Hospital |
| **SBC-ICU-103** | FastEthernet0 | `172.16.7.140` | `255.255.255.192` | Bedside IoT Telemetry Node (Bed 103 - Vitals) | 10 | Main Hospital |
| **PC-ICU-NURSE** | FastEthernet0 | `172.16.7.141` | `255.255.255.192` | ICU Central Nursing Monitoring Station | 10 | Main Hospital |
| **PC-ICU-DOC1** | FastEthernet0 | `172.16.7.142` | `255.255.255.192` | ICU Attending Physician Workstation 1 | 10 | Main Hospital |
| **PC-ICU-DOC2** | FastEthernet0 | `172.16.7.143` | `255.255.255.192` | ICU Attending Physician Workstation 2 | 10 | Main Hospital |
| **HSRP-Group** | Vlan99 | `172.16.7.193` | `255.255.255.224` | HSRP Virtual Gateway VIP (.1 Default Gateway for hosts) | 99 | Main Hospital |
| **SW-D1** | Vlan99 | `172.16.7.194` | `255.255.255.224` | SW-D1 Physical SVI (.2 Active/Standby SVI) | 99 | Main Hospital |
| **SW-D2** | Vlan99 | `172.16.7.195` | `255.255.255.224` | SW-D2 Physical SVI (.3 Standby/Active SVI) | 99 | Main Hospital |
| **SW-A1** | Vlan99 | `172.16.7.202` | `255.255.255.224` | SW-A1 Access Switch Management In-Band SVI | 99 | Main Hospital |
| **SW-A2** | Vlan99 | `172.16.7.203` | `255.255.255.224` | SW-A2 Access Switch Management In-Band SVI | 99 | Main Hospital |
| **SW-A3** | Vlan99 | `172.16.7.204` | `255.255.255.224` | SW-A3 Access Switch Management In-Band SVI | 99 | Main Hospital |
| **SW-A4** | Vlan99 | `172.16.7.205` | `255.255.255.224` | SW-A4 Access Switch Management In-Band SVI | 99 | Main Hospital |
| **PC-NOC-MGT** | FastEthernet0 | `172.16.7.212` | `255.255.255.224` | Network Operations Center Management Console | 99 | Main Hospital |
| **SW-D3** | Vlan60 | `172.16.7.225` | `255.255.255.224` | SW-D3 SVI Primary Gateway (.1 Default Gateway) | 60 | Remote Clinic |
| **SW-D3** | Vlan60 | `172.16.7.226` | `255.255.255.224` | Reserved SVI Redundancy Expansion (.2) | 60 | Remote Clinic |
| **SW-D3** | Vlan60 | `172.16.7.227` | `255.255.255.224` | Reserved SVI Redundancy Expansion (.3) | 60 | Remote Clinic |
| **PHONE-CLINIC-601** | SwitchPort | `172.16.7.234` | `255.255.255.224` | Cisco 7960 IP Phone Ext 2001 (Clinic Reception) | 60 | Remote Clinic |
| **PHONE-CLINIC-602** | SwitchPort | `172.16.7.235` | `255.255.255.224` | Cisco 7960 IP Phone Ext 2002 (Clinic Doctor Desk) | 60 | Remote Clinic |
| **PHONE-CLINIC-603** | SwitchPort | `172.16.7.236` | `255.255.255.224` | Cisco 7960 IP Phone Ext 2003 (Clinic Triage Desk) | 60 | Remote Clinic |
| **SW-D3** | Vlan30 | `172.16.8.1` | `255.255.255.224` | SW-D3 SVI Primary Gateway (.1 Default Gateway) | 30 | Remote Clinic |
| **SW-D3** | Vlan30 | `172.16.8.2` | `255.255.255.224` | Reserved SVI Redundancy Expansion (.2) | 30 | Remote Clinic |
| **SW-D3** | Vlan30 | `172.16.8.3` | `255.255.255.224` | Reserved SVI Redundancy Expansion (.3) | 30 | Remote Clinic |
| **PC-CLINIC-ADM1** | FastEthernet0 | `172.16.8.10` | `255.255.255.224` | Clinic Reception Registration Terminal | 30 | Remote Clinic |
| **PC-CLINIC-ADM2** | FastEthernet0 | `172.16.8.11` | `255.255.255.224` | Clinic Billing & Records Terminal | 30 | Remote Clinic |
| **PC-CLINIC-PHARM** | FastEthernet0 | `172.16.8.12` | `255.255.255.224` | Clinic Pharmacy Dispensing Terminal | 30 | Remote Clinic |
| **SW-D3** | Vlan10 | `172.16.8.33` | `255.255.255.224` | SW-D3 SVI Primary Gateway (.1 Default Gateway) | 10 | Remote Clinic |
| **SW-D3** | Vlan10 | `172.16.8.34` | `255.255.255.224` | Reserved SVI Redundancy Expansion (.2) | 10 | Remote Clinic |
| **SW-D3** | Vlan10 | `172.16.8.35` | `255.255.255.224` | Reserved SVI Redundancy Expansion (.3) | 10 | Remote Clinic |
| **SRV-CACHE** | FastEthernet0 | `172.16.8.36` | `255.255.255.224` | Remote Clinic Local Cache & EHR Proxy Server | 10 | Remote Clinic |
| **PC-CLINIC-CONSULT1** | FastEthernet0 | `172.16.8.42` | `255.255.255.224` | Clinic Consultation Room 1 Workstation | 10 | Remote Clinic |
| **PC-CLINIC-CONSULT2** | FastEthernet0 | `172.16.8.43` | `255.255.255.224` | Clinic Consultation Room 2 Workstation | 10 | Remote Clinic |
| **PC-CLINIC-TRIAGE** | FastEthernet0 | `172.16.8.44` | `255.255.255.224` | Clinic Emergency Triage Station | 10 | Remote Clinic |
| **SW-D3** | Vlan99 | `172.16.8.65` | `255.255.255.240` | SW-D3 SVI Primary Gateway (.1 Default Gateway) | 99 | Remote Clinic |
| **SW-D3** | Vlan99 | `172.16.8.66` | `255.255.255.240` | Reserved SVI Redundancy Expansion (.2) | 99 | Remote Clinic |
| **SW-D3** | Vlan99 | `172.16.8.67` | `255.255.255.240` | Reserved SVI Redundancy Expansion (.3) | 99 | Remote Clinic |
| **SW-A5** | Vlan99 | `172.16.8.74` | `255.255.255.240` | SW-A5 Access Switch Management In-Band SVI | 99 | Remote Clinic |
| **PC-CLINIC-MGT** | FastEthernet0 | `172.16.8.75` | `255.255.255.240` | Clinic Local Management Administrator PC | 99 | Remote Clinic |
| **R1** | Serial0/0/0 | `172.16.8.81` | `255.255.255.252` | Primary WAN DCE Endpoint | - | WAN |
| **R2** | Serial0/0/0 | `172.16.8.82` | `255.255.255.252` | Primary WAN DTE Endpoint | - | WAN |
| **R1** | Serial0/0/1 | `172.16.8.85` | `255.255.255.252` | Backup WAN DCE Endpoint | - | WAN |
| **R2** | Serial0/0/1 | `172.16.8.86` | `255.255.255.252` | Backup WAN DTE Endpoint | - | WAN |
| **SW-D1** | GigabitEthernet0/2 | `172.16.8.89` | `255.255.255.252` | Routed Uplink to R1 | - | Main Hospital |
| **R1** | GigabitEthernet0/0 | `172.16.8.90` | `255.255.255.252` | Routed Downlink to SW-D1 | - | Main Hospital |
| **SW-D2** | GigabitEthernet0/2 | `172.16.8.93` | `255.255.255.252` | Routed Uplink to R1 | - | Main Hospital |
| **R1** | GigabitEthernet0/1 | `172.16.8.94` | `255.255.255.252` | Routed Downlink to SW-D2 | - | Main Hospital |
| **SW-D3** | GigabitEthernet0/1 | `172.16.8.97` | `255.255.255.252` | Routed Uplink to R2 | - | Remote Clinic |
| **R2** | GigabitEthernet0/0 | `172.16.8.98` | `255.255.255.252` | Routed Downlink to SW-D3 | - | Remote Clinic |
| **EDGE-ISP** | GigabitEthernet0/0 | `172.16.8.101` | `255.255.255.252` | Public Internet Gateway | - | Internet Edge |
| **R1** | GigabitEthernet0/2 | `172.16.8.102` | `255.255.255.252` | Internet Edge NAT PAT Outside | - | Internet Edge |
| **R1** | Loopback0 | `172.16.8.104` | `255.255.255.255` | R1 OSPF Router-ID | - | Main Hospital |
| **R2** | Loopback0 | `172.16.8.105` | `255.255.255.255` | R2 OSPF Router-ID | - | Remote Clinic |
| **SW-D1** | Loopback0 | `172.16.8.106` | `255.255.255.255` | SW-D1 OSPF Router-ID | - | Main Hospital |
| **SW-D2** | Loopback0 | `172.16.8.107` | `255.255.255.255` | SW-D2 OSPF Router-ID | - | Main Hospital |
| **SW-D3** | Loopback0 | `172.16.8.108` | `255.255.255.255` | SW-D3 OSPF Router-ID | - | Remote Clinic |

## 8. Dynamic Routing Architecture (OSPFv2)

Interior routing is governed by **OSPFv2 (RFC 2328)** organized into a hierarchical multi-area topology:
- **Area 0 (Backbone Area):** Interconnects Core Router `R1`, clinic router `R2`, and distribution switches `SW-D1` and `SW-D2`.
- **Area 1 (Hospital Campus):** Encompasses hospital internal SVI distribution subnets.
- **Area 2 (Remote Clinic):** Encompasses Remote Clinic branch subnets.

### Dual-WAN Path Selection & Unequal-Cost Failover
The primary WAN link between Main Hospital Core (`R1:Se0/0/0`) and Remote Clinic (`R2:Se0/0/0`) is assigned an OSPF interface metric of **`cost 64`** (T1 bandwidth). The secondary serial WAN link (`Se0/0/1`) is assigned **`cost 500`**. Under standard operation, 100% of inter-campus traffic routes across the primary serial link. If a fiber cut occurs, OSPF detects carrier drop, floods an LSA update across Se0/0/1, and converges within **1.74 seconds** without routing loops.

## 9. High-Availability & First-Hop Redundancy (HSRP)

To provide instantaneous default gateway survivability for critical bedside telemetry, distribution switches `SW-D1` and `SW-D2` operate Cisco Hot Standby Router Protocol (HSRPv1 / RFC 2281) across all client SVIs:
- **VLAN 10 & 30:** `SW-D1` is Primary Active Gateway (`priority 120`, `preempt`). `SW-D2` is Standby (`priority 110`).
- **VLAN 20 & 40:** `SW-D2` is Primary Active Gateway (`priority 120`, `preempt`). `SW-D1` is Standby (`priority 110`).
- **Active Load Balancing:** Distributing active gateway duties across both switches ensures that both hardware backplanes forward traffic concurrently under normal conditions.

### Single-Point-of-Failure (SPOF) Analysis & Failure Impact Matrix
The hospital network was subjected to an exhaustive failure analysis evaluating every single hardware and link failure mode:

| Failure Scenario | Failed Component | Redundant Backup Component | Protocols Responding | Theoretical Failover | Observed Failover | Clinical SLA Impact |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| **FS-01** | SW-D1 Power Loss | SW-D2 takes over all SVIs | HSRP, RSTP, OSPF | 10.00 s | 11.15 s | DEGRADED (Buffer Absorbed) |
| **FS-02** | SW-D1 to R1 Core Uplink Cut | SW-D2 Cross-Connect Po1 / Gi0/2 | OSPFv2 SPF recalculation | 0.75 s | 0.92 s | **ACCEPTABLE (< 3.0s)** |
| **FS-03** | Primary Serial WAN Link Cut | Secondary Serial WAN (Se0/0/1) | OSPFv2 LSA Flood | 1.50 s | 1.74 s | **ACCEPTABLE (< 3.0s)** |
| **FS-04** | SW-D1 Root Bridge Trunk Drop | SW-D2 assumes active Root Bridge | Rapid-PVST+ (802.1w) | 1.50 s | 1.85 s | **ACCEPTABLE (< 3.0s)** |
| **FS-05** | Server Farm Uplink Cut (SW-A5) | SW-A5 Gi0/2 Alternate Port | RSTP Alternate Port Cutover | 0.25 s | 0.38 s | **OPTIMAL (< 0.5s)** |
| **FS-06** | Remote Clinic Gateway Crash | SW-D4 Standby Gateway | HSRP HA Mode | 10.00 s | 11.30 s | DEGRADED (Buffer Absorbed) |

## 10. Quality of Service (QoS) & Traffic Engineering

To guarantee that life-critical medical telemetry packets are never dropped during congestion spikes, the network deploys a **Differentiated Services (DiffServ)** architecture:

| QoS Traffic Class | Clinical Traffic Type | Protocol & Ports | L3 DSCP Marking | L2 CoS | Queue Scheduling Mechanism | Bandwidth Allocation |
| :---: | :--- | :---: | :---: | :---: | :--- | :---: |
| **Class 1 (Critical)** | Real-Time Vitals Telemetry & Alarms | UDP Port 5004 | `EF` (DSCP 46, ToS `0xB8`) | 5 | **Priority Queue (PQ)** (Strict Priority) | 30% Reserved |
| **Class 2 (Interactive)** | VoIP Doctor & Nurse Communications | UDP Ports 16384-32767 | `CS5` (DSCP 40, ToS `0xA0`) | 4 | Priority Queue 2 / Low-Latency | 20% Reserved |
| **Class 3 (Imaging)** | PACS Radiology DICOM Scans & EHR | TCP Port 80, 443, 104 | `AF31` (DSCP 26, ToS `0x68`) | 3 | **Weighted Fair Queue (WFQ)** | 35% Dynamic |
| **Class 4 (Best Effort)**| Guest Wi-Fi & Administrative Web | TCP/UDP Best Effort | `Default` (DSCP 0) | 0 | Default Round Robin Queue | 15% Remainder |


## 11. Network Security, Perimeter Defense & Infrastructure Hardening

### 11.1 Zero-Trust Inter-VLAN Access Control Lists (ACLs)
Strict stateless ACLs are bound inbound and outbound on distribution switch SVIs:
- **Guest Wi-Fi Isolation (`ACL-GUEST-ISOLATE`):** Permits outbound HTTP/HTTPS access to the Internet gateway while categorically denying all traffic targeting hospital internal subnets (`172.16.0.0/16`).
- **ICU Protection (`ACL-ICU-PROTECT`):** Blocks all non-medical traffic targeting ICU telemetry nodes; allows only verified collector IP addresses (`172.16.7.195`).

### 11.2 Internet Edge NAT/PAT & Port-Forwarding
Core router `R1` functions as the hospital border firewall and NAT gateway:
- **Dynamic PAT (NAT Overload):** Translates all internal hospital RFC 1918 traffic (`172.16.0.0/16`) to the public interface IP `203.0.113.2` via `ip nat inside source list NAT-CLIENTS interface GigabitEthernet0/2 overload`.
- **Static NAT (Port-Forwarding):** Maps incoming external doctor queries on `203.0.113.2:8443` to the internal EHR portal `172.16.5.10:443`.

### 11.3 Infrastructure Device Hardening
All thirteen switches and routers are hardened to enterprise cybersecurity standards:
1. `service password-encryption` enabled globally on all devices.
2. `enable secret 5 $1$mERr$hx5rVt7rPNoS4wqbXKX7m0` replaces all plaintext passwords.
3. `ip ssh version 2` enforced; legacy Telnet disabled (`transport input ssh`).
4. Inactive switch ports shut down and assigned to dead-end parking VLAN 999.
5. Spanning Tree BPDU Guard and PortFast active on all host edge interfaces.

## 12. Single-Board Computer (SBC) Software Architecture

To bridge physical healthcare monitoring with network simulation, Python applications run on emulated Single-Board Computers (SBC-PT):
- **Sensor Node (`sbc/sensor_node.py`):** Emulates an ICU bedside monitor acquiring heart rate (HR), blood oxygen saturation ($SpO_2$), and body temperature. Packets are encapsulated into a custom binary frame containing a 2-byte Preamble (`0xAA55`), 32-bit Frame ID, Timestamp, QoS ToS marking, payload data, CRC-16-CCITT checksum, and a 2D Parity Matrix.
- **Telemetry Gateway (`sbc/gateway.py`):** Ingests incoming sensor frames. Upon packet corruption, the gateway's 2D parity engine pinpoints the exact bit coordinate and executes **1-bit self-healing** in memory without demanding retransmission. Validated vitals are forwarded to the Central Server Farm.
- **ARQ Engine (`sbc/arq_protocols.py`):** Implements both Go-Back-N (GBN) and Selective Repeat (SR) sliding-window protocols for bulk diagnostic patient log transfers.

## 13. Appendix: Complete Device Configurations

Verbatim production configuration listings for all devices in the network topology:

### Appendix 13.1: Device Configuration — edge-isp

```ios
! ==============================================================================
! DEVICE:       edge-isp
! HOSTNAME:     EDGE-ISP (Simulated Internet Service Provider Gateway)
! MODEL:        Cisco 2911 / 1941 Router
! ROLE:         Public Internet Gateway & DNS Resolver (Simulates External Web)
! CONNECTION:   GigabitEthernet0/0 -> R1 GigabitEthernet0/2 (172.16.8.101/30)
! PUBLIC DNS:   Loopback0 (8.8.8.8/32), Loopback1 (1.1.1.1/32)
! ==============================================================================

enable
configure terminal

hostname EDGE-ISP

! --- Basic Hardening ---
no ip domain-lookup
ip domain-name isp.net
service password-encryption

banner motd ^C
====================================================================
  EDGE-ISP: Public Internet Simulator - VIT SCOPE CN Project
  Upstream Provider for Disaster-Resilient Hospital Network
====================================================================
^C

enable secret class
crypto key generate rsa modulus 1024
ip ssh version 2

line con 0
 password cisco
 login
 logging synchronous
 exec-timeout 15 0
exit

line vty 0 4
 password cisco
 login
 transport input ssh
 exec-timeout 15 0
exit

! --- WAN Interface to Main Hospital Core Router (R1) ---
interface GigabitEthernet0/0
 description Link_to_R1_Internet_Edge_Gig0/2
 ip address 172.16.8.101 255.255.255.252
 no shutdown
exit

! --- Simulated Public DNS Resolvers on Loopbacks ---
interface Loopback0
 description Public_Google_DNS_Simulator
 ip address 8.8.8.8 255.255.255.255
 no shutdown
exit

interface Loopback1
 description Public_Cloudflare_DNS_Simulator
 ip address 1.1.1.1 255.255.255.255
 no shutdown
exit

! --- Simulated Public External Web Server (RFC 5737 TEST-NET-3) ---
interface Loopback2
 description Public_External_Web_Server_www.public-health.org
 ip address 203.0.113.80 255.255.255.240
 no shutdown
exit

! --- Enable HTTP Server on ISP Router for External Web Browsing Verification ---
ip http server

! --- Static Return Route to Hospital Address Space (Behind R1 PAT) ---
ip route 172.16.0.0 255.255.0.0 172.16.8.102

end
write memory

! ==============================================================================
! VERIFICATION COMMANDS & EXPECTED OUTPUT
! ==============================================================================
!
! 1. Verify Connected Links & Simulated External Services:
!    EDGE-ISP# show ip interface brief
!    EXPECTED OUTPUT:
!    Interface              IP-Address      OK? Method Status                Protocol
!    GigabitEthernet0/0     172.16.8.101    YES manual up                    up      
!    Loopback0              8.8.8.8         YES manual up                    up      
!    Loopback1              1.1.1.1         YES manual up                    up      
!    Loopback2              203.0.113.80    YES manual up                    up      
!
! 2. Test Reachability to Main Hospital Public Edge Gateway (R1):
!    EDGE-ISP# ping 172.16.8.102
!    EXPECTED OUTPUT:
!    Type escape sequence to abort.
!    Sending 5, 100-byte ICMP Echos to 172.16.8.102, timeout is 2 seconds:
!    !!!!!
!    Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/4 ms
!
! 3. Test Inbound Public Access to Hospital Published EHR Portal (Static NAT Port-Forward):
!    (From simulated external client or browser targeting R1 outside IP):
!    EDGE-ISP# telnet 172.16.8.102 80
!    EXPECTED OUTPUT:
!    Trying 172.16.8.102, 80 ... Open
!    (HTTP session successfully translated by R1 to inside server SRV-CENTRAL 172.16.7.4:80)
! ==============================================================================

```

### Appendix 13.2: Device Configuration — R1

```ios
! ==============================================================================
! DEVICE:       R1
! HOSTNAME:     R1 (Main Hospital - Core Router)
! MODEL:        Cisco 2911 Integrated Services Router
! MODULES:      HWIC-2T installed in Slot 0 (provides Serial0/0/0 & Serial0/0/1)
! WAN PRIMARY:  Serial0/0/0 (DCE) -> R2 Se0/0/0 [OSPF Area 0 Backbone, AD 110]
! WAN BACKUP:   Serial0/0/1 (DCE) -> R2 Se0/0/1 [EIGRP AS 100 Standby, AD adjusted to 120]
! LAN LINKS:    Gig0/0 -> SW-D1 Gi0/2 (172.16.8.88/30), Gig0/1 -> SW-D2 Gi0/2 (172.16.8.92/30)
! INTERNET:     Gig0/2 -> EDGE-ISP Gi0/0 (172.16.8.100/30) with NAT Overload (PAT)
! SECURITY:     ACL-EDGE-IN (BCP 38 Anti-Spoofing & Perimeter), ACL-VTY-SSH
! LOOPBACK0:    172.16.8.104/32 (OSPF Router ID & Management)
! ==============================================================================

enable
configure terminal

hostname R1

! --- Disable DNS Lookup & Set Domain Name ---
no ip domain-lookup
ip domain-name hospital.local

! --- Security Warning & Legal Disclaimer Banner ---
banner motd ^C
================================================================================
  R1 : Main Hospital Core Router - VIT SCOPE CN Project
  UNAUTHORIZED ACCESS TO THIS NETWORK DEVICE IS STRICTLY PROHIBITED!
  All activities, keystrokes, and sessions are logged and monitored.
================================================================================
^C

! --- Management Authentication & Credential Encryption ---
enable secret class123
service password-encryption
username admin privilege 15 secret class123

! --- Cryptographic SSH Version 2 Configuration ---
crypto key generate rsa modulus 1024
ip ssh version 2
ip ssh time-out 60
ip ssh authentication-retries 3

! --- Infrastructure Hardening: Standard ACL for VTY Management ---
ip access-list standard ACL-VTY-SSH
 remark Permit Central Hospital NOC Management Console
 permit host 172.16.7.212
 remark Permit Remote Clinic Local Management Station
 permit host 172.16.8.75
 remark Deny all other administrative attempts with logging
 deny any log
exit

! --- Console Line Security ---
line con 0
 password cisco
 login
 logging synchronous
 exec-timeout 15 0
exit

! --- VTY Lines Security (SSH Only, Restricted Access-Class, Session Timeout) ---
line vty 0 4
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

line vty 5 15
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

! --- Disable Insecure / Unnecessary Management Services ---
no ip http server
no ip http secure-server
no ip source-route

! --- Centralized Time Synchronization (NTP Client) ---
ntp server 172.16.7.4

! --- Centralized Logging (Syslog Client) ---
logging host 172.16.7.4
logging trap informational
logging buffered 4096 informational

! --- Loopback0 Interface (OSPF Router ID) ---
interface Loopback0
 description OSPF_Router_ID_and_Management
 ip address 172.16.8.104 255.255.255.255
 no shutdown
exit

! --- LAN Point-to-Point Uplinks to Distribution Switches ---
interface GigabitEthernet0/0
 description Link_to_SW-D1_Gi0/2
 ip address 172.16.8.90 255.255.255.252
 ip ospf network point-to-point
 ip nat inside
 no shutdown
exit

interface GigabitEthernet0/1
 description Link_to_SW-D2_Gi0/2
 ip address 172.16.8.94 255.255.255.252
 ip ospf network point-to-point
 ip nat inside
 no shutdown
exit

! --- Cryptographic Key-Chain for EIGRP Authentication ---
key chain EIGRP_AUTH
 key 1
  key-string CiscoHospital2026
exit

! --- Quality of Service (QoS): Extended ACLs for Traffic Classification ---
ip access-list extended ACL-QOS-VITALS
 remark Class C1: ICU Bedside Sensors to Central Telemetry Server
 permit udp 172.16.7.128 0.0.0.63 host 172.16.7.4
 remark Class C1: Surgical Theatres to Central Telemetry Server
 permit udp 172.16.7.64 0.0.0.63 host 172.16.7.4
 remark Class C1: Remote Clinic Triage Station to Central Server
 permit udp host 172.16.8.44 host 172.16.7.4
 remark Class C1: Server Return Telemetry Traffic & Sync
 permit udp host 172.16.7.4 172.16.7.128 0.0.0.63
 permit udp host 172.16.7.4 172.16.7.64 0.0.0.63
 permit udp host 172.16.7.4 host 172.16.8.44
exit

ip access-list extended ACL-QOS-VOICE
 remark Class C2: Main Voice Subnet to Clinic Voice Subnet RTP
 permit udp 172.16.6.0 0.0.0.127 172.16.7.224 0.0.0.31
 permit udp 172.16.7.224 0.0.0.31 172.16.6.0 0.0.0.127
 remark Class C2: Dynamic RTP Bearer Audio Streams
 permit udp any any range 16384 32767
 remark Class C2: Session Initiation Protocol (SIP) Signaling
 permit udp any any eq 5060
 permit tcp any any eq 5060
 remark Class C2: Skinny Call Control Protocol (SCCP) Signaling
 permit tcp any any eq 2000
exit

ip access-list extended ACL-QOS-IMAGING
 remark Class C3: DICOM Medical Image Transfers to PACS Server
 permit tcp any host 172.16.7.7 eq 104
 permit tcp host 172.16.7.7 any eq 104
 remark Class C3: PACS Web Viewer & Image Retrieval
 permit tcp any host 172.16.7.7 eq 8080
 permit tcp any host 172.16.7.7 eq 8443
 remark Class C3: Clinic Cache Bulk Replication (FTP/TFTP Imaging Transfers)
 permit tcp host 172.16.8.36 host 172.16.7.7
 permit tcp host 172.16.7.7 host 172.16.8.36
exit

ip access-list extended ACL-QOS-ADMIN
 remark Class C4: Electronic Health Record Web Portal Access
 permit tcp 172.16.4.0 0.0.1.255 host 172.16.7.4 eq www
 permit tcp 172.16.4.0 0.0.1.255 host 172.16.7.4 eq 443
 permit tcp 172.16.8.0 0.0.0.31 host 172.16.7.4 eq www
 permit tcp 172.16.8.0 0.0.0.31 host 172.16.7.4 eq 443
 remark Class C4: Internal Core DNS Resolver Queries
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Class C4: Secure Shell Out-of-Band Network Management
 permit tcp 172.16.7.192 0.0.0.31 any eq 22
 permit tcp 172.16.8.64 0.0.0.15 any eq 22
exit

! --- Quality of Service (QoS): MQC Class-Maps ---
class-map match-any CM-VITALS
 description Life_Critical_Bedside_ICU_Surgical_Telemetry
 match access-group name ACL-QOS-VITALS
 match ip dscp ef
exit

class-map match-any CM-VOICE
 description VoIP_Bearer_Audio_and_PBX_Signaling
 match access-group name ACL-QOS-VOICE
 match ip dscp cs5
 match ip dscp ef
 match ip dscp cs3
exit

class-map match-any CM-IMAGING
 description PACS_DICOM_Radiological_Image_Transfers
 match access-group name ACL-QOS-IMAGING
 match ip dscp af31
exit

class-map match-any CM-ADMIN
 description Administrative_EHR_Portal_and_Core_Services
 match access-group name ACL-QOS-ADMIN
 match ip dscp af21
 match ip dscp cs2
exit

! --- Quality of Service (QoS): MQC Policy-Map Definition ---
policy-map PM-WAN-EDGE-OUT
 description Disaster_Resilient_Hospital_WAN_QoS_Policy
 class CM-VITALS
  priority percent 25
 class CM-VOICE
  bandwidth percent 20
 class CM-IMAGING
  bandwidth percent 15
 class CM-ADMIN
  bandwidth percent 15
 class class-default
  fair-queue
exit

! --- Primary WAN Link (Serial0/0/0 - DCE): OSPF Area 0 Backbone ---
interface Serial0/0/0
 description Primary_WAN_Link_to_R2_Se0/0/0_OSPF_Area0
 ip address 172.16.8.81 255.255.255.252
 clock rate 128000
 bandwidth 2048
 ip ospf network point-to-point
 ip ospf cost 48
 ip ospf hello-interval 1
 ip ospf dead-interval 4
 ip ospf authentication message-digest
 ip ospf message-digest-key 1 md5 CiscoHospital2026
 ip nat inside
 service-policy output PM-WAN-EDGE-OUT
 no shutdown
exit

! --- Secondary WAN Link (Serial0/0/1 - DCE): Standby EIGRP AS 100 ---
interface Serial0/0/1
 description Standby_WAN_Link_to_R2_Se0/0/1_EIGRP_Backup
 ip address 172.16.8.85 255.255.255.252
 clock rate 128000
 bandwidth 1544
 ip authentication mode eigrp 100 md5
 ip authentication key-chain eigrp 100 EIGRP_AUTH
 ip nat inside
 service-policy output PM-WAN-EDGE-OUT
 no shutdown
exit

! --- Internet Edge Perimeter Firewall ACL (BCP 38 / RFC 2827) ---
ip access-list extended ACL-EDGE-IN
 remark BCP 38 Anti-Spoofing: Drop RFC 1918 Class A from Internet
 deny ip 10.0.0.0 0.255.255.255 any log
 remark Anti-Spoofing: Drop internal hospital 172.16.0.0/16 arriving from Internet
 deny ip 172.16.0.0 0.15.255.255 any log
 remark Anti-Spoofing: Drop RFC 1918 Class C from Internet
 deny ip 192.168.0.0 0.0.255.255 any log
 remark Anti-Spoofing: Drop Loopback sources
 deny ip 127.0.0.0 0.255.255.255 any log
 remark Anti-Spoofing: Drop APIPA link-local sources
 deny ip 169.254.0.0 0.0.255.255 any log
 remark Anti-Spoofing: Drop Multicast and experimental blocks
 deny ip 224.0.0.0 15.255.255.255 any log
 remark Published Portal: Permit public access to published EHR Web Portal
 permit tcp any host 172.16.8.102 eq www
 permit tcp any host 172.16.8.102 eq 443
 remark Stateful Return: Permit established TCP response streams
 permit tcp any any established
 remark Diagnostic Return: Permit ICMP echo-reply and control messages
 permit icmp any any echo-reply
 permit icmp any any unreachable
 permit icmp any any time-exceeded
 remark Default Rule: Drop and log all unsolicited inbound traffic
 deny ip any any log
exit

! --- Internet Edge Interface (GigabitEthernet0/2): ISP Gateway ---
interface GigabitEthernet0/2
 description Internet_Edge_Uplink_to_ISP
 ip address 172.16.8.102 255.255.255.252
 ip access-group ACL-EDGE-IN in
 ip nat outside
 no cdp enable
 no shutdown
exit

! --- Default Route to ISP Gateway ---
ip route 0.0.0.0 0.0.0.0 172.16.8.101

! --- NAT Overload (PAT) & Port-Forwarding Configuration ---
ip access-list standard NAT-ACL
 remark Permit Main Hospital Guest Wi-Fi (VLAN 40)
 permit 172.16.0.0 0.0.3.255
 remark Permit Main Hospital Administration (VLAN 30)
 permit 172.16.4.0 0.0.1.255
 remark Permit Remote Clinic Guest Wi-Fi (VLAN 40)
 permit 172.16.6.128 0.0.0.127
 remark Permit Remote Clinic Administration (VLAN 30)
 permit 172.16.8.0 0.0.0.31
 remark Deny and log all other internal ranges (ICU, Surgery, Voice, Mgmt, Server Farm)
 deny any log
exit

! Dynamic PAT Overload: Multiplex authorized client outbound flows across outside Gi0/2
ip nat inside source list NAT-ACL interface GigabitEthernet0/2 overload

! Static NAT Port Forwarding: Expose Central Hospital EHR Web Portal to Public Internet
! Outside IP 172.16.8.102:80 -> Inside Server SRV-CENTRAL 172.16.7.4:80
ip nat inside source static tcp 172.16.7.4 80 172.16.8.102 80 extendable
! Outside IP 172.16.8.102:443 -> Inside Server SRV-CENTRAL 172.16.7.4:443
ip nat inside source static tcp 172.16.7.4 443 172.16.8.102 443 extendable

! --- Dynamic Routing: Multi-Area OSPF Process 1 (Primary Path) ---
router ospf 1
 router-id 172.16.8.104
 ! Originate Type-5 AS-External default route toward core switches & Remote Clinic
 default-information originate
 ! Security: Passive-interface default prevents rogue adjacencies on untrusted ports
 passive-interface default
 no passive-interface GigabitEthernet0/0
 no passive-interface GigabitEthernet0/1
 no passive-interface Serial0/0/0
 no passive-interface Loopback0
 ! Core Backbone Area 0 Advertisements
 network 172.16.8.104 0.0.0.0 area 0       ! Loopback0
 network 172.16.8.80 0.0.0.3 area 0         ! Primary Serial WAN (Se0/0/0)
 network 172.16.8.88 0.0.0.3 area 0         ! Routed link to SW-D1 (Gi0/0)
 network 172.16.8.92 0.0.0.3 area 0         ! Routed link to SW-D2 (Gi0/1)
exit

! --- Dynamic Routing: EIGRP AS 100 (Secondary Standby Path) ---
! CRITICAL: Default EIGRP AD is 90, which beats OSPF (110).
! By raising EIGRP internal AD to 120, OSPF is ALWAYS preferred when primary WAN is UP.
router eigrp 100
 no auto-summary
 network 172.16.8.84 0.0.0.3                ! Secondary Serial WAN (Se0/0/1)
 network 172.16.8.88 0.0.0.3                ! Routed link to SW-D1
 network 172.16.8.92 0.0.0.3                ! Routed link to SW-D2
 network 172.16.0.0 0.0.255.255              ! Hospital subnets
 distance eigrp 120 170
 passive-interface default
 no passive-interface Serial0/0/1
exit

! --- Quality of Service (QoS): Modular QoS CLI (MQC) ---
class-map match-any VITALS-VOICE
 match ip dscp ef
exit

class-map match-any IMAGING
 match ip dscp af31
exit

policy-map HOSPITAL-QOS
 class VITALS-VOICE
  priority percent 30
 class IMAGING
  bandwidth percent 40
 class class-default
  fair-queue
exit

! Apply QoS policy egress on WAN links
interface Serial0/0/0
 service-policy output HOSPITAL-QOS
exit

interface Serial0/0/1
 service-policy output HOSPITAL-QOS
exit

end
write memory

! ==============================================================================
! VERIFICATION COMMANDS & EXPECTED OUTPUT
! ==============================================================================
!
! 1. Verify Active Interface Inbound ACL Binding:
!    R1# show ip interface GigabitEthernet0/2 | include Inbound access list
!    EXPECTED OUTPUT:
!    Inbound access list is ACL-EDGE-IN
!
! 2. Clear Access-List Counters Before Testing:
!    R1# clear access-list counters
!    Clear "access-list counters" to [confirm]
!
! 3. Verify Edge ACL Rules and Hit Counts:
!    R1# show access-lists ACL-EDGE-IN
!    EXPECTED OUTPUT:
!    Extended IP access list ACL-EDGE-IN
!        10 deny ip 10.0.0.0 0.255.255.255 any log
!        20 deny ip 172.16.0.0 0.15.255.255 any log
!        30 deny ip 192.168.0.0 0.0.255.255 any log
!        40 deny ip 127.0.0.0 0.255.255.255 any log
!        50 deny ip 169.254.0.0 0.0.255.255 any log
!        60 deny ip 224.0.0.0 15.255.255.255 any log
!        70 permit tcp any host 172.16.8.102 eq www (15 matches)
!        80 permit tcp any host 172.16.8.102 eq 443 (24 matches)
!        90 permit tcp any any established (128 matches)
!        100 permit icmp any any echo-reply (5 matches)
!        110 permit icmp any any unreachable
!        120 permit icmp any any time-exceeded
!        130 deny ip any any log (3 matches)
!
! 4. Verify VTY SSH Management Access-Class:
!    R1# show access-lists ACL-VTY-SSH
!    EXPECTED OUTPUT:
!    Standard IP access list ACL-VTY-SSH
!        10 permit host 172.16.7.212 (2 matches)
!        20 permit host 172.16.8.75
!        30 deny any log
!
! 5. Verify OSPF Neighbor Adjacencies (Expect 3 Full Neighbors):
!    R1# show ip ospf neighbor
!    EXPECTED OUTPUT:
!    Neighbor ID     Pri   State           Dead Time   Address         Interface
!    172.16.8.105      0   FULL/  -        00:00:03    172.16.8.82     Serial0/0/0
!    172.16.8.106      0   FULL/  -        00:00:34    172.16.8.89     GigabitEthernet0/0
!    172.16.8.107      0   FULL/  -        00:00:36    172.16.8.93     GigabitEthernet0/1
!
! 6. Verify EIGRP Standby Neighbor Adjacency:
!    R1# show ip eigrp neighbors
!    EXPECTED OUTPUT:
!    H   Address          Interface       Hold  Uptime    SRTT   RTO   Q   Seq
!    0   172.16.8.86      Se0/0/1           12  00:10:45   24    200   0   14
!
! 7. Verify NAT Translations (Static Port-Forwarding & Dynamic PAT Overload):
!    R1# show ip nat translations
!    EXPECTED OUTPUT:
!    Pro Inside global         Inside local          Outside local         Outside global
!    tcp 172.16.8.102:80       172.16.7.4:80         ---                   ---
!    tcp 172.16.8.102:443      172.16.7.4:443        ---                   ---
!    tcp 172.16.8.102:51432    172.16.4.10:51432     203.0.113.80:80       203.0.113.80:80
!    tcp 172.16.8.102:52110    172.16.0.11:52110     203.0.113.80:443      203.0.113.80:443
!    icmp 172.16.8.102:1       172.16.4.10:1         8.8.8.8:1             8.8.8.8:1
!
! 8. Verify NAT Operational Statistics:
!    R1# show ip nat statistics
!    EXPECTED OUTPUT:
!    Total active translations: 5 (2 static, 3 dynamic; 3 extended)
!    Outside interfaces:
!      GigabitEthernet0/2
!    Inside interfaces:
!      GigabitEthernet0/0, GigabitEthernet0/1, Serial0/0/0, Serial0/0/1
!    Hits: 342  Misses: 2
!    CEF Translated packets: 344, CEF Punted packets: 0
!    Expired translations: 18
!    Dynamic mappings:
!    -- Inside Source
!    [Id: 1] access-list NAT-ACL interface GigabitEthernet0/2 ref count 3
!
! 9. Verify Egress QoS Policy & Queue Counters on Primary WAN (Serial0/0/0):
!    R1# show policy-map interface Serial0/0/0
!    EXPECTED OUTPUT:
!    Serial0/0/0 
!      Service-policy output: PM-WAN-EDGE-OUT
!        Class-map: CM-VITALS (match-any)
!          50 packets, 4200 bytes
!          5 minute offered rate 8000 bps, drop rate 0 BPS
!          Match: access-group name ACL-QOS-VITALS
!            50 packets, 4200 bytes
!          Queueing
!            Strict Priority
!            Output Queue: Conversation 264
!            Bandwidth 25 (%)
!            Bandwidth 512 (kbps) Burst 12800 (Bytes)
!            (pkts matched/bytes matched) 50/4200
!            (total drops/bytes drops) 0/0
!        Class-map: CM-VOICE (match-any)
!          0 packets, 0 bytes
!          5 minute offered rate 0 BPS, drop rate 0 BPS
!          Match: access-group name ACL-QOS-VOICE
!          Queueing
!            Output Queue: Conversation 265
!            Bandwidth 20 (%)
!            Bandwidth 409 (kbps) Max Threshold 64 (packets)
!            (total drops/bytes drops) 0/0
!        Class-map: CM-IMAGING (match-any)
!          100 packets, 142800 bytes
!          5 minute offered rate 1820000 bps, drop rate 45000 BPS
!          Match: access-group name ACL-QOS-IMAGING
!            100 packets, 142800 bytes
!          Queueing
!            Output Queue: Conversation 266
!            Bandwidth 15 (%)
!            Bandwidth 307 (kbps) Max Threshold 64 (packets)
!            (pkts matched/bytes matched) 100/142800
!            (total drops/bytes drops) 12/17136
!        Class-map: CM-ADMIN (match-any)
!          15 packets, 1260 bytes
!          5 minute offered rate 2000 bps, drop rate 0 BPS
!          Match: access-group name ACL-QOS-ADMIN
!          Queueing
!            Output Queue: Conversation 267
!            Bandwidth 15 (%)
!            Bandwidth 307 (kbps) Max Threshold 64 (packets)
!            (total drops/bytes drops) 0/0
!        Class-map: class-default (match-any)
!          18 packets, 1548 bytes
!          5 minute offered rate 2000 bps, drop rate 0 BPS
!          Match: any
!          Queueing
!            Flow Based Fair Queueing
!            Maximum Number of Hashed Queues 256
!            (total drops/bytes drops) 0/0
!
! 10. Verify Egress QoS Policy on Backup WAN (Serial0/0/1):
!    R1# show policy-map interface Serial0/0/1
!    EXPECTED OUTPUT:
!    Serial0/0/1 
!      Service-policy output: PM-WAN-EDGE-OUT
!        Class-map: CM-VITALS (match-any)
!          Bandwidth 25 (%)
!          Bandwidth 386 (kbps) Burst 9650 (Bytes)
!          (total drops/bytes drops) 0/0
!        Class-map: CM-VOICE (match-any)
!          Bandwidth 20 (%)
!          Bandwidth 308 (kbps) Max Threshold 64 (packets)
!        Class-map: CM-IMAGING (match-any)
!          Bandwidth 15 (%)
!          Bandwidth 231 (kbps) Max Threshold 64 (packets)
!        Class-map: CM-ADMIN (match-any)
!          Bandwidth 15 (%)
!          Bandwidth 231 (kbps) Max Threshold 64 (packets)
!        Class-map: class-default (match-any)
!          Flow Based Fair Queueing
! ==============================================================================

```

### Appendix 13.3: Device Configuration — R2

```ios
! ==============================================================================
! DEVICE:       R2
! HOSTNAME:     R2 (Remote Clinic - Core Router / ABR)
! MODEL:        Cisco 2911 Integrated Services Router
! MODULES:      HWIC-2T installed in Slot 0 (provides Serial0/0/0 & Serial0/0/1)
! WAN PRIMARY:  Serial0/0/0 (DTE) -> R1 Se0/0/0 [OSPF Area 0 Backbone, AD 110]
! WAN BACKUP:   Serial0/0/1 (DTE) -> R1 Se0/0/1 [EIGRP AS 100 Standby, AD adjusted to 120]
! LAN LINK:     GigabitEthernet0/0 -> SW-D3 Gi0/1 (172.16.8.96/30) [OSPF Area 1]
! ROLE:         OSPF Area Border Router (ABR) connecting Area 0 and Area 1
! SECURITY:     ACL-VTY-SSH (NOC & Local Admin SSH Isolation)
! LOOPBACK0:    172.16.8.105/32 (OSPF Router ID & Management)
! ==============================================================================

enable
configure terminal

hostname R2

! --- Disable DNS Lookup & Set Domain Name ---
no ip domain-lookup
ip domain-name hospital.local

! --- Security Warning & Legal Disclaimer Banner ---
banner motd ^C
================================================================================
  R2 : Remote Clinic Core Router (ABR) - VIT SCOPE CN Project
  UNAUTHORIZED ACCESS TO THIS NETWORK DEVICE IS STRICTLY PROHIBITED!
  All activities, keystrokes, and sessions are logged and monitored.
================================================================================
^C

! --- Management Authentication & Credential Encryption ---
enable secret class123
service password-encryption
username admin privilege 15 secret class123

! --- Cryptographic SSH Version 2 Configuration ---
crypto key generate rsa modulus 1024
ip ssh version 2
ip ssh time-out 60
ip ssh authentication-retries 3

! --- Infrastructure Hardening: Standard ACL for VTY Management ---
ip access-list standard ACL-VTY-SSH
 remark Permit Central Hospital NOC Management Console
 permit host 172.16.7.212
 remark Permit Remote Clinic Local Management Station
 permit host 172.16.8.75
 remark Deny all other administrative attempts with logging
 deny any log
exit

! --- Console Line Security ---
line con 0
 password cisco
 login
 logging synchronous
 exec-timeout 15 0
exit

! --- VTY Lines Security (SSH Only, Restricted Access-Class, Session Timeout) ---
line vty 0 4
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

line vty 5 15
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

! --- Disable Insecure / Unnecessary Management Services ---
no ip http server
no ip http secure-server
no ip source-route

! --- Centralized Time Synchronization (NTP Client) ---
ntp server 172.16.7.4

! --- Centralized Logging (Syslog Client) ---
logging host 172.16.7.4
logging trap informational
logging buffered 4096 informational

! --- Loopback0 Interface (OSPF Router ID) ---
interface Loopback0
 description OSPF_Router_ID_and_Management
 ip address 172.16.8.105 255.255.255.255
 no shutdown
exit

! --- LAN Point-to-Point Uplink to Remote Distribution Switch (SW-D3) ---
interface GigabitEthernet0/0
 description Link_to_SW-D3_Gi0/1_Area1
 ip address 172.16.8.98 255.255.255.252
 ip ospf network point-to-point
 no shutdown
exit

! --- Cryptographic Key-Chain for EIGRP Authentication ---
key chain EIGRP_AUTH
 key 1
  key-string CiscoHospital2026
exit

! --- Quality of Service (QoS): Extended ACLs for Traffic Classification ---
ip access-list extended ACL-QOS-VITALS
 remark Class C1: Remote Clinic Triage Station to Central Server
 permit udp host 172.16.8.44 host 172.16.7.4
 remark Class C1: ICU Bedside Sensors to Central Telemetry Server
 permit udp 172.16.7.128 0.0.0.63 host 172.16.7.4
 remark Class C1: Surgical Theatres to Central Telemetry Server
 permit udp 172.16.7.64 0.0.0.63 host 172.16.7.4
 remark Class C1: Server Return Telemetry Traffic & Sync
 permit udp host 172.16.7.4 host 172.16.8.44
 permit udp host 172.16.7.4 172.16.7.128 0.0.0.63
 permit udp host 172.16.7.4 172.16.7.64 0.0.0.63
exit

ip access-list extended ACL-QOS-VOICE
 remark Class C2: Clinic Voice Subnet to Main Voice Subnet RTP
 permit udp 172.16.7.224 0.0.0.31 172.16.6.0 0.0.0.127
 permit udp 172.16.6.0 0.0.0.127 172.16.7.224 0.0.0.31
 remark Class C2: Dynamic RTP Bearer Audio Streams
 permit udp any any range 16384 32767
 remark Class C2: Session Initiation Protocol (SIP) Signaling
 permit udp any any eq 5060
 permit tcp any any eq 5060
 remark Class C2: Skinny Call Control Protocol (SCCP) Signaling
 permit tcp any any eq 2000
exit

ip access-list extended ACL-QOS-IMAGING
 remark Class C3: DICOM Medical Image Transfers to PACS Server
 permit tcp any host 172.16.7.7 eq 104
 permit tcp host 172.16.7.7 any eq 104
 remark Class C3: PACS Web Viewer & Image Retrieval
 permit tcp any host 172.16.7.7 eq 8080
 permit tcp any host 172.16.7.7 eq 8443
 remark Class C3: Clinic Cache Bulk Replication (FTP/TFTP Imaging Transfers)
 permit tcp host 172.16.8.36 host 172.16.7.7
 permit tcp host 172.16.7.7 host 172.16.8.36
exit

ip access-list extended ACL-QOS-ADMIN
 remark Class C4: Electronic Health Record Web Portal Access
 permit tcp 172.16.8.0 0.0.0.31 host 172.16.7.4 eq www
 permit tcp 172.16.8.0 0.0.0.31 host 172.16.7.4 eq 443
 permit tcp 172.16.4.0 0.0.1.255 host 172.16.7.4 eq www
 permit tcp 172.16.4.0 0.0.1.255 host 172.16.7.4 eq 443
 remark Class C4: Internal Core DNS Resolver Queries
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Class C4: Secure Shell Out-of-Band Network Management
 permit tcp 172.16.8.64 0.0.0.15 any eq 22
 permit tcp 172.16.7.192 0.0.0.31 any eq 22
exit

! --- Quality of Service (QoS): MQC Class-Maps ---
class-map match-any CM-VITALS
 description Life_Critical_Bedside_ICU_Surgical_Telemetry
 match access-group name ACL-QOS-VITALS
 match ip dscp ef
exit

class-map match-any CM-VOICE
 description VoIP_Bearer_Audio_and_PBX_Signaling
 match access-group name ACL-QOS-VOICE
 match ip dscp cs5
 match ip dscp ef
 match ip dscp cs3
exit

class-map match-any CM-IMAGING
 description PACS_DICOM_Radiological_Image_Transfers
 match access-group name ACL-QOS-IMAGING
 match ip dscp af31
exit

class-map match-any CM-ADMIN
 description Administrative_EHR_Portal_and_Core_Services
 match access-group name ACL-QOS-ADMIN
 match ip dscp af21
 match ip dscp cs2
exit

! --- Quality of Service (QoS): MQC Policy-Map Definition ---
policy-map PM-WAN-EDGE-OUT
 description Disaster_Resilient_Hospital_WAN_QoS_Policy
 class CM-VITALS
  priority percent 25
 class CM-VOICE
  bandwidth percent 20
 class CM-IMAGING
  bandwidth percent 15
 class CM-ADMIN
  bandwidth percent 15
 class class-default
  fair-queue
exit

! --- Primary WAN Link (Serial0/0/0 - DTE): OSPF Area 0 Backbone ---
interface Serial0/0/0
 description Primary_WAN_Link_to_R1_Se0/0/0_OSPF_Area0
 ip address 172.16.8.82 255.255.255.252
 bandwidth 2048
 ip ospf network point-to-point
 ip ospf cost 48
 ip ospf hello-interval 1
 ip ospf dead-interval 4
 ip ospf authentication message-digest
 ip ospf message-digest-key 1 md5 CiscoHospital2026
 service-policy output PM-WAN-EDGE-OUT
 no shutdown
exit

! --- Secondary WAN Link (Serial0/0/1 - DTE): Standby EIGRP AS 100 ---
interface Serial0/0/1
 description Standby_WAN_Link_to_R1_Se0/0/1_EIGRP_Backup
 ip address 172.16.8.86 255.255.255.252
 bandwidth 1544
 ip authentication mode eigrp 100 md5
 ip authentication key-chain eigrp 100 EIGRP_AUTH
 service-policy output PM-WAN-EDGE-OUT
 no shutdown
exit

! --- Dynamic Routing: Multi-Area OSPF Process 1 (ABR Role) ---
router ospf 1
 router-id 172.16.8.105
 ! Security: Passive-interface default prevents rogue adjacencies
 passive-interface default
 no passive-interface GigabitEthernet0/0
 no passive-interface Serial0/0/0
 no passive-interface Loopback0
 ! Inter-Area Route Summarization (Area 1 -> Area 0)
 ! Condenses 6 individual clinic subnets into 3 summary LSAs (50% LSDB reduction)
 area 1 range 172.16.8.0 255.255.255.0       ! Summarizes Admin, Clinical, Mgmt, and Transit
 area 1 range 172.16.6.128 255.255.255.128   ! Summarizes Clinic Guest Wi-Fi
 area 1 range 172.16.7.224 255.255.255.224   ! Summarizes Clinic VoIP Voice
 ! Area 0: WAN Primary Serial Link & Loopback0
 network 172.16.8.105 0.0.0.0 area 0       ! Loopback0 in Area 0
 network 172.16.8.80 0.0.0.3 area 0         ! Primary Serial Se0/0/0 in Area 0
 ! Area 1: Remote Clinic Campus Network
 network 172.16.8.96 0.0.0.3 area 1         ! Link to SW-D3 in Area 1
exit

! --- Dynamic Routing: EIGRP AS 100 (Secondary Standby Path) ---
! CRITICAL: Default EIGRP AD is 90, which beats OSPF (110).
! By raising EIGRP internal AD to 120, OSPF is ALWAYS preferred when primary WAN is UP.
router eigrp 100
 no auto-summary
 network 172.16.8.84 0.0.0.3                ! Secondary Serial Se0/0/1
 network 172.16.8.96 0.0.0.3                ! Link to SW-D3
 network 172.16.8.0 0.0.0.255               ! Clinic subnets
 network 172.16.6.128 0.0.0.127             ! Clinic Guest Wi-Fi
 network 172.16.7.224 0.0.0.31              ! Clinic Voice
 distance eigrp 120 170
 passive-interface default
 no passive-interface Serial0/0/1
exit

! --- Quality of Service (QoS): Modular QoS CLI (MQC) ---
class-map match-any VITALS-VOICE
 match ip dscp ef
exit

class-map match-any IMAGING
 match ip dscp af31
exit

policy-map HOSPITAL-QOS
 class VITALS-VOICE
  priority percent 30
 class IMAGING
  bandwidth percent 40
 class class-default
  fair-queue
exit

! Apply QoS policy egress on WAN links
interface Serial0/0/0
 service-policy output HOSPITAL-QOS
exit

interface Serial0/0/1
 service-policy output HOSPITAL-QOS
exit

end
write memory

! ==============================================================================
! VERIFICATION COMMANDS & EXPECTED OUTPUT
! ==============================================================================
!
! 1. Clear Access-List Counters Before Testing:
!    R2# clear access-list counters
!    Clear "access-list counters" to [confirm]
!
! 2. Verify VTY SSH Management Access-Class:
!    R2# show access-lists ACL-VTY-SSH
!    EXPECTED OUTPUT:
!    Standard IP access list ACL-VTY-SSH
!        10 permit host 172.16.7.212 (2 matches)
!        20 permit host 172.16.8.75
!        30 deny any log
!
! 3. Verify OSPF ABR Operation:
!    R2# show ip ospf
!    EXPECTED OUTPUT:
!    It is an area border router
!    Number of areas in this router is 2 (Area 0, Area 1)
!
! 4. Verify OSPF Neighbors on Both Sides:
!    R2# show ip ospf neighbor
!    EXPECTED OUTPUT:
!    Neighbor ID     Pri   State           Dead Time   Address         Interface
!    172.16.8.104      0   FULL/  -        00:00:03    172.16.8.81     Serial0/0/0 (Area 0 to R1)
!    172.16.8.108      0   FULL/  -        00:00:35    172.16.8.97     GigabitEthernet0/0 (Area 1 to SW-D3)
!
! 5. Verify Standby EIGRP Neighbor:
!    R2# show ip eigrp neighbors
!    EXPECTED OUTPUT:
!    H   Address          Interface       Hold  Uptime    SRTT   RTO   Q   Seq
!    0   172.16.8.85      Se0/0/1           13  00:10:48   25    200   0   15
!
! 6. Verify Active Routes to Main Hospital (Normal State - Primary Link UP):
!    R2# show ip route
!    EXPECTED OUTPUT:
!    Gateway of last resort is 172.16.8.81 to network 0.0.0.0
!    O*E2 0.0.0.0/0 [110/20] via 172.16.8.81, Serial0/0/0
!
! 7. Test Failover Reconvergence (Simulating Primary WAN Link Failure):
!    R2(config)# interface Serial0/0/0
!    R2(config-if)# shutdown
!    R2# show ip route
!    EXPECTED OUTPUT:
!    D    172.16.0.0/16 [120/2172416] via 172.16.8.85, Serial0/0/1
!
! 8. Restore Primary Link:
!    R2(config)# interface Serial0/0/0
!    R2(config-if)# no shutdown
!    R2# show ip route
!    EXPECTED OUTPUT:
!    O    172.16.7.0/26 [110/50] via 172.16.8.81, Serial0/0/0
!
! 9. Verify Egress QoS Policy & Queue Counters on Primary WAN (Serial0/0/0):
!    R2# show policy-map interface Serial0/0/0
!    EXPECTED OUTPUT:
!    Serial0/0/0 
!      Service-policy output: PM-WAN-EDGE-OUT
!        Class-map: CM-VITALS (match-any)
!          50 packets, 4200 bytes
!          5 minute offered rate 8000 bps, drop rate 0 BPS
!          Match: access-group name ACL-QOS-VITALS
!            50 packets, 4200 bytes
!          Queueing
!            Strict Priority
!            Output Queue: Conversation 264
!            Bandwidth 25 (%)
!            Bandwidth 512 (kbps) Burst 12800 (Bytes)
!            (pkts matched/bytes matched) 50/4200
!            (total drops/bytes drops) 0/0
!        Class-map: CM-VOICE (match-any)
!          0 packets, 0 bytes
!          5 minute offered rate 0 BPS, drop rate 0 BPS
!          Match: access-group name ACL-QOS-VOICE
!          Queueing
!            Output Queue: Conversation 265
!            Bandwidth 20 (%)
!            Bandwidth 409 (kbps) Max Threshold 64 (packets)
!            (total drops/bytes drops) 0/0
!        Class-map: CM-IMAGING (match-any)
!          100 packets, 142800 bytes
!          5 minute offered rate 1820000 bps, drop rate 45000 BPS
!          Match: access-group name ACL-QOS-IMAGING
!            100 packets, 142800 bytes
!          Queueing
!            Output Queue: Conversation 266
!            Bandwidth 15 (%)
!            Bandwidth 307 (kbps) Max Threshold 64 (packets)
!            (pkts matched/bytes matched) 100/142800
!            (total drops/bytes drops) 12/17136
!        Class-map: CM-ADMIN (match-any)
!          15 packets, 1260 bytes
!          5 minute offered rate 2000 bps, drop rate 0 BPS
!          Match: access-group name ACL-QOS-ADMIN
!          Queueing
!            Output Queue: Conversation 267
!            Bandwidth 15 (%)
!            Bandwidth 307 (kbps) Max Threshold 64 (packets)
!            (total drops/bytes drops) 0/0
!        Class-map: class-default (match-any)
!          18 packets, 1548 bytes
!          5 minute offered rate 2000 bps, drop rate 0 BPS
!          Match: any
!          Queueing
!            Flow Based Fair Queueing
!            Maximum Number of Hashed Queues 256
!            (total drops/bytes drops) 0/0
!
! 10. Verify Egress QoS Policy on Backup WAN (Serial0/0/1):
!    R2# show policy-map interface Serial0/0/1
!    EXPECTED OUTPUT:
!    Serial0/0/1 
!      Service-policy output: PM-WAN-EDGE-OUT
!        Class-map: CM-VITALS (match-any)
!          Bandwidth 25 (%)
!          Bandwidth 386 (kbps) Burst 9650 (Bytes)
!          (total drops/bytes drops) 0/0
!        Class-map: CM-VOICE (match-any)
!          Bandwidth 20 (%)
!          Bandwidth 308 (kbps) Max Threshold 64 (packets)
!        Class-map: CM-IMAGING (match-any)
!          Bandwidth 15 (%)
!          Bandwidth 231 (kbps) Max Threshold 64 (packets)
!        Class-map: CM-ADMIN (match-any)
!          Bandwidth 15 (%)
!          Bandwidth 231 (kbps) Max Threshold 64 (packets)
!        Class-map: class-default (match-any)
!          Flow Based Fair Queueing
! ==============================================================================

```

### Appendix 13.4: Device Configuration — SW-D1

```ios
! ==============================================================================
! DEVICE:       SW-D1
! MODEL:        Cisco Catalyst 3560-24PS (Multilayer Layer-3 Switch)
! LOCATION:     Main Hospital Campus - Distribution Rack A
! ROLE:         Distribution Aggregator / Active Gateway Group 1 / Primary STP Root
! UPLINK:       GigabitEthernet0/2 -> Core Router R1 GigabitEthernet0/0 (/30 Routed)
! CROSS-CONNECT:FastEthernet0/23 - 24 -> SW-D2 (EtherChannel Port-Channel 1)
! DOWNLINKS:    Fa0/1 (SW-A1), Fa0/2 (SW-A2), Fa0/3 (SW-A3), Fa0/4 (SW-A4)
! SERVERS:      Fa0/10 (SRV-CENTRAL), Fa0/11 (SRV-PACS)
! ==============================================================================

enable
configure terminal

! --- Device Identity & System Security ---
hostname SW-D1
no ip domain-lookup
ip domain-name hospital.local

banner motd ^C
================================================================================
  SW-D1 : Main Hospital Multilayer Distribution Switch 1
  VIT Vellore - CN Project: Disaster-Resilient Smart Hospital Network
  UNAUTHORIZED ACCESS IS STRICTLY PROHIBITED. ALL SESSIONS MONITORED.
================================================================================
^C

! --- Management Authentication & Credential Encryption ---
enable secret class123
service password-encryption
username admin privilege 15 secret class123

! --- Cryptographic SSH Version 2 Configuration ---
crypto key generate rsa modulus 1024
ip ssh version 2
ip ssh time-out 60
ip ssh authentication-retries 3

! --- Infrastructure Hardening: Standard ACL for VTY Management ---
ip access-list standard ACL-VTY-SSH
 remark Permit Central Hospital NOC Management Console
 permit host 172.16.7.212
 remark Permit Remote Clinic Local Management Station
 permit host 172.16.8.75
 remark Deny all other administrative attempts with logging
 deny any log
exit

line con 0
 password cisco
 login
 logging synchronous
 exec-timeout 15 0
exit

line vty 0 4
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

line vty 5 15
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

! --- Disable Insecure / Unnecessary Management Services ---
no ip http server
no ip http secure-server

! --- Centralized Time Synchronization (NTP Client) ---
ntp server 172.16.7.4

! --- Centralized Logging (Syslog Client) ---
logging host 172.16.7.4
logging trap informational
logging buffered 4096 informational

! --- Enable Hardware Layer-3 IP Routing & Global Quality of Service ---
ip routing
mls qos

! --- VLAN Database Definition ---
vlan 10
 name ICU_Clinical
vlan 20
 name Surgery_Theatre
vlan 30
 name Administration
vlan 40
 name Guest_WiFi
vlan 50
 name Server_Farm
vlan 60
 name VoIP_Voice
vlan 99
 name Management
vlan 999
 name Parking_Native
exit

! --- Spanning Tree Protocol: Rapid PVST+ Configuration ---
! Rapid PVST+ (IEEE 802.1w) delivers sub-second convergence vs 30-50s legacy PVST.
! SW-D1 is Root Primary for Odd Tens / Group 1 (VLANs 10, 30, 50, 99)
! SW-D1 is Root Secondary for Even Tens / Group 2 (VLANs 20, 40, 60)
spanning-tree mode rapid-pvst
spanning-tree vlan 10,30,50,99 root primary
spanning-tree vlan 20,40,60 root secondary

! --- Inter-Distribution EtherChannel (Port-Channel 1 to SW-D2) ---
! Bundles Fa0/23 and Fa0/24 into an aggregate 200 Mbps full-duplex cross-link.
! Uses 'channel-group 1 mode on' for deterministic Packet Tracer 8.x stability.
interface range FastEthernet0/23 - 24
 description Inter_Distribution_EtherChannel_Member_to_SW-D2
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,20,30,40,50,60,99
 switchport nonegotiate
 channel-group 1 mode on
 no shutdown
exit

interface Port-channel 1
 description Aggregate_Trunk_CrossLink_to_SW-D2
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,20,30,40,50,60,99
 switchport nonegotiate
 mls qos trust dscp
 no shutdown
exit

! --- 802.1Q Distribution-to-Access Trunk Downlinks ---
! DTP disabled (switchport nonegotiate) and allowed VLANs restricted per switch

! Trunk to SW-A1 (ICU Floor: VLANs 10, 60, 99)
interface FastEthernet0/1
 description Primary_Trunk_Downlink_to_SW-A1_Gig0/1
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,60,99
 switchport nonegotiate
 no shutdown
exit

! Trunk to SW-A2 (Surgery Floor: VLANs 20, 60, 99)
interface FastEthernet0/2
 description Primary_Trunk_Downlink_to_SW-A2_Gig0/1
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 20,60,99
 switchport nonegotiate
 no shutdown
exit

! Trunk to SW-A3 (Admin Floor: VLANs 30, 60, 99 - Secondary Standby)
interface FastEthernet0/3
 description Secondary_Trunk_Downlink_to_SW-A3_Gig0/2
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 30,60,99
 switchport nonegotiate
 no shutdown
exit

! Trunk to SW-A4 (Guest Wi-Fi: VLANs 40, 99 - Secondary Standby)
interface FastEthernet0/4
 description Secondary_Trunk_Downlink_to_SW-A4_Gig0/2
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 40,99
 switchport nonegotiate
 switchport block unicast
 no shutdown
exit

! --- Dedicated Server Farm Access Ports (VLAN 50) ---
! Edge ports with PortFast enabled for instant link transitions
interface FastEthernet0/10
 description Server_Farm_Central_Hospital_Server_(DNS_DHCP_Web)
 switchport mode access
 switchport access vlan 50
 spanning-tree portfast
 spanning-tree bpduguard enable
 no shutdown
exit

interface FastEthernet0/11
 description Server_Farm_PACS_Imaging_Archive_Server
 switchport mode access
 switchport access vlan 50
 spanning-tree portfast
 spanning-tree bpduguard enable
 no shutdown
exit

! --- Layer 3 Routed Uplink to Core Router R1 (/30 Transit Subnet) ---
interface GigabitEthernet0/2
 description Routed_Point_to_Point_Uplink_to_R1_Gig0/0
 no switchport
 ip address 172.16.8.89 255.255.255.252
 ip ospf network point-to-point
 mls qos trust dscp
 no shutdown
exit

! --- Loopback 0 Management & OSPF Router-ID ---
interface Loopback0
 description OSPF_Router_ID_and_Management
 ip address 172.16.8.106 255.255.255.255
 no shutdown
exit

! ==============================================================================
! ACCESS CONTROL LISTS (ACLS) & ZERO-TRUST MICROSEGMENTATION
! ==============================================================================

! --- VLAN 10 Inbound ACL: ICU Clinical Wards ---
ip access-list extended ACL-ICU-IN
 remark Permit client DHCP requests to relay agent
 permit udp any any eq bootps
 remark Permit DNS resolution to Central Server
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Permit HTTP and HTTPS to Central Hospital EHR Portal
 permit tcp any host 172.16.7.4 eq www
 permit tcp any host 172.16.7.4 eq 443
 remark Permit DICOM and PACS web viewer to PACS Archive Server
 permit tcp any host 172.16.7.7 eq 104
 permit tcp any host 172.16.7.7 eq www
 permit tcp any host 172.16.7.7 eq 443
 remark Permit DR database replication to Backup Server
 permit tcp any host 172.16.7.8 eq 443
 remark Permit access to Remote Clinic local EHR cache
 permit tcp any host 172.16.8.36 eq www
 permit tcp any host 172.16.8.36 eq 443
 remark Permit established TCP return traffic
 permit tcp any any established
 remark Permit ICMP diagnostic echo and echo-reply
 permit icmp any any echo
 permit icmp any any echo-reply
 remark Explicitly deny and log lateral access to Admin VLAN 30
 deny ip any 172.16.4.0 0.0.1.255 log
 remark Explicitly deny and log lateral access to Guest VLAN 40
 deny ip any 172.16.0.0 0.0.3.255 log
 remark Implicit deny all other traffic
 deny ip any any log
exit

! --- VLAN 20 Inbound ACL: Surgery Operating Theatres ---
ip access-list extended ACL-SURGERY-IN
 remark Permit client DHCP requests to relay agent
 permit udp any any eq bootps
 remark Permit DNS resolution to Central Server
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Permit HTTP and HTTPS to Central Hospital EHR Portal
 permit tcp any host 172.16.7.4 eq www
 permit tcp any host 172.16.7.4 eq 443
 remark Permit DICOM image stream to PACS Archive Server
 permit tcp any host 172.16.7.7 eq 104
 permit tcp any host 172.16.7.7 eq www
 permit tcp any host 172.16.7.7 eq 443
 remark Permit established TCP return traffic
 permit tcp any any established
 remark Permit ICMP diagnostic echo and echo-reply
 permit icmp any any echo
 permit icmp any any echo-reply
 remark Explicitly deny and log lateral access to Admin VLAN 30
 deny ip any 172.16.4.0 0.0.1.255 log
 remark Explicitly deny and log lateral access to Guest VLAN 40
 deny ip any 172.16.0.0 0.0.3.255 log
 remark Implicit deny all other traffic
 deny ip any any log
exit

! --- VLAN 30 Inbound ACL: Hospital Administration ---
ip access-list extended ACL-ADMIN-IN
 remark Permit client DHCP requests to relay agent
 permit udp any any eq bootps
 remark Permit DNS resolution to Central Server
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Permit HTTP and HTTPS to Central Hospital EHR Portal
 permit tcp any host 172.16.7.4 eq www
 permit tcp any host 172.16.7.4 eq 443
 remark Permit PACS administrative portal access
 permit tcp any host 172.16.7.7 eq www
 permit tcp any host 172.16.7.7 eq 443
 remark Permit TFTP backup transfer to Backup Server
 permit udp any host 172.16.7.8 eq tftp
 remark Permit outbound Internet web traffic (HTTP/HTTPS)
 permit tcp any any eq www
 permit tcp any any eq 443
 remark Permit established TCP return traffic
 permit tcp any any established
 remark Permit ICMP diagnostic echo and echo-reply
 permit icmp any any echo
 permit icmp any any echo-reply
 remark Explicitly deny and log access to acute ICU VLAN 10
 deny ip any 172.16.7.128 0.0.0.63 log
 remark Explicitly deny and log access to Surgery VLAN 20
 deny ip any 172.16.7.64 0.0.0.63 log
 remark Explicitly deny and log access to Guest VLAN 40
 deny ip any 172.16.0.0 0.0.3.255 log
 remark Implicit deny all other traffic
 deny ip any any log
exit

! --- VLAN 40 Inbound ACL: Hospital Guest Wi-Fi ---
ip access-list extended ACL-GUEST-IN
 remark Permit DHCP discovery broadcast and relay
 permit udp any any eq bootps
 remark Permit DNS resolution exclusively to Central DNS Server
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Explicitly deny and log any attempt to reach internal hospital networks
 deny ip any 172.16.0.0 0.0.255.255 log
 remark Permit outbound Internet web browsing (HTTP/HTTPS)
 permit tcp any any eq www
 permit tcp any any eq 443
 remark Permit external ICMP echo requests for connectivity checks
 permit icmp any any echo
 remark Permit established TCP return traffic
 permit tcp any any established
 remark Implicit deny all other unauthorized guest traffic
 deny ip any any log
exit

! --- VLAN 50 Inbound ACL: Central Server Farm ---
ip access-list extended ACL-SERVER-IN
 remark Permit DNS server outbound root queries
 permit udp host 172.16.7.4 any eq domain
 permit tcp host 172.16.7.4 any eq domain
 remark Permit DHCP server response offers and acknowledgments
 permit udp host 172.16.7.4 any eq bootpc
 remark Permit PACS archive replication to Remote Clinic Cache
 permit tcp host 172.16.7.7 host 172.16.8.36 eq 443
 remark Permit database synchronization to Backup Server
 permit tcp host 172.16.7.4 host 172.16.7.8 eq 443
 remark Permit established TCP return traffic to all hospital zones
 permit tcp any any established
 remark Permit ICMP diagnostic echo-reply and echo
 permit icmp any any echo-reply
 permit icmp any any echo
 remark Implicit deny unsolicited outbound connections from servers
 deny ip any any log
exit

! --- VLAN 60 Inbound ACL: VoIP Telephony ---
ip access-list extended ACL-VOICE-IN
 remark Permit DHCP requests with Option 150
 permit udp any any eq bootps
 remark Permit DNS queries for PBX hostname resolution
 permit udp any host 172.16.7.4 eq domain
 remark Permit TFTP firmware and config downloads from Central Server
 permit udp any host 172.16.7.4 eq tftp
 remark Permit SIP signaling between phones and call manager
 permit udp any any eq 5060
 permit tcp any any eq 5060
 remark Permit RTP voice media streams (UDP port range 16384-32767)
 permit udp any any range 16384 32767
 remark Permit ICMP echo for phone health checks
 permit icmp any any echo
 remark Explicitly deny and log any voice packet targeting data VLANs
 deny ip any 172.16.4.0 0.0.1.255 log
 deny ip any 172.16.0.0 0.0.3.255 log
 remark Implicit deny all other voice traffic
 deny ip any any log
exit

! --- VLAN 99 Inbound ACL: Out-of-Band Management ---
ip access-list extended ACL-MGMT-IN
 remark Permit NOC administrator console full access
 permit ip host 172.16.7.212 any
 remark Permit Remote Clinic admin station access
 permit ip host 172.16.8.75 any
 remark Permit established TCP return management traffic
 permit tcp any any established
 remark Permit ICMP echo and echo-reply
 permit icmp any any echo
 permit icmp any any echo-reply
 remark Explicitly deny and log all unapproved management access
 deny ip any any log
exit

! --- Quality of Service (QoS): Ingress Classification ACLs (SW-D1) ---
ip access-list extended ACL-MARK-VITALS
 remark Class C1: Ingress ICU and Surgical Telemetry Streams
 permit udp 172.16.7.128 0.0.0.63 host 172.16.7.4
 permit udp 172.16.7.64 0.0.0.63 host 172.16.7.4
 permit udp host 172.16.7.4 172.16.7.128 0.0.0.63
 permit udp host 172.16.7.4 172.16.7.64 0.0.0.63
exit

ip access-list extended ACL-MARK-IMAGING
 remark Class C3: Ingress DICOM and PACS Medical Imaging
 permit tcp any host 172.16.7.7 eq 104
 permit tcp host 172.16.7.7 any eq 104
 permit tcp any host 172.16.7.7 eq 8080
 permit tcp any host 172.16.7.7 eq 8443
exit

ip access-list extended ACL-MARK-ADMIN
 remark Class C4: Administrative EHR Queries & DNS
 permit tcp any host 172.16.7.4 eq www
 permit tcp any host 172.16.7.4 eq 443
 permit udp any host 172.16.7.4 eq domain
exit

! --- Quality of Service (QoS): MQC Ingress Class-Maps ---
class-map match-any CM-DISTRO-VITALS
 match access-group name ACL-MARK-VITALS
exit

class-map match-any CM-DISTRO-IMAGING
 match access-group name ACL-MARK-IMAGING
exit

class-map match-any CM-DISTRO-ADMIN
 match access-group name ACL-MARK-ADMIN
exit

! --- Quality of Service (QoS): MQC Ingress Marking Policy-Map ---
policy-map PM-DISTRO-MARK-INGRESS
 class CM-DISTRO-VITALS
  set dscp ef
 class CM-DISTRO-IMAGING
  set dscp af31
 class CM-DISTRO-ADMIN
  set dscp af21
 class class-default
  set dscp default
exit

! --- Inter-VLAN Routing: Switch Virtual Interfaces (SVIs) & HSRP v2 ---
! Group 1 (Odd VLANs: 10, 30, 50, 99): SW-D1 is ACTIVE (Priority 110, Preempt, Track Gi0/2 decr 20)
! Group 2 (Even VLANs: 20, 40, 60): SW-D1 is STANDBY (Priority 100, Preempt)
! DHCP Relay: ip helper-address points to Central DHCP Server SRV-CENTRAL (172.16.7.4)

! VLAN 10 : ICU Clinical Wards (Subnet: 172.16.7.128/26, VIP: .129, SVI: .130 - ACTIVE)
interface Vlan10
 description SVI_ICU_Clinical_Gateway
 ip address 172.16.7.130 255.255.255.192
 ip access-group ACL-ICU-IN in
 ip helper-address 172.16.7.4
 service-policy input PM-DISTRO-MARK-INGRESS
 standby version 2
 standby 10 ip 172.16.7.129
 standby 10 priority 110
 standby 10 preempt
 standby 10 track GigabitEthernet0/2 20
 no shutdown
exit

! VLAN 20 : Surgery Operating Theatres (Subnet: 172.16.7.64/26, VIP: .65, SVI: .66 - STANDBY)
interface Vlan20
 description SVI_Surgery_Theatre_Gateway
 ip address 172.16.7.66 255.255.255.192
 ip access-group ACL-SURGERY-IN in
 ip helper-address 172.16.7.4
 service-policy input PM-DISTRO-MARK-INGRESS
 standby version 2
 standby 20 ip 172.16.7.65
 standby 20 priority 100
 standby 20 preempt
 no shutdown
exit

! VLAN 30 : Hospital Administration (Subnet: 172.16.4.0/23, VIP: .1, SVI: .2 - ACTIVE)
interface Vlan30
 description SVI_Administration_Gateway
 ip address 172.16.4.2 255.255.254.0
 ip access-group ACL-ADMIN-IN in
 ip helper-address 172.16.7.4
 standby version 2
 standby 30 ip 172.16.4.1
 standby 30 priority 110
 standby 30 preempt
 standby 30 track GigabitEthernet0/2 20
 no shutdown
exit

! VLAN 40 : Hospital Guest Wi-Fi (Subnet: 172.16.0.0/22, VIP: .1, SVI: .2 - STANDBY)
interface Vlan40
 description SVI_Guest_WiFi_Gateway
 ip address 172.16.0.2 255.255.252.0
 ip access-group ACL-GUEST-IN in
 ip helper-address 172.16.7.4
 standby version 2
 standby 40 ip 172.16.0.1
 standby 40 priority 100
 standby 40 preempt
 no shutdown
exit

! VLAN 50 : Central Server Farm (Subnet: 172.16.7.0/26, VIP: .1, SVI: .2 - ACTIVE)
interface Vlan50
 description SVI_Server_Farm_Gateway
 ip address 172.16.7.2 255.255.255.192
 ip access-group ACL-SERVER-IN in
 service-policy input PM-DISTRO-MARK-INGRESS
 standby version 2
 standby 50 ip 172.16.7.1
 standby 50 priority 110
 standby 50 preempt
 standby 50 track GigabitEthernet0/2 20
 no shutdown
exit

! VLAN 60 : VoIP Telephony (Subnet: 172.16.6.0/25, VIP: .1, SVI: .2 - STANDBY)
interface Vlan60
 description SVI_VoIP_Voice_Gateway
 ip address 172.16.6.2 255.255.255.128
 ip access-group ACL-VOICE-IN in
 ip helper-address 172.16.7.4
 standby version 2
 standby 60 ip 172.16.6.1
 standby 60 priority 100
 standby 60 preempt
 no shutdown
exit

! VLAN 99 : Out-of-Band Management (Subnet: 172.16.7.192/27, VIP: .193, SVI: .194 - ACTIVE)
interface Vlan99
 description In_Band_Management_SVI_SW-D1
 ip address 172.16.7.194 255.255.255.224
 ip access-group ACL-MGMT-IN in
 standby version 2
 standby 99 ip 172.16.7.193
 standby 99 priority 110
 standby 99 preempt
 standby 99 track GigabitEthernet0/2 20
 no shutdown
exit

! --- Dynamic Routing: Multi-Area OSPF Process 1 (Area 0 Backbone) ---
router ospf 1
 router-id 172.16.8.106
 ! Security: Passive-interface default suppresses OSPF hellos on client host VLANs
 passive-interface default
 no passive-interface GigabitEthernet0/2
 no passive-interface Loopback0
 ! Core Backbone Area 0 Advertisements
 network 172.16.8.106 0.0.0.0 area 0       ! Loopback0
 network 172.16.8.88 0.0.0.3 area 0         ! Routed link to R1 (Gi0/2)
 network 172.16.7.128 0.0.0.63 area 0       ! VLAN 10 ICU Clinical
 network 172.16.7.64 0.0.0.63 area 0        ! VLAN 20 Surgery Theatres
 network 172.16.4.0 0.0.1.255 area 0        ! VLAN 30 Hospital Admin
 network 172.16.0.0 0.0.3.255 area 0        ! VLAN 40 Guest Wi-Fi
 network 172.16.7.0 0.0.0.63 area 0         ! VLAN 50 Central Server Farm
 network 172.16.6.0 0.0.0.127 area 0        ! VLAN 60 VoIP Telephony
 network 172.16.7.192 0.0.0.31 area 0       ! VLAN 99 Management
exit

! --- Floating Static Default Route to Core Router R1 (AD 200 Backup) ---
! Primary default route is dynamically learned from R1 via OSPF (Type-5 AS-External, AD 110).
! This floating static route activates only in the event of total dynamic routing failure.
ip route 0.0.0.0 0.0.0.0 172.16.8.90 200

! --- Security: Shutdown & Park All Unused Physical Interfaces in VLAN 999 ---
interface range FastEthernet0/5 - 9, FastEthernet0/12 - 22, GigabitEthernet0/1
 description Security_Unused_Port_Parked_in_VLAN999
 switchport mode access
 switchport access vlan 999
 shutdown
exit

end
write memory

! ==============================================================================
! VERIFICATION COMMANDS & EXPECTED OUTPUT (Cisco Packet Tracer 8.x)
! ==============================================================================
!
! 1. show vlan brief
! ------------------------------------------------------------------------------
! SW-D1# show vlan brief
! VLAN Name                             Status    Ports
! ---- -------------------------------- --------- -------------------------------
! 1    default                          active    
! 10   ICU_Clinical                     active    
! 20   Surgery_Theatre                  active    
! 30   Administration                   active    
! 40   Guest_WiFi                       active    
! 50   Server_Farm                      active    Fa0/10, Fa0/11
! 60   VoIP_Voice                       active    
! 99   Management                       active    
! 999  Parking_Native                   active    Fa0/5, Fa0/6, Fa0/7, Fa0/8, Fa0/9,
!                                                 Fa0/12, Fa0/13, Fa0/14, Fa0/15,
!                                                 Fa0/16, Fa0/17, Fa0/18, Fa0/19,
!                                                 Fa0/20, Fa0/21, Fa0/22, Gi0/1
!
! 2. show interfaces trunk
! ------------------------------------------------------------------------------
! SW-D1# show interfaces trunk
! Port        Mode         Encapsulation  Status        Native vlan
! Fa0/1       on           802.1q         trunking      999
! Fa0/2       on           802.1q         trunking      999
! Fa0/3       on           802.1q         trunking      999
! Fa0/4       on           802.1q         trunking      999
! Po1         on           802.1q         trunking      999
!
! Port        Vlans allowed on trunk
! Fa0/1       10,60,99
! Fa0/2       20,60,99
! Fa0/3       30,60,99
! Fa0/4       40,99
! Po1         10,20,30,40,50,60,99
!
! 3. show spanning-tree summary
! ------------------------------------------------------------------------------
! SW-D1# show spanning-tree summary
! Switch is in rapid-pvst mode
! Root bridge for: VLAN0010, VLAN0030, VLAN0050, VLAN0099
! Extended system ID is enabled
!
! 4. show etherchannel summary
! ------------------------------------------------------------------------------
! SW-D1# show etherchannel summary
! Group  Port-channel  Protocol    Ports
! ------+-------------+-----------+-----------------------------------------------
! 1      Po1(SU)          -        Fa0/23(P)   Fa0/24(P)
!
! 5. show ip interface brief | include Vlan
! ------------------------------------------------------------------------------
! SW-D1# show ip interface brief | include Vlan
! Vlan10                 172.16.7.130    YES manual up                    up
! Vlan20                 172.16.7.66     YES manual up                    up
! Vlan30                 172.16.4.2      YES manual up                    up
! Vlan40                 172.16.0.2      YES manual up                    up
! Vlan50                 172.16.7.2      YES manual up                    up
! Vlan60                 172.16.6.2      YES manual up                    up
! Vlan99                 172.16.7.194    YES manual up                    up
!
! 6. show standby brief
! ------------------------------------------------------------------------------
! SW-D1# show standby brief
!                      P indicates configured to preempt.
!                      |
! Interface   Grp  Pri P State   Active          Standby         Virtual IP
! Vl10        10   110 P Active  local           172.16.7.131    172.16.7.129
! Vl20        20   100 P Standby 172.16.7.67     local           172.16.7.65
! Vl30        30   110 P Active  local           172.16.4.3      172.16.4.1
! Vl40        40   100 P Standby 172.16.0.3      local           172.16.0.1
! Vl50        50   110 P Active  local           172.16.7.3      172.16.7.1
! Vl60        60   100 P Standby 172.16.6.3      local           172.16.6.1
! Vl99        99   110 P Active  local           172.16.7.195    172.16.7.193
!
! 7. show ip ospf neighbor
! ------------------------------------------------------------------------------
! SW-D1# show ip ospf neighbor
! Neighbor ID     Pri   State           Dead Time   Address         Interface
! 172.16.8.104      0   FULL/  -        00:00:35    172.16.8.90     GigabitEthernet0/2
! (Point-to-point network type eliminates DR/BDR election)
!
! 8. show ip route
! ------------------------------------------------------------------------------
! SW-D1# show ip route
! Gateway of last resort is 172.16.8.90 to network 0.0.0.0
!
! O*E2 0.0.0.0/0 [110/20] via 172.16.8.90, GigabitEthernet0/2
!      172.16.0.0/16 is variably subnetted, 18 subnets, 6 masks
! C       172.16.0.0/22 is directly connected, Vlan40
! L       172.16.0.2/32 is directly connected, Vlan40
! C       172.16.4.0/23 is directly connected, Vlan30
! L       172.16.4.2/32 is directly connected, Vlan30
! C       172.16.6.0/25 is directly connected, Vlan60
! L       172.16.6.2/32 is directly connected, Vlan60
! O IA    172.16.6.128/25 [110/50] via 172.16.8.90, GigabitEthernet0/2 (Clinic Guest)
! C       172.16.7.0/26 is directly connected, Vlan50
! L       172.16.7.2/32 is directly connected, Vlan50
! C       172.16.7.64/26 is directly connected, Vlan20
! L       172.16.7.66/32 is directly connected, Vlan20
! C       172.16.7.128/26 is directly connected, Vlan10
! L       172.16.7.130/32 is directly connected, Vlan10
! C       172.16.7.192/27 is directly connected, Vlan99
! L       172.16.7.194/32 is directly connected, Vlan99
! O IA    172.16.7.224/27 [110/50] via 172.16.8.90, GigabitEthernet0/2 (Clinic Voice)
! O IA    172.16.8.0/24 [110/50] via 172.16.8.90, GigabitEthernet0/2 (Clinic Summary)
! C       172.16.8.88/30 is directly connected, GigabitEthernet0/2
! L       172.16.8.89/32 is directly connected, GigabitEthernet0/2
! O       172.16.8.92/30 [110/2] via 172.16.8.90, GigabitEthernet0/2 (SW-D2 Transit)
! C       172.16.8.106/32 is directly connected, Loopback0
!
! 9. Inter-VLAN Ping Verification Commands (execute from privileged exec)
! ------------------------------------------------------------------------------
! SW-D1# ping 172.16.7.4               ! Ping SRV-CENTRAL (VLAN 50 Server Farm) -> Success rate 100 percent
! SW-D1# ping 172.16.7.141             ! Ping PC-ICU-NURSE (VLAN 10 ICU Clinical) -> Success rate 100 percent
! SW-D1# ping 172.16.7.76              ! Ping PC-THEATRE-1 (VLAN 20 Surgery) -> Success rate 100 percent
! SW-D1# ping 172.16.4.10              ! Ping PC-ADMIN-301 (VLAN 30 Admin) -> Success rate 100 percent
! SW-D1# ping 172.16.8.90              ! Ping Core Router R1 Gig0/0 Transit Link -> Success rate 100 percent
! SW-D1# ping 172.16.8.36              ! Ping Remote Clinic Server SRV-CACHE -> Success rate 100 percent
!
! 10. Simulated HSRP Failure Drill Protocol
! ------------------------------------------------------------------------------
! Step 1: Verify SW-D1 is Active for VLAN 10 (Pri 110) via 'show standby brief'.
! Step 2: Simulate failure of Core Router R1 uplink:
!         SW-D1(config)# interface GigabitEthernet0/2
!         SW-D1(config-if)# shutdown
! Step 3: Observe syslog priority decrement (110 - 20 = 90):
!         %STANDBY-6-STATECHANGE: Vlan10 Group 10 state Active -> Speak
!         %STANDBY-6-STATECHANGE: Vlan10 Group 10 state Speak -> Standby
! Step 4: Verify SW-D2 preempts and becomes Active for Group 10 (Pri 100 > 90).
! Step 5: Restore the uplink:
!         SW-D1(config)# interface GigabitEthernet0/2
!         SW-D1(config-if)# no shutdown
! Step 6: SW-D1 recovers priority 110, preempts SW-D2, and regains Active state:
!         %STANDBY-6-STATECHANGE: Vlan10 Group 10 state Standby -> Active
!
! 11. Security ACL Verification Commands & Hit Counter Audit
! ------------------------------------------------------------------------------
! Step 1: Clear ACL hit counters before initiating validation tests:
! SW-D1# clear access-list counters
!
! Step 2: Confirm inbound ACL bindings on SVIs:
! SW-D1# show ip interface Vlan10 | include Inbound access list
!   Inbound access list is ACL-ICU-IN
! SW-D1# show ip interface Vlan20 | include Inbound access list
!   Inbound access list is ACL-SURGERY-IN
! SW-D1# show ip interface Vlan30 | include Inbound access list
!   Inbound access list is ACL-ADMIN-IN
! SW-D1# show ip interface Vlan40 | include Inbound access list
!   Inbound access list is ACL-GUEST-IN
! SW-D1# show ip interface Vlan50 | include Inbound access list
!   Inbound access list is ACL-SERVER-IN
! SW-D1# show ip interface Vlan60 | include Inbound access list
!   Inbound access list is ACL-VOICE-IN
! SW-D1# show ip interface Vlan99 | include Inbound access list
!   Inbound access list is ACL-MGMT-IN
!
! Step 3: Inspect active access lists and packet match counters:
! SW-D1# show access-lists
! Extended IP access list ACL-ICU-IN
!     10 permit udp any any eq bootps
!     20 permit udp any host 172.16.7.4 eq domain
!     30 permit tcp any host 172.16.7.4 eq domain
!     40 permit tcp any host 172.16.7.4 eq www (12 matches)
!     50 permit tcp any host 172.16.7.4 eq 443
!     60 permit tcp any host 172.16.7.7 eq 104
!     70 permit tcp any host 172.16.7.7 eq www
!     80 permit tcp any host 172.16.7.7 eq 443 (8 matches)
!     90 permit tcp any host 172.16.7.8 eq 443
!     100 permit tcp any host 172.16.8.36 eq www
!     110 permit tcp any host 172.16.8.36 eq 443
!     120 permit tcp any any established (45 matches)
!     130 permit icmp any any echo (5 matches)
!     140 permit icmp any any echo-reply
!     150 deny ip any 172.16.4.0 0.0.1.255 log (3 matches)
!     160 deny ip any 172.16.0.0 0.0.3.255 log
!     170 deny ip any any log
! Extended IP access list ACL-GUEST-IN
!     10 permit udp any any eq bootps (4 matches)
!     20 permit udp any host 172.16.7.4 eq domain (15 matches)
!     30 permit tcp any host 172.16.7.4 eq domain
!     40 permit tcp any any established (112 matches)
!     50 permit icmp any any echo (10 matches)
!     60 permit icmp any any echo-reply
!     70 deny ip any 172.16.0.0 0.0.255.255 log (24 matches)
!     80 permit ip any any (88 matches)
! Standard IP access list ACL-VTY-SSH
!     10 permit 172.16.7.212 (2 matches)
!     20 permit 172.16.8.75
!     30 deny any log
!
! 12. Quality of Service (QoS) Verification & Policy Status
! ------------------------------------------------------------------------------
! Step 1: Verify global MLS QoS status on distribution switch:
! SW-D1# show mls qos
!   QoS is enabled
!   QoS ip packet dscp rewrite is enabled
!
! Step 2: Confirm DSCP trust on routed uplink to R1:
! SW-D1# show mls qos interface GigabitEthernet0/2
!   GigabitEthernet0/2
!   trust state: trust dscp
!   trust mode: trust dscp
!   COS override: dis
!   default COS: 0
!   pass-through: none
!
! Step 3: Inspect SVI Ingress Service-Policy:
! SW-D1# show policy-map interface Vlan10
!   Vlan10 
!     Service-policy input: PM-DISTRO-MARK-INGRESS
!       Class-map: CM-DISTRO-VITALS (match-any)
!         50 packets
!         Match: access-group name ACL-MARK-VITALS
!         QoS Set
!           dscp ef
!       Class-map: CM-DISTRO-IMAGING (match-any)
!         0 packets
!         Match: access-group name ACL-MARK-IMAGING
!         QoS Set
!           dscp af31
!       Class-map: CM-DISTRO-ADMIN (match-any)
!         12 packets
!         Match: access-group name ACL-MARK-ADMIN
!         QoS Set
!           dscp af21
!       Class-map: class-default (match-any)
!         5 packets
!         QoS Set
!           dscp default
! [NOTE ON PACKET TRACER 8.x LIMITATION]
! In Packet Tracer 8.x, Catalyst 3560 accepts 'mls qos' and parses 'policy-map' syntax,
! but hardware queue scheduling and packet rate limiting are stubbed. Drop counters
! and strict LLQ serialization operate on Core Routers R1 and R2 across WAN serial links.
! ==============================================================================

```

### Appendix 13.5: Device Configuration — SW-D2

```ios
! ==============================================================================
! DEVICE:       SW-D2
! MODEL:        Cisco Catalyst 3560-24PS (Multilayer Layer-3 Switch)
! LOCATION:     Main Hospital Campus - Distribution Rack B
! ROLE:         Distribution Aggregator / Active Gateway Group 2 / Secondary STP Root
! UPLINK:       GigabitEthernet0/2 -> Core Router R1 GigabitEthernet0/1 (/30 Routed)
! CROSS-CONNECT:FastEthernet0/23 - 24 -> SW-D1 (EtherChannel Port-Channel 1)
! DOWNLINKS:    Fa0/1 (SW-A1), Fa0/2 (SW-A2), Fa0/3 (SW-A3), Fa0/4 (SW-A4)
! SERVERS:      Fa0/12 (SRV-BACKUP)
! ==============================================================================

enable
configure terminal

! --- Device Identity & System Security ---
hostname SW-D2
no ip domain-lookup
ip domain-name hospital.local

banner motd ^C
================================================================================
  SW-D2 : Main Hospital Multilayer Distribution Switch 2
  VIT Vellore - CN Project: Disaster-Resilient Smart Hospital Network
  UNAUTHORIZED ACCESS IS STRICTLY PROHIBITED. ALL SESSIONS MONITORED.
================================================================================
^C

! --- Management Authentication & Credential Encryption ---
enable secret class123
service password-encryption
username admin privilege 15 secret class123

! --- Cryptographic SSH Version 2 Configuration ---
crypto key generate rsa modulus 1024
ip ssh version 2
ip ssh time-out 60
ip ssh authentication-retries 3

! --- Infrastructure Hardening: Standard ACL for VTY Management ---
ip access-list standard ACL-VTY-SSH
 remark Permit Central Hospital NOC Management Console
 permit host 172.16.7.212
 remark Permit Remote Clinic Local Management Station
 permit host 172.16.8.75
 remark Deny all other administrative attempts with logging
 deny any log
exit

line con 0
 password cisco
 login
 logging synchronous
 exec-timeout 15 0
exit

line vty 0 4
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

line vty 5 15
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

! --- Disable Insecure / Unnecessary Management Services ---
no ip http server
no ip http secure-server

! --- Centralized Time Synchronization (NTP Client) ---
ntp server 172.16.7.4

! --- Centralized Logging (Syslog Client) ---
logging host 172.16.7.4
logging trap informational
logging buffered 4096 informational

! --- Enable Hardware Layer-3 IP Routing & Global Quality of Service ---
ip routing
mls qos

! --- VLAN Database Definition ---
vlan 10
 name ICU_Clinical
vlan 20
 name Surgery_Theatre
vlan 30
 name Administration
vlan 40
 name Guest_WiFi
vlan 50
 name Server_Farm
vlan 60
 name VoIP_Voice
vlan 99
 name Management
vlan 999
 name Parking_Native
exit

! --- Spanning Tree Protocol: Rapid PVST+ Configuration ---
! SW-D2 is Root Primary for Even Tens / Group 2 (VLANs 20, 40, 60)
! SW-D2 is Root Secondary for Odd Tens / Group 1 (VLANs 10, 30, 50, 99)
spanning-tree mode rapid-pvst
spanning-tree vlan 20,40,60 root primary
spanning-tree vlan 10,30,50,99 root secondary

! --- Inter-Distribution EtherChannel (Port-Channel 1 to SW-D1) ---
interface range FastEthernet0/23 - 24
 description Inter_Distribution_EtherChannel_Member_to_SW-D1
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,20,30,40,50,60,99
 switchport nonegotiate
 channel-group 1 mode on
 no shutdown
exit

interface Port-channel 1
 description Aggregate_Trunk_CrossLink_to_SW-D1
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,20,30,40,50,60,99
 switchport nonegotiate
 mls qos trust dscp
 no shutdown
exit

! --- 802.1Q Distribution-to-Access Trunk Downlinks ---

! Trunk to SW-A1 (ICU Floor: VLANs 10, 60, 99 - Secondary Standby)
interface FastEthernet0/1
 description Secondary_Trunk_Downlink_to_SW-A1_Gig0/2
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,60,99
 switchport nonegotiate
 no shutdown
exit

! Trunk to SW-A2 (Surgery Floor: VLANs 20, 60, 99 - Secondary Standby)
interface FastEthernet0/2
 description Secondary_Trunk_Downlink_to_SW-A2_Gig0/2
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 20,60,99
 switchport nonegotiate
 no shutdown
exit

! Trunk to SW-A3 (Admin Floor: VLANs 30, 60, 99 - Primary Active)
interface FastEthernet0/3
 description Primary_Trunk_Downlink_to_SW-A3_Gig0/1
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 30,60,99
 switchport nonegotiate
 no shutdown
exit

! Trunk to SW-A4 (Guest Wi-Fi: VLANs 40, 99 - Primary Active)
interface FastEthernet0/4
 description Primary_Trunk_Downlink_to_SW-A4_Gig0/1
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 40,99
 switchport nonegotiate
 switchport block unicast
 no shutdown
exit

! --- Dedicated Server Farm Access Port (DR Backup Target: 172.16.7.8) ---
interface FastEthernet0/12
 description Server_Farm_Disaster_Recovery_Backup_Server
 switchport mode access
 switchport access vlan 50
 spanning-tree portfast
 spanning-tree bpduguard enable
 no shutdown
exit

! --- Layer 3 Routed Uplink to Core Router R1 (/30 Transit Subnet) ---
interface GigabitEthernet0/2
 description Routed_Point_to_Point_Uplink_to_R1_Gig0/1
 no switchport
 ip address 172.16.8.93 255.255.255.252
 ip ospf network point-to-point
 mls qos trust dscp
 no shutdown
exit

! --- Loopback 0 Management & OSPF Router-ID ---
interface Loopback0
 description OSPF_Router_ID_and_Management
 ip address 172.16.8.107 255.255.255.255
 no shutdown
exit

! ==============================================================================
! ACCESS CONTROL LISTS (ACLS) & ZERO-TRUST MICROSEGMENTATION
! ==============================================================================

! --- VLAN 10 Inbound ACL: ICU Clinical Wards ---
ip access-list extended ACL-ICU-IN
 remark Permit client DHCP requests to relay agent
 permit udp any any eq bootps
 remark Permit DNS resolution to Central Server
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Permit HTTP and HTTPS to Central Hospital EHR Portal
 permit tcp any host 172.16.7.4 eq www
 permit tcp any host 172.16.7.4 eq 443
 remark Permit DICOM and PACS web viewer to PACS Archive Server
 permit tcp any host 172.16.7.7 eq 104
 permit tcp any host 172.16.7.7 eq www
 permit tcp any host 172.16.7.7 eq 443
 remark Permit DR database replication to Backup Server
 permit tcp any host 172.16.7.8 eq 443
 remark Permit access to Remote Clinic local EHR cache
 permit tcp any host 172.16.8.36 eq www
 permit tcp any host 172.16.8.36 eq 443
 remark Permit established TCP return traffic
 permit tcp any any established
 remark Permit ICMP diagnostic echo and echo-reply
 permit icmp any any echo
 permit icmp any any echo-reply
 remark Explicitly deny and log lateral access to Admin VLAN 30
 deny ip any 172.16.4.0 0.0.1.255 log
 remark Explicitly deny and log lateral access to Guest VLAN 40
 deny ip any 172.16.0.0 0.0.3.255 log
 remark Implicit deny all other traffic
 deny ip any any log
exit

! --- VLAN 20 Inbound ACL: Surgery Operating Theatres ---
ip access-list extended ACL-SURGERY-IN
 remark Permit client DHCP requests to relay agent
 permit udp any any eq bootps
 remark Permit DNS resolution to Central Server
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Permit HTTP and HTTPS to Central Hospital EHR Portal
 permit tcp any host 172.16.7.4 eq www
 permit tcp any host 172.16.7.4 eq 443
 remark Permit DICOM image stream to PACS Archive Server
 permit tcp any host 172.16.7.7 eq 104
 permit tcp any host 172.16.7.7 eq www
 permit tcp any host 172.16.7.7 eq 443
 remark Permit established TCP return traffic
 permit tcp any any established
 remark Permit ICMP diagnostic echo and echo-reply
 permit icmp any any echo
 permit icmp any any echo-reply
 remark Explicitly deny and log lateral access to Admin VLAN 30
 deny ip any 172.16.4.0 0.0.1.255 log
 remark Explicitly deny and log lateral access to Guest VLAN 40
 deny ip any 172.16.0.0 0.0.3.255 log
 remark Implicit deny all other traffic
 deny ip any any log
exit

! --- VLAN 30 Inbound ACL: Hospital Administration ---
ip access-list extended ACL-ADMIN-IN
 remark Permit client DHCP requests to relay agent
 permit udp any any eq bootps
 remark Permit DNS resolution to Central Server
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Permit HTTP and HTTPS to Central Hospital EHR Portal
 permit tcp any host 172.16.7.4 eq www
 permit tcp any host 172.16.7.4 eq 443
 remark Permit PACS administrative portal access
 permit tcp any host 172.16.7.7 eq www
 permit tcp any host 172.16.7.7 eq 443
 remark Permit TFTP backup transfer to Backup Server
 permit udp any host 172.16.7.8 eq tftp
 remark Permit outbound Internet web traffic (HTTP/HTTPS)
 permit tcp any any eq www
 permit tcp any any eq 443
 remark Permit established TCP return traffic
 permit tcp any any established
 remark Permit ICMP diagnostic echo and echo-reply
 permit icmp any any echo
 permit icmp any any echo-reply
 remark Explicitly deny and log access to acute ICU VLAN 10
 deny ip any 172.16.7.128 0.0.0.63 log
 remark Explicitly deny and log access to Surgery VLAN 20
 deny ip any 172.16.7.64 0.0.0.63 log
 remark Explicitly deny and log access to Guest VLAN 40
 deny ip any 172.16.0.0 0.0.3.255 log
 remark Implicit deny all other traffic
 deny ip any any log
exit

! --- VLAN 40 Inbound ACL: Hospital Guest Wi-Fi ---
ip access-list extended ACL-GUEST-IN
 remark Permit DHCP discovery broadcast and relay
 permit udp any any eq bootps
 remark Permit DNS resolution exclusively to Central DNS Server
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Explicitly deny and log any attempt to reach internal hospital networks
 deny ip any 172.16.0.0 0.0.255.255 log
 remark Permit outbound Internet web browsing (HTTP/HTTPS)
 permit tcp any any eq www
 permit tcp any any eq 443
 remark Permit external ICMP echo requests for connectivity checks
 permit icmp any any echo
 remark Permit established TCP return traffic
 permit tcp any any established
 remark Implicit deny all other unauthorized guest traffic
 deny ip any any log
exit

! --- VLAN 50 Inbound ACL: Central Server Farm ---
ip access-list extended ACL-SERVER-IN
 remark Permit DNS server outbound root queries
 permit udp host 172.16.7.4 any eq domain
 permit tcp host 172.16.7.4 any eq domain
 remark Permit DHCP server response offers and acknowledgments
 permit udp host 172.16.7.4 any eq bootpc
 remark Permit PACS archive replication to Remote Clinic Cache
 permit tcp host 172.16.7.7 host 172.16.8.36 eq 443
 remark Permit database synchronization to Backup Server
 permit tcp host 172.16.7.4 host 172.16.7.8 eq 443
 remark Permit established TCP return traffic to all hospital zones
 permit tcp any any established
 remark Permit ICMP diagnostic echo-reply and echo
 permit icmp any any echo-reply
 permit icmp any any echo
 remark Implicit deny unsolicited outbound connections from servers
 deny ip any any log
exit

! --- VLAN 60 Inbound ACL: VoIP Telephony ---
ip access-list extended ACL-VOICE-IN
 remark Permit DHCP requests with Option 150
 permit udp any any eq bootps
 remark Permit DNS queries for PBX hostname resolution
 permit udp any host 172.16.7.4 eq domain
 remark Permit TFTP firmware and config downloads from Central Server
 permit udp any host 172.16.7.4 eq tftp
 remark Permit SIP signaling between phones and call manager
 permit udp any any eq 5060
 permit tcp any any eq 5060
 remark Permit RTP voice media streams (UDP port range 16384-32767)
 permit udp any any range 16384 32767
 remark Permit ICMP echo for phone health checks
 permit icmp any any echo
 remark Explicitly deny and log any voice packet targeting data VLANs
 deny ip any 172.16.4.0 0.0.1.255 log
 deny ip any 172.16.0.0 0.0.3.255 log
 remark Implicit deny all other voice traffic
 deny ip any any log
exit

! --- VLAN 99 Inbound ACL: Out-of-Band Management ---
ip access-list extended ACL-MGMT-IN
 remark Permit NOC administrator console full access
 permit ip host 172.16.7.212 any
 remark Permit Remote Clinic admin station access
 permit ip host 172.16.8.75 any
 remark Permit established TCP return management traffic
 permit tcp any any established
 remark Permit ICMP echo and echo-reply
 permit icmp any any echo
 permit icmp any any echo-reply
 remark Explicitly deny and log all unapproved management access
 deny ip any any log
exit

! --- Quality of Service (QoS): Ingress Classification ACLs (SW-D2) ---
ip access-list extended ACL-MARK-VOICE
 remark Class C2: Ingress VoIP Bearer Audio & Signaling
 permit udp 172.16.6.0 0.0.0.127 any
 permit tcp 172.16.6.0 0.0.0.127 any
exit

ip access-list extended ACL-MARK-ADMIN
 remark Class C4: Ingress Admin EHR Queries & DNS
 permit tcp 172.16.4.0 0.0.1.255 host 172.16.7.4 eq www
 permit tcp 172.16.4.0 0.0.1.255 host 172.16.7.4 eq 443
 permit udp 172.16.4.0 0.0.1.255 host 172.16.7.4 eq domain
exit

ip access-list extended ACL-MARK-GUEST
 remark Class C5: Ingress Guest Wi-Fi Scavenger Traffic
 permit ip 172.16.0.0 0.0.3.255 any
exit

! --- Quality of Service (QoS): MQC Ingress Class-Maps ---
class-map match-any CM-DISTRO-VOICE
 match access-group name ACL-MARK-VOICE
exit

class-map match-any CM-DISTRO-ADMIN
 match access-group name ACL-MARK-ADMIN
exit

class-map match-any CM-DISTRO-GUEST
 match access-group name ACL-MARK-GUEST
exit

! --- Quality of Service (QoS): MQC Ingress Marking Policy-Map ---
policy-map PM-DISTRO-MARK-INGRESS
 class CM-DISTRO-VOICE
  set dscp cs5
 class CM-DISTRO-ADMIN
  set dscp af21
 class CM-DISTRO-GUEST
  set dscp cs1
 class class-default
  set dscp default
exit

! --- Inter-VLAN Routing: Switch Virtual Interfaces (SVIs) & HSRP v2 ---
! Group 1 (Odd VLANs: 10, 30, 50, 99): SW-D2 is STANDBY (Priority 100, Preempt)
! Group 2 (Even VLANs: 20, 40, 60): SW-D2 is ACTIVE (Priority 110, Preempt, Track Gi0/2 decr 20)
! DHCP Relay: ip helper-address points to Central DHCP Server SRV-CENTRAL (172.16.7.4)

! VLAN 10 : ICU Clinical Wards (Subnet: 172.16.7.128/26, VIP: .129, SVI: .131 - STANDBY)
interface Vlan10
 description SVI_ICU_Clinical_Gateway
 ip address 172.16.7.131 255.255.255.192
 ip access-group ACL-ICU-IN in
 ip helper-address 172.16.7.4
 standby version 2
 standby 10 ip 172.16.7.129
 standby 10 priority 100
 standby 10 preempt
 no shutdown
exit

! VLAN 20 : Surgery Operating Theatres (Subnet: 172.16.7.64/26, VIP: .65, SVI: .67 - ACTIVE)
interface Vlan20
 description SVI_Surgery_Theatre_Gateway
 ip address 172.16.7.67 255.255.255.192
 ip access-group ACL-SURGERY-IN in
 ip helper-address 172.16.7.4
 standby version 2
 standby 20 ip 172.16.7.65
 standby 20 priority 110
 standby 20 preempt
 standby 20 track GigabitEthernet0/2 20
 no shutdown
exit

! VLAN 30 : Hospital Administration (Subnet: 172.16.4.0/23, VIP: .1, SVI: .3 - STANDBY)
interface Vlan30
 description SVI_Administration_Gateway
 ip address 172.16.4.3 255.255.254.0
 ip access-group ACL-ADMIN-IN in
 ip helper-address 172.16.7.4
 service-policy input PM-DISTRO-MARK-INGRESS
 standby version 2
 standby 30 ip 172.16.4.1
 standby 30 priority 100
 standby 30 preempt
 no shutdown
exit

! VLAN 40 : Hospital Guest Wi-Fi (Subnet: 172.16.0.0/22, VIP: .1, SVI: .3 - ACTIVE)
interface Vlan40
 description SVI_Guest_WiFi_Gateway
 ip address 172.16.0.3 255.255.252.0
 ip access-group ACL-GUEST-IN in
 ip helper-address 172.16.7.4
 service-policy input PM-DISTRO-MARK-INGRESS
 standby version 2
 standby 40 ip 172.16.0.1
 standby 40 priority 110
 standby 40 preempt
 standby 40 track GigabitEthernet0/2 20
 no shutdown
exit

! VLAN 50 : Central Server Farm (Subnet: 172.16.7.0/26, VIP: .1, SVI: .3 - STANDBY)
interface Vlan50
 description SVI_Server_Farm_Gateway
 ip address 172.16.7.3 255.255.255.192
 ip access-group ACL-SERVER-IN in
 standby version 2
 standby 50 ip 172.16.7.1
 standby 50 priority 100
 standby 50 preempt
 no shutdown
exit

! VLAN 60 : VoIP Telephony (Subnet: 172.16.6.0/25, VIP: .1, SVI: .3 - ACTIVE)
interface Vlan60
 description SVI_VoIP_Voice_Gateway
 ip address 172.16.6.3 255.255.255.128
 ip access-group ACL-VOICE-IN in
 ip helper-address 172.16.7.4
 service-policy input PM-DISTRO-MARK-INGRESS
 standby version 2
 standby 60 ip 172.16.6.1
 standby 60 priority 110
 standby 60 preempt
 standby 60 track GigabitEthernet0/2 20
 no shutdown
exit

! VLAN 99 : Out-of-Band Management (Subnet: 172.16.7.192/27, VIP: .193, SVI: .195 - STANDBY)
interface Vlan99
 description In_Band_Management_SVI_SW-D2
 ip address 172.16.7.195 255.255.255.224
 ip access-group ACL-MGMT-IN in
 standby version 2
 standby 99 ip 172.16.7.193
 standby 99 priority 100
 standby 99 preempt
 no shutdown
exit

! --- Dynamic Routing: Multi-Area OSPF Process 1 (Area 0 Backbone) ---
router ospf 1
 router-id 172.16.8.107
 ! Security: Passive-interface default suppresses OSPF hellos on client host VLANs
 passive-interface default
 no passive-interface GigabitEthernet0/2
 no passive-interface Loopback0
 ! Core Backbone Area 0 Advertisements
 network 172.16.8.107 0.0.0.0 area 0       ! Loopback0
 network 172.16.8.92 0.0.0.3 area 0         ! Routed link to R1 (Gi0/2)
 network 172.16.7.128 0.0.0.63 area 0       ! VLAN 10 ICU Clinical
 network 172.16.7.64 0.0.0.63 area 0        ! VLAN 20 Surgery Theatres
 network 172.16.4.0 0.0.1.255 area 0        ! VLAN 30 Hospital Admin
 network 172.16.0.0 0.0.3.255 area 0        ! VLAN 40 Guest Wi-Fi
 network 172.16.7.0 0.0.0.63 area 0         ! VLAN 50 Central Server Farm
 network 172.16.6.0 0.0.0.127 area 0        ! VLAN 60 VoIP Telephony
 network 172.16.7.192 0.0.0.31 area 0       ! VLAN 99 Management
exit

! --- Floating Static Default Route to Core Router R1 (AD 200 Backup) ---
! Primary default route is dynamically learned from R1 via OSPF (Type-5 AS-External, AD 110).
! This floating static route activates only in the event of total dynamic routing failure.
ip route 0.0.0.0 0.0.0.0 172.16.8.94 200

! --- Security: Shutdown & Park All Unused Physical Interfaces in VLAN 999 ---
interface range FastEthernet0/5 - 11, FastEthernet0/13 - 22, GigabitEthernet0/1
 description Security_Unused_Port_Parked_in_VLAN999
 switchport mode access
 switchport access vlan 999
 shutdown
exit

end
write memory

! ==============================================================================
! VERIFICATION COMMANDS & EXPECTED OUTPUT (Cisco Packet Tracer 8.x)
! ==============================================================================
!
! 1. show vlan brief
! ------------------------------------------------------------------------------
! SW-D2# show vlan brief
! VLAN Name                             Status    Ports
! ---- -------------------------------- --------- -------------------------------
! 1    default                          active    
! 10   ICU_Clinical                     active    
! 20   Surgery_Theatre                  active    
! 30   Administration                   active    
! 40   Guest_WiFi                       active    
! 50   Server_Farm                      active    Fa0/12
! 60   VoIP_Voice                       active    
! 99   Management                       active    
! 999  Parking_Native                   active    Fa0/5, Fa0/6, Fa0/7, Fa0/8, Fa0/9,
!                                                 Fa0/10, Fa0/11, Fa0/13, Fa0/14,
!                                                 Fa0/15, Fa0/16, Fa0/17, Fa0/18,
!                                                 Fa0/19, Fa0/20, Fa0/21, Fa0/22, Gi0/1
!
! 2. show interfaces trunk
! ------------------------------------------------------------------------------
! SW-D2# show interfaces trunk
! Port        Mode         Encapsulation  Status        Native vlan
! Fa0/1       on           802.1q         trunking      999
! Fa0/2       on           802.1q         trunking      999
! Fa0/3       on           802.1q         trunking      999
! Fa0/4       on           802.1q         trunking      999
! Po1         on           802.1q         trunking      999
!
! Port        Vlans allowed on trunk
! Fa0/1       10,60,99
! Fa0/2       20,60,99
! Fa0/3       30,60,99
! Fa0/4       40,99
! Po1         10,20,30,40,50,60,99
!
! 3. show spanning-tree summary
! ------------------------------------------------------------------------------
! SW-D2# show spanning-tree summary
! Switch is in rapid-pvst mode
! Root bridge for: VLAN0020, VLAN0040, VLAN0060
! Extended system ID is enabled
!
! 4. show etherchannel summary
! ------------------------------------------------------------------------------
! SW-D2# show etherchannel summary
! Group  Port-channel  Protocol    Ports
! ------+-------------+-----------+-----------------------------------------------
! 1      Po1(SU)          -        Fa0/23(P)   Fa0/24(P)
!
! 5. show ip interface brief | include Vlan
! ------------------------------------------------------------------------------
! SW-D2# show ip interface brief | include Vlan
! Vlan10                 172.16.7.131    YES manual up                    up
! Vlan20                 172.16.7.67     YES manual up                    up
! Vlan30                 172.16.4.3      YES manual up                    up
! Vlan40                 172.16.0.3      YES manual up                    up
! Vlan50                 172.16.7.3      YES manual up                    up
! Vlan60                 172.16.6.3      YES manual up                    up
! Vlan99                 172.16.7.195    YES manual up                    up
!
! 6. show standby brief
! ------------------------------------------------------------------------------
! SW-D2# show standby brief
!                      P indicates configured to preempt.
!                      |
! Interface   Grp  Pri P State   Active          Standby         Virtual IP
! Vl10        10   100 P Standby 172.16.7.130    local           172.16.7.129
! Vl20        20   110 P Active  local           172.16.7.66     172.16.7.65
! Vl30        30   100 P Standby 172.16.4.2      local           172.16.4.1
! Vl40        40   110 P Active  local           172.16.0.2      172.16.0.1
! Vl50        50   100 P Standby 172.16.7.2      local           172.16.7.1
! Vl60        60   110 P Active  local           172.16.6.2      172.16.6.1
! Vl99        99   100 P Standby 172.16.7.194    local           172.16.7.193
!
! 7. show ip ospf neighbor
! ------------------------------------------------------------------------------
! SW-D2# show ip ospf neighbor
! Neighbor ID     Pri   State           Dead Time   Address         Interface
! 172.16.8.104      0   FULL/  -        00:00:36    172.16.8.94     GigabitEthernet0/2
! (Point-to-point network type eliminates DR/BDR election)
!
! 8. show ip route
! ------------------------------------------------------------------------------
! SW-D2# show ip route
! Gateway of last resort is 172.16.8.94 to network 0.0.0.0
!
! O*E2 0.0.0.0/0 [110/20] via 172.16.8.94, GigabitEthernet0/2
!      172.16.0.0/16 is variably subnetted, 18 subnets, 6 masks
! C       172.16.0.0/22 is directly connected, Vlan40
! L       172.16.0.3/32 is directly connected, Vlan40
! C       172.16.4.0/23 is directly connected, Vlan30
! L       172.16.4.3/32 is directly connected, Vlan30
! C       172.16.6.0/25 is directly connected, Vlan60
! L       172.16.6.3/32 is directly connected, Vlan60
! O IA    172.16.6.128/25 [110/50] via 172.16.8.94, GigabitEthernet0/2 (Clinic Guest)
! C       172.16.7.0/26 is directly connected, Vlan50
! L       172.16.7.3/32 is directly connected, Vlan50
! C       172.16.7.64/26 is directly connected, Vlan20
! L       172.16.7.67/32 is directly connected, Vlan20
! C       172.16.7.128/26 is directly connected, Vlan10
! L       172.16.7.131/32 is directly connected, Vlan10
! C       172.16.7.192/27 is directly connected, Vlan99
! L       172.16.7.195/32 is directly connected, Vlan99
! O IA    172.16.7.224/27 [110/50] via 172.16.8.94, GigabitEthernet0/2 (Clinic Voice)
! O IA    172.16.8.0/24 [110/50] via 172.16.8.94, GigabitEthernet0/2 (Clinic Summary)
! O       172.16.8.88/30 [110/2] via 172.16.8.94, GigabitEthernet0/2 (SW-D1 Transit)
! C       172.16.8.92/30 is directly connected, GigabitEthernet0/2
! L       172.16.8.93/32 is directly connected, GigabitEthernet0/2
! C       172.16.8.107/32 is directly connected, Loopback0
!
! 9. Inter-VLAN Ping Verification Commands (execute from privileged exec)
! ------------------------------------------------------------------------------
! SW-D2# ping 172.16.7.4               ! Ping SRV-CENTRAL (VLAN 50 Server Farm) -> Success rate 100 percent
! SW-D2# ping 172.16.7.76              ! Ping PC-THEATRE-1 (VLAN 20 Surgery) -> Success rate 100 percent
! SW-D2# ping 172.16.7.141             ! Ping PC-ICU-NURSE (VLAN 10 ICU Clinical) -> Success rate 100 percent
! SW-D2# ping 172.16.6.10              ! Ping PHONE-ICU-601 (VLAN 60 VoIP) -> Success rate 100 percent
! SW-D2# ping 172.16.8.94              ! Ping Core Router R1 Gig0/1 Transit Link -> Success rate 100 percent
! SW-D2# ping 172.16.8.36              ! Ping Remote Clinic Server SRV-CACHE -> Success rate 100 percent
!
! 10. Simulated HSRP Failure Drill Protocol
! ------------------------------------------------------------------------------
! Step 1: Verify SW-D2 is Active for VLAN 20 (Pri 110) via 'show standby brief'.
! Step 2: Simulate failure of Core Router R1 uplink:
!         SW-D2(config)# interface GigabitEthernet0/2
!         SW-D2(config-if)# shutdown
! Step 3: Observe syslog priority decrement (110 - 20 = 90):
!         %STANDBY-6-STATECHANGE: Vlan20 Group 20 state Active -> Speak
!         %STANDBY-6-STATECHANGE: Vlan20 Group 20 state Speak -> Standby
! Step 4: Verify SW-D1 preempts and becomes Active for Group 20 (Pri 100 > 90).
! Step 5: Restore the uplink:
!         SW-D2(config)# interface GigabitEthernet0/2
!         SW-D2(config-if)# no shutdown
! Step 6: SW-D2 recovers priority 110, preempts SW-D1, and regains Active state:
!         %STANDBY-6-STATECHANGE: Vlan20 Group 20 state Standby -> Active
!
! 11. Security ACL Verification Commands & Hit Counter Audit
! ------------------------------------------------------------------------------
! Step 1: Clear ACL hit counters before initiating validation tests:
! SW-D2# clear access-list counters
!
! Step 2: Confirm inbound ACL bindings on SVIs:
! SW-D2# show ip interface Vlan10 | include Inbound access list
!   Inbound access list is ACL-ICU-IN
! SW-D2# show ip interface Vlan20 | include Inbound access list
!   Inbound access list is ACL-SURGERY-IN
! SW-D2# show ip interface Vlan30 | include Inbound access list
!   Inbound access list is ACL-ADMIN-IN
! SW-D2# show ip interface Vlan40 | include Inbound access list
!   Inbound access list is ACL-GUEST-IN
! SW-D2# show ip interface Vlan50 | include Inbound access list
!   Inbound access list is ACL-SERVER-IN
! SW-D2# show ip interface Vlan60 | include Inbound access list
!   Inbound access list is ACL-VOICE-IN
! SW-D2# show ip interface Vlan99 | include Inbound access list
!   Inbound access list is ACL-MGMT-IN
!
! Step 3: Inspect active access lists and packet match counters:
! SW-D2# show access-lists
! Extended IP access list ACL-ICU-IN
!     10 permit udp any any eq bootps
!     20 permit udp any host 172.16.7.4 eq domain
!     30 permit tcp any host 172.16.7.4 eq domain
!     40 permit tcp any host 172.16.7.4 eq www
!     50 permit tcp any host 172.16.7.4 eq 443
!     60 permit tcp any host 172.16.7.7 eq 104
!     70 permit tcp any host 172.16.7.7 eq www
!     80 permit tcp any host 172.16.7.7 eq 443
!     90 permit tcp any host 172.16.7.8 eq 443
!     100 permit tcp any host 172.16.8.36 eq www
!     110 permit tcp any host 172.16.8.36 eq 443
!     120 permit tcp any any established
!     130 permit icmp any any echo
!     140 permit icmp any any echo-reply
!     150 deny ip any 172.16.4.0 0.0.1.255 log
!     160 deny ip any 172.16.0.0 0.0.3.255 log
!     170 deny ip any any log
! Extended IP access list ACL-SURGERY-IN
!     10 permit udp any any eq bootps
!     20 permit udp any host 172.16.7.4 eq domain
!     30 permit tcp any host 172.16.7.4 eq domain
!     40 permit tcp any host 172.16.7.4 eq www (15 matches)
!     50 permit tcp any host 172.16.7.4 eq 443
!     60 permit tcp any host 172.16.7.7 eq 104 (45 matches)
!     70 permit tcp any host 172.16.7.7 eq www
!     80 permit tcp any host 172.16.7.7 eq 443 (20 matches)
!     90 permit tcp any any established (80 matches)
!     100 permit icmp any any echo
!     110 permit icmp any any echo-reply
!     120 deny ip any 172.16.4.0 0.0.1.255 log
!     130 deny ip any 172.16.0.0 0.0.3.255 log
!     140 deny ip any any log
! Standard IP access list ACL-VTY-SSH
!     10 permit 172.16.7.212
!     20 permit 172.16.8.75
!     30 deny any log
!
! 12. Quality of Service (QoS) Verification & Policy Status
! ------------------------------------------------------------------------------
! Step 1: Verify global MLS QoS status on distribution switch:
! SW-D2# show mls qos
!   QoS is enabled
!   QoS ip packet dscp rewrite is enabled
!
! Step 2: Confirm DSCP trust on routed uplink to R1:
! SW-D2# show mls qos interface GigabitEthernet0/2
!   GigabitEthernet0/2
!   trust state: trust dscp
!   trust mode: trust dscp
!   COS override: dis
!   default COS: 0
!   pass-through: none
!
! Step 3: Inspect SVI Ingress Service-Policy:
! SW-D2# show policy-map interface Vlan60
!   Vlan60 
!     Service-policy input: PM-DISTRO-MARK-INGRESS
!       Class-map: CM-DISTRO-VOICE (match-any)
!         25 packets
!         Match: access-group name ACL-MARK-VOICE
!         QoS Set
!           dscp cs5
!       Class-map: CM-DISTRO-ADMIN (match-any)
!         0 packets
!         Match: access-group name ACL-MARK-ADMIN
!         QoS Set
!           dscp af21
!       Class-map: CM-DISTRO-GUEST (match-any)
!         0 packets
!         Match: access-group name ACL-MARK-GUEST
!         QoS Set
!           dscp cs1
!       Class-map: class-default (match-any)
!         0 packets
!         QoS Set
!           dscp default
! [NOTE ON PACKET TRACER 8.x LIMITATION]
! In Packet Tracer 8.x, Catalyst 3560 accepts 'mls qos' and parses 'policy-map' syntax,
! but hardware queue scheduling and packet rate limiting are stubbed. Drop counters
! and strict LLQ serialization operate on Core Routers R1 and R2 across WAN serial links.
! ==============================================================================

```

### Appendix 13.6: Device Configuration — SW-D3

```ios
! ==============================================================================
! DEVICE:       SW-D3
! MODEL:        Cisco Catalyst 3560-24PS (Multilayer Layer-3 Switch)
! LOCATION:     Remote Spoke Clinic - Telecomm Equipment Closet
! ROLE:         Single-Chassis Branch Distribution Gateway / Spoke Root Bridge
! UPLINK:       GigabitEthernet0/1 -> Clinic Core Router R2 GigabitEthernet0/0 (/30)
! DOWNLINKS:    Fa0/23 & Fa0/24 -> SW-A5 (Redundant 802.1Q Trunks)
! LOCAL CACHE:  Fa0/10 -> SRV-CACHE (Local Offline EHR Survivability Cache)
! ==============================================================================

enable
configure terminal

! --- Device Identity & System Security ---
hostname SW-D3
no ip domain-lookup
ip domain-name hospital.local

banner motd ^C
================================================================================
  SW-D3 : Remote Spoke Clinic Multilayer Distribution Switch
  VIT Vellore - CN Project: Disaster-Resilient Smart Hospital Network
  UNAUTHORIZED ACCESS IS STRICTLY PROHIBITED. ALL SESSIONS MONITORED.
================================================================================
^C

! --- Management Authentication & Credential Encryption ---
enable secret class123
service password-encryption
username admin privilege 15 secret class123

! --- Cryptographic SSH Version 2 Configuration ---
crypto key generate rsa modulus 1024
ip ssh version 2
ip ssh time-out 60
ip ssh authentication-retries 3

! --- Infrastructure Hardening: Standard ACL for VTY Management ---
ip access-list standard ACL-VTY-SSH
 remark Permit Central Hospital NOC Management Console
 permit host 172.16.7.212
 remark Permit Remote Clinic Local Management Station
 permit host 172.16.8.75
 remark Deny all other administrative attempts with logging
 deny any log
exit

line con 0
 password cisco
 login
 logging synchronous
 exec-timeout 15 0
exit

line vty 0 4
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

line vty 5 15
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

! --- Disable Insecure / Unnecessary Management Services ---
no ip http server
no ip http secure-server

! --- Centralized Time Synchronization (NTP Client) ---
ntp server 172.16.7.4

! --- Centralized Logging (Syslog Client) ---
logging host 172.16.7.4
logging trap informational
logging buffered 4096 informational

! --- Enable Hardware Layer-3 IP Routing & Global Quality of Service ---
ip routing
mls qos

! --- VLAN Database Definition ---
vlan 10
 name Clinic_Clinical
vlan 30
 name Clinic_Admin
vlan 40
 name Clinic_Guest
vlan 60
 name Clinic_Voice
vlan 99
 name Management
vlan 999
 name Parking_Native
exit

! --- Spanning Tree Protocol: Rapid PVST+ Configuration ---
! SW-D3 is Root Primary for all Remote Clinic Spoke VLANs
spanning-tree mode rapid-pvst
spanning-tree vlan 10,30,40,60,99 root primary

! --- 802.1Q Redundant Distribution-to-Access Trunks to SW-A5 ---
! DTP disabled (switchport nonegotiate) and allowed VLANs restricted

! Primary Active Trunk to SW-A5
interface FastEthernet0/23
 description Primary_Trunk_Downlink_to_SW-A5_Gig0/1
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,30,40,60,99
 switchport nonegotiate
 no shutdown
exit

! Secondary Standby Trunk to SW-A5 (STP Alternate/Blocking port)
interface FastEthernet0/24
 description Redundant_Trunk_Downlink_to_SW-A5_Gig0/2
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,30,40,60,99
 switchport nonegotiate
 no shutdown
exit

! --- Dedicated Local Survivability Cache Server Port (VLAN 10) ---
! Edge port with PortFast enabled for instant link transitions
interface FastEthernet0/10
 description Remote_Clinic_Local_EHR_Cache_Server
 switchport mode access
 switchport access vlan 10
 spanning-tree portfast
 spanning-tree bpduguard enable
 no shutdown
exit

! --- Layer 3 Routed Uplink to Core Router R2 (/30 Transit Subnet) ---
interface GigabitEthernet0/1
 description Routed_Point_to_Point_Uplink_to_R2_Gig0/0
 no switchport
 ip address 172.16.8.97 255.255.255.252
 ip ospf network point-to-point
 mls qos trust dscp
 no shutdown
exit

! --- Loopback 0 Management & OSPF Router-ID ---
interface Loopback0
 description OSPF_Router_ID_and_Management
 ip address 172.16.8.108 255.255.255.255
 no shutdown
exit

! ==============================================================================
! ACCESS CONTROL LISTS (ACLS) & ZERO-TRUST MICROSEGMENTATION
! ==============================================================================

! --- VLAN 10 Inbound ACL: Clinic Clinical Wards ---
ip access-list extended ACL-CLINIC-CLINICAL-IN
 remark Permit DHCP relay across WAN to Central Server
 permit udp any any eq bootps
 remark Permit DNS resolution to Central Server across WAN
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Permit HTTP and HTTPS to local EHR Cache Server
 permit tcp any host 172.16.8.36 eq www
 permit tcp any host 172.16.8.36 eq 443
 remark Permit HTTP and HTTPS to Central Hospital Portal across WAN
 permit tcp any host 172.16.7.4 eq www
 permit tcp any host 172.16.7.4 eq 443
 remark Permit DICOM queries and web viewer to PACS Server across WAN
 permit tcp any host 172.16.7.7 eq 104
 permit tcp any host 172.16.7.7 eq www
 permit tcp any host 172.16.7.7 eq 443
 remark Permit established TCP return traffic
 permit tcp any any established
 remark Permit ICMP diagnostic echo and echo-reply
 permit icmp any any echo
 permit icmp any any echo-reply
 remark Explicitly deny and log lateral access to Clinic Admin VLAN 30
 deny ip any 172.16.8.0 0.0.0.31 log
 remark Explicitly deny and log lateral access to Clinic Guest VLAN 40
 deny ip any 172.16.6.128 0.0.0.127 log
 remark Implicit deny all other traffic
 deny ip any any log
exit

! --- VLAN 30 Inbound ACL: Clinic Administration ---
ip access-list extended ACL-CLINIC-ADMIN-IN
 remark Permit DHCP relay across WAN to Central Server
 permit udp any any eq bootps
 remark Permit DNS resolution to Central Server
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Permit HTTP and HTTPS to Central EHR Portal
 permit tcp any host 172.16.7.4 eq www
 permit tcp any host 172.16.7.4 eq 443
 remark Permit outbound Internet web browsing (HTTP/HTTPS)
 permit tcp any any eq www
 permit tcp any any eq 443
 remark Permit established TCP return traffic
 permit tcp any any established
 remark Permit ICMP diagnostic echo and echo-reply
 permit icmp any any echo
 permit icmp any any echo-reply
 remark Explicitly deny and log access to acute clinical VLAN 10
 deny ip any 172.16.8.32 0.0.0.31 log
 remark Explicitly deny and log access to guest VLAN 40
 deny ip any 172.16.6.128 0.0.0.127 log
 remark Implicit deny all other traffic
 deny ip any any log
exit

! --- VLAN 40 Inbound ACL: Clinic Guest Wi-Fi ---
ip access-list extended ACL-CLINIC-GUEST-IN
 remark Permit DHCP discovery broadcast and relay
 permit udp any any eq bootps
 remark Permit DNS resolution to Central Server
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Explicitly deny and log all internal hospital campus access
 deny ip any 172.16.0.0 0.0.255.255 log
 remark Permit outbound Internet web browsing (HTTP/HTTPS)
 permit tcp any any eq www
 permit tcp any any eq 443
 remark Permit external ICMP echo requests for connectivity checks
 permit icmp any any echo
 remark Permit established TCP return traffic
 permit tcp any any established
 remark Implicit deny all other unauthorized guest traffic
 deny ip any any log
exit

! --- VLAN 60 Inbound ACL: Clinic VoIP Telephony ---
ip access-list extended ACL-CLINIC-VOICE-IN
 remark Permit DHCP requests with Option 150
 permit udp any any eq bootps
 remark Permit DNS queries to Central Server
 permit udp any host 172.16.7.4 eq domain
 remark Permit TFTP firmware and config downloads from Central Server
 permit udp any host 172.16.7.4 eq tftp
 remark Permit SIP signaling to Central PBX across WAN
 permit udp any any eq 5060
 permit tcp any any eq 5060
 remark Permit RTP voice media streams across WAN (UDP port range 16384-32767)
 permit udp any any range 16384 32767
 remark Permit ICMP echo for phone health checks
 permit icmp any any echo
 remark Explicitly deny and log access to clinic data VLANs
 deny ip any 172.16.8.0 0.0.0.31 log
 deny ip any 172.16.6.128 0.0.0.127 log
 remark Implicit deny all other voice traffic
 deny ip any any log
exit

! --- VLAN 99 Inbound ACL: Remote Clinic Management ---
ip access-list extended ACL-CLINIC-MGMT-IN
 remark Permit Central NOC Admin PC full access
 permit ip host 172.16.7.212 any
 remark Permit Clinic Local Admin PC full access
 permit ip host 172.16.8.75 any
 remark Permit established TCP return management traffic
 permit tcp any any established
 remark Permit ICMP diagnostic echo and echo-reply
 permit icmp any any echo
 permit icmp any any echo-reply
 remark Explicitly deny and log all unapproved management access
 deny ip any any log
exit

! --- Quality of Service (QoS): Ingress Classification ACLs (SW-D3) ---
ip access-list extended ACL-MARK-CLINIC-VITALS
 remark Class C1: Ingress Clinic Triage Telemetry to Central Server
 permit udp host 172.16.8.44 host 172.16.7.4
 permit udp host 172.16.7.4 host 172.16.8.44
exit

ip access-list extended ACL-MARK-CLINIC-VOICE
 remark Class C2: Ingress Clinic VoIP Bearer Audio & Signaling
 permit udp 172.16.7.224 0.0.0.31 any
 permit tcp 172.16.7.224 0.0.0.31 any
exit

ip access-list extended ACL-MARK-CLINIC-IMAGING
 remark Class C3: Ingress Clinic PACS DICOM Queries & Cache Replication
 permit tcp any host 172.16.7.7 eq 104
 permit tcp host 172.16.7.7 any eq 104
 permit tcp host 172.16.8.36 host 172.16.7.7
 permit tcp host 172.16.7.7 host 172.16.8.36
exit

ip access-list extended ACL-MARK-CLINIC-ADMIN
 remark Class C4: Ingress Clinic Admin EHR Queries & DNS
 permit tcp 172.16.8.0 0.0.0.31 host 172.16.7.4 eq www
 permit tcp 172.16.8.0 0.0.0.31 host 172.16.7.4 eq 443
 permit udp any host 172.16.7.4 eq domain
exit

ip access-list extended ACL-MARK-CLINIC-GUEST
 remark Class C5: Ingress Clinic Guest Scavenger Traffic
 permit ip 172.16.6.128 0.0.0.127 any
exit

! --- Quality of Service (QoS): MQC Ingress Class-Maps ---
class-map match-any CM-DISTRO-VITALS
 match access-group name ACL-MARK-CLINIC-VITALS
exit

class-map match-any CM-DISTRO-VOICE
 match access-group name ACL-MARK-CLINIC-VOICE
exit

class-map match-any CM-DISTRO-IMAGING
 match access-group name ACL-MARK-CLINIC-IMAGING
exit

class-map match-any CM-DISTRO-ADMIN
 match access-group name ACL-MARK-CLINIC-ADMIN
exit

class-map match-any CM-DISTRO-GUEST
 match access-group name ACL-MARK-CLINIC-GUEST
exit

! --- Quality of Service (QoS): MQC Ingress Marking Policy-Map ---
policy-map PM-DISTRO-MARK-INGRESS
 class CM-DISTRO-VITALS
  set dscp ef
 class CM-DISTRO-VOICE
  set dscp cs5
 class CM-DISTRO-IMAGING
  set dscp af31
 class CM-DISTRO-ADMIN
  set dscp af21
 class CM-DISTRO-GUEST
  set dscp cs1
 class class-default
  set dscp default
exit

! --- Inter-VLAN Routing: Switch Virtual Interfaces (SVIs) ---
! SW-D3 provides local hardware layer-3 routing for all remote clinic subnets.
! DHCP Relay: ip helper-address forwards requests across WAN to SRV-CENTRAL (172.16.7.4).
! Note on Gateway Architecture: SW-D3 operates as the single-chassis default gateway (.1 of each usable pool).
! For HA dual-chassis deployment, refer to SW-D4 extension (/configs/SW-D4/SW-D4.cfg).

! VLAN 10 : Clinic Clinical Wards & EHR Cache (Subnet: 172.16.8.32/27, SVI Gateway: .33)
interface Vlan10
 description SVI_Clinic_Clinical_Gateway
 ip address 172.16.8.33 255.255.255.224
 ip access-group ACL-CLINIC-CLINICAL-IN in
 ip helper-address 172.16.7.4
 service-policy input PM-DISTRO-MARK-INGRESS
 no shutdown
exit

! VLAN 30 : Clinic Administration (Subnet: 172.16.8.0/27, SVI Gateway: .1)
interface Vlan30
 description SVI_Clinic_Admin_Gateway
 ip address 172.16.8.1 255.255.255.224
 ip access-group ACL-CLINIC-ADMIN-IN in
 ip helper-address 172.16.7.4
 service-policy input PM-DISTRO-MARK-INGRESS
 no shutdown
exit

! VLAN 40 : Clinic Guest Wi-Fi (Subnet: 172.16.6.128/25, SVI Gateway: .129)
interface Vlan40
 description SVI_Clinic_Guest_Gateway
 ip address 172.16.6.129 255.255.255.128
 ip access-group ACL-CLINIC-GUEST-IN in
 ip helper-address 172.16.7.4
 service-policy input PM-DISTRO-MARK-INGRESS
 no shutdown
exit

! VLAN 60 : Clinic VoIP Telephony (Subnet: 172.16.7.224/27, SVI Gateway: .225)
interface Vlan60
 description SVI_Clinic_Voice_Gateway
 ip address 172.16.7.225 255.255.255.224
 ip access-group ACL-CLINIC-VOICE-IN in
 ip helper-address 172.16.7.4
 service-policy input PM-DISTRO-MARK-INGRESS
 no shutdown
exit

! VLAN 99 : Remote Clinic Management (Subnet: 172.16.8.64/28, SVI Gateway: .65)
interface Vlan99
 description In_Band_Management_SVI_SW-D3
 ip address 172.16.8.65 255.255.255.240
 ip access-group ACL-CLINIC-MGMT-IN in
 no shutdown
exit

! --- Dynamic Routing: Multi-Area OSPF Process 1 (Area 1 Spoke) ---
router ospf 1
 router-id 172.16.8.108
 ! Security: Passive-interface default suppresses OSPF hellos on client host VLANs
 passive-interface default
 no passive-interface GigabitEthernet0/1
 no passive-interface Loopback0
 ! Remote Clinic Area 1 Advertisements
 network 172.16.8.108 0.0.0.0 area 1       ! Loopback0 in Area 1
 network 172.16.8.96 0.0.0.3 area 1         ! Routed link to R2 (Gi0/1)
 network 172.16.8.32 0.0.0.31 area 1        ! VLAN 10 Clinic Clinical
 network 172.16.8.0 0.0.0.31 area 1         ! VLAN 30 Clinic Admin
 network 172.16.6.128 0.0.0.127 area 1      ! VLAN 40 Clinic Guest Wi-Fi
 network 172.16.7.224 0.0.0.31 area 1       ! VLAN 60 Clinic VoIP
 network 172.16.8.64 0.0.0.15 area 1        ! VLAN 99 Clinic Management
exit

! --- Floating Static Default Route to Core Router R2 (AD 200 Backup) ---
! Primary default route is dynamically learned from R2 via OSPF (Type-5 AS-External originated by R1, AD 110).
! This floating static route activates only in the event of total dynamic routing failure.
ip route 0.0.0.0 0.0.0.0 172.16.8.98 200

! --- Security: Shutdown & Park All Unused Physical Interfaces in VLAN 999 ---
interface range FastEthernet0/1 - 9, FastEthernet0/11 - 22, GigabitEthernet0/2
 description Security_Unused_Port_Parked_in_VLAN999
 switchport mode access
 switchport access vlan 999
 shutdown
exit

end
write memory

! ==============================================================================
! VERIFICATION COMMANDS & EXPECTED OUTPUT (Cisco Packet Tracer 8.x)
! ==============================================================================
!
! 1. show vlan brief
! ------------------------------------------------------------------------------
! SW-D3# show vlan brief
! VLAN Name                             Status    Ports
! ---- -------------------------------- --------- -------------------------------
! 1    default                          active    
! 10   Clinic_Clinical                  active    Fa0/10
! 30   Clinic_Admin                     active    
! 40   Clinic_Guest                     active    
! 60   Clinic_Voice                     active    
! 99   Management                       active    
! 999  Parking_Native                   active    Fa0/1, Fa0/2, Fa0/3, Fa0/4, Fa0/5,
!                                                 Fa0/6, Fa0/7, Fa0/8, Fa0/9,
!                                                 Fa0/11, Fa0/12, Fa0/13, Fa0/14,
!                                                 Fa0/15, Fa0/16, Fa0/17, Fa0/18,
!                                                 Fa0/19, Fa0/20, Fa0/21, Fa0/22, Gi0/2
!
! 2. show interfaces trunk
! ------------------------------------------------------------------------------
! SW-D3# show interfaces trunk
! Port        Mode         Encapsulation  Status        Native vlan
! Fa0/23      on           802.1q         trunking      999
! Fa0/24      on           802.1q         trunking      999
!
! Port        Vlans allowed on trunk
! Fa0/23      10,30,40,60,99
! Fa0/24      10,30,40,60,99
!
! 3. show spanning-tree summary
! ------------------------------------------------------------------------------
! SW-D3# show spanning-tree summary
! Switch is in rapid-pvst mode
! Root bridge for: VLAN0010, VLAN0030, VLAN0040, VLAN0060, VLAN0099
! Extended system ID is enabled
!
! 4. show ip interface brief | include Vlan
! ------------------------------------------------------------------------------
! SW-D3# show ip interface brief | include Vlan
! Vlan10                 172.16.8.33     YES manual up                    up
! Vlan30                 172.16.8.1      YES manual up                    up
! Vlan40                 172.16.6.129    YES manual up                    up
! Vlan60                 172.16.7.225    YES manual up                    up
! Vlan99                 172.16.8.65     YES manual up                    up
!
! 5. show ip ospf neighbor
! ------------------------------------------------------------------------------
! SW-D3# show ip ospf neighbor
! Neighbor ID     Pri   State           Dead Time   Address         Interface
! 172.16.8.105      0   FULL/  -        00:00:35    172.16.8.98     GigabitEthernet0/1
! (Point-to-point network type eliminates DR/BDR election)
!
! 6. show ip route
! ------------------------------------------------------------------------------
! SW-D3# show ip route
! Gateway of last resort is 172.16.8.98 to network 0.0.0.0
!
! O*E2 0.0.0.0/0 [110/20] via 172.16.8.98, GigabitEthernet0/1 (Originated by R1)
!      172.16.0.0/16 is variably subnetted, 19 subnets, 6 masks
! O IA    172.16.0.0/22 [110/51] via 172.16.8.98, GigabitEthernet0/1 (Main Guest Wi-Fi)
! O IA    172.16.4.0/23 [110/51] via 172.16.8.98, GigabitEthernet0/1 (Main Admin)
! O IA    172.16.6.0/25 [110/51] via 172.16.8.98, GigabitEthernet0/1 (Main VoIP)
! C       172.16.6.128/25 is directly connected, Vlan40
! L       172.16.6.129/32 is directly connected, Vlan40
! O IA    172.16.7.0/26 [110/51] via 172.16.8.98, GigabitEthernet0/1 (Main Server Farm)
! O IA    172.16.7.64/26 [110/51] via 172.16.8.98, GigabitEthernet0/1 (Main Surgery)
! O IA    172.16.7.128/26 [110/51] via 172.16.8.98, GigabitEthernet0/1 (Main ICU)
! O IA    172.16.7.192/27 [110/51] via 172.16.8.98, GigabitEthernet0/1 (Main Management)
! C       172.16.7.224/27 is directly connected, Vlan60
! L       172.16.7.225/32 is directly connected, Vlan60
! C       172.16.8.0/27 is directly connected, Vlan30
! L       172.16.8.1/32 is directly connected, Vlan30
! C       172.16.8.32/27 is directly connected, Vlan10
! L       172.16.8.33/32 is directly connected, Vlan10
! C       172.16.8.64/28 is directly connected, Vlan99
! L       172.16.8.65/32 is directly connected, Vlan99
! C       172.16.8.96/30 is directly connected, GigabitEthernet0/1
! L       172.16.8.97/32 is directly connected, GigabitEthernet0/1
! C       172.16.8.108/32 is directly connected, Loopback0
!
! 7. Clinic Inter-VLAN Ping Verification Commands (execute from privileged exec)
! ------------------------------------------------------------------------------
! SW-D3# ping 172.16.8.36              ! Ping SRV-CACHE (Local Clinic EHR Server) -> Success rate 100 percent
! SW-D3# ping 172.16.8.42              ! Ping PC-CLINIC-CONSULT1 (VLAN 10 Clinical) -> Success rate 100 percent
! SW-D3# ping 172.16.8.10              ! Ping PC-CLINIC-ADM1 (VLAN 30 Admin) -> Success rate 100 percent
! SW-D3# ping 172.16.7.234             ! Ping PHONE-CLINIC-601 (VLAN 60 Voice) -> Success rate 100 percent
! SW-D3# ping 172.16.8.98              ! Ping Core Router R2 Gig0/0 Transit Link -> Success rate 100 percent
! SW-D3# ping 172.16.7.4               ! Ping Main Hospital SRV-CENTRAL across WAN -> Success rate 100 percent
!
! 8. Architecture Note on Clinic Single Point of Failure (SPOF)
! ------------------------------------------------------------------------------
! In this base topology, SW-D3 is the sole distribution switch for the Remote Spoke Clinic.
! If SW-D3 fails, all local inter-VLAN routing and uplink WAN connectivity to R2 ceases.
! To eliminate this SPOF, enable the SW-D4 High-Availability extension detailed in
! /configs/SW-D4/README.md and /docs/intervlan_hsrp_guide.md.
!
! 9. Security ACL Verification Commands & Hit Counter Audit
! ------------------------------------------------------------------------------
! Step 1: Clear ACL hit counters before initiating validation tests:
! SW-D3# clear access-list counters
!
! Step 2: Confirm inbound ACL bindings on Clinic SVIs:
! SW-D3# show ip interface Vlan10 | include Inbound access list
!   Inbound access list is ACL-CLINIC-CLINICAL-IN
! SW-D3# show ip interface Vlan30 | include Inbound access list
!   Inbound access list is ACL-CLINIC-ADMIN-IN
! SW-D3# show ip interface Vlan40 | include Inbound access list
!   Inbound access list is ACL-CLINIC-GUEST-IN
! SW-D3# show ip interface Vlan60 | include Inbound access list
!   Inbound access list is ACL-CLINIC-VOICE-IN
! SW-D3# show ip interface Vlan99 | include Inbound access list
!   Inbound access list is ACL-CLINIC-MGMT-IN
!
! Step 3: Inspect active access lists and packet match counters:
! SW-D3# show access-lists
! Extended IP access list ACL-CLINIC-CLINICAL-IN
!     10 permit udp any any eq bootps
!     20 permit udp any host 172.16.7.4 eq domain
!     30 permit tcp any host 172.16.7.4 eq domain
!     40 permit tcp any host 172.16.8.36 eq www (18 matches)
!     50 permit tcp any host 172.16.8.36 eq 443
!     60 permit tcp any host 172.16.7.4 eq www (10 matches)
!     70 permit tcp any host 172.16.7.4 eq 443
!     80 permit tcp any host 172.16.7.7 eq 104 (5 matches)
!     90 permit tcp any host 172.16.7.7 eq www
!     100 permit tcp any host 172.16.7.7 eq 443
!     110 permit tcp any any established (40 matches)
!     120 permit icmp any any echo (4 matches)
!     130 permit icmp any any echo-reply
!     140 deny ip any 172.16.8.0 0.0.0.31 log
!     150 deny ip any 172.16.6.128 0.0.0.127 log
!     160 deny ip any any log
! Extended IP access list ACL-CLINIC-GUEST-IN
!     10 permit udp any any eq bootps (2 matches)
!     20 permit udp any host 172.16.7.4 eq domain (8 matches)
!     30 permit tcp any host 172.16.7.4 eq domain
!     40 deny ip any 172.16.0.0 0.0.255.255 log (14 matches)
!     50 permit tcp any any eq www (32 matches)
!     60 permit tcp any any eq 443 (55 matches)
!     70 permit icmp any any echo
!     80 permit tcp any any established (68 matches)
!     90 deny ip any any log
! Standard IP access list ACL-VTY-SSH
!     10 permit 172.16.7.212
!     20 permit 172.16.8.75 (1 match)
!     30 deny any log
!
! 12. Quality of Service (QoS) Verification & Policy Status
! ------------------------------------------------------------------------------
! Step 1: Verify global MLS QoS status on remote distribution switch:
! SW-D3# show mls qos
!   QoS is enabled
!   QoS ip packet dscp rewrite is enabled
!
! Step 2: Confirm DSCP trust on routed uplink to R2:
! SW-D3# show mls qos interface GigabitEthernet0/1
!   GigabitEthernet0/1
!   trust state: trust dscp
!   trust mode: trust dscp
!   COS override: dis
!   default COS: 0
!   pass-through: none
!
! Step 3: Inspect SVI Ingress Service-Policy:
! SW-D3# show policy-map interface Vlan10
!   Vlan10 
!     Service-policy input: PM-DISTRO-MARK-INGRESS
!       Class-map: CM-DISTRO-VITALS (match-any)
!         20 packets
!         Match: access-group name ACL-MARK-CLINIC-VITALS
!         QoS Set
!           dscp ef
!       Class-map: CM-DISTRO-VOICE (match-any)
!         0 packets
!       Class-map: CM-DISTRO-IMAGING (match-any)
!         5 packets
!         Match: access-group name ACL-MARK-CLINIC-IMAGING
!         QoS Set
!           dscp af31
!       Class-map: CM-DISTRO-ADMIN (match-any)
!         8 packets
!         Match: access-group name ACL-MARK-CLINIC-ADMIN
!         QoS Set
!           dscp af21
!       Class-map: CM-DISTRO-GUEST (match-any)
!         14 packets
!         Match: access-group name ACL-MARK-CLINIC-GUEST
!         QoS Set
!           dscp cs1
!       Class-map: class-default (match-any)
!         0 packets
! [NOTE ON PACKET TRACER 8.x LIMITATION]
! In Packet Tracer 8.x, Catalyst 3560 accepts 'mls qos' and parses 'policy-map' syntax,
! but hardware queue scheduling and packet rate limiting are stubbed. Drop counters
! and strict LLQ serialization operate on Core Routers R1 and R2 across WAN serial links.
! ==============================================================================

```

### Appendix 13.7: Device Configuration — SW-D4

```ios
! ==============================================================================
! DEVICE:       SW-D4
! MODEL:        Cisco Catalyst 3560-24PS (Multilayer Layer-3 Switch)
! LOCATION:     Remote Spoke Clinic - Telecomm Equipment Closet (Rack B)
! ROLE:         Secondary Clinic Distribution Gateway (HA Extension Peer to SW-D3)
! UPLINK:       GigabitEthernet0/1 -> Core Router R2 GigabitEthernet0/1 (/30 Routed)
! CROSS-CONNECT:FastEthernet0/21 - 22 -> SW-D3 (EtherChannel Port-Channel 1)
! DOWNLINK:     FastEthernet0/24 -> SW-A5 GigabitEthernet0/2 (802.1Q Redundant Trunk)
! ==============================================================================

enable
configure terminal

! --- Device Identity & System Security ---
hostname SW-D4
no ip domain-lookup
ip domain-name hospital.local

banner motd ^C
================================================================================
  SW-D4 : Remote Spoke Clinic Secondary Distribution Switch (HA Extension)
  VIT Vellore - CN Project: Disaster-Resilient Smart Hospital Network
  UNAUTHORIZED ACCESS IS STRICTLY PROHIBITED. ALL SESSIONS MONITORED.
================================================================================
^C

! --- Management Authentication & Credential Encryption ---
enable secret class123
service password-encryption
username admin privilege 15 secret class123

! --- Cryptographic SSH Version 2 Configuration ---
crypto key generate rsa modulus 1024
ip ssh version 2
ip ssh time-out 60
ip ssh authentication-retries 3

! --- Infrastructure Hardening: Standard ACL for VTY Management ---
ip access-list standard ACL-VTY-SSH
 remark Permit Central Hospital NOC Management Console
 permit host 172.16.7.212
 remark Permit Remote Clinic Local Management Station
 permit host 172.16.8.75
 remark Deny all other administrative attempts with logging
 deny any log
exit

line con 0
 password cisco
 login
 logging synchronous
 exec-timeout 15 0
exit

line vty 0 4
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

line vty 5 15
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

! --- Disable Insecure / Unnecessary Management Services ---
no ip http server
no ip http secure-server

! --- Centralized Time Synchronization (NTP Client) ---
ntp server 172.16.7.4

! --- Centralized Logging (Syslog Client) ---
logging host 172.16.7.4
logging trap informational
logging buffered 4096 informational

! --- Enable Hardware Layer-3 IP Routing & Global Quality of Service ---
ip routing
mls qos

! --- VLAN Database Definition ---
vlan 10
 name Clinic_Clinical
vlan 30
 name Clinic_Admin
vlan 40
 name Clinic_Guest
vlan 60
 name Clinic_Voice
vlan 99
 name Management
vlan 999
 name Parking_Native
exit

! --- Spanning Tree Protocol: Rapid PVST+ Configuration ---
! SW-D4 is Root Primary for Admin/Guest/Mgmt (VLANs 30, 40, 99)
! SW-D4 is Root Secondary for Clinical/Voice (VLANs 10, 60)
spanning-tree mode rapid-pvst
spanning-tree vlan 30,40,99 root primary
spanning-tree vlan 10,60 root secondary

! --- Inter-Distribution EtherChannel (Port-Channel 1 to SW-D3) ---
interface range FastEthernet0/21 - 22
 description Inter_Distribution_EtherChannel_Member_to_SW-D3
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,30,40,60,99
 switchport nonegotiate
 channel-group 1 mode on
 no shutdown
exit

interface Port-channel 1
 description Aggregate_Trunk_CrossLink_to_SW-D3
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,30,40,60,99
 switchport nonegotiate
 mls qos trust dscp
 no shutdown
exit

! --- 802.1Q Distribution-to-Access Redundant Trunk Downlink to SW-A5 ---
interface FastEthernet0/24
 description Secondary_Trunk_Downlink_to_SW-A5_Gig0/2
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,30,40,60,99
 switchport nonegotiate
 no shutdown
exit

! --- Layer 3 Routed Uplink to Core Router R2 (/30 Transit Subnet) ---
interface GigabitEthernet0/1
 description Routed_Point_to_Point_Uplink_to_R2_Gig0/1
 no switchport
 ip address 172.16.8.114 255.255.255.252
 mls qos trust dscp
 no shutdown
exit

! --- Loopback 0 Management & OSPF Router-ID ---
interface Loopback0
 description OSPF_Router_ID_and_Management
 ip address 172.16.8.109 255.255.255.255
 no shutdown
exit

! --- Quality of Service (QoS): Ingress Classification ACLs (SW-D4) ---
ip access-list extended ACL-MARK-CLINIC-VITALS
 remark Class C1: Ingress Clinic Triage Telemetry to Central Server
 permit udp host 172.16.8.44 host 172.16.7.4
 permit udp host 172.16.7.4 host 172.16.8.44
exit

ip access-list extended ACL-MARK-CLINIC-VOICE
 remark Class C2: Ingress Clinic VoIP Bearer Audio & Signaling
 permit udp 172.16.7.224 0.0.0.31 any
 permit tcp 172.16.7.224 0.0.0.31 any
exit

ip access-list extended ACL-MARK-CLINIC-IMAGING
 remark Class C3: Ingress Clinic PACS DICOM Queries & Cache Replication
 permit tcp any host 172.16.7.7 eq 104
 permit tcp host 172.16.7.7 any eq 104
 permit tcp host 172.16.8.36 host 172.16.7.7
 permit tcp host 172.16.7.7 host 172.16.8.36
exit

ip access-list extended ACL-MARK-CLINIC-ADMIN
 remark Class C4: Ingress Clinic Admin EHR Queries & DNS
 permit tcp 172.16.8.0 0.0.0.31 host 172.16.7.4 eq www
 permit tcp 172.16.8.0 0.0.0.31 host 172.16.7.4 eq 443
 permit udp any host 172.16.7.4 eq domain
exit

ip access-list extended ACL-MARK-CLINIC-GUEST
 remark Class C5: Ingress Clinic Guest Scavenger Traffic
 permit ip 172.16.6.128 0.0.0.127 any
exit

! --- Quality of Service (QoS): MQC Ingress Class-Maps ---
class-map match-any CM-DISTRO-VITALS
 match access-group name ACL-MARK-CLINIC-VITALS
exit

class-map match-any CM-DISTRO-VOICE
 match access-group name ACL-MARK-CLINIC-VOICE
exit

class-map match-any CM-DISTRO-IMAGING
 match access-group name ACL-MARK-CLINIC-IMAGING
exit

class-map match-any CM-DISTRO-ADMIN
 match access-group name ACL-MARK-CLINIC-ADMIN
exit

class-map match-any CM-DISTRO-GUEST
 match access-group name ACL-MARK-CLINIC-GUEST
exit

! --- Quality of Service (QoS): MQC Ingress Marking Policy-Map ---
policy-map PM-DISTRO-MARK-INGRESS
 class CM-DISTRO-VITALS
  set dscp ef
 class CM-DISTRO-VOICE
  set dscp cs5
 class CM-DISTRO-IMAGING
  set dscp af31
 class CM-DISTRO-ADMIN
  set dscp af21
 class CM-DISTRO-GUEST
  set dscp cs1
 class class-default
  set dscp default
exit

! --- Inter-VLAN Routing: Switch Virtual Interfaces (SVIs) & HSRP v2 ---
! Group 1 (Clinical & Voice: VLANs 10, 60): SW-D4 is STANDBY (Priority 100, Preempt)
! Group 2 (Admin, Guest, Mgmt: VLANs 30, 40, 99): SW-D4 is ACTIVE (Priority 110, Preempt, Track Gi0/1 decr 20)
! DHCP Relay: ip helper-address points to Central DHCP Server SRV-CENTRAL (172.16.7.4)

! VLAN 10 : Clinic Clinical Wards (Subnet: 172.16.8.32/27, VIP: .33, SVI: .35 - STANDBY)
interface Vlan10
 description SVI_Clinic_Clinical_Gateway
 ip address 172.16.8.35 255.255.255.224
 ip helper-address 172.16.7.4
 service-policy input PM-DISTRO-MARK-INGRESS
 standby version 2
 standby 10 ip 172.16.8.33
 standby 10 priority 100
 standby 10 preempt
 no shutdown
exit

! VLAN 30 : Clinic Administration (Subnet: 172.16.8.0/27, VIP: .1, SVI: .3 - ACTIVE)
interface Vlan30
 description SVI_Clinic_Admin_Gateway
 ip address 172.16.8.3 255.255.255.224
 ip helper-address 172.16.7.4
 service-policy input PM-DISTRO-MARK-INGRESS
 standby version 2
 standby 30 ip 172.16.8.1
 standby 30 priority 110
 standby 30 preempt
 standby 30 track GigabitEthernet0/1 20
 no shutdown
exit

! VLAN 40 : Clinic Guest Wi-Fi (Subnet: 172.16.6.128/25, VIP: .129, SVI: .131 - ACTIVE)
interface Vlan40
 description SVI_Clinic_Guest_Gateway
 ip address 172.16.6.131 255.255.255.128
 ip helper-address 172.16.7.4
 service-policy input PM-DISTRO-MARK-INGRESS
 standby version 2
 standby 40 ip 172.16.6.129
 standby 40 priority 110
 standby 40 preempt
 standby 40 track GigabitEthernet0/1 20
 no shutdown
exit

! VLAN 60 : Clinic VoIP Telephony (Subnet: 172.16.7.224/27, VIP: .225, SVI: .227 - STANDBY)
interface Vlan60
 description SVI_Clinic_Voice_Gateway
 ip address 172.16.7.227 255.255.255.224
 ip helper-address 172.16.7.4
 service-policy input PM-DISTRO-MARK-INGRESS
 standby version 2
 standby 60 ip 172.16.7.225
 standby 60 priority 100
 standby 60 preempt
 no shutdown
exit

! VLAN 99 : Remote Clinic Management (Subnet: 172.16.8.64/28, VIP: .65, SVI: .67 - ACTIVE)
interface Vlan99
 description In_Band_Management_SVI_SW-D4
 ip address 172.16.8.67 255.255.255.240
 standby version 2
 standby 99 ip 172.16.8.65
 standby 99 priority 110
 standby 99 preempt
 standby 99 track GigabitEthernet0/1 20
 no shutdown
exit

! --- Static Default Route to Core Router R2 ---
ip route 0.0.0.0 0.0.0.0 172.16.8.113

! --- Security: Shutdown & Park All Unused Physical Interfaces in VLAN 999 ---
interface range FastEthernet0/1 - 20, FastEthernet0/23, GigabitEthernet0/2
 description Security_Unused_Port_Parked_in_VLAN999
 switchport mode access
 switchport access vlan 999
 shutdown
exit

end
write memory

! ==============================================================================
! VERIFICATION COMMANDS & EXPECTED OUTPUT (Cisco Packet Tracer 8.x)
! ==============================================================================
!
! 1. show vlan brief
! ------------------------------------------------------------------------------
! SW-D4# show vlan brief
! VLAN Name                             Status    Ports
! ---- -------------------------------- --------- -------------------------------
! 1    default                          active    
! 10   Clinic_Clinical                  active    
! 30   Clinic_Admin                     active    
! 40   Clinic_Guest                     active    
! 60   Clinic_Voice                     active    
! 99   Management                       active    
! 999  Parking_Native                   active    Fa0/1 - 20, Fa0/23, Gi0/2
!
! 2. show interfaces trunk
! ------------------------------------------------------------------------------
! SW-D4# show interfaces trunk
! Port        Mode         Encapsulation  Status        Native vlan
! Fa0/24      on           802.1q         trunking      999
! Po1         on           802.1q         trunking      999
!
! Port        Vlans allowed on trunk
! Fa0/24      10,30,40,60,99
! Po1         10,30,40,60,99
!
! 3. show spanning-tree summary
! ------------------------------------------------------------------------------
! SW-D4# show spanning-tree summary
! Switch is in rapid-pvst mode
! Root bridge for: VLAN0030, VLAN0040, VLAN0099
! Extended system ID is enabled
!
! 4. show etherchannel summary
! ------------------------------------------------------------------------------
! SW-D4# show etherchannel summary
! Group  Port-channel  Protocol    Ports
! ------+-------------+-----------+-----------------------------------------------
! 1      Po1(SU)          -        Fa0/21(P)   Fa0/22(P)
!
! 5. show ip interface brief | include Vlan
! ------------------------------------------------------------------------------
! SW-D4# show ip interface brief | include Vlan
! Vlan10                 172.16.8.35     YES manual up                    up
! Vlan30                 172.16.8.3      YES manual up                    up
! Vlan40                 172.16.6.131    YES manual up                    up
! Vlan60                 172.16.7.227    YES manual up                    up
! Vlan99                 172.16.8.67     YES manual up                    up
!
! 6. show standby brief
! ------------------------------------------------------------------------------
! SW-D4# show standby brief
!                      P indicates configured to preempt.
!                      |
! Interface   Grp  Pri P State   Active          Standby         Virtual IP
! Vl10        10   100 P Standby 172.16.8.34     local           172.16.8.33
! Vl30        30   110 P Active  local           172.16.8.2      172.16.8.1
! Vl40        40   110 P Active  local           172.16.6.130    172.16.6.129
! Vl60        60   100 P Standby 172.16.7.226    local           172.16.7.225
! Vl99        99   110 P Active  local           172.16.8.66     172.16.8.65
!
! 7. show ip route
! ------------------------------------------------------------------------------
! SW-D4# show ip route
! Gateway of last resort is 172.16.8.113 to network 0.0.0.0
!
! S*    0.0.0.0/0 [1/0] via 172.16.8.113
!       172.16.0.0/16 is variably subnetted, 11 subnets, 5 masks
! C        172.16.6.128/25 is directly connected, Vlan40
! L        172.16.6.131/32 is directly connected, Vlan40
! C        172.16.7.224/27 is directly connected, Vlan60
! L        172.16.7.227/32 is directly connected, Vlan60
! C        172.16.8.0/27 is directly connected, Vlan30
! L        172.16.8.3/32 is directly connected, Vlan30
! C        172.16.8.32/27 is directly connected, Vlan10
! L        172.16.8.35/32 is directly connected, Vlan10
! C        172.16.8.64/28 is directly connected, Vlan99
! L        172.16.8.67/32 is directly connected, Vlan99
! C        172.16.8.112/30 is directly connected, GigabitEthernet0/1
! L        172.16.8.114/32 is directly connected, GigabitEthernet0/1
! C        172.16.8.109/32 is directly connected, Loopback0
!
! 8. Clinic Inter-VLAN Ping Verification Commands (execute from privileged exec)
! ------------------------------------------------------------------------------
! SW-D4# ping 172.16.8.36              ! Ping SRV-CACHE (Local Clinic EHR Server) -> Success rate 100 percent
! SW-D4# ping 172.16.8.10              ! Ping PC-CLINIC-ADM1 (VLAN 30 Admin) -> Success rate 100 percent
! SW-D4# ping 172.16.7.234             ! Ping PHONE-CLINIC-601 (VLAN 60 Voice) -> Success rate 100 percent
! SW-D4# ping 172.16.8.113             ! Ping Core Router R2 Gig0/1 Transit Link -> Success rate 100 percent
!
! 9. Quality of Service (QoS) Verification & Policy Status
! ------------------------------------------------------------------------------
! Step 1: Verify global MLS QoS status on remote distribution switch:
! SW-D4# show mls qos
!   QoS is enabled
!   QoS ip packet dscp rewrite is enabled
!
! Step 2: Confirm DSCP trust on routed uplink to R2:
! SW-D4# show mls qos interface GigabitEthernet0/1
!   GigabitEthernet0/1
!   trust state: trust dscp
!   trust mode: trust dscp
!   COS override: dis
!   default COS: 0
!   pass-through: none
!
! Step 3: Inspect SVI Ingress Service-Policy:
! SW-D4# show policy-map interface Vlan30
!   Vlan30 
!     Service-policy input: PM-DISTRO-MARK-INGRESS
!       Class-map: CM-DISTRO-ADMIN (match-any)
!         10 packets
!         Match: access-group name ACL-MARK-CLINIC-ADMIN
!         QoS Set
!           dscp af21
!       Class-map: CM-DISTRO-GUEST (match-any)
!         0 packets
!       Class-map: class-default (match-any)
!         0 packets
! [NOTE ON PACKET TRACER 8.x LIMITATION]
! In Packet Tracer 8.x, Catalyst 3560 accepts 'mls qos' and parses 'policy-map' syntax,
! but hardware queue scheduling and packet rate limiting are stubbed. Drop counters
! and strict LLQ serialization operate on Core Routers R1 and R2 across WAN serial links.
! ==============================================================================

```

### Appendix 13.8: Device Configuration — SW-A1

```ios
! ==============================================================================
! DEVICE:       SW-A1
! MODEL:        Cisco Catalyst 2960-24TT (Layer-2 Access Switch)
! LOCATION:     Main Hospital Campus - ICU Floor Wiring Closet
! ROLE:         Access Layer Switch - ICU Ward Telemetry & Nursing Station
! UPLINKS:      Gig0/1 -> SW-D1 Fa0/1 (Primary Trunk), Gig0/2 -> SW-D2 Fa0/1 (Secondary Trunk)
! DOWNLINKS:    Fa0/1 - 3 (SBC-ICU-101 to 103), Fa0/4 (PC-ICU-NURSE),
!               Fa0/5 - 6 (PC-ICU-DOC1 & DOC2), Fa0/7 (PHONE-ICU-601)
! ==============================================================================

enable
configure terminal

! --- Device Identity & System Security ---
hostname SW-A1
no ip domain-lookup
ip domain-name hospital.local

banner motd ^C
================================================================================
  SW-A1 : Main Hospital ICU Ward Layer-2 Access Switch
  VIT Vellore - CN Project: Disaster-Resilient Smart Hospital Network
  UNAUTHORIZED ACCESS IS STRICTLY PROHIBITED. ALL SESSIONS MONITORED.
================================================================================
^C

! --- Management Authentication & Credential Encryption ---
enable secret class123
service password-encryption
username admin privilege 15 secret class123

! --- Cryptographic SSH Version 2 Configuration ---
crypto key generate rsa modulus 1024
ip ssh version 2
ip ssh time-out 60
ip ssh authentication-retries 3

! --- Infrastructure Hardening: Standard ACL for VTY Management ---
ip access-list standard ACL-VTY-SSH
 remark Permit Central Hospital NOC Management Console
 permit host 172.16.7.212
 remark Permit Remote Clinic Local Management Station
 permit host 172.16.8.75
 remark Deny all other administrative attempts with logging
 deny any log
exit

line con 0
 password cisco
 login
 logging synchronous
 exec-timeout 15 0
exit

line vty 0 4
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

line vty 5 15
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

! --- Disable Insecure / Unnecessary Management Services ---
no ip http server
no ip http secure-server

! --- Centralized Time Synchronization (NTP Client) ---
ntp server 172.16.7.4

! --- Centralized Logging (Syslog Client) ---
logging host 172.16.7.4
logging trap informational
logging buffered 4096 informational

! --- VLAN Database Definition ---
vlan 10
 name ICU_Clinical
vlan 60
 name VoIP_Voice
vlan 99
 name Management
vlan 999
 name Parking_Native
exit

! --- Spanning Tree Protocol: Rapid PVST+ ---
spanning-tree mode rapid-pvst

! --- 802.1Q Redundant Trunk Uplinks to Distribution Layer ---
! On Catalyst 2960, dot1q is the only encapsulation, so 'switchport mode trunk' is direct.
! Allowed VLANs strictly limited to ICU traffic: 10 (Data), 60 (Voice), 99 (Management).
! DTP disabled via 'switchport nonegotiate'.

! Primary Uplink to SW-D1 (Active forwarding path for VLAN 10 Root)
interface GigabitEthernet0/1
 description Primary_Trunk_Uplink_to_SW-D1_Fa0/1
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,60,99
 switchport nonegotiate
 no shutdown
exit

! Secondary Uplink to SW-D2 (PVST+ Alternate/Blocking path)
interface GigabitEthernet0/2
 description Secondary_Trunk_Uplink_to_SW-D2_Fa0/1
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,60,99
 switchport nonegotiate
 no shutdown
exit

! --- Host-Facing Ports: ICU Bedside Telemetry Sensors & Nursing Workstations ---
! Life-critical clinical monitoring:
! - PortFast enabled for instant link transitions (bypasses 30s listening/learning)
! - BPDU Guard enabled to prevent rogue switch attachments
! - Port Security enabled: Max 2 MACs, sticky learning
! - Violation mode RESTRICT (Drops unauthorized frames and increments SNMP trap counter
!   WITHOUT err-disabling the port, preventing accidental patient monitor blackout)

interface range FastEthernet0/1 - 6
 switchport mode access
 switchport access vlan 10
 spanning-tree portfast
 spanning-tree bpduguard enable
 switchport port-security
 switchport port-security maximum 2
 switchport port-security mac-address sticky
 switchport port-security violation restrict
 no shutdown
exit

! Specific interface descriptions for audit traceability
interface FastEthernet0/1
 description Bedside_IoT_Telemetry_Node_Bed101_(SBC-ICU-101)
exit

interface FastEthernet0/2
 description Bedside_IoT_Telemetry_Node_Bed102_(SBC-ICU-102)
exit

interface FastEthernet0/3
 description Bedside_IoT_Telemetry_Node_Bed103_(SBC-ICU-103)
exit

interface FastEthernet0/4
 description ICU_Central_Nursing_Monitoring_Station_(PC-ICU-NURSE)
exit

interface FastEthernet0/5
 description ICU_Attending_Physician_Workstation_1_(PC-ICU-DOC1)
exit

interface FastEthernet0/6
 description ICU_Attending_Physician_Workstation_2_(PC-ICU-DOC2)
exit

! --- Cisco 7960 IP Phone Port (Voice VLAN 60 + Data Access VLAN 10) ---
interface FastEthernet0/7
 description ICU_Nursing_Station_VoIP_Phone_(PHONE-ICU-601)
 switchport mode access
 switchport access vlan 10
 switchport voice vlan 60
 spanning-tree portfast
 spanning-tree bpduguard enable
 no shutdown
exit

! --- In-Band Management SVI (VLAN 99) ---
interface Vlan99
 description In_Band_Management_SVI_SW-A1
 ip address 172.16.7.202 255.255.255.224
 no shutdown
exit

! Default Gateway pointing to HSRP Virtual IP (.1) on Distribution Tier
ip default-gateway 172.16.7.193

! --- Security: Shutdown & Park All Unused Physical Interfaces in VLAN 999 ---
interface range FastEthernet0/8 - 24
 description Security_Unused_Port_Parked_in_VLAN999
 switchport mode access
 switchport access vlan 999
 shutdown
exit

end
write memory

! ==============================================================================
! VERIFICATION COMMANDS & EXPECTED OUTPUT (Cisco Packet Tracer 8.x)
! ==============================================================================
!
! 1. show vlan brief
! ------------------------------------------------------------------------------
! SW-A1# show vlan brief
! VLAN Name                             Status    Ports
! ---- -------------------------------- --------- -------------------------------
! 1    default                          active    
! 10   ICU_Clinical                     active    Fa0/1, Fa0/2, Fa0/3, Fa0/4,
!                                                 Fa0/5, Fa0/6, Fa0/7
! 60   VoIP_Voice                       active    Fa0/7
! 99   Management                       active    
! 999  Parking_Native                   active    Fa0/8, Fa0/9, Fa0/10, Fa0/11,
!                                                 Fa0/12, Fa0/13, Fa0/14, Fa0/15,
!                                                 Fa0/16, Fa0/17, Fa0/18, Fa0/19,
!                                                 Fa0/20, Fa0/21, Fa0/22, Fa0/23,
!                                                 Fa0/24
!
! 2. show interfaces trunk
! ------------------------------------------------------------------------------
! SW-A1# show interfaces trunk
! Port        Mode         Encapsulation  Status        Native vlan
! Gi0/1       on           802.1q         trunking      999
! Gi0/2       on           802.1q         trunking      999
!
! Port        Vlans allowed on trunk
! Gi0/1       10,60,99
! Gi0/2       10,60,99
!
! 3. show spanning-tree summary
! ------------------------------------------------------------------------------
! SW-A1# show spanning-tree summary
! Switch is in rapid-pvst mode
! Root bridge for: none
! Extended system ID is enabled
! Portfast Default                     is disabled
! PortFast BPDU Guard Default          is disabled
!
! SW-A1# show spanning-tree vlan 10
! VLAN0010
!   Spanning tree enabled protocol rstp
!   Root ID    Priority    24586
!              Address     0001.42A1.B101 (SW-D1)
!              Cost        4
!              Port        25 (GigabitEthernet0/1)
!   Interface           Role Sts Cost      Prio.Nbr Type
!   ------------------- ---- --- --------- -------- --------------------------------
!   Gi0/1               Root FWD 4         128.25   P2p
!   Gi0/2               Altn BLK 4         128.26   P2p
!   Fa0/1               Desg FWD 19        128.1    P2p Edge
!   Fa0/2               Desg FWD 19        128.2    P2p Edge
!   Fa0/3               Desg FWD 19        128.3    P2p Edge
!   Fa0/4               Desg FWD 19        128.4    P2p Edge
!   Fa0/5               Desg FWD 19        128.5    P2p Edge
!   Fa0/6               Desg FWD 19        128.6    P2p Edge
!   Fa0/7               Desg FWD 19        128.7    P2p Edge
!
! 4. show port-security
! ------------------------------------------------------------------------------
! SW-A1# show port-security
! Secure Port  MaxSecureAddr  CurrentAddr  SecurityViolation  Security Action
!                (Count)       (Count)          (Count)
! ---------------------------------------------------------------------------
! Fa0/1              2             1                0             Restrict
! Fa0/2              2             1                0             Restrict
! Fa0/3              2             1                0             Restrict
! Fa0/4              2             1                0             Restrict
! Fa0/5              2             1                0             Restrict
! Fa0/6              2             1                0             Restrict
! ---------------------------------------------------------------------------
! Total Addresses in System (including duplications) : 6
! Max Addresses limit in System                      : 1024
!
! 5. show ip interface brief | include Vlan
! ------------------------------------------------------------------------------
! SW-A1# show ip interface brief | include Vlan
! Vlan99                 172.16.7.202    YES manual up                    up
! ==============================================================================

```

### Appendix 13.9: Device Configuration — SW-A2

```ios
! ==============================================================================
! DEVICE:       SW-A2
! MODEL:        Cisco Catalyst 2960-24TT (Layer-2 Access Switch)
! LOCATION:     Main Hospital Campus - Surgical Suites Wiring Closet
! ROLE:         Access Layer Switch - Operating Theatres & Surgical Workstations
! UPLINKS:      Gig0/1 -> SW-D1 Fa0/2 (Trunk), Gig0/2 -> SW-D2 Fa0/2 (Trunk)
! DOWNLINKS:    Fa0/1 - 2 (SBC-SURG-201 & 202), Fa0/3 - 5 (PC-THEATRE-1 to 3),
!               Fa0/7 (PHONE-SURG-602)
! ==============================================================================

enable
configure terminal

! --- Device Identity & System Security ---
hostname SW-A2
no ip domain-lookup
ip domain-name hospital.local

banner motd ^C
================================================================================
  SW-A2 : Main Hospital Surgical Suites Layer-2 Access Switch
  VIT Vellore - CN Project: Disaster-Resilient Smart Hospital Network
  UNAUTHORIZED ACCESS IS STRICTLY PROHIBITED. ALL SESSIONS MONITORED.
================================================================================
^C

! --- Management Authentication & Credential Encryption ---
enable secret class123
service password-encryption
username admin privilege 15 secret class123

! --- Cryptographic SSH Version 2 Configuration ---
crypto key generate rsa modulus 1024
ip ssh version 2
ip ssh time-out 60
ip ssh authentication-retries 3

! --- Infrastructure Hardening: Standard ACL for VTY Management ---
ip access-list standard ACL-VTY-SSH
 remark Permit Central Hospital NOC Management Console
 permit host 172.16.7.212
 remark Permit Remote Clinic Local Management Station
 permit host 172.16.8.75
 remark Deny all other administrative attempts with logging
 deny any log
exit

line con 0
 password cisco
 login
 logging synchronous
 exec-timeout 15 0
exit

line vty 0 4
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

line vty 5 15
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

! --- Disable Insecure / Unnecessary Management Services ---
no ip http server
no ip http secure-server

! --- Centralized Time Synchronization (NTP Client) ---
ntp server 172.16.7.4

! --- Centralized Logging (Syslog Client) ---
logging host 172.16.7.4
logging trap informational
logging buffered 4096 informational

! --- VLAN Database Definition ---
vlan 20
 name Surgery_Theatre
vlan 60
 name VoIP_Voice
vlan 99
 name Management
vlan 999
 name Parking_Native
exit

! --- Spanning Tree Protocol: Rapid PVST+ ---
spanning-tree mode rapid-pvst

! --- 802.1Q Redundant Trunk Uplinks to Distribution Layer ---
! Allowed VLANs strictly limited to Surgery traffic: 20 (Data), 60 (Voice), 99 (Management).
! DTP disabled via 'switchport nonegotiate'.

! Uplink to SW-D1 (PVST+ Alternate path for VLAN 20; Active for VLAN 99)
interface GigabitEthernet0/1
 description Trunk_Uplink_to_SW-D1_Fa0/2
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 20,60,99
 switchport nonegotiate
 no shutdown
exit

! Uplink to SW-D2 (Active Forwarding path for VLAN 20 Root)
interface GigabitEthernet0/2
 description Trunk_Uplink_to_SW-D2_Fa0/2
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 20,60,99
 switchport nonegotiate
 no shutdown
exit

! --- Host-Facing Ports: Surgical Telemetry & PACS DICOM Viewer Stations ---
! OR 1 and OR 2 Telemetry Nodes (SBC-SURG-201 and 202):
! - PortFast enabled for zero STP listening/learning delay
! - BPDU Guard enabled
! - Port Security: Max 2 MACs, sticky learning, VIOLATION RESTRICT (no patient telemetry shutdown)
interface range FastEthernet0/1 - 2
 switchport mode access
 switchport access vlan 20
 spanning-tree portfast
 spanning-tree bpduguard enable
 switchport port-security
 switchport port-security maximum 2
 switchport port-security mac-address sticky
 switchport port-security violation restrict
 no shutdown
exit

interface FastEthernet0/1
 description OR1_Anesthesia_and_Ventilator_Telemetry_(SBC-SURG-201)
exit

interface FastEthernet0/2
 description OR2_Surgical_Vital_Signs_Telemetry_(SBC-SURG-202)
exit

! High-Resolution Operating Theatre PACS DICOM Viewers & Surgical Consoles
interface range FastEthernet0/3 - 5
 switchport mode access
 switchport access vlan 20
 spanning-tree portfast
 spanning-tree bpduguard enable
 no shutdown
exit

interface FastEthernet0/3
 description Operating_Theatre_1_PACS_DICOM_Viewer_(PC-THEATRE-1)
exit

interface FastEthernet0/4
 description Operating_Theatre_2_PACS_DICOM_Viewer_(PC-THEATRE-2)
exit

interface FastEthernet0/5
 description Surgical_Head_Consultation_and_Telemetry_Display_(PC-THEATRE-3)
exit

! --- Cisco 7960 IP Phone Port (Voice VLAN 60 + Data Access VLAN 20) ---
interface FastEthernet0/7
 description Surgical_Suite_Reception_VoIP_Phone_(PHONE-SURG-602)
 switchport mode access
 switchport access vlan 20
 switchport voice vlan 60
 spanning-tree portfast
 spanning-tree bpduguard enable
 no shutdown
exit

! --- In-Band Management SVI (VLAN 99) ---
interface Vlan99
 description In_Band_Management_SVI_SW-A2
 ip address 172.16.7.203 255.255.255.224
 no shutdown
exit

! Default Gateway pointing to HSRP Virtual IP (.1) on Distribution Tier
ip default-gateway 172.16.7.193

! --- Security: Shutdown & Park All Unused Physical Interfaces in VLAN 999 ---
interface range FastEthernet0/6, FastEthernet0/8 - 24
 description Security_Unused_Port_Parked_in_VLAN999
 switchport mode access
 switchport access vlan 999
 shutdown
exit

end
write memory

! ==============================================================================
! VERIFICATION COMMANDS & EXPECTED OUTPUT (Cisco Packet Tracer 8.x)
! ==============================================================================
!
! 1. show vlan brief
! ------------------------------------------------------------------------------
! SW-A2# show vlan brief
! VLAN Name                             Status    Ports
! ---- -------------------------------- --------- -------------------------------
! 1    default                          active    
! 20   Surgery_Theatre                  active    Fa0/1, Fa0/2, Fa0/3, Fa0/4,
!                                                 Fa0/5, Fa0/7
! 60   VoIP_Voice                       active    Fa0/7
! 99   Management                       active    
! 999  Parking_Native                   active    Fa0/6, Fa0/8, Fa0/9, Fa0/10,
!                                                 Fa0/11, Fa0/12, Fa0/13, Fa0/14,
!                                                 Fa0/15, Fa0/16, Fa0/17, Fa0/18,
!                                                 Fa0/19, Fa0/20, Fa0/21, Fa0/22,
!                                                 Fa0/23, Fa0/24
!
! 2. show interfaces trunk
! ------------------------------------------------------------------------------
! SW-A2# show interfaces trunk
! Port        Mode         Encapsulation  Status        Native vlan
! Gi0/1       on           802.1q         trunking      999
! Gi0/2       on           802.1q         trunking      999
!
! Port        Vlans allowed on trunk
! Gi0/1       20,60,99
! Gi0/2       20,60,99
!
! 3. show spanning-tree vlan 20
! ------------------------------------------------------------------------------
! SW-A2# show spanning-tree vlan 20
! VLAN0020
!   Spanning tree enabled protocol rstp
!   Root ID    Priority    24596
!              Address     0001.42A1.B202 (SW-D2)
!              Cost        4
!              Port        26 (GigabitEthernet0/2)
!   Interface           Role Sts Cost      Prio.Nbr Type
!   ------------------- ---- --- --------- -------- --------------------------------
!   Gi0/1               Altn BLK 4         128.25   P2p
!   Gi0/2               Root FWD 4         128.26   P2p
!   Fa0/1               Desg FWD 19        128.1    P2p Edge
!   Fa0/2               Desg FWD 19        128.2    P2p Edge
!   Fa0/3               Desg FWD 19        128.3    P2p Edge
!   Fa0/4               Desg FWD 19        128.4    P2p Edge
!   Fa0/5               Desg FWD 19        128.5    P2p Edge
!   Fa0/7               Desg FWD 19        128.7    P2p Edge
!
! 4. show port-security
! ------------------------------------------------------------------------------
! SW-A2# show port-security
! Secure Port  MaxSecureAddr  CurrentAddr  SecurityViolation  Security Action
!                (Count)       (Count)          (Count)
! ---------------------------------------------------------------------------
! Fa0/1              2             1                0             Restrict
! Fa0/2              2             1                0             Restrict
! ---------------------------------------------------------------------------
!
! 5. show ip interface brief | include Vlan
! ------------------------------------------------------------------------------
! SW-A2# show ip interface brief | include Vlan
! Vlan99                 172.16.7.203    YES manual up                    up
! ==============================================================================

```

### Appendix 13.10: Device Configuration — SW-A3

```ios
! ==============================================================================
! DEVICE:       SW-A3
! MODEL:        Cisco Catalyst 2960-24TT (Layer-2 Access Switch)
! LOCATION:     Main Hospital Campus - Administration Floor Wiring Closet
! ROLE:         Access Layer Switch - Admissions, Billing, Records & NOC Management
! UPLINKS:      Gig0/1 -> SW-D2 Fa0/3 (Trunk), Gig0/2 -> SW-D1 Fa0/3 (Trunk)
! DOWNLINKS:    Fa0/1 - 3 (PC-ADMIN-301 to 303), Fa0/7 (PHONE-ADMIN-603),
!               Fa0/20 (PC-NOC-MGT)
! ==============================================================================

enable
configure terminal

! --- Device Identity & System Security ---
hostname SW-A3
no ip domain-lookup
ip domain-name hospital.local

banner motd ^C
================================================================================
  SW-A3 : Main Hospital Administration Layer-2 Access Switch
  VIT Vellore - CN Project: Disaster-Resilient Smart Hospital Network
  UNAUTHORIZED ACCESS IS STRICTLY PROHIBITED. ALL SESSIONS MONITORED.
================================================================================
^C

! --- Management Authentication & Credential Encryption ---
enable secret class123
service password-encryption
username admin privilege 15 secret class123

! --- Cryptographic SSH Version 2 Configuration ---
crypto key generate rsa modulus 1024
ip ssh version 2
ip ssh time-out 60
ip ssh authentication-retries 3

! --- Infrastructure Hardening: Standard ACL for VTY Management ---
ip access-list standard ACL-VTY-SSH
 remark Permit Central Hospital NOC Management Console
 permit host 172.16.7.212
 remark Permit Remote Clinic Local Management Station
 permit host 172.16.8.75
 remark Deny all other administrative attempts with logging
 deny any log
exit

line con 0
 password cisco
 login
 logging synchronous
 exec-timeout 15 0
exit

line vty 0 4
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

line vty 5 15
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

! --- Disable Insecure / Unnecessary Management Services ---
no ip http server
no ip http secure-server

! --- Centralized Time Synchronization (NTP Client) ---
ntp server 172.16.7.4

! --- Centralized Logging (Syslog Client) ---
logging host 172.16.7.4
logging trap informational
logging buffered 4096 informational

! --- VLAN Database Definition ---
vlan 30
 name Administration
vlan 60
 name VoIP_Voice
vlan 99
 name Management
vlan 999
 name Parking_Native
exit

! --- Spanning Tree Protocol: Rapid PVST+ ---
spanning-tree mode rapid-pvst

! --- 802.1Q Redundant Trunk Uplinks to Distribution Layer ---
! Allowed VLANs strictly limited to Admin traffic: 30 (Data), 60 (Voice), 99 (Management).
! DTP disabled via 'switchport nonegotiate'.

! Uplink to SW-D2 (Secondary path for VLAN 30 Root)
interface GigabitEthernet0/1
 description Trunk_Uplink_to_SW-D2_Fa0/3
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 30,60,99
 switchport nonegotiate
 no shutdown
exit

! Uplink to SW-D1 (Active Forwarding path for VLAN 30 Root)
interface GigabitEthernet0/2
 description Trunk_Uplink_to_SW-D1_Fa0/3
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 30,60,99
 switchport nonegotiate
 no shutdown
exit

! --- Host-Facing Ports: Administration & Billing Workstations ---
! Enterprise Administrative Security Policy:
! - PortFast enabled for instant workstation DHCP lease acquisition
! - BPDU Guard enabled
! - Port Security enabled: Max 2 MACs, sticky learning
! - VIOLATION SHUTDOWN: Immediately err-disables port if unauthorized hub or laptop
!   is attached, strictly protecting sensitive billing and patient financial records.
interface range FastEthernet0/1 - 3
 switchport mode access
 switchport access vlan 30
 spanning-tree portfast
 spanning-tree bpduguard enable
 switchport port-security
 switchport port-security maximum 2
 switchport port-security mac-address sticky
 switchport port-security violation shutdown
 no shutdown
exit

interface FastEthernet0/1
 description Admissions_and_Patient_Billing_Terminal_(PC-ADMIN-301)
exit

interface FastEthernet0/2
 description Medical_Records_Administration_Terminal_(PC-ADMIN-302)
exit

interface FastEthernet0/3
 description Hospital_Executive_Director_Workstation_(PC-ADMIN-303)
exit

! --- Network Operations Center (NOC) In-Band Management Console (VLAN 99) ---
interface FastEthernet0/20
 description Network_Operations_Center_Console_(PC-NOC-MGT)
 switchport mode access
 switchport access vlan 99
 spanning-tree portfast
 spanning-tree bpduguard enable
 switchport port-security
 switchport port-security maximum 2
 switchport port-security mac-address sticky
 switchport port-security violation shutdown
 no shutdown
exit

! --- Cisco 7960 IP Phone Port (Voice VLAN 60 + Data Access VLAN 30) ---
interface FastEthernet0/7
 description Admin_Front_Desk_VoIP_Phone_(PHONE-ADMIN-603)
 switchport mode access
 switchport access vlan 30
 switchport voice vlan 60
 spanning-tree portfast
 spanning-tree bpduguard enable
 no shutdown
exit

! --- In-Band Management SVI (VLAN 99) ---
interface Vlan99
 description In_Band_Management_SVI_SW-A3
 ip address 172.16.7.204 255.255.255.224
 no shutdown
exit

! Default Gateway pointing to HSRP Virtual IP (.1) on Distribution Tier
ip default-gateway 172.16.7.193

! --- Security: Shutdown & Park All Unused Physical Interfaces in VLAN 999 ---
interface range FastEthernet0/4 - 6, FastEthernet0/8 - 19, FastEthernet0/21 - 24
 description Security_Unused_Port_Parked_in_VLAN999
 switchport mode access
 switchport access vlan 999
 shutdown
exit

end
write memory

! ==============================================================================
! VERIFICATION COMMANDS & EXPECTED OUTPUT (Cisco Packet Tracer 8.x)
! ==============================================================================
!
! 1. show vlan brief
! ------------------------------------------------------------------------------
! SW-A3# show vlan brief
! VLAN Name                             Status    Ports
! ---- -------------------------------- --------- -------------------------------
! 1    default                          active    
! 30   Administration                   active    Fa0/1, Fa0/2, Fa0/3, Fa0/7
! 60   VoIP_Voice                       active    Fa0/7
! 99   Management                       active    Fa0/20
! 999  Parking_Native                   active    Fa0/4, Fa0/5, Fa0/6, Fa0/8,
!                                                 Fa0/9, Fa0/10, Fa0/11, Fa0/12,
!                                                 Fa0/13, Fa0/14, Fa0/15, Fa0/16,
!                                                 Fa0/17, Fa0/18, Fa0/19, Fa0/21,
!                                                 Fa0/22, Fa0/23, Fa0/24
!
! 2. show interfaces trunk
! ------------------------------------------------------------------------------
! SW-A3# show interfaces trunk
! Port        Mode         Encapsulation  Status        Native vlan
! Gi0/1       on           802.1q         trunking      999
! Gi0/2       on           802.1q         trunking      999
!
! Port        Vlans allowed on trunk
! Gi0/1       30,60,99
! Gi0/2       30,60,99
!
! 3. show spanning-tree vlan 30
! ------------------------------------------------------------------------------
! SW-A3# show spanning-tree vlan 30
! VLAN0030
!   Spanning tree enabled protocol rstp
!   Root ID    Priority    24606
!              Address     0001.42A1.B101 (SW-D1)
!              Cost        4
!              Port        26 (GigabitEthernet0/2)
!   Interface           Role Sts Cost      Prio.Nbr Type
!   ------------------- ---- --- --------- -------- --------------------------------
!   Gi0/1               Altn BLK 4         128.25   P2p
!   Gi0/2               Root FWD 4         128.26   P2p
!   Fa0/1               Desg FWD 19        128.1    P2p Edge
!   Fa0/2               Desg FWD 19        128.2    P2p Edge
!   Fa0/3               Desg FWD 19        128.3    P2p Edge
!   Fa0/7               Desg FWD 19        128.7    P2p Edge
!
! 4. show port-security
! ------------------------------------------------------------------------------
! SW-A3# show port-security
! Secure Port  MaxSecureAddr  CurrentAddr  SecurityViolation  Security Action
!                (Count)       (Count)          (Count)
! ---------------------------------------------------------------------------
! Fa0/1              2             1                0             Shutdown
! Fa0/2              2             1                0             Shutdown
! Fa0/3              2             1                0             Shutdown
! Fa0/20             2             1                0             Shutdown
! ---------------------------------------------------------------------------
!
! 5. show ip interface brief | include Vlan
! ------------------------------------------------------------------------------
! SW-A3# show ip interface brief | include Vlan
! Vlan99                 172.16.7.204    YES manual up                    up
! ==============================================================================

```

### Appendix 13.11: Device Configuration — SW-A4

```ios
! ==============================================================================
! DEVICE:       SW-A4
! MODEL:        Cisco Catalyst 2960-24TT (Layer-2 Access Switch)
! LOCATION:     Main Hospital Campus - Outpatient / Guest Lobby Wiring Closet
! ROLE:         Access Layer Switch - Guest Wi-Fi Network Access Point
! UPLINKS:      Gig0/1 -> SW-D2 Fa0/4 (Trunk), Gig0/2 -> SW-D1 Fa0/4 (Trunk)
! DOWNLINKS:    Fa0/10 -> AP-GUEST (Guest Wi-Fi Access Point)
! ==============================================================================

enable
configure terminal

! --- Device Identity & System Security ---
hostname SW-A4
no ip domain-lookup
ip domain-name hospital.local

banner motd ^C
================================================================================
  SW-A4 : Main Hospital Guest Wi-Fi Layer-2 Access Switch
  VIT Vellore - CN Project: Disaster-Resilient Smart Hospital Network
  UNAUTHORIZED ACCESS IS STRICTLY PROHIBITED. ALL SESSIONS MONITORED.
================================================================================
^C

! --- Management Authentication & Credential Encryption ---
enable secret class123
service password-encryption
username admin privilege 15 secret class123

! --- Cryptographic SSH Version 2 Configuration ---
crypto key generate rsa modulus 1024
ip ssh version 2
ip ssh time-out 60
ip ssh authentication-retries 3

! --- Infrastructure Hardening: Standard ACL for VTY Management ---
ip access-list standard ACL-VTY-SSH
 remark Permit Central Hospital NOC Management Console
 permit host 172.16.7.212
 remark Permit Remote Clinic Local Management Station
 permit host 172.16.8.75
 remark Deny all other administrative attempts with logging
 deny any log
exit

line con 0
 password cisco
 login
 logging synchronous
 exec-timeout 15 0
exit

line vty 0 4
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

line vty 5 15
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

! --- Disable Insecure / Unnecessary Management Services ---
no ip http server
no ip http secure-server

! --- Centralized Time Synchronization (NTP Client) ---
ntp server 172.16.7.4

! --- Centralized Logging (Syslog Client) ---
logging host 172.16.7.4
logging trap informational
logging buffered 4096 informational

! --- VLAN Database Definition ---
vlan 40
 name Guest_WiFi
vlan 99
 name Management
vlan 999
 name Parking_Native
exit

! --- Spanning Tree Protocol: Rapid PVST+ ---
spanning-tree mode rapid-pvst

! --- 802.1Q Redundant Trunk Uplinks to Distribution Layer ---
! Allowed VLANs strictly limited to Guest Wi-Fi traffic: 40 (Guest Data), 99 (Management).
! DTP disabled via 'switchport nonegotiate'.

! Uplink to SW-D2 (Active Forwarding path for VLAN 40 Root)
interface GigabitEthernet0/1
 description Primary_Trunk_Uplink_to_SW-D2_Fa0/4
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 40,99
 switchport nonegotiate
 no shutdown
exit

! Uplink to SW-D1 (Secondary Standby path for VLAN 40)
interface GigabitEthernet0/2
 description Secondary_Trunk_Uplink_to_SW-D1_Fa0/4
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 40,99
 switchport nonegotiate
 no shutdown
exit

! --- Host-Facing Port: Guest Wi-Fi Access Point (AP-GUEST) ---
! Connected to AccessPoint-PT in Outpatient Waiting Lobby:
! - PortFast enabled for instant AP association
! - BPDU Guard enabled to protect against unauthorized bridge injection
! - Port Security is NOT configured on AP trunk/access links to allow multiple
!   visitor MAC addresses to associate wirelessly over RF.
interface FastEthernet0/10
 description Guest_WiFi_Access_Point_Uplink_(AP-GUEST)
 switchport mode access
 switchport access vlan 40
 spanning-tree portfast
 spanning-tree bpduguard enable
 no cdp enable
 no shutdown
exit

! --- In-Band Management SVI (VLAN 99) ---
interface Vlan99
 description In_Band_Management_SVI_SW-A4
 ip address 172.16.7.205 255.255.255.224
 no shutdown
exit

! Default Gateway pointing to HSRP Virtual IP (.1) on Distribution Tier
ip default-gateway 172.16.7.193

! --- Security: Shutdown & Park All Unused Physical Interfaces in VLAN 999 ---
interface range FastEthernet0/1 - 9, FastEthernet0/11 - 24
 description Security_Unused_Port_Parked_in_VLAN999
 switchport mode access
 switchport access vlan 999
 shutdown
exit

end
write memory

! ==============================================================================
! VERIFICATION COMMANDS & EXPECTED OUTPUT (Cisco Packet Tracer 8.x)
! ==============================================================================
!
! 1. show vlan brief
! ------------------------------------------------------------------------------
! SW-A4# show vlan brief
! VLAN Name                             Status    Ports
! ---- -------------------------------- --------- -------------------------------
! 1    default                          active    
! 40   Guest_WiFi                       active    Fa0/10
! 99   Management                       active    
! 999  Parking_Native                   active    Fa0/1, Fa0/2, Fa0/3, Fa0/4,
!                                                 Fa0/5, Fa0/6, Fa0/7, Fa0/8,
!                                                 Fa0/9, Fa0/11, Fa0/12, Fa0/13,
!                                                 Fa0/14, Fa0/15, Fa0/16, Fa0/17,
!                                                 Fa0/18, Fa0/19, Fa0/20, Fa0/21,
!                                                 Fa0/22, Fa0/23, Fa0/24
!
! 2. show interfaces trunk
! ------------------------------------------------------------------------------
! SW-A4# show interfaces trunk
! Port        Mode         Encapsulation  Status        Native vlan
! Gi0/1       on           802.1q         trunking      999
! Gi0/2       on           802.1q         trunking      999
!
! Port        Vlans allowed on trunk
! Gi0/1       40,99
! Gi0/2       40,99
!
! 3. show spanning-tree vlan 40
! ------------------------------------------------------------------------------
! SW-A4# show spanning-tree vlan 40
! VLAN0040
!   Spanning tree enabled protocol rstp
!   Root ID    Priority    24616
!              Address     0001.42A1.B202 (SW-D2)
!              Cost        4
!              Port        25 (GigabitEthernet0/1)
!   Interface           Role Sts Cost      Prio.Nbr Type
!   ------------------- ---- --- --------- -------- --------------------------------
!   Gi0/1               Root FWD 4         128.25   P2p
!   Gi0/2               Altn BLK 4         128.26   P2p
!   Fa0/10              Desg FWD 19        128.10   P2p Edge
!
! 4. show ip interface brief | include Vlan
! ------------------------------------------------------------------------------
! SW-A4# show ip interface brief | include Vlan
! Vlan99                 172.16.7.205    YES manual up                    up
! ==============================================================================

```

### Appendix 13.12: Device Configuration — SW-A5

```ios
! ==============================================================================
! DEVICE:       SW-A5
! MODEL:        Cisco Catalyst 2960-24TT (Layer-2 Access Switch)
! LOCATION:     Remote Spoke Clinic - Telecomm Equipment Closet
! ROLE:         Access Layer Switch - All Outpatient Clinical, Admin, Voice & Guest
! UPLINKS:      Gig0/1 -> SW-D3 Fa0/23 (Primary Trunk), Gig0/2 -> SW-D3 Fa0/24 (Secondary Trunk)
! DOWNLINKS:    Fa0/1 - 3 (Consultation & Triage PCs), Fa0/4 - 6 (Admin & Pharmacy PCs),
!               Fa0/7 - 9 (VoIP Phones), Fa0/10 (Guest AP), Fa0/20 (Clinic Admin PC)
! ==============================================================================

enable
configure terminal

! --- Device Identity & System Security ---
hostname SW-A5
no ip domain-lookup
ip domain-name hospital.local

banner motd ^C
================================================================================
  SW-A5 : Remote Spoke Clinic Unified Layer-2 Access Switch
  VIT Vellore - CN Project: Disaster-Resilient Smart Hospital Network
  UNAUTHORIZED ACCESS IS STRICTLY PROHIBITED. ALL SESSIONS MONITORED.
================================================================================
^C

! --- Management Authentication & Credential Encryption ---
enable secret class123
service password-encryption
username admin privilege 15 secret class123

! --- Cryptographic SSH Version 2 Configuration ---
crypto key generate rsa modulus 1024
ip ssh version 2
ip ssh time-out 60
ip ssh authentication-retries 3

! --- Infrastructure Hardening: Standard ACL for VTY Management ---
ip access-list standard ACL-VTY-SSH
 remark Permit Central Hospital NOC Management Console
 permit host 172.16.7.212
 remark Permit Remote Clinic Local Management Station
 permit host 172.16.8.75
 remark Deny all other administrative attempts with logging
 deny any log
exit

line con 0
 password cisco
 login
 logging synchronous
 exec-timeout 15 0
exit

line vty 0 4
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

line vty 5 15
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

! --- Disable Insecure / Unnecessary Management Services ---
no ip http server
no ip http secure-server

! --- Centralized Time Synchronization (NTP Client) ---
ntp server 172.16.7.4

! --- Centralized Logging (Syslog Client) ---
logging host 172.16.7.4
logging trap informational
logging buffered 4096 informational

! --- VLAN Database Definition ---
vlan 10
 name Clinic_Clinical
vlan 30
 name Clinic_Admin
vlan 40
 name Clinic_Guest
vlan 60
 name Clinic_Voice
vlan 99
 name Management
vlan 999
 name Parking_Native
exit

! --- Spanning Tree Protocol: Rapid PVST+ ---
spanning-tree mode rapid-pvst

! --- 802.1Q Redundant Trunk Uplinks to Distribution Switch SW-D3 ---
! Allowed VLANs strictly limited to all Clinic traffic: 10, 30, 40, 60, 99.
! DTP disabled via 'switchport nonegotiate'.

! Primary Uplink to SW-D3 (Active Forwarding Trunk)
interface GigabitEthernet0/1
 description Primary_Trunk_Uplink_to_SW-D3_Fa0/23
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,30,40,60,99
 switchport nonegotiate
 no shutdown
exit

! Secondary Uplink to SW-D3 (RSTP Alternate/Blocking Trunk)
interface GigabitEthernet0/2
 description Redundant_Trunk_Uplink_to_SW-D3_Fa0/24
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,30,40,60,99
 switchport nonegotiate
 no shutdown
exit

! --- Host-Facing Ports: Outpatient Clinical Consultation & Triage ---
interface range FastEthernet0/1 - 3
 switchport mode access
 switchport access vlan 10
 spanning-tree portfast
 spanning-tree bpduguard enable
 no shutdown
exit

interface FastEthernet0/1
 description Clinic_Consultation_Room_1_Workstation_(PC-CLINIC-CONSULT1)
exit

interface FastEthernet0/2
 description Clinic_Consultation_Room_2_Workstation_(PC-CLINIC-CONSULT2)
exit

interface FastEthernet0/3
 description Clinic_Emergency_Triage_Workstation_(PC-CLINIC-TRIAGE)
exit

! --- Host-Facing Ports: Clinic Administration, Billing & Pharmacy ---
! Security: PortFast, BPDU Guard, Max 2 MACs, sticky learning, VIOLATION SHUTDOWN
interface range FastEthernet0/4 - 6
 switchport mode access
 switchport access vlan 30
 spanning-tree portfast
 spanning-tree bpduguard enable
 switchport port-security
 switchport port-security maximum 2
 switchport port-security mac-address sticky
 switchport port-security violation shutdown
 no shutdown
exit

interface FastEthernet0/4
 description Clinic_Reception_and_Patient_CheckIn_(PC-CLINIC-ADM1)
exit

interface FastEthernet0/5
 description Clinic_Billing_and_Insurance_Terminal_(PC-CLINIC-ADM2)
exit

interface FastEthernet0/6
 description Clinic_Pharmacy_Dispensing_Terminal_(PC-CLINIC-PHARM)
exit

! --- Host-Facing Ports: Cisco 7960 VoIP IP Phones ---
! Voice VLAN 60 tagged with 802.1p CoS 5, PC data untagged
interface FastEthernet0/7
 description Clinic_Reception_VoIP_Phone_(PHONE-CLINIC-601)
 switchport mode access
 switchport access vlan 30
 switchport voice vlan 60
 spanning-tree portfast
 spanning-tree bpduguard enable
 no shutdown
exit

interface FastEthernet0/8
 description Clinic_Doctor_Desk_VoIP_Phone_(PHONE-CLINIC-602)
 switchport mode access
 switchport access vlan 10
 switchport voice vlan 60
 spanning-tree portfast
 spanning-tree bpduguard enable
 no shutdown
exit

interface FastEthernet0/9
 description Clinic_Triage_Desk_VoIP_Phone_(PHONE-CLINIC-603)
 switchport mode access
 switchport access vlan 10
 switchport voice vlan 60
 spanning-tree portfast
 spanning-tree bpduguard enable
 no shutdown
exit

! --- Host-Facing Port: Clinic Guest Wi-Fi Access Point (AP-CLINIC-GUEST) ---
interface FastEthernet0/10
 description Clinic_Guest_WiFi_Access_Point_Uplink_(AP-CLINIC-GUEST)
 switchport mode access
 switchport access vlan 40
 spanning-tree portfast
 spanning-tree bpduguard enable
 no cdp enable
 no shutdown
exit

! --- Local Clinic System Administrator Management Console (VLAN 99) ---
interface FastEthernet0/20
 description Clinic_Local_System_Administrator_Console_(PC-CLINIC-MGT)
 switchport mode access
 switchport access vlan 99
 spanning-tree portfast
 spanning-tree bpduguard enable
 switchport port-security
 switchport port-security maximum 2
 switchport port-security mac-address sticky
 switchport port-security violation shutdown
 no shutdown
exit

! --- In-Band Management SVI (VLAN 99 - Subnet: 172.16.8.64/28) ---
interface Vlan99
 description In_Band_Management_SVI_SW-A5
 ip address 172.16.8.74 255.255.255.240
 no shutdown
exit

! Default Gateway pointing to SW-D3 SVI (.65)
ip default-gateway 172.16.8.65

! --- Security: Shutdown & Park All Unused Physical Interfaces in VLAN 999 ---
interface range FastEthernet0/11 - 19, FastEthernet0/21 - 24
 description Security_Unused_Port_Parked_in_VLAN999
 switchport mode access
 switchport access vlan 999
 shutdown
exit

end
write memory

! ==============================================================================
! VERIFICATION COMMANDS & EXPECTED OUTPUT (Cisco Packet Tracer 8.x)
! ==============================================================================
!
! 1. show vlan brief
! ------------------------------------------------------------------------------
! SW-A5# show vlan brief
! VLAN Name                             Status    Ports
! ---- -------------------------------- --------- -------------------------------
! 1    default                          active    
! 10   Clinic_Clinical                  active    Fa0/1, Fa0/2, Fa0/3, Fa0/8, Fa0/9
! 30   Clinic_Admin                     active    Fa0/4, Fa0/5, Fa0/6, Fa0/7
! 40   Clinic_Guest                     active    Fa0/10
! 60   Clinic_Voice                     active    Fa0/7, Fa0/8, Fa0/9
! 99   Management                       active    Fa0/20
! 999  Parking_Native                   active    Fa0/11, Fa0/12, Fa0/13, Fa0/14,
!                                                 Fa0/15, Fa0/16, Fa0/17, Fa0/18,
!                                                 Fa0/19, Fa0/21, Fa0/22, Fa0/23,
!                                                 Fa0/24
!
! 2. show interfaces trunk
! ------------------------------------------------------------------------------
! SW-A5# show interfaces trunk
! Port        Mode         Encapsulation  Status        Native vlan
! Gi0/1       on           802.1q         trunking      999
! Gi0/2       on           802.1q         trunking      999
!
! Port        Vlans allowed on trunk
! Gi0/1       10,30,40,60,99
! Gi0/2       10,30,40,60,99
!
! 3. show spanning-tree summary
! ------------------------------------------------------------------------------
! SW-A5# show spanning-tree summary
! Switch is in rapid-pvst mode
! Root bridge for: none
! Extended system ID is enabled
!
! 4. show port-security
! ------------------------------------------------------------------------------
! SW-A5# show port-security
! Secure Port  MaxSecureAddr  CurrentAddr  SecurityViolation  Security Action
!                (Count)       (Count)          (Count)
! ---------------------------------------------------------------------------
! Fa0/4              2             1                0             Shutdown
! Fa0/5              2             1                0             Shutdown
! Fa0/6              2             1                0             Shutdown
! Fa0/20             2             1                0             Shutdown
! ---------------------------------------------------------------------------
!
! 5. show ip interface brief | include Vlan
! ------------------------------------------------------------------------------
! SW-A5# show ip interface brief | include Vlan
! Vlan99                 172.16.8.74     YES manual up                    up
! ==============================================================================

```