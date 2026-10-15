# Faculty Syllabus & Curriculum Traceability Mapping: NS-3 Simulation

**Project:** Disaster-Resilient Smart Hospital Network  
**Course:** CSE2004 — Computer Networks, SCOPE, VIT Vellore  
**Authors:**
- Rohit Kathiravan (`24BCE0441`)
- Karthikeyan S (`24BCT0332`)

---

## 1. Overview & Objective

To satisfy faculty requirements for discrete-event network simulation (NS-2 / NS-3), this repository module reproduces the **Cisco Packet Tracer 8.x** hospital network architecture inside **NS-3**. 

While Packet Tracer provides interactive Cisco IOS CLI configuration, three-tier hierarchical switching, and visual PDU propagation, **NS-3 provides cycle-accurate, discrete-event packet simulation**, generating:
1. `flowmon.xml`: Fine-grained per-flow performance traces.
2. `.pcap` packet trace files readable in Wireshark.
3. Quantifiable TCP congestion control and routing convergence metrics under failure injection.

---

## 2. Topic-by-Topic Faculty Mapping Matrix

| Syllabus Topic / Lab Requirement | Packet Tracer Implementation | NS-3 Discrete-Event Implementation | Verification Artifact |
| :--- | :--- | :--- | :--- |
| **Network Topology & Addressing** | Three-tier campus, VLSM over `172.16.0.0/16`, Core Routers R1/R2. | Dual-site topology, `PointToPointNetDevice` WAN (2M/1M), 100M LANs. | `hospital-ns3/sim/hospital_baseline.cc` |
| **Discrete-Event Simulation (NS-2/NS-3)** | Interactive event-driven animation. | Microsecond-accurate discrete event queue (`Simulator::Schedule`). | `hospital-ns3/results/exp1_baseline/flowmon.xml` |
| **Dynamic Routing & Failover** | Multi-Area OSPFv2 with tuned timers + EIGRP standby WAN. | `Ipv4GlobalRoutingHelper` (Dijkstra SPF) with dynamic link down/up recomputation. | `hospital-ns3/results/exp2_wan_failover/` |
| **Transport Layer Protocols** | TCP vs. UDP comparative study. | RFC-compliant `TcpCubic`, `TcpNewReno`, and UDP vitals streams. | `hospital-ns3/scripts/sweep_runners.sh` |
| **Flow & Congestion Metrics** | Manual ping loss counting. | FlowMonitor XML parser extracting throughput, PDR, jitter, and delay. | `hospital-ns3/analysis/parse_flowmon.py` |
| **Quality of Service (QoS)** | Cisco IOS MQC (Class-Maps, Policy-Maps, Priority Queues). | `TrafficControlHelper`, `PrioQueueDisc` vs. DropTail queuing. | `hospital-ns3/analysis/plot_metrics.py` |
| **Parametric Sweeps & Statistical Repeatability** | Single simulation runs. | Multi-seed execution (`RngSeedManager::SetSeed`) with parameter sweeps. | `hospital-ns3/results/exp3_sweeps/` |

---

## 3. Key Differences & How They Are Addressed

1. **Routing Protocols (OSPF vs. GlobalRouting):**
   - *Limitation:* NS-3 does not implement native Cisco OSPF hello/DBD/LSA packet exchanges out-of-the-box.
   - *Academic Solution:* We employ `Ipv4GlobalRoutingHelper::PopulateRoutingTables()`, which uses Dijkstra's algorithm to compute shortest paths based on link metrics, exactly matching OSPF's Shortest Path First (SPF) algorithm. Dynamic failover is triggered via `Ipv4GlobalRoutingHelper::RecomputeRoutingTables()`.
2. **Switching & VLAN Encapsulation:**
   - *Limitation:* 802.1Q VLAN trunking tags add simulation overhead without changing L3 routing behavior.
   - *Academic Solution:* We model distinct IP subnets (`/26`, `/27`, `/23`) using dedicated point-to-point and CSMA channels, isolating broadcast domains identically to physical VLANs.
