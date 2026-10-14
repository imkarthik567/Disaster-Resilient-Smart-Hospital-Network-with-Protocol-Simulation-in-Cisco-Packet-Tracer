# Disaster-Resilient Smart Hospital Network: IPv6 Dual-Stack & OSPFv3 Architecture
**Document ID:** DOC-IPV6-DESIGN-2026-v1.0  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  
**Institution:** School of Computer Science and Engineering (SCOPE), VIT Vellore  
**Course Code:** CSE2004 — Computer Networks  
**Target Environment:** Cisco Packet Tracer 8.x+ / Cisco IOS 15.x  

---

## 1. Executive Summary & Clinical Justification

As medical device manufacturers transition to next-generation healthcare IoT, bedside patient monitors, robotic surgical consoles, and smart infusion pumps are equipped with native IPv6 protocol stacks. IPv6 eliminates NAT traversal complications, provides virtually inexhaustible address space, supports cryptographically generated addresses (CGA), and natively mandates IPsec encryption.

This specification defines the **IPv6 Dual-Stack Architecture** for the Disaster-Resilient Smart Hospital Network, running IPv4 and IPv6 concurrently across the same physical hardware, with **OSPFv3 (RFC 5340)** managing dynamic routing across the enterprise core and WAN backbone.

---

## 2. IPv6 Addressing Plan (`2001:db8:acad::/48`)

The hospital network is allocated the documentation/enterprise prefix `2001:db8:acad::/48`. The 16-bit Subnet ID field is systematically partitioned:

| Subnet CIDR Prefix | Subnet Function & Campus Zone | Associated VLAN | Static Default Gateway | Assigned Devices & Nodes |
| :--- | :--- | :---: | :--- | :--- |
| **`2001:db8:acad:10::/64`** | ICU Patient Telemetry | VLAN 10 | `2001:db8:acad:10::1` | Bedside Vital Signs SBCs, Infusion Pumps |
| **`2001:db8:acad:20::/64`** | Operating Theatre Sensors | VLAN 20 | `2001:db8:acad:20::1` | Surgical Robotic Consoles, Anesthesia Mon |
| **`2001:db8:acad:30::/64`** | General Ward & Admin | VLAN 30 | `2001:db8:acad:30::1` | Nursing Workstations, Billing Terminals |
| **`2001:db8:acad:40::/64`** | Diagnostic Imaging (PACS)| VLAN 40 | `2001:db8:acad:40::1` | MRI/CT Scanners, DICOM Image Archives |
| **`2001:db8:acad:50::/64`** | Central Server Farm | VLAN 50 | `2001:db8:acad:50::1` | Central EHR Database, DNSv6, DHCPv6 Server |
| **`2001:db8:acad:60::/64`** | Guest & Visitor Wi-Fi | VLAN 60 | `2001:db8:acad:60::1` | Public Mobile Devices (SLAAC) |
| **`2001:db8:acad:80::/64`** | Primary Serial WAN (R1-R2)| P2P (Area 0) | `2001:db8:acad:80::1` | Primary Inter-Campus Serial Link |
| **`2001:db8:acad:84::/64`** | Backup Serial WAN (R1-R2) | P2P (Area 0) | `2001:db8:acad:84::1` | Secondary Standby Serial WAN Link |
| **`2001:db8:acad:88::/64`** | R1 to SW-D1 Core Uplink | Routed (Area 0) | `2001:db8:acad:88::1` | Core Router R1 to Dist SW-D1 Link |
| **`2001:db8:acad:92::/64`** | R1 to SW-D2 Core Uplink | Routed (Area 0) | `2001:db8:acad:92::1` | Core Router R1 to Dist SW-D2 Link |
| **`2001:db8:acad:96::/64`** | R2 to SW-D3 Clinic Uplink| Routed (Area 0) | `2001:db8:acad:96::1` | Clinic Router R2 to Clinic Gateway |

---

## 3. Link-Local Addressing Architecture (`fe80::`)

To eliminate routing protocol dependency on global unicast address renumbering and facilitate human-readable network troubleshooting, all router and switch interfaces are explicitly assigned standard link-local addresses:

