# Disaster-Resilient Smart Hospital Network: Advanced Extensions Prioritization & Implementation Plan
**Document ID:** DOC-EXTENSIONS-2026-v1.0  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  
**Institution:** School of Computer Science and Engineering (SCOPE), VIT Vellore  
**Course Code:** CSE2004 — Computer Networks  
**Target Environment:** Cisco Packet Tracer 8.x+ / NetDevOps Automation Engine  

---

## 1. Prioritized Evaluation of Five Advanced Network Extensions

To demonstrate advanced networking competency beyond the baseline curriculum, five high-value extensions were evaluated across four engineering dimensions: **Engineering Effort (Hours)**, **Academic Marks Value**, **Implementation Risks**, and **Cisco Packet Tracer Platform Support**.

| Priority Rank | Advanced Extension Name | Architecture & Scope | Effort (Hours) | Academic Marks Value | Implementation Risks | Cisco Packet Tracer Support | Selection Decision |
| :---: | :--- | :--- | :---: | :---: | :--- | :---: | :---: |
| **RANK 1** | **Python Jinja2 Infrastructure-as-Code (IaC) Pipeline** | Complete network configuration generated from a single YAML Source of Truth (SSOT) via Jinja2 templates. | ~6 hrs | **VERY HIGH (Top Marks)** | Minimal; purely deterministic template compilation. | **100% Fully Supported** (Generates standard Cisco IOS running-config). | **SELECTED & IMPLEMENTED (Extension 1)** |
| **RANK 2** | **IPv6 Dual-Stack with OSPFv3 Core Routing** | End-to-end IPv6 address plan (`2001:db8:acad::/48`), link-local addressing (`fe80::`), and OSPFv3 dynamic routing across WAN & Core. | ~8 hrs | **VERY HIGH (Top Marks)** | Syntax differences between Cisco IOS classic OSPF and OSPFv3 (`ipv6 router ospf`). | **100% Fully Supported** (Cisco 2911/1941 routers & 3560/3650 switches). | **SELECTED & IMPLEMENTED (Extension 2)** |
| **RANK 3** | **SNMPv3 & Syslog Centralized NMS Monitoring** | Encrypted SNMPv3 traps, localized syslog logging to a centralized simulated NMS server (`172.16.5.15`). | ~5 hrs | **MEDIUM-HIGH** | Packet Tracer SNMP MIB tree is severely restricted to basic v1/v2c read-only strings; limited trap simulation. | **Partial Support** (Syslog is supported; SNMPv3 auth/priv is buggy). | Deferred to Future Scope |
| **RANK 4** | **DHCP Snooping & Dynamic ARP Inspection (DAI)** | Layer 2 switch security binding table, trusted DHCP uplinks, and ARP rate limiting against poisoning. | ~4 hrs | **MEDIUM** | Packet Tracer frequently drops legitimate DHCP traffic due to internal DAI rate-limit bugs on 2960 switches. | **Partial / Buggy** (Requires constant workaround reloads in simulation). | Deferred to Future Scope |
| **RANK 5** | **Lightweight AP Wireless Guest with WPA2-Enterprise** | Cisco 3504 Wireless LAN Controller (WLC), CAPWAP tunnels, 802.1X RADIUS authentication for guest devices. | ~10 hrs | **MEDIUM** | WLC web GUI in Packet Tracer is notoriously unstable and frequently loses AP association state upon reload. | **Unstable / High Risk** (High failure risk during live viva demonstration). | Deferred to Future Scope |

---

## 2. Selection Rationale for Top Two Extensions

### Extension 1: Infrastructure-as-Code (IaC) Automation Pipeline (Rank 1)
- **Why It Matters:** Modern network engineering has shifted away from error-prone manual CLI configuration ("Box-by-Box CLI") towards automated programmatic pipelines. By establishing a single YAML file as the Single Source of Truth (SSOT), any change to IP addresses, VLAN IDs, or ACL policies automatically regenerates consistent, hardened Cisco IOS configurations for all 13 devices without human syntax errors.
- **Academic Impact:** Proves mastery of contemporary NetDevOps workflows, Python templating, and configuration management.

### Extension 2: IPv6 Dual-Stack Architecture with OSPFv3 (Rank 2)
- **Why It Matters:** The global healthcare IoT ecosystem is transitioning to IPv6 due to IPv4 address exhaustion. Medical sensor manufacturers are embedding native IPv6 stacks for direct cloud telemetry. Implementing an IPv6 dual-stack architecture (`2001:db8:acad::/48`) alongside IPv4 proves that the hospital network is future-proofed.
- **Academic Impact:** Directly addresses advanced syllabus topics: IPv6 link-local addressing (`fe80::`), stateless address autoconfiguration (SLAAC), and OSPFv3 protocol mechanics (RFC 5340).
