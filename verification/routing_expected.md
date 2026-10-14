# Golden Expected Routing Tables & Verification Baseline
**Project:** Disaster-Resilient Smart Hospital Network (VIT SCOPE — Computer Networks)  
**Standard Compliance:** Cisco Packet Tracer 8.x | RFC 2328 (OSPFv2) | RFC 7868 (EIGRP)  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  

---

## 1. Overview & Verification Methodology

This document establishes the **golden routing state baseline** for all Layer 3 devices in the hospital network:
- **Core Routers:** `R1` (Main Hospital Core) and `R2` (Remote Spoke Clinic ABR)
- **Multilayer Distribution Switches:** `SW-D1`, `SW-D2` (Main Hospital Campus) and `SW-D3` (Remote Clinic)

Network administrators and evaluators can directly compare real outputs from Cisco Packet Tracer (`show ip route`, `show ip ospf neighbor`, `show ip eigrp neighbors`, `traceroute`) against the golden blocks in this document using standard text diff tools (`diff`, `fc`, or VS Code Diff).

```
================================================================================
                           TOPOLOGY ROUTING ARCHITECTURE
================================================================================
  [EDGE-ISP] 172.16.8.101/30
      ^
      | Gi0/2 (172.16.8.102/30) - Default Route via Static S*
  +---+-----------------------------------------------------------------------+
  | R1 Core (OSPF Area 0, Router-ID 172.16.8.104)                            |
  | Originate Default: Type-5 LSA (O*E2 0.0.0.0/0)                            |
  +---+--------------------+--------------------------------+-----------------+
      | Gi0/0 (.8.90)      | Gi0/1 (.8.94)                  | Se0/0/0 (.8.81) | Se0/0/1 (.8.85)
      v                    v                                v (OSPF Area 0)   v (EIGRP AS 100)
   [SW-D1]              [SW-D2]                             | AD 110, BW 2048 | AD 120, BW 1544
 (OSPF .8.106)        (OSPF .8.107)                         | Primary WAN     | Standby WAN
      \                    /                                v                 v
    VLANs 10,20,30,40,50,60,99                              +-----------------+
                                                            | R2 Core / ABR   |
                                                            | (Area 0 <-> 1)  |
                                                            | (OSPF .8.105)   |
                                                            +--------+--------+
                                                                     | Gi0/0 (172.16.8.98/30 - Area 1)
                                                                     v
                                                            +-----------------+
                                                            | SW-D3 (Dist)    |
                                                            | (OSPF .8.108)   |
                                                            +-----------------+
                                                                     |
                                                            Clinic VLANs 10,30,40,60,99
================================================================================
```

---

## 2. Cisco IOS Route Code Reference

Every route installed in the Routing Information Base (RIB) carries a specific routing code:

| Code | Protocol / Source | Administrative Distance (AD) | Role in Hospital Topology |
| :---: | :--- | :---: | :--- |
| **`C`** | Directly Connected Subnet | 0 | Physical link and active SVI subnets |
| **`L`** | Local Interface Host Route | 0 | Individual `/32` IP assigned to the local interface |
| **`S*`** | Static Default Route | 1 | Default route to ISP on R1; floating backup on switches (AD 200) |
| **`O`** | OSPF Intra-Area | 110 | Subnets belonging to the local OSPF area (Area 0 or Area 1) |
| **`O IA`** | OSPF Inter-Area | 110 | Subnets summarized across ABR R2 boundary |
| **`O*E2`** | OSPF External Type-2 | 110 (Metric 20) | Default route injected dynamically by Core Router R1 |
| **`D`** | EIGRP Internal (Tuned) | 120 | Standby routes learned via Serial0/0/1 (active only on primary failure) |
| **`D EX`**| EIGRP External | 170 | Redistributed external routes |

---

## 3. Golden Route Tables — Normal Operational State (Primary WAN UP)

### 3.1 Core Router R1 (Main Hospital Core)
- **Role:** Area 0 Core Router, Internet Edge Gateway (NAT PAT), OSPF Default Route Injector
- **Router ID:** `172.16.8.104` (Loopback0)
- **Primary WAN:** `Serial0/0/0` (UP, OSPF Area 0, Cost 48, AD 110)
- **Standby WAN:** `Serial0/0/1` (UP, EIGRP AS 100, AD 120 — dormant in topology table)

