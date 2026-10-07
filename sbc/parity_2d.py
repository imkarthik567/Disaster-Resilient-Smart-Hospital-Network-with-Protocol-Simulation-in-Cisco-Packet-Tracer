#!/usr/bin/env python3
"""
================================================================================
2-Dimensional (2D) Parity Error Detection & Correction Simulation
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
Target Platform: Cisco Packet Tracer SBC-PT (Python 3) / Standalone Terminal
================================================================================
"""

import sys
import time
import random

def format_byte(val):
    return f"{val:08b}"

def calculate_row_parity(matrix):
    """Calculate even parity for each row (8 bits data + 1 parity bit)."""
    row_parity = []
    for row in matrix:
        ones = sum(int(b) for b in row)
        parity = 1 if (ones % 2 != 0) else 0  # Even parity
        row_parity.append(parity)
    return row_parity

def calculate_col_parity(matrix, row_parity):
    """Calculate even parity for each column across all data rows + row parity column."""
    num_cols = len(matrix[0])
    col_parity = []
    for col_idx in range(num_cols):
        ones = sum(int(matrix[r][col_idx]) for r in range(len(matrix)))
        parity = 1 if (ones % 2 != 0) else 0
        col_parity.append(parity)
    
    # Parity of the parity bits (intersection bit)
    p_ones = sum(row_parity)
    col_parity.append(1 if (p_ones % 2 != 0) else 0)
    return col_parity

def encode_2d_parity(data_bytes):
    """Encodes a list of data bytes into a 2D Parity Frame."""
    matrix = [[int(bit) for bit in format_byte(b)] for b in data_bytes]
    row_parity = calculate_row_parity(matrix)
    col_parity = calculate_col_parity(matrix, row_parity)
    return matrix, row_parity, col_parity

def print_2d_frame(matrix, row_parity, col_parity, labels=None, highlight=None):
    """Renders the 2D parity matrix in terminal."""
    print("      Data Bits (Col 0-7)   | Row Parity")
    print("   " + "-" * 38)
    for r in range(len(matrix)):
        row_str = " ".join(str(b) for b in matrix[r])
        lbl = f"({labels[r]})" if labels and r < len(labels) else f"Row {r}"
        mark = " <-- ERROR" if highlight and highlight[0] == r and highlight[1] != 'P' else ""
        p_mark = " <-- PARITY ERROR" if highlight and highlight[0] == r and highlight[1] == 'P' else ""
        print(f"R{r} | {row_str} |     {row_parity[r]}   {lbl}{mark}{p_mark}")
    print("   " + "=" * 38)
    col_str = " ".join(str(b) for b in col_parity[:8])
    print(f"CP | {col_str} |     {col_parity[8]}   (Column Parity Bits)")
    if highlight and highlight[1] != 'P':
        col_indicator = "   " + "  " * highlight[1] + " ^"
        print(col_indicator + f" [Error detected at Col {highlight[1]}]")

def verify_and_correct(matrix, row_parity, col_parity, labels=None):
    """Verifies 2D parity, pinpoints error location, and performs single-bit correction."""
    recomputed_row_p = calculate_row_parity(matrix)
    bad_rows = [r for r in range(len(matrix)) if recomputed_row_p[r] != row_parity[r]]

    num_cols = len(matrix[0])
    recomputed_col_p = []
    for col_idx in range(num_cols):
        ones = sum(matrix[r][col_idx] for r in range(len(matrix)))
        recomputed_col_p.append(1 if (ones % 2 != 0) else 0)
    
    bad_cols = [c for c in range(num_cols) if recomputed_col_p[c] != col_parity[c]]

    print("\n--- Receiver Parity Analysis ---")
    if not bad_rows and not bad_cols:
        print("[SUCCESS] Zero parity violations detected. Frame integrity 100% verified.")
        return True, matrix
    
    if len(bad_rows) == 1 and len(bad_cols) == 1:
        err_r, err_c = bad_rows[0], bad_cols[0]
        print(f"[DETECTED] Single-bit transmission error at Row {err_r}, Column {err_c}!")
        orig_val = matrix[err_r][err_c]
        corrected_val = 1 - orig_val
        print(f"[CORRECTING] Inverting corrupted bit ({orig_val} -> {corrected_val})...")
        matrix[err_r][err_c] = corrected_val
        print("[SUCCESS] Error successfully corrected via 2D parity geometric intersection!")
        return True, matrix
    
    if len(bad_rows) > 1 or len(bad_cols) > 1:
        print(f"[ALERT] Multi-bit burst error detected! (Violating Rows: {bad_rows}, Violating Cols: {bad_cols})")
        print("[ACTION] Multi-bit errors detected; 2D parity cannot unambiguously self-heal. Requesting ARQ Retransmission!")
        return False, matrix

    if len(bad_rows) == 1 and not bad_cols:
        print(f"[DETECTED] Row Parity bit corrupted on Row {bad_rows[0]}. Data bits intact.")
        return True, matrix

    if not bad_rows and len(bad_cols) == 1:
        print(f"[DETECTED] Column Parity bit corrupted at Col {bad_cols[0]}. Data bits intact.")
        return True, matrix

    return False, matrix

