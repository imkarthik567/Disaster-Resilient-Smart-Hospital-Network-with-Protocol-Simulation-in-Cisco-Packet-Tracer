# Comprehensive Security Policy & Access Control Architecture
**Project:** Disaster-Resilient Smart Hospital Network (VIT SCOPE — Computer Networks)  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  
**Standard Compliance:** Cisco Packet Tracer 8.x | RFC 2827 (BCP 38) | NIST SP 800-125B (Micro-segmentation)  

---

## 1. Executive Summary & Zero-Trust Framework

Modern hospital environments converge critical life-support telemetry, medical imaging (PACS), electronic health records (EHR), VoIP telephony, and public guest Wi-Fi onto a shared IP infrastructure. A single infected visitor laptop or rogue medical IoT node must never compromise acute care operations.

This architecture enforces **Zero-Trust Microsegmentation** at Layer 3:
1. **Default Deny Posture:** All inter-zone communications are prohibited unless explicitly permitted by an access control list (ACL).
2. **Inbound Edge Enforcement:** Extended access lists are applied **inbound on the Switch Virtual Interfaces (SVIs) closest to the traffic source**, extinguishing malicious or unauthorized packets before they consume campus switching fabric or WAN bandwidth.
3. **Strict Service-Level Whitelisting:** Devices may only communicate with authorized server ports (e.g. ICU telemetry to PACS on port 104; DNS on port 53; EHR on ports 80/443). Host-to-host lateral movement between different clinical and non-clinical zones is strictly blocked.
4. **Perimeter Anti-Spoofing & Unsolicited Traffic Suppression:** The Internet Edge Router (`R1`) enforces **BCP 38 / RFC 2827** anti-spoofing filters to drop spoofed RFC 1918 traffic from external sources and limits inbound connectivity exclusively to the published EHR web portal.

```
+--------------------------------------------------------------------------------------------------------+
|                                    SECURITY ZONE BOUNDARIES & TRUST LEVELS                             |
+--------------------------------------------------------------------------------------------------------+
|                                                                                                        |
|   +--------------------------+   +--------------------------+   +----------------------------------+   |
|   |   GUEST ZONE (VLAN 40)   |   |   ADMIN ZONE (VLAN 30)   |   |   CLINICAL ZONES (VLAN 10/20)    |   |
|   |   Untrusted Public / IoT |   |   Admissions & Billing   |   |   ICU Wards & Surgery Theatres   |   |
|   +------------+-------------+   +------------+-------------+   +----------------+-----------------+   |
|                |                              |                                  |                     |
|                v                              v                                  v                     |
|          ACL-GUEST-IN                   ACL-ADMIN-IN                       ACL-ICU-IN                  |
|                |                              |                            ACL-SURGERY-IN              |
|                +------------------------------+----------------------------------+                     |
|                                               |                                                        |
|                                               v                                                        |
|                               +-------------------------------+                                        |
|                               |  DISTRIBUTION SWITCHES (SVI)  |                                        |
|                               |  Hardware Routing & Filtering |                                        |
|                               +---------------+---------------+                                        |
|                                               |                                                        |
|                       +-----------------------+-----------------------+                                |
|                       |                                               |                                |
|                       v                                               v                                |
|        +-----------------------------+                 +-----------------------------+                 |
|        |    SERVER FARM (VLAN 50)    |                 |   INTERNET EDGE ROUTER R1   |                 |
|        | DNS, DHCP, EHR, PACS Storage|                 |   ACL-EDGE-IN (Anti-Spoof)  |                 |
|        +-----------------------------+                 +--------------+--------------+                 |
|                                                                       |                                |
|                                                                       v                                |
|                                                          +-------------------------+                   |
|                                                          | Public Internet (ISP)   |                   |
|                                                          +-------------------------+                   |
+--------------------------------------------------------------------------------------------------------+
```

---

## 2. Zone-to-Zone Inter-VLAN Permit/Deny Matrix

The following matrix dictates the traffic filtering policy across all network zones.  
* **P:** Permit (with protocol/port restrictions)  
* **D:** Deny (explicitly logged)  
* **-:** Intra-zone (permitted at Layer 2 within the VLAN)

