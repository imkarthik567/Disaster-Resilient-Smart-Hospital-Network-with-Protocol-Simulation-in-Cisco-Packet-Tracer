# `configs/SW-D2` - Main Hospital Distribution Switch 2

## Purpose
Contains the complete Cisco IOS configuration for **SW-D2**, a Multilayer Layer-3 Switch aggregating administrative, guest, and VoIP traffic. Enforces the strict `BLOCK-GUEST` Extended Access Control List on SVI Vlan40, acts as STP Primary Root for VLANs 30, 40, and 60, and routes into OSPF Area 0.

## Device Metadata
- **Device Name:** `SW-D2`
- **Hardware Platform:** Cisco Catalyst 3560-24PS (Multilayer Switch)
- **SVIs Hosted:** VLAN 30 (172.16.2.1/24), VLAN 40 (172.16.0.1/23), VLAN 60 (172.16.3.1/25)
- **Security Policy:** Extended ACL `BLOCK-GUEST` applied inbound on `interface Vlan40`
- **STP Role:** Primary Root for VLANs 30, 40, 60; Secondary Root for VLANs 10, 20, 50, 99
- **Uplink:** `Gig0/2` (Routed point-to-point to R1 Gig0/1, 172.16.5.4/30)
- **Inter-Distribution:** `Gig0/1` (802.1Q Trunk to SW-D1 Gi0/1)

## File Naming Rules
- Complete running configuration: `SW-D2.txt` or `SW-D2.ios`.
- Snippets / outputs: `SW-D2_<section>.<ext>`.
