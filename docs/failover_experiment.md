# Disaster-Resilient Smart Hospital Network: Failover Experiment Execution Plan
**Document ID:** DOC-FAILOVER-2026-v1.0  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  
**Institution:** School of Computer Science and Engineering (SCOPE), VIT Vellore  
**Target Environment:** Cisco Packet Tracer 8.x+ / Cisco IOS 15.x  
**Related Requirements:** REQ-HA-001 through REQ-HA-006, REQ-SLA-001 (Vitals Outage < 3.0s)

---

## 1. Executive Summary & Test Methodology

High availability in healthcare critical infrastructure requires continuous data connectivity. IEC 80001-1 and hospital clinical telemetry guidelines dictate that patient vitals streams (ICU telemetry, surgical alarms) must survive infrastructure failures with an end-to-end recovery time of **$\le$ 3.0 seconds**. Bulk data transfers (EHR records, PACS imaging) may tolerate standard convergence intervals ($\le$ 10.0 to 15.0 seconds).

This document establishes the official test execution guide for six (6) distinct hardware and topological failure scenarios simulated within Cisco Packet Tracer. Each scenario evaluates multi-layer protocol interaction across the OSI stack:
1. **Layer 2 Spanning Tree Protocol:** Rapid-PVST+ (IEEE 802.1w) root port and alternate port convergence.
2. **First-Hop Gateway Redundancy:** Cisco HSRP (RFC 2281 / Cisco IOS Hot Standby Router Protocol).
3. **Layer 3 Dynamic Routing:** Open Shortest Path First (OSPFv2, RFC 2328) link-state updates and Dijkstra SPF recomputations.

```
                      +-------------------+
                      |   R1 (Core GW)    |
                      +---------+---------+
                                |
             +------------------+------------------+
             | Gi0/1                               | Gi0/2
     +-------+-------+                     +-------+-------+
     |     SW-D1     |<=== PortChannel ===>|     SW-D2     |
     | (HSRP Primary)|     (Inter-Dist)    | (HSRP Standby)|
     +-------+-------+                     +-------+-------+
             |                                     |
             +------------------+------------------+
                                |
                      +---------+---------+
                      |   SW-A1 (Access)  |
                      +---------+---------+
                                |
                      +---------+---------+
                      | ICU-PC1 / Sensor  |
                      +-------------------+
```

---

## 2. Theoretical Convergence Formulas & Baseline Expectations

| Protocol Mechanism | Governing Timers / RFC Parameters | Theoretical Convergence Time ($T_{\text{theo}}$) | Formula / Derivation |
| :--- | :--- | :--- | :--- |
| **RSTP Alternate Port Takeover** | IEEE 802.1w Proposal/Agreement Handshake | **$\le 0.50$ seconds** (Hardware: $< 50\text{ ms}$) | Immediate Root Port transition upon carrier loss on alternate port |
| **RSTP Root Bridge Re-election** | 3 $\times$ Hello Time (Hello = 2.0s) | **$6.00$ seconds** | $T_{\text{RSTP\_loss}} = 3 \times \text{Hello}$ |
| **HSRP Default Failover** | Hello = 3.0s, Hold = 10.0s (RFC 2281) | **$10.00$ seconds** | $T_{\text{HSRP}} = \text{HoldTime} = 3 \times \text{Hello} + 1.0\text{s}$ |
| **HSRP Fast Timers (Tuned)** | Hello = 250ms, Hold = 750ms | **$0.75$ seconds** | $T_{\text{HSRP\_fast}} = \text{HoldTime} = 750\text{ ms}$ |
| **OSPF Intra-Area Link Down** | Hardware Carrier Detect + LSA Flood + SPF | **$0.50 - 1.00$ seconds** | $T_{\text{SPF}} = \text{Detect} + T_{\text{LSA\_Pacing}} + T_{\text{Dijkstra}}$ |
| **OSPF Dead Timer Expiry** | Dead Interval = 4 $\times$ Hello (Hello = 10s) | **$40.00$ seconds** | $T_{\text{OSPF\_dead}} = 4 \times \text{Hello}$ (un-signaled link fault) |

