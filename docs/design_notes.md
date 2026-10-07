# Design Notes & Packet Tracer Caveats

**Project:** Disaster-Resilient Smart Hospital Network  
**Last Updated:** 2026-10-07

---

## 1. Architecture Overview

```
                         INTERNET
                            |
                     [NAT/ACL on R1]
                            |
          ┌─────────── R1 (Area 0) ───────────┐
          │   Se0/0/0          Se0/0/1         │
          │   OSPF             EIGRP           │
          │   (primary)        (backup,AD=120) │
          │   Se0/0/0          Se0/0/1         │
          └─────────── R2 (ABR) ──────────────┘
                     Area 0 ↕ Area 1
                            |
         ┌──────────────────┼───────────────────┐
     SW-D1 ════ SW-D2       │                SW-D3
    (Main Distrib.)         │           (Remote Distrib.)
     │    │    │    │       │                │    │
   SW-A1 SW-A2 SW-A3 SW-A4 │              SW-A5 ...
   ICU  Surg  Admin Guest  │             Clinic
                            │
                     [Main Hospital]      [Remote Clinic]
```

### Three-Tier Hierarchy Rationale

| Layer | Device(s) | Key Functions |
|-------|-----------|---------------|
| **Core** | R1, R2 (Cisco 2911) | WAN routing (OSPF + EIGRP), NAT, Internet edge, QoS marking |
| **Distribution** | SW-D1, SW-D2, SW-D3 (3560-24PS) | Inter-VLAN routing via SVIs, ACL enforcement, STP root, trunk aggregation |
| **Access** | SW-A1 to SW-A5 (2960-24TT) | Port security, VLAN assignment, 802.1Q trunks up |

---

## 2. Routing Design: OSPF + EIGRP Failover

### The Problem with Default Administrative Distances

Your design specifies OSPF on the primary WAN and EIGRP on the secondary. However:

| Protocol | Default AD |
|----------|:----------:|
| EIGRP Internal | **90** |
| OSPF | **110** |

If left at defaults, **EIGRP would be preferred** over OSPF — the opposite of what we want.

### The Fix

On **both R1 and R2**, raise EIGRP's AD above OSPF's:

```
router eigrp 100
 distance eigrp 120 170
```

This sets:
- EIGRP **internal** routes to AD **120** (was 90)
- EIGRP **external** routes to AD **170** (was 170, unchanged)

**Result:** OSPF routes (AD 110) are installed in the routing table when both paths are available. When the primary serial link fails and OSPF adjacency drops, EIGRP routes (AD 120) take over automatically. No redistribution needed — both protocols advertise the same destination networks independently.

### OSPF Area Design

- **Area 0 (Backbone):** All R1 LAN interfaces + the primary WAN serial link.
- **Area 1:** All R2 LAN interfaces (Remote Clinic subnets).
- **R2 is the ABR:** R2's Se0/0/0 is in Area 0, its Gig0/0 (to SW-D3) is in Area 1.
- R1 is entirely in Area 0.

### What to Verify in PT

