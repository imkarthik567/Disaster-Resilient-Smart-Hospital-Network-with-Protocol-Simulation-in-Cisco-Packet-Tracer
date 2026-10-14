# Dynamic Routing Architecture & Protocol Design Guide
**Project:** Disaster-Resilient Smart Hospital Network (VIT Vellore — Computer Networks)  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  
**Standard Compliance:** Cisco Packet Tracer 8.x | RFC 2328 (OSPFv2) | RFC 7868 (EIGRP)  

---

## 1. Executive Summary & Routing Architecture Overview

In a disaster-resilient healthcare enterprise connecting an acute-care hospital campus with a remote spoke clinic, dynamic routing must deliver:
1. **Sub-second convergence** during primary transit link severance.
2. **Deterministic path selection** without protocol contention or traffic inversion.
3. **Link-State Database (LSDB) isolation** to shield the campus backbone from branch network churn.
4. **Cryptographic security** to protect against rogue route injection.

This document establishes the comprehensive routing design for **Core Routers R1 and R2**, **Multilayer Distribution Switches SW-D1, SW-D2, and SW-D3**, and the **Internet Edge Gateway**, resolving key architectural dilemmas before configuration generation.

```
+----------------------------------------------------------------------------------------------------+
|                                    INTERNET EDGE & PUBLIC CLOUD                                    |
|                                         EDGE-ISP (172.16.8.101)                                    |
+--------------------------------------------------+-------------------------------------------------+
                                                   | Gig0/2 (172.16.8.102/30) - NAT PAT Outside
                                                   v
+----------------------------------------------------------------------------------------------------+
|                                      MAIN HOSPITAL CAMPUS (OSPF AREA 0)                            |
|                                                                                                    |
|                                        +---------------------+                                     |
|                                        |   Core Router R1    |                                     |
|                                        | (OSPF Router ID:    |                                     |
|                                        |    172.16.8.104)    |                                     |
|                                        +----------+----------+                                     |
|                                                   |                                                |
|                     +-----------------------------+-----------------------------+                  |
|                     | Gi0/0 (172.16.8.90/30)                                    | Gi0/1            |
|                     v                                                           v (172.16.8.94/30) |
|           +-------------------+                                       +-------------------+        |
|           |       SW-D1       |<=====================================>|       SW-D2       |        |
|           | (OSPF ID: .8.106) |            Port-Channel 1             | (OSPF ID: .8.107) |        |
|           +---------+---------+        (Fa0/23 - 24 Trunk)            +---------+---------+        |
|                     |                                                           |                  |
|                     +-----------------------------+-----------------------------+                  |
|                                                   |                                                |
|                                   VLANs 10, 20, 30, 40, 50, 60, 99                                 |
+---------------------------------------------------+------------------------------------------------+
                                                    |
             +--------------------------------------+--------------------------------------+
             | Primary Serial Se0/0/0 (172.16.8.81/30)     | Secondary Serial Se0/0/1 (172.16.8.85/30)
             | OSPF Area 0 Backbone [AD 110]               | EIGRP AS 100 Standby [AD 120]
             | Clock Rate: 128000 | Bandwidth: 2048 kbps   | Clock Rate: 128000 | Bandwidth: 1544 kbps
             v                                             v
+----------------------------------------------------------------------------------------------------+
|                                  REMOTE SPOKE CLINIC (OSPF AREA 1)                                 |
|                                                                                                    |
|                                        +---------------------+                                     |
|                                        |   Core Router R2    |                                     |
|                                        |  (Area Border ABR   |                                     |
|                                        |   OSPF ID: .8.105)  |                                     |
|                                        +----------+----------+                                     |
|                                                   |                                                |
|                                                   | Gi0/0 (172.16.8.98/30) - Area 1                |
|                                                   v                                                |
|                                        +---------------------+                                     |
|                                        |  SW-D3 (Dist Switch)|                                     |
|                                        |   (OSPF ID: .8.108) |                                     |
|                                        +----------+----------+                                     |
|                                                   |                                                |
|                                      Clinic VLANs 10, 30, 40, 60, 99                               |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Problem 1: OSPF Area Hierarchy & ABR Placement

### 2.1 The Inter-Site WAN Boundary Challenge
The initial project concept proposed *"OSPF Area 0 at Main Hospital, Area 1 at Remote Clinic"*. However, connecting R1 and R2 over a point-to-point serial WAN link introduces a fundamental protocol requirement:
- Under **RFC 2328 (OSPFv2)**, an OSPF adjacency will only reach `FULL` state if the **Area ID in received Hello packets matches the receiving interface's configured Area ID**.
- If R1 places `Serial0/0/0` in Area 0 and R2 places `Serial0/0/0` in Area 1, the adjacency fails permanently in `INIT` state. The WAN link must have a unified Area assignment.

### 2.2 Architectural Options Analysis

| Criterion | Option A: WAN in Area 1 (R1 as ABR) | Option B: WAN in Area 0 (R2 as ABR) — **[SELECTED]** |
| :--- | :--- | :--- |
| **ABR Location** | Core Router R1 (Main Campus) | Core Router R2 (Remote Clinic) |
| **WAN Link Area** | Area 1 (`Serial0/0/0` in Area 1 on both R1 and R2) | Area 0 Backbone (`Serial0/0/0` in Area 0 on both R1 and R2) |
| **Backbone Contiguity** | Area 0 terminates at R1 LAN boundary | Area 0 extends across the primary WAN link to R2 |
| **LSDB Impact of WAN Flaps** | Flaps generate Type-1 LSAs inside Area 1, triggering SPF across all clinic switches | Flaps generate Type-1 LSAs in Area 0; contained from Area 1 |
| **Summarization Point** | R1 summarizes Area 1 routes into Area 0 | R2 summarizes Area 1 routes into Area 0 before crossing WAN |
| **Core Router Workload** | R1 manages NAT, PAT, ACLs, and multi-area LSDB | R1 operates as pure backbone router; R2 handles ABR summarization |

### 2.3 Selected Layout & LSDB Implications
**Option B is selected as the authoritative architecture:**
- **Area 0 (Backbone):** Encompasses Main Hospital Core `R1`, Distribution Switches `SW-D1` and `SW-D2`, all campus SVIs, and the Primary WAN Serial link (`172.16.8.80/30`).
- **ABR Placement:** Core Router **`R2`** is designated as the **Area Border Router (ABR)**:
  - `Serial0/0/0` (`172.16.8.82/30`) belongs to **Area 0**.
  - `GigabitEthernet0/0` (`172.16.8.98/30`) belongs to **Area 1**.
  - `Loopback0` (`172.16.8.105/32`) belongs to **Area 0**.
- **Area 1 (Spoke):** Encompasses Clinic Distribution Switch `SW-D3`, Access Switch `SW-A5`, and all clinic VLANs (10, 30, 40, 60, 99).

#### LSDB Isolation Proof
1. **Type-1 (Router LSA) & Type-2 (Network LSA) Containment:** Flooding of Type-1 and Type-2 LSAs is strictly confined to Area 1. Transient link flaps at the clinic (e.g. guest Wi-Fi churn in VLAN 40 or DHCP lease renewals) never cross the ABR boundary into Area 0.
2. **Type-3 (Summary LSA) Generation:** ABR R2 converts Area 1 internal topology into Type-3 Summary LSAs advertised into Area 0.
3. **Partial Route Computation (PRC):** Main Hospital Core R1 and Distribution Switches SW-D1/SW-D2 run a lightweight Partial Route Computation on Type-3 updates rather than a resource-intensive full Shortest Path First (Dijkstra) calculation.

### 2.4 Inter-Area Route Summarization at ABR R2
Without summarization, R2 advertises 6 individual Type-3 LSAs across the serial link into Area 0:
- `172.16.8.0/27` (Clinic Admin)
- `172.16.8.32/27` (Clinic Clinical)
- `172.16.8.64/28` (Clinic Mgmt)
- `172.16.8.96/30` (R2-SW-D3 Transit Link)
- `172.16.6.128/25` (Clinic Guest Wi-Fi)
- `172.16.7.224/27` (Clinic VoIP Voice)

By configuring `area 1 range` commands on ABR R2, these routes are condensed:
```cisco
router ospf 1
 area 1 range 172.16.8.0 255.255.255.0       ! Summarizes Admin, Clinical, Mgmt, and Transit
 area 1 range 172.16.6.128 255.255.255.128   ! Summarizes Clinic Guest
 area 1 range 172.16.7.224 255.255.255.224   ! Summarizes Clinic Voice