---

## 3. Failure Scenario 1: SW-D1 Power Off (Distribution Switch Failure)

### 3.1 Objective & Physical Action
Simulate total electrical power loss or fatal ASIC motherboard failure on primary distribution switch `SW-D1`.
- **Packet Tracer Action:** Navigate to Packet Tracer Logical Workspace $\rightarrow$ Click on `SW-D1` $\rightarrow$ Select the **Physical** tab $\rightarrow$ Locate the rocker power switch next to the power supply unit $\rightarrow$ Click to toggle power to **OFF** (LEDs turn dark).
- **Alternative CLI Action:** On `SW-D1`: `reload` (confirm without saving).

### 3.2 Protocols Expected to Respond
1. **HSRP:** SW-D1 ceases transmission of multicast HSRP Hellos (`224.0.0.2` on UDP port 1985). SW-D2 monitors the standby hold timer (10 seconds). Upon timer expiry, SW-D2 transitions from `Standby` $\rightarrow$ `Active` on client SVIs (VLANs 10, 30).
2. **Rapid-PVST+:** Access switches (SW-A1, SW-A2, SW-A3) detect loss of root BPDUs from SW-D1. Alternate uplinks to SW-D2 transition to Root Forwarding.
3. **OSPFv2:** Core router R1 detects carrier drop on interface `GigabitEthernet0/1` and withdraws routes pointing to SW-D1.

### 3.3 Theoretical vs Packet Tracer Expectations
- **Theoretical Failover Duration:** $10.0\text{ seconds}$ (governed by HSRP hold timer).
- **Ping Command:** Execute from `ICU-PC1` (`172.16.8.40`):
  ```cmd
  ping -n 60 172.16.5.10
  ```
- **Expected Loss:** 9 to 11 consecutive dropped pings (1-second ping interval).
- **Clinical SLA Impact:** **DEGRADED / EXCEEDED (10s > 3s)** when operating on default HSRP timers; demonstrates critical justification for Phase 8 application-layer sequence buffers and fast timers.

### 3.4 Verification Commands
#### On SW-D2 (Standby Gateway):
```ios
SW-D2# show standby brief
                   P indicates configured to preempt.
                   |
Interface   Grp  Pri P State   Active          Standby         Virtual IP
Vl10        10   110   Active  local           unknown         172.16.8.33
Vl20        20   120 P Active  local           unknown         172.16.8.49
Vl30        30   110   Active  local           unknown         172.16.8.1
Vl40        40   120 P Active  local           unknown         172.16.6.129
Vl50        50   110   Active  local           unknown         172.16.7.193
```
*Verification Confirmation:* All SVIs previously served by SW-D1 now display `State: Active` and `Active: local`.

#### On Core Router R1:
```ios
R1# show ip route ospf
     172.16.0.0/16 is variably subnetted, 26 subnets, 6 masks
O        172.16.8.32/27 [110/3] via 172.16.8.94, 00:00:14, GigabitEthernet0/2
O        172.16.8.0/27 [110/3] via 172.16.8.94, 00:00:14, GigabitEthernet0/2
```
*Verification Confirmation:* All distribution subnets previously reachable via Gi0/1 (`172.16.8.98`) now route through Gi0/2 (`172.16.8.94`).

### 3.5 Recovery Procedure
1. Click `SW-D1` $\rightarrow$ Physical tab $\rightarrow$ Toggle power switch to **ON**.
2. Wait 45 seconds for Cisco IOS boot sequence.
3. Observe **HSRP Preemption**: Because `SW-D1` has `standby 10 priority 120` and `standby 10 preempt`, it detects SW-D2's lower priority (110) and reclaims the Active state.
4. Verify with `show standby brief` on SW-D1: State transitions back to `Active`.

