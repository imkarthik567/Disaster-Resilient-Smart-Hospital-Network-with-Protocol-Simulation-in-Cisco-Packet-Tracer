# Internet Edge, NAT/PAT Overload & Perimeter Translation Architecture
**Project:** Disaster-Resilient Smart Hospital Network (VIT SCOPE — Computer Networks)  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  
**Standard Compliance:** Cisco Packet Tracer 8.x | RFC 1631 / RFC 3022 (NAT/PAT) | RFC 2827 (BCP 38) | RFC 5737 (IPv4 Address Blocks for Documentation)  

---

## 1. Executive Summary & Edge Topology

The Internet Edge Router (`R1`) anchors the boundary between the private RFC 1918 campus addressing space (`172.16.0.0/16`) and the public untrusted Internet. The edge architecture accomplishes two vital operational objectives while maintaining strict Zero-Trust isolation:

1. **Outbound Internet Access (Dynamic PAT Overload):** Translates authorized private internal client subnets (Hospital Administration and Guest Wi-Fi across both the Main Hospital and Remote Clinic) into the single routable public IPv4 address assigned to the edge uplink interface (`172.16.8.102`).
2. **Inbound Demilitarized Service Exposure (Static NAT Port-Forwarding):** Translates incoming public HTTP (port 80) and HTTPS (port 443) requests destined for the public IP `172.16.8.102` directly to the internal Central Hospital Server `SRV-CENTRAL` (`172.16.7.4`), enabling patients and external medical professionals to access the Electronic Health Record (EHR) Web Portal without exposing sensitive database or internal management ports.

```
+------------------------------------------------------------------------------------------------------------------+
|                                      INTERNET EDGE & NAT ARCHITECTURE                                            |
+------------------------------------------------------------------------------------------------------------------+
|                                                                                                                  |
|   +---------------------------------+                                                                            |
|   |   Main Campus LAN Clients       |                                                                            |
|   |   - Admin VLAN 30 (172.16.4.0)  |---\                                                                        |
|   |   - Guest VLAN 40 (172.16.0.0)  |   |                                                                        |
|   +---------------------------------+   |                                                                        |
|                                         +--> [ SW-D1 / SW-D2 ]                                                   |
|   +---------------------------------+   |         | Gi0/2 (Routed /30)                                           |
|   |   Server Farm (VLAN 50)         |---/         v                                                              |
|   |   - SRV-CENTRAL (172.16.7.4)    |         [ Gi0/0 & Gi0/1: ip nat inside ]                                   |
|   +---------------------------------+                 |                                                          |
|                                                       v                                                          |
|   +---------------------------------+          +-------------+  Gi0/2 (172.16.8.102/30)   +------------------+   |
|   |   Remote Spoke Clinic Clients   |          | Core Router |  [ ip nat outside ]        | Simulated ISP    |   |
|   |   - Clinic Admin (172.16.8.0)   |--------> |     R1      |==========================> |    EDGE-ISP      |   |
|   |   - Clinic Guest (172.16.6.128) |  WAN     +-------------+  Transit: 172.16.8.100/30  +--------+---------+   |
|   +---------------------------------+  Circuits       ^                                            |             |
|                                                       | [ ip nat inside ]                          |             |
|                                                       |                                            v             |
|                                              [ Se0/0/0 & Se0/0/1 ]                       +-------------------+   |
|                                                                                          | External Web/DNS  |   |
|                                                                                          | - Web: 203.0.113.80 | |
|                                                                                          | - DNS: 8.8.8.8    |   |
|                                                                                          +-------------------+   |
+------------------------------------------------------------------------------------------------------------------+
```

---

## 2. Interface Roles & Default Routing

### 2.1 Interface Role Designation (`ip nat inside` vs. `ip nat outside`)
In Cisco IOS, address translation is statefully bound to the traffic transition between inside and outside interfaces:

