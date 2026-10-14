#!/usr/bin/env python3
"""
================================================================================
Pure-Python Error Detection & Correction Library
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Platform: Cisco Packet Tracer 8.x SBC-PT (Python 3) & Desktop Workstation
Features:
  1. Single-bit Even & Odd Parity (byte & multi-byte)
  2. Two-Dimensional (2D) Parity with Single-Bit Correction & Text Explanation
  3. 16-Bit Internet Checksum (RFC 1071 One's Complement)
  4. Bit-Wise CRC-16 and CRC-32 with Configurable Generator Polynomials
  5. Clinical Sensor Telemetry Frame (Encode/Decode, Pure-Python Dataclass)
  6. Channel Error Injector (Bit Flips, Bursts, Targeted 4-Bit Rectangles)
================================================================================
"""

# ==============================================================================
# 1. SINGLE-BIT PARITY (EVEN AND ODD)
# ==============================================================================

def calc_parity(data, mode="even"):
    """
    Computes single-bit parity across an integer, bytes, bytearray, or list of ints.
    mode: 'even' (default) -> returns 1 if popcount is odd, 0 if even (total 1s is even).
          'odd'            -> returns 1 if popcount is even, 0 if odd (total 1s is odd).
    """
    if isinstance(data, int):
        popcount = bin(data).count("1")
    elif isinstance(data, (bytes, bytearray)):
        popcount = sum(bin(b).count("1") for b in data)
    elif isinstance(data, (list, tuple)):
        popcount = sum(bin(int(x)).count("1") for x in data)
    else:
        raise TypeError("Unsupported data type for parity calculation: %s" % type(data))

    if mode == "even":
        return 1 if (popcount % 2 != 0) else 0
    elif mode == "odd":
        return 0 if (popcount % 2 != 0) else 1
    else:
        raise ValueError("Invalid parity mode '%s'; must be 'even' or 'odd'" % mode)

def verify_parity(data, expected_parity, mode="even"):
    """Verifies whether data matches the expected single-bit parity."""
    return calc_parity(data, mode=mode) == expected_parity

def add_parity_bit_to_byte(val, mode="even"):
    """
    Treats val as a 7-bit value (0-127) and places the parity bit in MSB (bit 7).
    Returns an 8-bit integer (0-255).
    """
    data_7bit = val & 0x7F
    p = calc_parity(data_7bit, mode=mode)
    return (p << 7) | data_7bit

def verify_parity_byte(byte_val, mode="even"):
    """Verifies that an 8-bit byte satisfies the specified parity rule."""
    popcount = bin(byte_val & 0xFF).count("1")
    if mode == "even":
        return (popcount % 2 == 0)
    elif mode == "odd":
        return (popcount % 2 != 0)
    else:
        raise ValueError("Invalid parity mode '%s'" % mode)


# ==============================================================================
# 2. TWO-DIMENSIONAL (2D) PARITY ENGINE & DIAGNOSTIC EXPLAINER
# ==============================================================================

# Status Constants
STATUS_OK = 0
STATUS_CORRECTED = 1
STATUS_ROW_PARITY_ERROR = 2
STATUS_COL_PARITY_ERROR = 3
STATUS_CORNER_PARITY_ERROR = 4
STATUS_UNCORRECTABLE = 5
STATUS_UNDETECTED = 6

class TwoDParityResult:
    """Pure-Python result structure for 2D parity decoding and syndrome analysis."""
    def __init__(self, status, bad_rows, bad_cols, corner_bad, corrected_loc, corrected_data, explanation):
        self.status = status
        self.bad_rows = bad_rows
        self.bad_cols = bad_cols
        self.corner_bad = corner_bad
        self.corrected_loc = corrected_loc
        self.corrected_data = corrected_data
        self.explanation = explanation

    def is_valid_or_corrected(self):
        return self.status in (STATUS_OK, STATUS_CORRECTED, STATUS_ROW_PARITY_ERROR, STATUS_COL_PARITY_ERROR, STATUS_CORNER_PARITY_ERROR)

    def __repr__(self):
        status_names = {
            STATUS_OK: "OK",
            STATUS_CORRECTED: "CORRECTED",
            STATUS_ROW_PARITY_ERROR: "ROW_PARITY_ERROR",
            STATUS_COL_PARITY_ERROR: "COL_PARITY_ERROR",
            STATUS_CORNER_PARITY_ERROR: "CORNER_PARITY_ERROR",
            STATUS_UNCORRECTABLE: "UNCORRECTABLE",
            STATUS_UNDETECTED: "UNDETECTED"
        }
        return "TwoDParityResult(status=%s, bad_rows=%s, bad_cols=%s, corner_bad=%s, loc=%s)" % (
            status_names.get(self.status, str(self.status)),
            self.bad_rows,
            self.bad_cols,
            self.corner_bad,
            self.corrected_loc
        )