```
- **LSDB Reduction:** Reduces advertised inter-area LSAs from 6 down to 3 (a **50.0% reduction** verified by our Python model [`/sim/routing_model.py`](../sim/routing_model.py)).
- **Fault Shielding:** If a clinic VLAN interface flaps, R2 suppresses LSA flooding into Area 0 as long as at least one subnet in the summary range remains operational.

---

## 3. Problem 2: Primary vs. Secondary Path & Administrative Distance Contention

### 3.1 The Administrative Distance (AD) Contention Problem
The Review-1 proposal specifies dual WAN links between R1 and R2:
- **Primary WAN:** Serial link running **OSPF**.
- **Secondary WAN:** Serial link running **EIGRP AS 100**.

Under default Cisco IOS behavior:
$$\text{AD}_{\text{EIGRP Internal}} = 90 \quad < \quad \text{AD}_{\text{OSPF}} = 110$$

If both protocols are enabled and advertise the same remote subnets:
1. The Cisco Routing Information Base (RIB) compares routes by Administrative Distance.
2. The router installs the EIGRP route ($AD = 90$) and ignores the OSPF route ($AD = 110$).
3. **The Failure Mode:** All traffic flows over the secondary link (`Serial0/0/1`), leaving the primary high-speed link (`Serial0/0/0`) completely idle! The primary/backup relationship is inverted.

```
[Default Un-Tuned Contention - FLAGGED DEFECT]
Destination: 172.16.8.32/27 (Clinic ICU)
OSPF Path:   via Serial0/0/0 (AD 110, Cost 64)   -> REJECTED BY RIB
EIGRP Path:  via Serial0/0/1 (AD 90, Metric ...) -> INSTALLED IN RIB (90 < 110)
Result: Traffic incorrectly defaults to secondary backup serial link!
```

### 3.2 Evaluation of Three Solutions

#### Solution (a): Administrative Distance Tuning (`distance eigrp 120 170`)
- **Mechanism:** On R1 and R2, increase EIGRP internal AD to **120** under `router eigrp 100`:
  ```cisco
  router eigrp 100
   distance eigrp 120 170
  ```
- **Resulting Metric Hierarchy:**
  $$\text{AD}_{\text{OSPF}} = 110 \quad < \quad \text{AD}_{\text{EIGRP Tuned}} = 120$$
  - When Primary Link is UP: OSPF ($110$) wins; installed in RIB.
  - When Primary Link FAILS: OSPF neighbor drops; EIGRP ($120$) immediately populates RIB.
- **Evaluation:** Clean, deterministic, zero routing loop risk, supported in Packet Tracer 8.x.

#### Solution (b): Two-Point Mutual Redistribution with Route Tagging & Route Maps
- **Mechanism:** Run OSPF on the primary link and EIGRP only on the secondary link. Redistribute between OSPF and EIGRP at R1 and R2.
- **AD Dynamics:** EIGRP external routes have $AD = 170$. Since $\text{AD}_{\text{OSPF}} = 110 < \text{AD}_{\text{EIGRP Ext}} = 170$, OSPF routes naturally win in the RIB.
- **Evaluation:** Highly sophisticated, but complex to administer. Any error in route-tag filtering produces immediate routing loops.

#### Solution (c): Single-Protocol OSPF on Both Links with Cost Tuning (EIGRP in Comparison Lab)
- **Mechanism:** Run OSPF across both serial links.
  - Set Primary link cost: `ip ospf cost 64` (Bandwidth 2048 kbps).
  - Set Secondary link cost: `ip ospf cost 500` (Bandwidth 64 kbps).
  - Primary path is chosen because $64 < 500$. Secondary link is a floating dynamic backup.
  - Reserve EIGRP for a standalone comparative convergence simulation in `/sim/benchmark_harness.py`.
- **Evaluation:** Industry best practice (avoids running dual IGPs on the same pair of routers), but departs from literal Review-1 multi-protocol wording.

### 3.3 Authoritative Recommendation
1. **Production Hospital Network:** **Solution (a)** is implemented in all configuration files. It directly satisfies the Review-1 multi-protocol requirement, provides automated failover, and introduces zero routing loop risk.
2. **Academic Comparison Lab:** **Solution (c)** is documented as an alternative and evaluated in Section 8 via our Python simulation harness.

---

## 4. Problem 3: Loop Prevention in Two-Point Mutual Redistribution

If mutual redistribution between OSPF and EIGRP is deployed across R1 and R2, a classic **routing feedback loop** arises:

```
                          [Domain Loop Hazard]
                    OSPF Area 0 Domain (R1 Core)
                                 |
                 (1) Route X injected into OSPF
                 (2) R1 redistributes OSPF -> EIGRP (Tag None)
                                 |
                                 v
                     EIGRP AS 100 Domain (Secondary WAN)
                                 |
                 (3) Route X arrives at R2 via EIGRP
                 (4) R2 redistributes EIGRP -> OSPF Area 1!
                                 |
                                 v
                 (5) Route X re-advertised to R1 with corrupt metric!
                 (6) Routing Loop / Blackhole Formed.
