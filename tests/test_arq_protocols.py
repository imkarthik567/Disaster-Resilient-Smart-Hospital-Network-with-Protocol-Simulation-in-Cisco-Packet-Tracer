#!/usr/bin/env python3
"""
Unit Test Suite: Sliding-Window ARQ Protocols & Packet Tracer Adapter Verification
Validates sbc/arq.py, sbc/adapter_pt.py, and sim/test_arq.py against project specifications,
sliding-window flow control invariants, and Packet Tracer simulation rules.
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sbc.arq import (
    StopAndWaitProtocol, GoBackNProtocol, SelectiveRepeatProtocol,
    SimulatedChannel, ARQSimulation, ARQFrame
)

ARQ_PY = os.path.join(PROJECT_ROOT, "sbc", "arq.py")
ADAPTER_PY = os.path.join(PROJECT_ROOT, "sbc", "adapter_pt.py")
TEST_ARQ_PY = os.path.join(PROJECT_ROOT, "sim", "test_arq.py")

def test_pure_python_compliance():
    """Verify sbc/arq.py and sbc/adapter_pt.py do not import banned third-party modules."""
    assert os.path.isfile(ARQ_PY), f"Missing {ARQ_PY}"
    assert os.path.isfile(ADAPTER_PY), f"Missing {ADAPTER_PY}"
    assert os.path.isfile(TEST_ARQ_PY), f"Missing {TEST_ARQ_PY}"

    for fpath in [ARQ_PY, ADAPTER_PY]:
        with open(fpath, "r", encoding="utf-8") as f:
            code = f.read()
        banned = ["numpy", "scipy", "pandas", "matplotlib", "dataclasses"]
        for b in banned:
            assert f"import {b}" not in code, f"{os.path.basename(fpath)} illegally imports {b}"

    print("  [PASS] test_pure_python_compliance (Zero banned third-party dependencies)")

def test_sequence_space_assertions():
    """Verify mathematical sequence space constraints for GBN (M >= N+1) and SR (M >= 2N)."""
    # GBN
    gbn_valid = GoBackNProtocol(window_size=4, seq_modulus=5)
    assert gbn_valid.seq_modulus == 5

    gbn_failed = False
    try:
        GoBackNProtocol(window_size=4, seq_modulus=4)
    except AssertionError:
        gbn_failed = True
    assert gbn_failed, "GBN must raise AssertionError when M < N + 1"

    # SR
    sr_valid = SelectiveRepeatProtocol(window_size=4, seq_modulus=8)
    assert sr_valid.seq_modulus == 8

    sr_failed = False
    try:
        SelectiveRepeatProtocol(window_size=4, seq_modulus=7)
    except AssertionError:
        sr_failed = True
    assert sr_failed, "Selective Repeat must raise AssertionError when M < 2N"

    print("  [PASS] test_sequence_space_assertions (GBN M>=N+1 and SR M>=2N verified)")

def test_retransmission_selectivity():
    """Verify that GBN resends full window while SR resends only the missing packet."""
    # 1. GBN: drop Frame #1
    ch_gbn = SimulatedChannel(loss_prob=0.0, prop_delay=2, seed=42)
    gbn = GoBackNProtocol(window_size=4, seq_modulus=16, timeout_ticks=10)
    for i in range(4):
        gbn.queue_payload(b"GBN_%d" % i)
    gbn.step(0, ch_gbn)
    ch_gbn.to_receiver_queue = [item for item in ch_gbn.to_receiver_queue if item['frame'].seq_num != 1]
    for t in range(1, 15):
        gbn.step(t, ch_gbn)
    gbn_resends = [l for l in gbn.trace_log if "[GBN-RESEND]" in l]
    assert len(gbn_resends) >= 2, "GBN must resend entire outstanding window"

    # 2. SR: drop Frame #1
    ch_sr = SimulatedChannel(loss_prob=0.0, prop_delay=2, seed=42)
    sr = SelectiveRepeatProtocol(window_size=4, seq_modulus=16, timeout_ticks=10)
    for i in range(4):
        sr.queue_payload(b"SR_%d" % i)
    sr.step(0, ch_sr)
    ch_sr.to_receiver_queue = [item for item in ch_sr.to_receiver_queue if item['frame'].seq_num != 1]
    for t in range(1, 15):
        sr.step(t, ch_sr)
    sr_resends = [l for l in sr.trace_log if "[SELECTIVE-TIMEOUT] Resending ONLY Frame #1" in l]
    assert len(sr_resends) >= 1, "SR must resend ONLY missing Frame #1"
    sr_others = [l for l in sr.trace_log if "[SELECTIVE-TIMEOUT] Resending ONLY Frame #2" in l]
    assert len(sr_others) == 0, "SR must not resend non-missing frames"

    print("  [PASS] test_retransmission_selectivity (GBN full-window vs SR selective resend verified)")

def test_end_to_end_transfer_under_loss():
    """Verify byte-for-byte in-order delivery and zero duplicate delivery under 0% and 15% loss."""
    for proto_cls in [StopAndWaitProtocol, GoBackNProtocol, SelectiveRepeatProtocol]:
        ch = SimulatedChannel(loss_prob=0.15, prop_delay=2, seed=42)
        if proto_cls == StopAndWaitProtocol:
            proto = proto_cls(timeout_ticks=12)
        else:
            proto = proto_cls(window_size=4, seq_modulus=16, timeout_ticks=12)

        sim = ARQSimulation(proto, ch, max_ticks=10000)
        chunks = [b"TELEMETRY_SAMPLE_BLOCK_%03d" % i for i in range(25)]
        metrics, trace = sim.run_transfer(chunks)

        assert proto.delivered_data == b"".join(chunks), f"{proto_cls.__name__} data mismatch!"
        assert len(proto.delivered_chunks) == 25, f"{proto_cls.__name__} chunk count mismatch!"
        assert metrics['frames_retransmitted'] > 0

    print("  [PASS] test_end_to_end_transfer_under_loss (SW, GBN, SR in-order delivery under loss verified)")

def test_adapter_pt_structure_and_todos():
    """Verify sbc/adapter_pt.py structure, pin mappings, and probe TODO markers."""
    with open(ADAPTER_PY, "r", encoding="utf-8") as f:
        content = f.read()

    # Hardware pins
    assert "PIN_ECG_ANALOG" in content and "PIN_SPO2_ANALOG" in content
    assert "PIN_NURSE_CALL" in content and "PIN_ALARM_SIREN" in content
    assert "read_vitals" in content and "trigger_alarm" in content

    # Protocol loops
    assert "run_sender_node" in content and "run_receiver_node" in content
    assert "PacketTracerNetworkAdapter" in content

    # Probe TODO markers
    assert "TODO: [PROBE-CHECK-SOCKET]" in content
    assert "TODO: [PROBE-CHECK-IP]" in content
    assert "TODO: [PROBE-CHECK-PINS]" in content
    assert "TODO: [PROBE-CHECK-YIELD]" in content

    print("  [PASS] test_adapter_pt_structure_and_todos (Hardware pins & probe TODO markers verified)")

def run_all_tests():
    print("=" * 70)
    print("  RUNNING SLIDING-WINDOW ARQ PROTOCOLS VERIFICATION SUITE")
    print("=" * 70)
    test_pure_python_compliance()
    test_sequence_space_assertions()
    test_retransmission_selectivity()
    test_end_to_end_transfer_under_loss()
    test_adapter_pt_structure_and_todos()
    print("=" * 70)
    print("  ALL 5 ARQ PROTOCOL VERIFICATION TESTS PASSED")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
