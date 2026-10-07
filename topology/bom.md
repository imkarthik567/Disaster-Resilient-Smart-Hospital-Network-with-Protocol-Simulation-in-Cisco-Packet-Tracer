# Device Bill of Materials (BOM) & Hardware Specifications

**Project:** Disaster-Resilient Smart Hospital Network  
**Platform:** Cisco Packet Tracer 8.x  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332) — VIT Vellore  
**Addressing Source:** [`/addressing/ip_table.csv`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/addressing/ip_table.csv)  
**Cabling Interconnects:** [`/topology/cabling.csv`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/topology/cabling.csv)  

---

## 1. Executive Summary & Hardware Scope

This document provides the definitive, production-grade Bill of Materials (BOM) and physical hardware configuration guide for the Disaster-Resilient Smart Hospital Network. Every device, expansion module, cable type, and power configuration is strictly validated against **Cisco Packet Tracer 8.x** hardware catalogs to guarantee zero compatibility or command-syntax errors during lab deployment and academic viva examination.

The physical architecture spans three operational domains:
1. **Main Hospital Campus:** Core Router R1, Distribution Switches SW-D1 & SW-D2, Access Switches SW-A1 through SW-A4, Central Server Farm, ICU and Surgery SBC IoT telemetry nodes, IP phones, and Guest Wi-Fi.
2. **Remote Spoke Clinic:** Core/ABR Router R2, Distribution Switch SW-D3, Access Switch SW-A5, Local Survivability Cache Server, clinical workstations, and Guest Wi-Fi.
3. **Internet Edge & WAN:** Dual Serial V.35 leased lines and a Gigabit transit link to the simulated Public ISP Gateway (`EDGE-ISP`).

---

## 2. Packet Tracer Device Models & Card Specifications

### 2.1 Core Routers (`R1`, `R2`, `EDGE-ISP`)
* **Chassis Model:** **Cisco 2911 Integrated Services Router (ISR G2)**
* **Onboard Interfaces:** 3x 10/100/1000 GigabitEthernet ports (`GigabitEthernet0/0`, `GigabitEthernet0/1`, `GigabitEthernet0/2`).
* **Expansion Slots:** 3x Enhanced High-Speed WAN Interface Card (EHWIC) slots.
* **WAN Interface Module:** **`HWIC-2T`** (2-Port Serial High-Speed WAN Interface Card).
* **Slot Assignment:** **Slot 0 (`EHWIC 0`)** on both `R1` and `R2`.
* **Interface Naming Result:** `Serial0/0/0` and `Serial0/0/1`.  
  *(Note: If installed in Slot 1, Cisco IOS names the ports `Serial0/1/0` and `Serial0/1/1`. Slot 0 is strictly mandatory to match all configuration scripts).*
* **Physical Installation Procedure (Packet Tracer 8.x):**
  > [!IMPORTANT]
  > **Cisco 2911 Power-Off Requirement:**  
  > 1. In Packet Tracer, click on the **R1** (or **R2**) router icon and select the **Physical** tab.
  > 2. Locate the green power rocker switch on the rear right panel and click it to **OFF** (the green LED turns off).
  > 3. In the left-hand *Modules* pane, select **HWIC-2T**.
  > 4. Drag the **HWIC-2T** module card into the bottom-right slot (**Slot 0 / EHWIC 0**).
  > 5. Click the rocker switch back to **ON** (green LED illuminates).
  > 6. Open the **CLI** tab and verify that the router boots and registers `Serial0/0/0` and `Serial0/0/1`.