```

### 4.1 Loop Prevention via Symmetrical 4-Way Route Tagging
To prevent route feedback, every redistributed route is stamped with an administrative **Route Tag** indicating its domain of origin:
- **Tag `110`:** Route originated inside OSPF.
- **Tag `200`:** Route originated inside EIGRP.

#### Cisco IOS Configuration for Core Router R1
```cisco
! --- Route-Maps for Tagging & Loop Filtering ---
route-map OSPF_TO_EIGRP deny 10
 match tag 200                                ! Deny routes that originated in EIGRP
route-map OSPF_TO_EIGRP permit 20
 set tag 110                                  ! Stamp OSPF routes with Tag 110

route-map EIGRP_TO_OSPF deny 10
 match tag 110                                ! Deny routes that originated in OSPF
route-map EIGRP_TO_OSPF permit 20
 set tag 200                                  ! Stamp EIGRP routes with Tag 200

! --- Redistribution with Route-Maps ---
router eigrp 100
 redistribute ospf 1 metric 10000 100 255 1 1500 route-map OSPF_TO_EIGRP

router ospf 1
 redistribute eigrp 100 subnets route-map EIGRP_TO_OSPF
```

#### Symmetrical Configuration for Core Router R2
Core Router R2 applies identical route-maps:
- When R2 receives Route $X$ via EIGRP with `tag 110`, route-map `EIGRP_TO_OSPF` evaluates rule 10 (`match tag 110`) and executes a **DENY**.
- Route $X$ is blocked from being injected into OSPF Area 1.
- **Mathematical Guarantee:** Routing loops and metric corruption are 100% prevented.

---

## 5. Problem 4: Fast Convergence Tuning & Packet Tracer Support Audit

Fast reconvergence is critical for medical IoT telemetry. We benchmarked and audited all convergence tuning features against Cisco Packet Tracer 8.x:

| Convergence Feature | Cisco IOS Syntax | Packet Tracer 8.x Status | Operational Behavior in Design |
| :--- | :--- | :---: | :--- |
| **Fast Hello / Dead Timers** | `interface Serial0/0/0`<br>` ip ospf hello-interval 1`<br>` ip ospf dead-interval 4` | **SUPPORTED** | Configured on primary serial link. Detects WAN failure in **4 seconds** instead of default 40s. |
| **Point-to-Point Network Type** | `interface GigabitEthernet0/0`<br>` ip ospf network point-to-point` | **SUPPORTED** | Configured on all `/30` routed links (`R1-SW-D1`, `R1-SW-D2`, `R2-SW-D3`). Eliminates 40s DR/BDR election wait time. |
| **Passive-Interface Default** | `router ospf 1`<br>` passive-interface default`<br>` no passive-interface Gig0/0` | **SUPPORTED** | Suppresses Hello multicasts on client VLANs, securing patient subnets and saving switch CPU. |
| **OSPF SPF Throttling** | `router ospf 1`<br>` timers throttle spf 50 200 5000` | **NOT SUPPORTED**<br>(CLI syntax rejected) | Documented as Packet Tracer limitation. Evaluated via Python simulation model. |
| **OSPF LSA Throttling** | `router ospf 1`<br>` timers throttle lsa all 50 200 5000` | **NOT SUPPORTED** | Documented as Packet Tracer limitation. |
| **BFD (Bidirectional Forwarding)**| `interface Serial0/0/0`<br>` bfd interval 50 min_rx 50 multiplier 3` | **NOT SUPPORTED** | Documented as Packet Tracer limitation. Modeled in benchmark harness. |

> [!IMPORTANT]
> Because Packet Tracer does not support `timers throttle spf`, attempting to enter it causes a syntax rejection error. Our configs strictly omit unsupported commands, maintaining 100% clean linter compliance.

---

## 6. Problem 5: Default Route Origination toward ISP & Floating Static Backup

### 6.1 ISP Gateway Connectivity
Core Router `R1` connects to `EDGE-ISP` via `GigabitEthernet0/2` (`172.16.8.102/30` to `172.16.8.101/30`):
- Static default route on `R1`:
  ```cisco
  ip route 0.0.0.0 0.0.0.0 172.16.8.101
  ```
- Dynamic Injection into OSPF:
  ```cisco
  router ospf 1
   default-information originate
  ```
  `default-information originate` advertises a **Type-5 AS-External LSA** ($E_2$ metric 20) throughout Area 0 and Area 1 **only while `172.16.8.101` is reachable in R1's RIB**. If the ISP uplink drops, R1 withdraws the default route, preventing campus devices from blackholing packets.

### 6.2 Floating Static Default Route Backup
On Distribution Switches `SW-D1` and `SW-D2`, floating static routes provide emergency default gateway connectivity if the OSPF routing process crashes:
```cisco
ip route 0.0.0.0 0.0.0.0 172.16.8.90 200       ! Floating default on SW-D1 (AD 200)
ip route 0.0.0.0 0.0.0.0 172.16.8.94 200       ! Floating default on SW-D2 (AD 200)
```
Because $AD = 200$ is higher than OSPF ($110$) and EIGRP ($120$), this route remains dormant in the configuration and only activates during a catastrophic routing protocol failure.

---

## 7. Problem 6: OSPF & EIGRP Cryptographic Authentication

Packet Tracer 8.x supports MD5 cryptographic authentication on both OSPF and EIGRP interfaces, securing links against rogue router insertion:

### 7.1 OSPF MD5 Authentication on Primary WAN (`Serial0/0/0`)
Configured identically on `R1` and `R2`:
```cisco
interface Serial0/0/0
 ip ospf authentication message-digest
 ip ospf message-digest-key 1 md5 CiscoHospital2026