#### Route Code Breakdown:
- **`S*` (1 route):** Static default route `0.0.0.0/0` via `172.16.8.101` (EDGE-ISP).
- **`O` (7 routes):** Main Hospital internal subnets (VLANs 10, 20, 30, 40, 50, 60, 99) ECMP load-balanced across SW-D1 (`172.16.8.89`) and SW-D2 (`172.16.8.93`).
- **`O IA` (3 routes):** Summarized Remote Clinic subnets via ABR R2 over `Serial0/0/0`:
  - `172.16.8.0/24` (Clinic Campus: Admin, Clinical, Mgmt, Transit)
  - `172.16.6.128/25` (Clinic Guest Wi-Fi)
  - `172.16.7.224/27` (Clinic VoIP Voice)
- **`C` / `L` (6 subnets):** Directly connected `/30` point-to-point links and Loopback0.

#### Exact Expected Output (`R1# show ip route`):
```text
Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area
       N1 - OSPF NSSA external type 1, N2 - OSPF NSSA external type 2
       E1 - OSPF external type 1, E2 - OSPF external type 2, E - EGP
       i - IS-IS, L1 - IS-IS level-1, L2 - IS-IS level-2, ia - IS-IS inter area
       * - candidate default, U - per-user static route, o - ODR
       P - periodic downloaded static route

Gateway of last resort is 172.16.8.101 to network 0.0.0.0

S*   0.0.0.0/0 [1/0] via 172.16.8.101
     172.16.0.0/16 is variably subnetted, 18 subnets, 6 masks
O       172.16.0.0/22 [110/2] via 172.16.8.93, 00:15:21, GigabitEthernet0/1
                      [110/2] via 172.16.8.89, 00:15:21, GigabitEthernet0/0
O       172.16.4.0/23 [110/2] via 172.16.8.93, 00:15:21, GigabitEthernet0/1
                      [110/2] via 172.16.8.89, 00:15:21, GigabitEthernet0/0
O       172.16.6.0/25 [110/2] via 172.16.8.93, 00:15:21, GigabitEthernet0/1
                      [110/2] via 172.16.8.89, 00:15:21, GigabitEthernet0/0
O IA    172.16.6.128/25 [110/49] via 172.16.8.82, 00:14:10, Serial0/0/0
O       172.16.7.0/26 [110/2] via 172.16.8.93, 00:15:21, GigabitEthernet0/1
                      [110/2] via 172.16.8.89, 00:15:21, GigabitEthernet0/0
O       172.16.7.64/26 [110/2] via 172.16.8.93, 00:15:21, GigabitEthernet0/1
                       [110/2] via 172.16.8.89, 00:15:21, GigabitEthernet0/0
O       172.16.7.128/26 [110/2] via 172.16.8.93, 00:15:21, GigabitEthernet0/1
                        [110/2] via 172.16.8.89, 00:15:21, GigabitEthernet0/0
O       172.16.7.192/27 [110/2] via 172.16.8.93, 00:15:21, GigabitEthernet0/1
                        [110/2] via 172.16.8.89, 00:15:21, GigabitEthernet0/0
O IA    172.16.7.224/27 [110/49] via 172.16.8.82, 00:14:10, Serial0/0/0
O IA    172.16.8.0/24 [110/49] via 172.16.8.82, 00:14:10, Serial0/0/0
C       172.16.8.80/30 is directly connected, Serial0/0/0
L       172.16.8.81/32 is directly connected, Serial0/0/0
C       172.16.8.84/30 is directly connected, Serial0/0/1
L       172.16.8.85/32 is directly connected, Serial0/0/1
C       172.16.8.88/30 is directly connected, GigabitEthernet0/0
L       172.16.8.90/32 is directly connected, GigabitEthernet0/0
C       172.16.8.92/30 is directly connected, GigabitEthernet0/1
L       172.16.8.94/32 is directly connected, GigabitEthernet0/1
C       172.16.8.100/30 is directly connected, GigabitEthernet0/2
L       172.16.8.102/32 is directly connected, GigabitEthernet0/2
C       172.16.8.104/32 is directly connected, Loopback0
```

