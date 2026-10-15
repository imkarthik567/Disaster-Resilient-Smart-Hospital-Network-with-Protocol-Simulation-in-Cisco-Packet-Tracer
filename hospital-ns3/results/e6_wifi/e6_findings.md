# Experiment E6 Findings: Hospital Wi-Fi Capacity, Hidden Terminal, Mobility & Fading

**Project:** Disaster-Resilient Smart Hospital Network (NS-3 Discrete-Event Phase)  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  
**Course:** CSE2004 Computer Networks, SCOPE, VIT Vellore  

---

## 1. Executive Summary & Clinical Context
Hospital wireless networks must support two fundamentally conflicting user groups:
1. **Clinical Healthcare Staff (Nurse Tablets & Mobile Infusion Pumps):** Low-latency, mission-critical vital sign telemetry and EHR updates across VLAN 50 / Subnet `172.16.5.0/24`.
2. **Untrusted Guest Visitors (Smartphones & Laptops):** High-bandwidth, best-effort media streaming and social browsing across VLAN 40 / Subnet `172.16.0.0/22`.

This experiment investigates IEEE 802.11n wireless local area network (WLAN) operation across four rigorous studies:
- **Study (a): Station Density Scalability ($5 \le N \le 50$ STAs):** Contention collapse and latency degradation.
- **Study (b): Hidden Terminal Problem & RTS/CTS Handshake:** Spatial collision dynamics.
- **Study (c): Mobile Nurse Tablets (RandomWaypoint, RandomWalk, GaussMarkov):** Velocity-induced packet drops.
- **Study (d): Multipath Channel Fading (Friis vs Nakagami-$m$):** Architectural obstruction modeling.

---

## 2. Quantitative Performance Table

| Study Scenario | Parameter / Configuration | Aggregate Throughput ($kbps$) | Per-Station Throughput ($kbps$) | P95 Latency ($ms$) | Packet Loss Ratio (%) | MAC Retries / Drops | Clinical Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Scalability (N=5)** | $N = 5$ STAs (Light Density) | **$22,140.5$** | **$4,428.1$** | **$2.45$** | **$0.00\%$** | $0$ | **EXCELLENT** |
| **Scalability (N=10)** | $N = 10$ STAs (Ward Baseline) | **$20,850.2$** | **$2,085.0$** | **$4.12$** | **$0.00\%$** | $0$ | **EXCELLENT** |
| **Scalability (N=20)** | $N = 20$ STAs (Moderate Density)| **$18,420.8$** | **$921.0$** | **$8.85$** | **$0.85\%$** | $68$ | **ACCEPTABLE** |
| **Scalability (N=30)** | $N = 30$ STAs (High Density) | **$16,510.4$** | **$550.3$** | **$16.40$** | **$2.25\%$** | $270$ | **DEGRADED** |
| **Scalability (N=50)** | $N = 50$ STAs (Contention Collapse)| **$13,780.1$** | **$275.6$** | **$42.15$** | **$5.80\%$** | $560$ | ❌ **UNACCEPTABLE** |
| **Hidden Terminal** | RTS/CTS Disabled ($Thr = 65535\text{B}$) | **$1,420.5$** | **$710.2$** | **$24.05$** | **$52.10\%$** | $480$ | ❌ **COLLISION COLLAPSE** |
| **Hidden Terminal** | RTS/CTS Enabled ($Thr = 100\text{B}$) | **$2,850.2$** | **$1,425.1$** | **$5.46$** | **$1.50\%$** | $8$ | **RESOLVED** (NAV Protected) |
| **Mobility (Walk)** | Gauss-Markov ($v = 1.0\text{ m/s}$) | **$17,120.4$** | **$1,141.3$** | **$2.85$** | **$1.20\%$** | $36$ | **EXCELLENT** |
| **Mobility (Trolley)**| Gauss-Markov ($v = 2.5\text{ m/s}$) | **$15,410.8$** | **$1,027.3$** | **$4.15$** | **$3.10\%$** | $93$ | **ACCEPTABLE** |
| **Mobility (Run)** | Gauss-Markov ($v = 5.0\text{ m/s}$) | **$13,180.2$** | **$878.6$** | **$6.25$** | **$6.20\%$** | $186$ | **DEGRADED** |
| **Fading (Friis)** | Line-of-Sight Free Space | **$22,400.1$** | **$1,493.3$** | **$2.59$** | **$0.50\%$** | $15$ | **OPTIMAL** |
| **Fading (Nakagami)** | Hospital Concrete Wall Fading | **$15,800.4$** | **$1,053.3$** | **$6.79$** | **$6.80\%$** | $204$ | **OBSTRUCTED** |

---

## 3. Deep Analysis of Experimental Studies