| Source Zone \ Destination Zone | Guest Zone (VLAN 40) | ICU Zone (VLAN 10) | Surgery Zone (VLAN 20) | Admin Zone (VLAN 30) | Server Farm (VLAN 50) | Voice Zone (VLAN 60) | Management (VLAN 99) | Spoke Clinic (VLANs 10,30,40) | Internet (External) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Guest Zone (VLAN 40)** | - | **D** (log) | **D** (log) | **D** (log) | **P** (DHCP, DNS only) | **D** (log) | **D** (log) | **D** (log) | **P** (HTTP/S, ICMP) |
| **ICU Zone (VLAN 10)** | **D** (log) | - | **D** (log) | **D** (log) | **P** (HTTP/S, PACS, DNS, DHCP) | **D** (log) | **D** (log) | **P** (Clinic Cache) | **P** (HTTP/S Updates) |
| **Surgery Zone (VLAN 20)** | **D** (log) | **D** (log) | - | **D** (log) | **P** (HTTP/S, PACS, DNS, DHCP) | **D** (log) | **D** (log) | **P** (Clinic Cache) | **D** (log) |
| **Admin Zone (VLAN 30)** | **D** (log) | **D** (log) | **D** (log) | - | **P** (HTTP/S, DNS, DHCP, TFTP) | **D** (log) | **D** (log) | **P** (Clinic Admin) | **P** (HTTP/S, Email) |
| **Server Farm (VLAN 50)** | **D** (log) | **P** (Established) | **P** (Established) | **P** (Established) | - | **P** (Voice/TFTP) | **D** (log) | **P** (Established, Repl) | **P** (NTP, DNS Updates) |
| **Voice Zone (VLAN 60)** | **D** (log) | **D** (log) | **D** (log) | **D** (log) | **P** (DHCP, TFTP 69, DNS) | - | **D** (log) | **P** (Inter-site SIP/RTP) | **D** (log) |
| **Management (VLAN 99)** | **D** (log) | **P** (SSH, ICMP) | **P** (SSH, ICMP) | **P** (SSH, ICMP) | **P** (SSH, Backup) | **P** (SSH, SNMP) | - | **P** (SSH across WAN) | **D** (log) |
| **Spoke Clinic Zones** | **D** (log) | **P** (Cache Query) | **D** (log) | **P** (Admin Sync) | **P** (DHCP Relay, EHR, PACS) | **P** (SIP/RTP) | **D** (log) | - | **P** (via R1 PAT) |
| **Internet (External)** | **D** (Unsolicited) | **D** (Drop) | **D** (Drop) | **D** (Drop) | **P** (EHR Portal 80/443 only)| **D** (Drop) | **D** (Drop) | **D** (Drop) | - |

---

## 3. Detailed Security Policy Rules & Technical Rationale

### 3.1 Guest Network Policy (VLAN 40)
* **DHCP Traversal:** Visitors and waiting room laptops must obtain IP addresses automatically. Because the DHCP server (`SRV-CENTRAL` - `172.16.7.4`) resides on VLAN 50, the DHCP broadcast (`255.255.255.255:67`) must be permitted by the inbound ACL on SVI Vlan40 before the `ip helper-address` engine can intercept and unicast-relay it. Blocking port 67 would break guest connectivity.
* **DNS Resolution:** Guests are permitted to query the hospital DNS resolver (`172.16.7.4`) on UDP/TCP port 53 exclusively.
* **Internal Isolation:** All access to internal hospital subnets (`172.16.0.0/16`) is strictly blocked and logged (`deny ip any 172.16.0.0 0.0.255.255 log`).
* **Internet Egress:** Unrestricted outbound HTTP (port 80), HTTPS (port 443), and ICMP Echo (ping) to external destinations.

### 3.2 Clinical IoT & Acute Care Isolation (VLAN 10 ICU & VLAN 20 Surgery)
* **Life-Critical Telemetry Protection:** ICU vital signs monitors and Operating Theatre surgical telemetry transmit continuous patient vitals. They must be completely quarantined from the general administrative network and guest users to prevent denial-of-service or malware contamination.
* **Authorized Data Flows:**
  - **PACS Image Retrieval:** `172.16.7.7` on TCP port 104 (DICOM Application Entity) and TCP port 443 (Web DICOM Viewer).
  - **Central Hospital Portal (EHR):** `172.16.7.4` on TCP ports 80 and 443.
  - **Disaster Recovery Backup:** `172.16.7.8` on TCP port 443.
  - **Local Spoke Clinic EHR Cache:** `172.16.8.36` on TCP ports 80 and 443.
* **Lateral Movement Blocking:** Explicit deny rules block any communication toward VLAN 30 (Administration) and VLAN 40 (Guest).

### 3.3 Hospital Administration Policy (VLAN 30)
* **Billing & Admissions Workstations:** Staff require access to the central database (`172.16.7.4`) and external insurance portals via the Internet.
* **Device Protection:** Administrative staff PCs are prohibited from reaching clinical IoT device VLANs (VLAN 10 and VLAN 20) directly, preventing accidental or malicious tampering with life-support telemetry.

