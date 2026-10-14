# Infrastructure Device Hardening Checklist & Verification Audit
**Project:** Disaster-Resilient Smart Hospital Network (VIT SCOPE — Computer Networks)  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  
**Standard Compliance:** Cisco Packet Tracer 8.x | CIS Cisco IOS Benchmark v4.1.0 | NIST SP 800-123 (Guide to General Server Security)  

---

## 1. Executive Summary & Hardening Framework

To ensure that the hospital network infrastructure remains resilient against unauthorized access, reconnaissance, credential sniffing, and lateral privilege escalation, every routing and switching node is hardened against a standardized baseline. 

The hardening policy covers:
1. **Administrative Access Control:** Elimination of cleartext passwords (`service password-encryption`), mandatory privileged secret hashing (`enable secret class123`), and role-based local accounts (`privilege 15`).
2. **Encrypted Remote Management:** Mandatory cryptographic SSH Version 2 (`crypto key generate rsa modulus 1024`, `ip ssh version 2`), suppression of Telnet (`transport input ssh`), and aggressive session timeout thresholds (`exec-timeout 15 0`).
3. **Management Plane Whitelisting:** Dedicated standard access-list `ACL-VTY-SSH` applied inbound on all VTY lines, locking CLI access exclusively to authorized Network Operations Center (NOC) and clinic console IP addresses.
4. **Attack Surface Minimization:** Disabling unused management daemons (`no ip http server`, `no ip http secure-server`, `no ip source-route`) and shutting down/parking all unused physical switchports in parking VLAN 999.
5. **Reconnaissance Suppression:** Disabling Cisco Discovery Protocol (`no cdp enable`) on external demarcation links and public-facing guest Wi-Fi access ports.
6. **Centralized Visibility & Time Sync:** Forwarding all security audit events to the central syslog server (`logging host 172.16.7.4`) and synchronizing system clocks with the central hospital NTP server (`ntp server 172.16.7.4`).

---

## 2. Reusable Baseline Hardening Snippet

The following snippet represents the golden configuration template applied uniformly across all hospital routers (`R1`, `R2`) and switches (`SW-D1`, `SW-D2`, `SW-D3`, `SW-D4`, `SW-A1`, `SW-A2`, `SW-A3`, `SW-A4`, `SW-A5`):

```cisco
! ==============================================================================
! GOLDEN BASELINE HARDENING TEMPLATE (CISCO PACKET TRACER 8.x COMPLIANT)
! ==============================================================================

! 1. Host Identity & DNS Broadcast Suppression
no ip domain-lookup
ip domain-name hospital.local

! 2. Credential Encryption & Management Authentication
enable secret class123
service password-encryption
username admin privilege 15 secret class123

! 3. Cryptographic SSH Version 2 Configuration
crypto key generate rsa modulus 1024
ip ssh version 2
ip ssh time-out 60
ip ssh authentication-retries 3

! 4. Management Plane Access Control (VTY Filter)
ip access-list standard ACL-VTY-SSH
 remark Permit Central Hospital NOC Management Console
 permit host 172.16.7.212
 remark Permit Remote Clinic Local Management Station
 permit host 172.16.8.75
 remark Deny all other administrative attempts with logging
 deny any log
exit

! 5. Console Line Security
line con 0
 password cisco
 login
 logging synchronous
 exec-timeout 15 0
exit

! 6. VTY Lines Hardening (SSH Only, Restricted Access-Class, Session Timeout)
line vty 0 4
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

line vty 5 15
 login local
 transport input ssh
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
exit

! 7. Legal Disclaimer & Security Warning Banner
banner motd ^C
================================================================================
  UNAUTHORIZED ACCESS TO THIS NETWORK DEVICE IS STRICTLY PROHIBITED!
  All activities, keystrokes, and sessions are logged and monitored.
  Violators will be prosecuted under applicable computer fraud regulations.
================================================================================
^C

! 8. Disable Insecure / Unnecessary Management Services
no ip http server
no ip http secure-server
no ip source-route

! 9. Centralized Time Synchronization (NTP Client)
ntp server 172.16.7.4

! 10. Centralized Logging (Syslog Client)
logging host 172.16.7.4
logging trap informational
logging buffered 4096 informational
```

---

## 3. Hardening Checklist with Single Verification Commands

Each item below provides the **exact, single verification command** used to audit compliance during laboratory evaluation:

| Control ID | Hardening Requirement | Verification Command | Expected Output & Pass Criteria | Enforcing Scope | Compliance |
| :---: | :--- | :--- | :--- | :---: | :---: |
| **SEC-01** | **Enable Secret Configured** | `show running-config \| include enable secret` | `enable secret 5 $1$...` (MD5 hash present; no cleartext `enable password`) | All Devices | **PASS** |
| **SEC-02** | **Service Password Encryption** | `show running-config \| include password-encryption` | `service password-encryption` present; all local passwords stored as Type 7 ciphertext | All Devices | **PASS** |
| **SEC-03** | **Local Admin Account (Priv 15)**| `show running-config \| include username` | `username admin privilege 15 secret ...` configured with individual credential | All Devices | **PASS** |
| **SEC-04** | **SSH Version 2 Enforced** | `show ip ssh` | `SSH Enabled - version 2.0`<br>`Authentication timeout: 60 secs; Authentication retries: 3` | All Devices | **PASS** |
| **SEC-05** | **Transport Input SSH Only** | `show running-config \| section line vty` | `transport input ssh` configured on both `vty 0 4` and `vty 5 15` (Telnet disabled) | All Devices | **PASS** |
| **SEC-06** | **VTY Access-Class Whitelist** | `show access-lists ACL-VTY-SSH` | `Standard IP access list ACL-VTY-SSH`<br>`10 permit host 172.16.7.212`<br>`20 permit host 172.16.8.75`<br>`30 deny any log` | All Devices | **PASS** |
| **SEC-07** | **VTY Access-Class Binding** | `show running-config \| section line vty` | `access-class ACL-VTY-SSH in` present on lines `0 4` and `5 15` | All Devices | **PASS** |
| **SEC-08** | **Inactivity Exec Timeout** | `show running-config \| include exec-timeout` | `exec-timeout 15 0` present under `line con 0`, `line vty 0 4`, and `line vty 5 15` | All Devices | **PASS** |
| **SEC-09** | **Console Synchronous Logging**| `show running-config \| section line con` | `logging synchronous` enabled (prevents unsolicited syslog messages from interrupting CLI input) | All Devices | **PASS** |
| **SEC-10** | **Legal Warning Banner** | `show running-config \| section banner motd` | Structured warning banner present warning unauthorized intruders of monitoring and prosecution | All Devices | **PASS** |
| **SEC-11** | **Disable DNS Lookup Lockups**| `show running-config \| include domain-lookup` | `no ip domain-lookup` present (prevents router hanging when mistyping a CLI command) | All Devices | **PASS** |
| **SEC-12** | **Disable Insecure HTTP Server**| `show running-config \| include ip http` | `no ip http server`<br>`no ip http secure-server` (Eliminates unauthenticated HTTP web admin vulnerabilities) | All Hospital Devices | **PASS** |
| **SEC-13** | **Disable CDP on Untrusted Ports**| `show cdp interface <port>` | `CDP is not enabled on <port>` (Verified on R1 Gi0/2, SW-A4 Fa0/10, SW-A5 Fa0/10) | Untrusted Interfaces | **PASS** |
| **SEC-14** | **Centralized NTP Time Sync** | `show running-config \| include ntp server` | `ntp server 172.16.7.4` pointing to central authoritative time server | All Hospital Devices | **PASS** |
| **SEC-15** | **Centralized Syslog Logging** | `show running-config \| include logging host` | `logging host 172.16.7.4`<br>`logging trap informational`<br>`logging buffered 4096 informational` | All Hospital Devices | **PASS** |
| **SEC-16** | **Shutdown & Park Unused Ports**| `show interfaces status` or `show ip interface brief` | All unallocated ports placed in `shutdown` state and assigned to isolated `VLAN 999` | All Switches | **PASS** |

---

## 4. Per-Device Verification Command & Output Reference

### 4.1 Core Routers (`R1` & `R2`)

#### Verification 1: SSH Version 2 Operational Status
```cisco
R1# show ip ssh
SSH Enabled - version 2.0
Authentication timeout: 60 secs; Authentication retries: 3
```

#### Verification 2: VTY Whitelist ACL & Hit Counters
```cisco
R1# show access-lists ACL-VTY-SSH
Standard IP access list ACL-VTY-SSH
    10 permit host 172.16.7.212 (4 matches)
    20 permit host 172.16.8.75
    30 deny any log
```

#### Verification 3: CDP Disabled on External Edge Link
```cisco
R1# show cdp interface GigabitEthernet0/2
GigabitEthernet0/2 is down, line protocol is down
  Encapsulation ARPA
  Sending CDP packets every 60 seconds
  Holdtime is 180 seconds
  CDP is not enabled on this interface
```

