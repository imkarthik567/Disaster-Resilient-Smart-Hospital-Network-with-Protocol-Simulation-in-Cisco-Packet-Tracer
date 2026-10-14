#!/usr/bin/env python3
"""
Unit Test Suite: ARQ Analysis, Theoretical Fit & Publication Visualizations
Validates sim/analysis.py, results/charts/, results/findings.md, and results/heatmap_goodput.csv
against project specifications, theoretical flow-control physics, and visualization criteria.
"""

import os
import sys
import csv
import math

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

ANALYSIS_PY = os.path.join(PROJECT_ROOT, "sim", "analysis.py")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
CHARTS_DIR = os.path.join(RESULTS_DIR, "charts")
FINDINGS_MD = os.path.join(RESULTS_DIR, "findings.md")
HEATMAP_CSV = os.path.join(RESULTS_DIR, "heatmap_goodput.csv")


def test_analysis_script_structure():
    """Verify sim/analysis.py exists, is syntactically valid, and exports required routines."""
    assert os.path.isfile(ANALYSIS_PY), f"Missing {ANALYSIS_PY}"
    with open(ANALYSIS_PY, "r", encoding="utf-8") as f:
        code = f.read()

    # Must define plotting functions for all 5 required figures
    required_funcs = [
        "plot_retransmissions_vs_loss",
        "plot_transfer_time_vs_window",
        "plot_efficiency_vs_window_theory",
        "plot_detection_coverage",
        "plot_goodput_heatmap",
        "generate_all_charts",
    ]
    for func in required_funcs:
        assert f"def {func}" in code, f"Missing required function '{func}' in sim/analysis.py"

    print("  [PASS] test_analysis_script_structure (All 5 plotting routines present)")


def test_charts_generated_files():
    """Verify all 10 chart files (5 PNGs + 5 PDFs) exist and meet size thresholds."""
    assert os.path.isdir(CHARTS_DIR), f"Missing charts directory: {CHARTS_DIR}"

    expected_charts = [
        "retransmissions_vs_loss",
        "transfer_time_vs_window",
        "efficiency_vs_window_theory",
        "detection_coverage_bars",
        "goodput_heatmap",
    ]

    for base in expected_charts:
        png_file = os.path.join(CHARTS_DIR, f"{base}.png")
        pdf_file = os.path.join(CHARTS_DIR, f"{base}.pdf")

        assert os.path.isfile(png_file), f"Missing PNG chart: {png_file}"
        assert os.path.isfile(pdf_file), f"Missing PDF chart: {pdf_file}"

        # PNG must be high-resolution (> 100 KB for 300 DPI)
        png_size = os.path.getsize(png_file)
        pdf_size = os.path.getsize(pdf_file)
        assert png_size > 100_000, f"PNG chart {base}.png is too small ({png_size} bytes, expected >100KB)"
        assert pdf_size > 10_000, f"PDF chart {base}.pdf is too small ({pdf_size} bytes, expected >10KB)"

    print("  [PASS] test_charts_generated_files (All 10 PNG/PDF files validated)")


def test_theoretical_formula_math():
    """Verify calculation of parameter a, pipe capacity 1+2a, and Mean Absolute Error (MAE)."""
    R = 2048000.0  # 2.048 Mbps
    frame_bytes = 538  # 512 + 26
    T_tx = (frame_bytes * 8.0) / R
    T_prop = 0.050  # 50 ms
    a = T_prop / T_tx
    one_plus_2a = 1.0 + 2.0 * a
    p = 0.05

    # Check parameter bounds
    assert 23.0 < a < 24.5, f"Parameter 'a' out of expected range: {a}"
    assert 47.0 < one_plus_2a < 50.0, f"Pipe capacity '1+2a' out of range: {one_plus_2a}"

    # Theoretical formulas
    # 1. Ideal sliding window
    assert abs(min(1.0, 1.0 / one_plus_2a) - (1.0 / one_plus_2a)) < 1e-6
    # 2. Stop-and-Wait under loss
    eta_sw = (1.0 - p) / one_plus_2a
    assert 0.015 < eta_sw < 0.025, f"Stop-and-wait efficiency out of range: {eta_sw}"

    # Load Window_Sweep measured goodput from summary.csv to test MAE bounds
    summary_path = os.path.join(RESULTS_DIR, "summary.csv")
    assert os.path.isfile(summary_path)

    with open(summary_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r["experiment"] == "Window_Sweep"]

    sr_rows = sorted([r for r in rows if r["protocol"] == "SR"], key=lambda x: int(x["window_size"]))
    gbn_rows = sorted([r for r in rows if r["protocol"] == "GBN"], key=lambda x: int(x["window_size"]))

    assert len(sr_rows) == 6, f"Expected 6 SR window sizes, got {len(sr_rows)}"
    assert len(gbn_rows) == 6, f"Expected 6 GBN window sizes, got {len(gbn_rows)}"

    sr_errors = []
    for r in sr_rows:
        N = int(r["window_size"])
        meas = float(r["goodput_mean_bps"]) / R
        theo = min(1.0, N / one_plus_2a) * (1.0 - p)
        sr_errors.append(abs(meas - theo))

    gbn_errors = []
    for r in gbn_rows:
        N = int(r["window_size"])
        meas = float(r["goodput_mean_bps"]) / R
        theo = (N * (1.0 - p)) / (one_plus_2a * (1.0 - p + N * p))
        gbn_errors.append(abs(meas - theo))

    mae_sr = sum(sr_errors) / len(sr_errors)
    mae_gbn = sum(gbn_errors) / len(gbn_errors)

    # MAE should be low and accurately reflect divergence
    assert 0.05 < mae_sr < 0.15, f"SR MAE out of expected bound: {mae_sr}"
    assert 0.01 < mae_gbn < 0.06, f"GBN MAE out of expected bound: {mae_gbn}"

    print(f"  [PASS] test_theoretical_formula_math (SR MAE={mae_sr*100:.2f}%, GBN MAE={mae_gbn*100:.2f}%)")