| Interface | Device | IP / Mask | Role | Purpose & Traffic Flow |
| :--- | :---: | :--- | :---: | :--- |
| **`GigabitEthernet0/0`** | `R1` | `172.16.8.90/30` | `ip nat inside` | Point-to-point transit link to Distribution Switch `SW-D1`. Ingress for Main Campus user traffic. |
| **`GigabitEthernet0/1`** | `R1` | `172.16.8.94/30` | `ip nat inside` | Point-to-point transit link to Distribution Switch `SW-D2`. Redundant ingress for Main Campus user traffic. |
| **`Serial0/0/0`** | `R1` | `172.16.8.81/30` | `ip nat inside` | Primary WAN circuit to Remote Spoke Clinic (`R2`). Ingress for spoke traffic requiring Internet breakout. |
| **`Serial0/0/1`** | `R1` | `172.16.8.85/30` | `ip nat inside` | Secondary Standby WAN circuit to Remote Spoke Clinic (`R2`). Backup ingress for spoke Internet breakout. |
| **`GigabitEthernet0/2`** | `R1` | `172.16.8.102/30`| `ip nat outside` | Public demarcation uplink to Simulated ISP Gateway (`EDGE-ISP`). Point of packet header translation. |
| **`GigabitEthernet0/0`** | `EDGE-ISP` | `172.16.8.101/30`| ISP Demarc | Upstream gateway for R1. Terminates the point-to-point transit link. |

### 2.2 Default Route Origination & Dynamic Propagation
1. **Static Default Route on `R1`:**
   ```cisco
   ip route 0.0.0.0 0.0.0.0 172.16.8.101
   ```
   Directs all unmapped and external destinations out `GigabitEthernet0/2` to the ISP next-hop (`172.16.8.101`).

2. **Dynamic OSPF Default Route Injection:**
   ```cisco
   router ospf 1
    default-information originate
   ```
   `R1` originates an OSPF Type-5 AS-External LSA (`E2`, Metric 20) across Area 0 and Area 1. Distribution switches `SW-D1`, `SW-D2`, and clinic switch `SW-D3` dynamically learn their gateway of last resort pointing back to `R1`, eliminating manual default route maintenance across internal switches.

3. **ISP Static Return Route:**
   ```cisco
   EDGE-ISP(config)# ip route 172.16.0.0 255.255.0.0 172.16.8.102
   ```
   Ensures the upstream provider routes any hospital traffic (such as inbound sessions to the portal) back to `R1`'s public interface.

---

## 3. Address Translation Whitelist vs. Exclusion Policy

In strict alignment with Zero-Trust principles, NAT is not applied universally to the entire `172.16.0.0/16` supernet. Instead, standard access-list `NAT-ACL` operates as an internal firewall-level filter enforcing which source subnets are permitted to initiate Internet sessions.

### 3.1 Subnet Translation Matrix

