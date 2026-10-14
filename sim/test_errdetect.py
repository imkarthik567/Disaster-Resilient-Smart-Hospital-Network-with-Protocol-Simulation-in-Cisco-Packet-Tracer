#!/usr/bin/env python3
"""
Unit Test Suite: Error Detection & Correction Library
Validates /sbc/errdetect.py against project specifications, RFC 1071,
and IEEE CRC standards. Pytest-compatible.
"""

import os
import sys
try:
    import pytest
except ImportError:
    pytest = None

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sbc.errdetect import (
    calc_parity, verify_parity, add_parity_bit_to_byte, verify_parity_byte,
    encode_2d_parity, decode_2d_parity, explain_2d_parity,
    STATUS_OK, STATUS_CORRECTED, STATUS_ROW_PARITY_ERROR, STATUS_COL_PARITY_ERROR,
    STATUS_CORNER_PARITY_ERROR, STATUS_UNCORRECTABLE, STATUS_UNDETECTED,
    checksum16, verify_checksum16,
    crc16, verify_crc16, crc32, verify_crc32, crc_bitwise,
    SensorFrame, SENSOR_ECG, SENSOR_SPO2, SENSOR_TEMP,
    CHECK_NONE, CHECK_PARITY, CHECK_2D_PARITY, CHECK_CHECKSUM, CHECK_CRC16, CHECK_CRC32,
    ErrorInjector
)

# ==============================================================================
# 1. TESTS: SINGLE-BIT PARITY (EVEN AND ODD)
# ==============================================================================

def test_single_bit_parity_basic():
    """Verify single-bit even and odd parity calculation on integers and bytes."""
    # Byte 0x41 ('A' = 01000001): 2 ones -> Even parity is 0, Odd parity is 1
    assert calc_parity(0x41, mode="even") == 0
    assert calc_parity(0x41, mode="odd") == 1
    assert verify_parity(0x41, 0, mode="even") is True
    assert verify_parity(0x41, 1, mode="odd") is True

    # Byte 0x43 ('C' = 01000011): 3 ones -> Even parity is 1, Odd parity is 0
    assert calc_parity(0x43, mode="even") == 1
    assert calc_parity(0x43, mode="odd") == 0

    # Multi-byte buffer
    data = b"ICU-101"
    # Verify even parity calculation
    p_even = calc_parity(data, mode="even")
    p_odd = calc_parity(data, mode="odd")
    assert p_even + p_odd == 1

def test_single_bit_byte_parity_packing():
    """Verify 7-bit ASCII + parity bit in MSB."""
    # Character 'A' = 0x41 (01000001, 2 ones)
    # Even parity MSB should be 0 -> byte is 0x41
    b_even = add_parity_bit_to_byte(0x41, mode="even")
    assert b_even == 0x41
    assert verify_parity_byte(b_even, mode="even") is True

    # Odd parity MSB should be 1 -> byte is 0xC1
    b_odd = add_parity_bit_to_byte(0x41, mode="odd")
    assert b_odd == (0x80 | 0x41)
    assert verify_parity_byte(b_odd, mode="odd") is True

    # Corrupting one bit should fail verification
    assert verify_parity_byte(b_even ^ 0x01, mode="even") is False
    assert verify_parity_byte(b_odd ^ 0x02, mode="odd") is False

# ==============================================================================
# 2. TESTS: TWO-DIMENSIONAL (2D) PARITY ENGINE
# ==============================================================================

def test_2d_parity_clean_transmission():
    """Verify clean 2D parity encoding and zero-violation decoding."""
    payload = b"PATIENT_VITALS_NORMAL"
    matrix, rp, cp, corner = encode_2d_parity(payload, mode="even")

    assert len(matrix) == len(payload)
    assert len(rp) == len(payload)
    assert len(cp) == 8

    res = decode_2d_parity(matrix, rp, cp, corner, mode="even")
    assert res.status == STATUS_OK
    assert len(res.bad_rows) == 0
    assert len(res.bad_cols) == 0
    assert res.corner_bad is False
    assert res.corrected_data == payload
    assert "Clean transmission" in res.explanation

