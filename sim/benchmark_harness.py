#!/usr/bin/env python3
"""
================================================================================
Host-Side Protocol Simulation & Benchmark Harness
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Runs on standard host PC. Evaluates Go-Back-N vs Selective Repeat under varying
channel loss rates (0% - 40%), benchmarks throughput/efficiency, writes CSV
data to /results/benchmark_results.csv, and generates publication charts to
/results/protocol_comparison.png.
"""

import os
import sys
import csv
import random

# Add project root to sys.path so we can import from sbc/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "sbc"))

from go_back_n import GoBackNSimulator
from selective_repeat import SelectiveRepeatSimulator

def run_loss_sweep(num_frames=50, window_size=4, loss_rates=None):
    if loss_rates is None:
        loss_rates = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]

    results = []

    for rate in loss_rates:
        # Determine fixed drop pattern based on rate
        num_drops = int(round(num_frames * rate))
        random.seed(42 + int(rate * 100))  # Consistent seed across both protocols
        dropped_indices = sorted(random.sample(range(1, num_frames), min(num_drops, num_frames - 2)))

        # Simulate GBN
        gbn = GoBackNSimulator(total_frames=num_frames, window_size=window_size, loss_frames=list(dropped_indices))
        res_gbn = gbn.simulate()

        # Simulate SR
        sr = SelectiveRepeatSimulator(total_frames=num_frames, window_size=window_size, loss_frames=list(dropped_indices))
        res_sr = sr.simulate()

        results.append({
            "loss_rate_pct": rate * 100,
            "lost_frames_count": len(dropped_indices),
            "total_frames": num_frames,
            "window_size": window_size,
            "gbn_total_transmissions": res_gbn["total_sent"],
            "gbn_retransmissions": res_gbn["retransmissions"],
            "gbn_efficiency_pct": round(res_gbn["efficiency"], 2),
            "sr_total_transmissions": res_sr["total_sent"],
            "sr_retransmissions": res_sr["retransmissions"],
            "sr_efficiency_pct": round(res_sr["efficiency"], 2),
            "efficiency_gain_pct": round(res_sr["efficiency"] - res_gbn["efficiency"], 2)
        })

    return results

def save_csv(results, csv_path):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    fieldnames = list(results[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"[OK] Benchmark CSV written -> {csv_path}")

def generate_charts(results, chart_path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        loss_rates = [r["loss_rate_pct"] for r in results]
        gbn_eff = [r["gbn_efficiency_pct"] for r in results]
        sr_eff = [r["sr_efficiency_pct"] for r in results]
        gbn_retx = [r["gbn_retransmissions"] for r in results]
        sr_retx = [r["sr_retransmissions"] for r in results]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Chart 1: Protocol Efficiency vs Loss Rate
        ax1.plot(loss_rates, gbn_eff, 'r-o', linewidth=2, label='Go-Back-N (GBN)')
        ax1.plot(loss_rates, sr_eff, 'g-s', linewidth=2, label='Selective Repeat (SR)')
        ax1.set_title('Protocol Efficiency vs. Channel Packet Loss Rate', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Channel Packet Loss Rate (%)', fontsize=11)
        ax1.set_ylabel('Efficiency (%)', fontsize=11)
        ax1.grid(True, linestyle='--', alpha=0.6)
        ax1.legend(loc='lower left')
        ax1.set_ylim(0, 105)

        # Chart 2: Retransmission Overhead
        ax2.bar([x - 0.7 for x in loss_rates], gbn_retx, width=1.4, color='#d9534f', label='GBN Retransmissions')
        ax2.bar([x + 0.7 for x in loss_rates], sr_retx, width=1.4, color='#5cb85c', label='SR Retransmissions')
        ax2.set_title('Retransmissions Incurred vs. Channel Loss Rate', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Channel Packet Loss Rate (%)', fontsize=11)
        ax2.set_ylabel('Number of Retransmissions', fontsize=11)
        ax2.grid(True, linestyle='--', alpha=0.6)
        ax2.legend(loc='upper left')

        plt.tight_layout()
        os.makedirs(os.path.dirname(chart_path), exist_ok=True)
        plt.savefig(chart_path, dpi=300)
        plt.close()
        print(f"[OK] Benchmark chart image generated -> {chart_path}")
    except ImportError:
        print("[WARN] matplotlib not installed; skipping chart generation.")

def main():
    print("=" * 80)
    print("  EXECUTING PROTOCOL BENCHMARK HARNESS (GBN vs SELECTIVE REPEAT)")
    print("=" * 80)
    results = run_loss_sweep(num_frames=50, window_size=4)

    # Print summary table
    print("\n" + "=" * 80)
    print(f"{'Loss Rate':<12} {'GBN Eff.':<12} {'SR Eff.':<12} {'GBN Retx':<12} {'SR Retx':<12} {'Gain':<10}")
    print("-" * 80)
    for r in results:
        print(f"{r['loss_rate_pct']:.1f}%{'':<6} {r['gbn_efficiency_pct']:.1f}%{'':<6} {r['sr_efficiency_pct']:.1f}%{'':<6} {r['gbn_retransmissions']:<12} {r['sr_retransmissions']:<12} +{r['efficiency_gain_pct']:.1f}%")
    print("=" * 80)

    results_dir = os.path.join(PROJECT_ROOT, "results")
    csv_file = os.path.join(results_dir, "benchmark_results.csv")
    img_file = os.path.join(results_dir, "protocol_comparison.png")

    save_csv(results, csv_file)
    generate_charts(results, img_file)

if __name__ == "__main__":
    main()