---

### 3.2 Core Router R2 (Remote Clinic Core / ABR)
- **Role:** OSPF Area Border Router (ABR) connecting Area 0 (Backbone WAN) and Area 1 (Clinic)
- **Router ID:** `172.16.8.105` (Loopback0)
- **Primary WAN:** `Serial0/0/0` (Area 0, Cost 48, AD 110)
- **ABR Summarization:** `area 1 range` condenses 6 subnets into 3 advertised into Area 0

#### Route Code Breakdown:
- **`O*E2` (1 route):** Default route `0.0.0.0/0` via `172.16.8.81` (R1).
- **`O` (7 routes):** Main Hospital campus subnets learned via Area 0 over `Serial0/0/0`.
- **`O` (5 routes):** Local Remote Clinic subnets learned via Area 1 over `GigabitEthernet0/0` (`SW-D3`).
- **`C` / `L` (4 subnets):** Directly connected `/30` WAN circuits, LAN link, and Loopback0.

#### Exact Expected Output (`R2# show ip route`):
```text
Gateway of last resort is 172.16.8.81 to network 0.0.0.0

O*E2 0.0.0.0/0 [110/20] via 172.16.8.81, 00:15:30, Serial0/0/0
     172.16.0.0/16 is variably subnetted, 17 subnets, 6 masks
O       172.16.0.0/22 [110/50] via 172.16.8.81, 00:15:30, Serial0/0/0
O       172.16.4.0/23 [110/50] via 172.16.8.81, 00:15:30, Serial0/0/0
O       172.16.6.0/25 [110/50] via 172.16.8.81, 00:15:30, Serial0/0/0
O       172.16.6.128/25 [110/2] via 172.16.8.97, 00:16:02, GigabitEthernet0/0
O       172.16.7.0/26 [110/50] via 172.16.8.81, 00:15:30, Serial0/0/0
O       172.16.7.64/26 [110/50] via 172.16.8.81, 00:15:30, Serial0/0/0
O       172.16.7.128/26 [110/50] via 172.16.8.81, 00:15:30, Serial0/0/0
O       172.16.7.192/27 [110/50] via 172.16.8.81, 00:15:30, Serial0/0/0
O       172.16.7.224/27 [110/2] via 172.16.8.97, 00:16:02, GigabitEthernet0/0
O       172.16.8.0/27 [110/2] via 172.16.8.97, 00:16:02, GigabitEthernet0/0
O       172.16.8.32/27 [110/2] via 172.16.8.97, 00:16:02, GigabitEthernet0/0
O       172.16.8.64/28 [110/2] via 172.16.8.97, 00:16:02, GigabitEthernet0/0
C       172.16.8.80/30 is directly connected, Serial0/0/0
L       172.16.8.82/32 is directly connected, Serial0/0/0
C       172.16.8.84/30 is directly connected, Serial0/0/1
L       172.16.8.86/32 is directly connected, Serial0/0/1
C       172.16.8.96/30 is directly connected, GigabitEthernet0/0
L       172.16.8.98/32 is directly connected, GigabitEthernet0/0
C       172.16.8.105/32 is directly connected, Loopback0
```

---

### 3.3 Multilayer Distribution Switch SW-D1 (Main Hospital)
- **Role:** Campus Distribution Gateway (HSRP Active for Odd VLANs 10, 30, 50, 99)
- **Router ID:** `172.16.8.106` (Loopback0)
- **Routed Uplink:** `GigabitEthernet0/2` -> `R1 Gi0/0` (`172.16.8.90`)

#### Route Code Breakdown:
- **`O*E2` (1 route):** Default route `0.0.0.0/0` via `172.16.8.90` (R1).
- **`O IA` (3 routes):** Summarized Remote Clinic subnets via R1.
- **`O` (1 route):** SW-D2 transit link `172.16.8.92/30` via `172.16.8.90`.
- **`C` / `L` (8 subnets):** 7 local campus SVIs, GigabitEthernet0/2, and Loopback0.