### 3.4 Out-of-Band Management & Infrastructure Hardening (VLAN 99)
* **Single Management Station Whitelisting:** Switch and router management interfaces (SVIs and VTY lines) are restricted to:
  - **Main NOC Console:** `PC-NOC-MGT` (`172.16.7.212` in VLAN 99).
  - **Clinic Admin Station:** `PC-CLINIC-MGT` (`172.16.8.75` in Clinic VLAN 99).
* **Protocol Restriction:** Only encrypted SSH (TCP port 22) and diagnostic ICMP Echo are permitted. Insecure protocols (Telnet, HTTP) are blocked.

### 3.5 Internet Edge Perimeter Defense & Anti-Spoofing (BCP 38 / RFC 2827)
Applied inbound on Core Router R1's external interface (`GigabitEthernet0/2`):
1. **RFC 1918 Address Filtering:** Private addresses (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) should never appear as source IPs on the public Internet. Packets arriving from the ISP with these sources are spoofed and immediately dropped.
2. **Internal Hospital Block Anti-Spoofing:** Drops any external packet claiming a source address inside `172.16.0.0/16` (anti-hairpinning spoof defense).
3. **Special Block Filtering:** Drops Loopback (`127.0.0.0/8`), APIPA (`169.254.0.0/16`), and Multicast (`224.0.0.0/4`).
4. **Demilitarized EHR Portal Pinholing:** External patients accessing the telemedicine/EHR portal are permitted to connect to R1's outside IP (`172.16.8.102`) on ports 80 and 443.
5. **Stateful Return Permitted:** TCP packets with ACK/RST flags set (`established`) are permitted to allow return traffic for internal user browsing.

---

## 4. Technical Deep Dive: Return Traffic Engineering & Packet Tracer Constraints

A critical architectural consideration in Layer 3 access control is handling **bidirectional return traffic**:

```
[Host in VLAN 10] --(1) SYN: Src 172.16.7.141 -> Dst 172.16.7.4:443--> [Server VLAN 50]
[Host in VLAN 10] <-- (2) SYN/ACK: Src 172.16.7.4:443 -> Dst 172.16.7.141 -- [Server VLAN 50]
```

### 4.1 Evaluation of Return Traffic Mechanisms

| Mechanism | Operating Principle | Packet Tracer 8.x Status | Architecture Decision |
| :--- | :--- | :---: | :--- |
| **Reflexive ACLs (`reflect` / `evaluate`)** | Creates temporary dynamic nested ACEs based on outbound sessions. | **NOT SUPPORTED**<br>(Syntax rejected on 3560/3650 SVIs) | Rejected due to simulator constraints. |
| **Zone-Based Policy Firewall (ZBPF)** | Stateful L4/L7 inspection (`inspect` type). Full connection tracking. | **PARTIALLY SUPPORTED**<br>(Supported on 2911 ISR routers; NOT supported on L3 switches) | Impractical for inter-VLAN routing on distribution switches. |
| **TCP `established` Keyword** | Stateless filter that inspects TCP header for **ACK (Acknowledgment)** or **RST (Reset)** flags ($ACK=1$ or $RST=1$). | **FULLY SUPPORTED**<br>(100% reliable on switches and routers) | **[SELECTED]** Deployed for all return TCP session flows. |
| **Symmetric Return Whitelisting** | Explicit ACEs permitting response flows for stateless UDP (DNS, DHCP, TFTP, SIP). | **FULLY SUPPORTED** | **[SELECTED]** Deployed for UDP/ICMP traffic. |

### 4.2 The TCP `established` Keyword Explained
Under RFC 793, TCP handshakes establish state as follows:
- **SYN Packet (Initiator -> Receiver):** $ACK = 0, RST = 0$. (New connection request).
- **SYN-ACK Packet (Receiver -> Initiator):** $ACK = 1, RST = 0$. (Return traffic).
- **ACK / Data Packets (Subsequent):** $ACK = 1$. (Established stream).

By configuring `permit tcp any any established`:
- Unsolicited inbound SYN packets from unauthorized zones are blocked ($ACK=0$).
- Legitimate return packets belonging to outbound connections initiated by internal hosts are permitted ($ACK=1$).
- UDP protocols (stateless) cannot use `established`; they are handled by explicit port-pair whitelists (e.g. UDP 53 to client ports, or UDP 68 to UDP 67).

---

## 5. ACL Placement Strategy & Architectural Justification

Cisco design guidelines dictate distinct placement strategies for standard versus extended ACLs:

