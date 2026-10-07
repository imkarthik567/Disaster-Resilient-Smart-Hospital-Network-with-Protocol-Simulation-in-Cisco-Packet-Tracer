# `configs/SW-A5` - Remote Clinic Access Switch

## Purpose
Contains the complete Cisco IOS configuration for **SW-A5**, providing unified access connectivity at the Remote Clinic for clinical patient monitors (VLAN 10), clinic administration workstations (VLAN 30), the local server cache (VLAN 50), and clinic VoIP phones (VLAN 60). Enforces port security, PortFast, and trunking to SW-D3.

## Device Metadata
- **Device Name:** `SW-A5`
- **Hardware Platform:** Cisco Catalyst 2960-24TT
- **Access VLANs:** VLAN 10 (Clinical), VLAN 30 (Admin), VLAN 50 (Server Cache), VLAN 60 (VoIP Voice)
- **Management SVI:** VLAN 99 (172.16.4.178/28, Default Gateway: 172.16.4.177)
- **Trunk Uplink:** `Fa0/24` -> SW-D3 Fa0/1 (Native VLAN 999)

## File Naming Rules
- Complete running configuration: `SW-A5.txt` or `SW-A5.ios`.
- Verification outputs: `SW-A5_<command>.<ext>`.
