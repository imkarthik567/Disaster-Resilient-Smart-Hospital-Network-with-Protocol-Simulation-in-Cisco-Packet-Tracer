# VLSM Addressing Plan

**Project:** Disaster-Resilient Smart Hospital Network  
**Base Block:** `172.16.0.0/16` (65,536 addresses)  
**Computed by:** `scripts/utils/vlsm_calculator.py` — machine-computed, not manual.

---

## Compact Summary Table

| # | Name | VLAN | CIDR | Subnet Mask | Wildcard | Gateway | Usable Hosts |
|---|------|------|------|-------------|----------|---------|:------------:|
| 1 | Main-VLAN40-Guest | 40 | `172.16.0.0/23` | `255.255.254.0` | `0.0.1.255` | `172.16.0.1` | 510 |
| 2 | Main-VLAN30-Admin | 30 | `172.16.2.0/24` | `255.255.255.0` | `0.0.0.255` | `172.16.2.1` | 254 |
| 3 | Main-VLAN60-Voice | 60 | `172.16.3.0/25` | `255.255.255.128` | `0.0.0.127` | `172.16.3.1` | 126 |
| 4 | Main-VLAN10-ICU | 10 | `172.16.3.128/26` | `255.255.255.192` | `0.0.0.63` | `172.16.3.129` | 62 |
| 5 | Main-VLAN20-Surgery | 20 | `172.16.3.192/26` | `255.255.255.192` | `0.0.0.63` | `172.16.3.193` | 62 |
| 6 | Main-VLAN50-Servers | 50 | `172.16.4.0/27` | `255.255.255.224` | `0.0.0.31` | `172.16.4.1` | 30 |
| 7 | Main-VLAN99-Mgmt | 99 | `172.16.4.32/27` | `255.255.255.224` | `0.0.0.31` | `172.16.4.33` | 30 |
| 8 | Remote-VLAN10-Clinical | 10 | `172.16.4.64/27` | `255.255.255.224` | `0.0.0.31` | `172.16.4.65` | 30 |
| 9 | Remote-VLAN30-Admin | 30 | `172.16.4.96/27` | `255.255.255.224` | `0.0.0.31` | `172.16.4.97` | 30 |
| 10 | Remote-VLAN60-Voice | 60 | `172.16.4.128/27` | `255.255.255.224` | `0.0.0.31` | `172.16.4.129` | 30 |
| 11 | Remote-VLAN50-Servers | 50 | `172.16.4.160/28` | `255.255.255.240` | `0.0.0.15` | `172.16.4.161` | 14 |
| 12 | Remote-VLAN99-Mgmt | 99 | `172.16.4.176/28` | `255.255.255.240` | `0.0.0.15` | `172.16.4.177` | 14 |
| 13 | WAN-Primary-Serial | -- | `172.16.4.192/30` | `255.255.255.252` | `0.0.0.3` | -- | 2 |
| 14 | WAN-Secondary | -- | `172.16.4.196/30` | `255.255.255.252` | `0.0.0.3` | -- | 2 |
| 15 | R1-Loopback0 | -- | `172.16.4.200/32` | `255.255.255.255` | `0.0.0.0` | -- | 1 |
| 16 | R2-Loopback0 | -- | `172.16.4.201/32` | `255.255.255.255` | `0.0.0.0` | -- | 1 |

**Utilisation:** 1,226 / 65,536 addresses (1.87%) — ample room for future expansion.

---

## Device Interface-to-IP Mapping

### Core Routers

#### R1 — Main Hospital Core (Router: 2911)

| Interface | Connected To | IP Address | Mask | Subnet Role | OSPF Area / EIGRP |
|-----------|-------------|------------|------|-------------|--------------------|
| `Loopback0` | -- | `172.16.4.200` | `255.255.255.255` | Router-ID | Area 0 |
| `Se0/0/0` (DCE) | R2 `Se0/0/0` | `172.16.4.193` | `255.255.255.252` | WAN Primary | Area 0 (OSPF) |
| `Se0/0/1` (DCE) | R2 `Se0/0/1` | `172.16.4.197` | `255.255.255.252` | WAN Secondary | EIGRP AS 100 |
| `Gig0/0` | SW-D1 (trunk/routed) | `172.16.3.129`* | `255.255.255.192`* | Link to Distribution | Area 0 |
| `Gig0/1` | SW-D2 (trunk/routed) | (see note) | -- | Link to Distribution | Area 0 |

> *\*R1's LAN-facing interface(s): if using router-on-a-stick, configure sub-interfaces. If SW-D1/D2 are L3 multilayer switches doing inter-VLAN routing, R1 connects to them via a routed point-to-point link (described in design_notes.md). The gateway IPs in the table above are assigned to the distribution switch SVIs, not to R1.*

#### R2 — Remote Clinic Core (Router: 2911)

| Interface | Connected To | IP Address | Mask | Subnet Role | OSPF Area / EIGRP |
|-----------|-------------|------------|------|-------------|--------------------|
| `Loopback0` | -- | `172.16.4.201` | `255.255.255.255` | Router-ID | Area 1 |
| `Se0/0/0` | R1 `Se0/0/0` | `172.16.4.194` | `255.255.255.252` | WAN Primary | Area 0 (OSPF) |
| `Se0/0/1` | R1 `Se0/0/1` | `172.16.4.198` | `255.255.255.252` | WAN Secondary | EIGRP AS 100 |
| `Gig0/0` | SW-D3 (trunk/routed) | (see note) | -- | Link to Distribution | Area 1 |

---

### Distribution Switches (Multilayer: 3560-24PS)