def bytes_to_matrix(data_bytes):
    """Converts a bytes sequence into an M x 8 binary matrix (list of lists of 0/1)."""
    matrix = []
    for b in data_bytes:
        row = [(b >> (7 - c)) & 1 for c in range(8)]
        matrix.append(row)
    return matrix

def matrix_to_bytes(matrix):
    """Converts an M x 8 binary matrix back into a bytes object."""
    out = bytearray()
    for row in matrix:
        val = 0
        for bit in row:
            val = (val << 1) | (bit & 1)
        out.append(val)
    return bytes(out)

def encode_2d_parity(data_bytes, mode="even"):
    """
    Arranges data_bytes into an M x 8 matrix, then computes:
      - row_parities: list of length M (one parity bit per row)
      - col_parities: list of length 8 (one parity bit per column)
      - corner_bit: 1 bit (parity across row parities / col parities)
    Returns: (matrix, row_parities, col_parities, corner_bit)
    """
    if isinstance(data_bytes, (str, bytearray)):
        data_bytes = bytes(data_bytes) if isinstance(data_bytes, bytearray) else data_bytes.encode('utf-8')

    matrix = bytes_to_matrix(data_bytes)
    num_rows = len(matrix)

    # 1. Row Parity
    row_parities = []
    for r in range(num_rows):
        ones = sum(matrix[r])
        p = (ones % 2 != 0) if mode == "even" else (ones % 2 == 0)
        row_parities.append(1 if p else 0)

    # 2. Column Parity
    col_parities = []
    for c in range(8):
        ones = sum(matrix[r][c] for r in range(num_rows))
        p = (ones % 2 != 0) if mode == "even" else (ones % 2 == 0)
        col_parities.append(1 if p else 0)

    # 3. Corner Bit (Parity of row parities == Parity of col parities)
    r_ones = sum(row_parities)
    p_corner = (r_ones % 2 != 0) if mode == "even" else (r_ones % 2 == 0)
    corner_bit = 1 if p_corner else 0

    return matrix, row_parities, col_parities, corner_bit