1. **Extended Access Lists: Placed as close to the traffic SOURCE as possible.**
   - **Mechanism:** Applied `in` on the source SVI (e.g. `ACL-GUEST-IN` applied inbound on `interface Vlan40`).
   - **Justification:** Unauthorized packets (such as a guest laptop attempting to probe the ICU telemetry subnet) are evaluated and discarded at the switch port ingress. This eliminates unnecessary forwarding across the switch backplane, cross-distribution EtherChannels, and routed WAN circuits, conserving CPU cycles and ASIC bandwidth.
2. **Standard Access Lists: Placed as close to the DESTINATION as possible.**
   - **Mechanism:** Applied on VTY management lines (`line vty 0 4`) via `access-class ACL-VTY-SSH in`.
   - **Justification:** Standard ACLs can only filter based on source address. Applying them on VTY endpoints isolates terminal management without impacting transit routing.
3. **Named vs. Numbered ACLs:**
   - Named extended ACLs (`ip access-list extended <NAME>`) are used exclusively.
   - Named ACLs support non-disruptive line insertion, explicit descriptive names, and inline `remark` documentation.

---

## 6. Production ACL Configurations

### 6.1 Distribution Switches SW-D1 and SW-D2 (Main Hospital Campus)

The identical ACL policy is deployed on both `SW-D1` and `SW-D2` to ensure consistent security policy regardless of which switch is HSRP Active for a given VLAN.