Inter-VLAN routing is performed on the distribution switches via **Switched Virtual Interfaces (SVIs)**.

#### SW-D1 — Main Hospital Distribution 1

| Interface | Type | IP / VLAN | Description |
|-----------|------|-----------|-------------|
| `VLAN 10 SVI` | SVI | `172.16.3.129 /26` | ICU gateway |
| `VLAN 20 SVI` | SVI | `172.16.3.193 /26` | Surgery gateway |
| `VLAN 50 SVI` | SVI | `172.16.4.1 /27` | Server Farm gateway |
| `VLAN 99 SVI` | SVI | `172.16.4.33 /27` | Management gateway |
| `Gig0/1` | Trunk | 802.1Q to SW-D2 | Inter-distribution link |
| `Gig0/2` | Routed/Trunk | To R1 `Gig0/0` | Uplink to core |
| `Fa0/1-6` | Trunk | To SW-A1, SW-A2 | Downlinks to access |

#### SW-D2 — Main Hospital Distribution 2

| Interface | Type | IP / VLAN | Description |
|-----------|------|-----------|-------------|
| `VLAN 30 SVI` | SVI | `172.16.2.1 /24` | Admin gateway |
| `VLAN 40 SVI` | SVI | `172.16.0.1 /23` | Guest gateway |
| `VLAN 60 SVI` | SVI | `172.16.3.1 /25` | Voice gateway |
| `Gig0/1` | Trunk | 802.1Q to SW-D1 | Inter-distribution link |
| `Gig0/2` | Routed/Trunk | To R1 `Gig0/1` | Uplink to core |
| `Fa0/1-6` | Trunk | To SW-A3, SW-A4 | Downlinks to access |

#### SW-D3 — Remote Clinic Distribution

| Interface | Type | IP / VLAN | Description |
|-----------|------|-----------|-------------|
| `VLAN 10 SVI` | SVI | `172.16.4.65 /27` | Clinical gateway |
| `VLAN 30 SVI` | SVI | `172.16.4.97 /27` | Admin gateway |
| `VLAN 50 SVI` | SVI | `172.16.4.161 /28` | Server cache gateway |
| `VLAN 60 SVI` | SVI | `172.16.4.129 /27` | Voice gateway |
| `VLAN 99 SVI` | SVI | `172.16.4.177 /28` | Management gateway |
| `Gig0/1` | Routed/Trunk | To R2 `Gig0/0` | Uplink to core |
| `Fa0/1-4` | Trunk | To SW-A5 | Downlinks to access |

---

### Access Switches (2960-24TT)

Access switches carry no IP routing — all ports are either **Access** or **Trunk**.

| Switch | Site | VLANs Served | Trunk Uplink To | Description |
|--------|------|--------------|-----------------|-------------|
| SW-A1 | Main | 10, 60, 99, 999 | SW-D1 Fa0/1 | ICU floor |
| SW-A2 | Main | 20, 60, 99, 999 | SW-D1 Fa0/3 | Surgery floor |
| SW-A3 | Main | 30, 60, 99, 999 | SW-D2 Fa0/1 | Admin floor |
| SW-A4 | Main | 40, 60, 99, 999 | SW-D2 Fa0/3 | Guest / overflow |
| SW-A5 | Remote | 10, 30, 50, 60, 99, 999 | SW-D3 Fa0/1 | Clinic floor |

---

### WAN Point-to-Point Links

| Link | R1 Interface | R1 IP | R2 Interface | R2 IP | Mask | Protocol |
|------|-------------|-------|-------------|-------|------|----------|
| Primary | `Se0/0/0` | `172.16.4.193` | `Se0/0/0` | `172.16.4.194` | `/30` | OSPF Area 0 |
| Secondary | `Se0/0/1` | `172.16.4.197` | `Se0/0/1` | `172.16.4.198` | `/30` | EIGRP AS 100 |

---

### DHCP Pools (served from PT Server or R1)

| Pool Name | Network | Default Router | DNS Server | Excluded Range |
|-----------|---------|---------------|------------|----------------|
| POOL-ICU | `172.16.3.128/26` | `172.16.3.129` | `172.16.4.2` | `.129` - `.131` (infra) |
| POOL-SURGERY | `172.16.3.192/26` | `172.16.3.193` | `172.16.4.2` | `.193` - `.195` (infra) |
| POOL-ADMIN | `172.16.2.0/24` | `172.16.2.1` | `172.16.4.2` | `.1` - `.5` (infra) |
| POOL-GUEST | `172.16.0.0/23` | `172.16.0.1` | `172.16.4.2` | `.1` - `.5` (infra) |
| POOL-VOICE | `172.16.3.0/25` | `172.16.3.1` | `172.16.4.2` | `.1` - `.3` (infra) |

> **DNS Server IP:** `172.16.4.2` — the PT Server in VLAN 50 (Server Farm).  
> **HTTP Server IP:** `172.16.4.3` (or same server, `172.16.4.2`).

---

## VLAN Summary

| VLAN ID | Name | Purpose | Sites Present |
|:-------:|------|---------|---------------|
| 10 | ICU | Bedside monitors, SBC telemetry | Main, Remote |
| 20 | Surgery | Operating theatre equipment | Main only |
| 30 | Admin | Staff workstations | Main, Remote |
| 40 | Guest | Untrusted visitor Wi-Fi | Main only |
| 50 | ServerFarm | DNS, HTTP, DHCP, PACS servers | Main, Remote |
| 60 | Voice | IP phones, VoIP | Main, Remote |
| 99 | Management | Switch/AP management OOB | Main, Remote |
| 999 | Native | Native/unused (no traffic) | All |
