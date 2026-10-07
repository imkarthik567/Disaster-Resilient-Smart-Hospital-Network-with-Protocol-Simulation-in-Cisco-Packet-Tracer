# Disaster-Resilient Smart Hospital Network with Protocol Simulation

**Course:** Computer Networks — VIT Vellore, SCOPE  
**Team Members:**  
- Rohit Kathiravan (`24BCE0441`) — B.Tech CSE  
- Karthikeyan S (`24BCT0332`) — B.Tech CSE  

---

## 1. Project Overview

A high-availability, multi-site enterprise healthcare network implemented in **Cisco Packet Tracer 8.x**, combining three-tier hierarchical switching, multi-area OSPF routing with standby EIGRP WAN failover, Access Control List zone quarantine, Quality of Service traffic prioritisation, and embedded Python-scripted data-link layer protocol simulations on Packet Tracer Single Board Computers (SBC-PT).

---

## 2. Repository Layout

```
CN_PROJECT/
├── README.md                       # Master repository overview and quickstart guide
├── CHANGELOG.md                    # Release history and audit log
├── requirements.txt                # Python host-side dependencies
├── tasks.py                        # Cross-platform CLI task runner (addressing, lint, bench, etc.)
├── Makefile                        # Make targets wrapper
├── .gitignore                      # Python, IDE, and Packet Tracer temp filters
│
├── docs/                           # Architectural notes, reports, and manuals
│   ├── README.md                   # Docs folder conventions & subdirectories
│   ├── addressing_plan.md          # Complete VLSM addressing specification
│   ├── design_notes.md             # Routing protocol AD tuning & PT caveats
│   ├── simulation_guide.md         # Simulation Mode PDU analysis lab manual
│   ├── server_setup.md             # Central PT Server DNS, HTTP, DHCP setup
│   ├── vlsm_allocations.json       # JSON metadata
│   └── vlsm_report.txt             # Plain text VLSM report
│
├── addressing/                     # VLSM engine & generated tables
│   ├── README.md                   # Purpose and naming rules
│   ├── vlsm_calculator.py          # Algorithmic subnet allocation engine
│   ├── addressing_table.csv        # Exportable CSV addressing table
│   ├── addressing_table.md         # Exportable Markdown addressing table
│   └── vlsm_allocations.json       # Subnet metadata
│
├── topology/                       # Topology builders & interconnect schematics
│   ├── README.md                   # Purpose and naming rules
│   ├── cabling_table.md            # Comprehensive physical and logical cabling table
│   ├── topology_diagram.puml       # PlantUML network topology source
│   └── pt_builder.py               # Hardware inventory and port schedule builder
│
├── configs/                        # Copy-paste ready Cisco IOS device configurations
│   ├── README.md                   # Config standards, verification commands, & rules
│   ├── R1/                         # Main Hospital Core Router (Cisco 2911)
│   ├── R2/                         # Remote Clinic Core Router / ABR (Cisco 2911)
│   ├── SW-D1/                      # Main Hospital Distro 1 (Catalyst 3560 L3)
│   ├── SW-D2/                      # Main Hospital Distro 2 (Catalyst 3560 L3)
│   ├── SW-D3/                      # Remote Clinic Distro (Catalyst 3560 L3)
│   ├── SW-A1/                      # ICU Access Switch (Catalyst 2960)
│   ├── SW-A2/                      # Surgery Access Switch (Catalyst 2960)
│   ├── SW-A3/                      # Admin Access Switch (Catalyst 2960)
│   ├── SW-A4/                      # Guest Wi-Fi Access Switch (Catalyst 2960)
│   ├── SW-A5/                      # Remote Clinic Access Switch (Catalyst 2960)
│   └── edge-isp/                   # Upstream Simulated ISP Router (Cisco 2911)
│
├── sbc/                            # Embedded Python scripts running on SBC-PT devices
│   ├── README.md                   # Purpose, PT execution steps, and rules
│   ├── parity_2d.py                # 2-D parity error detection & geometric bit correction
│   ├── checksum.py                 # RFC 1071 16-bit Internet checksum algorithm
│   ├── go_back_n.py                # Go-Back-N sliding window flow control simulation
│   └── selective_repeat.py         # Selective Repeat sliding window protocol & benchmark
│
├── sim/                            # Host-side simulation and benchmarking suite
│   ├── README.md                   # Purpose and rules
│   ├── benchmark_harness.py        # Loss-sweep benchmark generator (GBN vs SR)
│   └── test_protocols.py           # Pytest unit tests for protocol algorithms
│
├── verification/                   # Testing, linters, and audit frameworks
│   ├── README.md                   # Purpose and rules
│   ├── test_matrix.md              # Formal test matrix mapping IDs to pass/fail criteria
│   ├── config_linter.py            # Static analyzer auditing configs for security/syntax
│   └── verification_checklist.md   # Step-by-step CLI verification guide
│
├── evidence/                       # Empirical verification artifacts (screenshots, logs)
│   ├── README.md                   # Strict file naming rules (<phase>_<test_id>_*)
│   └── .gitkeep
│
└── results/                        # Generated data tables and analytical charts
    ├── README.md                   # Purpose and rules
    ├── benchmark_results.csv       # GBN vs SR performance loss-sweep data
    └── protocol_comparison.png     # Publication-ready Matplotlib chart
```

---

## 3. Quick Start & Task Automation

Use the cross-platform `tasks.py` script to run key project targets:

```bash
# 1. Regenerate VLSM addressing plans and markdown/CSV tables
python tasks.py addressing

# 2. Audit all device configurations against security standards
python tasks.py lint

# 3. Run host-side GBN vs SR benchmark loss-sweep harness
python tasks.py bench

# 4. Generate topology inventory and documentation sheets
python tasks.py docs

# 5. Execute full build pipeline (all tasks sequentially)
python tasks.py all
```

---

## 4. Cisco Packet Tracer Topology Setup Summary

1. **Core Routers (R1 & R2):** Model **Cisco 2911**. Power down in Physical tab, insert **HWIC-2T** module into Slot 0, and power back on.
2. **Distribution Switches (SW-D1, SW-D2, SW-D3):** Model **Catalyst 3560-24PS**.
3. **Access Switches (SW-A1 to SW-A5):** Model **Catalyst 2960-24TT**.
4. **Primary WAN Cable:** Serial DCE from R1 `Se0/0/0` (DCE) to R2 `Se0/0/0` (DTE).
5. **Standby WAN Cable:** Serial DCE from R1 `Se0/0/1` (DCE) to R2 `Se0/0/1` (DTE).
6. **Configurations:** Paste the corresponding `.txt` file from `/configs/<device>/` into each device's CLI.