#### Exact Expected Output (`SW-D1# show ip route`):
```text
Gateway of last resort is 172.16.8.90 to network 0.0.0.0

O*E2 0.0.0.0/0 [110/20] via 172.16.8.90, 00:15:45, GigabitEthernet0/2
     172.16.0.0/16 is variably subnetted, 18 subnets, 6 masks
C       172.16.0.0/22 is directly connected, Vlan40
L       172.16.0.2/32 is directly connected, Vlan40
C       172.16.4.0/23 is directly connected, Vlan30
L       172.16.4.2/32 is directly connected, Vlan30
C       172.16.6.0/25 is directly connected, Vlan60
L       172.16.6.2/32 is directly connected, Vlan60
O IA    172.16.6.128/25 [110/50] via 172.16.8.90, 00:14:22, GigabitEthernet0/2
C       172.16.7.0/26 is directly connected, Vlan50
L       172.16.7.2/32 is directly connected, Vlan50
C       172.16.7.64/26 is directly connected, Vlan20
L       172.16.7.66/32 is directly connected, Vlan20
C       172.16.7.128/26 is directly connected, Vlan10
L       172.16.7.130/32 is directly connected, Vlan10
C       172.16.7.192/27 is directly connected, Vlan99
L       172.16.7.194/32 is directly connected, Vlan99
O IA    172.16.7.224/27 [110/50] via 172.16.8.90, 00:14:22, GigabitEthernet0/2
O IA    172.16.8.0/24 [110/50] via 172.16.8.90, 00:14:22, GigabitEthernet0/2
C       172.16.8.88/30 is directly connected, GigabitEthernet0/2
L       172.16.8.89/32 is directly connected, GigabitEthernet0/2
O       172.16.8.92/30 [110/2] via 172.16.8.90, 00:15:45, GigabitEthernet0/2
C       172.16.8.106/32 is directly connected, Loopback0
```

---

### 3.4 Multilayer Distribution Switch SW-D2 (Main Hospital)
- **Role:** Campus Distribution Gateway (HSRP Active for Even VLANs 20, 40, 60)
- **Router ID:** `172.16.8.107` (Loopback0)
- **Routed Uplink:** `GigabitEthernet0/2` -> `R1 Gi0/1` (`172.16.8.94`)

#### Exact Expected Output (`SW-D2# show ip route`):
```text
Gateway of last resort is 172.16.8.94 to network 0.0.0.0

O*E2 0.0.0.0/0 [110/20] via 172.16.8.94, 00:15:40, GigabitEthernet0/2
     172.16.0.0/16 is variably subnetted, 18 subnets, 6 masks
C       172.16.0.0/22 is directly connected, Vlan40
L       172.16.0.3/32 is directly connected, Vlan40
C       172.16.4.0/23 is directly connected, Vlan30
L       172.16.4.3/32 is directly connected, Vlan30
C       172.16.6.0/25 is directly connected, Vlan60
L       172.16.6.3/32 is directly connected, Vlan60
O IA    172.16.6.128/25 [110/50] via 172.16.8.94, 00:14:20, GigabitEthernet0/2
C       172.16.7.0/26 is directly connected, Vlan50
L       172.16.7.3/32 is directly connected, Vlan50
C       172.16.7.64/26 is directly connected, Vlan20
L       172.16.7.67/32 is directly connected, Vlan20
C       172.16.7.128/26 is directly connected, Vlan10
L       172.16.7.131/32 is directly connected, Vlan10
C       172.16.7.192/27 is directly connected, Vlan99
L       172.16.7.195/32 is directly connected, Vlan99
O IA    172.16.7.224/27 [110/50] via 172.16.8.94, 00:14:20, GigabitEthernet0/2
O IA    172.16.8.0/24 [110/50] via 172.16.8.94, 00:14:20, GigabitEthernet0/2
O       172.16.8.88/30 [110/2] via 172.16.8.94, 00:15:40, GigabitEthernet0/2
C       172.16.8.92/30 is directly connected, GigabitEthernet0/2
L       172.16.8.93/32 is directly connected, GigabitEthernet0/2
C       172.16.8.107/32 is directly connected, Loopback0
```

