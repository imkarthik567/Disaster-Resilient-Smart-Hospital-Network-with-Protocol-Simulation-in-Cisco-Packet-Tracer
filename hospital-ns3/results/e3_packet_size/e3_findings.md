# Experiment E3 Findings: Packet Sizing, Protocol Overhead & Queuing Divergence

**Project:** Disaster-Resilient Smart Hospital Network (NS-3 Discrete-Event Phase)  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  
**Course:** CSE2004 Computer Networks, SCOPE, VIT Vellore  

---

## 1. Theoretical Model: Header Sizes & Channel Serialization

On the 2.0 Mbps Primary WAN point-to-point link ($R = 2.0\text{ Mbps} = 2 \times 10^6\text{ bps}$, $T_{\text{prop}} = 10\text{ ms}$), total frame encapsulation headers comprise:
- **L2 Framing (PPP):** $2\text{ bytes}$
- **L3 Network (IPv4):** $20\text{ bytes}$
- **L4 Transport (UDP):** $8\text{ bytes}$ $\implies H_{\text{UDP}} = 30\text{ bytes}$
- **L4 Transport (TCP):** $20\text{ bytes}$ $\implies H_{\text{TCP}} = 42\text{ bytes}$

### Mathematical Formulations:
1. **Protocol Efficiency ($\eta$):**
   $$\eta = \frac{S_{\text{payload}}}{S_{\text{payload}} + H_{\text{headers}}}$$
2. **Header Overhead Fraction ($OH$):**
   $$OH = \frac{H_{\text{headers}}}{S_{\text{payload}} + H_{\text{headers}}} = 1 - \eta$$
3. **Theoretical Transmission Delay ($T_{\text{tx}}$):**
   $$T_{\text{tx}} = \frac{(S_{\text{payload}} + H_{\text{headers}}) \times 8}{R}$$
4. **Total Theoretical Unloaded One-Way Latency ($D_{\text{theory}}$):**
   $$D_{\text{theory}} = T_{\text{prop}} + T_{\text{tx}} = 10.0\text{ ms} + \frac{(S_{\text{payload}} + H_{\text{headers}}) \times 8}{2000}\text{ ms}$$

---

## 2. Quantitative Comparison Table Across Packet Sizes (UDP Telemetry)

| Packet Size (Bytes) | Header Overhead (%) | Efficiency (%) | Theoretical Delay ($D_{\text{theory}}$) | Light Load Delay (30%) | Near Saturation Delay (90%) | Overloaded Delay (120%) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **64 B** | 31.91% | 68.09% | 10.38 ms | 10.65 ± 0.05 ms | 19.82 ± 0.45 ms | 78.42 ± 2.21 ms |
| **128 B** | 18.99% | 81.01% | 10.63 ms | 10.88 ± 0.04 ms | 20.85 ± 0.42 ms | 86.51 ± 2.34 ms |
| **200 B (ICU)** | **13.04%** | **86.96%** | **10.92 ms** | **11.18 ± 0.05 ms** | **21.95 ± 0.44 ms** | **94.80 ± 2.50 ms** |
| **256 B** | 10.49% | 89.51% | 11.14 ms | 11.41 ± 0.05 ms | 22.82 ± 0.46 ms | 101.40 ± 2.65 ms |
| **512 B** | 5.54% | 94.46% | 12.17 ms | 12.42 ± 0.04 ms | 26.54 ± 0.51 ms | 132.85 ± 3.12 ms |
| **1024 B** | 2.85% | 97.15% | 14.22 ms | 14.48 ± 0.05 ms | 34.62 ± 0.62 ms | 195.40 ± 4.10 ms |
| **1460 B** | 2.01% | 97.99% | 15.96 ms | 16.21 ± 0.04 ms | 41.50 ± 0.75 ms | 248.65 ± 4.85 ms |

---

## 3. Where and Why Measured Delay Diverges from Theory

Refer to [`e3_delay_vs_size.png`](e3_delay_vs_size.png):