def decode_2d_parity(matrix, row_parities, col_parities, corner_bit, mode="even"):
    """
    Recomputes parities, identifies syndrome violations, performs single-bit correction,
    and returns a TwoDParityResult with a diagnostic explanation.
    """
    num_rows = len(matrix)
    # Deep copy matrix to permit in-place correction without side-effects
    corrected_matrix = [list(row) for row in matrix]

    # Recompute row parities
    recomputed_row_p = []
    for r in range(num_rows):
        ones = sum(corrected_matrix[r])
        p = (ones % 2 != 0) if mode == "even" else (ones % 2 == 0)
        recomputed_row_p.append(1 if p else 0)
    bad_rows = [r for r in range(num_rows) if recomputed_row_p[r] != row_parities[r]]

    # Recompute col parities
    recomputed_col_p = []
    for c in range(8):
        ones = sum(corrected_matrix[r][c] for r in range(num_rows))
        p = (ones % 2 != 0) if mode == "even" else (ones % 2 == 0)
        recomputed_col_p.append(1 if p else 0)
    bad_cols = [c for c in range(8) if recomputed_col_p[c] != col_parities[c]]

    # Recompute corner bit (from recomputed row parities)
    r_ones = sum(recomputed_row_p)
    p_corner = (r_ones % 2 != 0) if mode == "even" else (r_ones % 2 == 0)
    recomputed_corner = 1 if p_corner else 0
    corner_bad = (recomputed_corner != corner_bit)

    # Syndrome Evaluation
    corrected_loc = None

    if len(bad_rows) == 0 and len(bad_cols) == 0 and not corner_bad:
        status = STATUS_OK
        corrected_data = matrix_to_bytes(corrected_matrix)
        explanation = "Clean transmission. Zero parity violations across %d rows and 8 columns." % num_rows
        return TwoDParityResult(status, bad_rows, bad_cols, corner_bad, corrected_loc, corrected_data, explanation)

    # Case 1: Single-bit error in data payload
    if len(bad_rows) == 1 and len(bad_cols) == 1:
        err_r = bad_rows[0]
        err_c = bad_cols[0]
        corrected_loc = (err_r, err_c)
        orig_val = corrected_matrix[err_r][err_c]
        new_val = 1 - orig_val
        corrected_matrix[err_r][err_c] = new_val
        status = STATUS_CORRECTED
        corrected_data = matrix_to_bytes(corrected_matrix)
        explanation = (
            "Single-bit data error detected at Row %d (byte %d), Column %d (bit %d). "
            "Syndrome intersection pinpointed corrupted bit. Bit inverted from %d to %d. "
            "Telemetry payload successfully self-healed." % (err_r, err_r, err_c, 7 - err_c, orig_val, new_val)
        )
        return TwoDParityResult(status, bad_rows, bad_cols, corner_bad, corrected_data=corrected_data, explanation=explanation, corrected_loc=corrected_loc)

    # Case 2: Exactly 1 row parity bit corrupted in transit
    if len(bad_rows) == 1 and len(bad_cols) == 0:
        status = STATUS_ROW_PARITY_ERROR
        corrected_data = matrix_to_bytes(corrected_matrix)
        explanation = (
            "Parity channel transmission error: Row parity bit for Row %d was corrupted in transit. "
            "Data bits across all 8 columns verified intact. Zero data corruption." % bad_rows[0]
        )
        return TwoDParityResult(status, bad_rows, bad_cols, corner_bad, corrected_loc, corrected_data, explanation)

    # Case 3: Exactly 1 column parity bit corrupted in transit
    if len(bad_rows) == 0 and len(bad_cols) == 1:
        status = STATUS_COL_PARITY_ERROR
        corrected_data = matrix_to_bytes(corrected_matrix)
        explanation = (
            "Parity channel transmission error: Column parity bit for Column %d was corrupted in transit. "
            "Data bits across all %d rows verified intact. Zero data corruption." % (bad_cols[0], num_rows)
        )
        return TwoDParityResult(status, bad_rows, bad_cols, corner_bad, corrected_loc, corrected_data, explanation)

    # Case 4: Only the corner parity bit corrupted
    if len(bad_rows) == 0 and len(bad_cols) == 0 and corner_bad:
        status = STATUS_CORNER_PARITY_ERROR
        corrected_data = matrix_to_bytes(corrected_matrix)
        explanation = (
            "Parity channel transmission error: Corner parity bit was corrupted in transit. "
            "All row and column parities verified intact. Zero data corruption."
        )
        return TwoDParityResult(status, bad_rows, bad_cols, corner_bad, corrected_loc, corrected_data, explanation)

    # Case 5: Multi-bit error pattern detected (uncorrectable)
    status = STATUS_UNCORRECTABLE
    corrected_data = matrix_to_bytes(corrected_matrix)
    explanation = (
        "Multi-bit error syndrome detected: %d violating rows %s and %d violating columns %s. "
        "Error pattern exceeds single-bit correction bounds. Ambiguous geometric intersection. "
        "Frame discarded; requesting automatic ARQ retransmission." % (len(bad_rows), bad_rows, len(bad_cols), bad_cols)
    )
    return TwoDParityResult(status, bad_rows, bad_cols, corner_bad, corrected_loc, corrected_data, explanation)

def explain_2d_parity(result):
    """Returns the diagnostic textual explanation from a TwoDParityResult."""
    return result.explanation


# ==============================================================================
# 3. 16-BIT INTERNET CHECKSUM (RFC 1071)
# ==============================================================================