| Subnet / VLAN | Zone & Description | NAT Status | Security & Operational Justification |
| :--- | :--- | :---: | :--- |
| **`172.16.4.0/23`** (VLAN 30) | Main Hospital Administration | **TRANSLATED** | Hospital billing, HR, state registry filing, and insurance verification require external cloud/web access. |
| **`172.16.0.0/22`** (VLAN 40) | Main Hospital Guest Wi-Fi | **TRANSLATED** | Patients, families, and visitors require general Internet web browsing (HTTP/HTTPS). |
| **`172.16.8.0/27`** (VLAN 30) | Remote Clinic Administration | **TRANSLATED** | Spoke clinic staff access national prescription registries and telemedicine portals via WAN breakout. |
| **`172.16.6.128/25`** (VLAN 40)| Remote Clinic Guest Wi-Fi | **TRANSLATED** | Spoke clinic waiting area visitor connectivity via WAN breakout. |
| **`172.16.7.128/26`** (VLAN 10)| ICU Clinical Wards | **EXCLUDED** | **Ransomware & Zero-Day Isolation:** Life-critical physiological patient monitors and infusion pumps must never possess direct outbound Internet access. |
| **`172.16.7.64/26`** (VLAN 20) | Surgery Operating Theatres | **EXCLUDED** | **Surgical Integrity:** Robotic surgical consoles, endoscopy processors, and anesthesia machines must remain strictly air-gapped from external networks. |
| **`172.16.7.0/26`** (VLAN 50) | Central Server Farm | **EXCLUDED** | **Anti-Exfiltration:** Servers (DNS, DHCP, PACS, EHR) must not establish arbitrary outbound Internet sessions. Inbound access is strictly limited via reverse port-forwarding. |
| **`172.16.6.0/25`** (VLAN 60) | VoIP Telephony | **EXCLUDED** | **Toll Fraud Prevention:** IP PBX and Cisco 7960 phones communicate via internal SIP/RTP. Direct public Internet traversal is prohibited. |
| **`172.16.7.192/27`** (VLAN 99)| Out-of-Band Management | **EXCLUDED** | **Control Plane Isolation:** SSH access to switch and router SVIs is restricted to internal NOC consoles; never routable to the Internet. |
| **`172.16.8.80/28`** | Transit Links & Loopbacks | **EXCLUDED** | Router-IDs and point-to-point transit interconnects have no business initiating web traffic. |

### 3.2 Production Cisco IOS Configuration (`R1`)

```cisco
! ==============================================================================
! R1 NAT OVERLOAD (PAT) & REVERSE PORT-FORWARDING CONFIGURATION
! ==============================================================================

! --- Define NAT Permitted Source Client Subnets ---
ip access-list standard NAT-ACL
 remark Permit Main Hospital Guest Wi-Fi (VLAN 40)
 permit 172.16.0.0 0.0.3.255
 remark Permit Main Hospital Administration (VLAN 30)
 permit 172.16.4.0 0.0.1.255
 remark Permit Remote Clinic Guest Wi-Fi (VLAN 40)
 permit 172.16.6.128 0.0.0.127
 remark Permit Remote Clinic Administration (VLAN 30)
 permit 172.16.8.0 0.0.0.31
 remark Deny all other internal ranges (ICU, Surgery, Voice, Mgmt, Server Farm)
 deny any log
exit

! --- Dynamic PAT Overload Configuration ---
! Multiplexes all authorized client sessions behind the single outside interface IP
ip nat inside source list NAT-ACL interface GigabitEthernet0/2 overload

! --- Static NAT Port-Forwarding (Reverse NAT) for Public EHR Web Portal ---
! Outside IP 172.16.8.102:80 -> Inside Server SRV-CENTRAL 172.16.7.4:80
ip nat inside source static tcp 172.16.7.4 80 172.16.8.102 80 extendable
! Outside IP 172.16.8.102:443 -> Inside Server SRV-CENTRAL 172.16.7.4:443
ip nat inside source static tcp 172.16.7.4 443 172.16.8.102 443 extendable
```

> [!NOTE]
> **Why `extendable` is mandatory in Cisco IOS:**  
> When multiple static translations reference the same public IP address (`172.16.8.102`) on different TCP ports (80 and 443), or when static translations share an IP with dynamic PAT (`interface GigabitEthernet0/2 overload`), the `extendable` keyword informs the IOS NAT table compiler to index the mapping as a specific IP+port socket rather than an exclusive IP binding. Omitting `extendable` results in an IOS command rejection (`% 172.16.8.102 already aliased`).

---

## 4. Simulated ISP Router Configuration (`EDGE-ISP`)

To provide realistic end-to-end testing without external physical infrastructure, `EDGE-ISP` simulates an upstream Tier-1 Internet Service Provider providing public DNS resolvers and an external public health web authority.

