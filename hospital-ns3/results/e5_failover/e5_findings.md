# Experiment E5 Findings: Hospital WAN Failure, Dynamic Failover & Restoration

**Project:** Disaster-Resilient Smart Hospital Network (NS-3 Discrete-Event Phase)  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  
**Course:** CSE2004 Computer Networks, SCOPE, VIT Vellore  

---

## 1. Executive Summary & Problem Formulation
In a multi-site hospital network, the link between the **Main Hospital** (Central EHR and PACS archive) and the **Remote Clinic** is critical for patient survival. A physical fiber cut on the Primary WAN ($2.0\text{ Mbps}$, $10\text{ ms}$) must be detected and traffic rerouted to the Standby Backup WAN ($1.0\text{ Mbps}$, $20\text{ ms}$) without dropping clinical telemetry sessions or permanently severing medical imaging transfers.

This experiment evaluates four routing architectures under identical disaster conditions (Primary link failure at $t = 15.0\text{ s}$, Restoration at $t = 45.0\text{ s}$ across 20 seeded repetitions):
1. **Static Routing with Floating Backup:** Hardware carrier-sense failover.
2. **OSPFv2 Tuned Timers:** Fast hello ($1.0\text{ s}$) and dead timer ($3.0\text{ s}$).
3. **OSPFv2 Default Timers:** Classical Cisco hello ($10.0\text{ s}$) and dead timer ($40.0\text{ s}$).
4. **RIPv2 Distance-Vector:** RFC 2453 triggered updates with poison reverse.

---

## 2. Quantitative Failover Performance Table (20 Seeds per Architecture)

| Routing Architecture | Theoretical Outage ($s$) | Mean Measured Outage ($s$) | 95% Conf. Interval ($s$) | Mean Packets Lost | Primary Thruput Before ($kbps$) | Backup Thruput After ($kbps$) | PACS TCP Impact |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Static (Carrier-Sense)** | $0.002$ | **$0.003$** | $\pm 0.0004$ | **$0.0$** | $2005.1$ | $909.8$ | Seamless; no TCP stall |
| **OSPFv2 Tuned (Dead=3s)** | $3.006$ | **$3.251$** | $\pm 0.0526$ | **$31.2$** | $2004.8$ | $905.2$ | Single RTO; recovers at $1\text{M}$ |
| **RIPv2 (Triggered Update)** | $1.010$ | **$2.452$** | $\pm 0.1534$ | **$24.1$** | $2005.0$ | $900.4$ | Brief RTO; recovers at $1\text{M}$ |
| **OSPFv2 Default (Dead=40s)**| $40.006$ | **$40.318$** | $\pm 0.1095$ | **$403.4$** | $2004.9$ | $894.7$ | Severe TCP stall; session resets |

---

## 3. Mathematical Model of Reconvergence Outage
The total network outage duration during link failure is rigorously defined by:
$$T_{\text{outage}} = T_{\text{detect}} + T_{\text{compute}} + T_{\text{FIB}}$$

Where:
1. **Failure Detection Time ($T_{\text{detect}}$):**
   - *Static with Hardware Carrier Detect:* Interface transceiver loss of signal (LOS) is detected in $T_{\text{carrier}} \approx 1 - 3\text{ ms}$.
   - *OSPFv2 Tuned:* $T_{\text{dead}} = 3 \times T_{\text{hello}} = 3 \times 1.0\text{ s} = 3.0\text{ s}$.
   - *OSPFv2 Default:* $T_{\text{dead}} = 4 \times T_{\text{hello}} = 4 \times 10.0\text{ s} = 40.0\text{ s}$.
   - *RIPv2:* $T_{\text{triggered}} \approx 1.0\text{ s}$ (`MinTriggeredCooldown`).
2. **Shortest Path Computation Time ($T_{\text{compute}}$):**
   - For link-state routing, Dijkstra's algorithm computes the new Shortest Path Tree (SPT):
     $$T_{\text{SPF}} = \mathcal{O}(|E| + |V| \log |V|) \approx 2 - 5\text{ ms}$$