---

## 4. Failure Scenario 2: SW-D1 to R1 Uplink Severed (Routed Core Uplink Failure)

### 4.1 Objective & Physical Action
Simulate physical fiber cut or transponder failure between distribution switch `SW-D1` and core router `R1`. SVI gateway functions on SW-D1 remain completely intact.
- **Packet Tracer Action:** Use the Delete tool (Red Cross) to delete the copper link between `SW-D1:Gi0/1` and `R1:Gi0/1`.
- **Alternative CLI Action:** On `SW-D1`:
  ```ios
  SW-D1# configure terminal
  SW-D1(config)# interface GigabitEthernet0/1
  SW-D1(config-if)# shutdown
  ```

### 4.2 Protocols Expected to Respond
1. **OSPFv2:** `SW-D1` detects interface down on Gi0/1. It generates a Type-1 Router LSA indicating link withdrawal and floods it across the cross-connect trunk (`Port-channel1` / Gi0/2) to `SW-D2`.
2. **Dijkstra SPF:** Both `R1` and `SW-D1` run SPF. `SW-D1` replaces default route next-hop with `172.16.8.102` (`SW-D2`).
3. **HSRP:** Remains in `Active` state on `SW-D1` because access VLAN SVIs are operational (unless HSRP object tracking is triggered).

### 4.3 Theoretical vs Packet Tracer Expectations
- **Theoretical Failover Duration:** $0.50 - 1.00\text{ seconds}$ (OSPF LSA flooding + SPF calculation).
- **Ping Command:** Execute from `ICU-PC1` (`172.16.8.40`):
  ```cmd
  ping -n 30 172.16.8.106
  ```
  *(172.16.8.106 is R1 Loopback0)*
- **Expected Loss:** 1 dropped ping (or 0 if ping aligns between packet transmissions).
- **Clinical SLA Impact:** **ACCEPTABLE ($< 1.0\text{s} \ll 3.0\text{s}$)**. Patient telemetry encounters zero alarm interruption.

### 4.4 Verification Commands
#### On SW-D1:
```ios
SW-D1# show ip route 0.0.0.0
Routing entry for 0.0.0.0/0, supernet
  Known via "ospf 1", distance 110, metric 2, candidate default path
  Last update from 172.16.8.102 on GigabitEthernet0/2, 00:00:08 ago
  Routing Descriptor Blocks:
  * 172.16.8.102, from 172.16.8.106, 00:00:08 ago, via GigabitEthernet0/2
```
*Verification Confirmation:* The outbound path to core router R1 is successfully routed through SW-D2 across link Gi0/2.

#### On SW-D2:
```ios
SW-D2# show ip ospf neighbor
Neighbor ID     Pri   State           Dead Time   Address         Interface
172.16.8.105      1   FULL/DR         00:00:32    172.16.8.101    GigabitEthernet0/2
172.16.8.106      1   FULL/DR         00:00:35    172.16.8.93     GigabitEthernet0/1
```
*Verification Confirmation:* SW-D2 maintains two full OSPF adjacencies and forwards transit traffic between SW-D1 and R1.

### 4.5 Recovery Procedure
1. Reconnect cable between `SW-D1:Gi0/1` and `R1:Gi0/1` (or issue `no shutdown` on `SW-D1:Gi0/1`).
2. OSPF establishes adjacency (`LOADING` $\rightarrow$ `FULL`).
3. Routing table on SW-D1 immediately reinstalls direct Gi0/1 path.

---

## 5. Failure Scenario 3: Primary Serial WAN Link R1-R2 Severed (WAN Link Failure)

### 5.1 Objective & Physical Action
Simulate telecommunications provider backhoe fiber cut on the primary point-to-point serial WAN link connecting Main Hospital Core (`R1`) to Remote Emergency Clinic (`R2`).
- **Packet Tracer Action:** Disconnect Serial DTE/DCE cable between `R1:Serial0/0/0` and `R2:Serial0/0/0`.
- **Alternative CLI Action:** On `R1`:
  ```ios
  R1# configure terminal
  R1(config)# interface Serial0/0/0
  R1(config-if)# shutdown
  ```

