# `/sbc` Directory: Embedded Single Board Computer Software Suite

**Project:** Disaster-Resilient Smart Hospital Network with Protocol Simulation in Cisco Packet Tracer  
**Institution:** VIT Vellore — School of Computer Science and Engineering (SCOPE)  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  
**Target Platform:** Cisco Packet Tracer 8.x Single Board Computer (SBC-PT) & Desktop Simulation  

---

## 1. Directory Overview & Architecture

This directory contains pure-Python (zero non-builtin dependencies) modules designed to execute natively within Cisco Packet Tracer's embedded Single Board Computer (`SBC-PT`) and Microcontroller (`MCU-PT`) execution environments, as well as on standard development workstations.

```
+----------------------------------------------------------------------------------------------------+
|                                    SBC SOFTWARE STACK ARCHITECTURE                                 |
|                                                                                                    |
|   +--------------------------------------------------------------------------------------------+   |
|   | APPLICATION LAYER:                                                                         |   |
|   | - sensor_node.py : Bedside Patient Monitor (HR, SpO2, Temp, Patient ID)                    |   |
|   | - alarm.py       : Emergency Threshold Engine & QoS Class C1 (DSCP EF) Marker              |   |
|   | - gateway.py     : Clinical Telemetry Ingestion, Validation & Records Forwarder            |   |
|   +--------------------------------------------------------------------------------------------+   |
|                                                |                                                   |
|   +--------------------------------------------v-----------------------------------------------+   |
|   | TRANSPORT & DATA-LINK PROTOCOLS:                                                           |   |
|   | - arq.py         : Stop-and-Wait, Go-Back-N, and Selective Repeat State Machines          |   |
|   | - errdetect.py   : Single Parity, 2D Parity (1-bit Self-Healing), Checksum16, CRC-16/32    |   |
|   +--------------------------------------------------------------------------------------------+   |
|                                                |                                                   |
|   +--------------------------------------------v-----------------------------------------------+   |
|   | HARDWARE & ENVIRONMENT ADAPTERS:                                                           |   |
|   | - adapter_pt.py  : Packet Tracer GPIO Pin Interface & Non-Blocking UDP Network Stack       |   |
|   | - probe.py       : Diagnostic Runtime Environment Discovery & Capabilities Inspector       |   |
|   | - ENVIRONMENT.md : Formal Packet Tracer Python Sandbox Specification & Constraints         |   |
|   +--------------------------------------------------------------------------------------------+   |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. SBC Device Deployment Matrix

The table below lists every programmable SBC node in the hospital network topology, which script to deploy, what the file must be named inside Packet Tracer's code editor, and the startup parameters to edit:

| Device Name in PT | Physical Location & VLAN | IP Address & Port | Script to Load | File Name in PT | Startup Parameters to Edit |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`SBC-ICU-101`** | Intensive Care Unit (VLAN 10, Port Fa0/4 on SW-A1) | `172.16.7.138:5005` (Gateway: `172.16.7.129`) | [`sensor_node.py`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/sbc/sensor_node.py) | `main.py` | `NODE_ID = "SBC-ICU-101"`<br>`PATIENT_ID = "ICU-101"`<br>`GATEWAY_IP = "172.16.7.195"`<br>`GATEWAY_PORT = 5005`<br>`CHECK_SCHEME = CHECK_CRC16`<br>`SAMPLE_INTERVAL = 1.0` |
| **`SBC-SURG-102`** | Operating Theater (VLAN 20, Port Fa0/3 on SW-A2) | `172.16.7.168:5005` (Gateway: `172.16.7.161`) | [`sensor_node.py`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/sbc/sensor_node.py) | `main.py` | `NODE_ID = "SBC-SURG-102"`<br>`PATIENT_ID = "SURG-102"`<br>`GATEWAY_IP = "172.16.7.195"`<br>`GATEWAY_PORT = 5005`<br>`CHECK_SCHEME = CHECK_2D_PARITY`<br>`SAMPLE_INTERVAL = 0.5` |
| **`SBC-CLINIC-201`** | Remote Outpatient Clinic (VLAN 60, Port Fa0/2 on SW-A4) | `172.16.7.202:5005` (Gateway: `172.16.7.201`) | [`gateway.py`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/sbc/gateway.py) | `main.py` | `NODE_ID = "SBC-CLINIC-201"`<br>`BIND_PORT = 5005`<br>`RECORDS_SERVER_IP = "172.16.7.195"`<br>`RECORDS_SERVER_PORT = 5006`<br>`FORWARD_INTERVAL = 5.0` |
| **`Server-EHR`** | Server Farm (VLAN 50, Port Fa0/2 on SW-A3) | `172.16.7.195:5006` (Gateway: `172.16.7.193`) | [`gateway.py`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/sbc/gateway.py) or [`adapter_pt.py`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/sbc/adapter_pt.py) | `main.py` | `NODE_ID = "EHR-CENTRAL-01"`<br>`BIND_PORT = 5006`<br>`ROLE = "RECEIVER"` |

---

## 3. Step-by-Step Instructions: Loading Code into Packet Tracer SBCs

Follow these exact steps for each SBC device in your Packet Tracer `.pkt` file:

1. **Open the Device**: Click on the target SBC device on the workspace canvas (e.g. `SBC-ICU-101`).
2. **Access the Programming Tab**: Click the **Programming** tab in the top navigation bar of the device dialog.
3. **Create a New Project**:
   - Click the **New** button.
   - Enter Project Name: `TelemetryApp` (or `GatewayApp`).
   - Select Template: **Empty - Python**.
   - Click **Create**.
4. **Load the Source Code**:
   - In the project file tree on the left, click **`main.py`** to open the built-in Python editor.
   - Delete any default boilerplate text.
   - Copy the entire source code of the appropriate script:
     - For `SBC-ICU-101`: paste [`sbc/sensor_node.py`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/sbc/sensor_node.py).
     - For `SBC-CLINIC-201`: paste [`sbc/gateway.py`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/sbc/gateway.py).
   - If using helper libraries, also click **New File**, create `errdetect.py`, `alarm.py`, and `arq.py`, and paste their respective code into the same project folder.
5. **Adjust Startup Parameters**:
   - Edit the IP addresses, patient ID, and sensor intervals near the top of `main.py` as detailed in the matrix above.
6. **Launch the Application**:
   - Click the green **Run** button at the top of the editor.
   - View live telemetry events, CSV logs, and emergency alarms in the **Run Console** pane at the bottom.

---

## 4. Hardware Pin Interfacing Guide

On the `SBC-PT`, physical sensors and actuators connect to the 10-pin header:

* **Pin A0 (Analog Input)**: Patient ECG Heart Rate sensor ($0–1023 \rightarrow 40–180\text{ BPM}$).
* **Pin A1 (Analog Input)**: Pulse Oximeter sensor ($0–1023 \rightarrow 70–100\%\text{ SpO}_2$).
* **Pin D0 (Digital Input)**: Bedside Emergency Nurse Call button (normally `LOW`, pulls `HIGH` when pressed).
* **Pin D1 (Digital Output)**: Critical Cardiac Alarm Buzzer/Siren (`HIGH` activates buzzer).
* **Pin D2 (Digital Output)**: Visual Alert Red Flashing LED (`HIGH` illuminates LED).

---

## 5. Uniform CSV Log Format

Every node writes a consistent CSV log line per event with a local timestamp:
```text
TIMESTAMP,NODE_ID,EVENT_TYPE,SEQ_NUM,PATIENT_ID,VITALS,STATUS,DETAIL
```
* **Routine Telemetry Example**:
  `2026-10-14T23:24:51,SBC-ICU-101,ROUTINE_TELEMETRY,0,ICU-101,HR=76;SPO2=98.5;TEMP=37.0,NORMAL_BE,NORMAL: Stable Hemodynamics`
* **Emergency Alarm Example**:
  `2026-10-14T23:24:51,SBC-ICU-101,EMERGENCY_ALARM,5,ICU-101,HR=38;SPO2=84.8;TEMP=39.6,CRITICAL_C1,QoS_TOS=0xB8;EMERGENCY: Bedside Nurse Call Button Pressed`
* **Gateway Ingestion Example**:
  `2026-10-14T23:26:06,GATEWAY-SBC-01,TELEMETRY_INGESTED,0,ICU-101,HR=72.0;SPO2=99.0;TEMP=37.0,VALID_OK,Clean (CRC-16 verified)`
* **Self-Healing Example**:
  `2026-10-14T23:26:06,GATEWAY-SBC-01,TELEMETRY_INGESTED,4,ICU-101,HR=76.0;SPO2=98.5;TEMP=37.0,HEALED_OK,Single-bit error self-healed at Row 24 Col 3`

---

## 6. Patient Log Bulk Transfer Mode (GBN vs. Selective Repeat)

To run a comparative bulk patient log transfer between `SBC-ICU-101` and the Gateway:
```powershell
# Run benchmark sweep from host terminal
python sim/benchmark_harness.py
```
Or trigger directly within `sensor_node.py`:
```python
node = BedsideSensorNode(node_id="SBC-ICU-101", patient_id="ICU-101")
# Runs 50 records under 10% loss
m_gbn, _ = node.run_patient_log_transfer("GBN", total_records=50, loss_rate=0.10)
m_sr, _  = node.run_patient_log_transfer("SR", total_records=50, loss_rate=0.10)
```
Expected performance under 10% channel packet loss:
* **Go-Back-N**: Efficiency ~61%, Retransmissions: ~32 frames (due to full window rollback).
* **Selective Repeat**: Efficiency ~81%, Retransmissions: ~12 frames (**zero redundant frame resends**).
