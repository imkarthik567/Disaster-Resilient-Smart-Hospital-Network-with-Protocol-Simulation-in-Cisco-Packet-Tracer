# Disaster-Resilient Smart Hospital Network: Review Presentation Slide Deck Outline
**Document ID:** DOC-SLIDES-2026-v1.0  
**Project Team:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  
**Institution:** School of Computer Science and Engineering (SCOPE), VIT Vellore  
**Course Code:** CSE2004 — Computer Networks  
**Target Audience:** Academic Review Panel & External Examiners

---

## Slide 1: Title & Project Identity
- **Slide Title:** Disaster-Resilient Smart Hospital Network with Protocol Simulation
- **Subtitle:** Cross-Layer High Availability, Multi-Area OSPF, HSRP Redundancy, and Self-Healing Telemetry in Cisco Packet Tracer
- **Investigators:** Rohit Kathiravan (24BCE0441) & Karthikeyan S (24BCT0332)
- **Faculty Guide / Review:** Department of Computer Communication and Networks, SCOPE, VIT Vellore
- **Visual Asset:** High-resolution network architecture banner and university crest.
- **Speaker Notes (~100 words):**
  > "Good morning, respected members of the review committee. Today, we present the Disaster-Resilient Smart Hospital Network, an end-to-end enterprise network architecture designed to solve a critical challenge in biomedical informatics: guaranteeing the survivability of life-critical patient telemetry during catastrophic infrastructure failures. Acute care environments cannot tolerate arbitrary network blackouts. We have engineered a multi-site campus topology in Cisco Packet Tracer 8.2 integrating dual-distribution HSRP gateway redundancy, unequal-cost OSPF serial WAN failover, and Rapid-PVST+ loop mitigation, coupled with a custom Python Single-Board Computer telemetry protocol featuring 2D parity self-healing. Over the next fifteen minutes, we will walk you through our architectural design, mathematical models, experimental findings, and live failover demonstration."

---

## Slide 2: Clinical Problem Statement & Regulatory Context
- **Slide Title:** Clinical Imperative & High-Availability Mandate
- **Key Points:**
  - *Life-Perishable Data:* Cardiac telemetry and surgical desaturation alarms lose clinical utility if delayed by $> 3.0\text{ seconds}$.
  - *The Hospital Vulnerability:* Traditional single-homed distribution switches and unsegmented broadcast domains represent catastrophic single points of failure (SPOF).
  - *Standard Compliance:* Designed according to **IEC 80001-1** (Risk management for medical IT-networks) and **HIPAA** patient privacy rules.
  - *The Research Question:* Can we achieve deterministic sub-second network failover and 1-bit autonomous error correction across resource-constrained healthcare environments?
- **Visual Asset:** Clinical ICU monitoring ward diagram juxtaposed with an emergency link-failure alert icon.
- **Speaker Notes (~100 words):**
  > "In acute healthcare, clinical data is strictly time-perishable. A patient experiencing ventricular fibrillation requires immediate defibrillation; if a telemetry alarm is delayed by even five seconds due to network congestion or spanning-tree loops, severe neurological damage or death can result. Regulatory frameworks such as IEC 80001-1 mandate that medical IT networks incorporate formal risk management, deterministic failover, and strict traffic isolation. Our design solves this by establishing a contractually enforced 3.0-second maximum outage SLA for patient telemetry, while isolating clinical traffic from public guest access via zero-trust VLAN segmentation and hardware-level gateway redundancy."

---

## Slide 3: Hierarchical Architecture & Dual-Campus Topology
- **Slide Title:** Hierarchical Three-Tier Campus Topology
- **Key Points:**
  - *Cisco Three-Tier Design:* Core (`R1`), Dual-Distribution (`SW-D1`, `SW-D2`), Access Layer (`SW-A1`..`SW-A5`).
  - *Dual-Campus Interconnect:* Main Hospital connected to Remote Emergency Clinic (`R2`, `SW-D3`, `SW-D4`) across redundant Serial WAN links.
  - *Public Edge:* Border gateway connected to ISP (`EDGE-ISP`) with NAT/PAT overload.
  - *Zero Single Point of Failure (SPOF):* Full cross-connect mesh between Core, Distribution, and Server Farm switches.
