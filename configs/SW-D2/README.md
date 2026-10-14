# `configs/SW-D2` - Main Hospital Distribution Switch 2

## Purpose
Contains the complete Cisco IOS configuration for **SW-D2**, a Multilayer Layer-3 Switch (Catalyst 3560-24PS) aggregating surgery suites, guest networks, and VoIP systems, while providing full hot-standby redundancy for SW-D1. Provides hardware-switched inter-VLAN routing, hosts HSRP v2 active/standby gateways, provides DHCP relay helper addresses, serves as STP Primary Root for Group 2 VLANs, and participates in core routing via a routed point-to-point uplink to R1.

## Device Metadata
- **Device Name:** `SW-D2`
- **Hardware Platform:** Cisco Catalyst 3560-24PS (Multilayer Switch)
- **SVIs & HSRP Roles:**
  - VLAN 10 (ICU): `172.16.7.131/26` (VIP `172.16.7.129` - Standby, Priority 100 Preempt)
  - VLAN 20 (Surgery): `172.16.7.67/26` (VIP `172.16.7.65` - Active, Priority 110 Preempt)
  - VLAN 30 (Admin): `172.16.4.3/23` (VIP `172.16.4.1` - Standby, Priority 100 Preempt)
  - VLAN 40 (Guest): `172.16.0.3/22` (VIP `172.16.0.1` - Active, Priority 110 Preempt)
  - VLAN 50 (Servers): `172.16.7.3/26` (VIP `172.16.7.1` - Standby, Priority 100 Preempt)
  - VLAN 60 (Voice): `172.16.6.3/25` (VIP `172.16.6.1` - Active, Priority 110 Preempt)
  - VLAN 99 (Mgmt): `172.16.7.195/27` (VIP `172.16.7.193` - Standby, Priority 100 Preempt)
- **STP Role:** Rapid PVST+ Primary Root for VLANs 20, 40, 60; Secondary Root for VLANs 10, 30, 50, 99
- **Uplink:** `GigabitEthernet0/2` (Routed point-to-point to R1 Gig0/1, `172.16.8.93/30`)
- **Inter-Distribution:** `FastEthernet0/23 - 24` (Port-Channel 1 EtherChannel to SW-D1)
- **Loopback 0:** `172.16.8.107/32` (OSPF Router-ID)

## File Naming Rules
- Complete production configuration: `SW-D2.cfg` (copy-paste ready into Packet Tracer CLI).
- Exact text mirror: `SW-D2.txt`.
