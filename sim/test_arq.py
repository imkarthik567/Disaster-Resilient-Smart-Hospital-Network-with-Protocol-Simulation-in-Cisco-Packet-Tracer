#!/usr/bin/env python3
"""
Unit Test Suite: Sliding-Window ARQ Protocols (Stop-and-Wait, GBN, Selective Repeat)
Validates /sbc/arq.py against project specifications, sequence space constraints,
in-order delivery under loss, retransmission selectivity, and timeline trace logging.
Pytest-compatible with standalone fallback runner.
"""

import os
import sys
try:
    import pytest
except ImportError:
    pytest = None

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sbc.arq import (
    StopAndWaitProtocol, GoBackNProtocol, SelectiveRepeatProtocol,
    SimulatedChannel, ARQSimulation, ARQFrame
)

# ==============================================================================
# 1. SEQUENCE NUMBER SPACE CONSTRAINT TESTS
# ==============================================================================

def test_sequence_space_constraints_assertions():
    """Verify that GBN requires M >= N+1 and SR requires M >= 2N, raising AssertionError otherwise."""
    # 1. GBN valid (N=4, M=5, 8, 16)
    gbn_ok = GoBackNProtocol(window_size=4, seq_modulus=5)
    assert gbn_ok.seq_modulus == 5

    # GBN invalid (N=4, M=4 -> violation!)
    with pytest.raises(AssertionError) if pytest else AssertRaises(AssertionError):
        GoBackNProtocol(window_size=4, seq_modulus=4)

    # 2. Selective Repeat valid (N=4, M=8, 16)
    sr_ok = SelectiveRepeatProtocol(window_size=4, seq_modulus=8)
    assert sr_ok.seq_modulus == 8

    # Selective Repeat invalid (N=4, M=7 -> violation! needs M >= 2N = 8)
    with pytest.raises(AssertionError) if pytest else AssertRaises(AssertionError):
        SelectiveRepeatProtocol(window_size=4, seq_modulus=7)

    # 3. Stop-and-Wait valid (N=1, M=2)
    sw_ok = StopAndWaitProtocol()
    assert sw_ok.window_size == 1
    assert sw_ok.seq_modulus == 2

class AssertRaises:
    """Helper context manager when pytest is not installed."""
    def __init__(self, exc_type):
        self.exc_type = exc_type
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        assert exc_type is not None and issubclass(exc_type, self.exc_type), (
            "Expected %s, got %s" % (self.exc_type, exc_type)
        )
        return True

# ==============================================================================
# 2. RETRANSMISSION BEHAVIOR TESTS: GBN (WHOLE WINDOW) VS SR (SELECTIVE ONLY)
# ==============================================================================

def test_gbn_retransmits_entire_window():
    """Verify that Go-Back-N retransmits all unacknowledged frames in the window upon timeout."""
    channel = SimulatedChannel(loss_prob=0.0, prop_delay=2, seed=42)
    gbn = GoBackNProtocol(window_size=4, seq_modulus=16, timeout_ticks=10, verbose=False)

    # Queue 4 frames: #0, #1, #2, #3
    chunks = [b"FRAME_%d" % i for i in range(4)]
    for c in chunks:
        gbn.queue_payload(c)

    # Step simulation until all 4 frames are in flight (tick 0)
    gbn.step(0, channel)

    # Intercept and drop Frame #1 from channel queue to force timeout on #1
    channel.to_receiver_queue = [
        item for item in channel.to_receiver_queue if item['frame'].seq_num != 1
    ]

    # Advance clock to trigger timeout on #1 (timeout is tick 10)
    for tick in range(1, 15):
        gbn.step(tick, channel)

    # Verify GBN behavior: upon timeout on #1, it retransmitted BOTH #1, #2, and #3
    assert gbn.timeouts >= 1
    # Check trace log for GBN retransmission markers
    gbn_resends = [line for line in gbn.trace_log if "[GBN-RESEND]" in line]
    assert len(gbn_resends) >= 2, "GBN must retransmit all outstanding frames in window"

