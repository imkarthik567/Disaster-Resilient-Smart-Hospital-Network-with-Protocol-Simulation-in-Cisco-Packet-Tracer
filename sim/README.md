# `/sim` Directory

## 1. Purpose
This directory contains host-side simulation scripts, benchmark test suites, and analytical harnesses designed to run on a standard workstation (outside Packet Tracer). It systematically quantifies the performance of data-link and transport protocols under variable channel impairments.

## 2. Contents
- `benchmark_harness.py`: Automated loss-sweep benchmark comparing Go-Back-N (GBN) and Selective Repeat (SR). Generates analytical CSV reports and Matplotlib figures stored in `/results/`.
- `test_protocols.py`: Pytest-compatible unit tests validating the algebraic and algorithmic correctness of 2-D parity, 16-bit Internet checksum, GBN, and Selective Repeat routines.

## 3. File Naming Rules
- Standalone benchmark runners must follow `<metric>_harness.py` or `benchmark_<name>.py`.
- Automated test suites must adhere to pytest conventions, starting with `test_*.py`.
- Helper simulation modules must use lowercase names with underscores: `<protocol>_sim.py`.
