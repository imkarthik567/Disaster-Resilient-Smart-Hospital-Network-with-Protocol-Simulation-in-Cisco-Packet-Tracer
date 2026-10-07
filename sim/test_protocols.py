#!/usr/bin/env python3
"""
Pytest Suite for Protocol Simulations
Disaster-Resilient Smart Hospital Network
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "sbc"))

from parity_2d import encode_2d_parity, verify_and_correct
from checksum import compute_checksum_16bit, verify_checksum_16bit
from go_back_n import GoBackNSimulator
from selective_repeat import SelectiveRepeatSimulator

def test_checksum_valid():
    words = [0x4943, 0x5531, 0x5263, 0x7D50]
    chk = compute_checksum_16bit(words)
    valid, res = verify_checksum_16bit(words, chk)
    assert valid is True
    assert res == 0xFFFF

def test_checksum_corruption():
    words = [0x4943, 0x5531, 0x5263, 0x7D50]
    chk = compute_checksum_16bit(words)
    corrupted = list(words)
    corrupted[1] = 0x5532  # 1-bit flip
    valid, _ = verify_checksum_16bit(corrupted, chk)
    assert valid is False

def test_2d_parity_single_bit_correction():
    data = [78, 98, 120, 37]
    matrix, row_p, col_p = encode_2d_parity(data)
    # Flip bit at (1, 3)
    matrix[1][3] = 1 - matrix[1][3]
    success, fixed = verify_and_correct(matrix, row_p, col_p)
    assert success is True
    # Verify bit was restored
    expected_matrix, _, _ = encode_2d_parity(data)
    assert fixed == expected_matrix

def test_go_back_n_simulation():
    sim = GoBackNSimulator(total_frames=10, window_size=3, loss_frames=[2])
    res = sim.simulate()
    assert res["frames"] == 10
    assert res["total_sent"] > 10  # Must incur retransmissions
    assert res["retransmissions"] > 0

def test_selective_repeat_efficiency_higher_than_gbn():
    test_losses = [2, 5]
    gbn = GoBackNSimulator(total_frames=12, window_size=4, loss_frames=list(test_losses))
    res_gbn = gbn.simulate()

    sr = SelectiveRepeatSimulator(total_frames=12, window_size=4, loss_frames=list(test_losses))
    res_sr = sr.simulate()

    assert res_sr["efficiency"] > res_gbn["efficiency"]
    assert res_sr["retransmissions"] <= res_gbn["retransmissions"]