def test_sr_retransmits_only_missing_frame():
    """Verify that Selective Repeat retransmits ONLY the single missing frame upon timeout."""
    channel = SimulatedChannel(loss_prob=0.0, prop_delay=2, seed=42)
    sr = SelectiveRepeatProtocol(window_size=4, seq_modulus=16, timeout_ticks=10, verbose=False)

    chunks = [b"FRAME_%d" % i for i in range(4)]
    for c in chunks:
        sr.queue_payload(c)

    # Step tick 0: all 4 frames transmitted
    sr.step(0, channel)

    # Drop ONLY Frame #1
    channel.to_receiver_queue = [
        item for item in channel.to_receiver_queue if item['frame'].seq_num != 1
    ]

    # Frames #0, #2, #3 arrive at receiver; #2 and #3 are buffered out-of-order
    for tick in range(1, 15):
        sr.step(tick, channel)

    # Verify SR behavior: retransmitted ONLY Frame #1!
    sr_resends = [line for line in sr.trace_log if "[SELECTIVE-TIMEOUT] Resending ONLY Frame #1" in line]
    assert len(sr_resends) >= 1, "Selective Repeat must retransmit ONLY Frame #1"

    # Frame #2 and #3 should NOT have been retransmitted
    sr_resend_others = [line for line in sr.trace_log if "[SELECTIVE-TIMEOUT] Resending ONLY Frame #2" in line or "[SELECTIVE-TIMEOUT] Resending ONLY Frame #3" in line]
    assert len(sr_resend_others) == 0, "Frames #2 and #3 must NOT be retransmitted in SR"

# ==============================================================================
# 3. END-TO-END IN-ORDER DELIVERY & ZERO DUPLICATE TESTS UNDER LOSS
# ==============================================================================

def run_protocol_transfer_test(protocol_class, loss_rate, num_chunks=40, chunk_size=250):
    """Executes end-to-end payload transfer test under specified channel loss rate."""
    channel = SimulatedChannel(loss_prob=loss_rate, prop_delay=3, seed=123)
    if protocol_class == StopAndWaitProtocol:
        proto = protocol_class(timeout_ticks=15, verbose=False)
    else:
        proto = protocol_class(window_size=4, seq_modulus=16, timeout_ticks=15, verbose=False)

    sim = ARQSimulation(proto, channel, max_ticks=20000)

    # Generate synthetic patient payload (scaled binary chunks)
    original_chunks = [b"PATIENT_VITAL_CHUNK_%04d_" % i + (b"X" * (chunk_size - 25)) for i in range(num_chunks)]
    expected_data = b"".join(original_chunks)

    metrics, _ = sim.run_transfer(original_chunks)

    # Assertions
    # 1. Total delivered bytes matches original exactly
    assert proto.delivered_data == expected_data, "Delivered payload does not match original data!"

    # 2. Number of delivered chunks matches without missing or duplicate application deliveries
    assert len(proto.delivered_chunks) == num_chunks, (
        "Delivered chunk count mismatch: expected %d, got %d" % (num_chunks, len(proto.delivered_chunks))
    )
    assert proto.delivered_chunks == original_chunks, "Delivered chunks out-of-order!"

    # 3. Zero loss check
    if loss_rate == 0.0:
        assert metrics['frames_retransmitted'] == 0
        assert metrics['protocol_efficiency_pct'] == 100.0
    else:
        # Under loss, retransmissions must have occurred
        assert metrics['frames_retransmitted'] > 0
        assert metrics['timeouts'] > 0

    return metrics

