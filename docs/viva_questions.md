# Disaster-Resilient Smart Hospital Network: Viva Voce Comprehensive Question Bank & Examination Defense Guide
**Document ID:** DOC-VIVA-2026-v1.0  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  
**Academic Institution:** School of Computer Science and Engineering (SCOPE), VIT Vellore  
**Course Code:** CSE2004 — Computer Networks  
**Scope:** 65 Curated Examiner Questions, Model Answers, Worked Mathematical Proofs, Design Trade-Off Justifications, and 5-Minute Live Demo Script

---

## Table of Contents
1. [Topic 1: VLSM Calculation Walkthroughs & IP Subnetting (Q1 - Q5)](#topic-1-vlsm-calculation-walkthroughs--ip-subnetting)
2. [Topic 2: Spanning Tree Protocols (STP & Rapid-PVST+) (Q6 - Q10)](#topic-2-spanning-tree-protocols-stp--rapid-pvst)
3. [Topic 3: First-Hop Redundancy Protocols (HSRP) (Q11 - Q15)](#topic-3-first-hop-redundancy-protocols-hsrp)
4. [Topic 4: OSPF Architecture, Areas, LSA Types & Elections (Q16 - Q22)](#topic-4-ospf-architecture-areas-lsa-types--elections)
5. [Topic 5: EIGRP Architecture, DUAL & Feasibility Condition (Q23 - Q26)](#topic-5-eigrp-architecture-dual--feasibility-condition)
6. [Topic 6: Administrative Distance & Route Selection (Q27 - Q29)](#topic-6-administrative-distance--route-selection)
7. [Topic 7: Access Control Lists (ACLs) & Wildcard Masks (Q30 - Q34)](#topic-7-access-control-lists-acls--wildcard-masks)
8. [Topic 8: Network Address Translation (NAT/PAT) (Q35 - Q38)](#topic-8-network-address-translation-natpat)
9. [Topic 9: Quality of Service (QoS) & DiffServ Architecture (Q39 - Q44)](#topic-9-quality-of-service-qos--diffserv-architecture)
10. [Topic 10: Error Detection, CRC & 2D Parity Mathematics (Q45 - Q49)](#topic-10-error-detection-crc--2d-parity-mathematics)
11. [Topic 11: Sliding-Window Flow Control & ARQ Protocols (Q50 - Q54)](#topic-11-sliding-window-flow-control--arq-protocols)
12. [Topic 12: Transport Layer: TCP Flow, Congestion & UDP Mechanics (Q55 - Q59)](#topic-12-transport-layer-tcp-flow-congestion--udp-mechanics)
13. [Topic 13: Architectural Trade-Offs: "Why Choose X over Y?" (Q60 - Q65)](#topic-13-architectural-trade-offs-why-choose-x-over-y)
14. [5-Minute Live Demonstration Script & Emergency Fallback Runbook](#5-minute-live-demonstration-script--emergency-fallback-runbook)

---

## Topic 1: VLSM Calculation Walkthroughs & IP Subnetting

### Q1: Walk through the exact VLSM calculation for allocating the ICU Telemetry subnet with 25 required host devices from base network 172.16.0.0/16.
**Model Answer:**
1. **Formula:** Usable host addresses on a subnet with $h$ host bits is given by $N_{\text{usable}} = 2^h - 2$.
2. **Determine Host Bits ($h$):** For 25 hosts: $2^h - 2 \ge 25 \implies 2^h \ge 27$. For $h=4$, $2^4 - 2 = 14$ (insufficient). For $h=5$, $2^5 - 2 = 30 \ge 25$. Thus, exactly $h = 5$ host bits are required.
3. **Determine Subnet Prefix ($p$):** $p = 32 - h = 32 - 5 = /27$.
4. **Subnet Mask:** A /27 prefix has 27 network ones:
   `11111111.11111111.11111111.11100000` $\implies 255.255.255.224$.
5. **Block Size & Range (for subnet 172.16.8.32/27):**
   - Block size in 4th octet $= 2^5 = 32$.
   - Network Address: `172.16.8.32`
   - First Usable Host: `172.16.8.33` (Assigned to HSRP VIP)
   - Last Usable Host: `172.16.8.62`
   - Broadcast Address: `172.16.8.63`
   - Utilization Efficiency: $25 / 30 = 83.33\%$.

### Q2: Why are point-to-point router links allocated /30 subnets instead of /24, and what is the mathematical efficiency?
**Model Answer:**
A point-to-point link (e.g., between R1 and R2 across a serial cable) requires exactly two endpoints. If a traditional Class C /24 subnet ($255.255.255.0$) were allocated, it would waste $254 - 2 = 252$ IP addresses (0.78% utilization). A /30 prefix provides $h = 32 - 30 = 2$ host bits, yielding $2^2 - 2 = 2$ usable IP addresses. This achieves **100% address utilization** ($2/2$) with zero wasted assignable host IPs. (Note: RFC 3021 defines /31 for point-to-point links on modern hardware, but Cisco Packet Tracer standard switches require /30 due to legacy broadcast address reservation).

### Q3: What is the Wildcard Mask corresponding to subnet mask 255.255.255.240, and how is it derived mathematically?
**Model Answer:**
A wildcard mask is the bitwise inverse of the subnet mask:
$$\text{Wildcard Mask} = 255.255.255.255 - \text{Subnet Mask}$$
For mask $255.255.255.240$ (/28 prefix):
- Octet 1: $255 - 255 = 0$
- Octet 2: $255 - 255 = 0$
- Octet 3: $255 - 255 = 0$
- Octet 4: $255 - 240 = 15$
Thus, the wildcard mask is **`0.0.0.15`**. In binary, the leading 28 zeros indicate bits that must match exactly, while the trailing 4 ones represent "don't care" bits covering the 16 IP addresses in the block.

### Q4: If an examiner asks you to carve a subnet for 100 hospital hosts, which prefix length do you pick, and why not /26?
**Model Answer:**
To accommodate 100 hosts:
- For /26: $h = 32 - 26 = 6$. Usable hosts $= 2^6 - 2 = 64 - 2 = 62$ hosts. (Insufficient; $62 < 100$).
- For /25: $h = 32 - 25 = 7$. Usable hosts $= 2^7 - 2 = 128 - 2 = 126$ hosts.
Therefore, a **/25 prefix** ($255.255.255.128$) is mathematically mandatory. It provides 126 usable host addresses, accommodating the 100 required hosts while leaving 26 addresses for clinical expansion.

### Q5: How does DHCP relay work across subnets, and why does an SVI need `ip helper-address`?
**Model Answer:**
DHCP Discover messages are Layer 2 broadcasts (`FF:FF:FF:FF:FF:FF`) with destination IP `255.255.255.255`. Routers and Layer 3 switches drop broadcast packets by default to prevent broadcast radiation. When a client on VLAN 10 broadcasts a DHCP Discover, the switch virtual interface (SVI) configured with `ip helper-address 172.16.5.10` acts as an RFC 1542 BOOTP Relay Agent. The switch converts the broadcast into a Layer 3 unicast packet, populates the `giaddr` (Gateway IP Address) field with its own SVI IP (`172.16.8.33`), and forwards it directly to the centralized DHCP server on VLAN 50. The server uses `giaddr` to match the correct pool (`POOL-ICU-TELEMETRY`) and assigns an address from that specific subnet.

---

## Topic 2: Spanning Tree Protocols (STP & Rapid-PVST+)

### Q6: What is the fundamental difference between legacy IEEE 802.1D STP and IEEE 802.1w Rapid-PVST+ in terms of convergence time?
**Model Answer:**
Legacy 802.1D STP relies on passive, timer-driven transitions through Blocking $\rightarrow$ Listening (15s Forward Delay) $\rightarrow$ Learning (15s Forward Delay) $\rightarrow$ Forwarding, requiring **30 to 50 seconds** to recover from a link failure. In contrast, IEEE 802.1w Rapid-PVST+ collapses port states into Discarding, Learning, and Forwarding, and utilizes an explicit, active **Proposal/Agreement handshake** on point-to-point links. When a root link fails, an alternate port immediately synchronizes with its neighbor and unblocks directly to Forwarding in **under 1.0 second** (typically $< 50\text{ ms}$ on physical ASICs), completely bypassing timer delays.

### Q7: Explain how the Spanning Tree Root Bridge is elected. What parameters determine the winner?
**Model Answer:**
The switch with the lowest **Bridge ID (BID)** is elected Root Bridge. The BID consists of:
$$\text{Bridge ID} = \text{Bridge Priority (4 bits)} + \text{Extended System ID (VLAN ID, 12 bits)} + \text{MAC Address (48 bits)}$$
1. Bridge Priority is evaluated first in increments of 4096. A switch configured with priority 4096 beats the default priority of 32768.
2. If priorities are identical, the switch with the lowest hardware MAC address breaks the tie. In our hospital design, SW-D1 is explicitly configured with `spanning-tree vlan 10,30,50 root primary` (Priority 4096), deterministically guaranteeing that it wins the root bridge election over access switches.

### Q8: What are the three port roles introduced in 802.1w that did not exist in 802.1D?
**Model Answer:**
1. **Alternate Port:** A backup path to the Root Bridge that receives BPDUs from another switch (replaces 802.1D non-designated/blocking port). It can immediately transition to Root Port if the primary Root Port fails.
2. **Backup Port:** A redundant path to a shared segment that receives BPDUs from the same switch (typically on shared hubs).
3. **Edge Port:** A port connected directly to an end host (enabled via Cisco PortFast) that transitions immediately to Forwarding and never generates Topology Change Notifications (TCNs).

### Q9: Why is BPDU Guard essential on access ports configured with PortFast?
**Model Answer:**
PortFast causes an access port to bypass listening and learning states, transitioning immediately to forwarding. If a user or attacker accidentally loops an Ethernet cable or connects an unauthorized switch to a PortFast port, a catastrophic broadcast storm would occur before STP could detect the loop. **BPDU Guard** monitors the edge port; if any BPDU is received on that interface, the switch immediately places the port into `err-disable` state (shutting down the port), neutralizing the loop risk before traffic can circulate.

### Q10: What is a Topology Change Notification (TCN), and how does RSTP handle it differently from 802.1D?
**Model Answer:**
In legacy 802.1D, a switch experiencing a link transition sends a TCN towards the Root Bridge, which then sets the TC flag in configuration BPDUs for Max Age + Forward Delay (35s), causing all switches to shorten their CAM aging timer from 300s to 15s. In RSTP (802.1w), only non-edge ports moving to Forwarding generate a TC. The detecting switch directly floods a BPDU with the TC bit set out all non-edge designated and root ports for two hello intervals, and immediately flushes all MAC entries learned on non-edge ports (except the port that received the TC). This achieves instantaneous enterprise-wide MAC table re-learning.

---

## Topic 3: First-Hop Redundancy Protocols (HSRP)

### Q11: Explain the roles of Active, Standby, and Virtual Router in Cisco HSRP.
**Model Answer:**
- **Virtual Router:** A logical entity defined by a shared Virtual IP address (VIP) and a standardized Virtual MAC address (e.g., `0000.0c07.ac0a` for HSRPv1 group 10). Host devices configure the VIP as their static default gateway.
- **Active Router:** The physical switch/router that actively receives and forwards frames sent to the Virtual MAC, and responds to host ARP requests for the VIP.
- **Standby Router:** The backup switch/router that monitors periodic multicast HSRP hellos from the Active router. It does not forward traffic for the VIP until the Active router's hold timer expires.

### Q12: What are the default HSRP Hello and Hold timers, and what happens when the Hold timer expires?
**Model Answer:**
- **Default Hello Timer:** 3.0 seconds (transmitted via multicast to `224.0.0.2` on UDP port 1985).
- **Default Hold Timer:** 10.0 seconds (approximately $3 \times \text{Hello} + 1\text{s}$).
- When 10 consecutive seconds elapse without receiving a valid Hello from the Active router, the Standby router assumes the Active router has failed. The Standby router transitions through `Speak` state to `Active`, transmits a gratuitous ARP to update Layer 2 switch CAM tables with the virtual MAC, and begins routing traffic for the VIP.

### Q13: Why is the `preempt` command critical in HSRP? What happens without it?
**Model Answer:**
Without the `preempt` command, if the primary switch (`SW-D1`, priority 120) reboots after a power failure, it will remain in `Standby` state even after coming back online, because the secondary switch (`SW-D2`, priority 110) is already active. HSRP by default does not dethrone an active router merely because a higher-priority device appears. With `standby 10 preempt`, `SW-D1` immediately detects that its priority ($120 > 110$) is higher than the current active router, triggers a role renegotiation, and reclaims active gateway status.

### Q14: How is the HSRP Virtual MAC address structured in HSRPv1 versus HSRPv2?
**Model Answer:**
- **HSRPv1:** Formatted as `0000.0C07.ACxx`, where:
  - `0000.0C`: Cisco OUI (Vendor ID).
  - `07.AC`: HSRP Well-Known Protocol Code.
  - `xx`: Hexadecimal representation of the HSRP Group ID (e.g., Group 10 is `0x0A`, producing `0000.0C07.AC0A`). Group range is 0 to 255.
- **HSRPv2:** Formatted as `0000.0C9F.Fxxx`, supporting expanded group numbers from 0 to 4095 and utilizing multicast IP `224.0.0.102`.

### Q15: How did your design achieve active-active load sharing across dual distribution switches using HSRP?
**Model Answer:**
Standard HSRP is active-standby per SVI. To achieve active-active hardware utilization across both distribution switches, we configured split gateway roles:
- On **SW-D1:** Configured with Priority 120 (Active) for VLANs 10, 30, and 50, and Priority 110 (Standby) for VLANs 20, 40, and 60.
- On **SW-D2:** Configured with Priority 120 (Active) for VLANs 20, 40, and 60, and Priority 110 (Standby) for VLANs 10, 30, and 50.
Under normal operations, both switches forward traffic simultaneously: SW-D1 routes ICU telemetry and admin traffic, while SW-D2 routes operating theatre and diagnostic imaging traffic. If either switch fails, the surviving switch assumes 100% of gateway duties.

---

## Topic 4: OSPF Architecture, Areas, LSA Types & Elections

### Q16: Why did you partition the hospital network into multiple OSPF areas instead of running a single flat Area 0?
**Model Answer:**
In a large network, running a single flat OSPF area causes every link flap or topology change to trigger an SPF (Dijkstra) calculation on every single router in the entire enterprise. Furthermore, every router must maintain identical Link-State Databases (LSDB), consuming excessive CPU and RAM. Partitioning into a multi-area hierarchy (Area 0 Core Backbone, Area 1 Main Hospital Campus, Area 2 Remote Clinic) confines Type-1 and Type-2 LSAs within their local area boundaries. Changes within the Remote Clinic do not trigger SPF recalculations across Main Hospital distribution switches, and enables inter-area route summarization at Area Border Routers (ABRs).

### Q17: Name the five primary OSPF LSA types and their functions.
**Model Answer:**
1. **Type 1 (Router LSA):** Generated by every router in an area; describes its local interfaces, links, and direct neighbors. Flooded strictly within that area.
2. **Type 2 (Network LSA):** Generated by the Designated Router (DR) on multi-access broadcast segments; lists all routers attached to that transit link.
3. **Type 3 (Summary LSA):** Generated by Area Border Routers (ABRs); advertises internal subnets from one area into other areas.
4. **Type 4 (ASBR Summary LSA):** Generated by an ABR; advertises the route to an Autonomous System Boundary Router (ASBR) to outside areas.
5. **Type 5 (AS External LSA):** Generated by an ASBR; advertises external routes redistributed into OSPF (e.g., default route to the ISP). Flooded throughout all non-stub areas.

### Q18: What are the criteria for electing the OSPF Designated Router (DR) and Backup Designated Router (BDR)?
**Model Answer:**
On multi-access broadcast networks (such as Ethernet VLANs), a DR and BDR are elected to avoid $N(N-1)/2$ full neighbor adjacencies:
1. **OSPF Interface Priority:** Routers with higher priority win (range 0-255, default 1). Priority 0 disqualifies a router from election.
2. **Router ID (RID):** If priorities tie, the router with the highest 32-bit Router ID wins. The RID is determined by: (a) explicit `router-id` command, (b) highest active Loopback IP, or (c) highest active physical interface IP.
3. **Non-Preemptive:** Once elected, a DR cannot be preempted by a newly introduced router with higher priority until the DR process is reloaded. On point-to-point links (e.g., Serial links), DR/BDR election is bypassed entirely.

### Q19: What is the OSPF metric formula, and how did you configure primary vs. backup WAN serial link failover?
**Model Answer:**
OSPF metric (cost) is inversely proportional to link bandwidth:
$$\text{Cost} = \frac{\text{Reference Bandwidth}}{\text{Interface Bandwidth}} = \frac{10^8 \text{ bps (100 Mbps)}}{\text{Bandwidth in bps}}$$
For primary and backup serial WAN failover:
- On primary interface `Serial0/0/0`, we configured `ip ospf cost 64` (representing 1.544 Mbps T1).
- On secondary backup interface `Serial0/0/1`, we configured `ip ospf cost 500`.
Because OSPF's Dijkstra algorithm strictly selects the shortest cumulative cost path, all inter-campus traffic routes over `Serial0/0/0` ($64 < 500$). If `Serial0/0/0` drops, OSPF detects carrier loss, withdraws the LSA, and immediately installs the backup route via `Serial0/0/1` in 1.74 seconds.

### Q20: What are the conditions required for two OSPF routers to form an adjacency (`FULL` state)?
**Model Answer:**
Two neighboring routers must match on the following parameters in their Hello packets:
1. **Area ID** (must belong to the exact same area number).
2. **Subnet IP and Subnet Mask** on the connecting link.
3. **Hello and Dead Intervals** (default 10s and 40s on broadcast).
4. **Authentication Type and Pre-Shared Key** (if configured).
5. **Area Type Flags** (Stub, NSSA, or Standard).
6. **Unique Router IDs** (no duplicate RIDs).
7. **Matching MTU** (if MTU mismatches, routers stall in `EXSTART` or `EXCHANGE` state).

### Q21: What is a Passive Interface in OSPF, and where was it deployed in your hospital network?
**Model Answer:**
A passive interface stops transmitting and listening for OSPF multicast Hello packets (`224.0.0.5`), preventing neighbor adjacencies from forming on that port, while still advertising the interface's connected subnet into OSPF. In our design, all client-facing SVIs (VLAN 10, 20, 30, 40, 60) and access switch ports were configured with `passive-interface`. This prevents clinical workstations or guest laptops from injecting malicious routing updates or establishing unauthorized OSPF adjacencies.

### Q22: How does OSPF achieve loop-free routing?
**Model Answer:**
Within an area, OSPF is inherently loop-free because every router possesses an identical copy of the Link-State Database (LSDB), representing a full directed graph of the network. Each router runs Dijkstra's Shortest Path First (SPF) algorithm placing itself as the root of a Shortest Path Tree, which mathematically guarantees that no cyclic loops can exist. Between areas, OSPF enforces a strict two-level star hierarchy where all non-backbone areas must connect directly to Area 0, preventing inter-area loops.

---

## Topic 5: EIGRP Architecture, DUAL & Feasibility Condition

### Q23: Explain the Diffusing Update Algorithm (DUAL) and how it guarantees loop-free convergence.
**Model Answer:**
DUAL is Cisco's patented finite state machine that governs EIGRP routing calculations. Instead of periodic global updates, DUAL maintains localized topology tables and performs instantaneous distributed computations. It guarantees loop-free routing by enforcing that a router only accepts an alternate path without calculation if that path satisfies the **Feasibility Condition (FC)**. If no feasible successor exists, DUAL transitions the route to `Active` state and queries neighbors, ensuring an alternate loop-free route is mathematically proven before installation.

### Q24: Define Feasible Distance (FD), Reported Distance (RD / AD), Successor, and Feasible Successor.
**Model Answer:**
- **Successor:** The primary neighbor router with the lowest metric to the destination, installed in the routing table.
- **Feasible Distance (FD):** The best metric computed along the path through the Successor to the destination.
- **Reported Distance (RD) / Advertised Distance (AD):** The metric advertised by an adjacent neighbor as its own cost to reach that destination.
- **Feasible Successor (FS):** A backup loop-free neighbor that satisfies the Feasibility Condition, ready to take over instantaneously if the Successor fails.

### Q25: State the Feasibility Condition mathematically. Why is it strictly `<` and not `\le`?
**Model Answer:**
$$\text{Feasibility Condition:} \quad \text{Reported Distance (RD)} < \text{Feasible Distance (FD of current Successor)}$$
It is strictly less-than ($<$) because if $\text{RD} \ge \text{FD}$, the neighbor's path to the destination might traverse the local router itself, creating a potential routing loop. If $\text{RD} < \text{FD}$, it is mathematically impossible for the neighbor's path to loop through the local router, because the neighbor is measurably closer to the destination than the local router currently is.

### Q26: What is the composite metric formula for EIGRP?
**Model Answer:**
Using default $K$-values ($K_1 = 1, K_2 = 0, K_3 = 1, K_4 = 0, K_5 = 0$):
$$\text{Metric} = 256 \times \left[ \left( \frac{10^7}{\text{Bandwidth}_{\min} \text{ in kbps}} \right) + \sum \left( \frac{\text{Delay in } \mu\text{s}}{10} \right) \right]$$
Metric evaluates the slowest bandwidth along the entire path and the cumulative sum of interface delays, scaled by 256 to provide a 32-bit metric value.

---

## Topic 6: Administrative Distance & Route Selection

### Q27: Define Administrative Distance (AD). How does a router choose between OSPF, EIGRP, and Static routes for the same destination prefix?
**Model Answer:**
Administrative Distance is an integer value from 0 to 255 representing the **trustworthiness** or believability of a routing information source. When a router learns the exact same destination IP prefix from multiple routing protocols with different algorithms, it installs the route with the **lowest Administrative Distance** into the forwarding table (FIB).
- Connected Interface: $\text{AD} = 0$
- Static Route: $\text{AD} = 1$
- EIGRP (Internal): $\text{AD} = 90$
- OSPF: $\text{AD} = 110$
- RIP: $\text{AD} = 120$
- External EIGRP: $\text{AD} = 170$
If an OSPF route (110) and a Static route (1) exist for `172.16.5.0/24`, the Static route is installed.

### Q28: How does the router select between two routes learned via the SAME protocol with different prefix lengths?
**Model Answer:**
Administrative Distance is only evaluated when comparing identical prefix lengths from different protocols. When comparing routes with different prefix lengths, the router strictly enforces **Longest Prefix Match (LPM)** regardless of AD or protocol. For example, a packet destined for `172.16.5.10` will match a `/28` route over a `/24` route, and a `/24` route over a default route `0.0.0.0/0`, because the more specific mask has more leading matching network bits.

### Q29: What is a Floating Static Route, and what Administrative Distance would you assign to back up OSPF?
**Model Answer:**
A floating static route is a static route configured with an Administrative Distance higher than that of the active dynamic routing protocol. Because its AD is higher, it remains inactive and hidden from the routing table during normal operations. To back up OSPF (which has $\text{AD} = 110$), the floating static route is assigned an AD of **115 or 120**:
```ios
ip route 172.16.6.0 255.255.255.0 172.16.8.86 115
```
If OSPF loses all routes to `172.16.6.0/24`, OSPF withdraws the route from the table, allowing the floating static route to float to the top and restore connectivity.

---

## Topic 7: Access Control Lists (ACLs) & Wildcard Masks

### Q30: Differentiate between Standard and Extended IPv4 Access Control Lists in terms of numbering, matching capabilities, and optimal placement.
**Model Answer:**
- **Standard ACLs (1-99, 1300-1999):** Inspect **Source IP address only**. Because they cannot inspect destination IPs or port numbers, they must be placed **as close to the destination as possible**; placing them close to the source would unintentionally block traffic destined for other valid services.
- **Extended ACLs (100-199, 2000-2699):** Inspect **Source IP, Destination IP, Protocol (TCP/UDP/ICMP), and Layer 4 Port numbers**. They must be placed **as close to the source as possible** to drop unauthorized traffic immediately, preserving downstream link bandwidth.

### Q31: Explain the implicit `deny any` at the end of every Cisco IOS ACL and how it impacts traffic.
**Model Answer:**
Every Cisco IOS Access Control List terminates with an unwritten, invisible default rule: `deny ip any any`. When a packet is evaluated against an ACL, the router tests entries sequentially from top to bottom. If a packet does not match any explicit `permit` statement, it falls through to the end and is silently dropped by the implicit deny. Therefore, any ACL containing `permit` statements must explicitly allow all required traffic, or include an explicit `permit ip any any` at the bottom if configured as a blacklist filter.

### Q32: Write an Extended Named ACL rule that permits HTTP and HTTPS traffic from subnet 172.16.7.0/24 to any public destination, but blocks all internal hospital subnets (172.16.0.0/16).
**Model Answer:**
```ios
ip access-list extended ACL-GUEST-ISOLATE
 deny   ip 172.16.7.0 0.0.0.255 172.16.0.0 0.0.255.255
 permit tcp 172.16.7.0 0.0.0.255 any eq 80
 permit tcp 172.16.7.0 0.0.0.255 any eq 443
 permit udp 172.16.7.0 0.0.0.255 any eq 53
 deny   ip any any
```
The first rule blocks any packet from Guest Wi-Fi targeting hospital internal RFC 1918 addresses. The subsequent rules allow web browsing and public DNS resolution.

### Q33: What is the `established` keyword in a TCP Extended ACL, and how does it provide primitive statefulness?
**Model Answer:**
The `established` keyword in an extended ACL checks the TCP control flags in the Layer 4 header. It matches any TCP segment where either the **ACK (Acknowledgment)** or **RST (Reset)** flag bit is set to 1. Because initial connection requests (SYN packets) have ACK=0, incoming packets from the outside with ACK=0 are dropped, while incoming packets responding to an outbound session initiated by an internal client have ACK=1 and are permitted. This provides lightweight unidirectional pseudo-stateful filtering.

### Q34: What is the difference between applying an ACL `in` versus `out` on an interface?
**Model Answer:**
- **Inbound (`in`):** Packets are filtered **before** the router performs a routing table lookup or NAT translation. Dropping packets inbound saves CPU cycles because the routing engine never has to process unroutable or forbidden packets.
- **Outbound (`out`):** Packets are processed after the routing lookup determines the egress interface, just before the packet is queued on the physical transmission wire.

---

## Topic 8: Network Address Translation (NAT/PAT)

### Q35: Explain the difference between Static NAT, Dynamic NAT, and Port Address Translation (PAT / NAT Overload).
**Model Answer:**
- **Static NAT:** One-to-one mapping between a single private IP and a single public IP. Used for public-facing servers (e.g., EHR portal mapped to `203.0.113.2`).
- **Dynamic NAT:** Many-to-many mapping from a pool of public IPs. A private host is temporarily assigned an available public IP from the pool; when the pool is exhausted, subsequent hosts are blocked.
- **Port Address Translation (PAT / Overload):** Many-to-one mapping where thousands of internal hosts share a single public IP address. The router tracks individual connections by modifying and multiplexing unique Layer 4 source port numbers ($> 1024$).

### Q36: Define the four Cisco NAT address terms: Inside Local, Inside Global, Outside Local, Outside Global.
**Model Answer:**
- **Inside Local:** The private RFC 1918 IP address assigned to an internal host on the hospital LAN (e.g., `172.16.8.40`).
- **Inside Global:** The publicly routable IP address that represents the inside host to the outside world after translation (e.g., `203.0.113.2`).
- **Outside Global:** The real public IP address assigned to an external host on the Internet (e.g., `203.0.113.1` on ISP).
- **Outside Local:** The IP address of an outside host as it appears to internal network hosts (usually identical to Outside Global).

### Q37: Write the Cisco IOS configuration commands to implement PAT (NAT Overload) on Core Router R1 for internal network 172.16.0.0/16 out interface GigabitEthernet0/2.
**Model Answer:**
```ios
ip access-list standard NAT-CLIENTS
 permit 172.16.0.0 0.0.255.255

interface GigabitEthernet0/1
 ip nat inside

interface GigabitEthernet0/2
 ip nat outside

ip nat inside source list NAT-CLIENTS interface GigabitEthernet0/2 overload
```

### Q38: Why does NAT break certain clinical application protocols, and how do Application Layer Gateways (ALGs) resolve this?
**Model Answer:**
Basic NAT only modifies Layer 3 IP headers and Layer 4 TCP/UDP port headers. Certain protocols—such as FTP (active mode), SIP VoIP, and DICOM medical imaging—embed IP addresses and dynamic data port numbers inside the application payload itself. When NAT translates the outer IP header, the embedded payload IP remains private, causing remote endpoints to attempt connections to unroutable RFC 1918 addresses. Application Layer Gateways (ALGs) inspect the application payload, rewrite the embedded addresses, and dynamically open pinhole ports in the firewall.

---

## Topic 9: Quality of Service (QoS) & DiffServ Architecture

### Q39: Differentiate between Best Effort, Integrated Services (IntServ), and Differentiated Services (DiffServ) QoS models.
**Model Answer:**
- **Best Effort:** Default FIFO queuing. All packets are treated equally with zero QoS guarantees. Packets are dropped indiscriminately during congestion.
- **IntServ (RFC 1633):** Hard QoS model using RSVP signaling to reserve end-to-end bandwidth before data flows. Highly unscalable because every router along the path must maintain per-flow state.
- **DiffServ (RFC 2474):** Soft QoS model that marks packets at the network ingress with a 6-bit DSCP value in the IP header. Intermediate routers enforce Per-Hop Behaviors (PHBs) via queue scheduling (PQ, WFQ) without maintaining per-flow state, providing enterprise scalability.

### Q40: What is DSCP Expedited Forwarding (EF), what is its numerical value, and why was it chosen for patient vitals telemetry?
**Model Answer:**
Expedited Forwarding (EF, RFC 3246) is designed for low-loss, low-latency, low-jitter traffic.
- **Binary DSCP:** `101110` (Decimal 46).
- **Type of Service (ToS) Byte:** Left-shifted by 2 bits, yielding `0xB8` (binary `10111000`).
- It was chosen for patient telemetry because Cisco switches and routers place DSCP EF packets into strict **Priority Queues (PQ)**. Priority Queues are always serviced first ahead of any other traffic, guaranteeing that cardiac alarms encounter zero queueing delay even when links are saturated.

### Q41: Explain Assured Forwarding (AF) classes and drop precedence. What does AF31 mean?
**Model Answer:**
Assured Forwarding (RFC 2597) defines 4 traffic classes ($AF1$ through $AF4$) and 3 levels of drop precedence (Low = 1, Medium = 2, High = 3), represented as $AFxy$:
- $x$: Class number (1 to 4), where higher classes receive larger bandwidth allocations in Weighted Fair Queuing (WFQ).
- $y$: Drop precedence (1 to 3), where higher values are dropped first during congestion via Weighted Random Early Detection (WRED).
- **`AF31`** represents Class 3 traffic with **Low Drop Precedence** (Binary `011010`, Decimal 26, ToS `0x68`). In our design, it is assigned to PACS DICOM imaging transfers.

### Q42: Differentiate between Priority Queuing (PQ) and Weighted Fair Queuing (WFQ). What is queue starvation?
**Model Answer:**
- **Priority Queuing (PQ):** Strict priority scheduling where high-priority queues are completely drained before lower-priority queues receive any service. **Queue starvation** occurs if high-priority traffic exceeds link capacity, completely starving Best-Effort traffic. To prevent starvation, traffic policers cap PQ bandwidth (e.g., `priority 460` limits telemetry to 460 kbps).
- **Weighted Fair Queuing (WFQ):** Fair scheduling allocating bandwidth proportionally based on packet weight/precedence, guaranteeing that lower-priority queues always receive a baseline percentage of link capacity.

### Q43: What is the difference between Traffic Policing and Traffic Shaping?
**Model Answer:**
- **Policing:** Enforces a hard rate limit. Excess traffic above the committed rate is **immediately dropped** or remarked to a lower DSCP. It introduces zero latency and is typically applied on inbound interfaces.
- **Shaping:** Enforces a rate limit by **buffering excess packets** in memory queues and smoothing output bursts over time. It prevents packet loss but introduces queueing delay, and is applied outbound on WAN edges.

### Q44: What are the three steps in the Cisco MQC (Modular QoS CLI) framework?
**Model Answer:**
1. **Class Map (`class-map`):** Classifies traffic by matching ACLs, protocol types, or DSCP/CoS values (e.g., `match ip dscp ef`).
2. **Policy Map (`policy-map`):** Defines actions for each class (e.g., `priority`, `bandwidth percent`, `set dscp`).
3. **Service Policy (`service-policy`):** Applies the policy map to a physical interface or SVI inbound or outbound (`service-policy output PM-HOSPITAL-QOS`).

---

## Topic 10: Error Detection, CRC & 2D Parity Mathematics

### Q45: Walk through a complete binary division calculation for Cyclic Redundancy Check (CRC). Given data bitstring 110101 and generator polynomial G = 1011 (x^3 + x + 1), compute the transmitted codeword.
**Model Answer:**
1. **Determine Degree of Generator ($r$):**
   $G = 1011$ has degree $r = 4 - 1 = 3$.
2. **Append $r$ zeros to Data ($D$):**
   Data $D = 110101 \implies$ Augmented Data $D' = 110101000$.
3. **Modulo-2 Binary Division (XOR division):**
   ```
            111100  <-- Quotient
     1011 ) 110101000
            1011
            ----
             1100
             1011
             ----
              1111
              1011
              ----
               1000
               1011
               ----
                0110
                0000
                ----
                 1100
                 1011
                 ----
                  111  <-- Remainder (CRC Checksum R = 111)
   ```
4. **Construct Transmitted Codeword ($T$):**
   $T = D' \oplus R = 110101000 \oplus 111 = \mathbf{110101111}$.
5. **Receiver Verification:** Receiver divides $110101111$ by $1011$. If remainder is $000$, the transmission is error-free.

### Q46: How does a Two-Dimensional (2D) Parity Matrix detect and correct a single-bit error autonomously without retransmission?
**Model Answer:**
Data bytes are arranged into an $M \times N$ matrix (e.g., $6 \times 8$).
1. An even-parity bit is appended to each row (Horizontal Parity).
2. An even-parity bit is appended to each column (Vertical Parity).
3. If a single bit flips during transmission:
   - Exactly **one row parity check will fail** at row coordinate $i$.
   - Exactly **one column parity check will fail** at column coordinate $j$.
4. The receiver calculates the syndrome intersection $(i, j)$ which uniquely pinpoints the corrupted bit.
5. The receiver inverts bit $(i, j)$ from $0 \rightarrow 1$ or $1 \rightarrow 0$, achieving **1-bit autonomous self-healing**.

### Q47: Why can standard Single Parity not detect double-bit errors, and what is its Hamming Distance?
**Model Answer:**
Single parity adds one bit such that the total number of 1s is even. If two bits flip simultaneously ($00 \rightarrow 11$ or $11 \rightarrow 00$), the total parity count changes by $+2, -2$, or $0$. Because the parity count remains even, the error check passes undetected ($P_{\text{alias}} = 100\%$). The **Hamming Distance ($d_{\min}$)** of single parity is **2**. By coding theory, a code can detect up to $d_{\min} - 1 = 1$ error and correct $0$ errors.

### Q48: What types of errors does CRC-16-CCITT mathematically guarantee to detect?
**Model Answer:**
CRC-16-CCITT uses generator polynomial $G(x) = x^{16} + x^{12} + x^5 + 1$. Because $G(x)$ contains $(x+1)$ as a factor and does not divide $x^k + 1$ for small $k$:
1. **100% of single-bit errors.**
2. **100% of double-bit errors** for frame lengths up to 32,767 bits.
3. **100% of all odd-count bit errors** (e.g., 3, 5, 7 bit flips).
4. **100% of all burst errors of length $\le 16$ bits.**
5. **$99.9985\%$ ($1 - 2^{-16}$) of all bursts exceeding 16 bits.**

### Q49: Explain the Internet Checksum (RFC 1071) algorithm. Why is one's complement addition used instead of standard two's complement?
**Model Answer:**
The Internet Checksum divides data into 16-bit words, sums them using **one's complement addition** (where any carry bit out of the 16th bit is wrapped around and added to the least significant bit), and inverts the final sum. One's complement is chosen because it is **byte-order independent**: big-endian and little-endian architectures compute identical checksums without requiring byte-swapping, significantly accelerating router software forwarding.

---

## Topic 11: Sliding-Window Flow Control & ARQ Protocols

### Q50: What is the maximum sender window size for Go-Back-N and Selective Repeat using $k$-bit sequence numbers? Prove mathematically why SR requires $W \le 2^{k-1}$.
**Model Answer:**
- **Go-Back-N Window Limit:** $W_{\max} = 2^k - 1$.
- **Selective Repeat Window Limit:** $W_{\max} = 2^{k-1}$.
**Proof for Selective Repeat:**
Suppose $k = 2$ bits, yielding sequence numbers $\{0, 1, 2, 3\}$.
If $W > 2^{k-1}$ (say $W = 3$):
1. Sender transmits frames $0, 1, 2$. Receiver receives all three and advances its receive window to $\{3, 0, 1\}$.
2. Receiver sends ACKs $0, 1, 2$, but all three ACKs are lost in transit.
3. Sender times out on frame 0 and retransmits frame 0.
4. Receiver receives frame 0. Because 0 is inside the receiver's new window $\{3, 0, 1\}$, the receiver cannot distinguish whether this is a **retransmission of old frame 0** or a **brand new frame 0**!
To prevent overlap between the old sender window and the advanced receiver window, the sum of sender and receiver windows must satisfy $W_s + W_r \le 2^k$. In symmetric SR where $W_s = W_r = W$:
$$2W \le 2^k \implies W \le 2^{k-1}$$

### Q51: Explain the sender and receiver operations in Go-Back-N when packet $N$ is dropped in transit.
**Model Answer:**
1. **Sender:** Maintains a window of $W$ unacknowledged frames starting at base $N$. Sender has transmitted frames $N, N+1, N+2, \dots, N+W-1$.
2. **Channel:** Packet $N$ is dropped; subsequent packets $N+1, \dots$ arrive safely at the receiver.
3. **Receiver:** Enforces strict in-order arrival. When packet $N+1$ arrives, the receiver discards it because it expected $N$. The receiver repeats a duplicate ACK for the last in-order frame ($N-1$).
4. **Sender:** Retransmission timer for packet $N$ expires. The sender **goes back $W$ frames** and retransmits packet $N$ AND all subsequent unacknowledged packets ($N+1, N+2, \dots$), wasting significant transmission bandwidth.

### Q52: How does Selective Repeat eliminate the bandwidth waste of Go-Back-N under lossy conditions?
**Model Answer:**
In Selective Repeat:
1. The receiver maintains a receive window buffer of size $W$. When packet $N$ is dropped and packet $N+1$ arrives, the receiver **buffers $N+1$** in memory and transmits a selective acknowledgment for frame $N+1$.
2. The sender maintains an individual retransmission timer for every unacknowledged frame.
3. When the timer for frame $N$ expires, the sender retransmits **strictly frame $N$**. It does not retransmit $N+1, N+2$, because their selective ACKs were already received.
4. When frame $N$ arrives, the receiver delivers buffered frames $N, N+1, N+2$ in order to the application, eliminating redundant retransmissions.

### Q53: Under what channel condition does Go-Back-N perform as well as Selective Repeat?
**Model Answer:**
When the channel frame loss probability is virtually zero ($P_{\text{loss}} < 0.001$ or $0.1\%$). In a clean, error-free channel, no retransmissions occur; hence, GBN transmits at full wire speed without triggering its punitive window rewind penalty. Under clean conditions, GBN is computationally preferable because it requires zero receiver buffering and uses simple cumulative ACKs.

### Q54: What is the Bandwidth-Delay Product (BDP), and how does it dictate optimal window sizing?
**Model Answer:**
$$\text{BDP} = \text{Link Bandwidth (bps)} \times \text{Round-Trip Time (RTT in seconds)}$$
BDP represents the volume of data "in flight" required to completely fill the transmission pipeline. To achieve 100% channel utilization, the sliding window size $W$ must satisfy:
$$W \ge \frac{\text{BDP}}{\text{Frame Size in bits}} = \frac{\text{Bandwidth} \times \text{RTT}}{\text{MSS}}$$
If window size $W < \text{BDP}$, the sender drains its window and stalls waiting for ACKs, leaving the link idle and wasting capacity.

---

## Topic 12: Transport Layer: TCP Flow, Congestion & UDP Mechanics

### Q55: Diagram the TCP Three-Way Handshake and explain why Initial Sequence Numbers (ISNs) are randomized.
**Model Answer:**
```
Client                               Server
  | ----- [SYN, Seq = x] -------------> |
  | <---- [SYN-ACK, Seq = y, Ack = x+1] |
  | ----- [ACK, Seq = x+1, Ack = y+1] -> |
```
ISNs are dynamically randomized (RFC 6528) based on a cryptographic clock counter rather than starting at 0 to prevent two vulnerabilities:
1. **Stale Duplicate Segments:** Prevents delayed packets from an old closed socket session from being mistakenly accepted by a newly opened session using the same port numbers.
2. **TCP Sequence Prediction Attacks:** Prevents malicious attackers from forging TCP reset or data injection packets.

### Q56: Explain TCP Congestion Control: Slow Start, Congestion Avoidance, Fast Retransmit, and Fast Recovery.
**Model Answer:**
- **Slow Start:** Starts with $cwnd = 1 \text{ SMSS}$. For every received ACK, $cwnd$ increases by 1 SMSS (exponential growth: $1 \rightarrow 2 \rightarrow 4 \rightarrow 8$). Continues until $cwnd \ge ssthresh$.
- **Congestion Avoidance (AIMD):** Once $cwnd \ge ssthresh$, $cwnd$ increases linearly by $1 \text{ SMSS}$ per Round-Trip Time ($cwnd \leftarrow cwnd + 1/cwnd$).
- **Fast Retransmit:** When 3 duplicate ACKs are received, TCP infers a single packet drop without waiting for the slow Retransmission Timeout (RTO) timer, and immediately retransmits the missing segment.
- **Fast Recovery:** Sets $ssthresh = cwnd / 2$ and reduces $cwnd = ssthresh + 3$, resuming linear congestion avoidance rather than dropping back to $cwnd = 1$.

### Q57: What is Head-of-Line (HoL) Blocking in TCP, and why is it fatal for real-time patient vitals telemetry?
**Model Answer:**
TCP guarantees strictly in-order byte-stream delivery. If segment $k$ is dropped while segments $k+1, k+2$ arrive successfully, the operating system kernel holds segments $k+1$ and $k+2$ in socket receive buffers and refuses to release them to the application until segment $k$ is retransmitted and acknowledged. In patient telemetry, this causes sudden latency spikes of 500 ms to 2000 ms. A nurse monitoring an acute arrhythmia cannot afford to have current heartbeats blocked behind a dropped packet; delayed physiological data is clinically obsolete.

### Q58: Why does UDP have no flow control or congestion control, and how does our application compensate?
**Model Answer:**
UDP is designed as an ultra-minimalist, connectionless transport layer (RFC 768) with an 8-byte header containing only Source Port, Destination Port, Length, and Checksum. It has no windowing, acknowledgment, or rate-throttling mechanisms, transmitting packets at the exact rate generated by the application. To compensate, our Python Single-Board Computer telemetry protocol implements application-layer flow control: telemetry is emitted at fixed, rate-limited intervals (10 Hz), and packet loss is monitored via embedded monotonic sequence numbers and CRC-16 checks.

### Q59: Explain the relationship between TCP Window Size ($rwnd$), Congestion Window ($cwnd$), and the actual transmission rate.
**Model Answer:**
At any given instant, the volume of unacknowledged data a TCP sender can transmit is bounded by the minimum of flow control and congestion control:
$$W_{\text{effective}} = \min(cwnd, rwnd)$$
- **$rwnd$ (Receive Window):** Advertised by the receiver in the TCP header, reflecting available buffer memory (protects the receiver from buffer overflow).
- **$cwnd$ (Congestion Window):** Computed dynamically by the sender based on perceived network loss (protects the intermediate network from buffer bloat and collapse).

---

## Topic 13: Architectural Trade-Offs: "Why Choose X over Y?"

### Q60: Why did you choose OSPF over EIGRP or RIP?
**Model Answer:**
- **Over RIP:** RIP is a legacy distance-vector protocol limited to 15 hops with slow 30-second periodic update timers, leading to count-to-infinity loops and unacceptable convergence delays.
- **Over EIGRP:** While EIGRP converges rapidly via DUAL, it is a proprietary protocol historically tied to Cisco equipment. In a real hospital environment containing medical IoT devices from multi-vendor ecosystems (GE Healthcare, Philips, Siemens), deploying the open IETF standard **OSPFv2 (RFC 2328)** ensures vendor neutrality and seamless integration. Furthermore, OSPF's strict hierarchical area architecture prevents route flap propagation across campuses.

### Q61: Why did you choose HSRP over VRRP or GLBP?
**Model Answer:**
- **Over VRRP:** VRRP (RFC 5798) is an open standard functionally identical to HSRP, but Cisco Packet Tracer's simulation engine provides superior, bug-free MIB emulation and diagnostic show commands for Cisco HSRP.
- **Over GLBP:** Gateway Load Balancing Protocol (GLBP) dynamically balances traffic using virtual MAC rotation. However, in healthcare environments, dynamic MAC rotation complicates Layer 2 security auditing and access switch CAM table tracking. We achieved predictable active-active load sharing through split HSRP priorities across VLANs while maintaining deterministic path auditing.

### Q62: Why did you select Rapid-PVST+ over standard 802.1D STP or Multiple Spanning Tree (MSTP)?
**Model Answer:**
- **Over 802.1D:** Legacy STP requires 30 to 50 seconds to unblock alternate ports, violating our 3.0-second clinical outage SLA.
- **Over MSTP (802.1s):** While MSTP reduces BPDU CPU overhead by grouping VLANs into instances, our enterprise topology has only six clinical VLANs. Rapid-PVST+ maintains independent spanning-tree instances per VLAN, allowing us to align the root bridge of VLAN 10 directly with the HSRP active gateway on SW-D1, eliminating sub-optimal dogleg routing across inter-switch trunks.

### Q63: Why did you design a custom application framing layer for UDP instead of using raw TCP or plain UDP?
**Model Answer:**
- **Why not TCP?** TCP's congestion backoff, three-way handshake, and Head-of-Line blocking introduce unbounded latency spikes that violate clinical telemetry timeliness.
- **Why not plain UDP?** Raw UDP lacks sequence numbers and provides only a weak 16-bit one's-complement checksum that allows 1 in 65,536 corrupted packets to slip through undetected.
- **Our Hybrid Solution:** We utilize UDP for wire-speed, jitter-free transmission, but embed custom application-layer framing containing 32-bit sequence numbers, timestamps, CRC-16 error detection, and a **2D parity matrix that enables autonomous 1-bit self-healing at the bedside gateway** without demanding retransmission.

### Q64: Why did you separate clinical traffic into six VLANs instead of using a single hospital-wide VLAN?
**Model Answer:**
A single flat hospital VLAN would place thousands of devices—patient monitors, surgical consoles, visitor smartphones, and administrative billing PCs—into a single massive Layer 2 broadcast domain. Broadcast storms from infected visitor laptops or ARP scans would flood bedside monitors, consuming CPU cycles and inducing latency. Segmentation into isolated VLANs enforces zero-trust boundaries: broadcast traffic is confined to local wards, and inter-VLAN traffic must cross multilayer distribution switches where security ACLs and QoS priority queues are enforced.

### Q65: Why was Selective Repeat selected over Go-Back-N for bulk medical log transfers?
**Model Answer:**
In emergency disaster scenarios where WAN links degrade and experience packet loss rates exceeding 5%, our benchmark proved that Go-Back-N suffers catastrophic throughput collapse. Because GBN discards valid out-of-order packets and retransmits the entire sliding window, at 20% loss GBN wastes 75% of link capacity on redundant retransmissions. Selective Repeat buffers out-of-order frames and retransmits strictly the missing frame, delivering a **4.18x goodput advantage** and guaranteeing rapid transfer of patient historical diagnostic files across congested links.

---

## 5-Minute Live Demonstration Script & Emergency Fallback Runbook

### Time Budget Breakdown (Strict 5-Minute Allocation):
- **0:00 - 1:00 (60s):** Baseline Connectivity & Telemetry Verification.
- **1:00 - 2:30 (90s):** Chaos Engineering Test: Primary WAN Link Severing & OSPF Recovery.
- **2:30 - 3:30 (60s):** Multi-Layer Show Command State Inspection.
- **3:30 - 4:30 (60s):** Zero-Trust Security ACL Enforcement (Guest Drop).
- **4:30 - 5:00 (30s):** SBC Sensor 1-Bit Self-Healing Terminal Showcase & Wrap-up.

---

### Step-by-Step Demonstration Actions & Verbal Script

#### Minute 0:00 - 1:00: Baseline Topology Health
- **Physical Action:** Open Packet Tracer workspace. Open command prompt on `ICU-PC1` (`172.16.8.40`).
- **Command:** `ping 172.16.5.10`
- **Spoken Script:**
  > "Examiners, we begin by verifying baseline end-to-end connectivity. From ICU-PC1 on VLAN 10, we ping the Central EHR database at 172.16.5.10. As you observe, all four echo requests reply in 4 milliseconds across our Core distribution fabric, confirming operational OSPF routing, HSRP gateway binding, and 802.1Q trunking."

#### Minute 1:00 - 2:30: Chaos Engineering: Primary WAN Link Cut
- **Physical Action:** 
  1. Start continuous ping on Remote Clinic Workstation (`172.16.8.45`):
     ```cmd
     ping -t 172.16.5.10
     ```
  2. Switch to Packet Tracer Logical topology. Select the **Delete Tool (Red X)**.
  3. Click and **delete the red serial cable** between `R1:Serial0/0/0` and `R2:Serial0/0/0`.
  4. Return immediately to the command prompt of `172.16.8.45`.
- **Expected Visual:** Exactly 1 or 2 `Request timed out` messages appear, followed immediately by continuous successful replies.
- **Spoken Script:**
  > "Now, we demonstrate disaster survivability. We have launched a continuous ping from the Remote Clinic to the Central Hospital. Watch closely as I physically delete the primary serial WAN link between R1 and R2. Notice that the ping stream encounters only two dropped packets—representing an outage of just 1.74 seconds—before OSPF dynamic routing automatically floods a Type-1 LSA and fails over to the backup serial link Se0/0/1. This comfortably beats our 3.0-second clinical SLA."

#### Minute 2:30 - 3:30: CLI Verification of Dynamic State
- **Physical Action:** Open CLI of `R2` and `SW-D1`.
- **Commands:**
  - On `R2`: `show ip ospf neighbor`
  - On `SW-D1`: `show standby brief`
- **Spoken Script:**
  > "To verify the new state in Cisco IOS: on router R2, `show ip ospf neighbor` confirms that neighbor R1 is now in FULL adjacency exclusively across backup link Serial0/0/1. On distribution switch SW-D1, `show standby brief` confirms that SW-D1 is Active for VLANs 10, 30, and 50 with virtual IP 172.16.8.33, while standby duties are assigned to SW-D2."

#### Minute 3:30 - 4:30: Zero-Trust Security ACL Enforcement
- **Physical Action:** Open command prompt on `Guest-Laptop` (`172.16.7.15`, VLAN 60).
- **Command:** `ping 172.16.8.40` (ICU Telemetry PC).
- **Expected Visual:** Immediate `Request timed out` or `Destination host unreachable`.
- **Physical Action (Simulation Mode):** Toggle Simulation Mode (`Shift+S`), re-enter ping, advance one step: visual **Red 'X'** appears at `SW-D1`.
- **Spoken Script:**
  > "Next, we prove zero-trust perimeter security. An untrusted guest on VLAN 60 attempts to ping the ICU bedside monitor. The ping fails immediately. In Simulation Mode, double-clicking the envelope reveals a Red 'X' where our SVI access-list ACL-GUEST-ISOLATE matches the deny statement and discards the unauthorized packet at Layer 3, safeguarding patient telemetry confidentiality."

#### Minute 4:30 - 5:00: SBC Self-Healing Telemetry Showcase
- **Physical Action:** Click `SBC-ICU-101` $\rightarrow$ Programming tab $\rightarrow$ Run terminal or show output from `sbc_gateway.py`.
- **Spoken Script:**
  > "Finally, on our bedside Single-Board Computer, our Python sensor node injects a synthetic single-bit corruption into an ECG telemetry datagram. As shown in the gateway console, the 2D parity matrix detects the row and column syndrome intersection and autonomously flips the corrupted bit in memory, achieving zero-retransmission self-healing. This concludes our live demonstration."

---

### Emergency Fallback Runbook (If Packet Tracer Misbehaves)

| Failure Symptom | Immediate Root Cause | 10-Second Quick Recovery Action | Fallback Evidence Presentation |
| :--- | :--- | :--- | :--- |
| **Pings fail after link delete** | PT clock paused or ARP table cleared | Click **Fast Forward Time** button (bottom left) 3 times; re-run ping. | Open `docs/convergence_findings.md` showing verified 1.74s convergence table. |
| **Packet Tracer freezes / crashes** | OS memory leak in PT GUI | Restart Packet Tracer; load saved state `network_topology.pkt`. | Switch immediately to `results/charts/failover_theoretical_vs_observed.png` and play pre-recorded video. |
| **SBC Python script throws error** | Indentation or simulator sandbox glitch | Reset SBC container or run standalone `/sim/detection_coverage.py` in host terminal. | Show `docs/pdu_analysis_guide.md` Figure 11.6 and unit test suite passing 27/27. |
| **HSRP fails to preempt** | Timer mismatch or preemption disabled | On SW-D1: `conf t` $\rightarrow$ `int vlan 10` $\rightarrow$ `standby 10 preempt`. | Present `configs/SW-D1/SW-D1.cfg` line 45 showing preemption directive. |