---

### 3.5 Multilayer Distribution Switch SW-D3 (Remote Clinic)
- **Role:** Remote Clinic Core Distribution Switch (OSPF Area 1 Spoke)
- **Router ID:** `172.16.8.108` (Loopback0)
- **Routed Uplink:** `GigabitEthernet0/1` -> `R2 Gi0/0` (`172.16.8.98`)

#### Route Code Breakdown:
- **`O*E2` (1 route):** Default route `0.0.0.0/0` via `172.16.8.98` (R2).
- **`O IA` (7 routes):** Main Hospital internal subnets (VLANs 10, 20, 30, 40, 50, 60, 99) learned across ABR R2.
- **`C` / `L` (6 subnets):** 5 local clinic SVIs, GigabitEthernet0/1, and Loopback0.

#### Exact Expected Output (`SW-D3# show ip route`):
```text
Gateway of last resort is 172.16.8.98 to network 0.0.0.0

O*E2 0.0.0.0/0 [110/20] via 172.16.8.98, 00:15:15, GigabitEthernet0/1
     172.16.0.0/16 is variably subnetted, 19 subnets, 6 masks
O IA    172.16.0.0/22 [110/51] via 172.16.8.98, 00:15:15, GigabitEthernet0/1
O IA    172.16.4.0/23 [110/51] via 172.16.8.98, 00:15:15, GigabitEthernet0/1
O IA    172.16.6.0/25 [110/51] via 172.16.8.98, 00:15:15, GigabitEthernet0/1
C       172.16.6.128/25 is directly connected, Vlan40
L       172.16.6.129/32 is directly connected, Vlan40
O IA    172.16.7.0/26 [110/51] via 172.16.8.98, 00:15:15, GigabitEthernet0/1
O IA    172.16.7.64/26 [110/51] via 172.16.8.98, 00:15:15, GigabitEthernet0/1
O IA    172.16.7.128/26 [110/51] via 172.16.8.98, 00:15:15, GigabitEthernet0/1
O IA    172.16.7.192/27 [110/51] via 172.16.8.98, 00:15:15, GigabitEthernet0/1
C       172.16.7.224/27 is directly connected, Vlan60
L       172.16.7.225/32 is directly connected, Vlan60
C       172.16.8.0/27 is directly connected, Vlan30
L       172.16.8.1/32 is directly connected, Vlan30
C       172.16.8.32/27 is directly connected, Vlan10
L       172.16.8.33/32 is directly connected, Vlan10
C       172.16.8.64/28 is directly connected, Vlan99
L       172.16.8.65/32 is directly connected, Vlan99
C       172.16.8.96/30 is directly connected, GigabitEthernet0/1
L       172.16.8.97/32 is directly connected, GigabitEthernet0/1
C       172.16.8.108/32 is directly connected, Loopback0
```

---

## 4. Dynamic Neighbor Adjacency Verifications

### 4.1 OSPF Adjacency Matrix (`show ip ospf neighbor`)

```text
! --- Core Router R1 ---
R1# show ip ospf neighbor
Neighbor ID     Pri   State           Dead Time   Address         Interface
172.16.8.105      0   FULL/  -        00:00:03    172.16.8.82     Serial0/0/0
172.16.8.106      0   FULL/  -        00:00:35    172.16.8.89     GigabitEthernet0/0
172.16.8.107      0   FULL/  -        00:00:37    172.16.8.93     GigabitEthernet0/1

! --- Core Router R2 (ABR) ---
R2# show ip ospf neighbor
Neighbor ID     Pri   State           Dead Time   Address         Interface
172.16.8.104      0   FULL/  -        00:00:03    172.16.8.81     Serial0/0/0
172.16.8.108      0   FULL/  -        00:00:36    172.16.8.97     GigabitEthernet0/0

! --- Multilayer Distribution Switch SW-D1 ---
SW-D1# show ip ospf neighbor
Neighbor ID     Pri   State           Dead Time   Address         Interface
172.16.8.104      0   FULL/  -        00:00:36    172.16.8.90     GigabitEthernet0/2

! --- Multilayer Distribution Switch SW-D2 ---
SW-D2# show ip ospf neighbor
Neighbor ID     Pri   State           Dead Time   Address         Interface
172.16.8.104      0   FULL/  -        00:00:38    172.16.8.94     GigabitEthernet0/2

! --- Multilayer Distribution Switch SW-D3 ---
SW-D3# show ip ospf neighbor
Neighbor ID     Pri   State           Dead Time   Address         Interface
172.16.8.105      0   FULL/  -        00:00:35    172.16.8.98     GigabitEthernet0/1
```