```

### 7.2 EIGRP MD5 Authentication on Secondary WAN (`Serial0/0/1`)
Uses a cryptographic key chain on `R1` and `R2`:
```cisco
key chain EIGRP_AUTH
 key 1
  key-string CiscoHospital2026
exit

interface Serial0/0/1
 ip authentication mode eigrp 100 md5
 ip authentication key-chain eigrp 100 EIGRP_AUTH
```

---

## 8. Master Routing Decision & Implementation Table

| Item | Problem / Requirement | Architectural Decision | Target Devices | Exact Cisco IOS Commands |
| :---: | :--- | :--- | :--- | :--- |
| **RD-01** | OSPF Area Hierarchy | Area 0 Backbone at Main Campus & WAN; Area 1 at Remote Clinic | `R1`, `R2`, `SW-D1`, `SW-D2`, `SW-D3` | `router ospf 1`<br>` network 172.16.8.80 0.0.0.3 area 0`<br>` network 172.16.8.96 0.0.0.3 area 1` |
| **RD-02** | ABR Assignment | Designate Core Router `R2` as ABR; condense Area 1 LSAs | `R2` | `router ospf 1`<br>` area 1 range 172.16.8.0 255.255.255.0`<br>` area 1 range 172.16.6.128 255.255.255.128`<br>` area 1 range 172.16.7.224 255.255.255.224` |
| **RD-03** | Primary/Backup Path Contention | Raise EIGRP internal AD from 90 to 120 so OSPF (AD 110) wins | `R1`, `R2` | `router eigrp 100`<br>` distance eigrp 120 170` |
| **RD-04** | Fast Link Failure Detection | Tune OSPF timers on primary serial link to 1s Hello / 4s Dead | `R1`, `R2` | `interface Serial0/0/0`<br>` ip ospf hello-interval 1`<br>` ip ospf dead-interval 4` |
| **RD-05** | DR/BDR Elimination | Configure Point-to-Point network type on `/30` routed links | `R1`, `R2`, `SW-D1`, `SW-D2`, `SW-D3` | `interface <port>`<br>` ip ospf network point-to-point` |
| **RD-06** | Host Port Security | Suppress OSPF hellos on all host-facing user VLANs | `SW-D1`, `SW-D2`, `SW-D3` | `router ospf 1`<br>` passive-interface default`<br>` no passive-interface <routed-port>` |
| **RD-07** | Internet Default Route | Originate dynamic Type-5 default route into OSPF | `R1` | `ip route 0.0.0.0 0.0.0.0 172.16.8.101`<br>`router ospf 1`<br>` default-information originate` |
| **RD-08** | Emergency Backup Default | Deploy floating static default route with AD 200 | `SW-D1`, `SW-D2` | `ip route 0.0.0.0 0.0.0.0 172.16.8.90 200` |
| **RD-09** | OSPF Link Security | MD5 cryptographic authentication on primary serial link | `R1`, `R2` | `interface Serial0/0/0`<br>` ip ospf authentication message-digest`<br>` ip ospf message-digest-key 1 md5 CiscoHospital2026` |
| **RD-10** | EIGRP Link Security | Key-chain MD5 authentication on standby serial link | `R1`, `R2` | `key chain EIGRP_AUTH`<br>` key 1`<br>`  key-string CiscoHospital2026`<br>`interface Serial0/0/1`<br>` ip authentication mode eigrp 100 md5`<br>` ip authentication key-chain eigrp 100 EIGRP_AUTH` |

---

## 9. Simulation Model Verification & Findings

Our Python simulation model [`/sim/routing_model.py`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/sim/routing_model.py) generated the following empirical results:

```
================================================================================
  DYNAMIC ROUTING ARCHITECTURE & CONVERGENCE SIMULATION RESULTS
