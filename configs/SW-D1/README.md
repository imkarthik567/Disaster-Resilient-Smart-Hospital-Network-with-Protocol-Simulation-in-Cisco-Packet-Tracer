# `configs/SW-D1` - Main Hospital Distribution Switch 1

## Purpose
Contains the complete Cisco IOS configuration for **SW-D1**, a Multilayer Layer-3 Switch aggregating clinical subnets (ICU, Surgery) and the Central Server Farm. Provides hardware-switched inter-VLAN routing, hosts DHCP relay helper addresses, serves as STP Primary Root for critical clinical VLANs, and participates in OSPF Area 0.

## Device Metadata
- **Device Name:** `SW-D1`
- **Hardware Platform:** Cisco Catalyst 3560-24PS (Multilayer Switch)
- **SVIs Hosted:** VLAN 10 (172.16.3.129/26), VLAN 20 (172.16.3.193/26), VLAN 50 (172.16.4.1/27), VLAN 99 (172.16.4.33/27)
- **STP Role:** Primary Root for VLANs 10, 20, 50, 99; Secondary Root for VLANs 30, 40, 60
- **Uplink:** `Gig0/2` (Routed point-to-point to R1 Gig0/0, 172.16.5.0/30)
- **Inter-Distribution:** `Gig0/1` (802.1Q Trunk to SW-D2 Gi0/1)

## File Naming Rules
- Complete running configuration: `SW-D1.txt` or `SW-D1.ios`.
- Snippets / outputs: `SW-D1_<section>.<ext>`.
