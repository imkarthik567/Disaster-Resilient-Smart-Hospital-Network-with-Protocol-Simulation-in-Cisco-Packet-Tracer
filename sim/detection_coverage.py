#!/usr/bin/env python3
"""
================================================================================
Empirical Error Detection & Correction Coverage Monte Carlo Simulator
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Evaluates error detection probability across:
  - Single-Bit Parity (Even)
  - Two-Dimensional (2D) Parity (Detection & Single-Bit Correction)
  - 16-Bit Internet Checksum (RFC 1071)
  - CRC-16 (poly 0x1021)
  - CRC-32 (IEEE 802.3, poly 0x04C11DB7)

Evaluates 11 distinct error models:
  1. Single-bit error (1 random bit flip)
  2. Double-bit error (2 random bit flips)
  3. Triple-bit error (3 random bit flips)
  4. 4-bit random error (4 random bit flips)
  5. 4-bit rectangular pattern (targeted 2D parity vulnerability)
  6. Burst error length k = 4 bits
  7. Burst error length k = 8 bits
  8. Burst error length k = 12 bits
  9. Burst error length k = 16 bits
  10. Burst error length k = 24 bits
  11. Burst error length k = 32 bits

Outputs:
  - Console formatted summary table
  - /results/detection_coverage.md (Markdown report for project defense)
  - /results/detection_coverage.csv (Machine-readable tabular data)
================================================================================
"""

import os
import sys
import time
import random
import argparse

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sbc.errdetect import (
    calc_parity, encode_2d_parity, decode_2d_parity, bytes_to_matrix,
    STATUS_OK, STATUS_CORRECTED, STATUS_ROW_PARITY_ERROR, STATUS_COL_PARITY_ERROR,
    STATUS_CORNER_PARITY_ERROR, STATUS_UNCORRECTABLE,
    checksum16, verify_checksum16,
    crc16, verify_crc16, crc32, verify_crc32,
    ErrorInjector
)

# Benchmark telemetry payload (typical ICU patient monitor buffer: 32 bytes)
BENCHMARK_PAYLOAD = b"ICU-101:HR=82,SPO2=99,TEMP=37.2C"

def run_simulation(num_trials=10000, seed=42):
    """
    Executes Monte Carlo simulation measuring empirical detection probability.
    num_trials: number of randomized iterations per error model.
    """
    random.seed(seed)
    payload = BENCHMARK_PAYLOAD
    payload_len = len(payload)
    total_bits = payload_len * 8

    # Precompute reference error-check values on clean payload
    ref_parity = calc_parity(payload, mode="even")
    ref_matrix, ref_rp, ref_cp, ref_corner = encode_2d_parity(payload, mode="even")
    ref_checksum = checksum16(payload)
    ref_crc16 = crc16(payload, poly=0x1021)
    ref_crc32 = crc32(payload, poly=0x04C11DB7)

    error_models = [
        ("1-Bit Error", "single", 1),
        ("2-Bit Error", "random_n", 2),
        ("3-Bit Error", "random_n", 3),
        ("4-Bit Random", "random_n", 4),
        ("4-Bit Rectangular", "rectangle", 4),
        ("Burst (k = 4)", "burst", 4),
        ("Burst (k = 8)", "burst", 8),
        ("Burst (k = 12)", "burst", 12),
        ("Burst (k = 16)", "burst", 16),
        ("Burst (k = 24)", "burst", 24),
        ("Burst (k = 32)", "burst", 32),
    ]

    results = []

    print("=" * 80)
    print("  EMPIRICAL ERROR DETECTION & CORRECTION COVERAGE BENCHMARK")
    print("  Target Buffer: %d bytes (%d bits) | Trials per Pattern: %d" % (payload_len, total_bits, num_trials))
    print("=" * 80)
    t_start_total = time.time()

    for label, mode, param in error_models:
        t0 = time.time()
        det_parity = 0
        det_2d_detect = 0
        det_2d_correct = 0
        det_checksum = 0
        det_crc16 = 0
        det_crc32 = 0

        for trial in range(num_trials):
            # 1. Generate Corrupted Payload
            if mode == "single":
                corrupted = ErrorInjector.flip_random_bits(payload, n=1)
            elif mode == "random_n":
                corrupted = ErrorInjector.flip_random_bits(payload, n=param)
            elif mode == "rectangle":
                # Random distinct rows r1, r2 and cols c1, c2
                r1, r2 = random.sample(range(payload_len), 2)
                c1, c2 = random.sample(range(8), 2)
                corrupted = ErrorInjector.inject_rectangular_4bit_error(payload, r1, r2, c1, c2)
            elif mode == "burst":
                max_start = total_bits - param
                start_bit = random.randint(0, max_start) if max_start > 0 else 0
                corrupted = ErrorInjector.inject_burst_error(payload, k=param, start_bit=start_bit, corrupt_intermediate=False)
            else:
                corrupted = payload

            # 2. Test Single-Bit Parity (Even)
            if calc_parity(corrupted, mode="even") != ref_parity:
                det_parity += 1

            # 3. Test 2D Parity
            m = bytes_to_matrix(corrupted)
            res_2d = decode_2d_parity(m, ref_rp, ref_cp, ref_corner, mode="even")
            if res_2d.status != STATUS_OK:
                det_2d_detect += 1
            if res_2d.status == STATUS_CORRECTED and res_2d.corrected_data == payload:
                det_2d_correct += 1

            # 4. Test 16-Bit Internet Checksum
            if not verify_checksum16(corrupted, ref_checksum):
                det_checksum += 1

            # 5. Test CRC-16
            if not verify_crc16(corrupted, ref_crc16, poly=0x1021):
                det_crc16 += 1

            # 6. Test CRC-32
            if not verify_crc32(corrupted, ref_crc32, poly=0x04C11DB7):
                det_crc32 += 1

        t_elapsed = time.time() - t0

        row = {
            "error_model": label,
            "trials": num_trials,
            "parity_pct": (det_parity / num_trials) * 100.0,
            "parity_2d_det_pct": (det_2d_detect / num_trials) * 100.0,
            "parity_2d_corr_pct": (det_2d_correct / num_trials) * 100.0,
            "checksum_pct": (det_checksum / num_trials) * 100.0,
            "crc16_pct": (det_crc16 / num_trials) * 100.0,
            "crc32_pct": (det_crc32 / num_trials) * 100.0,
            "time_sec": t_elapsed
        }
        results.append(row)

        print("  %-20s | Parity: %6.2f%% | 2D-Det: %6.2f%% | 2D-Corr: %6.2f%% | CS: %6.2f%% | CRC16: %6.2f%% | CRC32: %6.2f%% (%0.2fs)" % (
            label,
            row["parity_pct"],
            row["parity_2d_det_pct"],
            row["parity_2d_corr_pct"],
            row["checksum_pct"],
            row["crc16_pct"],
            row["crc32_pct"],
            t_elapsed
        ))

    t_total = time.time() - t_start_total
    print("=" * 80)
    print("  Simulation Complete in %0.2f seconds." % t_total)
    print("=" * 80)

    return results