### 3.1. Study (a): Contention Collapse in Dense Hospital Wards
Refer to [`e6_station_count_scaling.png`](e6_station_count_scaling.png):
- In IEEE 802.11 CSMA/CA, every station listens before transmitting and uses binary exponential backoff ($CW_{\text{min}} = 15$ slots).
- As station count increases from $N = 5$ to $N = 50$:
  - The probability of two or more stations picking the same backoff slot rises exponentially:
    $$P_{\text{collision}} \approx 1 - \left(1 - \frac{2}{CW + 1}\right)^{N-1}$$
  - At $N = 50$, packet collision drops jump to **$560$ frames**, causing P95 latency to explode from $2.45\text{ ms}$ to **$42.15\text{ ms}$**, violating the clinical telemetry SLA ($20\text{ ms}$).

### 3.2. Study (b): Hidden Terminal Geometry & RTS/CTS Mitigation
Refer to [`e6_hidden_terminal_rts_cts.png`](e6_hidden_terminal_rts_cts.png):
- **Spatial Geometry:** AP is centered at $(0, 0)$. Nurse Tablet 1 is at $(-25, 0)$ and Nurse Tablet 2 is at $(+25, 0)$.
  - The physical distance between the two tablets is $d = 50\text{ m}$.
  - The Wi-Fi carrier sense threshold limits Clear Channel Assessment (CCA) to $R_{\text{CS}} \approx 35\text{ m}$.
  - Because $d > R_{\text{CS}}$, Station 1 and Station 2 cannot hear each other's transmissions; they are mutually "hidden". Both are within $25\text{ m} < R_{\text{COMM}}$ of the AP.
- **Without RTS/CTS:** Both stations sense the channel idle and transmit simultaneously. Collisions occur at the AP antenna for every concurrent transmission, driving packet loss to **$52.1\%$** and cutting effective throughput in half ($1420.5\text{ kbps}$).
- **With RTS/CTS Handshake ($Thr = 100\text{B}$):**
  - Station 1 sends a small 20-byte Request to Send (RTS).
  - AP broadcasts a 14-byte Clear to Send (CTS).
  - Crucially, Station 2 **hears the AP's CTS**, reads the duration field, and updates its Network Allocation Vector (NAV), freezing its virtual carrier-sense timer.
  - Collisions drop to **$1.5\%$**, and aggregate throughput nearly doubles to **$2850.2\text{ kbps}$**.

### 3.3. Study (c): Nurse Mobility Dynamics
Refer to [`e6_nurse_mobility_comparison.png`](e6_nurse_mobility_comparison.png):
- Compares three mobility models:
  1. **Random Waypoint:** Realistic for nurses moving between patient beds and pausing.
  2. **Random Walk:** Memoryless Brownian motion, producing erratic signal variation.
  3. **Gauss-Markov:** Correlated velocity vector ($\alpha = 0.85$), best representing purposeful hospital staff rounds.
- As nurse walking speed increases from $1.0\text{ m/s}$ (normal pace) to $5.0\text{ m/s}$ (emergency code blue sprint):
  - Fast movement causes rapid signal-to-noise ratio (SNR) fluctuations.
  - The 802.11 Minstrel/Ideal rate adaptation algorithm steps down Modulation and Coding Schemes (MCS), resulting in lower effective bitrate and higher packet loss ($1.2\% \to 6.2\%$).

### 3.4. Study (d): Impact of Hospital Multipath Fading
Refer to [`e6_channel_fading_comparison.png`](e6_channel_fading_comparison.png):
- Ideal Friis free-space assumes an unobstructed line of sight ($22.40\text{ Mbps}$).
- In real hospitals, reinforced concrete walls, lead-shielded radiology suites, and metallic medical equipment induce Rayleigh/Rician multipath fading modeled by the **Nakagami-$m$ distribution**.
- Deep fades cause instantaneous SNR drops below the receiver sensitivity threshold, reducing aggregate capacity by **$29.5\%$** ($15.80\text{ Mbps}$) and increasing latency to $6.79\text{ ms}$.

---

## 4. Architectural Design Recommendation: SSID & VLAN Separation
The findings of Experiment E6 provide quantitative proof for the Cisco Packet Tracer network architecture:
1. **Never Co-locate Guest and Clinical Wi-Fi on the Same BSSID/VLAN:**
   - As proven in Study (a), 30+ guest smartphones streaming video will drive the contention window into collision collapse, introducing $> 40\text{ ms}$ jitter into patient telemetry.
2. **SSID Segmentation with 802.11e WMM/EDCA Priorities:**
   - **SSID `Hospital-Clinical` (VLAN 50):** Configured with 802.11e Access Category Voice/Video (`AC_VO` / `AC_VI`), smaller Arbitration Inter-Frame Spacing (AIFS=2), and $CW_{\text{min}}=3$.
   - **SSID `Hospital-Guest` (VLAN 40):** Configured with Best Effort / Background (`AC_BE` / `AC_BK`), AIFS=7, and rate-limited at the distribution switch.

---

## 5. Simulation Limitations
1. **No 802.11k/v/r Fast BSS Transition:** This scenario models single-AP BSS coverage. In multi-AP enterprise deployments, roaming latency is governed by 802.1X re-authentication and 802.11r FT key exchange.
2. **No Medical RF Interference (2.4 GHz Diathermy):** Hospital electrosurgical units (ESU) and microwave sterilization equipment emit wideband non-Wi-Fi RF noise that is not modeled in standard YansWifiPhy.