### 5.2 Protocols Expected to Respond
1. **OSPFv2 Multi-Area Routing:** Primary link `Serial0/0/0` has OSPF cost 64 (T1 bandwidth). Backup link `Serial0/0/1` has metric `ip ospf cost 500`.
2. Upon link fault, R1 and R2 tear down neighbor state on Se0/0/0 and flood LSA updates across the operational backup link Se0/0/1 (`172.16.8.84/30`).
3. OSPF installs Se0/0/1 as the active transit path for Area 0.

### 5.3 Theoretical vs Packet Tracer Expectations
- **Theoretical Failover Duration:** $1.00 - 2.00\text{ seconds}$ (Serial HDLC line protocol down + OSPF SPF run).
- **Ping Command:** Execute from Remote Clinic Workstation (`172.16.8.45` on VLAN 10) to Main EHR Database (`172.16.5.10`):
  ```cmd
  ping -n 40 172.16.5.10
  ```
- **Expected Loss:** 1 to 2 dropped pings.
- **Clinical SLA Impact:** **ACCEPTABLE ($< 2.0\text{s} \le 3.0\text{s}$)**. Remote doctor query experiences minor hiccup but stays connected.

### 5.4 Verification Commands
#### On Main Hospital Router R1:
```ios
R1# show ip route 172.16.6.0
Routing entry for 172.16.6.0/24, supernet
  Known via "ospf 1", distance 110, metric 502, type intra-area
  Last update from 172.16.8.86 on Serial0/0/1, 00:00:05 ago
  Routing Descriptor Blocks:
  * 172.16.8.86, from 172.16.8.107, 00:00:05 ago, via Serial0/0/1
```
*Verification Confirmation:* Route metric increased from 66 to 502, pointing out `Serial0/0/1`.

#### On Remote Clinic Router R2:
```ios
R2# show ip ospf neighbor
Neighbor ID     Pri   State           Dead Time   Address         Interface
172.16.8.106      1   FULL/  -        00:00:33    172.16.8.85     Serial0/0/1
172.16.8.108      1   FULL/BDR        00:00:36    172.16.8.97     GigabitEthernet0/1
```
*Verification Confirmation:* Neighbor `172.16.8.106` (`R1`) is active in state `FULL/-` across `Serial0/0/1`.

### 5.5 Recovery Procedure
1. Re-enable primary link: On `R1:Serial0/0/0`, issue `no shutdown`.
2. OSPF detects primary link with cost 64. Because $64 < 500$, SPF recalculates and re-elects `Serial0/0/0` as preferred path.
3. Trace route confirms traffic returns to primary serial interface.

---

## 6. Failure Scenario 4: Core Switch / Spanning Tree Root Bridge Failure

### 6.1 Objective & Physical Action
Evaluate Layer 2 loop-prevention and Rapid-PVST+ re-convergence when the active Root Bridge (`SW-D1`) loses all Layer 2 trunk connectivity.
- **Packet Tracer Action:** In CLI of `SW-D1`, shut down all downlink trunk interfaces to access switches `SW-A1` through `SW-A4`:
  ```ios
  SW-D1# configure terminal
  SW-D1(config)# interface range FastEthernet0/1 - 4
  SW-D1(config-if-range)# shutdown
  ```

### 6.2 Protocols Expected to Respond
1. **Rapid-PVST+ (802.1w):** Access switches `SW-A1`, `SW-A2`, `SW-A3`, `SW-A4` immediately detect loss of Root Port BPDUs.
2. The alternate blocking port connected to `SW-D2` receives an RSTP proposal, acknowledges with agreement, and unblocks directly to `Root Forwarding` without the legacy 30-second listening/learning delay.
3. **Secondary Root Bridge Promotion:** `SW-D2` (configured with `spanning-tree vlan ... root secondary` / priority 8192) becomes the functional active root bridge.