```
+-------------------------------------------------------------------------+
|                  Cisco 2911 Rear Panel (Packet Tracer)                  |
|  [Power Switch: OFF -> Insert Module -> ON]                             |
|  +--------------------+ +--------------------+ +---------------------+  |
|  | Slot 2 (EHWIC 2)   | | Slot 1 (EHWIC 1)   | | Slot 0 (EHWIC 0)    |  |
|  |     [Empty]        | |     [Empty]        | |    >> HWIC-2T <<    |  |
|  +--------------------+ +--------------------+ +---------------------+  |
|  [Gi0/0] [Gi0/1] [Gi0/2]   [Console] [Aux]                              |
+-------------------------------------------------------------------------+
```

### 2.2 Multilayer Distribution Switches (`SW-D1`, `SW-D2`, `SW-D3`)
* **Primary Model:** **Cisco Catalyst 3560-24PS**
* **Port Density:**
  * 24x 10/100 FastEthernet PoE ports (`FastEthernet0/1` through `FastEthernet0/24`).
  * 2x 10/100/1000 GigabitEthernet uplink ports (`GigabitEthernet0/1` and `GigabitEthernet0/2`).
* **Power Supply:** Integrated internal AC power supply (powers on immediately upon dropping onto canvas in Packet Tracer).
* **Layer 3 Feature Set:**
  * Hardware wire-speed routing (`ip routing`).
  * Switch Virtual Interfaces (SVIs) for VLANs 10, 20, 30, 40, 50, 60, 99.
  * Hot Standby Router Protocol (**HSRP**) with preemption and priority tuning.
  * Routed point-to-point ports (`no switchport`) with `/30` subnets.
  * Dynamic routing protocols (**OSPFv2** Multi-Area and **EIGRP**).
  * Inbound SVI Extended Access Control Lists (ACLs).
  * IEEE 802.3ad Link Aggregation / EtherChannel (`channel-group mode on / desirable`).
* **Comparison with Catalyst 3650-24PS:**
  * The Catalyst 3650-24PS is also supported in PT 8.x, but requires manual insertion of AC power modules (`AC-Power-Supply`) before booting, and numbers interfaces in a 3-tier hierarchy (`GigabitEthernet1/0/1`–`24`). To maximize reliability and eliminate startup power failures during viva demonstrations, the **Catalyst 3560-24PS** is selected as the primary distribution switch.

### 2.3 Layer 2 Access Switches (`SW-A1` to `SW-A5`)
* **Model:** **Cisco Catalyst 2960-24TT**
* **Port Density:**
  * 24x 10/100 FastEthernet access ports (`FastEthernet0/1` through `FastEthernet0/24`).
  * 2x 10/100/1000 GigabitEthernet uplink ports (`GigabitEthernet0/1` and `GigabitEthernet0/2`).
* **Features Used:**
  * IEEE 802.1Q VLAN trunking on Gigabit uplinks.
  * Cisco Voice VLAN architecture (`switchport voice vlan 60`).
  * Spanning Tree Protocol (PVST+) with PortFast and BPDU Guard on all host ports.
  * Static In-Band Management SVI in VLAN 99.

### 2.4 Single Board Computers (`SBC-PT`)
* **Model:** **SBC-PT (Single Board Computer)**
* **Role:** Programmable IoT Medical Telemetry Sensor Nodes.
* **Onboard Interfaces:** 1x FastEthernet interface (`FastEthernet0`), analog/digital I/O pins.
* **Programming Environment:** Python interpreter embedded directly inside Packet Tracer.
* **Nodes Deployed:**
  * **ICU (VLAN 10):** 3 nodes (`SBC-ICU-101`, `SBC-ICU-102`, `SBC-ICU-103`).
  * **Surgery (VLAN 20):** 2 nodes (`SBC-SURG-201`, `SBC-SURG-202`).
* **Simulation Algorithms:** Custom Python scripts executing 2D Parity, 16-bit One's Complement Checksum, Go-Back-N (GBN) ARQ, and Selective Repeat (SR) ARQ.