def test_stop_and_wait_loss_scenarios():
    """Verify Stop-and-Wait under 0%, 5%, and 20% loss."""
    m0 = run_protocol_transfer_test(StopAndWaitProtocol, loss_rate=0.0, num_chunks=20)
    assert m0['delivered_chunks'] == 20

    m5 = run_protocol_transfer_test(StopAndWaitProtocol, loss_rate=0.05, num_chunks=20)
    assert m5['delivered_chunks'] == 20

    m20 = run_protocol_transfer_test(StopAndWaitProtocol, loss_rate=0.20, num_chunks=20)
    assert m20['delivered_chunks'] == 20

def test_go_back_n_loss_scenarios():
    """Verify Go-Back-N under 0%, 5%, and 20% loss."""
    m0 = run_protocol_transfer_test(GoBackNProtocol, loss_rate=0.0, num_chunks=30)
    assert m0['delivered_chunks'] == 30

    m5 = run_protocol_transfer_test(GoBackNProtocol, loss_rate=0.05, num_chunks=30)
    assert m5['delivered_chunks'] == 30

    m20 = run_protocol_transfer_test(GoBackNProtocol, loss_rate=0.20, num_chunks=30)
    assert m20['delivered_chunks'] == 30

def test_selective_repeat_loss_scenarios():
    """Verify Selective Repeat under 0%, 5%, and 20% loss."""
    m0 = run_protocol_transfer_test(SelectiveRepeatProtocol, loss_rate=0.0, num_chunks=30)
    assert m0['delivered_chunks'] == 30

    m5 = run_protocol_transfer_test(SelectiveRepeatProtocol, loss_rate=0.05, num_chunks=30)
    assert m5['delivered_chunks'] == 30

    m20 = run_protocol_transfer_test(SelectiveRepeatProtocol, loss_rate=0.20, num_chunks=30)
    assert m20['delivered_chunks'] == 30

# ==============================================================================
# 4. CHANNEL CORRUPTION RECOVERY TEST
# ==============================================================================

def test_arq_channel_bit_corruption_recovery():
    """Verify that bit-corrupted frames are rejected by receiver and successfully retransmitted."""
    channel = SimulatedChannel(loss_prob=0.0, corruption_prob=0.15, prop_delay=2, seed=99)
    sr = SelectiveRepeatProtocol(window_size=4, seq_modulus=16, timeout_ticks=12, verbose=False)
    sim = ARQSimulation(sr, channel, max_ticks=15000)

    chunks = [b"VITAL_ECG_SAMPLE_%d" % i for i in range(25)]
    metrics, _ = sim.run_transfer(chunks)

    assert sr.delivered_data == b"".join(chunks)
    assert metrics['delivered_chunks'] == 25
    assert channel.total_frames_corrupted > 0

# ==============================================================================
# 5. TIMELINE TRACE MODE FORMAT TEST
# ==============================================================================

def test_verbose_timeline_trace_output():
    """Verify high-resolution timeline trace generator suitable for report screenshots."""
    channel = SimulatedChannel(loss_prob=0.10, prop_delay=3, seed=42)
    sr = SelectiveRepeatProtocol(window_size=4, seq_modulus=16, timeout_ticks=12, verbose=False)
    sim = ARQSimulation(sr, channel, max_ticks=2000)

    chunks = [b"HR=82,SPO2=99", b"HR=84,SPO2=98", b"HR=81,SPO2=99", b"HR=85,SPO2=99"]
    metrics, trace = sim.run_transfer(chunks)

    assert len(trace) > 10
    assert any("[T=" in line for line in trace)
    assert any("SENDER" in line for line in trace)
    assert any("RECEIVER" in line for line in trace)

    print("\n--- SAMPLE TIMELINE TRACE SNIPPET FOR VIVA REPORT ---")
    for line in trace[:12]:
        print("  " + line)
    print("----------------------------------------------------\n")

if __name__ == "__main__":
    if pytest is not None:
        sys.exit(pytest.main(["-v", __file__]))
    else:
        print("=" * 70)
        print("  RUNNING SLIDING-WINDOW ARQ PROTOCOLS TEST SUITE")
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