def run_simulation():
    print("=" * 70)
    print("  ICU SENSOR TELEMETRY - 2D PARITY PROTOCOL SIMULATION")
    print("=" * 70)
    
    # Simulated ICU telemetry metrics (4 sensor bytes)
    # Byte 0: Heart Rate = 78 bpm
    # Byte 1: SpO2 Oxygen Saturation = 98 %
    # Byte 2: Systolic Blood Pressure = 120 mmHg
    # Byte 3: Body Temperature (x10) = 37.0 C -> 37
    telemetry = [78, 98, 120, 37]
    labels = ["Heart Rate (78 bpm)", "SpO2 (98%)", "Sys BP (120 mmHg)", "Body Temp (37 C)"]
    
    print("\n[STEP 1] Generating Raw ICU Sensor Payload:")
    for i, val in enumerate(telemetry):
        print(f"  Metric {i}: {labels[i]:<22} Decimal: {val:<4} Binary: {format_byte(val)}")
    
    matrix, row_p, col_p = encode_2d_parity(telemetry)
    
    data_bits = len(telemetry) * 8
    parity_bits = len(row_p) + len(col_p)
    total_bits = data_bits + parity_bits
    overhead_pct = (parity_bits / total_bits) * 100
    
    print(f"\n[STEP 2] Computed 2D Parity Matrix at Sender:")
    print_2d_frame(matrix, row_p, col_p, labels)
    print(f"\n-> Data Bits: {data_bits} bits | Parity Overhead: {parity_bits} bits ({overhead_pct:.1f}% overhead)")
    
    # Case A: Transmission across channel with 1 induced bit flip
    print("\n" + "=" * 70)
    print("  SCENARIO A: Channel Noise Induces Single-Bit Error on ICU Telemetry")
    print("=" * 70)
    
    corrupt_row, corrupt_col = 2, 4  # Flip bit in Systolic BP
    matrix[corrupt_row][corrupt_col] = 1 - matrix[corrupt_row][corrupt_col]
    print(f"[CHANNEL] Flipping bit at Row {corrupt_row}, Col {corrupt_col} during wireless transmission...")
    
    print_2d_frame(matrix, row_p, col_p, labels, highlight=(corrupt_row, corrupt_col))
    success, fixed_matrix = verify_and_correct(matrix, row_p, col_p, labels)
    
    # Reconstruct recovered value
    recovered_bp = int("".join(str(b) for b in fixed_matrix[2]), 2)
    print(f"[RESULT] Recovered Systolic BP Value: {recovered_bp} mmHg (Original was 120 mmHg)")
    
    # Case B: Multi-bit burst error
    print("\n" + "=" * 70)
    print("  SCENARIO B: Severe Noise Induces Double-Bit Burst Error")
    print("=" * 70)
    # Flip two bits in Row 0
    matrix[0][1] = 1 - matrix[0][1]
    matrix[0][5] = 1 - matrix[0][5]
    print("[CHANNEL] Injected 2 bit-flips into Heart Rate telemetry packet...")
    verify_and_correct(matrix, row_p, col_p, labels)

if __name__ == "__main__":
    run_simulation()