- [ ] `show ip route` on R1: remote clinic subnets should appear as `O IA` (OSPF inter-area) via Se0/0/0, **not** as `D` (EIGRP).
- [ ] Shut down Se0/0/0 on R1: same subnets should reappear as `D` via Se0/0/1 after convergence.
- [ ] `show ip eigrp topology` should show the remote routes in the topology table even while OSPF is active (they're just not installed in the RIB because AD 120 > AD 110).

### PT Caveat: `distance eigrp` Command

The `distance eigrp <internal> <external>` command works on PT 8.x routers (2911, 1941, etc.). If for any reason it is not accepted, the fallback is:

```
router eigrp 100
 distance 120
```

This sets a blanket AD of 120 for all EIGRP routes. Less granular but achieves the same failover behavior.

---

## 3. Distribution Layer: Inter-VLAN Routing with SVIs

### Why SVIs on Distribution Switches (Not Router-on-a-Stick)

Router-on-a-stick forces all inter-VLAN traffic through a single router sub-interface — a bottleneck and single point of failure. Using **L3 multilayer switches (3560-24PS)** with SVIs:

- Routes locally between VLANs at wire speed
- Only sends traffic to R1 when it needs to reach the WAN, Internet, or Remote Clinic
- Provides a natural place for ACLs (applied on the SVI)

### VLAN-to-Switch Assignment

| Distribution Switch | SVIs (Gateway for) | Rationale |
|--------------------|--------------------|-----------|
| **SW-D1** | VLAN 10, 20, 50, 99 | Clinical + Servers — low-latency path to PACS |
| **SW-D2** | VLAN 30, 40, 60 | Admin + Guest + Voice — higher host counts |
| **SW-D3** | VLAN 10, 30, 50, 60, 99 | All remote clinic VLANs |

### Distribution-to-Core Connectivity

SW-D1 and SW-D2 each have a **routed uplink** (no switchport) to R1. We use a small /30 transit subnet for each:

| Link | Subnet | SW-Dx IP | R1 IP |
|------|--------|----------|-------|
| SW-D1 ↔ R1 | `172.16.5.0/30` | `.1` | `.2` |
| SW-D2 ↔ R1 | `172.16.5.4/30` | `.5` | `.6` |
| SW-D3 ↔ R2 | `172.16.5.8/30` | `.9` | `.10` |

> These three /30 transit subnets were carved from the unused portion of `172.16.0.0/16` (starting at `172.16.5.0`). They must be added to the OSPF/EIGRP network statements.

**On the 3560**, the uplink port is configured as:

```
interface GigabitEthernet0/2
 no switchport
 ip address 172.16.5.1 255.255.255.252
 no shutdown
```

Then a default route (or OSPF) points upstream to R1:

```
ip route 0.0.0.0 0.0.0.0 172.16.5.2
```

> **PT Caveat:** Cisco 3560 in PT supports `ip routing`, `no switchport`, and SVIs. Confirm `ip routing` is enabled globally with `show ip route` — you should see connected/local routes for all SVIs.

### STP Configuration

- **SW-D1:** `spanning-tree vlan 10,20,50,99 root primary` (root for its VLANs)
- **SW-D2:** `spanning-tree vlan 30,40,60 root primary`
- Cross-link between SW-D1 and SW-D2 ensures L2 redundancy.
- Access switches remain at default STP priority.
- **Native VLAN 999** on all trunks to avoid VLAN-hopping attacks.

---

## 4. Security Design

### ACL Strategy

**Goal:** Guest VLAN (40) must NOT reach ICU (10), Surgery (20), or Server Farm (50).

Applied **inbound on SW-D2's VLAN 40 SVI** (filter at the source):

```
ip access-list extended BLOCK-GUEST
 deny   ip 172.16.0.0 0.0.1.255 172.16.3.128 0.0.0.63     ! Guest → ICU
 deny   ip 172.16.0.0 0.0.1.255 172.16.3.192 0.0.0.63     ! Guest → Surgery
 deny   ip 172.16.0.0 0.0.1.255 172.16.4.0   0.0.0.31     ! Guest → Servers
 permit ip any any                                          ! Allow everything else
!
interface Vlan40
 ip access-group BLOCK-GUEST in
```

> **Wildcard masks above are code-computed.** They match exactly the VLSM subnets in the addressing plan.

### NAT Overload (PAT)

Configured on **R1**, translating all internal `172.16.0.0/16` traffic to R1's Internet-facing interface:

```
ip nat inside source list NAT-ACL interface GigabitEthernet0/2 overload
!
ip access-list standard NAT-ACL
 permit 172.16.0.0 0.0.255.255
!
! Mark interfaces:
interface GigabitEthernet0/0
 ip nat inside
interface GigabitEthernet0/2
 ip nat outside
```

> **PT Caveat:** NAT overload (PAT) works in PT 8.x on routers. The Internet-facing interface depends on your topology — adjust `Gig0/2` to whatever interface connects to your ISP/cloud.

---

## 5. QoS Design

### DSCP Marking Plan

| Traffic Class | DSCP Value | DSCP Name | PHB | Examples |
|--------------|:----------:|-----------|-----|----------|
| Real-time vitals & VoIP | 46 | EF | Expedited Forwarding | UDP telemetry from SBC, VoIP RTP |
| Medical imaging | 26 | AF31 | Assured Forwarding | TCP DICOM/PACS transfers |
| Everything else | 0 | BE | Best Effort | Guest browsing, email |

### MQC Configuration (on R1)

```
! --- Class Maps ---
class-map match-any VITALS-VOICE
 match dscp ef
!
class-map match-any IMAGING
 match dscp af31
!
! --- Policy Map ---
policy-map HOSPITAL-QOS
 class VITALS-VOICE
  priority percent 30
 class IMAGING
  bandwidth percent 40
 class class-default
  fair-queue
!
! --- Apply to WAN interfaces ---
interface Serial0/0/0
 service-policy output HOSPITAL-QOS
interface Serial0/0/1
 service-policy output HOSPITAL-QOS
```

> **PT Caveat (IMPORTANT):** Packet Tracer's MQC support is **limited**. `class-map`, `policy-map`, and `service-policy` are accepted syntactically on routers, but PT may not actually enforce queuing behavior during simulation. The commands will appear in `show running-config` and `show policy-map`, which is sufficient for demonstration and documentation purposes. If PT rejects `priority percent` or `bandwidth percent`, fall back to:
> ```
> policy-map HOSPITAL-QOS
>  class VITALS-VOICE
>   set dscp ef
>  class IMAGING
>   set dscp af31
> ```
> This at least marks packets, even if PT doesn't queue them differentially.

---

## 6. SBC Python Scripts — Scope & Limitations

### What PT's SBC-PT Supports

- Python 3 scripting via the **Programming** tab on the SBC device
- GPIO access, basic networking via PT's custom modules
- `realtime` module for timing
- **No** `socket` module (standard Python sockets are not available)
- Communication between SBCs uses PT's IoT/networking infrastructure or custom serial/GPIO

### Design Approach for Protocol Simulations

Since we cannot use real TCP/UDP sockets between SBCs, our protocol simulations are **self-contained algorithmic demonstrations**:

1. **2-D Parity:** Encode a message, compute row+column parity, introduce bit errors, detect them.
2. **Checksum:** Compute 16-bit Internet checksum, verify integrity, measure overhead.
3. **Go-Back-N:** Simulate windowed transmission with frame loss and timer expiry.
4. **Selective Repeat:** Simulate individual frame ACK/NAK with out-of-order buffering.

Each script outputs to the SBC's **Terminal** tab, producing logs suitable for screenshots in the project report.

### If Socket Communication IS Needed

If the evaluators expect SBC-to-SBC communication: place two SBCs on the same VLAN and use PT's IoT messaging API (if available in 8.x) or connect them via a custom IoT device. This requires PT 8.2+ and should be tested first.

---

## 7. Assumptions Log

| # | Assumption | Must Verify |
|---|-----------|-------------|
| 1 | Remote Clinic does NOT have Surgery (VLAN 20) or Guest (VLAN 40) | Confirm with project requirements |
| 2 | 3560-24PS is used for distribution switches (supports `ip routing`, SVIs) | Verify device model in PT |
| 3 | 2911 routers are used for R1 and R2 (have 2x serial + 2x GigE) | Verify available modules in PT |
| 4 | HWIC-2T serial module is installed in routers for dual serial ports | Add module in PT's Physical tab |
| 5 | `distance eigrp 120 170` is accepted in PT 8.x | Test on first router config |
| 6 | PT's MQC accepts `priority percent` and `bandwidth percent` | Test; fallback to `set dscp` if not |
| 7 | SBC-PT Python does NOT have socket module | Confirm; adjust script design if it does |
| 8 | Clock rate on serial DCE side is set to 128000 (or 64000) | Standard PT serial config |
| 9 | The Internet edge uses a simulated ISP cloud or loopback | Adjust NAT outside interface accordingly |
| 10 | Transit /30 subnets between distribution and core (172.16.5.0/30, .4/30, .8/30) are acceptable | Review addressing plan |