#### Verification 4: Centralized Logging Configuration
```cisco
R1# show logging | include Logging to
    Logging to 172.16.7.4 (udp port 514, audit logging enabled)
```

---

### 4.2 Multilayer Distribution Switches (`SW-D1`, `SW-D2`, `SW-D3`, `SW-D4`)

#### Verification 1: Service Password Encryption Audit
```cisco
SW-D1# show running-config | include password
service password-encryption
enable secret 5 $1$mERr$hx5rVt7rPNoS4wqbXReTa/
 password 7 0822455D0A16
```

#### Verification 2: Insecure Web Daemons Disabled
```cisco
SW-D1# show running-config | include ip http
no ip http server
no ip http secure-server
```

#### Verification 3: VTY Line Protection
```cisco
SW-D1# show running-config | section line vty
line vty 0 4
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
 login local
 transport input ssh
line vty 5 15
 access-class ACL-VTY-SSH in
 exec-timeout 15 0
 login local
 transport input ssh
```

#### Verification 4: NTP Association
```cisco
SW-D1# show running-config | include ntp
ntp server 172.16.7.4
```

---

### 4.3 Layer-2 Access Switches (`SW-A1`, `SW-A2`, `SW-A3`, `SW-A4`, `SW-A5`)

#### Verification 1: Unused Port Parking in VLAN 999
```cisco
SW-A4# show vlan id 999
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
999  Parking_Native                   active    Fa0/1, Fa0/2, Fa0/3, Fa0/4,
                                                Fa0/5, Fa0/6, Fa0/7, Fa0/8,
                                                Fa0/9, Fa0/11, Fa0/12, Fa0/13,
                                                Fa0/14, Fa0/15, Fa0/16, Fa0/17,
                                                Fa0/18, Fa0/19, Fa0/20, Fa0/21,
                                                Fa0/22, Fa0/23, Fa0/24
```

#### Verification 2: CDP Disabled on Guest Wi-Fi Access Point Port
```cisco
SW-A4# show cdp interface FastEthernet0/10
FastEthernet0/10 is up, line protocol is up
  Encapsulation ARPA
  CDP is not enabled on this interface
```

#### Verification 3: Host PortFast & BPDU Guard Enforcement
```cisco
SW-A1# show spanning-tree interface FastEthernet0/4 detail | include (PortFast|BPDU)
  The port is in the portfast mode
  Bpdu guard is enabled
```

---

## 5. Cisco Packet Tracer 8.x Support & Limitations Analysis

During test execution, specific Cisco IOS features were analyzed for simulation fidelity inside Packet Tracer 8.x:

| Feature / Command | Packet Tracer 8.x Behavior | Limitation or Operational Finding | Hardening Workaround Deployed |
| :--- | :--- | :--- | :--- |
| **`ntp server <ip>`** | **Supported** | Basic client association operates. However, cryptographic NTP authentication (`ntp authenticate`, `ntp trusted-key`) is partially stubbed on 2960 models. | Basic IP-directed client `ntp server 172.16.7.4` deployed across all nodes. |
| **`logging host <ip>`** | **Supported** | Standard UDP 514 syslog generation is fully functional. Packets appear in Packet Tracer simulation mode targeting `172.16.7.4`. Secure TLS syslog (`logging host ... transport tls`) is unsupported in PT. | Standard syslog with `logging trap informational` and 4KB local buffer. |
| **`crypto key generate rsa`** | **Supported** | Supports modulus up to 2048 bits. Keys persist across simulated reboots. | 1024-bit modulus standard deployed across all devices. |
| **`no cdp enable` (per interface)** | **Supported** | Reliably disables CDP packet transmission on designated interfaces while leaving global CDP intact for internal discovery. | Applied on edge Gi0/2 and guest AP access ports. |
| **`service password-encryption`** | **Supported** | Reversibly obfuscates passwords using Vigenère Type 7 cipher. | Deployed on all devices in conjunction with MD5 Type 5 `enable secret`. |
| **`no ip http server`** | **Supported** | Suppresses the built-in HTTP daemon on switches and routers. | Deployed on all hospital gear; enabled only on `EDGE-ISP` for test simulation. |
| **AAA TACACS+/RADIUS** | **Partially Supported** | Server-PT supports AAA service, but local `username ... secret` is more robust for standalone lab grading without external dependencies. | Standalone local database with `privilege 15` secrets and VTY access-class whitelist. |