> [!NOTE]
> Point-to-point network type (`ip ospf network point-to-point`) on all routed transit links bypasses DR/BDR election completely, yielding `FULL/ -` states instantly upon Hello exchange.

### 4.2 EIGRP Standby Adjacency Matrix (`show ip eigrp neighbors`)

```text
! --- Core Router R1 ---
R1# show ip eigrp neighbors
IP-EIGRP neighbors for process 100
H   Address          Interface       Hold  Uptime    SRTT   RTO   Q   Seq
                                     (sec)           (ms)        Cnt  Num
0   172.16.8.86      Se0/0/1           12  00:18:22   24    200   0   14

! --- Core Router R2 ---
R2# show ip eigrp neighbors
IP-EIGRP neighbors for process 100
H   Address          Interface       Hold  Uptime    SRTT   RTO   Q   Seq
                                     (sec)           (ms)        Cnt  Num
0   172.16.8.85      Se0/0/1           13  00:18:24   25    200   0   15
```

---

## 5. End-to-End Path Verification (Traceroute)

### 5.1 Primary Path: ICU Nurse PC to Clinic Cache Server
- **Source:** `PC-ICU-NURSE` (`172.16.7.141` in VLAN 10, Main Hospital)
- **Target:** `SRV-CACHE` (`172.16.8.36` in VLAN 10, Remote Clinic)
- **Command:** `PC-ICU-NURSE> tracert 172.16.8.36`

```text
Tracing route to 172.16.8.36 over a maximum of 30 hops:

  1   <1 ms    <1 ms    <1 ms   172.16.7.129   [SW-D1 HSRP VIP - Vlan10 Active Gateway]
  2   <1 ms    <1 ms    <1 ms   172.16.8.90    [R1 Gig0/0 - Campus Core Ingress]
  3    3 ms     3 ms     3 ms   172.16.8.82    [R2 Serial0/0/0 - Primary WAN Circuit via OSPF]
  4   <1 ms    <1 ms    <1 ms   172.16.8.97    [SW-D3 Gig0/1 - Clinic Core Ingress]
  5   <1 ms    <1 ms    <1 ms   172.16.8.36    [SRV-CACHE - Remote Clinic EHR Server]

Trace complete.
```

#### Hop Analysis & Proof of Determinism:
1. **Hop 1 (`172.16.7.129`):** The ICU host sends frames to its default gateway, the HSRP v2 Virtual IP. Because VLAN 10 is an odd VLAN, SW-D1 (Priority 110) answers the ARP request and performs hardware Layer 3 routing.
2. **Hop 2 (`172.16.8.90`):** SW-D1 forwards the packet across point-to-point transit link `GigabitEthernet0/2` to Core Router R1's `GigabitEthernet0/0`.
3. **Hop 3 (`172.16.8.82`):** R1 consults its RIB for destination `172.16.8.36`. It matches OSPF inter-area summary route `172.16.8.0/24 [110/49]` out `Serial0/0/0`. EIGRP route via `Serial0/0/1` is suppressed because $AD_{\text{OSPF}} = 110 < AD_{\text{EIGRP}} = 120$.
4. **Hop 4 (`172.16.8.97`):** R2 receives the packet, routes it via OSPF Area 1 to SW-D3's transit interface `GigabitEthernet0/1`.
5. **Hop 5 (`172.16.8.36`):** SW-D3 routes the packet into VLAN 10 and delivers it directly to the local cache server.

