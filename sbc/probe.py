#!/usr/bin/env python3
"""
================================================================================
Packet Tracer 8.x SBC-PT Python Environment Discovery & Diagnostic Probe
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Target: Cisco Packet Tracer 8.x SBC-PT / MCU-PT & Desktop Python Compatibility
Purpose: Probes runtime introspection, standard libraries, Packet Tracer-specific
         APIs (gpio, IoEClient), data types, bitwise operators, and network sockets.
Instructions:
  1. Open Packet Tracer -> Click SBC-PT -> 'Programming' tab -> 'New' (Python).
  2. Paste this entire script into main.py and click 'Run'.
  3. Copy the output between the BEGIN and END delimiters and paste it into chat.
================================================================================
"""

import sys

def probe_environment():
    output_lines = []
    
    def log(msg=""):
        output_lines.append(msg)
        print(msg)

    log("=" * 76)
    log("===== BEGIN PACKET TRACER SBC-PT ENVIRONMENT PROBE REPORT =====")
    log("=" * 76)
    log("Project: Disaster-Resilient Smart Hospital Network (VIT Vellore)")
    log("Target : Cisco Packet Tracer 8.x Single Board Computer (SBC-PT)")
    log("=" * 76)

    # --------------------------------------------------------------------------
    # 1. RUNTIME & SYSTEM INTROSPECTION
    # --------------------------------------------------------------------------
    log("\n[1] SYSTEM & RUNTIME INTROSPECTION")
    log("-" * 76)
    try:
        log("  Python Version String : " + str(sys.version).replace("\n", " "))
    except Exception as e:
        log("  Python Version String : [FAILED] " + str(e))

    try:
        ver_info = getattr(sys, "version_info", None)
        log("  Version Tuple         : " + str(tuple(ver_info) if ver_info else "N/A"))
    except Exception as e:
        log("  Version Tuple         : [FAILED] " + str(e))

    try:
        log("  Target Platform       : " + str(getattr(sys, "platform", "unknown")))
    except Exception as e:
        log("  Target Platform       : [FAILED] " + str(e))

    try:
        log("  Byte Order            : " + str(getattr(sys, "byteorder", "unknown")))
    except Exception as e:
        log("  Byte Order            : [FAILED] " + str(e))

    try:
        log("  Max Integer / Pointer : " + str(getattr(sys, "maxsize", "unknown")))
    except Exception as e:
        log("  Max Integer / Pointer : [FAILED] " + str(e))

    # --------------------------------------------------------------------------
    # 2. STANDARD LIBRARY IMPORT PROBE
    # --------------------------------------------------------------------------
    log("\n[2] STANDARD PYTHON LIBRARY MODULE AVAILABILITY")
    log("-" * 76)
    std_modules = [
        ("sys", "System-specific parameters and functions"),
        ("time", "Time access, sleeping, and timestamps"),
        ("math", "Mathematical functions and constants"),
        ("random", "Pseudo-random number generation"),
        ("json", "JSON encoding and decoding"),
        ("os", "Operating system interface"),
        ("io", "Core tools for working with streams"),
        ("re", "Regular expression operations"),
        ("struct", "Binary data packing/unpacking (pack/unpack)"),
        ("binascii", "Binary and ASCII conversions (hexlify/b2a)"),
        ("zlib", "Compression and CRC32 calculation"),
        ("threading", "Thread-based parallelism"),
        ("socket", "Low-level networking interface (BSD sockets)"),
        ("select", "Waiting for I/O completion"),
        ("hashlib", "Secure hashes and message digests (MD5, SHA)"),
        ("collections", "High-performance container datatypes"),
        ("itertools", "Functions creating iterators for efficient looping"),
        ("copy", "Shallow and deep copy operations"),
    ]

    available_std = []
    missing_std = []

    for mod_name, desc in std_modules:
        try:
            mod = __import__(mod_name)
            available_std.append(mod_name)
            log("  [OK]     %-14s : Available (%s)" % (mod_name, desc))
        except ImportError as ie:
            missing_std.append(mod_name)
            log("  [MISS]   %-14s : Missing (%s) - %s" % (mod_name, desc, str(ie)))
        except Exception as e:
            missing_std.append(mod_name)
            log("  [ERROR]  %-14s : Failed (%s) - %s" % (mod_name, desc, str(e)))

    # --------------------------------------------------------------------------
    # 3. PACKET TRACER BUILT-IN HARDWARE & IOT MODULES
    # --------------------------------------------------------------------------
    log("\n[3] PACKET TRACER EMBEDDED HARDWARE & IOT MODULES")
    log("-" * 76)
    pt_modules = [
        ("gpio", "Hardware digital/analog pin control (SBC/MCU)"),
        ("realtime", "Packet Tracer simulation clock synchronization"),
        ("IoEClient", "Packet Tracer IoT Registration Server interface"),
        ("networking", "Packet Tracer physical network interface bindings"),
        ("physical", "Packet Tracer environmental physical hooks"),
        ("devices", "Packet Tracer hardware device object tree"),
    ]

    available_pt = []
    missing_pt = []

    for mod_name, desc in pt_modules:
        try:
            mod = __import__(mod_name)
            available_pt.append(mod_name)
            log("  [OK]     %-14s : Available (%s)" % (mod_name, desc))
        except ImportError:
            missing_pt.append(mod_name)
            log("  [N/A]    %-14s : Not Found (Standard on PC / restricted build)" % mod_name)
        except Exception as e:
            missing_pt.append(mod_name)
            log("  [ERROR]  %-14s : Failed - %s" % (mod_name, str(e)))

    # --------------------------------------------------------------------------
    # 4. FUNCTIONAL CAPABILITY CHECKS
    # --------------------------------------------------------------------------
    log("\n[4] FUNCTIONAL PRIMITIVES & OPERATIONAL CHECKS")
    log("-" * 76)

    # 4.1 Bitwise Operations (Essential for 2D Parity and 16-Bit Checksum)
    try:
        a = 0xAA55
        b = 0x55AA
        and_res = a & b
        or_res = a | b
        xor_res = a ^ b
        not_res = (~a) & 0xFFFF
        shl_res = (a << 4) & 0xFFFF
        shr_res = a >> 4
        assert and_res == 0x0000
        assert or_res == 0xFFFF
        assert xor_res == 0xFFFF
        assert not_res == 0x55AA
        log("  [OK] Bitwise Primitives       : AND, OR, XOR, NOT, SHL, SHR verified")
    except Exception as e:
        log("  [FAIL] Bitwise Primitives     : " + str(e))

    # 4.2 Large Integer Arithmetic (Arbitrary Precision Check)
    try:
        big_val = (1 << 64) + 12345
        assert big_val > 18446744073709551615
        log("  [OK] Large Integer Precision  : 64-bit+ arbitrary precision integers supported")
    except Exception as e:
        log("  [FAIL] Large Integer Precision: " + str(e))

    # 4.3 String Formatting Techniques
    try:
        # %-formatting
        pct_fmt = "Val: 0x%04X" % 0x5263
        # str.format()
        str_fmt = "Val: 0x{:04X}".format(0x5263)
        assert pct_fmt == str_fmt == "Val: 0x5263"
        log("  [OK] String Formatting (Classic): %-formatting and str.format() supported")
    except Exception as e:
        log("  [FAIL] String Formatting      : " + str(e))

    fstring_supported = False
    try:
        # Evaluate f-string dynamically to avoid syntax error in pre-3.6 parsers
        test_val = 0x5263
        fs_res = eval('f"Val: 0x{test_val:04X}"')
        if fs_res == "Val: 0x5263":
            fstring_supported = True
            log("  [OK] String Formatting (f-str): Python 3.6+ f-strings supported")
    except Exception:
        log("  [INFO] String Formatting (f-str): f-strings not supported (use % or .format)")

    # 4.4 Time and Scheduling Yields
    try:
        import time
        t0 = time.time()
        time.sleep(0.02)
        elapsed = time.time() - t0
        log("  [OK] time.sleep() Yield       : Verified (slept ~%0.3fs)" % elapsed)
    except Exception as e:
        log("  [INFO] time.sleep() Yield     : Standard time.sleep error - " + str(e))

    # Check if global delay() or uptime() exist (Packet Tracer builtins)
    pt_uptime_fn = globals().get("uptime") or getattr(sys.modules.get("time", None), "uptime", None)
    if pt_uptime_fn:
        try:
            up_val = pt_uptime_fn()
            log("  [OK] Packet Tracer uptime()   : Available (uptime = %s sec)" % str(up_val))
        except Exception as e:
            log("  [INFO] Packet Tracer uptime() : Present but call failed: " + str(e))
    else:
        log("  [INFO] Packet Tracer uptime() : Not globally bound (normal outside PT)")

    # 4.5 GPIO Module Capabilities (if available)
    if "gpio" in available_pt:
        try:
            gpio_mod = sys.modules["gpio"]
            symbols = [s for s in ["pinMode", "digitalRead", "digitalWrite", "analogRead", "analogWrite", "IN", "OUT", "HIGH", "LOW"] if hasattr(gpio_mod, s)]
            log("  [OK] gpio API Symbols Found   : " + ", ".join(symbols))
            # Test pinMode on pin 0
            if hasattr(gpio_mod, "pinMode") and hasattr(gpio_mod, "IN"):
                gpio_mod.pinMode(0, gpio_mod.IN)
                log("  [OK] gpio.pinMode(0, IN)      : Successfully configured pin 0")
            if hasattr(gpio_mod, "digitalRead"):
                val = gpio_mod.digitalRead(0)
                log("  [OK] gpio.digitalRead(0)      : Value = %s" % str(val))
        except Exception as e:
            log("  [FAIL] gpio Execution Check   : " + str(e))
    else:
        log("  [INFO] gpio Execution Check   : Module 'gpio' not present on this host")

    # 4.6 Virtual File I/O Check
    try:
        fname = "_probe_pt_test.tmp"
        with open(fname, "w") as f:
            f.write("PT-SBC-TEST-OK\n")
        with open(fname, "r") as f:
            content = f.read().strip()
        assert content == "PT-SBC-TEST-OK"
        # Cleanup
        try:
            import os
            os.remove(fname)
        except Exception:
            pass
        log("  [OK] File I/O (open/read/write): Functional (local or virtual filesystem)")
    except Exception as e:
        log("  [FAIL] File I/O               : " + str(e))

    # 4.7 BSD Socket Capabilities (if socket module is present)
    if "socket" in available_std:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(0.1)
            sock.close()
            log("  [OK] UDP Socket Creation      : socket.socket(AF_INET, SOCK_DGRAM) succeeded")
        except Exception as e:
            log("  [FAIL] UDP Socket Creation    : " + str(e))
    else:
        log("  [INFO] UDP Socket Creation    : 'socket' module unavailable in this environment")

    # --------------------------------------------------------------------------
    # 5. DIAGNOSTIC SUMMARY & RECOMMENDATIONS
    # --------------------------------------------------------------------------
    log("\n[5] ENVIRONMENT SUMMARY & ARCHITECTURAL VERDICT")
    log("-" * 76)
    log("  Standard Modules Present : %d / %d" % (len(available_std), len(std_modules)))
    log("  PT Hardware Modules      : %d / %d" % (len(available_pt), len(pt_modules)))
    
    if "struct" not in available_std:
        log("  [CRITICAL] 'struct' module is ABSENT.")
        log("             -> Pure-Python bit-shifting mandatory for packet serialization.")
    else:
        log("  [NOTE] 'struct' is present, but pure-Python bit-shifts remain safer for PT.")

    if "socket" not in available_std:
        log("  [CRITICAL] 'socket' module is ABSENT.")
        log("             -> Direct UDP sockets cannot be used; simulate via terminal logs / IoE.")
    else:
        log("  [NOTE] 'socket' is present; direct UDP client transmission is possible if permitted.")

    log("\n" + "=" * 76)
    log("===== END PACKET TRACER SBC-PT ENVIRONMENT PROBE REPORT =====")
    log("=" * 76)
    log("Instructions for Chat:")
    log("1. Select all text from '===== BEGIN ... =====' to '===== END ... ====='.")
    log("2. Copy (Ctrl+C) and paste (Ctrl+V) into your chat window.")
    log("=" * 76 + "\n")

    return {
        "available_std": available_std,
        "missing_std": missing_std,
        "available_pt": available_pt,
        "missing_pt": missing_pt,
        "bitwise_ok": and_res == 0 and or_res == 0xFFFF,
        "fstrings": fstring_supported,
        "raw_report": "\n".join(output_lines)
    }

if __name__ == "__main__":
    probe_environment()