### 6.3 Theoretical vs Packet Tracer Expectations
- **Theoretical Failover Duration:** $1.00 - 2.00\text{ seconds}$ (RSTP Proposal/Agreement sync).
- **Ping Command:** Execute from `ICU-PC1` (`172.16.8.40` on `SW-A1`) to Default Gateway VIP (`172.16.8.33`):
  ```cmd
  ping -n 30 172.16.8.33
  ```
- **Expected Loss:** 1 dropped ping.
- **Clinical SLA Impact:** **ACCEPTABLE ($< 2.0\text{s} \le 3.0\text{s}$)**.

### 6.4 Verification Commands
#### On Access Switch SW-A1:
```ios
SW-A1# show spanning-tree vlan 10
VLAN0010
  Spanning tree enabled protocol rstp
  Root ID    Priority    8202
             Address     0060.70aa.bb02
             Cost        4
             Port        2 (GigabitEthernet0/2)
             Hello Time   2 sec  Max Age 20 sec  Forward Delay 15 sec

  Bridge ID  Priority    32778  (priority 32768 sys-id-ext 10)
             Address     0060.70aa.bb11
             Hello Time   2 sec  Max Age 20 sec  Forward Delay 15 sec

Interface        Role Sts Cost      Prio.Nbr Type
---------------- ---- --- --------- -------- --------------------------------
Gi0/2            Root FWD 4         128.2    P2p
Fa0/1            Desg FWD 19        128.1    P2p Edge
```
*Verification Confirmation:* Root port is now `Gi0/2` (connected to `SW-D2`) in status `FWD`.

#### On SW-D2:
```ios
SW-D2# show spanning-tree vlan 10 root
                                        Root    Hello Max Fwd
Vlan                   Root ID          Cost    Time  Age Dly  Root Port
---------------- -------------------- --------- ----- --- ---  ------------
VLAN0010             8202 0060.70aa.bb02         0    2   20  15
```
*Verification Confirmation:* SW-D2 reports Root Cost 0, confirming it has assumed the active Root Bridge role.

### 6.5 Recovery Procedure
1. Re-enable trunk ports on `SW-D1`:
   ```ios
   SW-D1(config)# interface range FastEthernet0/1 - 4
   SW-D1(config-if-range)# no shutdown
   ```
2. `SW-D1` transmits BPDUs with Priority 4106 ($4096 + 10$). Because $4106 < 8202$, access switches immediately re-select `SW-D1` as Root Bridge.

---

## 7. Failure Scenario 5: Server Farm Switch Uplink Failure

### 7.1 Objective & Physical Action
Simulate severing the primary distribution uplink connecting the mission-critical Server Farm access switch (`SW-A5`) to `SW-D1`. The server farm hosts Central EHR, Telemetry Collector, DNS, and DHCP.
- **Packet Tracer Action:** Delete the cable between `SW-A5:Gi0/1` and `SW-D1:Fa0/5` (or shutdown `SW-A5:Gi0/1`).
  ```ios
  SW-A5# configure terminal
  SW-A5(config)# interface GigabitEthernet0/1
  SW-A5(config-if)# shutdown
  ```

### 7.2 Protocols Expected to Respond
1. **Rapid-PVST+ (802.1w):** Under normal operations, `SW-A5:Gi0/1` is `Root Forwarding` to `SW-D1`. `SW-A5:Gi0/2` is an `Alternate Blocking` port to `SW-D2`.
2. Carrier loss on Gi0/1 immediately activates the RSTP Alternate Port mechanism on Gi0/2.
3. Gi0/2 transitions from `BLK` $\rightarrow$ `FWD` instantaneously.
4. MAC address tables on `SW-D2` update via Topology Change Notification (TCN).