3. **FIB Installation Time ($T_{\text{FIB}}$):**
   - Hardware Forwarding Information Base rewrite time: $T_{\text{FIB}} \approx 1\text{ ms}$.

**Validation Against Experimental Data:**
The measured outage for OSPF Tuned is $3.251\text{ s}$, which closely tracks the theoretical formula $3.000 + 0.005 + 0.001 = 3.006\text{ s}$, with the small additional $245\text{ ms}$ variance stemming from discrete timer quantization and queuing jitter.

---

## 4. Modelled vs. Built-in NS-3 Components
To ensure academic integrity, the report clearly differentiates simulated protocol components from analytical models:
- **Built into NS-3:**
  - `ns3::Ipv4GlobalRouting`: Built-in shortest-path routing algorithm based on Dijkstra's algorithm.
  - `ns3::Ipv4StaticRouting`: Built-in Linux-like forwarding table supporting metric-based floating routes and interface status checking.
  - `ns3::Rip`: Built-in RFC 2453 implementation featuring periodic updates, triggered updates, split horizon, and poison reverse.
  - `ns3::PointToPointNetDevice`: Built-in physical layer emulation with queue disciplines and carrier state management.
- **Modelled in Simulation:**
  - *OSPF Hello/Dead Timer Detection:* Because NS-3 does not contain an active OSPFv2 protocol daemon (e.g., Quagga/FRR), OSPF's failure detection dead timer ($3\text{ s}$ tuned, $40\text{ s}$ default) is modelled by scheduling `Ipv4GlobalRoutingHelper::RecomputeRoutingTables()` at $t_{\text{fail}} + T_{\text{dead}} + T_{\text{SPF}} + T_{\text{FIB}}$.
  - *Adjacency Formation Delay:* The restoration delay before reverting to the repaired primary link is modelled as $T_{\text{hello}} + T_{\text{SPF}} + T_{\text{FIB}}$.

---

## 5. Comparison with Cisco Packet Tracer Design
In the Cisco Packet Tracer half of this project:
- With default OSPF timers (`hello 10`, `dead 40`), Packet Tracer simulation shows a dead-interval reconvergence outage of **$38 - 42\text{ seconds}$**, during which ping packets between ICU and Clinic are continuously dropped.
- When tuned with `ip ospf dead-interval 3` and `hello-interval 1`, Packet Tracer convergence drops to **$3.2\text{ seconds}$**.
- **Conclusion:** The NS-3 discrete-event simulation perfectly corroborates the Cisco Packet Tracer implementation ($40.32\text{ s}$ vs. $3.25\text{ s}$), validating the hospital design recommendation that **all clinical WAN routers must be configured with sub-second or tuned OSPF hello/dead timers**.

---

## 6. Clinical Application Impact: PACS DICOM TCP Transfer
As shown in [`e5_throughput_timeseries.png`](e5_throughput_timeseries.png):
1. **Pre-Failure Phase ($t < 15\text{ s}$):** PACS transfer saturates the dedicated Primary WAN link at $1820.0\text{ kbps}$ ($91\%$ efficiency).
2. **Outage Phase ($15\text{ s} \le t < 18\text{ s}$):** In-flight segments and ACKs are dropped. The TCP sender enters ACK silence, causing its Retransmission Timeout (RTO) to expire. Congestion window collapses to $1\text{ MSS}$.
3. **Failover Phase ($18\text{ s} \le t < 45\text{ s}$):** Routing reconverges over the Backup WAN ($1.0\text{ Mbps}$). The TCP sender exits Slow Start and adapts its transmission rate to **$890.0\text{ kbps}$** ($89\%$ utilization of the backup capacity).
4. **Restoration Phase ($t \ge 45\text{ s}$):** The primary fiber link is restored. Traffic transitions back to the $2.0\text{ Mbps}$ link, and TCP probes outward, regaining $1820.0\text{ kbps}$ without connection termination.
