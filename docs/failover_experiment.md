# Disaster-Resilient Smart Hospital Network: Failover Experiment Protocol & Convergence Analysis
**Document ID:** DOC-FAILOVER-2026-v2.0  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  
**Institution:** School of Computer Science and Engineering (SCOPE), VIT Vellore  
**Target Environment:** Cisco Packet Tracer 8.x+ / Cisco IOS 15.x  
**Related Requirements:** REQ-HA-001 through REQ-HA-006, REQ-SLA-001 (Vitals Outage < 3.0s), REQ-SLA-002 (EHR Outage < 15.0s)  
**Verification Harness:** [`sim/convergence_analysis.py`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/sim/convergence_analysis.py), [`sim/parse_ping.py`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/sim/parse_ping.py)  

---

## 1. Executive Summary & Regulatory Context

In mission-critical healthcare campus networks, instantaneous recovery from topological faults is an indispensable safety requirement. Under **IEC 80001-1** (Application of Risk Management for IT-Networks Incorporating Medical Devices) and clinical telemetry reliability standards, continuous physiological data streams—including electrocardiogram (ECG), arterial blood pressure (ABP), and intracranial pressure (ICP)—cannot endure an end-to-end communication disruption exceeding **$\le 3.0$ seconds** without triggering hazardous clinical false alarms or vital telemetry blackouts. Secondary hospital traffic, such as electronic health record (EHR) transactions, laboratory information systems (LIS), and digital radiology (PACS), can withstand standard operational convergence intervals of **$\le 10.0$ to $15.0$ seconds**.

This document defines the formal, reproducible **High-Availability Failover Experiment Protocol** for the hospital network architecture across Cisco Packet Tracer 8.x+. The protocol tests resilience across three protocol planes:
1. **First-Hop Gateway Redundancy:** Cisco Hot Standby Router Protocol (HSRP, RFC 2281).
2. **Layer 2 Loop-Free Redundancy:** Rapid Spanning Tree Protocol (IEEE 802.1w / Rapid-PVST+).
3. **Layer 3 Interior Gateway Dynamic Routing:** Open Shortest Path First (OSPFv2, RFC 2328) with metric-based secondary path diversion and floating Enhanced Interior Gateway Routing Protocol (EIGRP AS 100, RFC 7868).

```
                            +--------------------------+
                            |       Internet Edge      |
                            |       Gateway (R-GW)     |
                            +------------+-------------+
                                         | Gi0/0
                                         |
                            +------------+-------------+
                            |     Main Hospital Core   |
                            |        Router (R1)       |
                            +---+------------------+---+
             Primary WAN Link   |                  |   Secondary WAN Link
          (Serial0/0/0, Cost 64)|                  |   (Serial0/0/1, Cost 500 / EIGRP AD 115)
                                |                  |
                                v                  v
                            +---+------------------+---+
                            |  Remote Clinic Branch    |
                            |        Router (R2)       |
                            +------------+-------------+
                                         | Gi0/1 (Routed Uplink)
                                         v
                            +------------+-------------+
                            | Clinic Dist Switch SW-D3 |
                            +--------------------------+
                                         |
                            +------------+-------------+
                            | Clinic Host / EHR Server |
                            +--------------------------+

      [Main Hospital Campus Distribution & Access Architecture]
                            +--------------------------+
                            |        Router (R1)       |
                            +---+------------------+---+
                Gi0/1 (172.16.8.96/30)            Gi0/2 (172.16.8.92/30)
                                |                  |
                                v                  v
                        +-------+-------+  Port-   +-------+-------+
                        |     SW-D1     | Channel1 |     SW-D2     |
                        | (HSRP Primary)|<========>| (HSRP Standby)|
                        | (RSTP Root Pri|  Trunk   | (RSTP Sec Root|
                        +-------+-------+          +-------+-------+
                                |                          |
                                +------------+-------------+
                                             | Access Trunks (802.1Q)
                                             v
                                    +--------+--------+
                                    |  SW-A1 (Access) |
                                    +--------+--------+
                                             | Fa0/1 (Access VLAN 10)
                                             v
                                    +--------+--------+
                                    |  ICU Patient    |
                                    | Monitor (Host)  |
                                    +-----------------+
```

---

## 2. Comparison of Three Protocol Configurations

The experiment tests three distinct dynamic routing and failover configurations across identical hardware failures to evaluate the trade-off between control-plane overhead and convergence velocity:

```
+----------------------------------------------------------------------------------------------------+
|                                    CONFIGURATION MATRIX                                            |
+-------------------+-------------------------------+-------------------------------+----------------+
| Parameter         | Config A: Default OSPFv2      | Config B: Tuned Fast OSPFv2   | Config C: EIGRP|
|                   |                               |                               | Backup Design  |
+-------------------+-------------------------------+-------------------------------+----------------+
| Primary WAN Link  | OSPF Area 0, Cost 64          | OSPF Area 0, Cost 64          | OSPF Area 0    |
| Secondary WAN Link| OSPF Area 0, Cost 500         | OSPF Area 0, Cost 500         | EIGRP AS 100   |
| Primary Hello /   | Hello = 10.0 s                | Hello = 1.0 s                 | Hello = 10.0 s |
| Dead Timers       | Dead = 40.0 s                 | Dead = 4.0 s (or 3.0 s)       | Dead = 40.0 s  |
| Backup Hello /    | Hello = 10.0 s                | Hello = 1.0 s                 | Hello = 5.0 s  |
| Hold Timers       | Dead = 40.0 s                 | Dead = 4.0 s (or 3.0 s)       | Hold = 15.0 s  |
| Routing Preference| OSPF Metric (Cost 64 vs 500)  | OSPF Metric (Cost 64 vs 500)  | Floating AD    |
|                   | Intra-Area Shortest Path      | Intra-Area Shortest Path      | (110 vs 115)   |
| SPF Pacing        | Default (5000ms init delay)   | Throttled (50ms init delay)   | DUAL Diffusing |
| Fast Carrier Drop | Hardware carrier-detect line  | Hardware carrier-detect line  | Immediate line |
| Convergence Basis | Link-state advertisement (LSA)| Aggressive LSA flood + SPF    | Instantaneous  |
|                   | flood + Dijkstra algorithm    | fast timer calculation        | Feasible Succ. |
+-------------------+-------------------------------+-------------------------------+----------------+
```

### 2.1 Configuration A: Default OSPFv2 Timers
- **Specification:** Standard RFC 2328 parameters. Point-to-point serial interfaces run with `ip ospf hello-interval 10` and `ip ospf dead-interval 40`.
- **Behavior:** On signaled interface shutdown (carrier drop), neighbor tear-down is immediate ($< 100\text{ ms}$). However, for un-signaled faults (downstream transponder failure or intermediate frame loss), the router waits the full $40.0\text{ s}$ Dead Timer before declaring adjacency down and recalculating the shortest path tree (SPT).
- **Control Overhead:** Minimal. Hello packets transmitted once every 10 seconds.

### 2.2 Configuration B: Tuned Fast OSPFv2 Timers
- **Specification:** Point-to-point serial links and routed distribution uplinks configured with aggressive timers:
  ```ios
  interface Serial0/0/0
   ip ospf hello-interval 1
   ip ospf dead-interval 4
  !
  router ospf 1
   timers throttle spf 50 100 1000
  ```
  *(Note: Cisco Packet Tracer 8.x supports `hello-interval 1` and `dead-interval 4` or `3` across Cisco 2911 and 1941 ISR platforms).*
- **Behavior:** Un-signaled link losses are detected within $\le 4.0\text{ s}$ instead of $40.0\text{ s}$. SPF calculation begins within $50\text{ ms}$ of LSA reception.
- **Control Overhead:** 10$\times$ higher hello generation rate.

### 2.3 Configuration C: Dynamic EIGRP Backup Design
- **Specification:** Dual routing protocol architecture. The primary serial link (`Serial0/0/0`) participates in OSPF Process 1 (Administrative Distance = 110). The secondary serial link (`Serial0/0/1`) runs EIGRP AS 100 with a floating Administrative Distance of 115:
  ```ios
  router eigrp 100
   network 172.16.8.84 0.0.0.3
   distance eigrp 115 115
  ```
- **Behavior:** Under steady state, OSPF route ($AD=110$) populates the Routing Information Base (RIB) and Forwarding Information Base (FIB). When the primary link fails, OSPF route is purged, and the EIGRP route ($AD=115$) is installed into the FIB. If EIGRP maintains a Feasible Successor ($RD < FD$), convergence is instantaneous ($< 100\text{ ms}$).

---

## 3. Theoretical Convergence Derivations & Sanity-Checking

To distinguish empirical simulation artifacts from protocol behavior, every observed outage duration must be compared against first-principles mathematical derivations:

$$T_{\text{conv}} = T_{\text{detect}} + T_{\text{SPF/DUAL}} + T_{\text{FIB}} + T_{\text{L2/ARP}}$$

Where:
1. **$T_{\text{detect}}$ (Fault Detection Latency):**
   - *Signaled Carrier Drop (Direct Link Cut / Administrative Shutdown):* Carrier-detect hardware interrupt triggers interface state transition to `down/down`. $T_{\text{detect}} \approx 10\text{ ms} - 50\text{ ms}$.
   - *Un-signaled Fault (Silent Link Blackhole / Switch ASIC Stall):* Governed by protocol dead timer:
     $$T_{\text{detect\_OSPF\_default}} = 4 \times \text{Hello} = 40.00\text{ s}$$
     $$T_{\text{detect\_OSPF\_tuned}} = 4 \times \text{Hello} = 4.00\text{ s}$$
     $$T_{\text{detect\_HSRP\_default}} = \text{HoldTime} = 10.00\text{ s}$$
     $$T_{\text{detect\_EIGRP\_default}} = \text{HoldTime} = 3 \times \text{Hello} = 15.00\text{ s}$$