```cisco
! ==============================================================================
! ACCESS CONTROL LIST CONFIGURATION: SW-D1 & SW-D2 (MAIN HOSPITAL)
! ==============================================================================

! --- VTY Management Line Security ACL ---
ip access-list standard ACL-VTY-SSH
 remark Permit Main Hospital NOC Management Console
 permit host 172.16.7.212
 remark Permit Remote Clinic Local Management Station
 permit host 172.16.8.75
 remark Deny all other administrative attempts with logging
 deny any log
exit

! --- VLAN 10 Inbound ACL: ICU Clinical Wards ---
ip access-list extended ACL-ICU-IN
 remark Permit client DHCP requests to relay agent
 permit udp any any eq bootps
 remark Permit DNS resolution to Central Server
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Permit HTTP and HTTPS to Central Hospital EHR Portal
 permit tcp any host 172.16.7.4 eq www
 permit tcp any host 172.16.7.4 eq 443
 remark Permit DICOM and PACS web viewer to PACS Archive Server
 permit tcp any host 172.16.7.7 eq 104
 permit tcp any host 172.16.7.7 eq www
 permit tcp any host 172.16.7.7 eq 443
 remark Permit DR database replication to Backup Server
 permit tcp any host 172.16.7.8 eq 443
 remark Permit access to Remote Clinic local EHR cache
 permit tcp any host 172.16.8.36 eq www
 permit tcp any host 172.16.8.36 eq 443
 remark Permit established TCP return traffic
 permit tcp any any established
 remark Permit ICMP diagnostic echo and echo-reply
 permit icmp any any echo
 permit icmp any any echo-reply
 remark Explicitly deny and log lateral access to Admin VLAN 30
 deny ip any 172.16.4.0 0.0.1.255 log
 remark Explicitly deny and log lateral access to Guest VLAN 40
 deny ip any 172.16.0.0 0.0.3.255 log
 remark Implicit deny all other traffic
 deny ip any any log
exit

! --- VLAN 20 Inbound ACL: Surgery Operating Theatres ---
ip access-list extended ACL-SURGERY-IN
 remark Permit client DHCP requests to relay agent
 permit udp any any eq bootps
 remark Permit DNS resolution to Central Server
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Permit HTTP and HTTPS to Central Hospital EHR Portal
 permit tcp any host 172.16.7.4 eq www
 permit tcp any host 172.16.7.4 eq 443
 remark Permit DICOM image stream to PACS Archive Server
 permit tcp any host 172.16.7.7 eq 104
 permit tcp any host 172.16.7.7 eq www
 permit tcp any host 172.16.7.7 eq 443
 remark Permit established TCP return traffic
 permit tcp any any established
 remark Permit ICMP diagnostic echo and echo-reply
 permit icmp any any echo
 permit icmp any any echo-reply
 remark Explicitly deny and log lateral access to Admin VLAN 30
 deny ip any 172.16.4.0 0.0.1.255 log
 remark Explicitly deny and log lateral access to Guest VLAN 40
 deny ip any 172.16.0.0 0.0.3.255 log
 remark Implicit deny all other traffic
 deny ip any any log
exit

! --- VLAN 30 Inbound ACL: Hospital Administration ---
ip access-list extended ACL-ADMIN-IN
 remark Permit client DHCP requests to relay agent
 permit udp any any eq bootps
 remark Permit DNS resolution to Central Server
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Permit HTTP and HTTPS to Central Hospital EHR Portal
 permit tcp any host 172.16.7.4 eq www
 permit tcp any host 172.16.7.4 eq 443
 remark Permit PACS administrative portal access
 permit tcp any host 172.16.7.7 eq www
 permit tcp any host 172.16.7.7 eq 443
 remark Permit TFTP backup transfer to Backup Server
 permit udp any host 172.16.7.8 eq tftp
 remark Permit outbound Internet web traffic (HTTP/HTTPS)
 permit tcp any any eq www
 permit tcp any any eq 443
 remark Permit established TCP return traffic
 permit tcp any any established
 remark Permit ICMP diagnostic echo and echo-reply
 permit icmp any any echo
 permit icmp any any echo-reply
 remark Explicitly deny and log access to acute ICU VLAN 10
 deny ip any 172.16.7.128 0.0.0.63 log
 remark Explicitly deny and log access to Surgery VLAN 20
 deny ip any 172.16.7.64 0.0.0.63 log
 remark Explicitly deny and log access to Guest VLAN 40
 deny ip any 172.16.0.0 0.0.3.255 log
 remark Implicit deny all other traffic
 deny ip any any log
exit

! --- VLAN 40 Inbound ACL: Hospital Guest Wi-Fi ---
ip access-list extended ACL-GUEST-IN
 remark Permit DHCP discovery broadcast and relay
 permit udp any any eq bootps
 remark Permit DNS resolution exclusively to Central DNS Server
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Explicitly deny and log any attempt to reach internal hospital networks
 deny ip any 172.16.0.0 0.0.255.255 log
 remark Permit outbound Internet web browsing (HTTP/HTTPS)
 permit tcp any any eq www
 permit tcp any any eq 443
 remark Permit external ICMP echo requests for connectivity checks
 permit icmp any any echo
 remark Permit established TCP return traffic
 permit tcp any any established
 remark Implicit deny all other unauthorized guest traffic
 deny ip any any log
exit

! --- VLAN 50 Inbound ACL: Central Server Farm ---
ip access-list extended ACL-SERVER-IN
 remark Permit DNS server outbound root queries
 permit udp host 172.16.7.4 any eq domain
 permit tcp host 172.16.7.4 any eq domain
 remark Permit DHCP server response offers and acknowledgments
 permit udp host 172.16.7.4 any eq bootpc
 remark Permit PACS archive replication to Remote Clinic Cache
 permit tcp host 172.16.7.7 host 172.16.8.36 eq 443
 remark Permit database synchronization to Backup Server
 permit tcp host 172.16.7.4 host 172.16.7.8 eq 443
 remark Permit established TCP return traffic to all hospital zones
 permit tcp any any established
 remark Permit ICMP diagnostic echo-reply and echo
 permit icmp any any echo-reply
 permit icmp any any echo
 remark Implicit deny unsolicited outbound connections from servers
 deny ip any any log
exit

! --- VLAN 60 Inbound ACL: VoIP Telephony ---
ip access-list extended ACL-VOICE-IN
 remark Permit DHCP requests with Option 150
 permit udp any any eq bootps
 remark Permit DNS queries for PBX hostname resolution
 permit udp any host 172.16.7.4 eq domain
 remark Permit TFTP firmware and config downloads from Central Server
 permit udp any host 172.16.7.4 eq tftp
 remark Permit SIP signaling between phones and call manager
 permit udp any any eq 5060
 permit tcp any any eq 5060
 remark Permit RTP voice media streams (UDP port range 16384-32767)
 permit udp any any range 16384 32767
 remark Permit ICMP echo for phone health checks
 permit icmp any any echo
 remark Explicitly deny and log any voice packet targeting data VLANs
 deny ip any 172.16.4.0 0.0.1.255 log
 deny ip any 172.16.0.0 0.0.3.255 log
 remark Implicit deny all other voice traffic
 deny ip any any log
exit

! --- VLAN 99 Inbound ACL: Out-of-Band Management ---
ip access-list extended ACL-MGMT-IN
 remark Permit NOC administrator console full access
 permit ip host 172.16.7.212 any
 remark Permit Remote Clinic admin station access
 permit ip host 172.16.8.75 any
 remark Permit established TCP return management traffic
 permit tcp any any established
 remark Permit ICMP echo and echo-reply
 permit icmp any any echo
 permit icmp any any echo-reply
 remark Explicitly deny and log all unapproved management access
 deny ip any any log
exit
```

#### SVI Application on SW-D1 and SW-D2:
```cisco
interface Vlan10
 ip access-group ACL-ICU-IN in
exit

interface Vlan20
 ip access-group ACL-SURGERY-IN in
exit

interface Vlan30
 ip access-group ACL-ADMIN-IN in
exit

interface Vlan40
 ip access-group ACL-GUEST-IN in
exit

interface Vlan50
 ip access-group ACL-SERVER-IN in
exit

interface Vlan60
 ip access-group ACL-VOICE-IN in
exit

interface Vlan99
 ip access-group ACL-MGMT-IN in
exit

line vty 0 4
 access-class ACL-VTY-SSH in
 transport input ssh
exit
```

