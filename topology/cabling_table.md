# Physical Cabling & Interconnect Specification

**Project:** Disaster-Resilient Smart Hospital Network  
**Environment:** Cisco Packet Tracer 8.x  

---

## 1. Core & WAN Cabling

| Local Device | Local Port | Remote Device | Remote Port | Cable Type | Clock Rate / Role | Subnet / Role |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **R1** | `Serial0/0/0` | **R2** | `Serial0/0/0` | Serial DCE | `128000` (on R1) | `172.16.4.192/30` (Primary OSPF Area 0) |
| **R1** | `Serial0/0/1` | **R2** | `Serial0/0/1` | Serial DCE | `128000` (on R1) | `172.16.4.196/30` (Secondary EIGRP AS 100) |
| **R1** | `GigabitEthernet0/0` | **SW-D1** | `GigabitEthernet0/2` | Copper Straight-Through | Auto | `172.16.5.0/30` (Routed Transit link) |
| **R1** | `GigabitEthernet0/1` | **SW-D2** | `GigabitEthernet0/2` | Copper Straight-Through | Auto | `172.16.5.4/30` (Routed Transit link) |
| **R1** | `GigabitEthernet0/2` | **EDGE-ISP** | `GigabitEthernet0/0` | Copper Cross-Over | Auto | `203.0.113.0/30` (Internet Edge NAT PAT) |
| **R2** | `GigabitEthernet0/0` | **SW-D3** | `GigabitEthernet0/1` | Copper Straight-Through | Auto | `172.16.5.8/30` (Routed Transit link Area 1) |

---

## 2. Distribution Layer Cabling

| Local Switch | Local Port | Remote Switch | Remote Port | Cable Type | Trunk / Mode | Allowed VLANs |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SW-D1** | `GigabitEthernet0/1` | **SW-D2** | `GigabitEthernet0/1` | Copper Cross-Over | 802.1Q Trunk | `10,20,30,40,50,60,99` (Native 999) |
| **SW-D1** | `FastEthernet0/1` | **SW-A1** | `FastEthernet0/24` | Copper Straight-Through | 802.1Q Trunk | `10,20,30,40,50,60,99` (Native 999) |
| **SW-D1** | `FastEthernet0/3` | **SW-A2** | `FastEthernet0/24` | Copper Straight-Through | 802.1Q Trunk | `10,20,30,40,50,60,99` (Native 999) |
| **SW-D1** | `FastEthernet0/10`| **SRV-CENTRAL** | `FastEthernet0` | Copper Straight-Through | Access (VLAN 50)| Server Farm Central Server |
| **SW-D2** | `FastEthernet0/1` | **SW-A3** | `FastEthernet0/24` | Copper Straight-Through | 802.1Q Trunk | `10,20,30,40,50,60,99` (Native 999) |
| **SW-D2** | `FastEthernet0/3` | **SW-A4** | `FastEthernet0/24` | Copper Straight-Through | 802.1Q Trunk | `10,20,30,40,50,60,99` (Native 999) |
| **SW-D3** | `FastEthernet0/1` | **SW-A5** | `FastEthernet0/24` | Copper Straight-Through | 802.1Q Trunk | `10,30,50,60,99` (Native 999) |

---

## 3. Access Layer Host Assignments

| Access Switch | Port Range | Assigned Role | VLAN | IP Range / DHCP Pool |
| :--- | :--- | :--- | :---: | :--- |
| **SW-A1** | `Fa0/1 - 10` | ICU Bedside Monitors & SBC Telemetry | 10 | `172.16.3.135 - 172.16.3.190` (`POOL-ICU`) |
| **SW-A1** | `Fa0/11 - 15`| ICU Staff IP Phones | 60 (Voice) | `172.16.3.10 - 172.16.3.126` (`POOL-VOICE`) |
| **SW-A2** | `Fa0/1 - 10` | Surgery Theatre Equipment & PACS Workstations | 20 | `172.16.3.200 - 172.16.3.254` (`POOL-SURGERY`) |
| **SW-A2** | `Fa0/11 - 15`| Surgical Team IP Phones | 60 (Voice) | `POOL-VOICE` |
| **SW-A3** | `Fa0/1 - 16` | Hospital Admin Workstations | 30 | `172.16.2.10 - 172.16.2.254` (`POOL-ADMIN`) |
| **SW-A3** | `Fa0/17 - 20`| Admin IP Phones | 60 (Voice) | `POOL-VOICE` |
| **SW-A4** | `Fa0/1 - 16` | Guest Wi-Fi APs & Waiting Area Kiosks | 40 | `172.16.0.10 - 172.16.1.254` (`POOL-GUEST`) |
| **SW-A4** | `Fa0/17 - 20`| Reception Desk IP Phones | 60 (Voice) | `POOL-VOICE` |
| **SW-A5** | `Fa0/1 - 8`  | Remote Clinic Patient Monitors | 10 | `172.16.4.70 - 172.16.4.94` (Static / Clinic) |
| **SW-A5** | `Fa0/9 - 14` | Remote Clinic Staff PCs | 30 | `172.16.4.100 - 172.16.4.126` (Static / Clinic) |
| **SW-A5** | `Fa0/15 - 18`| Remote Local Cache Server | 50 | `172.16.4.162` (Static) |
| **SW-A5** | `Fa0/19 - 22`| Remote VoIP Phones | 60 (Voice) | `172.16.4.135 - 172.16.4.158` (Static / Clinic) |
