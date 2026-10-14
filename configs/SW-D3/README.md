# `configs/SW-D3` - Remote Clinic Distribution Switch

## Purpose
Contains the complete Cisco IOS configuration for **SW-D3**, a Multilayer Layer-3 Switch (Catalyst 3560-24PS) aggregating all remote spoke clinic subnets (clinical, administration, guest Wi-Fi, VoIP, and management). Provides local hardware inter-VLAN routing, WAN DHCP relay to the central hospital server, serves as STP Primary Root for all clinic VLANs, and connects to Clinic Core Router R2 via a routed point-to-point uplink.

## Device Metadata
- **Device Name:** `SW-D3`
- **Hardware Platform:** Cisco Catalyst 3560-24PS (Multilayer Switch)
- **SVIs Hosted (Single Chassis Gateways):**
  - VLAN 10 (Clinical): `172.16.8.33/27` (Local Gateway for Clinic Clinical & EHR Cache)
  - VLAN 30 (Admin): `172.16.8.1/27` (Local Gateway for Clinic Admissions & Pharmacy)
  - VLAN 40 (Guest): `172.16.6.129/25` (Local Gateway for Clinic Visitor Wi-Fi)
  - VLAN 60 (Voice): `172.16.7.225/27` (Local Gateway for Clinic IP Phones)
  - VLAN 99 (Mgmt): `172.16.8.65/28` (Local Gateway for Switch Management)
- **STP Role:** Rapid PVST+ Primary Root for VLANs 10, 30, 40, 60, 99
- **Uplink:** `GigabitEthernet0/1` (Routed point-to-point to R2 Gig0/0, `172.16.8.97/30`)
- **Downlinks:** `FastEthernet0/23` (Primary Trunk) & `FastEthernet0/24` (Standby Trunk) to `SW-A5`
- **Loopback 0:** `172.16.8.108/32` (OSPF Router-ID)

## Single Point of Failure (SPOF) Note & SW-D4 Extension
SW-D3 is a single-chassis distribution gateway. For high-availability branch deployments requiring dual-chassis HSRP redundancy, refer to `SW-D3_ha_extension.cfg` and the companion switch `/configs/SW-D4/SW-D4.cfg`.

## File Naming Rules
- Complete production configuration: `SW-D3.cfg` (copy-paste ready into Packet Tracer CLI).
- Exact text mirror: `SW-D3.txt`.
- HA Extension pairing configuration: `SW-D3_ha_extension.cfg`.
