#!/usr/bin/env python3
"""
================================================================================
16-Bit Internet Checksum (RFC 1071) Protocol Simulation
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
Target Platform: Cisco Packet Tracer SBC-PT (Python 3) / Standalone Terminal
================================================================================
"""

import sys

def compute_checksum_16bit(words):
    """
    Computes standard 16-bit 1's complement Internet Checksum (RFC 1071).
    Algorithm:
    1. Sum all 16-bit words.
    2. Add any end-around carry bits back into the lower 16 bits.
    3. Take the 1's complement (bitwise NOT) of the final sum.
    """
    total = sum(words)
    # Fold 32-bit sum into 16 bits (add carries)
    while (total >> 16) > 0:
        carry = total >> 16
        total = (total & 0xFFFF) + carry
    # One's complement
    checksum = ~total & 0xFFFF
    return checksum

def verify_checksum_16bit(words, received_checksum):
    """
    Receiver verification:
    Sum all data words PLUS the received checksum.
    If transmission is error-free, the sum folded must equal 0xFFFF (or 0 after NOT).
    """
    all_words = words + [received_checksum]
    total = sum(all_words)
    while (total >> 16) > 0:
        carry = total >> 16
        total = (total & 0xFFFF) + carry
    # If valid, total == 0xFFFF
    is_valid = (total == 0xFFFF)
    return is_valid, total

def format_hex_bin(word):
    return f"0x{word:04X} ({word:016b})"

def run_simulation():
    print("=" * 75)
    print("  ICU PATIENT MONITOR - 16-BIT INTERNET CHECKSUM (RFC 1071) SIMULATION")
    print("=" * 75)

    # Simulated Clinical Telemetry Packet formatted as 16-bit words:
    # Word 0: Device ID (0x4943 = 'IC')
    # Word 1: Patient ID (0x5531 = 'U1') -> Patient "ICU1"
    # Word 2: Heart Rate (82 bpm) + SpO2 (99%) -> (82 << 8) | 99 = 0x5263
    # Word 3: Systolic BP (125 mmHg) + Diastolic BP (80 mmHg) -> 0x7D50
    # Word 4: Body Temp (37.2 C -> 372) = 0x0174
    # Word 5: ECG Lead-II Amplitude sample = 0x03E8
    telemetry_words = [
        0x4943,  # Device ID 'IC'
        0x5531,  # Patient ID 'U1'
        0x5263,  # HR: 82 bpm, SpO2: 99%
        0x7D50,  # BP: 125/80 mmHg
        0x0174,  # Temp: 37.2 C
        0x03E8   # ECG mV sample
    ]
    
    labels = [
        "Device Identifier ('IC')",
        "Patient Bed Tag ('U1')",
        "HR (82 bpm) & SpO2 (99%)",
        "NIBP Blood Pressure (125/80)",
        "Temperature (37.2 C)",
        "ECG Lead-II Waveform"
    ]

    print("\n[STEP 1] Assembling ICU Telemetry Packet (Sender Side):")
    for i, w in enumerate(telemetry_words):
        print(f"  Word {i}: {format_hex_bin(w)}  -->  {labels[i]}")

    # Compute Checksum
    chk = compute_checksum_16bit(telemetry_words)
    payload_bits = len(telemetry_words) * 16
    total_bits = payload_bits + 16
    overhead_pct = (16 / total_bits) * 100

    print(f"\n[STEP 2] Computed 16-Bit 1's Complement Checksum:")
    print(f"  Checksum: {format_hex_bin(chk)}")
    print(f"  Transmission Frame: 6 data words (96 bits) + 1 checksum word (16 bits) = 112 bits")
    print(f"  Protocol Overhead: {overhead_pct:.2f}% (Significantly lower than 2D parity!)")

    # Scenario 1: Clean Transmission
    print("\n" + "=" * 75)
    print("  SCENARIO 1: Clean Wireless Transmission across Hospital WLAN (VLAN 10)")
    print("=" * 75)
    valid, res_sum = verify_checksum_16bit(telemetry_words, chk)
    print(f"  Receiver accumulated sum: 0x{res_sum:04X} ({res_sum:016b})")
    if valid:
        print("  [STATUS: PASS] Sum equals 0xFFFF. Telemetry packet authenticated and accepted.")
        print("  [DISPATCH] Forwarding telemetry to EHR Server (records.hospital.local: 172.16.4.2)")

    # Scenario 2: Bit Corruption in Transit
    print("\n" + "=" * 75)
    print("  SCENARIO 2: RF Interference Corrupts Patient Vitals in Transit")
    print("=" * 75)
    corrupted_words = list(telemetry_words)
    # Corrupt Heart Rate Word: 0x5263 -> 0x5273 (bit flip in pulse rate)
    corrupted_words[2] = 0x5273
    print(f"  Sender Word 2:    0x{telemetry_words[2]:04X} (HR: 82 bpm)")
    print(f"  Received Word 2:  0x{corrupted_words[2]:04X} (Corrupted bit flipped pulse to 115 bpm!)")

    valid2, res_sum2 = verify_checksum_16bit(corrupted_words, chk)
    print(f"  Receiver accumulated sum: 0x{res_sum2:04X} ({res_sum2:016b})")
    if not valid2:
        print("  [STATUS: CORRUPT] Sum != 0xFFFF! Checksum mismatch detected.")
        print("  [PROTECTION] Malformed clinical data rejected by SBC! Prevented false patient alarm.")
        print("  [ACTION] Issuing retransmission request (ARQ)...")

if __name__ == "__main__":
    run_simulation()
