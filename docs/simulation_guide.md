# Packet Tracer Simulation Mode Protocol Analysis Guide

**Project:** Disaster-Resilient Smart Hospital Network  
**Course:** Computer Networks — VIT Vellore, SCOPE  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  
**Environment:** Cisco Packet Tracer 8.x Simulation Mode & PDU Envelope Inspector

---

## 1. Overview of Simulation Mode Setup

Packet Tracer's **Simulation Mode** allows step-by-step PDU (Protocol Data Unit) tracing across the network fabric. Instead of packets traveling instantaneously as in Realtime Mode, Simulation Mode captures each frame at every OSI layer on each hop.

### Accessing Simulation Mode:
1. In the bottom-right corner of Packet Tracer, click the **Simulation** tab (or press `Shift + S`).
2. In the **Event List Filters**, click **Show None**, then click **Edit Filters**.
3. Under the **IPv4** tab, select:
   - `ICMP`
   - `OSPF`
   - `EIGRP`
4. Under the **Misc** tab, select:
   - `DNS`
   - `HTTP`
   - `TCP`
   - `UDP`

---

## 2. Experiment 1: DNS Resolution of Internal Hospital Portals

### Objective:
Verify name resolution of `records.hospital.local` to `172.16.4.2` using UDP transport across VLAN boundaries.

### Procedure:
1. Open any workstation in the hospital (e.g., Admin PC in VLAN 30, `172.16.2.10`).
2. Open **Command Prompt** and enter:
   ```cmd
   nslookup records.hospital.local
   ```
3. In the Simulation Panel, click the **Capture / Forward** button step-by-step.

### PDU Inspection Points:
* **Outbound PDU at Admin PC:**
  - **OSI Layer 7:** DNS Query formatted for `records.hospital.local`, Type A, Class IN.
  - **OSI Layer 4 (UDP):** Source Port = Ephemeral (e.g. `1025`), Destination Port = `53`.
  - **OSI Layer 3 (IP):** Source IP = `172.16.2.10`, Destination IP = `172.16.4.2` (Central DNS Server).
  - **OSI Layer 2 (Ethernet II):** Destination MAC = Default Gateway (SW-D2 SVI Vlan30 MAC).
* **Inter-Distribution Routing at SW-D2 & SW-D1:**
  - Observe SW-D2 forwarding the packet across the 802.1Q trunk link to SW-D1.
* **Inbound & Outbound PDU at Central Server (172.16.4.2):**
  - Layer 7 DNS Engine matches the record and constructs the DNS Answer: `records.hospital.local -> 172.16.4.2`.
  - UDP reply dispatched back to client port `1025`.

---

## 3. Experiment 2: TCP Three-Way Handshake & EHR Web Portal Access

### Objective:
Inspect TCP connection establishment, sequence number synchronisation, window sizing, and teardown during EHR portal access.

### Procedure:
1. From Admin PC (`172.16.2.10`), open the **Web Browser**.
2. Type `http://records.hospital.local` and press **Go**.
3. Step forward through the packet events in Simulation Mode.

### Step-by-Step Packet Trace:

| Step | PDU Type | Source IP | Destination IP | Flags / Header Details | Observation |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | TCP | `172.16.2.10` | `172.16.4.2` | `SYN`, Seq = `0`, Win = `16384` | Client initiates connection; advertises receive window. |
| **2** | TCP | `172.16.4.2` | `172.16.2.10` | `SYN + ACK`, Seq = `0`, Ack = `1` | Server acknowledges client's SYN and sends its own SYN. |
| **3** | TCP | `172.16.2.10` | `172.16.4.2` | `ACK`, Seq = `1`, Ack = `1` | Client acknowledges server's SYN. Handshake complete! |
| **4** | HTTP | `172.16.2.10` | `172.16.4.2` | `GET / HTTP/1.1` | Application layer HTTP request transmitted over TCP socket. |
| **5** | HTTP | `172.16.4.2` | `172.16.2.10` | `HTTP/1.1 200 OK` | Server returns clinical dashboard HTML payload. |
| **6** | TCP | `172.16.2.10` | `172.16.4.2` | `ACK`, Seq = `103`, Ack = `472` | Client confirms receipt of HTML data payload. |

---

## 4. Experiment 3: Telemetry Streaming (UDP) vs. Medical Imaging (TCP)

### Objective:
Contrast UDP stream characteristics for bedside IoT telemetry against TCP bulk transfers for MRI/CT imaging, verifying QoS marking.