```cisco
! ==============================================================================
! DEVICE: EDGE-ISP (Simulated Internet Service Provider Gateway)
! ==============================================================================
hostname EDGE-ISP
no ip domain-lookup
enable secret class

! Demarcation Link to Hospital R1
interface GigabitEthernet0/0
 description Link_to_R1_Internet_Edge_Gig0/2
 ip address 172.16.8.101 255.255.255.252
 no shutdown
exit

! Public Google DNS Simulator
interface Loopback0
 description Public_Google_DNS_Simulator
 ip address 8.8.8.8 255.255.255.255
 no shutdown
exit

! Public Cloudflare DNS Simulator
interface Loopback1
 description Public_Cloudflare_DNS_Simulator
 ip address 1.1.1.1 255.255.255.255
 no shutdown
exit

! Public External Web Server Simulator (RFC 5737 TEST-NET-3)
interface Loopback2
 description Public_External_Web_Server_www.public-health.org
 ip address 203.0.113.80 255.255.255.240
 no shutdown
exit

! Enable Built-in HTTP Server on EDGE-ISP to service web requests
ip http server

! Static Return Route to Hospital Address Space
ip route 172.16.0.0 255.255.0.0 172.16.8.102
```

---

## 5. Comprehensive Verification & Execution Protocol

### 5.1 Verification Command 1: Inspect Active NAT Translations (`show ip nat translations`)

```cisco
R1# show ip nat translations
Pro Inside global         Inside local          Outside local         Outside global
tcp 172.16.8.102:80       172.16.7.4:80         ---                   ---
tcp 172.16.8.102:443      172.16.7.4:443        ---                   ---
tcp 172.16.8.102:51432    172.16.4.10:51432     203.0.113.80:80       203.0.113.80:80
tcp 172.16.8.102:52110    172.16.0.11:52110     203.0.113.80:443      203.0.113.80:443
icmp 172.16.8.102:1       172.16.4.10:1         8.8.8.8:1             8.8.8.8:1
```

* **Lines 1–2 (Static Port-Forwarding):** Permanent entries mapping `172.16.8.102:80` and `:443` to `SRV-CENTRAL` (`172.16.7.4`). The dashes in `Outside local/global` indicate persistent listening state awaiting inbound connections.
* **Line 3 (Dynamic PAT - Admin Web Browsing):** PC-ADMIN-301 (`172.16.4.10`) communicating with external web server `203.0.113.80:80`. Source port `51432` is translated to `172.16.8.102:51432`.
* **Line 4 (Dynamic PAT - Guest Web Browsing):** Guest Laptop (`172.16.0.11`) accessing secure web server `203.0.113.80:443`.
* **Line 5 (Dynamic PAT - ICMP Diagnostic):** PC-ADMIN-301 pinging Google DNS `8.8.8.8`.

### 5.2 Verification Command 2: NAT Operational Statistics (`show ip nat statistics`)

```cisco
R1# show ip nat statistics
Total active translations: 5 (2 static, 3 dynamic; 3 extended)
Outside interfaces:
  GigabitEthernet0/2
Inside interfaces:
  GigabitEthernet0/0, GigabitEthernet0/1, Serial0/0/0, Serial0/0/1
Hits: 342  Misses: 2
CEF Translated packets: 344, CEF Punted packets: 0
Expired translations: 18
Dynamic mappings:
-- Inside Source
[Id: 1] access-list NAT-ACL interface GigabitEthernet0/2 ref count 3
```

* **Total active translations:** 5 total (2 static for EHR portal, 3 dynamic client sessions).
* **Interface Roles:** Confirms `GigabitEthernet0/2` is the sole Outside interface; inside interfaces encompass all core downlinks and WAN circuits.
* **Hits vs. Misses:** 342 packets matched existing state translation entries; 2 new sessions initiated allocation.

---

## 6. End-to-End Test Scenarios

### Test Scenario 1: Admin Host Outbound Ping & HTTP Request to External Web Server
**Objective:** Confirm that internal Admin host (`PC-ADMIN-301`, `172.16.4.10`) can reach external Internet services via PAT.

