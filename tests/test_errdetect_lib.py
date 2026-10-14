#!/usr/bin/env python3
"""
Unit Test Suite: Error Detection Library & Simulation Coverage Verification
Validates /sbc/errdetect.py, /sim/test_errdetect.py, and /sim/detection_coverage.py
against project specifications, mathematical error bounds, and Packet Tracer rules.
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sbc.errdetect import (
    calc_parity, verify_parity, add_parity_bit_to_byte, verify_parity_byte,
    encode_2d_parity, decode_2d_parity, explain_2d_parity,
    STATUS_OK, STATUS_CORRECTED, STATUS_ROW_PARITY_ERROR, STATUS_COL_PARITY_ERROR,
    STATUS_CORNER_PARITY_ERROR, STATUS_UNCORRECTABLE,
    checksum16, verify_checksum16,
    crc16, verify_crc16, crc32, verify_crc32,
    SensorFrame, SENSOR_ECG, SENSOR_SPO2,
    CHECK_NONE, CHECK_PARITY, CHECK_2D_PARITY, CHECK_CHECKSUM, CHECK_CRC16, CHECK_CRC32,
    ErrorInjector
)

ERRDETECT_PY = os.path.join(PROJECT_ROOT, "sbc", "errdetect.py")
COVERAGE_MD = os.path.join(PROJECT_ROOT, "results", "detection_coverage.md")
COVERAGE_CSV = os.path.join(PROJECT_ROOT, "results", "detection_coverage.csv")

def test_errdetect_pure_python_dependencies():
    """Verify sbc/errdetect.py uses strictly pure Python with zero third-party or native C imports."""
    assert os.path.isfile(ERRDETECT_PY), f"Missing errdetect.py at {ERRDETECT_PY}"
    with open(ERRDETECT_PY, "r", encoding="utf-8") as f:
        code = f.read()

    banned = ["struct", "binascii", "zlib", "threading", "numpy", "pandas", "scipy", "dataclasses"]
    for b in banned:
        assert f"import {b}" not in code, f"errdetect.py illegally imports '{b}'"
        assert f"from {b}" not in code, f"errdetect.py illegally imports from '{b}'"

    print("  [PASS] test_errdetect_pure_python_dependencies (Zero non-builtin dependencies)")

def test_single_bit_parity_operations():
    """Verify single-bit even and odd parity operations."""
    assert calc_parity(0x41, mode="even") == 0
    assert calc_parity(0x41, mode="odd") == 1
    assert calc_parity(0x43, mode="even") == 1
    assert calc_parity(0x43, mode="odd") == 0

    byte_packed = add_parity_bit_to_byte(0x41, mode="even")
    assert verify_parity_byte(byte_packed, mode="even") is True
    assert verify_parity_byte(byte_packed ^ 0x01, mode="even") is False

    print("  [PASS] test_single_bit_parity_operations (Even/odd parity verified)")

def test_2d_parity_matrix_and_correction():
    """Verify 2D parity matrix encoding, single-bit correction, and text explanation."""
    payload = b"PATIENT_TELEMETRY_SAMPLE"
    matrix, rp, cp, corner = encode_2d_parity(payload, mode="even")

    # Clean verification
    res_clean = decode_2d_parity(matrix, rp, cp, corner, mode="even")
    assert res_clean.status == STATUS_OK
    assert res_clean.corrected_data == payload

    # Single-bit error correction
    m_err = [list(r) for r in matrix]
    m_err[2][4] ^= 1  # Row 2, Col 4
    res_corr = decode_2d_parity(m_err, rp, cp, corner, mode="even")
    assert res_corr.status == STATUS_CORRECTED
    assert res_corr.corrected_loc == (2, 4)
    assert res_corr.corrected_data == payload
    expl = explain_2d_parity(res_corr)
    assert "Row 2" in expl and "Column 4" in expl and "self-healed" in expl

    # Parity channel corruption
    bad_rp = list(rp)
    bad_rp[0] ^= 1
    res_rp = decode_2d_parity(matrix, bad_rp, cp, corner, mode="even")
    assert res_rp.status == STATUS_ROW_PARITY_ERROR
    assert res_rp.corrected_data == payload

    print("  [PASS] test_2d_parity_matrix_and_correction (Encoding, 1-bit self-healing & explanation verified)")

def test_2d_parity_error_bounds_and_blindspots():
    """Verify 2D parity multi-bit detection and 4-bit rectangular pattern blindspot."""
    payload = b"VENTILATOR_CRITICAL_DATA"
    matrix, rp, cp, corner = encode_2d_parity(payload, mode="even")

    # 2-bit error -> UNCORRECTABLE (triggers ARQ)
    m2 = [list(r) for r in matrix]
    m2[1][1] ^= 1
    m2[3][5] ^= 1
    res2 = decode_2d_parity(m2, rp, cp, corner, mode="even")
    assert res2.status == STATUS_UNCORRECTABLE
    assert "ARQ retransmission" in res2.explanation

    # 4-bit rectangular pattern -> completely defeats 2D parity
    m4 = [list(r) for r in matrix]
    r1, r2, c1, c2 = 1, 4, 2, 6
    m4[r1][c1] ^= 1
    m4[r1][c2] ^= 1
    m4[r2][c1] ^= 1
    m4[r2][c2] ^= 1
    res4 = decode_2d_parity(m4, rp, cp, corner, mode="even")
    assert res4.status == STATUS_OK  # Undetected! Zero parity violations!
    assert res4.corrected_data != payload

    print("  [PASS] test_2d_parity_error_bounds_and_blindspots (2-bit ARQ & 4-bit rectangular blindspot verified)")

def test_rfc1071_checksum_and_crc_algorithms():
    """Verify 16-bit Internet checksum, CRC-16 and CRC-32 with configurable polynomials."""
    data = b"123456789"

    # RFC 1071
    cs = checksum16(data)
    assert verify_checksum16(data, cs) is True
    assert verify_checksum16(data + b"\x01", cs) is False

    # CRC-16 (poly 0x1021)
    c16 = crc16(data, poly=0x1021)
    assert c16 == 0x29B1
    assert verify_crc16(data, 0x29B1, poly=0x1021) is True

    # CRC-16 with alternate polynomial (0x8005)
    c16_alt = crc16(data, poly=0x8005)
    assert c16_alt != c16
    assert verify_crc16(data, c16_alt, poly=0x8005) is True

    # CRC-32 (IEEE 802.3 Ethernet standard)
    c32 = crc32(data, poly=0x04C11DB7)
    assert c32 == 0xCBF43926
    assert verify_crc32(data, 0xCBF43926) is True

    # CRC-16 Burst Error Guarantee: detects 100% bursts <= 16 bits
    data_burst = b"ICU_TELEMETRY_LONG_BUFFER"
    ref_crc = crc16(data_burst, poly=0x1021)
    for blen in range(1, 17):
        corrupted = ErrorInjector.inject_burst_error(data_burst, k=blen, start_bit=8)
        assert not verify_crc16(corrupted, ref_crc, poly=0x1021)

    print("  [PASS] test_rfc1071_checksum_and_crc_algorithms (Checksum, CRC16/32, burst property verified)")

def test_sensor_telemetry_frame_and_self_healing():
    """Verify SensorFrame structure, encoding, decoding, and self-healing in transit."""
    frame = SensorFrame(
        seq_num=777,
        patient_id="ICU-101",
        sensor_type=SENSOR_ECG,
        value=72.5,
        timestamp=1730001000,
        payload=b"ECG_LEAD2_SAMPLES",
        check_type=CHECK_2D_PARITY
    )

    wire = frame.encode()
    assert len(wire) >= 24

    # Clean decode
    ok, dec_clean, _ = SensorFrame.decode(wire)
    assert ok is True
    assert dec_clean == frame

    # Self-healing test: flip 1 bit in payload
    wire_corrupted = ErrorInjector.flip_bit(wire, bit_index=26 * 8 + 2)
    ok_heal, dec_healed, heal_msg = SensorFrame.decode(wire_corrupted)
    assert ok_heal is True
    assert dec_healed.payload == b"ECG_LEAD2_SAMPLES"
    assert "self-healed" in heal_msg

    print("  [PASS] test_sensor_telemetry_frame_and_self_healing (Frame serialization & self-healing verified)")

def test_coverage_reports_generated():
    """Verify detection coverage report files exist and document theoretical findings."""
    assert os.path.isfile(COVERAGE_MD), f"Missing coverage MD report: {COVERAGE_MD}"
    assert os.path.isfile(COVERAGE_CSV), f"Missing coverage CSV report: {COVERAGE_CSV}"

    with open(COVERAGE_MD, "r", encoding="utf-8") as f:
        md_text = f.read()

    assert "4-Bit Rectangular" in md_text
    assert "Burst (k = 16)" in md_text
    assert "The 4-Bit Rectangular Blindspot (0.0% Detection)" in md_text
    assert "CRC-16 Burst Error Detection Guarantee" in md_text

    print("  [PASS] test_coverage_reports_generated (Markdown and CSV reports validated)")

def run_all_tests():
    print("=" * 70)
    print("  RUNNING ERROR DETECTION & CORRECTION UNIT TEST SUITE")
    print("=" * 70)
    test_errdetect_pure_python_dependencies()
    test_single_bit_parity_operations()
    test_2d_parity_matrix_and_correction()
    test_2d_parity_error_bounds_and_blindspots()
    test_rfc1071_checksum_and_crc_algorithms()
    test_sensor_telemetry_frame_and_self_healing()
    test_coverage_reports_generated()
    print("=" * 70)
    print("  ALL 7 ERROR DETECTION & CORRECTION TESTS PASSED")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
