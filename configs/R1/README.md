# `configs/R1` - Main Hospital Core Router

## Purpose
Contains the complete Cisco IOS configuration for **R1**, the Core Backbone Router for the Main Hospital Campus. R1 anchors OSPF Area 0, maintains standby EIGRP failover, acts as the Internet NAT/PAT edge gateway, and enforces egress QoS queuing across WAN serial links.

## Device Metadata
- **Device Name:** `R1`
- **Hardware Platform:** Cisco 2911 ISR with HWIC-2T Serial Module in Slot 0
- **Routing Roles:** OSPF Process 1 (Area 0 Backbone), EIGRP AS 100 (Internal AD tuned to 120)
- **Primary Uplink:** `Serial0/0/0` (DCE, 172.16.4.193/30) -> R2 Se0/0/0
- **Standby Uplink:** `Serial0/0/1` (DCE, 172.16.4.197/30) -> R2 Se0/0/1
- **Distribution Links:** `Gig0/0` (to SW-D1, 172.16.5.0/30), `Gig0/1` (to SW-D2, 172.16.5.4/30)
- **Internet Edge:** `Gig0/2` (to EDGE-ISP, 203.0.113.2/30)

## File Naming Rules
- Complete running configuration: `R1.txt` or `R1.ios`.
- Module snippets / verification outputs: `R1_<section>.<ext>` (e.g., `R1_show_ip_route.txt`).
