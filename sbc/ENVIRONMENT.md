# Packet Tracer 8.x SBC-PT Embedded Python Execution Environment

**Project:** Disaster-Resilient Smart Hospital Network with Protocol Simulation in Cisco Packet Tracer  
**Institution:** VIT Vellore — School of Computer Science and Engineering (SCOPE)  
**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  
**Course:** Computer Networks (Winter Semester 2025–26)  
**Target Platform:** Cisco Packet Tracer 8.x Single Board Computer (SBC-PT) & Microcontroller (MCU-PT)  

---

## 1. Executive Overview & Runtime Architecture

Cisco Packet Tracer 8.x includes an embedded Internet of Things (IoT) simulation subsystem featuring two programmable hardware modules:
1. **SBC-PT (Single Board Computer)**: Modeled conceptually after a Raspberry Pi or BeagleBone Black, equipped with a FastEthernet network interface (`FastEthernet0`), USB ports, wireless slot, and ten general-purpose I/O pins (Digital pins `D0`–`D9`, Analog pins `A0`–`A5`).
2. **MCU-PT (Microcontroller Unit)**: Modeled after an Arduino / ATmega platform, optimized for low-level pin interfacing.

```
+----------------------------------------------------------------------------------------------------+
|                                    SBC-PT EXECUTION ENVIRONMENT                                    |
|                                                                                                    |
|  [ PACKET TRACER GUI ]                                                                             |
|  Device Configuration Dialog -> "Programming" Tab                                                 |
|                                                                                                    |
|  +----------------------------------------------------------------------------------------------+  |
|  | File Manager: [ main.py ] [ project.json ]                                                   |  |
|  | Controls:     [ Run ] [ Stop ] [ New File ]                                                  |  |
|  +----------------------------------------------------------------------------------------------+  |
|  | Embedded Python Code Editor                                                                  |  |
|  |   from gpio import *                                                                         |  |
|  |   from time import *                                                                         |  |
|  |   def main():                                                                                |  |
|  |       pinMode(0, IN)                                                                         |  |
|  |       print("Telemetry Active...")                                                           |  |
|  +----------------------------------------------------------------------------------------------+  |
|  | Run Console (Standard Output & Exceptions):                                                  |  |
|  |   > Telemetry Active...                                                                      |  |
|  +----------------------------------------------------------------------------------------------+  |
|                                                                                                    |
|  [ EMBEDDED ENGINE ]                                   [ NETWORK & PERIPHERAL HOOKS ]              |
|  - Custom AST / Brython / MicroPython Interpreter     - FastEthernet0 (172.16.7.138/26)            |
|  - Python 3.x Syntax Subset                           - Digital Pins D0 - D9 (Buttons, LEDs)       |
|  - Single-Threaded Event Loop                         - Analog Pins A0 - A5 (Sensors: SpO2, ECG)   |
|  - NO Native C-Extension Libraries                     - IoT Server Registration API                |
+----------------------------------------------------------------------------------------------------+
```

### The Embedded Runtime Reality
Unlike desktop CPython running on Linux or Windows, Packet Tracer's Python environment is a **sandboxed, simulated interpreter** embedded directly within the Packet Tracer C++ application core. It provides a lightweight language engine designed for educational IoT demonstrations, but lacks the vast majority of standard C-extension libraries found in full Python distributions.

---

## 2. Script Lifecycle, Naming, Execution & Console Output

### 1. Project Structure & File Naming
* In Packet Tracer, an SBC project consists of an internal directory managed within the device's **Programming** tab.
* The default entry point script is typically named **`main.py`** or **`app.py`**.
* Multiple `.py` files can be stored within the same project directory, but cross-module importing (`import my_module`) is often restricted or version-dependent. Therefore, production SBC scripts should either be **monolithic standalone scripts** or use strictly relative intra-project imports.

### 2. Execution Model & Cooperative Scheduling
* Clicking the **Run** button launches the script. The script continues running until:
  * The user clicks **Stop**.
  * The script reaches the end of its top-level statements.
  * An unhandled exception terminates the interpreter.