2. **$T_{\text{SPF/DUAL}}$ (Algorithm Execution Latency):**
   - *OSPF Dijkstra Calculation:* $T_{\text{SPF}} = T_{\text{hold}} + T_{\text{Dijkstra}}$. In small enterprise topologies ($< 20$ nodes), $T_{\text{Dijkstra}} < 5\text{ ms}$. SPF hold-down timer defaults to $5.00\text{ s}$ (or $0.10\text{ s}$ when tuned).
   - *EIGRP Feasible Successor:* $T_{\text{DUAL}} = 0\text{ ms}$ (instantaneous lookup in EIGRP topology table).
3. **$T_{\text{FIB}}$ (Forwarding Table Update Latency):**
   - Cisco Express Forwarding (CEF) table prefix rewrite and TCAM ASIC reprogramming. $T_{\text{FIB}} \approx 5\text{ ms} - 25\text{ ms}$ in enterprise hardware ($< 100\text{ ms}$ in Packet Tracer emulation).
4. **$T_{\text{L2/ARP}}$ (Data-Link & MAC Table Realignment):**
   - Rapid-PVST+ Proposal/Agreement handshake: $T_{\text{RSTP}} \approx 100\text{ ms} - 500\text{ ms}$.
   - Gratuitous ARP (GARP) broadcast + CAM table flush: $T_{\text{GARP}} \approx 10\text{ ms} - 50\text{ ms}$.

### Summary of Theoretical Expected Convergence Bounds

```
+----------------------------------------------------------------------------------------------------+
|                                THEORETICAL CONVERGENCE SUMMARY                                     |
+-------------------+--------------------+------------------------+----------------------------------+
| Failure Event     | Protocol           | Theoretical Outage     | Limiting Factor / Formula        |
|                   | Configuration      | Range ($T_{\text{theo}}$)|                                  |
+-------------------+--------------------+------------------------+----------------------------------+
| Primary WAN Link  | Config A (Default) | 1.00 s - 2.00 s        | Carrier drop + OSPF SPF run      |
| Down (Signaled)   | Config B (Tuned)   | 0.15 s - 0.50 s        | Fast SPF throttle (50ms)         |
|                   | Config C (EIGRP)   | 0.10 s - 0.30 s        | Instantaneous AD 115 install     |
+-------------------+--------------------+------------------------+----------------------------------+
| Primary WAN Link  | Config A (Default) | 40.00 s - 42.00 s      | Dead timer (40s) + SPF + FIB     |
| (Un-signaled)     | Config B (Tuned)   | 4.00 s - 4.50 s        | Fast Dead timer (4s) + SPF       |
|                   | Config C (EIGRP)   | 15.00 s - 15.50 s      | EIGRP Hold timer (15s)           |
+-------------------+--------------------+------------------------+----------------------------------+
| Secondary WAN     | All Configurations | 0.00 s                 | Primary link carries active flow;|
| Link Down         |                    |                        | zero packet loss on live traffic |
+-------------------+--------------------+------------------------+----------------------------------+
| WAN Partition &   | Config A (Default) | 5.00 s - 12.00 s       | HDLC up -> OSPF 2-Way -> Full    |
| Primary Restored  | Config B (Tuned)   | 1.50 s - 3.00 s        | 1s Hellos -> Adjacency -> Preempt|
|                   | Config C (EIGRP)   | 3.00 s - 6.00 s        | OSPF adjacency re-preempts EIGRP |
+-------------------+--------------------+------------------------+----------------------------------+
| R1 Distribution   | Config A & B       | 0.50 s - 1.00 s        | Gi0/1 down -> OSPF intra-area    |
| Uplink Failure    |                    |                        | reroute via SW-D2 Port-channel1  |
+-------------------+--------------------+------------------------+----------------------------------+
| SW-D1 Switch Crash| HSRP Default       | 10.00 s - 11.50 s      | HSRP Hold Timer (10s) + GARP     |
| (HSRP + STP)      | HSRP Tuned (msec)  | 0.75 s - 1.25 s        | Fast HSRP (750ms) + 802.1w sync  |
+-------------------+--------------------+------------------------+----------------------------------+
| R2 Clinic Uplink  | Dual-Dist (HA)     | 0.50 s - 1.00 s        | OSPF link down -> SW-D4 reroute  |
| Failure (Gi0/1)   | Single-Dist        | Permanent Outage       | Clinic subnets isolated from WAN |
+-------------------+--------------------+------------------------+----------------------------------+
```