| Device Name | Assigned Link-Local Address | Interfaces Configured | Clinical Purpose |
| :--- | :--- | :--- | :--- |
| **R1 (Core Router)** | `fe80::1` | Gi0/0, Gi0/1, Se0/0/0, Se0/0/1 | Core OSPFv3 Next-Hop Identity |
| **R2 (Clinic Router)**| `fe80::2` | Gi0/0, Se0/0/0, Se0/0/1 | Remote Clinic Next-Hop Identity |
| **SW-D1 (Dist 1)** | `fe80::d1` | Gi0/2, Vlan10, Vlan20, Vlan30, Vlan50 | Primary Default Gateway Next-Hop |
| **SW-D2 (Dist 2)** | `fe80::d2` | Gi0/2, Vlan10, Vlan20, Vlan40, Vlan60 | Secondary Default Gateway Next-Hop |
| **SW-D3 (Clinic Dist)**| `fe80::d3`| Gi0/1, Vlan10, Vlan30, Vlan40, Vlan60 | Clinic Gateway Next-Hop |

---

## 4. OSPFv3 Protocol Architecture (RFC 5340)

OSPFv3 is specifically engineered to route IPv6:
1. **Network-LSA Separation:** In OSPFv2, IPv4 addresses are carried directly inside Type-1 and Type-2 LSAs. In OSPFv3, Type-1 and Type-2 LSAs carry only topological graph linkages; IPv6 prefixes are advertised separately via **Type-8 (Link LSA)** and **Type-9 (Intra-Area-Prefix LSA)**. This allows the topology tree to remain stable even when IP prefixes flap.
2. **Link-Local Peering:** OSPFv3 runs per-link rather than per-subnet. Neighbors peer strictly over IPv6 link-local addresses (`fe80::`), and link-local addresses are installed as next-hops in the IPv6 routing table.
3. **Interface Configuration:** OSPFv3 completely abandons the legacy `network <ip> <wildcard> area <id>` command. Instead, routing is enabled directly on each interface via `ipv6 ospf 1 area <id>`.

---

## 5. Dual-Stack Configuration Snippets

### 5.1 Core Router R1 (`configs/ipv6_dual_stack/R1_ipv6.cfg`)
```ios
ipv6 unicast-routing
!
interface Loopback0
 ipv6 address 2001:db8:acad:106::1/128
 ipv6 ospf 1 area 0
!
interface GigabitEthernet0/0
 description Routed Uplink to SW-D1
 ipv6 address fe80::1 link-local
 ipv6 address 2001:db8:acad:88::2/64
 ipv6 ospf 1 area 0
 ipv6 ospf cost 1
!
interface GigabitEthernet0/1
 description Routed Uplink to SW-D2
 ipv6 address fe80::1 link-local
 ipv6 address 2001:db8:acad:92::2/64
 ipv6 ospf 1 area 0
 ipv6 ospf cost 1
!
interface Serial0/0/0
 description Primary Serial WAN to R2
 ipv6 address fe80::1 link-local
 ipv6 address 2001:db8:acad:80::1/64
 ipv6 ospf 1 area 0
 ipv6 ospf cost 64
!
interface Serial0/0/1
 description Secondary Backup Serial WAN to R2
 ipv6 address fe80::1 link-local
 ipv6 address 2001:db8:acad:84::1/64
 ipv6 ospf 1 area 0
 ipv6 ospf cost 500
!
ipv6 router ospf 1
 router-id 172.16.8.106
 log-adjacency-changes
```

### 5.2 Primary Distribution Switch SW-D1 (`configs/ipv6_dual_stack/SW-D1_ipv6.cfg`)
```ios
sdm prefer dual-ipv4-and-ipv6 default
ipv6 unicast-routing
!
interface GigabitEthernet0/2
 description Routed Uplink to R1 Gi0/0
 no switchport
 ipv6 address fe80::d1 link-local
 ipv6 address 2001:db8:acad:88::1/64
 ipv6 ospf 1 area 0
!
interface Vlan10
 description ICU Telemetry IPv6 Gateway
 ipv6 address fe80::d1 link-local
 ipv6 address 2001:db8:acad:10::2/64
 ipv6 ospf 1 area 1
!
interface Vlan50
 description Server Farm IPv6 Gateway
 ipv6 address fe80::d1 link-local
 ipv6 address 2001:db8:acad:50::2/64
 ipv6 ospf 1 area 1
!
ipv6 router ospf 1
 router-id 172.16.8.104
 log-adjacency-changes
 passive-interface Vlan10
 passive-interface Vlan50
```

---

## 6. Verification Commands & Diagnostics

To verify IPv6 operational state in Cisco Packet Tracer:
- `show ipv6 interface brief`: Displays all assigned link-local and global unicast addresses.
- `show ipv6 route ospf`: Displays routes learned via OSPFv3 with next-hops resolving to `fe80::` link-local addresses.
- `show ipv6 ospf neighbor`: Displays OSPFv3 neighbor adjacencies across physical links.
- `ping 2001:db8:acad:50::10`: Tests end-to-end IPv6 connectivity between clinical hosts and the central server.
