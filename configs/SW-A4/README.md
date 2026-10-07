# `configs/SW-A4` - Main Hospital Guest & Public Access Switch

## Purpose
Contains the complete Cisco IOS configuration for **SW-A4**, connecting untrusted Guest Wi-Fi access points and public waiting area terminals (VLAN 40) along with reception desk VoIP phones (VLAN 60). Enforces port security tuned for AP multi-client behavior, PortFast, BPDU Guard, and trunking to SW-D2.

## Device Metadata
- **Device Name:** `SW-A4`
- **Hardware Platform:** Cisco Catalyst 2960-24TT
- **Access VLANs:** VLAN 40 (Guest Wi-Fi), VLAN 60 (VoIP Voice)
- **Management SVI:** VLAN 99 (172.16.4.37/27, Default Gateway: 172.16.4.33)
- **Trunk Uplink:** `Fa0/24` -> SW-D2 Fa0/3 (Native VLAN 999)

## File Naming Rules
- Complete running configuration: `SW-A4.txt` or `SW-A4.ios`.
- Verification outputs: `SW-A4_<command>.<ext>`.