---

### 6.2 Distribution Switch SW-D3 (Remote Spoke Clinic)

```cisco
! ==============================================================================
! ACCESS CONTROL LIST CONFIGURATION: SW-D3 (REMOTE CLINIC)
! ==============================================================================

ip access-list standard ACL-VTY-SSH
 remark Permit Central NOC Admin PC via WAN
 permit host 172.16.7.212
 remark Permit Clinic Local Admin PC
 permit host 172.16.8.75
 remark Deny all other management attempts
 deny any log
exit

ip access-list extended ACL-CLINIC-CLINICAL-IN
 remark Permit DHCP relay across WAN
 permit udp any any eq bootps
 remark Permit DNS resolution to Central Server across WAN
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Permit HTTP/HTTPS to local EHR Cache Server
 permit tcp any host 172.16.8.36 eq www
 permit tcp any host 172.16.8.36 eq 443
 remark Permit HTTP/HTTPS to Central Hospital Portal across WAN
 permit tcp any host 172.16.7.4 eq www
 permit tcp any host 172.16.7.4 eq 443
 remark Permit DICOM queries to PACS Server across WAN
 permit tcp any host 172.16.7.7 eq 104
 permit tcp any host 172.16.7.7 eq www
 permit tcp any host 172.16.7.7 eq 443
 remark Permit established TCP return traffic
 permit tcp any any established
 remark Permit ICMP diagnostics
 permit icmp any any echo
 permit icmp any any echo-reply
 remark Deny lateral access to Clinic Admin VLAN 30
 deny ip any 172.16.8.0 0.0.0.31 log
 remark Deny lateral access to Clinic Guest VLAN 40
 deny ip any 172.16.6.128 0.0.0.127 log
 remark Implicit deny
 deny ip any any log
exit

ip access-list extended ACL-CLINIC-ADMIN-IN
 remark Permit DHCP relay across WAN
 permit udp any any eq bootps
 remark Permit DNS resolution to Central Server
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Permit HTTP/HTTPS to Central EHR Portal
 permit tcp any host 172.16.7.4 eq www
 permit tcp any host 172.16.7.4 eq 443
 remark Permit outbound Internet browsing
 permit tcp any any eq www
 permit tcp any any eq 443
 remark Permit established TCP return traffic
 permit tcp any any established
 remark Permit ICMP diagnostics
 permit icmp any any echo
 permit icmp any any echo-reply
 remark Deny access to acute clinical VLAN 10
 deny ip any 172.16.8.32 0.0.0.31 log
 remark Deny access to guest VLAN 40
 deny ip any 172.16.6.128 0.0.0.127 log
 remark Implicit deny
 deny ip any any log
exit

ip access-list extended ACL-CLINIC-GUEST-IN
 remark Permit DHCP discovery broadcast and relay
 permit udp any any eq bootps
 remark Permit DNS resolution to Central Server
 permit udp any host 172.16.7.4 eq domain
 permit tcp any host 172.16.7.4 eq domain
 remark Explicitly deny and log all internal hospital campus access
 deny ip any 172.16.0.0 0.0.255.255 log
 remark Permit outbound Internet web browsing (HTTP/HTTPS)
 permit tcp any any eq www
 permit tcp any any eq 443
 remark Permit external ICMP echo requests
 permit icmp any any echo
 remark Permit established TCP return traffic
 permit tcp any any established
 remark Implicit deny
 deny ip any any log
exit

ip access-list extended ACL-CLINIC-VOICE-IN
 remark Permit DHCP requests
 permit udp any any eq bootps
 remark Permit DNS queries to Central Server
 permit udp any host 172.16.7.4 eq domain
 remark Permit TFTP firmware downloads from Central Server
 permit udp any host 172.16.7.4 eq tftp
 remark Permit SIP signaling to Central PBX across WAN
 permit udp any any eq 5060
 permit tcp any any eq 5060
 remark Permit RTP voice media streams across WAN
 permit udp any any range 16384 32767
 remark Permit ICMP echo
 permit icmp any any echo
 remark Deny access to clinic data VLANs
 deny ip any 172.16.8.0 0.0.0.31 log
 deny ip any 172.16.6.128 0.0.0.127 log
 remark Implicit deny
 deny ip any any log
exit

ip access-list extended ACL-CLINIC-MGMT-IN
 remark Permit Central NOC Admin PC full access
 permit ip host 172.16.7.212 any
 remark Permit Clinic Local Admin PC full access
 permit ip host 172.16.8.75 any
 remark Permit established TCP return traffic
 permit tcp any any established
 remark Permit ICMP diagnostics
 permit icmp any any echo
 permit icmp any any echo-reply
 remark Deny unauthorized management attempts
 deny ip any any log
exit
```

