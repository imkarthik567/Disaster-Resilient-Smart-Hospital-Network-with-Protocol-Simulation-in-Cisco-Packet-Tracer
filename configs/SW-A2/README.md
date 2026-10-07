# `configs/SW-A2` - Main Hospital Surgery Access Switch

## Purpose
Contains the complete Cisco IOS configuration for **SW-A2**, providing access connectivity to operating theatre equipment and PACS imaging terminals (VLAN 20) with VoIP voice support (VLAN 60). Enforces port security, PortFast, BPDU Guard, and trunking to SW-D1.

## Device Metadata
- **Device Name:** `SW-A2`
- **Hardware Platform:** Cisco Catalyst 2960-24TT
- **Access VLANs:** VLAN 20 (Surgery), VLAN 60 (VoIP Voice)
- **Management SVI:** VLAN 99 (172.16.4.35/27, Default Gateway: 172.16.4.33)
- **Trunk Uplink:** `Fa0/24` -> SW-D1 Fa0/3 (Native VLAN 999)

## File Naming Rules
- Complete running configuration: `SW-A2.txt` or `SW-A2.ios`.
- Verification outputs: `SW-A2_<command>.<ext>`.
