# `configs/SW-D1` - Main Hospital Distribution Switch 1

## Purpose
Contains the complete Cisco IOS configuration for **SW-D1**, a Multilayer Layer-3 Switch (Catalyst 3560-24PS) aggregating clinical subnets (ICU, Surgery), administrative systems, and the Central Server Farm. Provides hardware-switched inter-VLAN routing, hosts HSRP v2 active/standby gateways, provides DHCP relay helper addresses, serves as STP Primary Root for Group 1 VLANs, and participates in core routing via a routed point-to-point uplink to R1.

## Device Metadata
- **Device Name:** `SW-D1`
- **Hardware Platform:** Cisco Catalyst 3560-24PS (Multilayer Switch)
- **SVIs & HSRP Roles:**
  - VLAN 10 (ICU): `172.16.7.130/26` (VIP `172.16.7.129` - Active, Priority 110 Preempt)
  - VLAN 20 (Surgery): `172.16.7.66/26` (VIP `172.16.7.65` - Standby, Priority 100 Preempt)
  - VLAN 30 (Admin): `172.16.4.2/23` (VIP `172.16.4.1` - Active, Priority 110 Preempt)
  - VLAN 40 (Guest): `172.16.0.2/22` (VIP `172.16.0.1` - Standby, Priority 100 Preempt)
  - VLAN 50 (Servers): `172.16.7.2/26` (VIP `172.16.7.1` - Active, Priority 110 Preempt)
  - VLAN 60 (Voice): `172.16.6.2/25` (VIP `172.16.6.1` - Standby, Priority 100 Preempt)
  - VLAN 99 (Mgmt): `172.16.7.194/27` (VIP `172.16.7.193` - Active, Priority 110 Preempt)
- **STP Role:** Rapid PVST+ Primary Root for VLANs 10, 30, 50, 99; Secondary Root for VLANs 20, 40, 60
- **Uplink:** `GigabitEthernet0/2` (Routed point-to-point to R1 Gig0/0, `172.16.8.89/30`)
- **Inter-Distribution:** `FastEthernet0/23 - 24` (Port-Channel 1 EtherChannel to SW-D2)
- **Loopback 0:** `172.16.8.106/32` (OSPF Router-ID)

## File Naming Rules
- Complete production configuration: `SW-D1.cfg` (copy-paste ready into Packet Tracer CLI).
- Exact text mirror: `SW-D1.txt`.
