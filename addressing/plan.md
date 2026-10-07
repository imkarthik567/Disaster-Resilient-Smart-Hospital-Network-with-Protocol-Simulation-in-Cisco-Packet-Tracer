# VLSM Addressing Plan & Summarisation Architecture

**Base Address Block:** `172.16.0.0/16` (65,536 total IPv4 addresses)  
**Growth Headroom Applied:** `30.0%` applied to all host pools  
**Total Allocated Space:** `2,157` addresses (3.29% of `/16` block)  
**Free Unallocated Capacity:** `63,379` addresses  

## 1. Subnet Allocation Table (Sorted Largest First)

| Subnet Name | Site | VLAN | Network CIDR | Subnet Mask | Wildcard Mask | Usable Host Range | Needed | Usable | Wasted | Util % |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **Main-VLAN40-Guest** | Main Hospital | 40 | `172.16.0.0/22` | `255.255.252.0` | `0.0.3.255` | `172.16.0.1 - 172.16.3.254` | 520 | 1022 | 502 | 50.88% |
| **Main-VLAN30-Admin** | Main Hospital | 30 | `172.16.4.0/23` | `255.255.254.0` | `0.0.1.255` | `172.16.4.1 - 172.16.5.254` | 260 | 510 | 250 | 50.98% |
| **Main-VLAN60-Voice** | Main Hospital | 60 | `172.16.6.0/25` | `255.255.255.128` | `0.0.0.127` | `172.16.6.1 - 172.16.6.126` | 78 | 126 | 48 | 61.9% |
| **Clinic-VLAN40-Guest** | Remote Clinic | 40 | `172.16.6.128/25` | `255.255.255.128` | `0.0.0.127` | `172.16.6.129 - 172.16.6.254` | 65 | 126 | 61 | 51.59% |
| **Main-VLAN50-Servers** | Main Hospital | 50 | `172.16.7.0/26` | `255.255.255.192` | `0.0.0.63` | `172.16.7.1 - 172.16.7.62` | 39 | 62 | 23 | 62.9% |
| **Main-VLAN20-Surgery** | Main Hospital | 20 | `172.16.7.64/26` | `255.255.255.192` | `0.0.0.63` | `172.16.7.65 - 172.16.7.126` | 52 | 62 | 10 | 83.87% |
| **Main-VLAN10-ICU** | Main Hospital | 10 | `172.16.7.128/26` | `255.255.255.192` | `0.0.0.63` | `172.16.7.129 - 172.16.7.190` | 52 | 62 | 10 | 83.87% |
| **Main-VLAN99-Mgmt** | Main Hospital | 99 | `172.16.7.192/27` | `255.255.255.224` | `0.0.0.31` | `172.16.7.193 - 172.16.7.222` | 26 | 30 | 4 | 86.67% |
| **Clinic-VLAN60-Voice** | Remote Clinic | 60 | `172.16.7.224/27` | `255.255.255.224` | `0.0.0.31` | `172.16.7.225 - 172.16.7.254` | 26 | 30 | 4 | 86.67% |
| **Clinic-VLAN30-Admin** | Remote Clinic | 30 | `172.16.8.0/27` | `255.255.255.224` | `0.0.0.31` | `172.16.8.1 - 172.16.8.30` | 26 | 30 | 4 | 86.67% |
| **Clinic-VLAN10-Clinical** | Remote Clinic | 10 | `172.16.8.32/27` | `255.255.255.224` | `0.0.0.31` | `172.16.8.33 - 172.16.8.62` | 26 | 30 | 4 | 86.67% |
| **Clinic-VLAN99-Mgmt** | Remote Clinic | 99 | `172.16.8.64/28` | `255.255.255.240` | `0.0.0.15` | `172.16.8.65 - 172.16.8.78` | 13 | 14 | 1 | 92.86% |
| **WAN-Primary-Serial** | WAN | - | `172.16.8.80/30` | `255.255.255.252` | `0.0.0.3` | `172.16.8.81 - 172.16.8.82` | 2 | 2 | 0 | 100.0% |
| **WAN-Secondary-Serial** | WAN | - | `172.16.8.84/30` | `255.255.255.252` | `0.0.0.3` | `172.16.8.85 - 172.16.8.86` | 2 | 2 | 0 | 100.0% |
| **Transit-R1-SW-D1** | Main Hospital | - | `172.16.8.88/30` | `255.255.255.252` | `0.0.0.3` | `172.16.8.89 - 172.16.8.90` | 2 | 2 | 0 | 100.0% |
| **Transit-R1-SW-D2** | Main Hospital | - | `172.16.8.92/30` | `255.255.255.252` | `0.0.0.3` | `172.16.8.93 - 172.16.8.94` | 2 | 2 | 0 | 100.0% |
| **Transit-R2-SW-D3** | Remote Clinic | - | `172.16.8.96/30` | `255.255.255.252` | `0.0.0.3` | `172.16.8.97 - 172.16.8.98` | 2 | 2 | 0 | 100.0% |
| **Edge-R1-ISP** | Internet Edge | - | `172.16.8.100/30` | `255.255.255.252` | `0.0.0.3` | `172.16.8.101 - 172.16.8.102` | 2 | 2 | 0 | 100.0% |
| **Loopback-R1** | Main Hospital | - | `172.16.8.104/32` | `255.255.255.255` | `0.0.0.0` | `172.16.8.104` | 1 | 1 | 0 | 100.0% |
| **Loopback-R2** | Remote Clinic | - | `172.16.8.105/32` | `255.255.255.255` | `0.0.0.0` | `172.16.8.105` | 1 | 1 | 0 | 100.0% |
| **Loopback-SW-D1** | Main Hospital | - | `172.16.8.106/32` | `255.255.255.255` | `0.0.0.0` | `172.16.8.106` | 1 | 1 | 0 | 100.0% |
| **Loopback-SW-D2** | Main Hospital | - | `172.16.8.107/32` | `255.255.255.255` | `0.0.0.0` | `172.16.8.107` | 1 | 1 | 0 | 100.0% |
| **Loopback-SW-D3** | Remote Clinic | - | `172.16.8.108/32` | `255.255.255.255` | `0.0.0.0` | `172.16.8.108` | 1 | 1 | 0 | 100.0% |