#### SVI Application on SW-D3:
```cisco
interface Vlan10
 ip access-group ACL-CLINIC-CLINICAL-IN in
exit

interface Vlan30
 ip access-group ACL-CLINIC-ADMIN-IN in
exit

interface Vlan40
 ip access-group ACL-CLINIC-GUEST-IN in
exit

interface Vlan60
 ip access-group ACL-CLINIC-VOICE-IN in
exit

interface Vlan99
 ip access-group ACL-CLINIC-MGMT-IN in
exit

line vty 0 4
 access-class ACL-VTY-SSH in
 transport input ssh
exit
```

---

### 6.3 Internet Edge Core Router R1 (Perimeter & Anti-Spoofing)

Applied inbound on `interface GigabitEthernet0/2` (facing `EDGE-ISP`):

```cisco
! ==============================================================================
! ACCESS CONTROL LIST CONFIGURATION: R1 (INTERNET EDGE)
! ==============================================================================

ip access-list standard ACL-VTY-SSH
 remark Permit Central NOC Admin PC
 permit host 172.16.7.212
 remark Permit Clinic Local Admin PC
 permit host 172.16.8.75
 remark Deny all other VTY access
 deny any log
exit

ip access-list extended ACL-EDGE-IN
 remark --- BCP 38 / RFC 2827 Ingress Anti-Spoofing Filters ---
 remark Deny RFC 1918 Class A private block
 deny ip 10.0.0.0 0.255.255.255 any log
 remark Deny internal hospital 172.16.0.0/16 address space arriving from Internet
 deny ip 172.16.0.0 0.15.255.255 any log
 remark Deny RFC 1918 Class C private block
 deny ip 192.168.0.0 0.0.255.255 any log
 remark Deny Loopback block
 deny ip 127.0.0.0 0.255.255.255 any log
 remark Deny APIPA link-local block
 deny ip 169.254.0.0 0.0.255.255 any log
 remark Deny Multicast and experimental blocks
 deny ip 224.0.0.0 15.255.255.255 any log

 remark --- Published Inbound Services (Demilitarized Portal) ---
 remark Permit inbound public access to published EHR Web Portal
 permit tcp any host 172.16.8.102 eq www
 permit tcp any host 172.16.8.102 eq 443

 remark --- Stateful Inspection for Outbound User Sessions ---
 remark Permit return TCP traffic for internal hospital hosts
 permit tcp any any established

 remark --- Inbound ICMP Control Messages ---
 remark Permit ICMP echo-reply from external web servers
 permit icmp any any echo-reply
 remark Permit ICMP destination-unreachable for path MTU discovery
 permit icmp any any unreachable
 remark Permit ICMP time-exceeded for traceroute diagnostics
 permit icmp any any time-exceeded

 remark --- Default Quarantine Rule ---
 remark Deny all unsolicited inbound traffic with logging
 deny ip any any log
exit
```

#### Application on Core Router R1:
```cisco
interface GigabitEthernet0/2
 ip access-group ACL-EDGE-IN in
exit

line vty 0 4
 access-class ACL-VTY-SSH in
 transport input ssh
exit
```

---

## 7. Comprehensive Verification Test Matrix & Counter Audit Protocol

### 7.1 Automated Policy Test Matrix