### 2.5 Servers (`Server-PT`)
* **Model:** **Server-PT**
* **Network Interface:** 1x FastEthernet interface (`FastEthernet0`).
* **Services Hosted:**
  * `SRV-CENTRAL`: DNS (`records.hospital.local`), DHCP Server (Pools for VLAN 10, 20, 30, 40, 60), HTTP/HTTPS EHR Web Portal.
  * `SRV-PACS`: Medical Imaging PACS Archive (DICOM storage simulator).
  * `SRV-BACKUP`: Disaster Recovery Database Replication Target.
  * `SRV-CACHE`: Remote Spoke Clinic Local EHR Proxy and Survivability Cache.

### 2.6 Workstations & Mobile Endpoints (`PC-PT`, `Laptop-PT`)
* **Clinical & Admin Workstations:** **PC-PT** equipped with standard copper FastEthernet NIC.
* **Guest Wi-Fi Laptops:** **Laptop-PT** modified with **`WPC300N`** 2.4 GHz wireless module.
  > [!TIP]
  > **Laptop-PT Wireless Card Installation:**  
  > In Packet Tracer, power off the laptop, drag the copper `PT-LAPTOP-NM-1CFE` card out of the slot into the bottom trash/tray, drag the **`WPC300N`** wireless card into the empty slot, and power the laptop back on.

### 2.7 VoIP IP Phones (`IP-Phone-PT`)
* **Model:** **Cisco 7960 IP Phone**
* **Ports:** 1x 10/100 Switch Port (uplink to switch) and 1x 10/100 PC Port (daisy-chain downstream workstation).
* **Power Requirement:** In Packet Tracer, drag the AC power brick cable from the lower right of the Physical tab and plug it into the power socket on the phone rear panel.

### 2.8 Wireless Access Points (`AccessPoint-PT`)
* **Model:** **AccessPoint-PT**
* **Antenna/Band:** 2.4 GHz 802.11b/g/n.
* **SSID Configurations:**
  * Main Hospital: `Hospital_Guest_WiFi` (VLAN 40, Open / WPA2-PSK).
  * Remote Clinic: `Clinic_Guest_WiFi` (VLAN 40, Open / WPA2-PSK).

---

## 3. Master Hardware Bill of Materials (BOM)