---

## 2. Address Block Carving Visualization

The base `172.16.0.0/16` block is partitioned from low-order addresses upwards based on strict VLSM binary boundaries:

```
+-----------------------------------------------------------------------------------------+
| 172.16.0.0/16 Base Hospital Enterprise Block (65,536 Addresses)                         |
+-----------------------------------------------------------------------------------------+
| 172.16.0.0/22   | Main Hospital Guest Wi-Fi (VLAN 40) - 1,024 Addresses                 |
+-----------------+-----------------------------------------------------------------------+
| 172.16.4.0/23   | Main Hospital Administration (VLAN 30) - 512 Addresses                |
+-----------------+-----------------------------------------------------------------------+
| 172.16.6.0/25   | Main Hospital VoIP Voice (VLAN 60) - 128 Addresses                    |
+-----------------+-----------------------------------------------------------------------+
| 172.16.6.128/25 | Remote Clinic Guest Wi-Fi (VLAN 40) - 128 Addresses                   |
+-----------------+-----------------------------------------------------------------------+
| 172.16.7.0/26   | Main Hospital ICU Clinical (VLAN 10) - 64 Addresses                   |
+-----------------+-----------------------------------------------------------------------+
| 172.16.7.64/26  | Main Hospital Surgery Suites (VLAN 20) - 64 Addresses                  |
+-----------------+-----------------------------------------------------------------------+
| 172.16.7.128/26 | Main Hospital Central Server Farm (VLAN 50) - 64 Addresses            |
+-----------------+-----------------------------------------------------------------------+
| 172.16.7.192/27 | Main Hospital Out-of-Band Management (VLAN 99) - 32 Addresses         |
+-----------------+-----------------------------------------------------------------------+
| 172.16.7.224/27 | Remote Clinic Patient Monitoring (VLAN 10) - 32 Addresses             |
+-----------------+-----------------------------------------------------------------------+
| 172.16.8.0/27   | Remote Clinic Administration (VLAN 30) - 32 Addresses                 |
+-----------------+-----------------------------------------------------------------------+
| 172.16.8.32/27  | Remote Clinic VoIP Voice (VLAN 60) - 32 Addresses                     |
+-----------------+-----------------------------------------------------------------------+
| 172.16.8.64/28  | Remote Clinic Management (VLAN 99) - 16 Addresses                     |
+-----------------+-----------------------------------------------------------------------+
| 172.16.8.80+    | Point-to-Point WAN Serial /30s, Transit Uplinks, and /32 Loopbacks    |
+-----------------+-----------------------------------------------------------------------+
| 172.16.9.0 - 172.16.255.255 (Unused Reserve Space for Disaster Expansion - ~63,000 IPs) |
+-----------------------------------------------------------------------------------------+
```

---

## 3. OSPF Area Summarisation Analysis (ABR Route Aggregation)

### The Clinical Rationale for Route Summarisation
In a disaster-resilient multi-site topology, flapping access links or DHCP churn at the Remote Clinic must **not** trigger full Shortest Path First (SPF) recalculations across the Main Hospital Core. By summarising routes at Area Border Router **R2**, we reduce the OSPF Link-State Database (LSDB) size and isolate SPF recalculations to Area 1.

### Recommended Area 1 Route Aggregation
- **Contiguous Supernet Covering All Remote Clinic Subnets:** `172.16.0.0/20`  
- **Summary Subnet Mask:** `255.255.240.0`  
- **ABR Cisco IOS Configuration (on Core Router R2):**

```cisco
router ospf 1
 area 1 range 172.16.0.0 255.255.240.0
exit
```

> **Result:** Rather than injecting multiple Type-3 Summary LSAs for every small remote VLAN, R2 advertises a single aggregated summary route (`172.16.0.0/20`) into Backbone Area 0. If any individual remote subnet experiences an intermittent link flap, the summary LSA remains stable, guaranteeing zero CPU churn on Core Router R1.
