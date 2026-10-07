# `/configs` Directory

## 1. Purpose
This directory houses copy-paste ready Cisco IOS configuration scripts for all active network devices across the three-tier hierarchy (Core, Distribution, Access) and the Internet Edge simulator.

## 2. Device Breakdown
- `/configs/R1/`: Main Hospital Core Router (Cisco 2911) — OSPF Area 0, EIGRP AS 100 (AD 120), NAT PAT, QoS MQC.
- `/configs/R2/`: Remote Clinic Core Router / ABR (Cisco 2911) — OSPF Area 0/1, EIGRP AS 100 (AD 120).
- `/configs/SW-D1/`: Main Campus Distribution Switch 1 (Cisco 3560) — SVIs for VLAN 10, 20, 50, 99, STP Primary Root.
- `/configs/SW-D2/`: Main Campus Distribution Switch 2 (Cisco 3560) — SVIs for VLAN 30, 40, 60, STP Primary Root, `BLOCK-GUEST` ACL.
- `/configs/SW-D3/`: Remote Clinic Distribution Switch (Cisco 3560) — SVIs for Remote Clinic VLANs, OSPF Area 1.
- `/configs/SW-A1/`: Main Hospital ICU Access Switch (Cisco 2960) — VLAN 10 & Voice 60.
- `/configs/SW-A2/`: Main Hospital Surgery Access Switch (Cisco 2960) — VLAN 20 & Voice 60.
- `/configs/SW-A3/`: Main Hospital Admin Access Switch (Cisco 2960) — VLAN 30 & Voice 60.
- `/configs/SW-A4/`: Main Hospital Guest/Public Access Switch (Cisco 2960) — VLAN 40 & Voice 60.
- `/configs/SW-A5/`: Remote Clinic Access Switch (Cisco 2960) — Clinic Access & Voice.
- `/configs/edge-isp/`: Simulated Internet Service Provider Router (Cisco 2911) — Public DNS on loopbacks.

## 3. Configuration Standards (Rule 1 & Rule 2)
1. Every configuration begins with a structured comment block stating device name, model, layer, and IP interfaces.
2. Every configuration includes copy-paste ready Cisco IOS CLI commands.
3. Every configuration is terminated with exact `show` verification commands and expected outputs.
4. All commands strictly conform to Cisco Packet Tracer 8.x supported feature sets.

## 4. File Naming Rules
- Base configurations inside each device folder must be named `<device_name>.txt` or `<device_name>.ios` (e.g., `R1.txt` or `R1.ios`).
- Differential or patch configurations must use `<device_name>_<feature>.txt` (e.g., `R1_qos_patch.txt`).