---

## 4. Rigorous Step-by-Step Failure Scenarios

### 4.1 Controlled Variables
During all 6 experimental scenarios, the following variables must remain strictly controlled:
1. **Traffic Load:** A continuous, steady-state ICMP stream generated from ICU Host `ICU-PC1` (`172.16.8.40`) to Clinic Server `172.16.5.10` (or `172.16.8.36`) at a fixed transmission frequency ($\Delta t_{\text{ping}} = 1.00\text{ s}$). Background SBC vitals telemetry runs concurrently over UDP port 5000.
2. **Link Metrics:** Primary WAN (`R1:Se0/0/0` <-> `R2:Se0/0/0`) OSPF Cost = 64. Secondary WAN (`R1:Se0/0/1` <-> `R2:Se0/0/1`) OSPF Cost = 500.
3. **STP Priority:** `SW-D1` Bridge Priority = 4096 (VLANs 10, 30, 50); `SW-D2` Priority = 8192.
4. **HSRP Priority:** `SW-D1` Priority = 120 (Preempt enabled); `SW-D2` Priority = 110.

---

### 4.2 Scenario 1: Primary WAN Link Failure (R1-R2 Serial0/0/0)

#### A. Objective
Quantify traffic interruption when the primary point-to-point T1 serial WAN link between the Main Hospital Core (`R1`) and Remote Clinic (`R2`) fails, forcing inter-site clinical traffic onto the lower-bandwidth secondary serial link (`Serial0/0/1`).

#### B. Physical & CLI Execution Action
- **Packet Tracer Physical Workspace Action:** Select the Delete Tool (Red 'X' icon or `Del` key) and click directly on the Serial DTE/DCE cable between `R1:Serial0/0/0` and `R2:Serial0/0/0`.
- **Packet Tracer CLI Action (Preferred for Precision):**
  On `R1`:
  ```ios
  R1# configure terminal
  R1(config)# interface Serial0/0/0
  R1(config-if)# shutdown
  ```

#### C. Protocols Expected to Respond
1. **HDLC Layer 2:** Line protocol transitions to `down/down`.
2. **OSPFv2 Link-State Update:** R1 and R2 detect carrier loss on `Serial0/0/0`. Neighbor state immediately transitions `FULL` $\rightarrow$ `DOWN`. R1 generates a Type-1 Router LSA withdrawing the `172.16.8.80/30` stub and point-to-point link, flooding it out `Serial0/0/1`.
3. **Dijkstra Calculation:** R1 and R2 execute Dijkstra's algorithm. Because `Serial0/0/1` has metric 500 ($500 > 64$), it becomes the active shortest path to Remote Clinic subnets (`172.16.6.128/25`, `172.16.8.32/28`).
4. **Routing Table Transition:**
   - *Pre-Failure Route:* `172.16.6.128/25 [110/66] via 172.16.8.82, Serial0/0/0`
   - *Post-Failure Route:* `172.16.6.128/25 [110/502] via 172.16.8.86, Serial0/0/1`

#### D. Live Capture Commands
```ios
R1# debug ip ospf adj
R1# show ip ospf neighbor
R1# show ip route ospf
R1# show ip route 172.16.6.128
```

---

### 4.3 Scenario 2: Secondary WAN Link Failure (R1-R2 Serial0/0/1)

#### A. Objective
Validate that the failure of the standby/secondary WAN link has **zero impact** on active patient vitals telemetry and EHR traffic, verifying true non-blocking redundancy.

#### B. Physical & CLI Execution Action
- **Packet Tracer CLI Action:**
  On `R1`:
  ```ios
  R1# configure terminal
  R1(config)# interface Serial0/0/1
  R1(config-if)# shutdown
  ```

#### C. Protocols Expected to Respond
1. **OSPFv2 / EIGRP:** Adjacency on `Serial0/0/1` drops (`FULL` $\rightarrow$ `DOWN`). Syslog emits `%OSPF-5-ADJCHG: Process 1, Nbr 172.16.8.107 on Serial0/0/1 from FULL to DOWN, Neighbor Down: Interface down or detached`.
2. **RIB / FIB Impact:** No change to active forwarding paths. All transit packets continue traversing `Serial0/0/0` without drop.

#### D. Expected Loss & SLA Evaluation
- **Packets Dropped:** Exactly **0 packets lost** ($N_{\text{lost}} = 0$).
- **Clinical SLA Impact:** **OPTIMAL / COMPLIANT ($0.0\text{ s} \ll 3.0\text{ s}$)**.

---

### 4.4 Scenario 3: Complete WAN Partition and Primary Restoration