* **CRITICAL PITFALL — UI Lockup on Tight Loops**:  
  Packet Tracer's interpreter is **single-threaded and non-preemptive**. A `while True:` loop without cooperative sleep yields will completely freeze the Packet Tracer GUI thread:
  ```python
  # DANGEROUS: Will freeze Packet Tracer 8.x
  while True:
      val = digitalRead(0)

  # CORRECT: Yields CPU cycles to the Packet Tracer event simulation scheduler
  while True:
      val = digitalRead(0)
      sleep(0.1)  # Or delay(100)
  ```

### 3. Console Output & Debugging
* Standard `print(...)` statements are redirected to the **Run Console** output pane at the bottom of the Programming tab.
* The console supports basic string printing, integer interpolation, and newline flushing.
* ANSI terminal color escape codes (`\033[31m`) are generally **not interpreted** and will display as raw characters; all console logs should use clean ASCII text.

---

## 3. Available Packet Tracer Built-in Modules

Packet Tracer exposes custom hardware-interaction modules that exist only within the SBC/MCU sandbox:

### 1. The `gpio` Module (Hardware Pin Interfacing)
The `gpio` module provides low-level digital and analog pin access, modeled after the Arduino Wiring / WiringPi API:

```python
from gpio import *

# Pin Modes
pinMode(pin, mode)
# pin: Integer 0 to 9 (Digital D0-D9) or 0 to 5 (Analog A0-A5)
# mode: IN (0) or OUT (1) (also INPUT / OUTPUT in some builds)

# Digital Operations
val = digitalRead(pin)        # Returns HIGH (1) or LOW (0)
digitalWrite(pin, value)      # Sets pin to HIGH (1) or LOW (0)

# Analog Operations
sensor_val = analogRead(pin)  # Reads analog voltage, returns integer 0 - 1023
analogWrite(pin, pwm_val)     # Writes PWM duty cycle (0 - 255)

# Custom Operations (for complex smart things like LCDs, servos, or RFID)
customWrite(pin, string_value)
```

#### Common Medical Sensor & Actuator Pin Mappings on SBC-PT:
* **Pin D0 (Digital Input)**: Bedside Emergency Nurse Call Push Button (normally `LOW`, pulls `HIGH` on press).
* **Pin D1 (Digital Output)**: Critical Cardiac Alarm Siren / Buzzer.
* **Pin D2 (Digital Output)**: Visual Alert LED (Flashing Red on Vent Failure).
* **Pin A0 (Analog Input)**: Patient ECG Heart Rate Pulse Sensor (dynamic voltage $0–1023 \rightarrow 40–180\text{ BPM}$).
* **Pin A1 (Analog Input)**: Pulse Oximeter Sensor ($0–1023 \rightarrow 70–100\%\text{ SpO}_2$).

---

### 2. The `time` Module (Timing & Scheduling)
* **`sleep(seconds)`**: Suspends execution for a floating-point number of seconds (e.g. `sleep(0.5)`).
* **`delay(milliseconds)`**: Alternative Arduino-style millisecond pause (e.g. `delay(500)`).
* **`uptime()`**: Returns total simulation seconds elapsed since the device booted.
* **`time()`**: In some builds, returns simulated Unix epoch timestamp.

---

### 3. Networking & Communications Modules
Packet Tracer provides multiple mechanisms for network communication, depending on the device model and firmware:
* **`realtime` / `IoEClient`**: Used for Packet Tracer IoT Registration Server communications:
  ```python
  from IoEClient import *
  IoEClient.setup({
      "type": "PatientMonitor",
      "states": [{"name": "HeartRate", "type": "int", "unit": "BPM"}]
  })
  IoEClient.sendReport("HeartRate", 72)
  ```
* **Raw Sockets (`socket` module)**:
  * In standard desktop Python, network applications open BSD sockets (`import socket`).
  * In Packet Tracer 8.x, the presence of `socket` is **uncertain and version-dependent**:
    * Some builds allow basic UDP client sockets: `sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)`.
    * Other builds throw `ImportError: No module named 'socket'`, restricting network I/O to IoT server reporting.
  * **Our Architecture Solution**: We implement a self-probing diagnostic script (`probe.py`) to confirm socket availability, and design all core protocol logic to be transport-agnostic!

---

## 4. Standard Library Limitations: Confirmed vs. Uncertain