---

## 6. Primary Link Failure & Reconvergence Drill

### 6.1 Failure Simulation Protocol
To simulate an inter-site fiber severance or primary carrier circuit failure:
```cisco
R1# configure terminal
R1(config)# interface Serial0/0/0
R1(config-if)# shutdown
```

### 6.2 Convergence Sequence & Timeline
1. **$t = 0.00\text{s}$:** Carrier loss detected on `Serial0/0/0`.
2. **$t = 4.00\text{s}$:** OSPF dead-timer expires ($4 \times \text{hello-interval} = 4\text{s}$). The OSPF adjacency with `172.16.8.105` transitions to `DOWN`.
3. **$t = 4.05\text{s}$:** R1 removes all `O IA` routes associated with `Serial0/0/0` from its RIB.
4. **$t = 4.10\text{s}$:** The Cisco RIB queries EIGRP AS 100 for alternate paths. EIGRP already has pre-computed Feasible Successor routes over `Serial0/0/1` in its topology table.
5. **$t = 4.15\text{s}$:** EIGRP routes ($AD = 120$) are promoted and installed in R1 and R2's routing tables.
6. **Total Outage Duration:** **$\approx 4$ seconds** (compared to default 40s without timer tuning).

---

## 7. Before vs. After Failure Routing State Matrix

| Device | Destination Network | Normal State (Primary Link UP) | Failed State (Primary Se0/0/0 DOWN) | Protocol Shift & Next-Hop |
| :--- | :--- | :--- | :--- | :--- |
| **R1** | Clinic Campus (`172.16.8.0/24`) | `O IA [110/49] via 172.16.8.82, Se0/0/0` | `D [120/2172416] via 172.16.8.86, Se0/0/1` | OSPF -> EIGRP Failover |
| **R1** | Clinic Guest (`172.16.6.128/25`)| `O IA [110/49] via 172.16.8.82, Se0/0/0` | `D [120/2172416] via 172.16.8.86, Se0/0/1` | OSPF -> EIGRP Failover |
| **R1** | Clinic Voice (`172.16.7.224/27`)| `O IA [110/49] via 172.16.8.82, Se0/0/0` | `D [120/2172416] via 172.16.8.86, Se0/0/1` | OSPF -> EIGRP Failover |
| **R2** | Campus Core (`172.16.0.0/16`)   | `O [110/50] via 172.16.8.81, Se0/0/0`    | `D [120/2172416] via 172.16.8.85, Se0/0/1` | OSPF -> EIGRP Failover |
| **R2** | Default Route (`0.0.0.0/0`)     | `O*E2 [110/20] via 172.16.8.81, Se0/0/0` | `D*EX [170/...] via 172.16.8.85, Se0/0/1`   | EIGRP Floating Backup Default |
| **SW-D1**| Clinic Campus (`172.16.8.0/24`)| `O IA [110/50] via 172.16.8.90, Gi0/2`   | `O IA [110/50] via 172.16.8.90, Gi0/2`    | Unchanged (R1 hides WAN shift) |
| **SW-D3**| Campus Core (`172.16.7.0/26`)  | `O IA [110/51] via 172.16.8.98, Gi0/1`   | `O IA [110/51] via 172.16.8.98, Gi0/1`    | Unchanged (R2 hides WAN shift) |

