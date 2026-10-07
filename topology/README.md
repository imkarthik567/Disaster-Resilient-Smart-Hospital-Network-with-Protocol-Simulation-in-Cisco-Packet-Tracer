# `/topology` Directory

## 1. Purpose
This directory houses all resources related to the physical and logical network topology design for the Disaster-Resilient Smart Hospital Network. It provides the blueprints and interconnection schedules required to reconstruct or audit the topology in Cisco Packet Tracer 8.x.

## 2. Contents
- `cabling_table.md`: Comprehensive port-by-port interconnectivity table covering media types, trunking modes, and subnets.
- `topology_diagram.puml`: PlantUML source code for generating architectural and physical network topology diagrams.
- `pt_builder.py`: Python CLI tool that generates device inventories, hardware module installation instructions, and cabling schedules.

## 3. File Naming Rules
- Cabling tables and port mappings must use lowercase alphanumeric names with underscores: `cabling_<descriptor>.md`.
- Diagram source files must end with standard extensions: `.puml` (PlantUML), `.mmd` (Mermaid), or `.drawio`.
- Scripts facilitating topology construction must be prefixed with `pt_` or end with `_builder.py`.