### 7.3 Theoretical vs Packet Tracer Expectations
- **Theoretical Failover Duration:** $\le 0.50\text{ seconds}$ (RSTP Alternate Port fast cutover).
- **Ping Command:** Execute from `ICU-PC1` (`172.16.8.40`) to Central EHR Server (`172.16.5.10`):
  ```cmd
  ping -n 30 172.16.5.10
  ```
- **Expected Loss:** **0 to 1 dropped ping**.
- **Clinical SLA Impact:** **OPTIMAL ($< 0.5\text{s} \ll 3.0\text{s}$)**. Completely transparent to clinical monitoring stations.

### 7.4 Verification Commands
#### On Server Farm Switch SW-A5:
```ios
SW-A5# show spanning-tree vlan 50
VLAN0050
  Spanning tree enabled protocol rstp
  Root ID    Priority    4146
             Address     0060.70aa.bb01
             Cost        4
             Port        2 (GigabitEthernet0/2)
Interface        Role Sts Cost      Prio.Nbr Type
---------------- ---- --- --------- -------- --------------------------------
Gi0/2            Root FWD 4         128.2    P2p
Fa0/1            Desg FWD 19        128.1    P2p Edge
Fa0/2            Desg FWD 19        128.2    P2p Edge
```
*Verification Confirmation:* `Gi0/2` transitioned from `Altn BLK` to `Root FWD`.

#### On SW-D2:
```ios
SW-D2# show mac address-table vlan 50
          Mac Address Table
-------------------------------------------
Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
  50    0001.9654.1201    DYNAMIC     Gi0/3
  50    0001.9654.1202    DYNAMIC     Gi0/3
```
*Verification Confirmation:* Server MAC addresses are dynamically learned across the alternate uplink.

### 7.5 Recovery Procedure
1. Re-enable primary uplink: On `SW-A5:Gi0/1`, issue `no shutdown`.
2. RSTP negotiates Gi0/1 back to Root Forwarding; Gi0/2 returns to Alternate Blocking.

---

## 8. Failure Scenario 6: Remote Clinic Gateway Failure

### 8.1 Objective & Physical Action
Simulate hardware crash or uplink disconnection on the Remote Clinic Distribution Gateway (`SW-D3`), isolating the remote branch clinic from local inter-VLAN routing and WAN access.
- **Packet Tracer Action:** Click `SW-D3` $\rightarrow$ Physical tab $\rightarrow$ Power switch to **OFF**, or shutdown the routed uplink to R2:
  ```ios
  SW-D3# configure terminal
  SW-D3(config)# interface GigabitEthernet0/1
  SW-D3(config-if)# shutdown
  ```

### 8.2 Protocols Expected to Respond
1. **HA Redundancy Mode (`SW-D3` + `SW-D4` deployed):**
   - `SW-D4` detects loss of HSRP hellos from `SW-D3` on the clinic distribution trunk.
   - `SW-D4` transitions from `Standby` $\rightarrow$ `Active` on Clinic VLANs 10, 30, 40, 60.
   - `SW-D4` advertises its local SVI subnets to `R2` across its own routed uplink `Gi0/1` (`172.16.8.112/30`).
2. **Standalone Mode (`SW-D3` single switch):**
   - Total clinic outage until physical recovery. (Validates requirement for HA Extension in high-risk regional clinics).

### 8.3 Theoretical vs Packet Tracer Expectations
- **Theoretical Failover Duration (HA Mode):** $10.00\text{ seconds}$ (HSRP hold timer) or $1.00\text{ second}$ (OSPF uplink reroute).
- **Ping Command:** Execute from Remote Clinic Triage PC (`172.16.8.45`) to Central EHR Server (`172.16.5.10`):
  ```cmd
  ping -n 60 172.16.5.10
  ```
- **Expected Loss (HA Mode):** 9 to 11 dropped pings (HSRP failover).
- **Clinical SLA Impact:** **DEGRADED (10s > 3s)**. Patient telemetry encounters brief loss; SBC frame buffer absorbs loss.