| # | Device Hostname | Packet Tracer Model | Expansion Modules Installed | Module Slot | Power Supply Note | Physical Location / Role |
| :-: | :--- | :--- | :--- | :-: | :--- | :--- |
| **1** | `R1` | Cisco 2911 ISR | `HWIC-2T` (Dual Serial WAN) | Slot 0 | AC Power (Power-off to insert card) | Main Campus Server Room (Core Router / ASBR / NAT Edge) |
| **2** | `R2` | Cisco 2911 ISR | `HWIC-2T` (Dual Serial WAN) | Slot 0 | AC Power (Power-off to insert card) | Remote Clinic Telecomm Room (Core / ABR Router) |
| **3** | `EDGE-ISP` | Cisco 2911 ISR | *None (Onboard GigE)* | - | Standard AC Power | Public WAN Cloud (Simulated Internet Provider) |
| **4** | `SW-D1` | Catalyst 3560-24PS | *Integrated 24 FE + 2 GigE* | - | Internal AC (Boots automatically) | Main Campus Distribution Rack A (Active HSRP Clinical/Servers) |
| **5** | `SW-D2` | Catalyst 3560-24PS | *Integrated 24 FE + 2 GigE* | - | Internal AC (Boots automatically) | Main Campus Distribution Rack B (Active HSRP Admin/Guest/Voice) |
| **6** | `SW-D3` | Catalyst 3560-24PS | *Integrated 24 FE + 2 GigE* | - | Internal AC (Boots automatically) | Remote Clinic Distribution Rack (Single-chassis Branch Gateway) |
| **7** | `SW-A1` | Catalyst 2960-24TT | *Integrated 24 FE + 2 GigE* | - | Internal AC | Main Campus Access Rack (ICU Ward Switch) |
| **8** | `SW-A2` | Catalyst 2960-24TT | *Integrated 24 FE + 2 GigE* | - | Internal AC | Main Campus Access Rack (Surgical Suites Switch) |
| **9** | `SW-A3` | Catalyst 2960-24TT | *Integrated 24 FE + 2 GigE* | - | Internal AC | Main Campus Access Rack (Hospital Administration Switch) |
| **10** | `SW-A4` | Catalyst 2960-24TT | *Integrated 24 FE + 2 GigE* | - | Internal AC | Main Campus Access Rack (Guest Wi-Fi Access Switch) |
| **11** | `SW-A5` | Catalyst 2960-24TT | *Integrated 24 FE + 2 GigE* | - | Internal AC | Remote Clinic Access Rack (All Clinic Clinical/Admin Access) |
| **12** | `SRV-CENTRAL` | Server-PT | FastEthernet Copper NIC | - | Internal Power | Main Campus Server Farm (DNS, DHCP, EHR Web Portal) |
| **13** | `SRV-PACS` | Server-PT | FastEthernet Copper NIC | - | Internal Power | Main Campus Server Farm (PACS Imaging Archive) |
| **14** | `SRV-BACKUP` | Server-PT | FastEthernet Copper NIC | - | Internal Power | Main Campus Server Farm (Disaster Recovery DB Target) |
| **15** | `SRV-CACHE` | Server-PT | FastEthernet Copper NIC | - | Internal Power | Remote Clinic Telecomm Closet (Local EHR Cache / Offline Proxy) |
| **16** | `SBC-ICU-101` | SBC-PT | IoTEth / FastEthernet | - | Internal 5V DC | ICU Bed 101 Telemetry Node (Python Vitals Simulation) |
| **17** | `SBC-ICU-102` | SBC-PT | IoTEth / FastEthernet | - | Internal 5V DC | ICU Bed 102 Telemetry Node (Python Vitals Simulation) |
| **18** | `SBC-ICU-103` | SBC-PT | IoTEth / FastEthernet | - | Internal 5V DC | ICU Bed 103 Telemetry Node (Python Vitals Simulation) |
| **19** | `SBC-SURG-201`| SBC-PT | IoTEth / FastEthernet | - | Internal 5V DC | Operating Room 1 Surgical Telemetry Node (Python) |
| **20** | `SBC-SURG-202`| SBC-PT | IoTEth / FastEthernet | - | Internal 5V DC | Operating Room 2 Surgical Telemetry Node (Python) |
| **21** | `PC-ICU-NURSE`| PC-PT | FastEthernet Copper NIC | - | Standard AC | ICU Central Nursing Station Monitoring Workstation |
| **22** | `PC-ICU-DOC1` | PC-PT | FastEthernet Copper NIC | - | Standard AC | ICU Attending Physician Clinical Workstation 1 |
| **23** | `PC-ICU-DOC2` | PC-PT | FastEthernet Copper NIC | - | Standard AC | ICU Attending Physician Clinical Workstation 2 |
| **24** | `PC-THEATRE-1`| PC-PT | FastEthernet Copper NIC | - | Standard AC | Operating Theatre 1 High-Resolution PACS DICOM Viewer |
| **25** | `PC-THEATRE-2`| PC-PT | FastEthernet Copper NIC | - | Standard AC | Operating Theatre 2 High-Resolution PACS DICOM Viewer |
| **26** | `PC-THEATRE-3`| PC-PT | FastEthernet Copper NIC | - | Standard AC | Surgical Head Consultation & Vital Signs Display |
| **27** | `PC-ADMIN-301`| PC-PT | FastEthernet Copper NIC | - | Standard AC | Main Hospital Admissions & Billing Terminal |
| **28** | `PC-ADMIN-302`| PC-PT | FastEthernet Copper NIC | - | Standard AC | Hospital Medical Records Administration Terminal |
| **29** | `PC-ADMIN-303`| PC-PT | FastEthernet Copper NIC | - | Standard AC | Hospital Executive Director Workstation |
| **30** | `AP-GUEST` | AccessPoint-PT | Port0 (Wired) / Port1 (RF) | - | AC Power Adapter | Main Hospital Outpatient Waiting Lobby Access Point |
| **31** | `LAPTOP-GUEST-1`| Laptop-PT | `WPC300N` Wireless Card | Module Bay | Internal Battery / AC | Guest Waiting Lounge Visitor Laptop |
| **32** | `LAPTOP-GUEST-2`| Laptop-PT | `WPC300N` Wireless Card | Module Bay | Internal Battery / AC | Hospital Cafeteria Visitor Laptop |
| **33** | `LAPTOP-GUEST-3`| Laptop-PT | `WPC300N` Wireless Card | Module Bay | Internal Battery / AC | Family Waiting Area Visitor Laptop |
| **34** | `PHONE-ICU-601`| Cisco 7960 | Dual 10/100 Switch/PC Ports | - | External AC Power Brick plugged in | ICU Nursing Station IP Phone (Ext: 1001) |
| **35** | `PHONE-SURG-602`| Cisco 7960 | Dual 10/100 Switch/PC Ports | - | External AC Power Brick plugged in | Surgical Suite Reception IP Phone (Ext: 1002) |
| **36** | `PHONE-ADMIN-603`| Cisco 7960 | Dual 10/100 Switch/PC Ports | - | External AC Power Brick plugged in | Hospital Front Desk IP Phone (Ext: 1003) |
| **37** | `PC-NOC-MGT` | PC-PT | FastEthernet Copper NIC | - | Standard AC | Network Operations Center (VLAN 99 Out-of-band Console) |
| **38** | `PC-CLINIC-CONSULT1`| PC-PT| FastEthernet Copper NIC | - | Standard AC | Remote Clinic Consultation Room 1 Workstation |
| **39** | `PC-CLINIC-CONSULT2`| PC-PT| FastEthernet Copper NIC | - | Standard AC | Remote Clinic Consultation Room 2 Workstation |
| **40** | `PC-CLINIC-TRIAGE` | PC-PT| FastEthernet Copper NIC | - | Standard AC | Remote Clinic Emergency Triage Station |
| **41** | `PC-CLINIC-ADM1` | PC-PT | FastEthernet Copper NIC | - | Standard AC | Remote Clinic Reception & Patient Check-in Terminal |
| **42** | `PC-CLINIC-ADM2` | PC-PT | FastEthernet Copper NIC | - | Standard AC | Remote Clinic Billing & Insurance Terminal |
| **43** | `PC-CLINIC-PHARM`| PC-PT | FastEthernet Copper NIC | - | Standard AC | Remote Clinic Pharmacy Dispensing PC |
| **44** | `AP-CLINIC-GUEST`| AccessPoint-PT | Port0 (Wired) / Port1 (RF) | - | AC Power Adapter | Remote Clinic Patient Waiting Lobby Access Point |
| **45** | `LAPTOP-CLINIC-G1`| Laptop-PT | `WPC300N` Wireless Card | Module Bay | Internal Battery / AC | Clinic Visitor Laptop 1 |
| **46** | `LAPTOP-CLINIC-G2`| Laptop-PT | `WPC300N` Wireless Card | Module Bay | Internal Battery / AC | Clinic Visitor Laptop 2 |
| **47** | `LAPTOP-CLINIC-G3`| Laptop-PT | `WPC300N` Wireless Card | Module Bay | Internal Battery / AC | Clinic Visitor Laptop 3 |
| **48** | `PHONE-CLINIC-601`| Cisco 7960 | Dual 10/100 Switch/PC Ports | - | External AC Power Brick plugged in | Clinic Reception IP Phone (Ext: 2001) |
| **49** | `PHONE-CLINIC-602`| Cisco 7960 | Dual 10/100 Switch/PC Ports | - | External AC Power Brick plugged in | Clinic Doctor Desk IP Phone (Ext: 2002) |
| **50** | `PHONE-CLINIC-603`| Cisco 7960 | Dual 10/100 Switch/PC Ports | - | External AC Power Brick plugged in | Clinic Triage Desk IP Phone (Ext: 2003) |
| **51** | `PC-CLINIC-MGT` | PC-PT | FastEthernet Copper NIC | - | Standard AC | Remote Clinic Local System Administrator PC |