| Protocol Characteristic | Bedside Telemetry / VoIP | PACS MRI / CT Imaging |
| :--- | :--- | :--- |
| **Transport Protocol** | **UDP** | **TCP** |
| **Target Port** | UDP 5004 / 514 | TCP 104 (DICOM) / 80 / 443 |
| **Connection Overhead** | None (0 ms setup latency) | 3-Way Handshake required |
| **Flow & Error Control** | None (best for real-time streams) | Sliding Window + Cumulative ACK |
| **QoS Marking (IP Precedence / DSCP)** | **DSCP EF (Expedited Forwarding - 46)** | **DSCP AF31 (Assured Forwarding - 26)** |
| **Packet Inspection in PT** | Click PDU -> Inbound/Outbound PDU Details -> IP Header -> **TOS / DSCP Field** displays `0xB8` (EF). | IP Header TOS/DSCP displays `0x68` (AF31). |

---

## 5. Experiment 4: Multi-Area OSPF Reconvergence & Standby EIGRP Failover

### Objective:
Deliberately cut the primary inter-site WAN serial link and record convergence duration, routing table updates, and packet rerouting onto the secondary link.

### Test Procedure:
1. Open a command prompt on **Remote Clinic PC** (`172.16.4.100`) and initiate a continuous ping to Main Hospital Server:
   ```cmd
   ping 172.16.4.2 -t
   ```
2. Verify ICMP replies are succeeding via primary link (`Serial0/0/0`).
3. On **Core Router R1**, enter global configuration and sever the primary WAN link:
   ```cisco
   R1# configure terminal
   R1(config)# interface Serial0/0/0
   R1(config-if)# shutdown
   ```
4. Observe the continuous ping output:
   - Notice the brief burst of `Request timed out` messages during reconvergence.
5. In Simulation Mode, filter for `OSPF` and `EIGRP`:
   - Observe OSPF adjacency loss: Dead timer expires on R1/R2 for neighbor `172.16.4.193` / `172.16.4.194`.
   - Observe EIGRP topology table: EIGRP AS 100 route (AD 120) is immediately installed in the routing table on R1 and R2.
   - Pings resume successfully across `Serial0/0/1`!
6. Measure convergence time:
   $$\text{Convergence Time} = \text{Lost Pings} \times 1.0\text{ second}$$
   *(Typically 3–5 seconds when dead timers or interface down events trigger).*
7. Restore the primary link:
   ```cisco
   R1(config-if)# no shutdown
   ```
8. OSPF adjacencies re-establish; OSPF (AD 110) replaces EIGRP (AD 120) in the RIB with zero packet loss.

---

## 6. Experiment 5: Guest VLAN Isolation ACL Enforcement

### Objective:
Validate that Guest Wi-Fi clients (VLAN 40) are strictly blocked from accessing ICU medical devices (VLAN 10) and Server Farm (VLAN 50), while retaining full outbound Internet access.

### Test Scenarios:

#### Test A: Guest to ICU Medical Sensor (Blocked)
1. On Guest PC (`172.16.0.10`), ping an ICU bedside sensor:
   ```cmd
   ping 172.16.3.135
   ```
2. **Result:** `Destination host unreachable` or `Request timed out`.
3. In Simulation Mode:
   - Trace the ICMP packet reaching **SW-D2**.
   - Open the PDU envelope on SW-D2:
     - Layer 3 indicates: **"The packet matches the criteria of the input access list: BLOCK-GUEST. The switch drops the packet."**
   - The PDU envelope shows a red `X` and is discarded.

#### Test B: Verify ACL Drop Counters on Switch
On **SW-D2** CLI:
```cisco
SW-D2# show access-lists BLOCK-GUEST
```
**Expected Output:**
```text
Extended IP access list BLOCK-GUEST
    10 permit udp 172.16.0.0 0.0.1.255 host 172.16.4.2 eq domain (12 matches)
    20 permit udp 172.16.0.0 0.0.1.255 host 172.16.4.2 eq bootps (4 matches)
    30 deny ip 172.16.0.0 0.0.1.255 172.16.3.128 0.0.0.63 (4 matches)  <-- DENIED!
    40 deny ip 172.16.0.0 0.0.1.255 172.16.3.192 0.0.0.63
    50 deny ip 172.16.0.0 0.0.1.255 172.16.4.0 0.0.0.31 (4 matches)    <-- DENIED!
    60 permit ip 172.16.0.0 0.0.1.255 any (38 matches)
```
*The counter confirms active security policy enforcement at the distribution tier.*