| Test ID | Source Host & IP | Destination IP & Host | Protocol & Port | Expected Action | Enforcing Device & ACL Line | Expected Counter Change |
| :---: | :--- | :--- | :---: | :---: | :--- | :--- |
| **SEC-01** | `LAPTOP-GUEST-1` (`172.16.0.11`) | `255.255.255.255` (Broadcast) | UDP 67 (DHCP) | **PERMIT** | SW-D1 `ACL-GUEST-IN` line `permit udp any any eq bootps` | Counter increments (+1) |
| **SEC-02** | `LAPTOP-GUEST-1` (`172.16.0.11`) | `172.16.7.4` (`SRV-CENTRAL`) | UDP 53 (DNS) | **PERMIT** | SW-D1 `ACL-GUEST-IN` line `permit udp any host 172.16.7.4 eq domain` | Counter increments (+1) |
| **SEC-03** | `LAPTOP-GUEST-1` (`172.16.0.11`) | `172.16.7.4` (`SRV-CENTRAL`) | TCP 80 (HTTP) | **DENY** | SW-D1 `ACL-GUEST-IN` line `deny ip any 172.16.0.0 0.0.255.255 log` | Counter increments (+1), syslog logged |
| **SEC-04** | `LAPTOP-GUEST-1` (`172.16.0.11`) | `172.16.7.141` (`PC-ICU-NURSE`) | ICMP Echo | **DENY** | SW-D1 `ACL-GUEST-IN` line `deny ip any 172.16.0.0 0.0.255.255 log` | Counter increments (+1), ping fails |
| **SEC-05** | `LAPTOP-GUEST-1` (`172.16.0.11`) | `8.8.8.8` (Public DNS) | ICMP Echo | **PERMIT** | SW-D1 `ACL-GUEST-IN` line `permit icmp any any echo` | Counter increments (+1), ping succeeds |
| **SEC-06** | `PC-ICU-NURSE` (`172.16.7.141`) | `172.16.7.7` (`SRV-PACS`) | TCP 104 (DICOM) | **PERMIT** | SW-D1 `ACL-ICU-IN` line `permit tcp any host 172.16.7.7 eq 104` | Counter increments (+1) |
| **SEC-07** | `PC-ICU-NURSE` (`172.16.7.141`) | `172.16.4.10` (`PC-ADMIN-301`) | ICMP Echo | **DENY** | SW-D1 `ACL-ICU-IN` line `deny ip any 172.16.4.0 0.0.1.255 log` | Counter increments (+1), ping fails |
| **SEC-08** | `PC-ADMIN-301` (`172.16.4.10`) | `172.16.7.141` (`PC-ICU-NURSE`) | ICMP Echo | **DENY** | SW-D1 `ACL-ADMIN-IN` line `deny ip any 172.16.7.128 0.0.0.63 log` | Counter increments (+1), ping fails |
| **SEC-09** | `PC-ADMIN-301` (`172.16.4.10`) | `172.16.7.4` (`SRV-CENTRAL`) | TCP 443 (HTTPS) | **PERMIT** | SW-D1 `ACL-ADMIN-IN` line `permit tcp any host 172.16.7.4 eq 443` | Counter increments (+1), web loads |
| **SEC-10** | `PC-NOC-MGT` (`172.16.7.212`) | `172.16.7.194` (`SW-D1` Vlan99) | TCP 22 (SSH) | **PERMIT** | SW-D1 `ACL-VTY-SSH` line `permit host 172.16.7.212` | Counter increments (+1), SSH prompt |
| **SEC-11** | `PC-ADMIN-301` (`172.16.4.10`) | `172.16.7.194` (`SW-D1` Vlan99) | TCP 22 (SSH) | **DENY** | SW-D1 `ACL-VTY-SSH` line `deny any log` | Counter increments (+1), connection refused |
| **SEC-12** | `EDGE-ISP` (`172.16.8.101`) | `172.16.8.102` (R1 Outside) | TCP 22 (SSH) | **DENY** | R1 `ACL-EDGE-IN` line `deny ip any any log` | Counter increments (+1), packet dropped |
| **SEC-13** | Spoofed External Host (`10.1.1.5`) | `172.16.7.4` (`SRV-CENTRAL`) | Any IP | **DENY** | R1 `ACL-EDGE-IN` line `deny ip 10.0.0.0 0.255.255.255 any log` | Anti-spoof counter increments (+1) |

---

### 7.2 Verification Protocol Commands

Before executing policy test scripts, clear all access list hit counters:
```cisco
SW-D1# clear access-list counters
SW-D2# clear access-list counters
SW-D3# clear access-list counters
R1# clear access-list counters
```

To verify active interface bindings and inbound filter attachment:
```cisco
SW-D1# show ip interface Vlan40 | include Inbound access list
Inbound access list is ACL-GUEST-IN

SW-D1# show ip interface Vlan10 | include Inbound access list
Inbound access list is ACL-ICU-IN

R1# show ip interface GigabitEthernet0/2 | include Inbound access list
Inbound access list is ACL-EDGE-IN
```

To display active hit counters and match statistics:
```cisco
SW-D1# show access-lists ACL-GUEST-IN
Extended IP access list ACL-GUEST-IN
    10 permit udp any any eq bootps (14 matches)
    20 permit udp any host 172.16.7.4 eq domain (28 matches)
    30 permit tcp any host 172.16.7.4 eq domain
    40 deny ip any 172.16.0.0 0.0.255.255 log (6 matches)
    50 permit tcp any any eq www (45 matches)
    60 permit tcp any any eq 443 (82 matches)
    70 permit icmp any any echo (5 matches)
    80 permit tcp any any established (110 matches)
    90 deny ip any any log
```
