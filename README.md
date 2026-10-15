# Disaster-Resilient Smart Hospital Network with Protocol Simulation

[![Tests: 29/29 Passing](https://img.shields.io/badge/Tests-29%2F29%20Passing-brightgreen.svg)](tests/)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](requirements.txt)
[![Cisco Packet Tracer: 8.x](https://img.shields.io/badge/Cisco%20Packet%20Tracer-8.x-orange.svg)](topology/)
[![License: Academic](https://img.shields.io/badge/License-MIT%2FAcademic-purple.svg)](LICENSE)

**Course:** CSE2004 — Computer Networks  
**Institution:** School of Computer Science and Engineering (SCOPE), VIT Vellore  
**Authors:**
- **Rohit Kathiravan** (`24BCE0441`) — B.Tech Computer Science and Engineering
- **Karthikeyan S** (`24BCT0332`) — B.Tech Computer Science and Engineering

**GitHub Repository:** [imkarthik567/Disaster-Resilient-Smart-Hospital-Network-with-Protocol-Simulation-in-Cisco-Packet-Tracer](https://github.com/imkarthik567/Disaster-Resilient-Smart-Hospital-Network-with-Protocol-Simulation-in-Cisco-Packet-Tracer)

---

## 1. Executive Summary

This repository hosts the complete engineering implementation, simulation models, configuration artifacts, and empirical research for a **Disaster-Resilient Smart Hospital Network**. Designed to withstand core router physical destructions, dual WAN fiber cuts, distribution gateway failures, and medical sensor telemetry packet drop bursts, the architecture couples:
1. **Three-Tier Hierarchical Campus Topology:** Redundant Cisco 2911 Core Routers, multi-layer Catalyst 3560 Distribution Switches (HSRP with sub-second timers, RSTP 802.1w), and Catalyst 2960 Access layer with Port Security and BPDU Guard.
2. **Dynamic Routing & Edge Resiliency:** Multi-Area OSPFv2 (with tuned Hello/Dead intervals), standby EIGRP WAN failover, floating static routes, and Cisco IOS NAT/PAT with medical telemetry port forwarding.
3. **Clinical SLA & QoS Traffic Engineering:** Modular QoS CLI (MQC) prioritizing life-critical telemetry (DSCP EF / 46, Expedited Forwarding, 20% reserved bandwidth) and medical imaging PACS transfers (DSCP AF31, Assured Forwarding) over guest internet traffic (Class Best Effort).
4. **Embedded SBC-PT Telemetry Protocol Stack:** Custom Python data-link layer protocols running inside Packet Tracer Single Board Computers (SBC-PT), comparing RFC 1071 Checksum, 2D Parity bit-syndrome correction, CRC-CCITT polynomial division, and sliding window Go-Back-N vs. Selective Repeat ARQ.
5. **NetworkX Digital Twin & Chaos Simulation:** An algorithmic graph model proving edge-disjoint path redundancy across all 55 physical links, calculating an overall network resilience score of **96.88%** under single-element failure modes.
6. **NetDevOps Infrastructure as Code (IaC):** Single Source of Truth (YAML SSOT) with a Jinja2 template compilation pipeline generating validated Cisco IOS configurations.
7. **IPv6 Dual-Stack Next-Generation Extension:** Full dual-stack deployment across the hospital core, distribution, and server farm running OSPFv3 and EUI-64 addressing.

---

## 2. Master Deliverables Directory

| Deliverable ID | Component Name | Primary Path | Description |
| :--- | :--- | :--- | :--- |
| **D1** | **Network Design Document** | [`docs/network_design_document.docx`](docs/network_design_document.docx)<br>[`docs/network_design_document.md`](docs/network_design_document.md) | 240 KB IEEE-style engineering document covering VLSM, topology, routing, security, QoS, and failure modes. |
| **D2** | **Simulation Analysis Report** | [`docs/simulation_report.md`](docs/simulation_report.md) | Empirical analysis of error detection, ARQ throughput, QoS delay, OSPF convergence, and ACL enforcement. |
| **D3** | **Packet Tracer Network Model** | [`topology/`](topology/)<br>[`configs/`](configs/) | Complete device inventories, cabling schedules, and copy-paste ready Cisco IOS configurations. |
| **D4** | **SBC Medical Protocol Stack** | [`sbc/`](sbc/)<br>[`sim/`](sim/) | Python sensor telemetry apps, 2D parity, CRC-16, RFC 1071 checksum, GBN, and Selective Repeat engines. |
| **D5** | **Review Slides & Viva Guide** | [`docs/review_slides.md`](docs/review_slides.md)<br>[`docs/viva_questions.md`](docs/viva_questions.md) | 14-slide presentation deck with ~100-word speaker notes, plus 65 viva questions with worked mathematical proofs. |
| **D6** | **Traceability Matrix** | [`docs/traceability_matrix.csv`](docs/traceability_matrix.csv)<br>[`docs/traceability_matrix.md`](docs/traceability_matrix.md) | Bi-directional traceability linking all 88 atomic proposal requirements to configs, tests, and evidence. |
| **D7** | **Digital Twin & Chaos Sim** | [`sim/digital_twin.py`](sim/digital_twin.py)<br>[`docs/resilience_report.md`](docs/resilience_report.md) | NetworkX graph model with 10,000 Monte Carlo failure runs and resilience heatmap visualization. |
| **D8** | **Failover Convergence Pipeline** | [`sim/convergence_analysis.py`](sim/convergence_analysis.py)<br>[`sim/parse_ping.py`](sim/parse_ping.py) | Multi-trial 95% CI statistical analysis, raw ping terminal parser, and error-bar convergence charts. |
| **D9** | **NetDevOps & IPv6 Extensions**| [`automation/`](automation/)<br>[`configs/ipv6_dual_stack/`](configs/ipv6_dual_stack/) | YAML SSOT Jinja2 configuration compiler and complete IPv6 dual-stack OSPFv3 architecture. |

---

## 3. Repository Architecture

```
CN_PROJECT/
├── README.md                       # Master documentation & showcase
├── CHANGELOG.md                    # Project development & release history
├── requirements.txt                # Python host-side dependencies
├── tasks.py                        # Cross-platform CLI task runner (29 test suites)
├── Makefile                        # POSIX wrapper for task automation
│
├── addressing/                     # VLSM engine & generated allocation tables
│   ├── vlsm_calculator.py          # Algorithmic subnet allocation engine
│   ├── addressing_table.csv        # Subnet allocation table (CSV)
│   ├── addressing_table.md         # Subnet allocation table (Markdown)
│   └── vlsm_allocations.json       # JSON metadata
│
├── automation/                     # NetDevOps Infrastructure-as-Code pipeline
│   ├── network_source_of_truth.yaml# Single Source of Truth (SSOT) data model
│   ├── generate_configs.py         # Jinja2 template rendering engine
│   └── templates/                  # Modular Cisco IOS Jinja2 templates
│
├── configs/                        # Production Cisco IOS device configurations
│   ├── R1/                         # Main Hospital Core Router (Cisco 2911)
│   ├── R2/                         # Remote Clinic Core Router / ABR (Cisco 2911)
│   ├── SW-D1/                      # Main Hospital Distribution 1 (Catalyst 3560)
│   ├── SW-D2/                      # Main Hospital Distribution 2 (Catalyst 3560)
│   ├── SW-D3/                      # Remote Clinic Distribution (Catalyst 3560)
│   ├── SW-A1/ to SW-A5/            # Clinical & Administrative Access Switches (Catalyst 2960)
│   ├── edge-isp/                   # Simulated Edge ISP Gateway Router
│   └── ipv6_dual_stack/            # IPv6 Dual-Stack OSPFv3 Configurations
│
├── docs/                           # Formal engineering reports and documentation
│   ├── network_design_document.docx# Complete IEEE-style Network Design Document
│   ├── network_design_document.md  # Source Markdown Network Design Document
│   ├── simulation_report.md        # Comprehensive Simulation Analysis Report
│   ├── review_slides.md            # 14-Slide Review Presentation Deck
│   ├── viva_questions.md           # 65 Comprehensive Viva Questions with Worked Math
│   ├── pdu_analysis_guide.md       # Step-by-Step Simulation Mode PDU Capture Plan
│   ├── tcp_vs_udp_study.md         # Transport-Layer Comparison & Design Justification
│   ├── resilience_report.md        # Digital Twin Chaos Testing Analysis & SLA Proof
│   ├── convergence_findings.md     # Multi-Trial Convergence Statistics & CI Report
│   ├── advanced_extensions_prioritization.md # Evaluation of High-Value Extensions
│   ├── gap_audit.md                # Deliverable Completeness Audit & Pre-Submission Checklist
│   └── traceability_matrix.csv     # 88-Item Bi-Directional Requirements Traceability Matrix
│
├── results/                        # Publication-quality charts & empirical datasets
│   ├── benchmark_results.csv       # GBN vs SR loss-sweep raw data
│   └── charts/                     # High-resolution PNG and vector PDF charts
│       ├── failover_multi_trial_comparison.png # 95% CI error bar failover comparison
│       ├── failover_theoretical_vs_observed.png# Theoretical vs observed convergence
│       ├── failover_cumulative_loss.png        # Cumulative packet loss curves
│       ├── resilience_heatmap.png              # NetworkX chaos failure heatmap
│       ├── arq_throughput_vs_loss.png          # GBN vs Selective Repeat throughput
│       └── error_detection_coverage.png        # Parity vs Checksum vs CRC-16
│
├── sbc/                            # Single Board Computer (SBC-PT) Python stack
│   ├── medical_sensor_app.py       # Patient telemetry sensor application
│   ├── parity_2d.py                # 2D parity matrix & bit-syndrome correction
│   ├── checksum.py                 # RFC 1071 16-bit Internet checksum
│   ├── go_back_n.py                # Go-Back-N sliding window ARQ
│   └── selective_repeat.py         # Selective Repeat sliding window ARQ
│
├── sim/                            # Host-side benchmarking & digital twin engines
│   ├── digital_twin.py             # NetworkX topology chaos testing engine
│   ├── convergence_analysis.py     # Multi-trial statistical convergence processor
│   ├── parse_ping.py               # Universal CLI ping log parser & outage estimator
│   ├── run_benchmarks.py           # Protocol throughput & frame error rate sweep
│   └── sample_failover_trials.csv  # 110-trial benchmark dataset (tagged SAMPLE)
│
├── tests/                          # 29 Automated unit and integration test suites
│   ├── test_vlsm.py                # Subnet boundary and host capacity tests
│   ├── test_topology.py            # Physical cabling and port schedule tests
│   ├── test_intervlan_hsrp.py      # Gateway redundancy and virtual IP tests
│   ├── test_security_acls.py       # ACL quarantine and perimeter enforcement tests
│   ├── test_qos_design.py          # MQC QoS queue and DSCP marking tests
│   ├── test_digital_twin.py        # Chaos failure simulation tests
│   ├── test_convergence_analysis.py# Multi-trial statistical estimator tests
│   └── ... (29 test suites total)
│
└── verification/                   # Static analyzers, linters, and verification matrices
    ├── config_linter.py            # Basic syntax and credential safety linter
    ├── lint_configs.py             # CiscoConfParse deep policy verification auditor
    └── test_matrix.md              # 50-test formal test plan
```

---

## 4. Quick Start & Execution

### 4.1 Prerequisites
- Python 3.10+
- Dependencies: `pip install -r requirements.txt` (`networkx`, `ciscoconfparse`, `jinja2`, `pyyaml`, `matplotlib`, `pytest`, `python-docx`)

### 4.2 Automated Build & Test Tasks
The repository includes a centralized task runner [`tasks.py`](tasks.py):

```bash
# Run all 29 automated test suites (100% pass required)
python tasks.py test

# Recompile all configurations from YAML SSOT via Jinja2
python tasks.py docs

# Run static configuration linter & policy auditor
python tasks.py lint

# Run protocol throughput loss-sweep benchmark
python tasks.py bench

# Generate all high-resolution publication charts
python tasks.py charts

# Execute entire end-to-end build and validation pipeline
python tasks.py all
```

---

## 5. Failover Analysis & Convergence Processing

The repository includes a dedicated CLI utility [`sim/parse_ping.py`](sim/parse_ping.py) to parse terminal outputs from Cisco Packet Tracer and Cisco IOS ping sessions:

```bash
# Ingest raw ping output inline and compute SLA compliance
python sim/parse_ping.py --text "Reply from 172.16.5.10: bytes=32 time=3ms TTL=126
Reply from 172.16.5.10: bytes=32 time=4ms TTL=126
Request timed out.
Request timed out.
Reply from 172.16.5.10: bytes=32 time=3ms TTL=126" --scenario "SC-01 Primary WAN Cut" --config "Tuned Fast OSPF"
```

To run multi-trial statistical convergence processing across all 6 disaster failure scenarios with 95% Confidence Intervals:
```bash
python sim/convergence_analysis.py --trials sim/sample_failover_trials.csv
```

---

## 6. Digital Twin Resilience & Chaos Results

Using NetworkX ([`sim/digital_twin.py`](sim/digital_twin.py)), every physical link and device was subjected to isolated and cascading failure injections. Key findings:
- **Single Link Failure:** **0% loss of reachability** between clinical subnets and the central server farm across all 55 physical links.
- **Resilience Score:** **96.88%** under all single-element failures.
- **Failure Boundary:** Core and Distribution layers achieve seamless failover via HSRP and RSTP. Access switches represent single points of failure for locally attached single-homed endpoints, mitigated via dual-homed NIC teaming.

---

## 7. Requirements Traceability

All 88 atomic requirements from Section 4.2 of the project proposal are tracked in [`docs/traceability_matrix.csv`](docs/traceability_matrix.csv) and [`docs/traceability_matrix.md`](docs/traceability_matrix.md). Every requirement links directly to:
1. Specific Cisco IOS configuration stanzas.
2. Automated regression tests in `tests/`.
3. Verification artifacts in `docs/` and `evidence/`.

**Status:** **100% VERIFIED (88 / 88 Requirements Met).**

---

## 8. Authors & Academic Integrity

- **Rohit Kathiravan** (`24BCE0441`), School of Computer Science and Engineering (SCOPE), VIT Vellore.
- **Karthikeyan S** (`24BCT0332`), School of Computer Science and Engineering (SCOPE), VIT Vellore.

Course: **CSE2004 — Computer Networks**, Faculty of Computer Science and Engineering, Vellore Institute of Technology, Vellore, Tamil Nadu, India.