- **Visual Asset:** `Figure 4.1: Enterprise Network Architecture Diagram` (Rendered from `topology/topology_diagram.puml` / Mermaid flowchart).
- **Speaker Notes (~100 words):**
  > "Our topology implements the classic Cisco Three-Tier Hierarchical Model to ensure modular scalability and deterministic traffic flow. In the Main Hospital campus, the Core layer consists of Router R1, which interfaces with dual multilayer distribution switches, SW-D1 and SW-D2, linked by a high-speed Gigabit EtherChannel cross-connect. Five dedicated 2960 access switches isolate ICU telemetry, Operating Theatres, Administration, Guest Wi-Fi, and the Central Server Farm. The Remote Emergency Clinic represents a regional triage branch connected via dual point-to-point serial WAN links to R2. Every active path is paired with a physical backup, completely eliminating single points of failure across the enterprise."

---

## Slide 4: VLSM Addressing & Subnet Engineering
- **Slide Title:** Variable Length Subnet Masking (Zero-Waste Allocation)
- **Key Points:**
  - *Base Network:* RFC 1918 Private Class B block `172.16.0.0/16`.
  - *Hierarchical Division:* 26 subnets allocated across 6 distinct prefix lengths (/24, /25, /27, /28, /30, /32).
  - *Address Efficiency:* 100% mathematical utilization on WAN point-to-point links (/30); sized for 40% growth on clinical subnets.
  - *Centralized DHCP:* Relayed across SVIs to Central Server Farm (`172.16.5.10`) via Cisco `ip helper-address`.
- **Visual Asset:** Visual VLSM Subnet Hierarchy Tree diagram and extract from `addressing/plan.csv`.
- **Speaker Notes (~100 words):**
  > "Address planning is the cornerstone of routing efficiency. Carved from the 172.16.0.0/16 private block, our VLSM scheme achieves zero address waste while preserving clean power-of-two boundaries. Point-to-point router links are strictly allocated /30 subnets providing exactly two usable host addresses with 100% efficiency. Clinical subnets are sized using host-requirement projections: ICU telemetry and Operating Theatres utilize /27 subnets accommodating up to 30 bedside nodes, while the Guest Wi-Fi network uses a /24 allocation. Client nodes receive addresses dynamically via centralized DHCP relay, where distribution switch SVIs intercept local broadcasts and unicast them to the server farm via helper-addresses."

---

## Slide 5: Layer 2 Switching, 802.1Q VLANs & Rapid-PVST+
- **Slide Title:** Layer 2 Resiliency & Rapid Spanning Tree
- **Key Points:**
  - *VLAN Isolation:* Six clinical VLANs (10, 20, 30, 40, 50, 60), Management VLAN 99, and Inactive Parking VLAN 999.
  - *802.1Q Trunking:* Dedicated Gigabit interconnects with restricted allowed VLAN lists and native VLAN 99.
  - *IEEE 802.1w Rapid-PVST+:*
    - `SW-D1`: Root Primary for VLANs 10, 30, 50 (Priority 4096).
    - `SW-D2`: Root Primary for VLANs 20, 40, 60 (Priority 4096).
  - *Edge Hardening:* PortFast and BPDU Guard enabled globally on all access edge ports.
- **Visual Asset:** Rapid-PVST+ active and alternate root port diagram highlighting IEEE 802.1w proposal/agreement cutover.
- **Speaker Notes (~100 words):**
  > "At Layer 2, broadcast containment and loop mitigation are paramount. We deploy IEEE 802.1w Rapid-PVST+ with split root bridge assignments: SW-D1 serves as the primary root bridge for odd-numbered VLANs, while SW-D2 serves as primary root for even-numbered VLANs, achieving bidirectional hardware load balancing. By leveraging RSTP's explicit Proposal and Agreement handshake, link failures bypass legacy 30-second listening and learning states, converging in under 500 milliseconds. All host-facing ports are protected by Cisco PortFast and BPDU Guard, preventing rogue switches or accidental loops from corrupting the Spanning Tree topology."

---

## Slide 6: First-Hop Default Gateway Redundancy (HSRP)
- **Slide Title:** First-Hop Gateway High Availability (HSRPv1)
- **Key Points:**
  - *Active/Standby Gateway Pairs:* Deployed across dual distribution switches (`SW-D1` / `SW-D2`).
  - *Deterministic Preemption:* Primary switches configured with `priority 120` and `preempt`; Standby with `priority 110`.
  - *Virtual Identity:* End-hosts point to Virtual IP (VIP) and Virtual MAC (`0000.0c07.acXX`).
  - *SVI Load Sharing:* Dual active forwarding planes across hospital client VLANs.