---

## 4. End-Device Count & Verification Audit per VLAN

To guarantee rigorous empirical testing during viva and packet simulation analysis, the design enforces:
* **Rule A:** At least **3 testable endpoints** per VLAN.
* **Rule B:** Exactly **3 SBC sensor nodes** in Main Hospital ICU (VLAN 10).
* **Rule C:** Exactly **2 SBC sensor nodes** in Main Hospital Surgery (VLAN 20).

### 4.1 End-Device Count Audit Table

| Site | VLAN ID | Subnet CIDR | Virtual Gateway | Min Req. | Actual Hosts | SBC Nodes | Assigned Device Hostnames | Audit Status |
| :--- | :---: | :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| **Main Hospital** | **10** (ICU) | `172.16.7.128/26` | `172.16.7.129` | $\ge 3$ + 3 SBC | **6** | **3** | `SBC-ICU-101`, `SBC-ICU-102`, `SBC-ICU-103`, `PC-ICU-NURSE`, `PC-ICU-DOC1`, `PC-ICU-DOC2` | **PASS (Compliant)** |
| **Main Hospital** | **20** (Surgery) | `172.16.7.64/26` | `172.16.7.65` | $\ge 3$ + 2 SBC | **5** | **2** | `SBC-SURG-201`, `SBC-SURG-202`, `PC-THEATRE-1`, `PC-THEATRE-2`, `PC-THEATRE-3` | **PASS (Compliant)** |
| **Main Hospital** | **30** (Admin) | `172.16.4.0/23` | `172.16.4.1` | $\ge 3$ | **3** | 0 | `PC-ADMIN-301`, `PC-ADMIN-302`, `PC-ADMIN-303` | **PASS (Compliant)** |
| **Main Hospital** | **40** (Guest) | `172.16.0.0/22` | `172.16.0.1` | $\ge 3$ | **3** (+1 AP) | 0 | `AP-GUEST`, `LAPTOP-GUEST-1`, `LAPTOP-GUEST-2`, `LAPTOP-GUEST-3` | **PASS (Compliant)** |
| **Main Hospital** | **50** (Servers) | `172.16.7.0/26` | `172.16.7.1` | $\ge 3$ | **3** | 0 | `SRV-CENTRAL`, `SRV-PACS`, `SRV-BACKUP` | **PASS (Compliant)** |
| **Main Hospital** | **60** (Voice) | `172.16.6.0/25` | `172.16.6.1` | $\ge 3$ | **3** | 0 | `PHONE-ICU-601`, `PHONE-SURG-602`, `PHONE-ADMIN-603` | **PASS (Compliant)** |
| **Main Hospital** | **99** (Mgmt) | `172.16.7.192/27` | `172.16.7.193` | 1 NOC + SVIs | **1** (+4 SVIs) | 0 | `PC-NOC-MGT` (Plus SVIs on SW-A1, SW-A2, SW-A3, SW-A4) | **PASS (Compliant)** |
| **Remote Clinic** | **10** (Clinical) | `172.16.8.32/27` | `172.16.8.33` | $\ge 3$ | **4** | 0 | `SRV-CACHE`, `PC-CLINIC-CONSULT1`, `PC-CLINIC-CONSULT2`, `PC-CLINIC-TRIAGE` | **PASS (Compliant)** |
| **Remote Clinic** | **30** (Admin) | `172.16.8.0/27` | `172.16.8.1` | $\ge 3$ | **3** | 0 | `PC-CLINIC-ADM1`, `PC-CLINIC-ADM2`, `PC-CLINIC-PHARM` | **PASS (Compliant)** |
| **Remote Clinic** | **40** (Guest) | `172.16.6.128/25` | `172.16.6.129` | $\ge 3$ | **3** (+1 AP) | 0 | `AP-CLINIC-GUEST`, `LAPTOP-CLINIC-G1`, `LAPTOP-CLINIC-G2`, `LAPTOP-CLINIC-G3` | **PASS (Compliant)** |
| **Remote Clinic** | **60** (Voice) | `172.16.7.224/27` | `172.16.7.225` | $\ge 3$ | **3** | 0 | `PHONE-CLINIC-601`, `PHONE-CLINIC-602`, `PHONE-CLINIC-603` | **PASS (Compliant)** |
| **Remote Clinic** | **99** (Mgmt) | `172.16.8.64/28` | `172.16.8.65` | 1 Mgt + SVIs | **1** (+1 SVI) | 0 | `PC-CLINIC-MGT` (Plus SVI on SW-A5) | **PASS (Compliant)** |