def test_2d_parity_single_bit_data_correction():
    """Verify 2D parity detects, pinpoints, and self-heals every single-bit data error."""
    payload = b"SPO2=99_HR=78"
    matrix, rp, cp, corner = encode_2d_parity(payload, mode="even")

    # Inject single bit error at Row 3 (byte 3), Column 5 (bit 2)
    corrupted_matrix = [list(r) for r in matrix]
    corrupted_matrix[3][5] ^= 1

    res = decode_2d_parity(corrupted_matrix, rp, cp, corner, mode="even")
    assert res.status == STATUS_CORRECTED
    assert res.bad_rows == [3]
    assert res.bad_cols == [5]
    assert res.corrected_loc == (3, 5)
    assert res.corrected_data == payload  # Exact recovery!

    # Verify textual diagnostic explanation
    expl = explain_2d_parity(res)
    assert "Row 3" in expl
    assert "Column 5" in expl
    assert "self-healed" in expl

def test_2d_parity_single_bit_parity_channel_errors():
    """Verify 2D parity handles corruption of row, column, or corner parity bits."""
    payload = b"CRITICAL_ALERT"
    matrix, rp, cp, corner = encode_2d_parity(payload, mode="even")

    # 1. Corrupt one row parity bit
    bad_rp = list(rp)
    bad_rp[2] ^= 1
    res1 = decode_2d_parity(matrix, bad_rp, cp, corner, mode="even")
    assert res1.status == STATUS_ROW_PARITY_ERROR
    assert res1.bad_rows == [2]
    assert len(res1.bad_cols) == 0
    assert res1.corrected_data == payload

    # 2. Corrupt one column parity bit
    bad_cp = list(cp)
    bad_cp[6] ^= 1
    res2 = decode_2d_parity(matrix, rp, bad_cp, corner, mode="even")
    assert res2.status == STATUS_COL_PARITY_ERROR
    assert len(res2.bad_rows) == 0
    assert res2.bad_cols == [6]
    assert res2.corrected_data == payload

    # 3. Corrupt only the corner parity bit
    bad_corner = corner ^ 1
    res3 = decode_2d_parity(matrix, rp, cp, bad_corner, mode="even")
    assert res3.status == STATUS_CORNER_PARITY_ERROR
    assert len(res3.bad_rows) == 0
    assert len(res3.bad_cols) == 0
    assert res3.corner_bad is True
    assert res3.corrected_data == payload

def test_2d_parity_multi_bit_detection_uncorrectable():
    """Verify 2D parity detects 2-bit and 3-bit errors as uncorrectable and requests ARQ."""
    payload = b"ECG_SAMPLE_STREAM"
    matrix, rp, cp, corner = encode_2d_parity(payload, mode="even")

    # Inject 2-bit error in different rows and different cols: (1, 2) and (4, 6)
    m2 = [list(r) for r in matrix]
    m2[1][2] ^= 1
    m2[4][6] ^= 1
    res2 = decode_2d_parity(m2, rp, cp, corner, mode="even")
    assert res2.status == STATUS_UNCORRECTABLE
    assert set(res2.bad_rows) == {1, 4}
    assert set(res2.bad_cols) == {2, 6}
    assert "ARQ retransmission" in res2.explanation

    # Inject 2-bit error in the same row: (2, 1) and (2, 5)
    m_same_row = [list(r) for r in matrix]
    m_same_row[2][1] ^= 1
    m_same_row[2][5] ^= 1
    res_sr = decode_2d_parity(m_same_row, rp, cp, corner, mode="even")
    assert res_sr.status == STATUS_UNCORRECTABLE
    assert len(res_sr.bad_rows) == 0  # Even number of flips in row cancels row violation!
    assert set(res_sr.bad_cols) == {1, 5}  # But column parity catches both!

def test_2d_parity_rectangular_4bit_vulnerability():
    """Verify the classic 4-bit rectangular pattern completely defeats 2D parity."""
    payload = b"VENTILATOR_ALARM"
    matrix, rp, cp, corner = encode_2d_parity(payload, mode="even")

    # Invert 4 bits forming the corners of rectangle: rows (2, 5), cols (1, 6)
    m4 = [list(r) for r in matrix]
    m4[2][1] ^= 1
    m4[2][6] ^= 1
    m4[5][1] ^= 1
    m4[5][6] ^= 1

    res = decode_2d_parity(m4, rp, cp, corner, mode="even")
    # Both violating rows had 2 flips -> row parities match!
    # Both violating cols had 2 flips -> col parities match!
    # Corner parity had 4 flips -> corner matches!
    assert len(res.bad_rows) == 0
    assert len(res.bad_cols) == 0
    assert res.corner_bad is False
    assert res.status == STATUS_OK  # Undetected! Proves the theoretical limitation!
    assert res.corrected_data != payload

