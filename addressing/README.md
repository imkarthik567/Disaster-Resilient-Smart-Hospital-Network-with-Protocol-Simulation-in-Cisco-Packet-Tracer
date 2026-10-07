# `/addressing` Directory

## 1. Purpose
This directory manages the Variable Length Subnet Masking (VLSM) addressing architecture for the entire enterprise hospital network. It contains the algorithmic calculator, machine-readable allocations, and exportable documentation artifacts.

## 2. Contents
- `vlsm_calculator.py`: Python engine allocating subnets from the base `172.16.0.0/16` block. Computes network addresses, subnet masks, wildcard masks, broadcast addresses, default gateways, and host capacity.
- `addressing_table.csv`: Exportable comma-separated table suitable for spreadsheets, IPAM tools, and device automation.
- `addressing_table.md`: Formatted Markdown table for project reports, design reviews, and presentation slides.
- `vlsm_allocations.json`: Structured JSON containing complete metadata for programmatic consumption by configuration generators.

## 3. File Naming Rules
- Calculation engines must end with `_calculator.py`.
- Generated tabular views must follow `addressing_table.<ext>` (`.csv`, `.md`, `.json`).
- Supplementary subnet plans must use `vlsm_<descriptor>.<ext>`.