---

## 5. Physical Cabling Inventory

| Cable Media Type | Quantity | Standard Connector | Purpose & Application |
| :--- | :---: | :--- | :--- |
| **Serial DCE / DTE Cable** | **2** | Smart Serial V.35 | Inter-site WAN point-to-point links between R1 and R2 (`LINK-WAN-01`, `LINK-WAN-02`). R1 is DCE (`clock rate 128000`). |
| **Copper Straight-Through (Cat6)** | **46** | RJ-45 | Core routed uplinks, distribution-to-access 802.1Q trunks, server connections, PC workstations, SBC sensors, IP phones, and WAPs. |
| **Copper Crossover (Cat6)** | **2** | RJ-45 | Inter-distribution EtherChannel cross-links between SW-D1 and SW-D2 (`FastEthernet0/23` and `FastEthernet0/24`). |
| **Wireless 802.11 RF Links** | **6** | 2.4 GHz RF | Over-the-air connections between guest laptops and wireless access points (`AP-GUEST`, `AP-CLINIC-GUEST`). |
| **Console Rollover Cable** | *Lab Use* | RJ-45 to DB-9 | Initial out-of-band switch and router bootstrapping during manual lab setup. |
| **Total Physical / Logical Links** | **56** | — | **Zero unmapped interfaces across all 51 devices.** |