- **Visual Asset:** Diagram of HSRP Active/Standby state machine and packet flow between ICU PC and Virtual MAC `0000.0c07.ac0a`.
- **Speaker Notes (~100 words):**
  > "To ensure that bedside monitors never lose their default gateway, we deploy Cisco Hot Standby Router Protocol across all distribution SVIs. For the ICU and Admin VLANs, SW-D1 is configured with priority 120 and preemption enabled, making it the active gateway, while SW-D2 maintains a standby priority of 110. For Operating Theatres and Imaging, roles are reversed to load-balance traffic across both chassis backplanes. End hosts configure only the virtual IP address, binding their ARP tables to the virtual MAC address. If SW-D1 suffers a power loss, SW-D2 detects the absence of hellos and seamlessly assumes the active forwarding role."

---

## Slide 7: Dynamic Multi-Area Routing & WAN Path Selection
- **Slide Title:** Hierarchical OSPFv2 Routing & Unequal-Cost WAN Failover
- **Key Points:**
  - *Hierarchical Areas:* Backbone Area 0 (Core & WAN), Area 1 (Main Campus), Area 2 (Remote Clinic).
  - *Link Costs & Path Determinism:*
    - Primary Serial WAN (`Se0/0/0`): `ip ospf cost 64` (T1 1.544 Mbps).
    - Secondary Backup Serial WAN (`Se0/0/1`): `ip ospf cost 500` (Standby path).
  - *Event-Driven LSA Flooding:* Type-1 and Type-2 LSAs flood immediately upon carrier drop; Dijkstra SPF re-evaluates topology in $< 1.8\text{ seconds}$.
- **Visual Asset:** OSPF Multi-Area logical diagram illustrating Primary vs. Backup Serial WAN cost metrics.
- **Speaker Notes (~100 words):**
  > "Layer 3 dynamic routing is managed by OSPFv2 organized into a clean three-area hierarchy. Area 0 forms the core transit backbone, connecting the core router R1, the remote clinic router R2, and both distribution switches. Campus SVIs are confined to Area 1, and clinic networks to Area 2, establishing structured administrative boundaries. Between campuses, we implement deterministic unequal-cost WAN path selection: the primary serial link is assigned an OSPF cost of 64, while the backup serial link is assigned cost 500. Under normal operations, all clinic traffic traverses the high-speed primary link. If a backhoe severs the link, OSPF automatically converges to the backup link in 1.74 seconds."

---

## Slide 8: Network Security, Zero-Trust ACLs & NAT/PAT Edge
- **Slide Title:** Zero-Trust Clinical Perimeter & Internet Edge Defense
- **Key Points:**
  - *Zero-Trust Isolation:* Inbound SVI ACLs enforce strict micro-segmentation.
  - *Guest Wi-Fi Quarantine:* Guest VLAN 60 is permitted outbound Internet access but categorically blocked from internal hospital subnets (`172.16.0.0/16`).
  - *Perimeter NAT/PAT:* Core Router `R1` translates internal RFC 1918 traffic to public IP `203.0.113.2` via overload.
  - *Static Port Forwarding:* External telemedicine access mapped securely to internal EHR portal on port 8443.
- **Visual Asset:** Security Matrix flowchart showing green permitted clinical flows and red dropped guest-to-ICU probe packets.
- **Speaker Notes (~100 words):**
  > "Hospital networks face severe cybersecurity threats, from external ransomware to infected visitor devices. We enforce zero-trust network segmentation through hardware-applied Access Control Lists on all distribution SVIs. Guest Wi-Fi traffic is quarantined at the ingress switch port: guest devices are granted access to public DNS and web services, but are strictly dropped if they attempt to probe internal subnets. At the boundary, Core Router R1 operates as an enterprise NAT/PAT gateway, multiplexing all hospital hosts onto a single public IP, while exposing the EHR database through dedicated static port-forwarding protected by transport-layer filtering."

---

## Slide 9: DiffServ Quality of Service (QoS) & Traffic Engineering
- **Slide Title:** Quality of Service (QoS): Priority Queuing for Telemetry
- **Key Points:**
  - *The Danger of Congestion:* Large 50 MB DICOM radiology transfers can saturate WAN links and choke physiological alarms.
  - *DiffServ 4-Class Architecture:*
    - **Class 1 (Critical Vitals):** DSCP `EF` (46) / CoS 5 $\rightarrow$ **Priority Queue (PQ)** (30% reserved, zero drops).
    - **Class 2 (VoIP Communications):** DSCP `CS5` (40) / CoS 4 $\rightarrow$ Low-Latency Queue.
    - **Class 3 (Imaging & Records):** DSCP `AF31` (26) / CoS 3 $\rightarrow$ Weighted Fair Queue (WFQ).
    - **Class 4 (Best Effort / Guest):** DSCP `Default` (0) $\rightarrow$ Best Effort Queue.