### 8.4 Verification Commands
#### On Clinic HA Switch SW-D4:
```ios
SW-D4# show standby brief
Interface   Grp  Pri P State   Active          Standby         Virtual IP
Vl10        10   110 P Active  local           unknown         172.16.8.33
Vl40        40   110 P Active  local           unknown         172.16.6.129
Vl60        60   110 P Active  local           unknown         172.16.7.225
```
*Verification Confirmation:* `SW-D4` successfully assumes active default gateway duty for all clinic VLANs.

#### On Remote Router R2:
```ios
R2# show ip route ospf
O        172.16.6.128/25 [110/2] via 172.16.8.114, 00:00:12, GigabitEthernet0/2
```
*Verification Confirmation:* Route points to SW-D4's routed link interface.

### 8.5 Recovery Procedure
1. Power on `SW-D3` (or issue `no shutdown` on `Gi0/1`).
2. `SW-D3` boots; HSRP priority 120 preempts `SW-D4` (priority 110).
3. Primary gateway state restored.

---

## 9. Comprehensive Failover Results & Verification Recording Table

Use this master recording sheet during live test execution in Cisco Packet Tracer:

| Scenario # | Failure Scenario Description | Primary Protocol | Theoretical Failover ($T_{\text{theo}}$) | Observed Failover ($T_{\text{obs}}$) | Pings Lost ($N_{\text{drop}}$) | Target Destination Tested | 3.0s SLA Status | Verified By |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **SC-01** | SW-D1 Power Off (Dist Switch Crash) | HSRP / RSTP | 10.00 s | *[Record s]* | *[Record #]* | `172.16.5.10` (Central EHR) | DEGRADED | Engineer |
| **SC-02** | SW-D1 to R1 Core Uplink Severed | OSPFv2 | 0.50 - 1.00 s | *[Record s]* | *[Record #]* | `172.16.8.106` (R1 Lo0) | **PASS** | Engineer |
| **SC-03** | Primary Serial WAN Link R1-R2 Cut | OSPFv2 | 1.00 - 2.00 s | *[Record s]* | *[Record #]* | `172.16.5.10` (Main EHR) | **PASS** | Engineer |
| **SC-04** | STP Root Bridge Trunk Drop (SW-D1) | Rapid-PVST+ | 1.00 - 2.00 s | *[Record s]* | *[Record #]* | `172.16.8.33` (Gateway VIP) | **PASS** | Engineer |
| **SC-05** | Server Farm Uplink Cut (SW-A5 Gi0/1)| RSTP (802.1w) | 0.05 - 0.50 s | *[Record s]* | *[Record #]* | `172.16.5.10` (Central EHR) | **PASS** | Engineer |
| **SC-06** | Remote Clinic Gateway Crash (SW-D3) | HSRP (HA Mode)| 10.00 s | *[Record s]* | *[Record #]* | `172.16.5.10` (Central EHR) | DEGRADED | Engineer |

---

## 10. Viva & Review Discussion Points

1. **Why does Scenario 5 achieve sub-second convergence while Scenario 1 takes 10 seconds?**
   - *Answer:* Scenario 5 triggers Rapid-PVST+ Alternate Port cutover. Because the alternate port is already pre-computed in hardware as a loop-free backup, it unblocks immediately upon carrier loss without running any timer. Scenario 1 relies on HSRP default timers (Hello=3s, Hold=10s). The standby switch cannot assume the active role until 10 full seconds of missed hellos have elapsed.
2. **How can the hospital network achieve $< 1.0\text{ second}$ failover on Scenario 1?**
   - *Answer:* By tuning HSRP timers to sub-second values (`standby 10 timers msec 250 msec 750`) or deploying Bidirectional Forwarding Detection (BFD). In hardware Cisco Catalyst switches, this reduces outage to $< 750\text{ ms}$, fully complying with the 3.0s telemetry SLA.