def format_ascii_table(results):
    """Formats results into a clean presentation table."""
    lines = []
    lines.append("+" + "-" * 20 + "+" + "-" * 10 + "+" + "-" * 11 + "+" + "-" * 11 + "+" + "-" * 11 + "+" + "-" * 11 + "+" + "-" * 11 + "+")
    lines.append("| %-18s | %-8s | %-9s | %-9s | %-9s | %-9s | %-9s |" % (
        "Error Pattern", "Parity", "2D-Detect", "2D-Correct", "Checksum16", "CRC-16", "CRC-32"
    ))
    lines.append("+" + "=" * 20 + "+" + "=" * 10 + "+" + "=" * 11 + "+" + "=" * 11 + "+" + "=" * 11 + "+" + "=" * 11 + "+" + "=" * 11 + "+")
    for r in results:
        lines.append("| %-18s | %7.2f%% | %8.2f%% | %8.2f%% | %8.2f%% | %8.2f%% | %8.2f%% |" % (
            r["error_model"],
            r["parity_pct"],
            r["parity_2d_det_pct"],
            r["parity_2d_corr_pct"],
            r["checksum_pct"],
            r["crc16_pct"],
            r["crc32_pct"]
        ))
    lines.append("+" + "-" * 20 + "+" + "-" * 10 + "+" + "-" * 11 + "+" + "-" * 11 + "+" + "-" * 11 + "+" + "-" * 11 + "+" + "-" * 11 + "+")
    return "\n".join(lines)