1. **ICMP Reachability Test:**
   ```
   PC-ADMIN-301> ping 203.0.113.80
   Pinging 203.0.113.80 with 32 bytes of data:
   Reply from 203.0.113.80: bytes=32 time=3ms TTL=254
   Reply from 203.0.113.80: bytes=32 time=2ms TTL=254
   Reply from 203.0.113.80: bytes=32 time=2ms TTL=254
   Reply from 203.0.113.80: bytes=32 time=2ms TTL=254
   Ping statistics for 203.0.113.80:
       Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)
   ```
2. **HTTP Web Browser Test:**
   In Packet Tracer Desktop Web Browser on `PC-ADMIN-301`, open URL `http://203.0.113.80/`:
   * **Result:** Page loads successfully with HTTP 200 OK displaying the Cisco IOS simulated web page.
   * **Inspection:** `show ip nat translations` on `R1` displays an active TCP translation for `172.16.4.10` to `203.0.113.80:80`.

---

### Test Scenario 2: Inbound Public Access to Hospital Published EHR Portal (Static Port-Forward)
**Objective:** Confirm that external Internet users can access the published hospital EHR portal on `172.16.8.102:80` and `:443`, but are blocked from all other ports and internal IP addresses.

1. **External Web Request from ISP Router:**
   ```cisco
   EDGE-ISP# telnet 172.16.8.102 80
   Trying 172.16.8.102, 80 ... Open
   ```
2. **Perimeter Firewall Validation (`R1`):**
   ```cisco
   R1# show access-lists ACL-EDGE-IN
   Extended IP access list ACL-EDGE-IN
       70 permit tcp any host 172.16.8.102 eq www (1 match)
       80 permit tcp any host 172.16.8.102 eq 443
   ```
   The hit counter on line 70 increments by 1. The packet is translated from `172.16.8.102:80` to `172.16.7.4:80` and delivered to `SRV-CENTRAL`.

---

### Test Scenario 3: Failure Drill — Guest Wi-Fi Isolation vs. Functional NAT
**Objective:** Demonstrate that the Zero-Trust SVI ACL (`ACL-GUEST-IN`) strictly blocks guest devices from probing internal hospital servers, while outbound Internet NAT continues to function normally.

1. **Host Configuration:** `LAPTOP-GUEST-1` (IP `172.16.0.11`, VLAN 40, Default Gateway `172.16.0.2` on `SW-D1`).

2. **Step A — Attempted Internal Lateral Probe (BLOCKED):**
   ```
   LAPTOP-GUEST-1> ping 172.16.7.4
   Pinging 172.16.7.4 with 32 bytes of data:
   Request timed out.
   Request timed out.
   Request timed out.
   Request timed out.
   Ping statistics for 172.16.7.4:
       Packets: Sent = 4, Received = 0, Lost = 4 (100% loss)
   ```
   * **Distribution Switch Syslog (`SW-D1`):**
     ```
     %SEC-6-IPACCESSLOGP: list ACL-GUEST-IN denied ip 172.16.0.11 -> 172.16.7.4, 4 packets
     ```
   * **Verification Command:**
     ```cisco
     SW-D1# show access-lists ACL-GUEST-IN
     Extended IP access list ACL-GUEST-IN
         ...
         40 deny ip any 172.16.0.0 0.0.255.255 log (28 matches)  <-- Incremented by 4
     ```
   * **Conclusion:** Lateral reconnaissance is dropped at SVI ingress on `SW-D1`. Packet never reaches the core router or server farm.