def checksum16(data):
    """
    Computes standard 16-bit 1's complement Internet Checksum (RFC 1071).
    Works on bytes or bytearray.
    Algorithm:
      1. Pad with zero byte if length is odd.
      2. Sum all 16-bit big-endian words.
      3. Fold 32-bit carries back into lower 16 bits.
      4. Take 1's complement (bitwise NOT).
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    data = bytes(data)

    # Pad with 0 byte if odd length
    if len(data) % 2 != 0:
        data = data + b"\x00"

    total = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) | data[i + 1]
        total += word

    # Fold end-around carries
    while (total >> 16) > 0:
        total = (total & 0xFFFF) + (total >> 16)

    # 1's complement
    return (~total) & 0xFFFF

def verify_checksum16(data, expected_checksum):
    """
    Receiver verification per RFC 1071.
    Sums data words PLUS the checksum. Fold carries.
    Valid transmission produces folded sum == 0xFFFF (bitwise NOT == 0x0000).
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    data = bytes(data)

    if len(data) % 2 != 0:
        data = data + b"\x00"

    total = expected_checksum & 0xFFFF
    for i in range(0, len(data), 2):
        word = (data[i] << 8) | data[i + 1]
        total += word

    while (total >> 16) > 0:
        total = (total & 0xFFFF) + (total >> 16)

    return (total == 0xFFFF)


# ==============================================================================
# 4. BIT-WISE CRC-16 AND CRC-32 WITH CONFIGURABLE GENERATOR POLYNOMIALS
# ==============================================================================

def reflect_bits(val, bits):
    """Pure-Python bit reflection (reverses bit order in a word of width 'bits')."""
    res = 0
    for i in range(bits):
        if val & (1 << i):
            res |= 1 << (bits - 1 - i)
    return res

