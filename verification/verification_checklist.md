# Verification Checklist

**Project:** Disaster-Resilient Smart Hospital Network  
**Usage:** After pasting each device config, run these `show` commands and compare against expected output.

---

## Phase 1: Layer 2 — VLANs, Trunking, STP

### On Every Switch (SW-D1, SW-D2, SW-D3, SW-A1–A5)

```
show vlan brief
```
**Expected:** VLANs 10, 20, 30, 40, 50, 60, 99, 999 exist. Access ports assigned to correct VLANs. VLAN 1 has no ports.

```
show interfaces trunk
```
**Expected:** Trunk links show VLANs 10,20,30,40,50,60,99 as allowed/active. Native VLAN = 999.

```
show spanning-tree summary
```
**Expected:** SW-D1 is root for VLANs 10,20,50,99. SW-D2 is root for VLANs 30,40,60.

---

## Phase 2: Layer 3 — SVIs, Inter-VLAN Routing

### On Distribution Switches (SW-D1, SW-D2, SW-D3)

```
show ip interface brief
```
**Expected:** All SVI interfaces show `up/up` with correct IP addresses per addressing plan.

```
show ip route
```
**Expected:** Connected routes for local VLANs. Static default route pointing to R1 (or R2 for SW-D3).

### Inter-VLAN Ping Test (from any host)

- ICU host → Admin host: **should succeed** (both are trusted VLANs)
- ICU host → Server: **should succeed**
- Guest host → ICU host: **should FAIL** (ACL blocks it)
- Guest host → Internet: **should succeed** (NAT allows it)

---

## Phase 3: Routing — OSPF + EIGRP Failover

### On R1

```
show ip ospf neighbor
```
**Expected:** R2 appears as FULL neighbor via Se0/0/0.

```
show ip eigrp neighbors
```
**Expected:** R2 appears as neighbor via Se0/0/1.

```
show ip route ospf
```
**Expected:** Remote clinic subnets (172.16.4.64/27, .96/27, .128/27, .160/28, .176/28) appear as `O IA` via Se0/0/0.

```
show ip route eigrp
```
**Expected:** EMPTY (EIGRP routes not installed because AD 120 > OSPF AD 110).

### Failover Test

1. On R1: `interface Se0/0/0` → `shutdown`
2. Wait ~30 seconds for OSPF dead timer to expire.
3. Run `show ip route` on R1.
4. **Expected:** Remote clinic subnets now appear as `D` (EIGRP) via Se0/0/1.
5. Ping from Main Hospital host to Remote Clinic host — **should succeed** via backup path.
6. Re-enable: `no shutdown` on Se0/0/0. After OSPF reconverges, routes should switch back to `O IA`.

```
show ip route
```
**Expected after failover:** `D  172.16.4.64/27 [120/...] via 172.16.4.198, Se0/0/1`

---

## Phase 4: Security — ACLs and NAT

### ACL Verification

```
show access-lists
```
**Expected:** `BLOCK-GUEST` ACL with match counters. After a denied ping from Guest → ICU, the deny counter should increment.

### NAT Verification

```
show ip nat translations
```
**Expected:** After a host browses the Internet, inside local/global translations appear.

```
show ip nat statistics
```
**Expected:** Hit count > 0 on the NAT rule.

---

## Phase 5: QoS

```
show policy-map
```
**Expected:** `HOSPITAL-QOS` policy with class definitions for VITALS-VOICE and IMAGING.

```
show policy-map interface Serial0/0/0
```
**Expected:** Policy applied; packet/byte counters may or may not increment in PT (PT limitation).

---

## Phase 6: Services — DNS, DHCP, HTTP

### DHCP

On any host configured for DHCP:
```
ipconfig /renew     (on PC command prompt)
ipconfig            (verify correct IP, mask, gateway, DNS)
```
**Expected:** IP from correct VLAN pool, gateway matches SVI address.

### DNS

```
nslookup records.hospital.local
```
**Expected:** Resolves to the PT Server IP (172.16.4.2 or .3).

### HTTP

Open web browser on a PC → `http://records.hospital.local`  
**Expected:** Hospital portal page loads.

---

## Phase 7: SBC Python Scripts

### On each SBC-PT device

1. Open **Programming** tab → paste script → **Run**
2. Switch to **Terminal** tab
3. **Expected output** for each script:
   - **2D Parity:** Shows original data, parity matrix, error injection, detection result
   - **Checksum:** Shows segments, computed checksum, verification pass/fail
   - **Go-Back-N:** Shows window slides, timeout events, retransmissions, final stats
   - **Selective Repeat:** Shows individual ACK/NAK, selective retransmissions, final stats

---

## Phase 8: Simulation Mode Analysis

### TCP Three-Way Handshake

1. Switch to **Simulation Mode** (stopwatch icon)
2. Filter: TCP only
3. From a PC, open browser to `http://records.hospital.local`
4. Step through PDUs: observe SYN → SYN-ACK → ACK
5. Click each PDU to inspect sequence numbers, flags, window size

### DNS Resolution

1. Filter: DNS only
2. From a PC, `nslookup records.hospital.local`
3. Observe: DNS query (UDP 53) → DNS response

### OSPF Reconvergence

1. Start continuous ping from Main Hospital PC to Remote Clinic PC
2. In Simulation Mode, filter: OSPF
3. Shut down R1 Se0/0/0
4. Observe: OSPF Hello timeout → LSA flooding → SPF recalculation
5. Count dropped ICMP packets to estimate convergence time
