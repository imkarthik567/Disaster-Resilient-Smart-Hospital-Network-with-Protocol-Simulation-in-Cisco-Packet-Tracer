# `configs/SW-A3` - Main Hospital Admin Access Switch

## Purpose
Contains the complete Cisco IOS configuration for **SW-A3**, connecting administrative staff workstations (VLAN 30) and hospital administrative IP phones (VLAN 60). Enforces port security, PortFast, BPDU Guard, and trunking to SW-D2.

## Device Metadata
- **Device Name:** `SW-A3`
- **Hardware Platform:** Cisco Catalyst 2960-24TT
- **Access VLANs:** VLAN 30 (Administration), VLAN 60 (VoIP Voice)
- **Management SVI:** VLAN 99 (172.16.4.36/27, Default Gateway: 172.16.4.33)
- **Trunk Uplink:** `Fa0/24` -> SW-D2 Fa0/1 (Native VLAN 999)

## File Naming Rules
- Complete running configuration: `SW-A3.txt` or `SW-A3.ios`.
- Verification outputs: `SW-A3_<command>.<ext>`.
