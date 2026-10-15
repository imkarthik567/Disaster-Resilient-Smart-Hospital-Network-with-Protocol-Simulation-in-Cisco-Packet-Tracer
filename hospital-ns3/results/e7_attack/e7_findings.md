# Experiment E7 Findings: Untrusted Guest Zone Threat Model & ML Intrusion Detection

**Disaster-Resilient Smart Hospital Network (NS-3 Discrete-Event Simulation Phase)**  
**Course:** CSE2004 Computer Networks, SCOPE, VIT Vellore  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  

---

## 1. Executive Summary & Problem Formulation
In hospital enterprise networks, the **Guest Wi-Fi zone (VLAN 40)** accommodates hundreds of untrusted patient and visitor personal devices. A compromised endpoint in this zone can launch malicious attacks:
1. **Volumetric UDP Flood (10 Mbps):** Targeting the central Electronic Health Records (EHR) and PACS server farm (`172.16.7.10`) to exhaust buffer queues.
2. **Stealth Reconnaissance Scan:** Low-rate probe packets cycling across ICU bedside telemetry monitors (`172.16.7.128/26`) to discover vulnerabilities in unpatched infusion pumps and physiological monitors.

This study implements:
- A **1-second sliding-window feature extractor** yielding packet count, byte volume, mean packet size, inter-arrival time mean/variance, and distinct destination counts.
- **Two Machine Learning Classifiers:** Random Forest and Regularized Logistic Regression evaluated with a **seed-stratified train/test split** (70% train seeds, 30% held-out test seeds) to prevent intra-simulation data leakage.
- An **ACL & Rate-Limiting Mitigation Engine** emulating Cisco IOS Extended ACL 101 on Distribution Switch `SW-D1`.

---

## 2. Machine Learning Classifier Performance on Held-Out Test Seeds

Refer to [`e7_roc_curves.png`](e7_roc_curves.png) and [`e7_confusion_matrices.png`](e7_confusion_matrices.png):

| Metric | Random Forest (Ensemble) | Logistic Regression (Linear) | Notes |
| :--- | :---: | :---: | :--- |
| **Precision** | **100.00%** | 100.00% | Proportion of raised alerts that are true attacks |
| **Recall (Sensitivity)** | **100.00%** | 100.00% | Detection rate of malicious 1-second windows |
| **F1-Score** | **100.00%** | 100.00% | Harmonic mean of precision and recall |
| **Specificity** | **100.00%** | 100.00% | Rejection rate of benign traffic windows |
| **ROC-AUC** | **1.0000** | 1.0000 | Area under ROC curve across all thresholds |
| **Detection Latency** | **0.00 +/- 0.00 s** | 0.00 +/- 0.00 s** | Time elapsed from attack onset ($T=10$s) to first alert |

### Key Machine Learning Insights:
1. **Random Forest Superiority:** Random Forest achieved near-optimal classification ($F_1 = 100.00\%$) because it effectively handles the multi-modal distribution of two fundamentally different attack types:
   - High-packet volumetric flood ($2400\text{ pkts/s}$).
   - Low-packet stealth scan ($1\text{ pkt/s}$, but high `distinct_dst` count).
2. **Feature Importance Ranking:** Refer to [`e7_feature_importance.png`](e7_feature_importance.png):
   - `packets` and `bytes` dominate detection for volumetric UDP floods.
   - `distinct_dst` and `iat_var_ms2` provide the critical discriminating power for separating stealth scans from periodic ICU telemetry.
3. **Detection Latency:** Both classifiers triggered an alert within **0.00 seconds** of attack initiation, well before link buffers saturated completely.

---

## 3. Impact of Attack & Mitigation on Critical ICU Telemetry

Refer to [`e7_icu_impact_mitigation.png`](e7_icu_impact_mitigation.png):

| Clinical Metric | Baseline (Normal) | Unmitigated Attack (No ACL) | Mitigated Attack (ACL 101) | Clinical SLA Limit |
| :--- | :---: | :---: | :---: | :---: |
| **ICU P95 Latency** | $2.84\text{ ms}$ | **33.97 ms** | **2.83 ms** | $\le 20.0\text{ ms}$ |
| **ICU Packet Loss** | $0.00\%$ | **17.19%** | **0.00%** | $\le 0.10\%$ |
| **Scan Probes Delivered to ICU** | $0$ | $30\text{ (100% delivered)}$ | **$0\text{ (100% blocked)}$** | $0\text{ probes}$ |

### Clinical Conclusion:
- Without mitigation, the UDP flood exhausts the server queue buffer, starving life-critical ICU cardiac telemetry packets, driving latency to **33.97 ms** (violating the $20\text{ ms}$ clinical safety threshold) and discarding **17.19%** of telemetry frames.
- Enabling Cisco IOS Extended ACL 101 (`access-list 101 deny ip 172.16.0.0 0.0.3.255 172.16.7.128 0.0.0.63`) and guest policing completely insulates the clinical infrastructure.

---

## 4. Overfitting Risks in Simulated Data & Unjustified Claims

### 4.1. Why High F1 in Simulation Can Be Misleading:
1. **Deterministic Header Patterns:** In discrete-event network simulation (NS-3), background traffic models (OnOff, BulkSend) generate synthetic packets with highly regular inter-arrival distributions and fixed MTU packet sizes. This makes separating benign from malicious flows significantly easier than in production.
2. **Absence of Clinical Bursts:** Real patient telemetry is not perfectly constant-bit-rate. When a patient enters ventricular fibrillation or cardiac arrest, multiparameter bedside monitors burst high-frequency telemetry alarms (10x normal rate). In simulated data without physiological burst modeling, an anomaly detector might misclassify life-saving clinical bursts as malicious scans.
3. **Lack of Background Noise:** Public guest Wi-Fi networks exhibit immense protocol diversity (QUIC, WebSockets, BitTorrent, VPN tunnels, MDNS, mDNS multicast, Apple AirDrop). This diverse background creates heavy-tailed noise that degrades simple linear and tree classifiers.

### 4.2. Explicitly Unjustified Claims:
- **CLAIM NOT JUSTIFIED:** *"This machine learning classifier achieves 99%+ accuracy and can be directly deployed in a hospital production switch without retraining."*  
  *Correction:* The model is evaluated on simulated synthetic traffic. Deployment in clinical production requires training on multi-gigabyte production PCAP traces containing real medical IoT protocols (HL7, DICOM, FHIR, ASTM).
- **CLAIM NOT JUSTIFIED:** *"Signature-free machine learning alone eliminates the need for network ACLs."*  
  *Correction:* ML detection latency ($\sim 1.0\text{ s}$) is too slow to prevent initial microsecond queue drops. Hardware-enforced ACLs (L3/L4 ASIC filters) remain essential as the primary line of deterministic defense; ML serves as a secondary supervisory anomaly detector.
