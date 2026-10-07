# `configs/SW-D3` - Remote Clinic Distribution Switch

## Purpose
Contains the complete Cisco IOS configuration for **SW-D3**, a Multilayer Layer-3 Switch aggregating all access subnets at the Remote Clinic. Handles inter-VLAN routing for clinical, admin, cache server, and voice zones, and advertises them into OSPF Area 1.

## Device Metadata
- **Device Name:** `SW-D3`
- **Hardware Platform:** Cisco Catalyst 3560-24PS (Multilayer Switch)
- **SVIs Hosted:** VLAN 10 (172.16.4.65/27), VLAN 30 (172.16.4.97/27), VLAN 50 (172.16.4.161/28), VLAN 60 (172.16.4.129/27), VLAN 99 (172.16.4.177/28)
- **Routing Role:** OSPF Process 1 (Area 1 - Remote Clinic Campus)
- **Uplink:** `Gig0/1` (Routed point-to-point to R2 Gig0/0, 172.16.5.8/30)
- **Downlink:** `Fa0/1` (802.1Q Trunk to SW-A5 Fa0/24)

## File Naming Rules
- Complete running configuration: `SW-D3.txt` or `SW-D3.ios`.
- Snippets / outputs: `SW-D3_<section>.<ext>`.