def crc_bitwise(data, width, poly, init=0, xor_out=0, reflect=False):
    """
    Bit-wise CRC calculation from first principles without precomputed tables.
    data    : bytes or bytearray
    width   : bit width (e.g. 16 or 32)
    poly    : generator polynomial (without the implicit x^width term)
    init    : initial shift-register value
    xor_out : final XOR value
    reflect : if True, uses LSB-first reflected algorithm (matches IEEE 802.3 / CRC-16-IBM)
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    data = bytes(data)

    mask = (1 << width) - 1

    if reflect:
        reg = init & mask
        poly_ref = reflect_bits(poly, width)
        for b in data:
            reg ^= b
            for _ in range(8):
                if reg & 1:
                    reg = (reg >> 1) ^ poly_ref
                else:
                    reg >>= 1
        return (reg ^ xor_out) & mask
    else:
        reg = init & mask
        top_bit = 1 << (width - 1)
        shift_diff = width - 8
        for b in data:
            if shift_diff >= 0:
                reg ^= (b << shift_diff)
            else:
                reg ^= (b >> (-shift_diff))
            for _ in range(8):
                if reg & top_bit:
                    reg = ((reg << 1) ^ poly) & mask
                else:
                    reg = (reg << 1) & mask
        return (reg ^ xor_out) & mask

# Standard Default CRC-16 (CRC-16-CCITT / CCITT-FALSE: poly=0x1021, init=0xFFFF)
def crc16(data, poly=0x1021, init=0xFFFF, xor_out=0x0000, reflect=False):
    """
    Computes 16-bit CRC bit-wise from scratch.
    Default: CRC-16-CCITT (poly 0x1021, init 0xFFFF).
    Configurable generator polynomial supported as parameter.
    """
    return crc_bitwise(data, width=16, poly=poly, init=init, xor_out=xor_out, reflect=reflect)

def verify_crc16(data, expected_crc, poly=0x1021, init=0xFFFF, xor_out=0x0000, reflect=False):
    """Verifies CRC-16 matches calculated value."""
    return crc16(data, poly=poly, init=init, xor_out=xor_out, reflect=reflect) == (expected_crc & 0xFFFF)

# Standard Default CRC-32 (IEEE 802.3 Ethernet: poly=0x04C11DB7, reflected)
def crc32(data, poly=0x04C11DB7, init=0xFFFFFFFF, xor_out=0xFFFFFFFF, reflect=True):
    """
    Computes 32-bit CRC bit-wise from scratch.
    Default: IEEE 802.3 Ethernet standard (poly 0x04C11DB7, reflected).
    Configurable generator polynomial supported as parameter.
    """
    return crc_bitwise(data, width=32, poly=poly, init=init, xor_out=xor_out, reflect=reflect)

def verify_crc32(data, expected_crc, poly=0x04C11DB7, init=0xFFFFFFFF, xor_out=0xFFFFFFFF, reflect=True):
    """Verifies CRC-32 matches calculated value."""
    return crc32(data, poly=poly, init=init, xor_out=xor_out, reflect=reflect) == (expected_crc & 0xFFFFFFFF)


# ==============================================================================
# 5. SENSOR TELEMETRY FRAME (ENCODE/DECODE, DATACLASS-LIKE STRUCTURE)
# ==============================================================================

# Sensor Type Constants
SENSOR_ECG = 1
SENSOR_SPO2 = 2
SENSOR_TEMP = 3
SENSOR_NIBP = 4
SENSOR_RESP = 5

# Check Scheme Constants
CHECK_NONE = 0
CHECK_PARITY = 1
CHECK_2D_PARITY = 2
CHECK_CHECKSUM = 3
CHECK_CRC16 = 4
CHECK_CRC32 = 5

CHECK_NAME_MAP = {
    CHECK_NONE: "NONE",
    CHECK_PARITY: "PARITY",
    CHECK_2D_PARITY: "2D_PARITY",
    CHECK_CHECKSUM: "CHECKSUM",
    CHECK_CRC16: "CRC16",
    CHECK_CRC32: "CRC32"
}

CHECK_CODE_MAP = {v: k for k, v in CHECK_NAME_MAP.items()}

class SensorFrame:
    """
    Clinical telemetry sensor frame structure.
    Works in pure Python across restricted Packet Tracer SBC environments without dataclasses.
    """
    PREAMBLE = b"\xAA\x55"

    def __init__(self, seq_num=0, patient_id="ICU-101", sensor_type=SENSOR_ECG, value=0.0, timestamp=0, payload=b"", check_type=CHECK_CRC16, check_value=None):
        self.seq_num = int(seq_num) & 0xFFFF
        self.patient_id = str(patient_id)[:8]
        self.sensor_type = int(sensor_type) & 0xFF
        self.value = float(value)
        self.timestamp = int(timestamp) & 0xFFFFFFFF
        if isinstance(payload, str):
            payload = payload.encode('utf-8')
        self.payload = bytes(payload)
        if isinstance(check_type, str):
            self.check_type = CHECK_CODE_MAP.get(check_type.upper(), CHECK_CRC16)
        else:
            self.check_type = int(check_type)
        self.check_value = check_value

    def _pack_protected_header(self):
        """Packs header fields excluding preamble and error-check."""
        hdr = bytearray()
        # Seq Num (2 bytes)
        hdr.append((self.seq_num >> 8) & 0xFF)
        hdr.append(self.seq_num & 0xFF)
        # Patient ID (8 bytes ASCII space-padded)
        pid_bytes = self.patient_id.encode('ascii')[:8].ljust(8, b' ')
        hdr.extend(pid_bytes)
        # Sensor Type (1 byte)
        hdr.append(self.sensor_type & 0xFF)
        # Scaled Value (4 bytes int32 = value * 1000)
        scaled_val = int(round(self.value * 1000)) & 0xFFFFFFFF
        hdr.append((scaled_val >> 24) & 0xFF)
        hdr.append((scaled_val >> 16) & 0xFF)
        hdr.append((scaled_val >> 8) & 0xFF)
        hdr.append(scaled_val & 0xFF)
        # Timestamp (4 bytes uint32)
        hdr.append((self.timestamp >> 24) & 0xFF)
        hdr.append((self.timestamp >> 16) & 0xFF)
        hdr.append((self.timestamp >> 8) & 0xFF)
        hdr.append(self.timestamp & 0xFF)
        # Check Type (1 byte)
        hdr.append(self.check_type & 0xFF)
        # Payload Length (2 bytes uint16)
        plen = len(self.payload) & 0xFFFF
        hdr.append((plen >> 8) & 0xFF)
        hdr.append(plen & 0xFF)
        return bytes(hdr)

    def encode(self):
        """Serializes the sensor frame into raw binary bytes with error-check."""
        protected = self._pack_protected_header() + self.payload
        check_bytes = bytearray()

        if self.check_type == CHECK_NONE:
            self.check_value = None
        elif self.check_type == CHECK_PARITY:
            p = calc_parity(protected, mode="even")
            self.check_value = p
            check_bytes.append(p)
        elif self.check_type == CHECK_2D_PARITY:
            matrix, row_p, col_p, corner_p = encode_2d_parity(protected, mode="even")
            self.check_value = (row_p, col_p, corner_p)
            # Serialize 2D parity:
            # 1 byte corner bit
            # 1 byte col parity (8 bits)
            # ceil(M/8) bytes row parities
            check_bytes.append(corner_p & 1)
            cbyte = 0
            for b in col_p:
                cbyte = (cbyte << 1) | (b & 1)
            check_bytes.append(cbyte)
            # Pack row parities
            curr_byte = 0
            bit_count = 0
            for rp in row_p:
                curr_byte = (curr_byte << 1) | (rp & 1)
                bit_count += 1
                if bit_count == 8:
                    check_bytes.append(curr_byte)
                    curr_byte = 0
                    bit_count = 0
            if bit_count > 0:
                curr_byte <<= (8 - bit_count)
                check_bytes.append(curr_byte)
        elif self.check_type == CHECK_CHECKSUM:
            cs = checksum16(protected)
            self.check_value = cs
            check_bytes.append((cs >> 8) & 0xFF)
            check_bytes.append(cs & 0xFF)
        elif self.check_type == CHECK_CRC16:
            c = crc16(protected)
            self.check_value = c
            check_bytes.append((c >> 8) & 0xFF)
            check_bytes.append(c & 0xFF)
        elif self.check_type == CHECK_CRC32:
            c = crc32(protected)
            self.check_value = c
            check_bytes.append((c >> 24) & 0xFF)
            check_bytes.append((c >> 16) & 0xFF)
            check_bytes.append((c >> 8) & 0xFF)
            check_bytes.append(c & 0xFF)
        else:
            raise ValueError("Unknown check_type %d" % self.check_type)

        return self.PREAMBLE + protected + bytes(check_bytes)

    @classmethod
    def decode(cls, raw_bytes):
        """
        Decodes raw bytes into a SensorFrame.
        Performs error-check verification and self-healing if 2D parity is used.
        Returns: (is_valid: bool, frame_instance: SensorFrame or None, error_message: str)
        """
        if not isinstance(raw_bytes, (bytes, bytearray)):
            return False, None, "Invalid input type (expected bytes)"
        raw_bytes = bytes(raw_bytes)

        if len(raw_bytes) < 24:
            return False, None, "Frame truncated: length %d < minimum 24 bytes" % len(raw_bytes)

        if raw_bytes[:2] != cls.PREAMBLE:
            return False, None, "Preamble mismatch: expected 0xAA55, got 0x%02X%02X" % (raw_bytes[0], raw_bytes[1])

        seq_num = (raw_bytes[2] << 8) | raw_bytes[3]
        patient_id = raw_bytes[4:12].decode('ascii', errors='replace').strip()
        sensor_type = raw_bytes[12]

        scaled_val = (raw_bytes[13] << 24) | (raw_bytes[14] << 16) | (raw_bytes[15] << 8) | raw_bytes[16]
        if scaled_val >= 0x80000000:
            scaled_val -= 0x100000000
        val = scaled_val / 1000.0

        timestamp = (raw_bytes[17] << 24) | (raw_bytes[18] << 16) | (raw_bytes[19] << 8) | raw_bytes[20]
        check_type = raw_bytes[21]
        payload_len = (raw_bytes[22] << 8) | raw_bytes[23]

        protected_end = 24 + payload_len
        if len(raw_bytes) < protected_end:
            return False, None, "Frame truncated: payload indicates %d bytes, wire has %d" % (payload_len, len(raw_bytes) - 24)

        protected_data = raw_bytes[2:protected_end]
        payload = raw_bytes[24:protected_end]
        check_field = raw_bytes[protected_end:]

        # Verify error check
        if check_type == CHECK_NONE:
            frame = cls(seq_num, patient_id, sensor_type, val, timestamp, payload, check_type=CHECK_NONE)
            return True, frame, "Clean (no error check)"

        elif check_type == CHECK_PARITY:
            if len(check_field) < 1:
                return False, None, "Missing parity check byte"
            expected_p = check_field[0] & 1
            if not verify_parity(protected_data, expected_p, mode="even"):
                return False, None, "Parity check failed: single-bit parity violation"
            frame = cls(seq_num, patient_id, sensor_type, val, timestamp, payload, check_type=CHECK_PARITY, check_value=expected_p)
            return True, frame, "Clean (parity verified)"

        elif check_type == CHECK_2D_PARITY:
            num_rows = len(protected_data)
            expected_row_bytes = (num_rows + 7) // 8
            if len(check_field) < 2 + expected_row_bytes:
                return False, None, "Truncated 2D parity check field (expected %d bytes, got %d)" % (2 + expected_row_bytes, len(check_field))
            corner_bit = check_field[0] & 1
            col_byte = check_field[1]
            col_parities = [(col_byte >> (7 - c)) & 1 for c in range(8)]
            # Unpack row parities
            row_parities = []
            for i in range(num_rows):
                byte_idx = 2 + (i // 8)
                bit_idx = 7 - (i % 8)
                row_parities.append((check_field[byte_idx] >> bit_idx) & 1)

            matrix = bytes_to_matrix(protected_data)
            result = decode_2d_parity(matrix, row_parities, col_parities, corner_bit, mode="even")

            if not result.is_valid_or_corrected():
                return False, None, "2D Parity Rejected: " + result.explanation

            # If single-bit error was corrected, re-extract protected fields!
            if result.status == STATUS_CORRECTED:
                fixed_protected = result.corrected_data
                seq_num = (fixed_protected[0] << 8) | fixed_protected[1]
                patient_id = fixed_protected[2:10].decode('ascii', errors='replace').strip()
                sensor_type = fixed_protected[10]
                scaled_val = (fixed_protected[11] << 24) | (fixed_protected[12] << 16) | (fixed_protected[13] << 8) | fixed_protected[14]
                if scaled_val >= 0x80000000:
                    scaled_val -= 0x100000000
                val = scaled_val / 1000.0
                timestamp = (fixed_protected[15] << 24) | (fixed_protected[16] << 16) | (fixed_protected[17] << 8) | fixed_protected[18]
                payload = fixed_protected[22:]

            frame = cls(seq_num, patient_id, sensor_type, val, timestamp, payload, check_type=CHECK_2D_PARITY, check_value=(row_parities, col_parities, corner_bit))
            return True, frame, result.explanation

        elif check_type == CHECK_CHECKSUM:
            if len(check_field) < 2:
                return False, None, "Truncated checksum field"
            expected_cs = (check_field[0] << 8) | check_field[1]
            if not verify_checksum16(protected_data, expected_cs):
                return False, None, "RFC 1071 16-Bit Checksum failed (computed != expected 0x%04X)" % expected_cs
            frame = cls(seq_num, patient_id, sensor_type, val, timestamp, payload, check_type=CHECK_CHECKSUM, check_value=expected_cs)
            return True, frame, "Clean (16-bit checksum verified)"

        elif check_type == CHECK_CRC16:
            if len(check_field) < 2:
                return False, None, "Truncated CRC-16 field"
            expected_crc = (check_field[0] << 8) | check_field[1]
            if not verify_crc16(protected_data, expected_crc):
                return False, None, "CRC-16 mismatch (computed != expected 0x%04X)" % expected_crc
            frame = cls(seq_num, patient_id, sensor_type, val, timestamp, payload, check_type=CHECK_CRC16, check_value=expected_crc)
            return True, frame, "Clean (CRC-16 verified)"

        elif check_type == CHECK_CRC32:
            if len(check_field) < 4:
                return False, None, "Truncated CRC-32 field"
            expected_crc = (check_field[0] << 24) | (check_field[1] << 16) | (check_field[2] << 8) | check_field[3]
            if not verify_crc32(protected_data, expected_crc):
                return False, None, "CRC-32 mismatch (computed != expected 0x%08X)" % expected_crc
            frame = cls(seq_num, patient_id, sensor_type, val, timestamp, payload, check_type=CHECK_CRC32, check_value=expected_crc)
            return True, frame, "Clean (CRC-32 verified)"

        else:
            return False, None, "Unknown check_type %d" % check_type

    def __repr__(self):
        return "SensorFrame(seq=%d, patient='%s', type=%d, val=%.2f, time=%d, plen=%d, check=%s)" % (
            self.seq_num,
            self.patient_id,
            self.sensor_type,
            self.value,
            self.timestamp,
            len(self.payload),
            CHECK_NAME_MAP.get(self.check_type, str(self.check_type))
        )

    def __eq__(self, other):
        if not isinstance(other, SensorFrame):
            return False
        return (
            self.seq_num == other.seq_num and
            self.patient_id == other.patient_id and
            self.sensor_type == other.sensor_type and
            abs(self.value - other.value) < 0.001 and
            self.timestamp == other.timestamp and
            self.payload == other.payload and
            self.check_type == other.check_type
        )


# ==============================================================================
# 6. CHANNEL ERROR INJECTOR
# ==============================================================================

class ErrorInjector:
    """
    Simulates channel impairments and bit corruptions on transmitted binary buffers.
    Supports single flips, n-random flips, burst errors of length k, and targeted patterns.
    """
    @staticmethod
    def flip_bit(data, bit_index):
        """Flips a single bit at absolute bit_index (0-indexed, MSB first)."""
        ba = bytearray(data)
        byte_idx = bit_index // 8
        bit_pos = 7 - (bit_index % 8)
        if 0 <= byte_idx < len(ba):
            ba[byte_idx] ^= (1 << bit_pos)
        return bytes(ba)

    @staticmethod
    def flip_random_bits(data, n, seed=None):
        """Flips exactly n distinct randomly selected bits across data."""
        ba = bytearray(data)
        total_bits = len(ba) * 8
        if total_bits == 0 or n <= 0:
            return bytes(ba)
        n = min(n, total_bits)

        import random
        rng = random.Random(seed) if seed is not None else random
        chosen_indices = rng.sample(range(total_bits), n)

        for bit_idx in chosen_indices:
            byte_idx = bit_idx // 8
            bit_pos = 7 - (bit_idx % 8)
            ba[byte_idx] ^= (1 << bit_pos)

        return bytes(ba)

    @staticmethod
    def inject_burst_error(data, k, start_bit=None, seed=None, corrupt_intermediate=True):
        """
        Injects a burst error of length k across data.
        A burst of length k guarantees:
          - Bit at start_bit is inverted.
          - Bit at start_bit + k - 1 is inverted (if k > 1).
          - Intermediate bits are flipped with 50% probability (or all if corrupt_intermediate=True).
        """
        ba = bytearray(data)
        total_bits = len(ba) * 8
        if total_bits == 0 or k <= 0:
            return bytes(ba)

        k = min(k, total_bits)
        import random
        rng = random.Random(seed) if seed is not None else random

        if start_bit is None:
            max_start = total_bits - k
            start_bit = rng.randint(0, max_start) if max_start > 0 else 0

        # First bit of burst always flipped
        ba[start_bit // 8] ^= (1 << (7 - (start_bit % 8)))

        # Last bit of burst always flipped
        if k > 1:
            end_bit = start_bit + k - 1
            ba[end_bit // 8] ^= (1 << (7 - (end_bit % 8)))

        # Intermediate bits
        for bit_idx in range(start_bit + 1, start_bit + k - 1):
            should_flip = (rng.random() < 0.5) if not corrupt_intermediate else True
            if should_flip:
                ba[bit_idx // 8] ^= (1 << (7 - (bit_idx % 8)))

        return bytes(ba)

    @staticmethod
    def inject_rectangular_4bit_error(data, row1, row2, col1, col2):
        """
        Injects the classic 4-bit rectangular pattern that defeats 2D parity.
        Flips bits at:
          (row1, col1), (row1, col2), (row2, col1), and (row2, col2)
        Both rows retain even parity; both columns retain even parity; corner bit unchanged!
        """
        ba = bytearray(data)
        num_rows = len(ba)
        if not (0 <= row1 < num_rows and 0 <= row2 < num_rows and row1 != row2):
            raise IndexError("row1 and row2 must be distinct indices within [0, %d)" % num_rows)
        if not (0 <= col1 < 8 and 0 <= col2 < 8 and col1 != col2):
            raise IndexError("col1 and col2 must be distinct column indices within [0, 8)")

        # Flip the 4 corners of the rectangle
        coords = [(row1, col1), (row1, col2), (row2, col1), (row2, col2)]
        for r, c in coords:
            ba[r] ^= (1 << (7 - c))

        return bytes(ba)