| Feature / Module | Purpose | Status in PT 8.x SBC-PT | Fallback / Mitigation Strategy |
| :--- | :--- | :---: | :--- |
| **`sys`** | System version & platform inspection | **CONFIRMED** (Partial) | Use only `sys.version` and `sys.platform`; avoid complex OS hooks. |
| **`math`** | Mathematical functions (`floor`, `ceil`) | **CONFIRMED** | Built-in integer arithmetic (`//`, `%`, `abs`) is always preferred. |
| **`gpio`** | Digital/Analog pin manipulation | **CONFIRMED** | Primary hardware interfacing module for SBC sensors and alarms. |
| **`time`** | `sleep()`, `delay()`, `uptime()` | **CONFIRMED** | Use `sleep()` in every loop to prevent GUI thread lockups. |
| **Bitwise Operators** | `&`, `|`, `^`, `~`, `<<`, `>>` | **CONFIRMED** | **Primary mechanism** for parity matrices and RFC 1071 checksums. |
| **`random`** | Stochastic loss & bit corruption | **UNCERTAIN** | If missing, use our custom pure-Python Linear Congruential Generator (LCG). |
| **`struct`** | Binary packing (`pack('>H')`) | **UNAVAILABLE / UNCERTAIN** | **BANNED IN CORE**: Replaced with pure-Python bit shifts: `(b0 << 8) | b1`. |
| **`binascii` / `zlib`** | Hex encoding, CRC32, compression | **UNAVAILABLE** | **BANNED IN CORE**: Use native string formatting (`f"{val:02x}"` or `%02x`). |
| **`threading`** | Multi-threaded timers & receivers | **UNAVAILABLE** | **BANNED**: Use single-threaded cooperative event loops with `uptime()`. |
| **File I/O (`open`)** | Disk persistence | **VIRTUAL ONLY** | In-memory only; does not persist to host filesystem upon reload. |
| **`socket` (UDP/TCP)**| Direct network packet transmission | **PROBE TARGET** | Test via `probe.py`; if absent, wrap in adapter with terminal logging. |

---

## 5. Master Feature Matrix: Confirmed, Uncertain & Test Protocol

```
+----------------------------------------------------------------------------------------------------+
|                                    MASTER FEATURE STATUS MATRIX                                    |
+------------------------------+-------------------------------+-------------------------------------+
| Capability / Module          | Status                        | Operational Impact & Action Plan    |
+------------------------------+-------------------------------+-------------------------------------+
| Python 3 Language Syntax     | [CONFIRMED]                   | Functions, classes, lists, dicts.   |
| Basic Data Types (int, str)  | [CONFIRMED]                   | Arbitrary precision integers work.  |
| Digital Read/Write (D0-D9)   | [CONFIRMED]                   | Verified for buttons and sirens.    |
| Analog Read/Write (A0-A5)    | [CONFIRMED]                   | Verified for telemetry sensors.     |
| sleep() / delay() Yielding   | [CONFIRMED]                   | Mandatory inside all loop bodies.   |
| sys.version / sys.platform   | [CONFIRMED]                   | Basic runtime identification.       |
+------------------------------+-------------------------------+-------------------------------------+
| random module (randint, seed)| [UNCERTAIN: VERSION-DEPENDENT]| May lack seed() or sample().        |
| String f-strings (f"...")    | [UNCERTAIN: VERSION-DEPENDENT]| Fall back to % or .format() if old. |
| BSD Socket Module (socket)   | [UNCERTAIN: VERSION-DEPENDENT]| Test via probe.py in Packet Tracer. |
| json module (dumps, loads)   | [UNCERTAIN: VERSION-DEPENDENT]| Test via probe.py in Packet Tracer. |
| Virtual File I/O (open)      | [UNCERTAIN: TRANSIENT ONLY]   | Only exists within current session. |
+------------------------------+-------------------------------+-------------------------------------+
| threading / multiprocessing  | [CONFIRMED ABSENT]            | Multithreading is not supported.    |
| struct / zlib / binascii     | [CONFIRMED ABSENT]            | Native C-extensions do not exist.   |
| pip / External Packages      | [CONFIRMED ABSENT]            | Zero third-party package support.   |
+------------------------------+-------------------------------+-------------------------------------+
```