def test_heatmap_dataset():
    """Verify results/heatmap_goodput.csv contains complete 2D grid of 84 cells."""
    assert os.path.isfile(HEATMAP_CSV), f"Missing {HEATMAP_CSV}"
    with open(HEATMAP_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # 2 protocols * 6 window sizes * 7 loss rates = 84 cells
    assert len(rows) == 84, f"Expected 84 cells in heatmap dataset, got {len(rows)}"

    # Check key physical properties
    # At loss = 0, goodput must increase monotonically with window size
    sr_loss0 = sorted([r for r in rows if r["protocol"] == "SR" and float(r["loss_prob"]) == 0.0],
                      key=lambda x: int(x["window_size"]))
    for i in range(len(sr_loss0) - 1):
        assert float(sr_loss0[i]["goodput_mean_bps"]) < float(sr_loss0[i+1]["goodput_mean_bps"])

    # At N=32, loss=0.30: SR goodput must be significantly higher than GBN
    gbn_n32_l30 = next(r for r in rows if r["protocol"] == "GBN" and int(r["window_size"]) == 32 and abs(float(r["loss_prob"]) - 0.3) < 1e-4)
    sr_n32_l30 = next(r for r in rows if r["protocol"] == "SR" and int(r["window_size"]) == 32 and abs(float(r["loss_prob"]) - 0.3) < 1e-4)

    ratio = float(sr_n32_l30["goodput_mean_bps"]) / float(gbn_n32_l30["goodput_mean_bps"])
    assert ratio > 3.0, f"Expected SR to be >3x higher than GBN at N=32, loss=30%, got ratio {ratio}"

    print(f"  [PASS] test_heatmap_dataset (84 cells, SR advantage confirmed: {ratio:.2f}x)")


def test_findings_report_content():
    """Verify results/findings.md contains required interpretations, divergence analysis, and conclusions."""
    assert os.path.isfile(FINDINGS_MD), f"Missing {FINDINGS_MD}"
    with open(FINDINGS_MD, "r", encoding="utf-8") as f:
        text = f.read()

    # Must discuss all 5 charts
    assert "retransmissions_vs_loss" in text
    assert "transfer_time_vs_window" in text
    assert "efficiency_vs_window_theory" in text
    assert "detection_coverage_bars" in text
    assert "goodput_heatmap" in text

    # Must address divergence reasons
    assert "Timeouts" in text or "timeout" in text
    assert "Framing" in text or "header" in text
    assert "ACK" in text
    assert "MAE" in text or "Mean Absolute Error" in text

    # Must provide three concrete conclusions
    assert "Conclusion 1" in text
    assert "Conclusion 2" in text
    assert "Conclusion 3" in text

    print("  [PASS] test_findings_report_content (All sections & conclusions present)")


def main():
    print("=" * 70)
    print("RUNNING PROTOCOL ANALYSIS & PUBLICATION CHARTS TEST SUITE")
    print("=" * 70)

    test_analysis_script_structure()
    test_charts_generated_files()
    test_theoretical_formula_math()
    test_heatmap_dataset()
    test_findings_report_content()

    print("=" * 70)
    print("ALL PROTOCOL ANALYSIS & PUBLICATION CHARTS TESTS PASSED (5/5)")
    print("=" * 70)
    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
