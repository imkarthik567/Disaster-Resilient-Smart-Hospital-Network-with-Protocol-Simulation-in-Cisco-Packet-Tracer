# Changelog

All notable changes to the **Disaster-Resilient Smart Hospital Network** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to Semantic Versioning.

---

## [1.2.0] - 2026-10-14

### Added
- **Phase 3.2: Inter-VLAN Routing & Gateway Redundancy Architecture:**
  - Configured hardware `ip routing` and Switch Virtual Interfaces (SVIs) on `SW-D1`, `SW-D2`, `SW-D3`, and `SW-D4`.
  - Implemented **HSRP Version 2** (`standby version 2`) across Main Hospital distribution pair (`SW-D1` / `SW-D2`) with VIP `.1` across all enterprise VLANs.
  - Implemented **Deterministic Fate-Sharing**: Aligned HSRP Active role with Rapid PVST+ Primary Root (Group 1: VLANs 10, 30, 50, 99 on `SW-D1`; Group 2: VLANs 20, 40, 60 on `SW-D2`), eliminating sub-optimal inter-switch cross-link traversal.
  - Configured intelligent uplink interface tracking on active gateways (`standby <vlan> track GigabitEthernet0/2 20`), ensuring dynamic priority decrement from `110` to `90` upon core transit link failure, triggering immediate preemption by the standby node (`priority 100`).
  - Added centralized DHCP relay (`ip helper-address 172.16.7.4`) across all client SVIs pointing to `SRV-CENTRAL` on VLAN 50.
  - Configured routed point-to-point `/30` uplinks to Core Routers (`SW-D1` Gi0/2 -> R1, `SW-D2` Gi0/2 -> R1, `SW-D3` Gi0/1 -> R2) with static default routes.
  - Conducted honest Single Point of Failure (SPOF) critique of `SW-D3` single-chassis clinic design and engineered the optional `SW-D4` dual-chassis High-Availability branch extension (`configs/SW-D4/` and `configs/SW-D3/SW-D3_ha_extension.cfg`).
  - Produced comprehensive technical architecture guide: [`docs/intervlan_hsrp_guide.md`](docs/intervlan_hsrp_guide.md) detailing fate-sharing proofs, tracking mechanics, ping matrix, and simulated failure drill protocols.
  - Added unit test suite `tests/test_intervlan_hsrp.py` hooked into `tasks.py test`, verifying 100% compliance of SVIs, HSRP v2, VIPs, tracking, and helpers.

## [1.0.0] - 2026-10-07

### Added
- **Repository Scaffold & Architecture:**
  - Initialized formal repository structure: `/docs`, `/addressing`, `/topology`, `/configs`, `/sbc`, `/sim`, `/verification`, `/evidence`, `/results`.
  - Added dedicated `README.md` documentation in every subdirectory detailing folder purpose and strict file naming rules.
  - Added Python `.gitignore` and `requirements.txt` (`matplotlib`, `numpy`, `pandas`, `ciscoconfparse`, `pytest`, `tabulate`).
  - Added multi-target task runners (`tasks.py` and `Makefile`) supporting `addressing`, `lint`, `bench`, `charts`, and `docs`.
- **Addressing Plan (`/addressing`):**
  - Algorithmic VLSM calculator engine (`vlsm_calculator.py`) allocating all subnets from `172.16.0.0/16`.
  - Automated exports: `addressing_table.csv`, `addressing_table.md`, and `vlsm_allocations.json`.
- **Topology & Interconnect (`/topology`):**
  - Physical and logical cabling specification table (`cabling_table.md`).
  - PlantUML architectural topology source (`topology_diagram.puml`).
  - Packet Tracer topology build sheet generator (`pt_builder.py`).
- **Device Configurations (`/configs`):**
  - Core Routers: `R1` (Main Hospital Core) and `R2` (Remote Clinic ABR) with multi-area OSPF, EIGRP failover (AD 120), PAT NAT, and MQC QoS.
  - Multilayer Distribution Switches: `SW-D1`, `SW-D2`, and `SW-D3` with SVIs, DHCP relay, STP roots, and `BLOCK-GUEST` ACL.
  - Access Layer Switches: `SW-A1` (ICU), `SW-A2` (Surgery), `SW-A3` (Admin), `SW-A4` (Guest), and `SW-A5` (Clinic) with port security, voice VLAN, and native VLAN 999.
  - Internet Edge: `EDGE-ISP` simulating public Internet gateway with loopback DNS servers.
- **Embedded SBC Scripts (`/sbc`):**
  - `parity_2d.py`: 2-D parity error detection and single-bit geometric correction.
  - `checksum.py`: RFC 1071 16-bit one's complement Internet checksum for ICU telemetry.
  - `go_back_n.py`: Go-Back-N sliding window flow control with timeout and cumulative ACKs.
  - `selective_repeat.py`: Selective Repeat sliding window protocol with out-of-order buffering and GBN comparative benchmark.
- **Host-Side Simulation & Benchmarking (`/sim`):**
  - `benchmark_harness.py`: Automated loss rate sweep (0% to 30%) comparing GBN vs SR.
  - `test_protocols.py`: Pytest suite validating checksum, parity, and flow control logic.
  - Benchmark data export to `/results/benchmark_results.csv` and chart generation.
- **Verification & Quality Assurance (`/verification`):**
  - Comprehensive test matrix (`test_matrix.md`) mapping 13 test cases across 5 phases.
  - Cisco IOS configuration linter (`config_linter.py`) verifying password hardening, native VLAN 999, banners, and verification headers.
  - Operational verification checklist (`verification_checklist.md`).
- **Documentation (`/docs`):**
  - Detailed design notes (`design_notes.md`) covering EIGRP AD rationale and PT caveats.
  - Simulation mode analysis manual (`simulation_guide.md`) detailing step-by-step PDU envelope inspection.
  - Central Server Farm configuration manual (`server_setup.md`).