================================================================================

1. ADMINISTRATIVE DISTANCE (AD) ROUTE ELECTION:
Scenario                                            | Primary (Se0/0/0) | OSPF AD | EIGRP AD | RIB Winner
----------------------------------------------------+-------------------+---------+----------+----------------------------
Default Cisco Distances (Flawed Design)             | UP                | 110     | 90       | EIGRP (Se0/0/1 - Secondary)
Tuned Distances (ADR-02) - Primary Link UP          | UP                | 110     | 120      | OSPF (Se0/0/0 - Primary)
Tuned Distances (ADR-02) - Primary Link DOWN        | DOWN              | Evicted | 120      | EIGRP (Se0/0/1 - Secondary)

2. TWO-POINT MUTUAL REDISTRIBUTION LOOP SIMULATION:
- With Route Tagging (Tag 110 OSPF / Tag 200 EIGRP):
  * Route 172.16.7.128/26 tagged 110 upon redistribution into EIGRP.
  * R2 inspects tag: match tag 110 -> DENY! Re-injection blocked.
  * Result: ZERO ROUTING LOOPS.

- Without Route Tagging:
  * Route re-injected into OSPF Area 1 with corrupt metric.
  * Result: ROUTING FEEDBACK LOOP DETECTED.

3. OSPF ABR ROUTE SUMMARIZATION AT R2:
- Unsummarized Type-3 LSAs: 6
- Summarized Type-3 LSAs:   3
- LSDB Route Reduction:     50.0%
================================================================================
```