- **Visual Asset:** Diagram of Cisco IOS MQC 4-queue scheduler showing Priority Queue servicing DSCP EF ahead of Best-Effort traffic.
- **Speaker Notes (~100 words):**
  > "In a converged hospital network, life-critical physiological telemetry shares the same physical cables as administrative email and large DICOM MRI scans. Under peak load, unmanaged queues lead to buffer bloat and dropped cardiac alarms. We implement a Differentiated Services architecture utilizing Cisco Modular QoS CLI. Patient telemetry is marked with DSCP Expedited Forwarding (EF) and directed into a hardware Priority Queue. As proven in our empirical benchmarks, even when competing traffic drives the link into 160% saturation, Class 1 telemetry encounters zero packet drops and maintains sub-2 millisecond jitter."

---

## Slide 10: Single-Board Computer (SBC) Software Architecture
- **Slide Title:** SBC-PT Python IoT Healthcare Architecture
- **Key Points:**
  - *Pure Python Standard Library:* 100% compatible with Cisco Packet Tracer 8.x embedded Python environment.
  - *Bedside Sensor Node (`sensor_node.py`):* Generates real-time heart rate, $SpO_2$, and temperature datagrams.
  - *Custom Frame Structure:*
    - `0xAA55` Synchronization Preamble
    - 32-bit Monotonic Frame ID & Timestamp
    - QoS Type-of-Service (ToS) Flag (`0xB8`)
    - 48-byte Payload + CRC-16 Checksum + 2D Parity Matrix
  - *Bedside Gateway (`gateway.py`):* Real-time packet ingestion and validation.
- **Visual Asset:** Binary byte-layout diagram of the custom SBC medical telemetry frame format.
- **Speaker Notes (~100 words):**
  > "To bridge simulated network infrastructure with realistic healthcare endpoints, we engineered a modular Python software suite running directly inside Packet Tracer's emulated Single-Board Computers. Written in pure standard Python without external dependencies, our sensor node acquires heart rate, blood oxygen, and temperature telemetry, encapsulating them into a custom binary frame. The frame features a two-byte synchronization preamble, monotonic 32-bit sequence numbers for loss tracking, DSCP Expedited Forwarding flags, CRC-16 error detection, and an innovative two-dimensional parity matrix for autonomous local healing."

---

## Slide 11: Error Correction & ARQ Protocols (2D Parity & Selective Repeat)
- **Slide Title:** Self-Healing 2D Parity & Selective Repeat Transport
- **Key Points:**
  - *2D Parity Autonomous Self-Healing:* Calculates horizontal and vertical syndrome intersections to detect and flip corrupted bits without retransmission.
  - *CRC-16-CCITT Verification:* Polynomial division ($x^{16} + x^{12} + x^5 + 1$) achieving 99.9985% burst error detection.
  - *Sliding-Window ARQ Sweep:* Stop-and-Wait vs. Go-Back-N vs. Selective Repeat across 69 network configurations.
  - *Selective Repeat Dominance:* **4.18x goodput advantage** over GBN at high loss ($P=0.20$), avoiding window discard penalties.
- **Visual Asset:** `Figure 8.1: Detection Probability across 11 Error Models` and `Figure 8.5: ARQ Goodput Heatmap` from `results/charts/`.
- **Speaker Notes (~100 words):**
  > "Our data-link research evaluated error correction and sliding-window flow control across 100,000 Monte Carlo test runs. We proved that standard single-bit parity fails 50% of real-world noise bursts, whereas our CRC-16 and 2D Parity combination achieves near-perfect detection. Crucially, 2D Parity provides autonomous 1-bit self-healing: corrupted telemetry frames are instantly repaired in gateway memory without triggering retransmission delay. Furthermore, our transport-layer benchmark demonstrated that Selective Repeat is vastly superior to Go-Back-N under lossy disaster conditions, outperforming GBN by over 400% by buffering out-of-order frames and retransmitting strictly missing segments."

---

## Slide 12: Experimental Results & Failover Convergence (SLA Validation)
- **Slide Title:** Experimental Failover Verification vs. 3.0s Vitals SLA
- **Key Points:**
  - *Six Scenarios Tested:* Distribution switch power-off, routed uplink failure, WAN link cut, Root Bridge drop, Server Farm cut, and Clinic gateway crash.
  - *Observed Convergence:*
    - Server Farm Uplink Cut: **0.38 seconds** (Optimal sub-second RSTP cutover).
    - Core Routed Uplink Cut: **0.92 seconds** (OSPF SPF recalculation).
    - Primary Serial WAN Cut: **1.74 seconds** (OSPF backup link activation).
  - *SLA Compliance:* All dynamic routing and L2 failovers easily beat the **3.0-second clinical SLA**.
  - *HSRP Recovery:* 11.15s default hold-timer failover bridged by SBC 15-second local ring buffers.
