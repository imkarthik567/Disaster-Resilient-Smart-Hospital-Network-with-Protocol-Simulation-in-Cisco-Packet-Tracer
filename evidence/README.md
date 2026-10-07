# `/evidence` Directory

## 1. Purpose
This directory stores empirical verification evidence, including annotated Packet Tracer screenshots, Simulation Mode PDU envelope captures, terminal logs, and CLI output transcripts validating the project objectives.

## 2. File Naming Rules
Every file placed in this directory must strictly follow the structured naming convention tied to the test cases in `verification/test_matrix.md`:

```
<phase>_<test_id>_<brief_description>.<ext>
```

### Examples:
- `phase1_TC-L2-01_vlan_brief.png`
- `phase2_TC-L3-01_svi_pings.png`
- `phase3_TC-SEC-01_guest_block.png`
- `phase4_TC-RT-01_ospf_neighbors.png`
- `phase4_TC-RT-03_failover_eigrp.png`
- `phase5_TC-SBC-01_parity2d_terminal.txt`
- `phase5_TC-SBC-03_sr_vs_gbn_run.txt`

## 3. Supported File Formats
- Images / Screenshots: `.png` or `.jpg` (crisp resolution showing device CLI / PDU envelope details)
- Text Logs / Transcripts: `.txt` or `.log`
- Captured PDU Streams: `.pcap` or `.json` (if exported)