# ==============================================================================
# 3. TESTS: 16-BIT INTERNET CHECKSUM (RFC 1071)
# ==============================================================================

def test_checksum16_rfc1071_known_vector():
    """Verify RFC 1071 checksum calculation, carry folding, and verification."""
    # Test vector: words 0x0001, 0x0002 -> sum 0x0003 -> checksum 0xFFFC
    data = bytes([0x00, 0x01, 0x00, 0x02])
    cs = checksum16(data)
    assert cs == 0xFFFC
    assert verify_checksum16(data, cs) is True

    # Test odd length padding (3 bytes)
    data_odd = bytes([0x00, 0x01, 0x02])
    cs_odd = checksum16(data_odd)
    assert verify_checksum16(data_odd, cs_odd) is True

    # Corrupt single bit
    corrupted = bytearray(data)
    corrupted[1] ^= 0x01
    assert verify_checksum16(corrupted, cs) is False

# ==============================================================================
# 4. TESTS: BIT-WISE CRC-16 AND CRC-32 WITH PARAMETERIZED POLYNOMIALS
# ==============================================================================

def test_crc16_standard_vectors():
    """Verify CRC-16 on standard '123456789' vector."""
    test_str = b"123456789"
    # CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF, xor_out 0x0000)
    c16 = crc16(test_str, poly=0x1021, init=0xFFFF, xor_out=0x0000)
    assert c16 == 0x29B1
    assert verify_crc16(test_str, 0x29B1, poly=0x1021, init=0xFFFF) is True

    # Different polynomial (CRC-16-IBM / ANSI: 0x8005)
    c16_ibm = crc16(test_str, poly=0x8005, init=0x0000, xor_out=0x0000)
    assert c16_ibm != c16
    assert verify_crc16(test_str, c16_ibm, poly=0x8005, init=0x0000) is True

def test_crc32_ieee8023_standard_vector():
    """Verify CRC-32 on standard '123456789' IEEE 802.3 vector."""
    test_str = b"123456789"
    c32 = crc32(test_str, poly=0x04C11DB7, init=0xFFFFFFFF, xor_out=0xFFFFFFFF, reflect=True)
    assert c32 == 0xCBF43926
    assert verify_crc32(test_str, 0xCBF43926) is True

    # Corrupt single bit
    corrupted = bytearray(test_str)
    corrupted[0] ^= 0x01
    assert verify_crc32(corrupted, 0xCBF43926) is False

def test_crc16_burst_detection_mathematical_property():
    """Verify that CRC-16 detects 100% of burst errors up to length 16 bits."""
    data = b"PATIENT_VITALS_BUFFER_LONG"
    orig_crc = crc16(data, poly=0x1021)

    # Test all burst lengths from 1 to 16 bits at various bit offsets
    for burst_len in range(1, 17):
        for start_bit in range(0, min(100, len(data) * 8 - burst_len)):
            corrupted = ErrorInjector.inject_burst_error(data, k=burst_len, start_bit=start_bit, corrupt_intermediate=True)
            assert corrupted != data
            # CRC-16 is mathematically guaranteed to detect every burst of length <= 16
            assert not verify_crc16(corrupted, orig_crc, poly=0x1021)

# ==============================================================================
# 5. TESTS: SENSOR TELEMETRY FRAME ENCODE & DECODE
# ==============================================================================

def test_sensor_frame_roundtrip_all_check_types():
    """Verify SensorFrame roundtrip encoding and decoding across all check schemes."""
    check_schemes = [CHECK_NONE, CHECK_PARITY, CHECK_2D_PARITY, CHECK_CHECKSUM, CHECK_CRC16, CHECK_CRC32]

    for scheme in check_schemes:
        frame = SensorFrame(
            seq_num=101,
            patient_id="ICU-101",
            sensor_type=SENSOR_ECG,
            value=74.25,
            timestamp=1730000000,
            payload=b"ECG_WAVEFORM_SAMPLE_BLOCK",
            check_type=scheme
        )

        wire = frame.encode()
        assert len(wire) >= 24

        ok, decoded, msg = SensorFrame.decode(wire)
        assert ok is True, "Failed to decode frame with check_type %d: %s" % (scheme, msg)
        assert decoded == frame
        assert decoded.seq_num == 101
        assert decoded.patient_id == "ICU-101"
        assert abs(decoded.value - 74.25) < 0.001

