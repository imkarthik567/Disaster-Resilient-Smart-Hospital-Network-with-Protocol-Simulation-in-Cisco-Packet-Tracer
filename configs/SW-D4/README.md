# `configs/SW-D4` - Remote Clinic High-Availability Distribution Switch (HA Extension)

## Purpose
Contains the complete Cisco IOS configuration for **SW-D4**, an optional secondary Multilayer Layer-3 Switch designed to eliminate the Single Point of Failure (SPOF) present in the single-chassis `SW-D3` branch clinic design.

When deployed alongside `SW-D3`, `SW-D4` establishes:
1. **HSRP Version 2 Gateway Redundancy:** Default gateway survivability across all clinic VLANs (10, 30, 40, 60, 99).
2. **Deterministic Load-Balancing:** SW-D3 is Active for Clinical (10) and Voice (60); SW-D4 is Active for Admin (30), Guest (40), and Management (99).
3. **Uplink Failure Protection:** Uplink tracking (`standby <group> track GigabitEthernet0/1 20`) dynamically fails over traffic if the core router transit link drops.
4. **Inter-Switch Aggregation:** 2-port 802.1Q EtherChannel (`Port-Channel 1` over `Fa0/21 - 22`) cross-linking `SW-D3` and `SW-D4`.

## Device Metadata
- **Device Name:** `SW-D4`
- **Hardware Platform:** Cisco Catalyst 3560-24PS (Multilayer Switch)
- **SVIs Hosted:**
  - VLAN 10 (Clinical): `172.16.8.35/27` (VIP `172.16.8.33` - Standby)
  - VLAN 30 (Admin): `172.16.8.3/27` (VIP `172.16.8.1` - Active, Priority 110 Preempt)
  - VLAN 40 (Guest): `172.16.6.131/25` (VIP `172.16.6.129` - Active, Priority 110 Preempt)
  - VLAN 60 (Voice): `172.16.7.227/27` (VIP `172.16.7.225` - Standby)
  - VLAN 99 (Mgmt): `172.16.8.67/28` (VIP `172.16.8.65` - Active, Priority 110 Preempt)
- **STP Role:** Rapid PVST+ Primary Root for VLANs 30, 40, 99; Secondary Root for VLANs 10, 60.
- **Uplink:** `GigabitEthernet0/1` -> `R2 GigabitEthernet0/1` (`172.16.8.114/30` routed link).
- **Inter-Distribution:** `Fa0/21 - 22` -> `SW-D3 Fa0/21 - 22` (`Port-Channel 1` trunk).
- **Downlink:** `Fa0/24` -> `SW-A5 GigabitEthernet0/2` (802.1Q trunk).

## How to Enable the HA Extension
1. Deploy `SW-D4` in the Packet Tracer workspace next to `SW-D3`.
2. Cable `Fa0/21` and `Fa0/22` between `SW-D3` and `SW-D4`.
3. Cable `SW-D4 Fa0/24` to `SW-A5 GigabitEthernet0/2`.
4. Cable `SW-D4 GigabitEthernet0/1` to `R2 GigabitEthernet0/1`.
5. Apply `/configs/SW-D4/SW-D4.cfg` to `SW-D4`.
6. Update `SW-D3` using the companion configuration `/configs/SW-D3/SW-D3_ha_extension.cfg`.
