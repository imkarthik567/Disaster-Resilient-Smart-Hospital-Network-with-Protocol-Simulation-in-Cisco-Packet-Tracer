# `/sbc` Directory

## 1. Purpose
This directory contains standalone Python 3 scripts designed to execute directly within Cisco Packet Tracer's Single Board Computer (SBC-PT) embedded programming environment. These scripts simulate and evaluate data-link layer error detection, error correction, and sliding-window flow control protocols.

## 2. Contents
- `parity_2d.py`: Two-dimensional parity generator, single-bit error pinpointer, and self-healing engine with burst-error detection.
- `checksum.py`: RFC 1071 16-bit one's complement Internet Checksum algorithm validating simulated ICU patient telemetry.
- `go_back_n.py`: Go-Back-N (GBN) sliding window flow control protocol simulating packet loss, timer timeouts, cumulative ACKs, and full-window retransmission.
- `selective_repeat.py`: Selective Repeat (SR) sliding window protocol with out-of-order buffering, independent ACK tracking, selective frame retransmission, and head-to-head GBN benchmarking.

## 3. How to Run Inside Packet Tracer SBC-PT
1. Place an **SBC-PT** device onto the workspace (e.g., connected to SW-A1 in VLAN 10).
2. Click the SBC device and open the **Programming** tab.
3. Click **New**, select **Python**, and name the file (e.g., `main.py`).
4. Paste the contents of any script from this directory into the editor.
5. Click **Run** and switch to the **Terminal** tab to view live protocol execution and telemetry logs.

## 4. File Naming Rules
- Error detection algorithms must be named after the technique: `parity_<variant>.py` or `checksum.py`.
- Flow control protocols must use lowercase with underscores: `go_back_n.py`, `selective_repeat.py`.
- Embedded scripts must avoid external third-party dependencies to ensure native execution on the SBC-PT MicroPython/Python3 engine.
