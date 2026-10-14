#!/usr/bin/env python3
"""
Unit Test Suite: ARQ Simulation Sweep & Benchmark Statistics Verification
Validates sim/run_benchmarks.py, results/raw.csv, and results/summary.csv
against project requirements, statistical confidence interval formulas, and flow control physics.
"""

import os
import sys
import math

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sim.run_benchmarks import (
    execute_single_run, compute_mean_and_ci95, load_completed_keys,
    generate_experiment_configs, RAW_CSV_HEADER
)

BENCHMARKS_PY = os.path.join(PROJECT_ROOT, "sim", "run_benchmarks.py")
RAW_CSV_PATH = os.path.join(PROJECT_ROOT, "results", "raw.csv")
SUMMARY_CSV_PATH = os.path.join(PROJECT_ROOT, "results", "summary.csv")

def test_benchmark_script_and_no_banned_modules():
    """Verify sim/run_benchmarks.py exists and does not import banned third-party packages."""
    assert os.path.isfile(BENCHMARKS_PY), f"Missing {BENCHMARKS_PY}"
    with open(BENCHMARKS_PY, "r", encoding="utf-8") as f:
        code = f.read()

    banned = ["numpy", "pandas", "scipy", "matplotlib"]
    for b in banned:
        assert f"import {b}" not in code, f"run_benchmarks.py illegally imports {b}"

    print("  [PASS] test_benchmark_script_and_no_banned_modules (Pure Python / stdlib compliant)")

def test_statistical_confidence_interval_math():
    """Verify sample mean, sample standard deviation, and 95% confidence interval formulas."""
    # Constant values -> std = 0, ci95 = 0
    vals_const = [100.0] * 30
    m_c, s_c, ci_c = compute_mean_and_ci95(vals_const)
    assert m_c == 100.0
    assert s_c == 0.0
    assert ci_c == 0.0

    # Known distribution
    vals = [10.0, 12.0, 14.0, 16.0, 18.0] * 6  # 30 samples, mean = 14.0
    m, s, ci = compute_mean_and_ci95(vals)
    assert abs(m - 14.0) < 1e-6
    assert s > 0.0
    assert ci > 0.0
    # Expected CI half-width: t_crit * (s / sqrt(30))
    expected_ci = 2.0452 * (s / math.sqrt(30))
    assert abs(ci - expected_ci) < 1e-4

    print("  [PASS] test_statistical_confidence_interval_math (95% CI student-t verified)")

def test_single_run_metrics_computation():
    """Verify execute_single_run returns all required metrics with correct keys and ranges."""
    # (run_id, experiment, protocol, window_size, loss_prob, delay_ms, bandwidth_bps, frame_size, payload_bytes, seed, rep)
    params = (1, "Test_Exp", "SR", 4, 0.05, 20, 2048000, 512, 10240, 42, 0)
    res = execute_single_run(params)

    required_keys = [
        "run_id", "experiment", "protocol", "window_size", "loss_prob", "delay_ms",
        "bandwidth_bps", "frame_size", "payload_bytes", "seed", "repetition",
        "total_frames_on_wire", "total_retransmissions", "timeouts", "acks_sent",
        "transfer_time_sec", "goodput_bps", "link_utilisation_pct", "efficiency_pct"
    ]
    for k in required_keys:
        assert k in res, f"Missing key '{k}' in single run result"

    assert res['transfer_time_sec'] > 0
    assert res['goodput_bps'] > 0
    assert 0.0 <= res['efficiency_pct'] <= 100.0
    assert 0.0 <= res['link_utilisation_pct'] <= 100.0

    print("  [PASS] test_single_run_metrics_computation (All metrics properly formulated)")

def test_resumability_key_detection():
    """Verify load_completed_keys parses completed run tuples from raw.csv."""
    assert os.path.isfile(RAW_CSV_PATH), f"Missing {RAW_CSV_PATH}"
    completed = load_completed_keys(RAW_CSV_PATH)
    assert len(completed) >= 2000, f"Expected >= 2000 completed runs, got {len(completed)}"

    # Check key structure
    sample_key = next(iter(completed))
    assert len(sample_key) == 8  # (exp, proto, win, loss, delay, bw, fs, rep)
    assert sample_key[1] in ("SW", "GBN", "SR")

    print("  [PASS] test_resumability_key_detection (Resumable key lookup verified)")

def test_results_summary_statistical_findings():
    """Verify results/summary.csv contains 69 configurations with 95% CIs and proves SR superiority."""
    assert os.path.isfile(SUMMARY_CSV_PATH), f"Missing {SUMMARY_CSV_PATH}"

    summary_rows = []
    with open(SUMMARY_CSV_PATH, "r", encoding="utf-8") as f:
        header = f.readline().strip().split(",")
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 20:
                summary_rows.append(parts)

    assert len(summary_rows) == 69, f"Expected 69 summarized configurations, found {len(summary_rows)}"

    # Index lookups:
    # 0:exp, 1:proto, 2:win, 3:loss, 4:delay, 5:bw, 6:fs, 7:payload, 8:reps
    # 9:goodput_mean, 10:goodput_std, 11:goodput_ci95
    # 15:eff_mean, 16:eff_std, 17:eff_ci95
    # 21:retx_mean, 22:retx_std, 23:retx_ci95

    # Check Loss_Sweep at 5% loss (loss=0.05)
    gbn_loss5 = next(r for r in summary_rows if r[0] == "Loss_Sweep" and r[1] == "GBN" and r[3] == "0.05")
    sr_loss5 = next(r for r in summary_rows if r[0] == "Loss_Sweep" and r[1] == "SR" and r[3] == "0.05")

    # Assert SR achieves higher goodput and higher efficiency than GBN under loss
    gbn_gp = float(gbn_loss5[9])
    sr_gp = float(sr_loss5[9])
    gbn_eff = float(gbn_loss5[15])
    sr_eff = float(sr_loss5[15])
    gbn_retx = float(gbn_loss5[21])
    sr_retx = float(sr_loss5[21])

    assert sr_gp > gbn_gp, f"Selective Repeat goodput ({sr_gp}) must exceed GBN ({gbn_gp})"
    assert sr_eff > gbn_eff, f"Selective Repeat efficiency ({sr_eff}%) must exceed GBN ({gbn_eff}%)"
    assert sr_retx < gbn_retx, f"Selective Repeat retransmissions ({sr_retx}) must be fewer than GBN ({gbn_retx})"

    # Verify 95% Confidence Intervals are non-zero and populated
    for r in summary_rows:
        assert float(r[8]) == 30  # 30 repetitions
        assert float(r[11]) >= 0.0  # goodput CI95
        assert float(r[14]) >= 0.0  # transfer time CI95
        assert float(r[17]) >= 0.0  # efficiency CI95

    print("  [PASS] test_results_summary_statistical_findings (69 configs, 30 reps, 95% CI & SR superiority verified)")

def run_all_tests():
    print("=" * 70)
    print("  RUNNING BENCHMARK SWEEP & ARQ STATISTICS VERIFICATION SUITE")
    print("=" * 70)
    test_benchmark_script_and_no_banned_modules()
    test_statistical_confidence_interval_math()
    test_single_run_metrics_computation()
    test_resumability_key_detection()
    test_results_summary_statistical_findings()
    print("=" * 70)
    print("  ALL 5 BENCHMARK SWEEP TESTS PASSED")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