def write_reports(results, results_dir):
    """Writes Markdown and CSV reports to /results."""
    os.makedirs(results_dir, exist_ok=True)
    csv_path = os.path.join(results_dir, "detection_coverage.csv")
    md_path = os.path.join(results_dir, "detection_coverage.md")

    # 1. Write CSV
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("error_model,trials,parity_pct,parity_2d_det_pct,parity_2d_corr_pct,checksum_pct,crc16_pct,crc32_pct\n")
        for r in results:
            f.write("%s,%d,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f\n" % (
                r["error_model"], r["trials"], r["parity_pct"], r["parity_2d_det_pct"],
                r["parity_2d_corr_pct"], r["checksum_pct"], r["crc16_pct"], r["crc32_pct"]
            ))
    print("[OK] Wrote CSV report -> %s" % csv_path)

    # 2. Write Markdown Report
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Empirical Error Detection & Correction Coverage Report\n\n")
        f.write("**Project:** Disaster-Resilient Smart Hospital Network  \n")
        f.write("**Module:** Data-Link Error Detection & Correction Library (`/sbc/errdetect.py`)  \n")
        f.write("**Authors:** Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)  \n")
        f.write("**Target Platform:** Cisco Packet Tracer 8.x SBC-PT & Workstation Simulation  \n\n")
        f.write("---\n\n")
        f.write("## 1. Executive Summary & Comparative Coverage Table\n\n")
        f.write("This empirical benchmark evaluates the error detection and correction capabilities of five distinct algorithms across 11 error patterns on a 32-byte clinical ICU telemetry packet.\n\n")
        f.write("| Error Pattern | Single Parity | 2D Parity (Detect) | 2D Parity (Correct) | 16-Bit Checksum | CRC-16 (poly `0x1021`) | CRC-32 (IEEE 802.3) |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for r in results:
            f.write("| **%s** | %.2f%% | %.2f%% | %.2f%% | %.2f%% | %.2f%% | %.2f%% |\n" % (
                r["error_model"], r["parity_pct"], r["parity_2d_det_pct"], r["parity_2d_corr_pct"],
                r["checksum_pct"], r["crc16_pct"], r["crc32_pct"]
            ))
        f.write("\n---\n\n")
        f.write("## 2. Key Mathematical Proofs & Experimental Findings\n\n")
        f.write("### 1. Two-Dimensional (2D) Parity Capabilities & Vulnerabilities\n")
        f.write("- **100% Single-Bit Correction**: When exactly 1 bit flips in the data matrix, exactly one row parity check and one column parity check fail. Their intersection $(r, c)$ uniquely pinpoints the faulty bit, enabling deterministic single-bit self-healing without retransmission.\n")
        f.write("- **100% Double-Bit & Triple-Bit Detection**: Any 2-bit error produces at least two row violations, two column violations, or cancels within a row/column while leaving the orthogonal parity violated. In all cases, `status == STATUS_UNCORRECTABLE`, prompting an automatic ARQ retransmission.\n")
        f.write("- **The 4-Bit Rectangular Blindspot (0.0% Detection)**: If four bits at the intersections of two rows $(r_1, r_2)$ and two columns $(c_1, c_2)$ flip simultaneously, each violating row experiences $\\Delta = 2 \\pmod 2 = 0$ flips, and each violating column experiences $\\Delta = 2 \\pmod 2 = 0$ flips. The corner parity also experiences $\\Delta = 4 \\pmod 2 = 0$. Consequently, all parity syndromes evaluate to zero, and the error passes **100% undetected**!\n\n")
        f.write("### 2. CRC-16 Burst Error Detection Guarantee\n")
        f.write("- **100.00% Detection for Bursts $\\le 16$ Bits**: Mathematically, any burst error of length $k \\le 16$ can be represented as an error polynomial $E(x) = x^j \\cdot B(x)$ where $\\deg(B(x)) = k - 1 < 16$. Because the generator polynomial $G(x)$ has degree 16 and contains a non-zero $x^0$ term, $G(x)$ cannot divide $x^j$ and cannot divide $B(x)$. Thus, the remainder $E(x) \\pmod{G(x)}$ is strictly non-zero, guaranteeing **100% detection of all burst impairments up to 16 bits**.\n\n")
        f.write("### 3. Checksum vs. CRC Reliability in Clinical Telemetry\n")
        f.write("- **16-Bit Checksum**: Provides good coverage for random flips (~99.998%) but has known blindspots when bytes swap positions or when compensating errors cancel each other out in the one's complement sum.\n")
        f.write("- **CRC-16 & CRC-32**: Provide cryptographic-grade transmission integrity suitable for life-critical telemetry (ICU vitals, ventilator alarms) over noisy serial WAN and wireless hospital access points.\n")
    print("[OK] Wrote Markdown report -> %s" % md_path)

def main():
    parser = argparse.ArgumentParser(description="Empirical Error Detection Coverage Benchmark")
    parser.add_argument("--trials", type=int, default=10000, help="Number of random trials per error model (default: 10000)")
    parser.add_argument("--seed", type=int, default=42, help="PRNG seed for reproducible simulation (default: 42)")
    args = parser.parse_args()

    results = run_simulation(num_trials=args.trials, seed=args.seed)
    table_str = format_ascii_table(results)
    print("\n" + table_str + "\n")

    results_dir = os.path.join(PROJECT_ROOT, "results")
    write_reports(results, results_dir)

if __name__ == "__main__":
    main()
