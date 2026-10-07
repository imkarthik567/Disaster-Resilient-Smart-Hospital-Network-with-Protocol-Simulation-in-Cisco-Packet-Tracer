# Architecture Decision Records (ADRs)

**Project:** Disaster-Resilient Smart Hospital Network with Protocol Simulation in Cisco Packet Tracer  
**Course:** Computer Networks — VIT Vellore, SCOPE  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  
**Document Status:** Approved Architecture Decisions for Review-2, Viva Defense, and Final Implementation

---

## Index of Architecture Decision Records

* [ADR-01: OSPF Multi-Area Hierarchy and ABR Placement](#adr-01-ospf-multi-area-hierarchy-and-abr-placement)
* [ADR-02: Administrative Distance Tuning for Deterministic WAN Failover (OSPF vs. EIGRP)](#adr-02-administrative-distance-tuning-for-deterministic-wan-failover-ospf-vs-eigrp)
* [ADR-03: First-Hop Gateway Redundancy (HSRP) Across Distribution Switches](#adr-03-first-hop-gateway-redundancy-hsrp-across-distribution-switches)
* [ADR-04: Mitigation of Single Point of Failure at Remote Clinic (SW-D3)](#adr-04-mitigation-of-single-point-of-failure-at-remote-clinic-sw-d3)
* [ADR-05: Inbound SVI ACL Policy with Essential Service Exceptions (Guest Isolation)](#adr-05-inbound-svi-acl-policy-with-essential-service-exceptions-guest-isolation)
* [ADR-06: Dedicated Voice VLAN Architecture and Auxiliary Frame Tagging](#adr-06-dedicated-voice-vlan-architecture-and-auxiliary-frame-tagging)
* [ADR-07: QoS Trust Boundary Placement and Layer 3 DSCP Marking Strategy](#adr-07-qos-trust-boundary-placement-and-layer-3-dscp-marking-strategy)
* [ADR-08: Link Aggregation (EtherChannel / LACP) vs. STP Port Blocking](#adr-08-link-aggregation-etherchannel-lacp-vs-stp-port-blocking)
* [ADR-09: Inter-Site OSPF Route Summarisation at the ABR Boundary](#adr-09-inter-site-ospf-route-summarisation-at-the-abr-boundary)
* [ADR-10: Multi-Tier Verification Strategy for Packet Tracer Emulation Boundaries](#adr-10-multi-tier-verification-strategy-for-packet-tracer-emulation-boundaries)

---

## ADR-01: OSPF Multi-Area Hierarchy and ABR Placement

* **Status:** Accepted
* **Date:** 2026-10-07
* **Deciders:** Rohit Kathiravan, Karthikeyan S

### Context
The Review-1 proposal stated that Core Router R1 operates in OSPF Area 0, while Core Router R2 operates in OSPF Area 1, connected by a point-to-point primary serial WAN link. In OSPF (RFC 2328), two adjacent routers exchange Hello packets containing an `Area ID` field. If the Area ID does not match on the shared subnet, the OSPF adjacency fails immediately, and no LSAs are exchanged.

### Options Considered
1. **Option 1 (Flawed Review-1 Concept):** Assign R1 Serial interface to Area 0 and R2 Serial interface to Area 1.
   * *Pros:* None.
   * *Cons:* Protocol invalid; OSPF neighbor adjacency will never form.
2. **Option 2 (Single Flat Area 0):** Place both campuses and the WAN link into Backbone Area 0.
   * *Pros:* Simple configuration.
   * *Cons:* High CPU churn; access link flaps or DHCP churn at the Remote Clinic force full SPF tree recalculations across the Main Hospital Core.
3. **Option 3 (R2 as Dedicated Area Border Router):** Designate R1 as an Internal Backbone Router (Area 0), assign the Primary WAN Serial link (`172.16.8.80/30`) to Area 0, and designate Core Router R2 as an **Area Border Router (ABR)**. R2's WAN port (`Serial0/0/0`) belongs to Area 0, while its LAN downlink (`Gig0/0`) belongs to Area 1.

### Decision
Adopt **Option 3**. R2 is explicitly configured as an OSPF ABR. The primary WAN serial link is part of Backbone Area 0. All Remote Clinic subnets are contained in Area 1.

### Consequences
* **Positive:** OSPF adjacency establishes successfully over the serial WAN. Remote Clinic topology changes remain confined to Area 1. Enables inter-area route summarisation via `area 1 range`.
* **Negative:** Requires R2 to maintain two independent Link-State Databases (LSDB for Area 0 and LSDB for Area 1).

---

## ADR-02: Administrative Distance Tuning for Deterministic WAN Failover (OSPF vs. EIGRP)

* **Status:** Accepted
* **Date:** 2026-10-07
* **Deciders:** Rohit Kathiravan, Karthikeyan S

### Context
The hospital architecture specifies dynamic WAN redundancy between R1 and R2 using OSPF over the primary serial link and EIGRP over the standby serial link. By default in Cisco IOS:
* **EIGRP Internal AD:** `90`
* **OSPF Inter-Area / Intra-Area AD:** `110`

If both protocols concurrently advertise inter-site subnets, the Cisco Routing Information Base (RIB) will preferentially install the EIGRP route because $90 < 110$. This causes the standby secondary link to become active by default, leaving the primary high-bandwidth OSPF path completely unused.

### Options Considered
1. **Option 1 (Default Administrative Distances):** Leave ADs untouched.
   * *Pros:* Default configuration.
   * *Cons:* Breaks design intent; secondary link takes 100% of traffic; primary link sits idle.
2. **Option 2 (Redistribution with Metric Manipulation):** Redistribute between OSPF and EIGRP on both routers.
   * *Pros:* Protocol flexibility.
   * *Cons:* Severe risk of suboptimal routing loops and route feedback without complex route-tags; unnecessary complexity for a two-router dual-link spoke.
3. **Option 3 (Administrative Distance Tuning via `distance eigrp`):** Explicitly raise EIGRP's internal administrative distance to **120** on both R1 and R2 (`distance eigrp 120 170`).

### Decision
Adopt **Option 3**. Adjust EIGRP internal AD to 120.

### Consequences
* **Positive:** When the primary WAN link is UP, OSPF (AD 110) wins the RIB election over EIGRP (AD 120). When the primary link is severed (`Serial0/0/0` down), OSPF routes are evicted, and EIGRP routes immediately populate the routing table without manual intervention.
* **Negative:** Network engineers inspecting `show ip route` must remember that EIGRP routes have a non-standard AD of 120.

---

## ADR-03: First-Hop Gateway Redundancy (HSRP) Across Distribution Switches

* **Status:** Accepted
* **Date:** 2026-10-07
* **Deciders:** Rohit Kathiravan, Karthikeyan S

### Context
The original Review-1 design split SVIs across distribution switches: SW-D1 hosted gateways for Clinical VLANs (10, 20) and Server Farm (50), while SW-D2 hosted gateways for Admin (30), Guest (40), and Voice (60). If SW-D1 suffers a catastrophic hardware failure or power supply loss, the entire ICU and Server Farm lose their default gateway, leaving the hospital paralyzed even though SW-D2 remains fully operational.

### Options Considered
1. **Option 1 (Isolated Split SVIs - Review-1):** SVIs partitioned between SW-D1 and SW-D2 without failover.
   * *Pros:* No gateway redundancy protocol overhead.
   * *Cons:* Fatal Single Point of Failure (SPOF) for all clinical and server systems.
2. **Option 2 (VRRP - Virtual Router Redundancy Protocol):** Open standard FHRP.
   * *Pros:* Vendor neutral.
   * *Cons:* Packet Tracer 8.x has inconsistent VRRP CLI support across Catalyst 3560 switch images.
3. **Option 3 (HSRP - Hot Standby Router Protocol):** Configure dual SVIs on both SW-D1 and SW-D2 for every VLAN. Assign `.1` to the HSRP Virtual IP (VIP), `.2` to SW-D1, and `.3` to SW-D2. Configure HSRP priority 110 with preemption on SW-D1 for Clinical/Servers, and priority 110 on SW-D2 for Admin/Guest/Voice.

### Decision
Adopt **Option 3**. Deploy HSRP across SW-D1 and SW-D2 with load-sharing active/standby gateway roles per VLAN.

### Consequences
* **Positive:** True hardware disaster resilience. If SW-D1 fails, SW-D2 assumes the active gateway role for the ICU and servers in under 3 seconds. Hosts require zero reconfiguration because their default gateway points to `.1`.
* **Negative:** Consumes 3 IP addresses per subnet (`.1` VIP, `.2` SVI1, `.3` SVI2).

---

## ADR-04: Mitigation of Single Point of Failure at Remote Clinic (SW-D3)

* **Status:** Accepted
* **Date:** 2026-10-07
* **Deciders:** Rohit Kathiravan, Karthikeyan S

### Context
At the Remote Clinic, only a single distribution switch (SW-D3) was specified. An examiner in viva will immediately challenge this as a Single Point of Failure (SPOF) that contradicts the "Disaster-Resilient" project title.

### Options Considered
1. **Option 1 (Dual Distribution Switches at Clinic):** Deploy SW-D3 and SW-D4 with HSRP at the clinic.
   * *Pros:* Full hardware parity with Main Campus.
   * *Cons:* Unrealistic for a small outpatient spoke clinic; exceeds typical branch project hardware footprint in Packet Tracer.
2. **Option 2 (Accepted Branch Office Trade-off with Dual Uplink Redundancy):** Retain a single distribution switch chassis (SW-D3), but eliminate link-level SPOFs by provisioning redundant dual-homed uplinks:
   * Dual physical links between SW-D3 and Core Router R2.
   * Dual 802.1Q trunk links between SW-D3 and Access Switch SW-A5.
   * Deploy local EHR cache server (`SRV-CACHE` at `172.16.8.68`) so clinic doctors can continue local consultations even if the WAN is cut.

### Decision
Adopt **Option 2**. Document SW-D3 as an economically justified single-chassis branch distribution node with redundant link topology and local survivability caching.

### Consequences
* **Positive:** Defensible in academic viva: reflects real-world hub-and-spoke enterprise budgets while providing local offline EHR continuity.
* **Negative:** Chassis-level failure of SW-D3 still requires physical replacement.

---

## ADR-05: Inbound SVI ACL Policy with Essential Service Exceptions (Guest Isolation)

* **Status:** Accepted
* **Date:** 2026-10-07
* **Deciders:** Rohit Kathiravan, Karthikeyan S

### Context
Objective 4.2 mandates blocking Guest Wi-Fi (VLAN 40) from accessing medical equipment (VLAN 10/20) and Server Farm databases (VLAN 50). However, the central DHCP server and internal DNS resolver reside in the Server Farm (`172.16.7.4` and `.5`). A naïve blanket deny statement (`deny ip 172.16.0.0/22 172.16.7.0/26`) would prevent guest devices from leasing IP addresses and resolving domain names, breaking outbound Internet access.

### Options Considered
1. **Option 1 (Blanket Deny at Router Interface):** Filter traffic at Core Router R1 egress.
   * *Pros:* Simple router ACL.
   * *Cons:* Wasteful; malicious guest packets traverse access, distribution, and core links before being dropped. Breaks DHCP/DNS if servers are in the target zone.
2. **Option 2 (SVI Inbound Extended ACL with Explicit Service Hole Punching):** Apply extended ACL `BLOCK-GUEST` inbound on SW-D2 SVI `Vlan40`. Explicitly permit DNS (UDP 53) and DHCP (UDP 67/68) to `host 172.16.7.4` / `172.16.7.5` before executing deny rules against medical and server subnets.

### Decision
Adopt **Option 2**. Apply inbound filtering on the distribution SVI with explicit service permits.

### Consequences
* **Positive:** Drops unauthorized guest traffic at the earliest Layer 3 boundary. Preserves guest Internet browsing and dynamic addressing while guaranteeing absolute isolation of medical subnets.
* **Negative:** Requires precise rule ordering; misconfiguring the order could expose internal server ports.

---

## ADR-06: Dedicated Voice VLAN Architecture and Auxiliary Frame Tagging

* **Status:** Accepted
* **Date:** 2026-10-07
* **Deciders:** Rohit Kathiravan, Karthikeyan S

### Context
Real-time VoIP traffic and patient telemetry must be prioritized over bulk imaging. The initial Review-1 proposal lacked an isolated Voice VLAN, implying VoIP phones would share the access VLAN with data PCs. Sharing broadcast domains allows PC broadcast storms to induce jitter/latency on voice calls and creates an eavesdropping vulnerability (sniffing doctor-patient consultations via ARP spoofing).

### Options Considered
1. **Option 1 (Shared Data/Voice VLAN):** Single VLAN per floor for both PCs and IP phones.
   * *Pros:* Fewer VLANs and subnets.
   * *Cons:* No QoS isolation, high jitter, severe medical compliance/privacy violation.
2. **Option 2 (Dedicated Auxiliary Voice VLAN 60):** Provision dedicated VLAN 60 (`172.16.6.0/25`). Configure access switch ports with `switchport mode access`, `switchport access vlan <data>`, and `switchport voice vlan 60`.

### Decision
Adopt **Option 2**. Deploy dedicated Voice VLAN 60 across both campuses.

### Consequences
* **Positive:** Cisco IP phones separate voice traffic into 802.1Q tagged frames with 802.1p CoS 5, while daisy-chained PC traffic remains untagged in the data VLAN. Prevents eavesdropping and eliminates PC broadcast contention.
* **Negative:** Requires DHCP server to provide Option 150/66 for IP phone TFTP configuration.

---

## ADR-07: QoS Trust Boundary Placement and Layer 3 DSCP Marking Strategy

* **Status:** Accepted
* **Date:** 2026-10-07
* **Deciders:** Rohit Kathiravan, Karthikeyan S

### Context
Review-1 proposed marking traffic at "the edge". However, untrusted guest devices and staff PCs could deliberately mark their bulk downloads with `DSCP EF` (46) to hijack the high-priority queue, starving ICU patient telemetry.

### Options Considered
1. **Option 1 (Trust at Host Port):** Trust all incoming DSCP/CoS markings from edge access switch ports.
   * *Pros:* Simple switch configuration.
   * *Cons:* Critical security flaw; open to QoS theft and denial-of-service against ICU monitors.
2. **Option 2 (Enforce Strict Trust Boundary at Access Layer, Remark at Distribution):** Treat all access switch ports as untrusted by default, resetting incoming DSCP to 0 (Best Effort). Trust markings only on designated medical IoT ports and IP phones. At the distribution layer (SW-D1/D2), use class-maps to enforce marking:
   * UDP Telemetry & Voice -> `DSCP EF` (46)
   * TCP Imaging (DICOM/PACS) -> `DSCP AF31` (26)
   * All other traffic -> `DSCP 0` (Best Effort)

### Decision
Adopt **Option 2**. Establish the trust boundary at the access switch port; enforce deterministic DSCP marking at the Layer 3 distribution tier.

### Consequences
* **Positive:** Rogue endpoints cannot hijack priority queues. Guarantees deterministic low latency for bedside telemetry.
* **Negative:** Requires maintaining classification ACLs on distribution switches.

---

## ADR-08: Link Aggregation (EtherChannel / LACP) vs. STP Port Blocking

* **Status:** Accepted
* **Date:** 2026-10-07
* **Deciders:** Rohit Kathiravan, Karthikeyan S

### Context
Review-1 specified that SW-D1 and SW-D2 are cross-linked with Spanning Tree Protocol (STP) blocking one redundant link. Classic STP port blocking leaves 50% of costly inter-distribution bandwidth completely unused and introduces a 1–3 second reconvergence delay during link cuts, causing dropped clinical sessions.

### Options Considered
1. **Option 1 (STP Active/Blocking - Review-1):** Single link active, redundant link blocked by PVST+.
   * *Pros:* Minimal configuration.
   * *Cons:* 50% wasted bandwidth; failover causes brief packet loss and STP topology change notifications.
2. **Option 2 (IEEE 802.3ad LACP EtherChannel Bundle):** Combine physical links `Gig0/1` and `Gig0/2` into Port-Channel 1 using LACP (`channel-group 1 mode active`).
   * *Pros:* 2 Gbps aggregate full-duplex bandwidth, active-active load balancing, sub-millisecond hardware failover if one link is severed, zero STP recalculation.
   * *Cons:* Requires matching speed, duplex, trunking, and native VLAN configurations across both member ports.

### Decision
Adopt **Option 2**. Bundle inter-distribution links into an active LACP EtherChannel (Port-Channel 1).

### Consequences
* **Positive:** Doubles backplane throughput between SW-D1 and SW-D2; guarantees lossless failover if a fiber strand breaks.
* **Negative:** Configuration errors on member ports can cause channel misconfiguration guard to shut down the interface.

---

## ADR-09: Inter-Site OSPF Route Summarisation at the ABR Boundary

* **Status:** Accepted
* **Date:** 2026-10-07
* **Deciders:** Rohit Kathiravan, Karthikeyan S

### Context
The Remote Clinic hosts 5 discrete subnets (Clinical, Admin, Guest, Voice, Management). Without route summarisation, Core Router R2 injects 5 separate Type-3 Summary LSAs across the serial WAN into Area 0. Any temporary port flap or DHCP renew inside the clinic causes LSA flooding and routing table recomputation across the Main Hospital Core.

### Options Considered
1. **Option 1 (No Summarisation):** Advertise all discrete `/27` and `/28` subnets into Area 0.
   * *Pros:* Specific routing entries.
   * *Cons:* WAN overhead; Core router CPU churn on remote link flaps.
2. **Option 2 (ABR Area Range Aggregation):** Group all Remote Clinic subnets within a contiguous CIDR boundary (`172.16.6.128` through `172.16.8.78`) and configure `area 1 range 172.16.0.0 255.255.240.0` on Core Router R2.

### Decision
Adopt **Option 2**. Configure OSPF route summarisation on ABR R2.

### Consequences
* **Positive:** Replaces multiple discrete LSAs with a single summary LSA in Backbone Area 0. Flapping links inside the clinic are completely hidden from Core Router R1.
* **Negative:** If a summary route is active, traffic destined for an unassigned IP in the summary block will be routed to R2 before being dropped by Null0.

---

## ADR-10: Multi-Tier Verification Strategy for Packet Tracer Emulation Boundaries

* **Status:** Accepted
* **Date:** 2026-10-07
* **Deciders:** Rohit Kathiravan, Karthikeyan S

### Context
Cisco Packet Tracer 8.x is an educational discrete-event simulator with well-documented feature limitations:
1. It does not enforce true Low-Latency Queuing (LLQ) or CBWFQ hardware packet drops during high-bandwidth link saturation.
2. The SBC-PT Python environment lacks the standard Berkeley `socket` module for direct socket-to-socket cross-network communication.
3. It does not support stateful Layer 7 deep packet inspection (DPI) for medical protocols.

### Options Considered
1. **Option 1 (Ignore Limitations):** Claim in the report that QoS and socket communications work natively in Packet Tracer.
   * *Pros:* Less documentation work.
   * *Cons:* Dishonest; easily exposed and penalized during examiner viva demonstration.
2. **Option 2 (Hybrid Multi-Tier Validation Framework):**
   * Demonstrate syntax and configuration correctness inside Cisco IOS (`show policy-map`, `show access-lists`, `show ip route`).
   * Inspect Simulation Mode PDU headers to verify Layer 3 TOS/DSCP marking bytes (`0xB8` for EF, `0x68` for AF31) and TCP three-way handshakes.
   * Execute standalone Python scripts inside the SBC-PT **Programming** and **Terminal** tabs to prove algorithmic correctness for 2-D parity, checksums, GBN, and Selective Repeat.
   * Execute host-side Python test harnesses (`sim/benchmark_harness.py`, `tests/test_vlsm.py`) to generate empirical CSV tables and Matplotlib performance plots under simulated packet loss.

### Decision
Adopt **Option 2**. Implement a transparent hybrid verification model that pairs Packet Tracer simulation with host-side analytical benchmarking.

### Consequences
* **Positive:** 100% academic integrity. Demonstrates deep understanding of simulator boundaries and production engineering validation methods.
* **Negative:** Requires maintaining both in-PT scripts and host-side test harnesses.