### 7.1 Failed State Routing Table on R1 (`R1# show ip route`)
```text
Gateway of last resort is 172.16.8.101 to network 0.0.0.0

S*   0.0.0.0/0 [1/0] via 172.16.8.101
     172.16.0.0/16 is variably subnetted, 16 subnets, 5 masks
O       172.16.0.0/22 [110/2] via 172.16.8.93, 00:20:11, GigabitEthernet0/1
                      [110/2] via 172.16.8.89, 00:20:11, GigabitEthernet0/0
O       172.16.4.0/23 [110/2] via 172.16.8.93, 00:20:11, GigabitEthernet0/1
                      [110/2] via 172.16.8.89, 00:20:11, GigabitEthernet0/0
O       172.16.6.0/25 [110/2] via 172.16.8.93, 00:20:11, GigabitEthernet0/1
                      [110/2] via 172.16.8.89, 00:20:11, GigabitEthernet0/0
D       172.16.6.128/25 [120/2172416] via 172.16.8.86, 00:00:15, Serial0/0/1  <-- EIGRP TAKES OVER!
O       172.16.7.0/26 [110/2] via 172.16.8.93, 00:20:11, GigabitEthernet0/1
                      [110/2] via 172.16.8.89, 00:20:11, GigabitEthernet0/0
O       172.16.7.64/26 [110/2] via 172.16.8.93, 00:20:11, GigabitEthernet0/1
                       [110/2] via 172.16.8.89, 00:20:11, GigabitEthernet0/0
O       172.16.7.128/26 [110/2] via 172.16.8.93, 00:20:11, GigabitEthernet0/1
                        [110/2] via 172.16.8.89, 00:20:11, GigabitEthernet0/0
O       172.16.7.192/27 [110/2] via 172.16.8.93, 00:20:11, GigabitEthernet0/1
                        [110/2] via 172.16.8.89, 00:20:11, GigabitEthernet0/0
D       172.16.7.224/27 [120/2172416] via 172.16.8.86, 00:00:15, Serial0/0/1  <-- EIGRP TAKES OVER!
D       172.16.8.0/24 [120/2172416] via 172.16.8.86, 00:00:15, Serial0/0/1    <-- EIGRP TAKES OVER!
C       172.16.8.84/30 is directly connected, Serial0/0/1
L       172.16.8.85/32 is directly connected, Serial0/0/1
C       172.16.8.88/30 is directly connected, GigabitEthernet0/0
L       172.16.8.90/32 is directly connected, GigabitEthernet0/0
C       172.16.8.92/30 is directly connected, GigabitEthernet0/1
L       172.16.8.94/32 is directly connected, GigabitEthernet0/1
C       172.16.8.100/30 is directly connected, GigabitEthernet0/2
L       172.16.8.102/32 is directly connected, GigabitEthernet0/2
C       172.16.8.104/32 is directly connected, Loopback0
```

### 7.2 Failover Traceroute: ICU Nurse PC to Clinic Cache Server
```text
Tracing route to 172.16.8.36 over a maximum of 30 hops:

  1   <1 ms    <1 ms    <1 ms   172.16.7.129   [SW-D1 HSRP VIP - Vlan10 Active Gateway]
  2   <1 ms    <1 ms    <1 ms   172.16.8.90    [R1 Gig0/0 - Campus Core Ingress]
  3    4 ms     4 ms     4 ms   172.16.8.86    [R2 Serial0/0/1 - Standby WAN Circuit via EIGRP AS 100]
  4   <1 ms    <1 ms    <1 ms   172.16.8.97    [SW-D3 Gig0/1 - Clinic Core Ingress]
  5   <1 ms    <1 ms    <1 ms   172.16.8.36    [SRV-CACHE - Remote Clinic EHR Server]

Trace complete.
```
> [!IMPORTANT]
> Notice Hop 3 has shifted from `172.16.8.82` (`Serial0/0/0`) to `172.16.8.86` (`Serial0/0/1`), proving automatic failover to the secondary path with zero manual operator intervention.

---

## 8. Link Restoration & Preemption Verification

When the primary link is repaired:
```cisco
R1(config)# interface Serial0/0/0
R1(config-if)# no shutdown
```

### Restoration Mechanics:
1. Physical link comes UP.
2. OSPF Hello packets are exchanged over `Serial0/0/0`.
3. In under 2 seconds, OSPF state reaches `FULL`.
4. R1 and R2 receive OSPF LSAs with Administrative Distance 110.
5. Because $AD = 110$ is strictly lower than EIGRP's tuned $AD = 120$, the Cisco RIB evicts the EIGRP routes from the routing table and re-installs the OSPF routes.
6. Traceroute immediately reverts to Hop 3 `172.16.8.82` (`Serial0/0/0`).
7. **Zero Routing Loops Occurred:** Symmetrical AD tuning ensures that neither router retains a stale EIGRP route while the other uses OSPF.
