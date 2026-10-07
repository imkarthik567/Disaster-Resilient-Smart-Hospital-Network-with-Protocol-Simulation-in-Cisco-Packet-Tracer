# `configs/R2` - Remote Clinic Core Router (ABR)

## Purpose
Contains the complete Cisco IOS configuration for **R2**, the Core Gateway and OSPF Area Border Router (ABR) for the Remote Clinic. R2 interconnects OSPF Area 0 (Backbone WAN) with OSPF Area 1 (Remote Clinic Campus), provides EIGRP AS 100 secondary failover, and applies WAN QoS.

## Device Metadata
- **Device Name:** `R2`
- **Hardware Platform:** Cisco 2911 ISR with HWIC-2T Serial Module in Slot 0
- **Routing Roles:** OSPF ABR (Area 0 on WAN, Area 1 on LAN), EIGRP AS 100 (Internal AD 120)
- **Primary Uplink:** `Serial0/0/0` (DTE, 172.16.4.194/30) -> R1 Se0/0/0
- **Standby Uplink:** `Serial0/0/1` (DTE, 172.16.4.198/30) -> R1 Se0/0/1
- **LAN Link:** `Gig0/0` (to SW-D3, 172.16.5.8/30 in Area 1)

## File Naming Rules
- Complete running configuration: `R2.txt` or `R2.ios`.
- Module snippets / verification outputs: `R2_<section>.<ext>`.