3. **Step B — Outbound Internet Access (PERMITTED VIA NAT):**
   ```
   LAPTOP-GUEST-1> ping 203.0.113.80
   Pinging 203.0.113.80 with 32 bytes of data:
   Reply from 203.0.113.80: bytes=32 time=3ms TTL=254
   Reply from 203.0.113.80: bytes=32 time=2ms TTL=254
   Reply from 203.0.113.80: bytes=32 time=2ms TTL=254
   Reply from 203.0.113.80: bytes=32 time=2ms TTL=254
   ```
   * **Router NAT Table (`R1`):**
     ```cisco
     R1# show ip nat translations | include 172.16.0.11
     icmp 172.16.8.102:2       172.16.0.11:2         203.0.113.80:2        203.0.113.80:2
     ```
   * **Conclusion:** The SVI ACL permits outbound packets destined for the Internet (`permit icmp any any echo`), and `R1` translates the packet through `NAT-ACL` into the public IP. **Internal isolation is 100% enforced without degrading Internet services.**

---

## 7. Viva / Oral Examination Note: "Why NAT is NOT a Security Feature"

> [!IMPORTANT]
> **Key Thesis for Faculty Viva:**  
> *"NAT obscures internal IP addresses for address conservation; stateful firewalls enforce access control policies for security. Confusing obscurity with security is a fundamental architectural error."*

### Key Technical Arguments for the Viva:

1. **Design Intent (RFC 1631 vs. Security):**
   * NAT was defined in 1994 (RFC 1631, later RFC 3022) exclusively as a **short-term operational workaround for IPv4 address exhaustion**, not as a security mechanism.
   * Its function is strictly layer-3/layer-4 address/port manipulation to stretch private IPv4 address longevity.

2. **The "State Table Drop" is an Incidental Side-Effect, Not Policy Enforcement:**
   * Proponents often argue that PAT "protects" internal hosts because unsolicited incoming packets are dropped.
   * **The Reality:** That drop occurs merely because there is no matching translation slot in the NAT state table—it is a **routing limitation of dynamic port multiplexing**, not an intentional security decision.
   * A firewall evaluates packets against an explicit **security rulebase** (identity, protocol compliance, directionality, threat signatures). NAT simply looks up an address in a translation table.

3. **Zero Payload Inspection & Zero Threat Prevention:**
   * NAT operates strictly at Layers 3 and 4 (IP header and TCP/UDP ports).
   * NAT has **zero visibility into packet payloads**. If an internal user in VLAN 30 clicks a phishing link or downloads ransomware from `http://203.0.113.80/malware.exe`, NAT translates the packet headers with zero scrutiny and delivers the malicious payload straight into the hospital network.
   * Command and Control (C2) callbacks, botnet beaconing, DNS tunneling, and cross-site scripting (XSS) pass unimpeded through any NAT device. Only a **Stateful Next-Generation Firewall (NGFW) or Deep Packet Inspection (DPI) engine** can detect and drop these threats.

4. **Port-Forwarding Directly Punctures the "NAT Security Blanket":**
   * The moment static NAT or port-forwarding is configured (such as our EHR portal `172.16.8.102:80 -> 172.16.7.4:80`), external attackers can directly connect to the internal host.
   * If the web server has an unpatched Apache vulnerability or SQL injection flaw, NAT provides **zero protection**. Only perimeter ACLs (`ACL-EDGE-IN`) and Web Application Firewalls (WAF) provide defense.

5. **NAT Breaks the End-to-End Principle & Complicates Forensics:**
   * NAT violates RFC 1958 (Architectural Principles of the Internet) by breaking end-to-end address transparency.
   * It breaks protocols with embedded IP addresses in the application payload (e.g., active FTP, SIP/VoIP, IPsec AH).
   * In a security incident, external logging servers only see the single public IP (`172.16.8.102`). Identifying which internal hospital workstation committed an exfiltration event requires complex, synchronized NAT state-log correlation.

6. **The Definitive Proof: The IPv6 Paradigm:**
   * In IPv6, where every single host has a Globally Unique Address (GUA) and NAT is eliminated, enterprise networks remain **equally or more secure** than IPv4 networks.
   * Security in IPv6 is maintained by **stateful firewalls** blocking unsolicited inbound traffic and inspecting flows. If NAT were truly a security feature, an IPv6 network would be inherently insecure—a proposition that every standard body (IETF, NIST) completely rejects.