def test_sensor_frame_self_healing_with_2d_parity():
    """Verify that a SensorFrame protected by 2D parity automatically self-heals a single-bit error."""
    frame = SensorFrame(
        seq_num=502,
        patient_id="ICU-102",
        sensor_type=SENSOR_SPO2,
        value=98.5,
        timestamp=1730000050,
        payload=b"SPO2_VALID",
        check_type=CHECK_2D_PARITY
    )

    wire = frame.encode()

    # Corrupt a single bit in the protected payload area (e.g. byte 26)
    corrupted_wire = ErrorInjector.flip_bit(wire, bit_index=26 * 8 + 3)
    assert corrupted_wire != wire

    # Decode corrupted frame
    ok, decoded, msg = SensorFrame.decode(corrupted_wire)
    assert ok is True  # Successfully decoded because it self-healed!
    assert decoded.seq_num == 502
    assert decoded.patient_id == "ICU-102"
    assert decoded.payload == b"SPO2_VALID"
    assert "self-healed" in msg

def test_sensor_frame_corruption_rejection():
    """Verify that corruptions are caught and rejected for CRC16 and Checksum."""
    frame = SensorFrame(seq_num=77, patient_id="ICU-103", sensor_type=SENSOR_TEMP, value=37.2, check_type=CHECK_CRC16)
    wire = frame.encode()

    # Corrupt 1 bit
    corrupted = ErrorInjector.flip_bit(wire, bit_index=30)
    ok, decoded, msg = SensorFrame.decode(corrupted)
    assert ok is False
    assert "CRC-16 mismatch" in msg

# ==============================================================================
# 6. TESTS: ERROR INJECTOR CAPABILITIES
# ==============================================================================

def test_error_injector_functions():
    """Verify flip_bit, flip_random_bits, burst_error, and rectangular 4-bit injection."""
    data = b"0123456789ABCDEF"
    total_bits = len(data) * 8

    # 1. Flip single bit
    f1 = ErrorInjector.flip_bit(data, 10)
    diff_bits = sum(bin(a ^ b).count("1") for a, b in zip(data, f1))
    assert diff_bits == 1

    # 2. Flip n random bits
    fn = ErrorInjector.flip_random_bits(data, n=5, seed=42)
    diff_bits_n = sum(bin(a ^ b).count("1") for a, b in zip(data, fn))
    assert diff_bits_n == 5

    # 3. Burst error of length k
    burst_k = ErrorInjector.inject_burst_error(data, k=12, start_bit=16, seed=42)
    assert burst_k != data
    # Verify first bit (16) and last bit (16 + 12 - 1 = 27) are flipped
    assert (burst_k[16 // 8] ^ data[16 // 8]) & (1 << (7 - (16 % 8))) != 0
    assert (burst_k[27 // 8] ^ data[27 // 8]) & (1 << (7 - (27 % 8))) != 0

    # 4. Rectangular 4-bit injection
    rect = ErrorInjector.inject_rectangular_4bit_error(data, row1=2, row2=6, col1=1, col2=7)
    diff_bits_rect = sum(bin(a ^ b).count("1") for a, b in zip(data, rect))
    assert diff_bits_rect == 4

if __name__ == "__main__":
    if pytest is not None:
        sys.exit(pytest.main(["-v", __file__]))
    else:
        print("=" * 70)
        print("  RUNNING ERROR DETECTION & CORRECTION UNIT TESTS (STANDALONE RUNNER)")
        print("=" * 70)
        tests = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
        passed = 0
        failed = 0
        for test_fn in tests:
            try:
                test_fn()
                print("  [PASS] %s" % test_fn.__name__)
                passed += 1
            except Exception as e:
                print("  [FAIL] %s: %s" % (test_fn.__name__, str(e)))
                failed += 1
        print("=" * 70)
        print("  SUMMARY: %d Passed, %d Failed" % (passed, failed))
        print("=" * 70)
        sys.exit(0 if failed == 0 else 1)