### What You Should Test Yourself First
To verify the exact runtime capabilities of your specific Packet Tracer build (e.g. 8.0, 8.1, 8.2, 8.2.1, or 8.2.2):
1. **Load `probe.py` onto an SBC-PT**: Follow the execution guide in Section 7.
2. **Review the Probe Log**: Note which modules return `[OK]` and which return `[FAILED]`.
3. **Inspect Socket Support**: Check whether `socket.socket(AF_INET, SOCK_DGRAM)` succeeds.

---

## 6. Architectural Blueprint for All Later SBC Code

To ensure that our medical telemetry algorithms run with 100% reliability in Packet Tracer while remaining fully testable on standard development PCs, all SBC code is architected into **three decoupled tiers**:

```
+----------------------------------------------------------------------------------------------------+
|                                   THREE-TIER SBC CODE ARCHITECTURE                                 |
|                                                                                                    |
|   TIER 1: PURE-PYTHON CORE ENGINE (/sbc/core/)                                                     |
|   - 100% pure Python with ZERO non-builtin dependencies                                            |
|   - Bitwise arithmetic (&, |, ^, <<, >>) replaces struct/binascii                                  |
|   - Deterministic Linear Congruential Generator (LCG) replaces random                              |
|   - Portable across both Desktop CPython 3.12+ and Packet Tracer SBC-PT                            |
|   - Modules:                                                                                       |
|     * parity_2d.py     (2D Parity Matrix, Single-Bit Correction, Burst Detection)                  |
|     * checksum.py      (RFC 1071 16-Bit Internet Checksum Engine)                                  |
|     * go_back_n.py     (Go-Back-N Sliding Window State Machine)                                    |
|     * selective_rep.py (Selective Repeat Out-of-Order Buffer Engine)                              |
|                                                                                                    |
|                                         |                                                          |
|                    +--------------------+--------------------+                                     |
|                    |                                         |                                     |
|                    v                                         v                                     |
|   TIER 2: THIN PACKET TRACER ADAPTER        TIER 3: HOST-SIDE TEST HARNESS                         |
|   (/sbc/adapters/)                          (/sim/ & /tests/)                                      |
|   - Auto-detects runtime environment        - Runs on standard workstation PC                      |
|   - If in Packet Tracer:                    - Imports exact same /sbc/core/ files                  |
|     * Binds gpio (pinMode, digitalRead)     - Automated unit tests via tasks.py test               |
|     * Binds SBC FastEthernet IP stack       - Benchmark sweep across 0% - 30% loss rates           |
|     * Translates sensor voltage to vitals   - Head-to-head GBN vs SR efficiency comparison         |
|   - If on PC:                               - Zero code duplication between PT and PC              |
|     * Emulates hardware pins in terminal                                                           |
+----------------------------------------------------------------------------------------------------+
```

### Benefits of this Architecture
1. **Bulletproof Reliability in Packet Tracer**: Because the core engine uses only core language primitives (`int`, `str`, `list`, `dict`, and bitwise operators), it cannot fail due to missing standard libraries.
2. **Automated Unit Testing on PC**: We can run rigorous test suites with hundreds of edge-case test vectors on our PC before ever pasting code into Packet Tracer.
3. **Viva Examination Defensibility**: When examiners ask how the protocol logic was verified, we can demonstrate the host PC test harness generating comparative CSV benchmarks while explaining how the adapter interfaces with simulated physical pins.

---

## 7. How to Run `probe.py` in Cisco Packet Tracer

1. Open your Packet Tracer workspace.
2. From the device palette (**Components -> Boards**), drag an **SBC-PT** (or click existing `SBC-ICU-101`).
3. Click the SBC device to open its configuration dialog.
4. Select the **Programming** tab.
5. Click **New**, set Project Type to **Empty - Python**, and name the project `Probe`.
6. Open `main.py` in the code editor, delete any default template text, and paste the entire contents of [`sbc/probe.py`](file:///c:/Users/karth/OneDrive/Desktop/CN_PROJECT/sbc/probe.py).
7. Click the green **Run** button.
8. View the diagnostic output in the **Run Console** pane.
9. Select all text in the console, copy it, and review it against the Master Feature Matrix.