#### A. Objective
Measure network behavior during a catastrophic simultaneous failure of both WAN links (complete inter-site partition), followed by the restoration of the primary link, measuring re-convergence latency upon circuit recovery.

#### B. Physical & CLI Execution Action
1. **Induce Partition:**
   On `R1`:
   ```ios
   R1(config)# interface range Serial0/0/0 - 1
   R1(config-if-range)# shutdown
   ```
2. **Observe Partition:** Confirm continuous ping drops between ICU Host and Remote Clinic. Wait 30 seconds for all OSPF/EIGRP neighbor states to fully clear.
3. **Execute Recovery:**
   On `R1`:
   ```ios
   R1(config)# interface Serial0/0/0
   R1(config-if)# no shutdown
   ```

#### C. Protocols Expected to Respond
1. **Physical/Data-Link:** Serial carrier restored. Line protocol transitions to `up/up`.
2. **OSPF Finite State Machine:** R1 sends OSPF Multicast Hello to `224.0.0.5`. Adjacency transitions through states: `DOWN` $\rightarrow$ `INIT` $\rightarrow$ `2-WAY` $\rightarrow$ `EXSTART` (Master/Slave election based on Router ID) $\rightarrow$ `EXCHANGE` (DBD exchange) $\rightarrow$ `LOADING` (LSR/LSU exchange) $\rightarrow$ `FULL`.
3. **SPF Run & Route Reinstallation:** Once in `FULL`, SPF executes and installs clinic routes via `Serial0/0/0`.

#### D. Theoretical vs Packet Tracer Expectations
- **Theoretical Recovery Time:** $\approx 3.0\text{ s} - 6.0\text{ s}$ (governed by OSPF Hello interval, DBD handshake, and route installation).
- **Packets Dropped on Recovery:** Echoes fail during the first 3 to 6 seconds following `no shutdown`, after which continuous replies resume.

---

### 4.5 Scenario 4: R1 Core Distribution Uplink Failure (R1 Gi0/1)

#### A. Objective
Simulate the failure of primary routed link between Core Router `R1` and Distribution Switch `SW-D1`, testing OSPF Area 0 rerouting across the inter-distribution cross-connect (`SW-D1` to `SW-D2` via `Port-channel1`).

#### B. Physical & CLI Execution Action
- **Packet Tracer CLI Action:**
  On `R1`:
  ```ios
  R1# configure terminal
  R1(config)# interface GigabitEthernet0/1
  R1(config-if)# shutdown
  ```

#### C. Protocols Expected to Respond
1. **OSPF Area 0 Adjacency:** Adjacency between `R1:Gi0/1` (`172.16.8.97`) and `SW-D1:Gi0/1` (`172.16.8.98`) drops.
2. **Inter-Switch Rerouting:** `SW-D1` forwards outbound core traffic across its `Port-channel1` link to `SW-D2` (`172.16.8.102`), which forwards to `R1` across operational link `Gi0/2` (`172.16.8.93`).
3. **Route Before Failure:** `0.0.0.0/0 [110/2] via 172.16.8.97, GigabitEthernet0/1`
4. **Route After Failure:** `0.0.0.0/0 [110/3] via 172.16.8.102, GigabitEthernet0/2` (Port-channel1)

#### D. Expected Loss & SLA Evaluation
- **Packets Dropped:** **0 to 1 dropped ping**.
- **Outage Duration:** $\le 1.00\text{ s}$. Fully compliant with the 3.0s vitals SLA.

---

### 4.6 Scenario 5: SW-D1 Switch Crash (HSRP Gateway & STP Root Failure)

#### A. Objective
Simulate a catastrophic hardware power supply failure or ASIC motherboard crash on Primary Distribution Switch `SW-D1`, which simultaneously acts as HSRP Active Default Gateway for odd VLANs and Rapid-PVST+ Root Bridge.

#### B. Physical & CLI Execution Action
- **Packet Tracer Physical Workspace Action:**
  Click on `SW-D1` $\rightarrow$ Select **Physical** tab $\rightarrow$ Click the rocker power switch next to the power supply unit to toggle to **OFF**.
- **Alternative CLI Action:**
  ```ios
  SW-D1# reload
  Proceed with reload? [confirm] <ENTER>
  ```

#### C. Protocols Expected to Respond
1. **HSRP (RFC 2281):** `SW-D1` ceases transmission of HSRP multicast hellos (`224.0.0.2` on UDP port 1985). `SW-D2` runs its Standby Hold Timer ($10.0\text{ s}$ default). Upon expiry, `SW-D2` transitions:
   `Standby` $\rightarrow$ `Listen` $\rightarrow$ `Speak` $\rightarrow$ `Active`.
   `SW-D2` broadcasts a Gratuitous ARP (GARP) with virtual MAC `0000.0c07.ac0a` across access switches to refresh their CAM tables.
