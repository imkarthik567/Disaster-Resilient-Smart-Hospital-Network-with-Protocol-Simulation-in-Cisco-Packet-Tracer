# `configs/SW-A1` - Main Hospital ICU Access Switch

## Purpose
Contains the complete Cisco IOS configuration for **SW-A1**, providing edge access connectivity to ICU bedside monitors, telemetry SBCs (VLAN 10), and staff IP phones (Voice VLAN 60). Enforces port security, Spanning Tree PortFast/BPDU Guard, and 802.1Q trunking to SW-D1.

## Device Metadata
- **Device Name:** `SW-A1`
- **Hardware Platform:** Cisco Catalyst 2960-24TT
- **Access VLANs:** VLAN 10 (ICU), VLAN 60 (VoIP Voice)
- **Management SVI:** VLAN 99 (172.16.4.34/27, Default Gateway: 172.16.4.33)
- **Trunk Uplink:** `Fa0/24` -> SW-D1 Fa0/1 (Native VLAN 999)

## File Naming Rules
- Complete running configuration: `SW-A1.txt` or `SW-A1.ios`.
- Verification outputs: `SW-A1_<command>.<ext>`.