---

## 6. Verification Checklist Before Building in Packet Tracer

1. [ ] **Router Card Insertion:** Verify that both `R1` and `R2` have `HWIC-2T` inserted into **Slot 0**, not Slot 1. Confirm interface names are `Serial0/0/0` and `Serial0/0/1`.
2. [ ] **Serial DCE Clock Rate:** Ensure the `Serial DCE` cable end (marked with clock symbol in PT) is connected to **R1**. The command `clock rate 128000` must be present on R1's `Serial0/0/0` and `Serial0/0/1`.
3. [ ] **IP Phone Powering:** Verify each of the 6 Cisco 7960 IP phones has its AC power brick connected in the Physical tab. Phones will not power on or boot Cisco IOS skinny/SIP firmware without external power in PT.
4. [ ] **Wireless Modules:** Verify all 6 `Laptop-PT` devices have the `WPC300N` wireless card inserted and their Wi-Fi adapter SSID configured to associate with `Hospital_Guest_WiFi` or `Clinic_Guest_WiFi`.
5. [ ] **Multilayer Switch EtherChannel:** Confirm SW-D1 and SW-D2 member ports `FastEthernet0/23` and `0/24` have identical speed, duplex, trunk encapsulation (`dot1q`), and native VLAN (`999`) before bringing up Port-Channel 1.
