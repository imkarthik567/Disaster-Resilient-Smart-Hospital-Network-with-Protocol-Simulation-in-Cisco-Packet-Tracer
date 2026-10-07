# `/topology` — Physical & Logical Topology Architecture

**Project:** Disaster-Resilient Smart Hospital Network  
**Target Simulator:** Cisco Packet Tracer 8.x  
**Team Members:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332) — VIT Vellore  

---

## 1. Overview & Directory Contents

This directory contains the physical and logical network blueprints, hardware specifications, automated builder scripts, and cabling schedules for the Disaster-Resilient Smart Hospital Network. The topology is designed across three operational domains:
1. **Main Hospital Campus (Left Zone):** Dual Distribution Switches (`SW-D1`, `SW-D2`), Access Layer switches (`SW-A1` to `SW-A4`), Central Server Farm, ICU bedside telemetry sensors (`SBC-ICU-101` to `103`), Surgery suites (`SBC-SURG-201`, `202`), IP phones, and Guest Wi-Fi.
2. **Core WAN & Internet Edge (Middle Zone):** Core Routers `R1` (Main Campus ASBR / NAT Edge) and `R2` (Clinic ABR), dual redundant Serial WAN leased lines, and a Gigabit transit link to the Public ISP Gateway (`EDGE-ISP`).
3. **Remote Spoke Clinic (Right Zone):** Single-chassis Branch Gateway Distribution Switch (`SW-D3`), Access Switch (`SW-A5`), Local Survivability Cache Server (`SRV-CACHE`), outpatient clinical terminals, and Guest Wi-Fi.

### Directory Inventory

| File | Purpose & Description |
| :--- | :--- |
| [`bom.md`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/topology/bom.md) | Comprehensive Hardware Bill of Materials, expansion card slot specs, power notes, and per-VLAN host audit table. |
| [`cabling.csv`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/topology/cabling.csv) | Master physical & logical interconnect schedule (58 links: Link-ID, Device A/B, Ports, Cable Types, Layers, Subnets). |
| [`generate_ptbuilder.py`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/topology/generate_ptbuilder.py) | Python automation generator that parses `cabling.csv` and regenerates `build_topology.js`. |
| [`build_topology.js`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/topology/build_topology.js) | Production-grade, defensive JavaScript script for the Cisco Packet Tracer Script Engine. |
| [`pt_builder.js`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/topology/pt_builder.js) | Identical compatibility build of the PTBuilder script. |
| [`topology_diagram.puml`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/topology/topology_diagram.puml) | PlantUML architectural topology source code. |

---

## 2. PTBuilder Automated Topology Script (`build_topology.js`)

`build_topology.js` is a PTBuilder-style automation script written for the **Cisco Packet Tracer Script Engine**. It automates the creation of all 51 network devices, module slot cards, 58 physical/logical cables, and arranges them in a clean 3-zone visual grid.

### 2.1 Defensive Architectural Design
Because the script cannot be interactively debugged until run inside Packet Tracer, it incorporates defensive engineering safeguards:
1. **Centralized Configuration Object (`CONFIG`):** All device model strings (`2911`, `3560-24PS`, `2960-24TT`, `Server-PT`, `SBC-PT`, etc.) are isolated at the top of the file in `CONFIG.models`. If a specific Packet Tracer build expects `"CISCO2911"` instead of `"2911"`, you modify **a single line** at the top of the script.
2. **Modular Decoupled Functions:**
   - `buildDevices(net)`: Creates all 51 device nodes.
   - `installModules(net)`: Powers down routers/laptops, inserts `HWIC-2T` and `WPC300N` cards, and powers them back up.
   - `createLinks(net)`: Connects all physical cables with verified media types.
   - `applyLayout(net)`: Repositions devices to eliminate overlapping icons and establish a clean grid.
   - `reportSummary()`: Aggregates real-time execution metrics.
3. **Fault-Tolerant Try/Catch Guards:** Every device, module, and link has an isolated try/catch block. A failure on a single port or module card logs a warning and immediately proceeds to the next device without crashing the script.
4. **Adaptive API Wrapper:** Dynamically tests for multiple Packet Tracer API method variants (`net.addDevice`, `net.createDevice`, `net.addLink`, `net.createLink`, `dev.setPower`, `dev.moveTo`, `dev.setPosition`).

---

## 3. Step-by-Step Guide: Running the Script in Cisco Packet Tracer 8.x

### Method 1: Using the Script Projects Dialog (Recommended)
1. Launch **Cisco Packet Tracer 8.x** and open a fresh, empty workspace (`File > New`).
2. In the top application menu bar, navigate to:
   ```
   Extensions > Scripting > Script Projects...
   ```
3. In the Script Projects manager window:
   - Click **Open** or **Add Script...**
   - Browse to your local project repository:  
     `c:\Users\karth\OneDrive\Desktop\CN_PROJECT\topology\build_topology.js`
4. Click **Run** or **Execute**.
5. Switch back to the main workspace and observe the devices spawning and cabling automatically.

