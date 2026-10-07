# `/results` Directory

## 1. Purpose
This directory stores quantitative analytical data, benchmark outputs, and generated graphical charts resulting from running the simulation and benchmark harness in `/sim/`.

## 2. Contents
- `benchmark_results.csv`: Tabular benchmark output recording frame loss rates, retransmission totals, protocol efficiency, and relative gain.
- `protocol_comparison.png`: Generated Matplotlib comparison plot contrasting Go-Back-N and Selective Repeat efficiency and retransmission overhead.

## 3. File Naming Rules
- Tabular result files must use `.csv` with lowercase descriptors: `<experiment>_results.csv`.
- Generated charts and graphs must use `.png` (high DPI) with descriptive names: `<metric>_comparison.png` or `<protocol>_chart.png`.
- Intermediate or serialized data must use `.json`.