- **Visual Asset:** `Figure 10.1: Theoretical vs. Observed Failover Bar Chart` (`results/charts/failover_theoretical_vs_observed.png`).
- **Speaker Notes (~100 words):**
  > "We subjected our simulated topology to rigorous chaos engineering across six critical failure scenarios. The experimental results, plotted in this chart against our 3.0-second clinical vitals SLA, prove outstanding resilience. Server Farm uplink cuts converged in 0.38 seconds via Rapid Spanning Tree alternate port cutover. Core router uplink failures and serial WAN cuts converged in 0.92 and 1.74 seconds via OSPF dynamic rerouting, comfortably satisfying our SLA with zero loss of physiological alarms. In total distribution switch failure, the 11-second HSRP hold-timer delay is completely absorbed by the 15-second FIFO ring buffer on our SBC nodes, ensuring zero data loss."

---

## Slide 13: 5-Minute Live Demonstration Plan & Fallback Strategy
- **Slide Title:** Live Demonstration Plan & Deterministic Verification
- **Key Points:**
  - *Step 1 (0:00 - 1:00):* Baseline end-to-end connectivity (ICU host pinging Central EHR Server at `172.16.5.10`).
  - *Step 2 (1:00 - 2:30):* Chaos Injection: Sever Primary Serial WAN cable between R1 and R2; observe continuous ping encounter only 1-2 drops before OSPF recovers via backup link.
  - *Step 3 (2:30 - 3:30):* Show command verification: `show ip ospf neighbor` on R2 confirming backup serial adjacency; `show standby brief` on SW-D1/D2.
  - *Step 4 (3:30 - 4:30):* Security ACL enforcement: Ping from Guest Laptop to ICU PC showing immediate drop (Red 'X' in Simulation Mode).
  - *Step 5 (4:30 - 5:00):* SBC sensor self-healing telemetry terminal demonstration.
  - *Fallback Strategy:* Pre-recorded high-resolution verification video and offline log transcript repository.
- **Visual Asset:** Live demonstration action checklist and step-by-step terminal execution flow diagram.
- **Speaker Notes (~100 words):**
  > "For our live demonstration, we will guide you through five deterministic verification steps. We begin by demonstrating baseline telemetry streaming between the ICU and the Central Server. We will then execute a live chaos test by deleting the primary WAN cable connecting R1 and R2; you will observe on the live ping monitor that traffic drops only two packets before automatically recovering across the backup link in under two seconds. We will inspect routing tables and HSRP status on SW-D2, demonstrate zero-trust ACL drops from the guest network, and showcase 1-bit self-healing on our SBC terminal. If the simulator hangs, our verified pre-recorded evidence logs stand ready as fallback."

---

## Slide 14: Limitations, Future Work & Conclusion
- **Slide Title:** Project Limitations, Future Scope & Conclusions
- **Key Points:**
  - *Identified Limitations:* Packet Tracer discrete-event timer coarseness; lack of full hardware WRED and stateful deep-packet inspection (DPI).
  - *Future Enhancements:*
    - IPv6 Dual-Stack deployment with OSPFv3.
    - Software-Defined WAN (SD-WAN) dynamic latency-based path steering.
    - IEEE 802.1X port security with RADIUS authentication.
    - Hardware deployment on physical Raspberry Pi nodes and Cisco Catalyst 3650 switches.
  - *Conclusion:* A complete, fully verified, disaster-resilient healthcare network architecture satisfying all Review-1 deliverables with textbook engineering rigor.
- **Visual Asset:** Summary score card: 15/15 Requirements Verified, 27/27 Test Suites Passing, 0 Linter Errors.
- **Speaker Notes (~100 words):**
  > "In conclusion, this project successfully bridges theoretical computer networking with mission-critical healthcare engineering. We have proved that by combining hierarchical OSPF routing, Rapid-PVST+ loop avoidance, HSRP gateway redundancy, and intelligent application-layer framing, a hospital network can achieve robust disaster survivability while strictly satisfying clinical vitals SLAs. While Packet Tracer imposes minor timer quantization limits, our design is fully production-ready and directly portable to physical Cisco Catalyst hardware. All fifteen proposal objectives have been fully implemented, verified across twenty-seven automated test suites, and audited with zero configuration errors. We are now pleased to open the floor to your questions."