2. **Rapid Spanning Tree (IEEE 802.1w):** Access switches (`SW-A1` through `SW-A4`) detect BPDU timeout on root ports connected to `SW-D1`. Their alternate blocking ports to `SW-D2` transition to Root Forwarding via the Proposal/Agreement handshake within $\le 500\text{ ms}$.
3. **OSPF Core Routing:** `R1` detects carrier loss on `Gi0/1` and withdraws direct routes to `SW-D1`.

#### D. Expected Loss & SLA Evaluation
- **Packets Dropped (Default HSRP Timers):** 9 to 11 dropped pings ($T_{\text{outage}} \approx 10.0\text{ s} - 11.2\text{ s}$).
- **Packets Dropped (Tuned Fast Timers `msec 250 750`):** 0 to 1 dropped ping ($T_{\text{outage}} \approx 0.75\text{ s}$).
- **Clinical SLA Impact:** **DEGRADED under default timers**; fully justifies Phase 8 host-side SBC packet buffering and fast HSRP deployment.

---

### 4.7 Scenario 6: R2 Clinic Distribution Uplink Failure (R2 Gi0/1)

#### A. Objective
Evaluate branch clinic resilience when the primary distribution uplink connecting Clinic Router `R2` to Clinic Switch `SW-D3` fails.

#### B. Physical & CLI Execution Action
- **Packet Tracer CLI Action:**
  On `R2`:
  ```ios
  R2# configure terminal
  R2(config)# interface GigabitEthernet0/1
  R2(config-if)# shutdown
  ```

#### C. Protocols Expected to Respond
1. **In High-Availability Clinic Topology (`SW-D3` + `SW-D4` deployed):**
   - `SW-D4` detects loss of HSRP hellos from `SW-D3` on the clinic distribution trunk.
   - `SW-D4` assumes Active Gateway role for Clinic VLANs 10, 40, 60.
   - Traffic reroutes to `R2` across `SW-D4:Gi0/1` (`172.16.8.112/30`).
2. **In Single Distribution Switch Mode (`SW-D3` only):**
   - Total clinic isolation. OSPF on R2 withdraws clinic prefixes (`172.16.6.128/25`, `172.16.8.32/28`).

#### D. Expected Loss & SLA Evaluation
- **HA Mode Outage:** $\approx 1.0\text{ s} - 2.0\text{ s}$ (OSPF route change) or $10.0\text{ s}$ (HSRP default).
- **Single Mode Outage:** Complete loss until interface recovery.

---

## 5. Formal 10-Repetition Measurement Protocol

To ensure textbook scientific validity and eliminate random measurement noise, every scenario must be executed for a minimum of **$N = 10$ independent trials** per configuration mode:

```
                                  [TEST CYCLE EXECUTION]
                                             |
                         +-------------------+-------------------+
                         | 1. Establish Steady-State Flow        |
                         |    ICU-PC1: ping -n 50 172.16.5.10    |
                         +-------------------+-------------------+
                                             |
                         +-------------------+-------------------+
                         | 2. Trigger Failure Action at Ping #10 |
                         |    (Shutdown interface or pull link)  |
                         +-------------------+-------------------+
                                             |
                         +-------------------+-------------------+
                         | 3. Observe Packet Drops & Recovery    |
                         |    Count consecutive "Request timed   |
                         |    out" messages                      |
                         +-------------------+-------------------+
                                             |
                         +-------------------+-------------------+
                         | 4. Restore Link & Wait 45s Cooldown   |
                         |    Ensure OSPF/HSRP returns to state  |
                         +-------------------+-------------------+
                                             |
                         +-------------------+-------------------+
                         | 5. Record Run Data in CSV Matrix      |
                         |    Calculate mean, std dev, 95% CI    |
                         +---------------------------------------+
```

### 5.1 Continuous Ping Execution Script
On `ICU-PC1` Command Prompt:
```cmd
ping -n 50 172.16.5.10
```
*Note: Packet Tracer's PC Command Prompt sends 1 echo request per second ($1000\text{ ms}$ interval) with a default timeout of $2000\text{ ms}$.*

### 5.2 Quantifying Metrics
1. **Lost Packets ($N_{\text{lost}}$):** Number of consecutive "Request timed out" responses.
2. **Estimated Convergence Time ($T_{\text{est}}$):**
   $$T_{\text{est}} = N_{\text{lost}} \times \Delta t_{\text{ping}}$$
