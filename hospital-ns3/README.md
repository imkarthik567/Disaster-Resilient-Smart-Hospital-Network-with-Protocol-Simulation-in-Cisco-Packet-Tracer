# Disaster-Resilient Smart Hospital Network (NS-3 Discrete-Event Simulation)

**Course:** CSE2004 — Computer Networks  
**Institution:** SCOPE, VIT Vellore  
**Authors:**
- Rohit Kathiravan (`24BCE0441`) — B.Tech CSE
- Karthikeyan S (`24BCT0332`) — B.Tech CSE

---

## 1. Module Overview

This module provides the **NS-3 (Network Simulator 3)** discrete-event simulation counterpart to our Cisco Packet Tracer campus network design. It reproduces the two-site hospital topology (Main Hospital and Remote Clinic), primary 2 Mbps / backup 1 Mbps WAN links, and clinical traffic zones (ICU Vitals UDP, PACS Imaging TCP, Admin Web, Clinical Voice VoIP) to generate cycle-accurate FlowMonitor metrics, packet delivery ratios, and disaster failover convergence traces.

---

## 2. Directory Structure

```
hospital-ns3/
├── sim/                # C++ simulation scenarios (synced into ns-3/scratch/)
│   └── hospital_baseline.cc
├── analysis/           # Python post-processing and charting engines
│   ├── parse_flowmon.py# FlowMonitor XML parser and CSV exporter
│   └── plot_metrics.py # Matplotlib throughput, latency, and SLA chart generator
├── results/            # Simulation output data (XML traces, CSVs, PDF/PNG charts)
│   ├── exp1_baseline/
│   ├── exp2_wan_failover/
│   └── exp3_sweeps/
├── docs/               # Faculty reports and syllabus mapping
│   └── faculty_mapping.md
└── scripts/            # Automation helper scripts
    ├── setup_scratch.sh# Syncs scenarios into ns-3/scratch and builds
    ├── run_all.sh      # Runs all experiments and triggers analysis
    └── sweep_runners.sh# Runs multi-seed and TCP congestion control sweeps
```

---

## 3. Daily Commands Cheat Sheet

Run these commands inside your WSL2 Ubuntu terminal:

### 3.1. Synchronize Scenarios and Build
Whenever you create or modify a `.cc` scenario in `sim/`, run:
```bash
./scripts/setup_scratch.sh --ns3-dir ~/ns-3
```
*(If `NS3_DIR` is set in your `~/.bashrc`, you can simply run `./scripts/setup_scratch.sh`)*

### 3.2. Run a Single Scenario Manually
Navigate to your NS-3 root directory and run with custom CLI parameters:
```bash
cd ~/ns-3

# View all available CLI arguments
./ns3 run "hospital_baseline --PrintHelp"

# Run baseline simulation for 30 seconds
./ns3 run "hospital_baseline --simTime=30.0 --enableFailure=false"

# Run WAN disaster failure test with TCP CUBIC
./ns3 run "hospital_baseline --simTime=30.0 --enableFailure=true --failureTime=10.0 --recoveryTime=20.0 --tcpVariant=TcpCubic"
```

### 3.3. Execute Full Automated Suite (Experiments 1 & 2)
To run baseline operation, inject link failures, parse FlowMonitor XML, and generate charts in one command:
```bash
./scripts/run_all.sh
```

### 3.4. Execute Parametric & Multi-Seed Sweeps
To run repeatability sweeps (5 random seeds across TCP NewReno vs. TCP CUBIC):
```bash
./scripts/sweep_runners.sh
```

### 3.5. Parse FlowMonitor XML and Generate Publication Charts
```bash
# Extract flow table from XML to CSV
python3 analysis/parse_flowmon.py results/exp1_baseline/flowmon.xml -o results/exp1_baseline/flow_metrics.csv

# Generate throughput and latency vs. SLA charts
python3 analysis/plot_metrics.py results/exp1_baseline/flow_metrics.csv -o results/exp1_baseline
```

---

## 4. Smoke-Test Checklist

Before submitting or presenting to your faculty, execute this smoke-test checklist:

- [ ] **WSL & Toolchain:** `g++ --version` (>= 11), `cmake --version` (>= 3.22), `ninja --version`.
- [ ] **NS-3 Build Status:** `cd ~/ns-3 && ./ns3 build` exits with code `0`.
- [ ] **First Example Check:** `./ns3 run first` displays client transmission and server echo messages.
- [ ] **Hospital Scenario Build:** `./scripts/setup_scratch.sh` successfully links `hospital_baseline.cc` and compiles without errors.
- [ ] **FlowMonitor Output:** Executing `./scripts/run_all.sh` creates `results/exp1_baseline/flowmon.xml` (> 5 KB).
- [ ] **Metric Parser Verification:** `python3 analysis/parse_flowmon.py results/exp1_baseline/flowmon.xml` outputs a clean table showing ICU Telemetry, PACS Imaging, and Clinic Triage flows.
- [ ] **Chart Generation:** High-resolution charts `ns3_zone_throughput.png` and `ns3_latency_sla.png` exist in `results/exp1_baseline/`.
- [ ] **Git Tracking:** All scripts, analysis tools, and docs are committed to version control.
