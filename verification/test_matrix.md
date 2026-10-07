# Verification & Test Matrix

**Project:** Disaster-Resilient Smart Hospital Network  
**Course:** Computer Networks — VIT SCOPE  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  

---

| Test ID | Phase | Test Objective | Test Procedure | Pass / Fail Criteria | Verification Command | Evidence Reference |
| :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| **TC-L2-01** | Phase 1 (L2) | VLAN isolation & port membership | Verify VLANs 10,20,30,40,50,60,99,999 exist and access ports are assigned | VLAN 1 has no assigned access ports; VLAN 999 contains all unused shutdown ports | `show vlan brief` on all switches | `evidence/phase1_TC-L2-01_vlan_brief.png` |
| **TC-L2-02** | Phase 1 (L2) | 802.1Q trunking & Native VLAN | Inspect trunk links on all inter-switch connections | Native VLAN is 999; VLANs 10-99 permitted; status is `trunking` | `show interfaces trunk` | `evidence/phase1_TC-L2-02_trunk_status.png` |
| **TC-L2-03** | Phase 1 (L2) | STP Root Bridge placement | Check STP root for each VLAN on SW-D1 and SW-D2 | SW-D1 is root for 10,20,50,99; SW-D2 is root for 30,40,60 | `show spanning-tree root` | `evidence/phase1_TC-L2-03_stp_root.png` |
| **TC-L3-01** | Phase 2 (L3) | Inter-VLAN SVI Gateway reachability | Ping SVI default gateways from hosts within each respective VLAN | 100% ICMP echo reply from local SVI gateway | `ping <gateway_ip>` | `evidence/phase2_TC-L3-01_svi_pings.png` |
| **TC-L3-02** | Phase 2 (L3) | DHCP Dynamic Pool Assignment | Verify host receives IP, mask, default gateway, and DNS via DHCP | Correct IP range assigned; DNS = 172.16.4.2 | `ipconfig /all` on host | `evidence/phase2_TC-L3-02_dhcp_lease.png` |
| **TC-SEC-01**| Phase 3 (Sec)| Guest VLAN Isolation (ICU & Surgery) | Guest PC (VLAN 40) attempts to ping ICU sensor (VLAN 10) | Packets dropped at SW-D2; drop counter increments on `BLOCK-GUEST` ACL | `show access-lists BLOCK-GUEST` | `evidence/phase3_TC-SEC-01_guest_block.png` |
| **TC-SEC-02**| Phase 3 (Sec)| Guest VLAN Isolation (Server Farm) | Guest PC attempts HTTP/ICMP to Server Farm (172.16.4.2) | Denied for port 80/ICMP; permitted only for UDP 53 (DNS) | `show access-lists BLOCK-GUEST` | `evidence/phase3_TC-SEC-02_server_block.png` |
| **TC-SEC-03**| Phase 3 (Sec)| Internet NAT Overload (PAT) | Internal PC accesses simulated external Web/DNS (8.8.8.8) | Packet translated to R1 Gig0/2 public IP (203.0.113.2); ping succeeds | `show ip nat translations` | `evidence/phase3_TC-SEC-03_nat_pat.png` |
| **TC-RT-01** | Phase 4 (RT) | OSPF Multi-Area Backbone Convergence | Verify OSPF neighbor adjacencies between R1, R2, and distro switches | Neighbors show `FULL` state; Area 0 & Area 1 routes populated | `show ip ospf neighbor` | `evidence/phase4_TC-RT-01_ospf_neighbors.png` |
| **TC-RT-02** | Phase 4 (RT) | EIGRP Standby Topology Placement | Verify EIGRP routes exist in topology table but NOT active in routing table | EIGRP AD is 120; OSPF (AD 110) installed in RIB | `show ip route ospf` & `show ip eigrp topology` | `evidence/phase4_TC-RT-02_eigrp_standby.png` |
| **TC-RT-03** | Phase 4 (RT) | Primary WAN Failure Reconvergence | Shut down Serial0/0/0 on R1 while continuous ping runs to Remote Clinic | Traffic automatically reroutes over Serial0/0/1 via EIGRP; downtime < 5s | Continuous `ping -t` & `show ip route` | `evidence/phase4_TC-RT-03_failover_eigrp.png` |
| **TC-SBC-01**| Phase 5 (SBC)| 2-D Parity Error Detection & Correction | Transmit 4 sensor bytes, inject single-bit flip on SBC | Error pinpointed at (row, col) coordinates and corrected automatically | SBC Terminal output log | `evidence/phase5_TC-SBC-01_parity2d.png` |
| **TC-SBC-02**| Phase 5 (SBC)| 16-Bit Internet Checksum Verification | Send telemetry packet with induced bit corruption | Valid sum = 0xFFFF; corrupted sum != 0xFFFF; packet rejected | SBC Terminal output log | `evidence/phase5_TC-SBC-02_checksum.png` |
| **TC-SBC-03**| Phase 5 (SBC)| Flow Control: GBN vs Selective Repeat | Transmit 12 frames with simulated drop of frames 3 and 7 | SR completes in 14 transmissions vs 17 for GBN; efficiency gain > 15% | SBC Terminal & harness summary | `evidence/phase5_TC-SBC-03_sr_vs_gbn.png` |