3. **Statistical Sample Aggregation:**
   - Sample Mean: $\bar{T} = \frac{1}{N} \sum_{i=1}^{N} T_i$
   - Sample Standard Deviation: $s = \sqrt{\frac{1}{N-1} \sum_{i=1}^{N} (T_i - \bar{T})^2}$
   - 95% Confidence Interval (Student's $t$ with $N-1 = 9$ degrees of freedom, $t_{0.025, 9} = 2.262$):
     $$\text{CI}_{95\%} = \bar{T} \pm 2.262 \times \frac{s}{\sqrt{N}}$$

---

## 6. Comprehensive Results Recording Table

Use this master engineering table to record observed empirical data across all configurations:

```
+----------------------------------------------------------------------------------------------------------------------------------------+
|                                              MASTER FAILOVER RESULTS RECORDING TABLE                                                   |
+-------+-----------------------------+----------+---------------+----------------+------------+--------------------+--------------------+
| Scen. | Scenario Description        | Protocol | Config Mode   | Route Before   | Route After| Packets Lost       | Convergence Time   |
| ID    |                             |          |               | Failure        | Failure    | ($N_{\text{lost}}$)| ($T_{\text{conv}}$)|
+-------+-----------------------------+----------+---------------+----------------+------------+--------------------+--------------------+
| SC-01 | Primary WAN Link Cut        | OSPFv2   | Config A (Def)| via Se0/0/0    | via Se0/0/1| 1 - 2 drops        | 1.00 s - 2.00 s    |
| SC-01 | Primary WAN Link Cut        | OSPFv2   | Config B (Tun)| via Se0/0/0    | via Se0/0/1| 0 - 1 drops        | 0.20 s - 1.00 s    |
| SC-01 | Primary WAN Link Cut        | EIGRP    | Config C (EIG)| via Se0/0/0    | via Se0/0/1| 0 - 1 drops        | 0.10 s - 1.00 s    |
+-------+-----------------------------+----------+---------------+----------------+------------+--------------------+--------------------+
| SC-02 | Secondary WAN Link Cut      | OSPF/EIGR| All Configs   | via Se0/0/0    | via Se0/0/0| 0 drops            | 0.00 s (Seamless)  |
+-------+-----------------------------+----------+---------------+----------------+------------+--------------------+--------------------+
| SC-03 | WAN Partition & Restoration | OSPFv2   | Config A (Def)| Partition (Ø)  | via Se0/0/0| 5 - 10 drops       | 5.00 s - 10.00 s   |
| SC-03 | WAN Partition & Restoration | OSPFv2   | Config B (Tun)| Partition (Ø)  | via Se0/0/0| 2 - 4 drops        | 2.00 s - 4.00 s    |
| SC-03 | WAN Partition & Restoration | EIGRP    | Config C (EIG)| Partition (Ø)  | via Se0/0/0| 3 - 5 drops        | 3.00 s - 5.00 s    |
+-------+-----------------------------+----------+---------------+----------------+------------+--------------------+--------------------+
| SC-04 | R1 Core Dist Uplink Down    | OSPFv2   | Config A & B  | via Gi0/1      | via SW-D2  | 0 - 1 drops        | 0.50 s - 1.00 s    |
+-------+-----------------------------+----------+---------------+----------------+------------+--------------------+--------------------+
| SC-05 | SW-D1 Dist Switch Crash     | HSRP/RSTP| Default HSRP  | Active=SW-D1   | Active=SW-D2 9 - 11 drops      | 10.00 s - 11.20 s  |
| SC-05 | SW-D1 Dist Switch Crash     | HSRP/RSTP| Tuned HSRP    | Active=SW-D1   | Active=SW-D2 0 - 1 drops       | 0.75 s - 1.00 s    |
+-------+-----------------------------+----------+---------------+----------------+------------+--------------------+--------------------+
| SC-06 | R2 Clinic Uplink Failure    | OSPF/HSRP| HA Mode       | via SW-D3      | via SW-D4  | 1 - 2 drops        | 1.00 s - 2.00 s    |
| SC-06 | R2 Clinic Uplink Failure    | OSPF     | Single Mode   | via SW-D3      | Isolated   | All drops (Ø)      | Permanent Outage   |
+-------+-----------------------------+----------+---------------+----------------+------------+--------------------+--------------------+
```

---

## 7. Honest Assessment of Cisco Packet Tracer Timing Limits

In any rigorous scientific or engineering defense, the boundaries and limits of the experimental simulation platform must be acknowledged. Cisco Packet Tracer is a high-level educational discrete-event network simulator, not a hardware emulator (such as Cisco VIRL/CML or GNS3/Dynamips) nor real silicon:

```
+----------------------------------------------------------------------------------------------------+
|                                    PACKET TRACER LIMITATION MATRIX                                 |
+--------------------------+---------------------------------+---------------------------------------+
| Simulator Dimension      | Real Cisco Hardware (Catalyst)  | Cisco Packet Tracer 8.x               |
+--------------------------+---------------------------------+---------------------------------------+
| Simulation Clock         | Continuous microsecond wall-time| Discrete quantized event ticks        |
| Ping Measurement Step    | Sub-millisecond (e.g., 0.1 ms)  | Quantized to 1.0-second discrete steps|
| Packet Forwarding Plane  | Hardware ASIC / TCAM lookup     | Software thread sequential loop       |
| Timestamp Resolution     | `datetime msec` (millisecond)   | Seconds only in console logs          |
| Fast BFD Support         | Supported (Sub-50ms BFD)        | Unsupported (Requires OSPF Fast Timers|
| Memory Queuing Behavior  | Real buffer drops & tail drop   | Simplified statistical drop model     |
+--------------------------+---------------------------------+---------------------------------------+
```

### Detailed Evaluation of Timing Limits
1. **Discrete-Event Simulation Clock Coarseness:**
   Packet Tracer executes events by processing discrete timestamps from an internal priority queue. When operating in **Realtime Mode**, the simulation engine syncs to host CPU wall-clock time in 1-second coarse intervals. When multiple asynchronous control-plane packets arrive simultaneously (e.g., HSRP hellos, RSTP BPDUs, and OSPF Hellos), they are evaluated sequentially rather than in true asynchronous parallel silicon.
2. **Ping Interval Quantization ($\Delta t = 1.0\text{ s}$):**
   The simulated Windows Command Prompt ping tool issues requests at exactly $1000\text{ ms}$ intervals. Consequently, an outage duration of $450\text{ ms}$ may register as either 0 dropped packets or 1 dropped packet depending entirely on whether the physical link failure occurs immediately before or immediately after an echo transmission. The measurement error is bounded by $\pm 1.0\text{ s}$.
3. **Absence of Millisecond Console Timestamps:**
   Cisco IOS running within Packet Tracer does not support `service timestamps debug datetime msec`. Debug outputs (`debug ip ospf adj`, `debug standby`) only display second-level timestamps (`00:00:32`), preventing sub-second timestamp correlation directly from router terminal logs.
4. **Hardware ASIC vs. Software Emulation:**
   In real Catalyst 3560/3850 switches, CEF prefix updates and MAC table learning are executed directly in TCAM ASICs in $< 10\text{ ms}$. In Packet Tracer, MAC table transitions and Gratuitous ARP broadcasts incur software loop latency, occasionally adding 1 additional second of observed drop.

---

## 8. Viva & Technical Review Discussion Points

1. **Why does Scenario 1 (Primary WAN Cut) converge in $< 2.0\text{ s}$ even with default OSPF timers (Dead=40s)?**
   - *Model Answer:* Because the link failure is a **signaled carrier drop**. When `Serial0/0/0` is shut down, the physical layer line protocol drops immediately (`down/down`). Cisco IOS does not wait for the 40-second dead timer; the carrier loss immediately triggers an interface down event, an immediate Type-1 LSA generation, and a Dijkstra calculation. The 40-second dead timer only applies to **un-signaled failures** where the cable remains physically connected but frames are dropped silently.
2. **Why does Scenario 5 (SW-D1 Power Off) take $\approx 11\text{ seconds}$ to failover?**
   - *Model Answer:* `SW-D1` is powered off completely, meaning it cannot send any teardown notification. `SW-D2` must wait for the HSRP Hold Timer ($10.0\text{ s} = 3 \times 3.0\text{ s} + 1.0\text{ s}$) to expire before concluding that the Active Gateway is dead and promoting itself to Active. The additional 1 second is attributable to Gratuitous ARP learning across access switches and Packet Tracer's 1-second ping quantization.
3. **How does our architecture ensure patient vitals telemetry survives Scenario 5 without violating the 3.0s SLA?**
   - *Model Answer:* Through two complimentary designs:
     1. In production Cisco hardware, HSRP timers are configured in milliseconds (`standby 10 timers msec 250 msec 750`), reducing failover to $< 750\text{ ms}$.
     2. In Phase 8, the SBC-PT clinical IoT sensor gateway implements a local FIFO ring buffer with Selective Repeat ARQ. During the 10-second HSRP convergence window, sensor vitals frames are buffered in local SBC memory and automatically retransmitted upon gateway recovery, ensuring zero patient record loss.
4. **What is the Feasibility Condition in EIGRP, and why does Configuration C provide faster recovery than Configuration A?**
   - *Model Answer:* EIGRP's Feasibility Condition states that an alternate path is loop-free and can be immediately installed as a Feasible Successor if the neighbor's Reported Distance (RD) is strictly less than the current Feasible Distance (FD):
     $$\text{RD} < \text{FD}$$
     When met, EIGRP does not execute the DUAL diffusing computation; it immediately shifts traffic to the pre-computed backup link in $< 50\text{ ms}$, whereas OSPF must flood LSAs and run Dijkstra's algorithm.
