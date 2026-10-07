# `configs/edge-isp` - Simulated Internet Service Provider Router

## Purpose
Contains the Cisco IOS configuration for **EDGE-ISP**, simulating an external upstream Internet Service Provider gateway. Connects directly to R1's external interface (`Gig0/2`) across `203.0.113.0/30` and provides simulated public DNS resolvers (`8.8.8.8` and `1.1.1.1`) on loopback interfaces to test outbound hospital NAT overload (PAT) functionality.

## Device Metadata
- **Device Name:** `EDGE-ISP`
- **Hardware Platform:** Cisco 2911 or 1941 Router
- **Uplink to Hospital:** `GigabitEthernet0/0` (203.0.113.1/30) -> R1 Gig0/2
- **Public Resolvers:** `Loopback0` (8.8.8.8/32), `Loopback1` (1.1.1.1/32)

## File Naming Rules
- Base running configuration: `edge-isp.txt` or `edge-isp.ios`.
- Snippets / tests: `edge-isp_<test>.<ext>`.
