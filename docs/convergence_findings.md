# Disaster-Resilient Smart Hospital Network: Failover & Convergence Findings
**Document ID:** DOC-CONVERGENCE-2026-v1.0  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  
**Target Environment:** Cisco Packet Tracer 8.x+ / Cisco IOS 15.x  
**Clinical Baseline:** Real-time Patient Telemetry Maximum Outage SLA = **3.0 seconds**  

---

## 1. Quantitative Failover Measurement Summary Table

| Scenario | Protocol Involved | Theoretical Failover (s) | Observed Failover (s) | Packet Loss (%) | Clinical Impact (3.0s Vitals SLA) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **SC-01: SW-D1 Power Off (Dist Switch Crash)** | HSRP / RSTP | 10.00 s | 11.15 s | 22.0% | **DEGRADED** |
| **SC-02: SW-D1 to R1 Uplink Severed** | OSPFv2 | 0.75 s | 0.92 s | 2.5% | **ACCEPTABLE** |
| **SC-03: Primary Serial WAN Cut** | OSPFv2 | 1.50 s | 1.74 s | 5.0% | **ACCEPTABLE** |
| **SC-04: STP Root Bridge Trunk Drop** | Rapid-PVST+ | 1.50 s | 1.85 s | 5.0% | **ACCEPTABLE** |
| **SC-05: Server Farm Uplink Cut** | RSTP (802.1w) | 0.25 s | 0.38 s | 0.0% | **ACCEPTABLE** |
| **SC-06: Remote Clinic Gateway Crash** | HSRP (HA Mode) | 10.00 s | 11.30 s | 22.0% | **DEGRADED** |

---

## 2. Convergence Visualizations

The experimental data produced two publication-grade analytical charts in `/results/charts/`:

1. **Theoretical vs. Observed Outage:** `failover_theoretical_vs_observed.png` (`.pdf`) — Grouped bar comparison with the 3.0s clinical SLA demarcated.
2. **Cumulative Packet Loss Curve:** `failover_cumulative_loss.png` (`.pdf`) — Temporal progression of packet drops illustrating recovery curves.

```
Failover Summary Chart:
[SC-01] Theo: ##########   (10.00s) | Obs: ===========  (11.15s)
[SC-02] Theo:              ( 0.75s) | Obs:              ( 0.92s)
[SC-03] Theo: #            ( 1.50s) | Obs: =            ( 1.74s)
[SC-04] Theo: #            ( 1.50s) | Obs: =            ( 1.85s)
[SC-05] Theo:              ( 0.25s) | Obs:              ( 0.38s)
[SC-06] Theo: ##########   (10.00s) | Obs: ===========  (11.30s)
```

---

## 3. Discrepancy Analysis: Theoretical vs. Observed Convergence

> [!NOTE] Analytical Evaluation of Convergence Variance
> Across all six failure scenarios, the observed convergence durations systematically exceeded theoretical mathematical baselines by an average of 0.22 to 1.30 seconds. This empirical discrepancy is attributable to three compounding networking and simulation phenomena:
>
> 1. **Packet Tracer Simulation Event Scheduling Coarseness:** Cisco Packet Tracer's discrete-event simulation engine quantizes timer decrements to internal clock ticks, introducing scheduling jitter when evaluating asynchronous protocol events (such as HSRP 3.0s multicast hellos and OSPF SPF calculations).
> 2. **Gratuitous ARP Resolution and CAM Table Flushes:** When HSRP transitions `SW-D2` from Standby to Active upon `SW-D1` failure, `SW-D2` broadcasts a Gratuitous ARP (GARP) to update Layer 2 switch CAM tables with the virtual MAC (`0000.0c07.ac0a`). Intermediate access switches experience a momentary frame drop while clearing old CAM entries and learning the newly active trunk port.
> 3. **RSTP Sync and Edge Port BPDU Interlocking:** In Root Bridge promotion scenarios, although IEEE 802.1w Rapid-PVST+ avoids legacy 30-second forward delay timers via the Proposal/Agreement mechanism, non-edge interconnect trunks still undergo a multi-hop synchronization handshake. When sampled at discrete 1000 ms ICMP echo intervals, these cumulative millisecond transit delays register as additional full-second packet loss counts.


## 4. Engineering Recommendations & Clinical Mitigations

1. **Sub-Second HSRP Timers (`msec`):** Transition HSRP configuration on distribution switches `SW-D1`/`SW-D2` from default seconds to millisecond timers (`standby 10 timers msec 250 msec 750`). In real Catalyst hardware, this drops SVI failover from 11.15s to 0.75s, bringing Scenario 1 and 6 within the 3.0-second vitals SLA.
2. **Application-Layer Frame Buffering (SBC-PT):** The host-side SBC vitals telemetry application buffers the last 15 seconds of sensor telemetry in a local FIFO ring buffer. When the network layer re-converges, the Selective Repeat (SR) transport layer transfers lost frames without dropping life-critical historical trend records.