### 3.1. Under Light Load (30% WAN):
- Measured end-to-end latency tracks the theoretical curve $D_{\text{theory}} = 10\text{ ms} + \frac{(S+H)\times 8}{2000}$ almost perfectly across all packet sizes (divergence is less than $0.3\text{ ms}$).
- **Reason:** At $30\%$ link utilization, the average queue length $\bar{Q} \approx 0$. Packets arrive at an idle interface and are serialized onto the wire immediately without queuing delay ($D_{\text{queue}} \approx 0$).

### 3.2. Under Near Saturation (90% WAN) and Overloaded (120% WAN):
- As utilization $\rho \to 1.0$, measured latency diverges exponentially from the theoretical transmission line:
  - For $64\text{ B}$, delay rises from $10.38\text{ ms}$ (theory) to **$78.42\text{ ms}$** ($7.5\times$ increase).
  - For $1460\text{ B}$, delay rises from $15.96\text{ ms}$ (theory) to **$248.65\text{ ms}$** ($15.6\times$ increase).
- **Mathematical Root Cause (Queuing Theory):**
  From the Pollaczek-Khinchine / M/M/1 queue model, average queuing delay is given by:
  $$W_q = \frac{\rho}{\mu (1 - \rho)}$$
  As offered load approaches link capacity ($\rho \to 1$), the denominator $(1 - \rho) \to 0$, causing queue occupancy and waiting time to diverge asymptotically.
- **Packet Size Magnification Effect:**
  While smaller packets suffer higher header overhead, larger packets ($1460\text{ B}$) take longer to serialize ($T_{\text{tx}} = 5.96\text{ ms}$ per packet). When a queue of 50 packets forms, each queued $1460\text{ B}$ packet delays every subsequent arrival by $5.96\text{ ms}$, creating an aggregate drain time of $50 \times 5.96\text{ ms} \approx 300\text{ ms}$!

---

## 4. Engineering Design Recommendation: Optimal Packet Size for ICU Telemetry

### The Dilemma:
1. **Tiny Packets (64 Bytes):**
   - High serialization speed ($T_{\text{tx}} = 0.38\text{ ms}$), but **severe header overhead ($31.91\%$)**. Transporting $160\text{ kbps}$ of telemetry requires $235\text{ kbps}$ on the wire, wasting nearly a quarter of a megabit of precious WAN bandwidth.
2. **Maximum MTU Packets (1460 Bytes):**
   - Superb protocol efficiency ($97.99\%$). However, an IoT medical sensor sampling an ECG signal at $100\text{ Hz}$ ($1600\text{ bps} = 200\text{ bytes/s}$) would have to wait **7.3 seconds** just to accumulate enough physiological samples to fill a single $1460\text{ B}$ frame! This introduces an unacceptable **7300 ms packetization delay**, directly violating the 3000 ms clinical SLA. Furthermore, losing a single $1460\text{ B}$ frame loses over 7 seconds of patient cardiac history.

### The Recommendation: **200 to 256 Bytes**
For our Disaster-Resilient Smart Hospital Network, bedside ICU telemetry nodes must configure a payload size of **200 to 256 Bytes**:
1. **Protocol Efficiency:** Delivers **$86.96\% - 89.51\%$ efficiency** ($< 13\%$ header overhead), preserving WAN bandwidth.
2. **Clinical Packetization Latency:** At $100\text{ Hz}$ multi-lead ECG sampling, a $200\text{ B}$ payload is filled every **$1.0\text{ second}$**, perfectly balancing fresh alarm updates with low network chatter.
3. **Low Serialization Delay:** Transmission time on the $2.0\text{ Mbps}$ WAN is only **$0.92\text{ ms}$**, ensuring that even when telemetry packets arrive at the distribution switch, they cause negligible head-of-line blocking for concurrent clinical voice packets ($160\text{ B}$).
4. **Packet Tracer SBC Alignment:** Exactly matches the frame structure implemented in our Python SBC sensor scripts (`sbc/medical_sensor_app.py`), maintaining 100% design consistency across Cisco Packet Tracer and NS-3.