### Method 2: Direct Script Execution via Activity Wizard / PT Script Console
1. In Packet Tracer, press `Ctrl + Shift + S` or navigate to:
   ```
   Extensions > Scripting > Run Script...
   ```
2. Select `build_topology.js`.
3. Open the **Script Output** console window to view real-time logging.

### 3.1 How to Read the Execution Log
The script outputs structured log messages with timestamps:

| Log Tag | Meaning | Action Required |
| :--- | :--- | :--- |
| `[OK]` | Device, module, link, or coordinate placed successfully. | None. Operation completed. |
| `[INFO]` | Informational status (e.g. Wi-Fi links handled over-the-air via SSID). | None. Normal behavior. |
| `[WARN]` | Non-fatal anomaly (e.g. module already present or API restricted). | Check the Manual Fallback Table below. |
| `[ERROR]` | Failed operation (e.g. device model string rejected by PT). | Check `CONFIG.models` at top of `build_topology.js`. |

At completion, the script prints an audit summary:
```
================================================================================
  PACKET TRACER TOPOLOGY BUILD EXECUTION SUMMARY
================================================================================
  Devices Created:   51 / 51 (Failed: 0)
  Modules Installed: 8 / 8   (Failed: 0)
  Links Established: 58 / 58 (Failed: 0)
  Layout Aligned:    51 / 51 coordinates verified
================================================================================
  [SUCCESS] TOPOLOGY BUILD COMPLETED FLAWLESSLY WITH ZERO ERRORS.
================================================================================
```

---

## 4. Manual Fallback Reference Table

In certain installations or restricted student modes of Cisco Packet Tracer, the scripting engine sandboxes direct hardware manipulation (such as power switches or physical module dragging). Use this fallback reference table to execute any step manually:

| Task / Item | Automated in Script? | If Script Fails: Manual Fallback Step in Packet Tracer GUI |
| :--- | :---: | :--- |
| **Device Creation** | Yes (`buildDevices`) | Open bottom device palette, drag **Routers > 2911**, **Switches > 3560-24PS**, **Switches > 2960**, **End Devices > Server-PT**, **SBC-PT**, **PC-PT**, **Laptop-PT**, **IP Phone-PT**, **Wireless > AccessPoint-PT**. Rename to match `bom.md`. |
| **Router HWIC-2T Installation** | Yes (`installModules`) | Click `R1` (or `R2`) > **Physical** tab > click power rocker switch to **OFF** > drag **HWIC-2T** from left module list into **Slot 0** (bottom right slot) > click power switch to **ON**. |
| **Laptop WPC300N Wireless Card** | Yes (`installModules`) | Click Laptop > **Physical** tab > power switch to **OFF** > drag default copper NIC `PT-LAPTOP-NM-1CFE` out to trash > drag **`WPC300N`** into empty bay > click power to **ON**. |
| **Cisco 7960 IP Phone Power** | *Hardware Sandbox* | In PT, IP phones require an external power brick. Click each of the 6 IP phones (`PHONE-ICU-601`, `SURG-602`, `ADMIN-603`, `CLINIC-601`–`603`) > **Physical** tab > drag the black power adapter cord from bottom right and insert it into the power socket. |
| **Serial WAN Links (DCE/DTE)** | Yes (`createLinks`) | In Cables palette, select **Serial DCE** (red zigzag with clock). **Click R1 first** (`Serial0/0/0`), then connect to **R2** (`Serial0/0/0`). Repeat for `Serial0/0/1`. |
| **EtherChannel Cross-Links** | Yes (`createLinks`) | Connect `SW-D1 FastEthernet0/23` to `SW-D2 FastEthernet0/23` and `Fa0/24` to `Fa0/24` using **Copper Crossover** cable. |
| **802.1Q Switch Uplinks** | Yes (`createLinks`) | Connect access switch uplinks (`SW-A1`–`A4` `Gig0/1`, `Gig0/2`) to distribution ports using standard **Copper Straight-Through** cables as specified in `cabling.csv`. |
| **Guest Wi-Fi SSID Association** | *Dynamic RF* | Click `AP-GUEST` > **Config** tab > **Port 1** > set SSID to `Hospital_Guest_WiFi`. Click `AP-CLINIC-GUEST` > Port 1 > set SSID to `Clinic_Guest_WiFi`. In each Laptop > **Config** > **Wireless0** > enter matching SSID. |

---

## 5. Python Generator (`generate_ptbuilder.py`)

Whenever [`/topology/cabling.csv`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/topology/cabling.csv) is modified (e.g. adding a link, changing a port, or introducing an expansion switch), re-run the Python generator to regenerate the JavaScript scripts:

```bash
# Regenerate PTBuilder scripts from cabling.csv
python topology/generate_ptbuilder.py

# Or run via project task runner
python tasks.py docs
```

The generator will:
1. Re-parse all devices, media types, and interfaces from `cabling.csv`.
2. Re-compute the grid coordinate matrix (`LAYOUT_COORDINATES`).
3. Re-generate `build_topology.js` and `pt_builder.js` with updated definitions.
