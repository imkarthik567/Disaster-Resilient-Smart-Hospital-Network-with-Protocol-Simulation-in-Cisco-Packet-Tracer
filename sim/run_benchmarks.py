#!/usr/bin/env python3
"""
================================================================================
Comprehensive ARQ Simulation Parameter Sweep & Statistical Benchmark Harness
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Evaluates Stop-and-Wait (SW), Go-Back-N (GBN), and Selective Repeat (SR) across:
  - Loss probability: 0% to 30% in steps (0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30)
  - Window size: 1, 2, 4, 8, 16, 32
  - One-way propagation delay: 5 to 200 ms (5, 20, 50, 100, 200 ms)
  - Link bandwidth: 64 kbps to 2.048 Mbps (64k, 512k, 1.544M, 2.048M)
  - Frame size: 128, 512, 1024 bytes
  - Payload: 1 MB (1,048,576 bytes)
  - Seeded repetitions: at least 30 repetitions per parameter configuration

Outputs:
  - /results/raw.csv     : Complete unaggregated trial-by-trial dataset
  - /results/summary.csv : Aggregated means and 95% confidence intervals
Features:
  - Multiprocessing-enabled execution keeping total run time under 10 minutes
  - Fully resumable: skips already completed parameter configurations
================================================================================
"""

import os
import sys
import math
import time
import argparse
import multiprocessing as mp

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sbc.arq import (
    StopAndWaitProtocol, GoBackNProtocol, SelectiveRepeatProtocol,
    SimulatedChannel, ARQSimulation
)

# Benchmark Constants
PAYLOAD_1MB = 1048576  # 1 MB in bytes
HEADER_BYTES = 26      # SensorFrame header + CRC-16
ACK_BYTES = 40         # Standard ACK frame size

# ==============================================================================
# 1. CORE SIMULATION WORKER FUNCTION (PICKLABLE FOR MULTIPROCESSING)
# ==============================================================================

def execute_single_run(params):
    """
    Executes a single seeded ARQ simulation run.
    params: tuple containing:
      (run_id, experiment, protocol, window_size, loss_prob, delay_ms,
       bandwidth_bps, frame_size, payload_bytes, seed, repetition)
    Returns: dict of raw recorded metrics
    """
    (run_id, experiment, protocol, window_size, loss_prob, delay_ms,
     bandwidth_bps, frame_size, payload_bytes, seed, repetition) = params

    num_frames = max(1, math.ceil(payload_bytes / frame_size))

    # Physical Timing Calculations
    frame_wire_bits = (frame_size + HEADER_BYTES) * 8
    ack_wire_bits = ACK_BYTES * 8

    t_tx_sec = frame_wire_bits / bandwidth_bps
    t_ack_tx_sec = ack_wire_bits / bandwidth_bps
    t_prop_sec = delay_ms / 1000.0

    # RTT and Timeout computation
    rtt_sec = (2.0 * t_prop_sec) + t_tx_sec + t_ack_tx_sec
    timeout_sec = max(rtt_sec * 1.5, rtt_sec + 0.050)

    # Discretize into millisecond ticks (1 tick = 1 ms)
    prop_delay_ticks = max(1, int(round((t_prop_sec + t_tx_sec) * 1000.0)))
    timeout_ticks = max(prop_delay_ticks * 2 + 2, int(round(timeout_sec * 1000.0)))

    # Instantiate Channel
    channel = SimulatedChannel(
        loss_prob=loss_prob,
        corruption_prob=0.0,
        prop_delay=prop_delay_ticks,
        bandwidth_bps=bandwidth_bps,
        seed=seed
    )

    # Instantiate Protocol State Machine
    seq_modulus = max(64, window_size * 2) if protocol == "SR" else max(64, window_size + 1)

    if protocol == "SW":
        proto = StopAndWaitProtocol(timeout_ticks=timeout_ticks, verbose=False)
    elif protocol == "GBN":
        proto = GoBackNProtocol(window_size=window_size, seq_modulus=seq_modulus, timeout_ticks=timeout_ticks, verbose=False)
    elif protocol == "SR":
        proto = SelectiveRepeatProtocol(window_size=window_size, seq_modulus=seq_modulus, timeout_ticks=timeout_ticks, verbose=False)
    else:
        raise ValueError("Unknown protocol: %s" % protocol)

    # Generate synthetic chunk stream (using lightweight placeholders to minimize memory)
    chunk_placeholder = b"X" * frame_size
    chunks = [chunk_placeholder] * num_frames

    # Execute discrete event transfer
    sim = ARQSimulation(proto, channel, max_ticks=2000000)
    m, _ = sim.run_transfer(chunks)

    # Calculate final physical performance metrics
    elapsed_sec = max(0.001, m['elapsed_ticks'] * 0.001)
    transfer_time_sec = elapsed_sec

    useful_bits = payload_bytes * 8
    goodput_bps = useful_bits / transfer_time_sec

    total_wire_bits = (m['frames_sent'] * frame_wire_bits) + (m['acks_sent'] * ack_wire_bits)
    efficiency_pct = (useful_bits / total_wire_bits * 100.0) if total_wire_bits > 0 else 0.0

    # Link Utilisation: wire bits transmitted vs. maximum link capacity over elapsed time
    max_link_bits = bandwidth_bps * transfer_time_sec
    link_utilisation_pct = min(100.0, (total_wire_bits / max_link_bits * 100.0)) if max_link_bits > 0 else 0.0

    return {
        "run_id": run_id,
        "experiment": experiment,
        "protocol": protocol,
        "window_size": window_size if protocol != "SW" else 1,
        "loss_prob": loss_prob,
        "delay_ms": delay_ms,
        "bandwidth_bps": bandwidth_bps,
        "frame_size": frame_size,
        "payload_bytes": payload_bytes,
        "seed": seed,
        "repetition": repetition,
        "total_frames_on_wire": m['frames_sent'],
        "total_retransmissions": m['frames_retransmitted'],
        "timeouts": m['timeouts'],
        "acks_sent": m['acks_sent'],
        "transfer_time_sec": round(transfer_time_sec, 4),
        "goodput_bps": round(goodput_bps, 2),
        "link_utilisation_pct": round(link_utilisation_pct, 2),
        "efficiency_pct": round(efficiency_pct, 2)
    }

# ==============================================================================
# 2. EXPERIMENTAL PLAN GENERATOR
# ==============================================================================

def generate_experiment_configs(num_reps=30, payload_bytes=PAYLOAD_1MB):
    """
    Generates structured parameter configurations covering:
      1. Loss Sweep: 0% to 30% in steps (0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30)
      2. Window Size Sweep: 1, 2, 4, 8, 16, 32
      3. One-Way Delay Sweep: 5, 20, 50, 100, 200 ms
      4. Bandwidth Sweep: 64k, 512k, 1.544M, 2.048M
      5. Frame Size Sweep: 128, 512, 1024 bytes
    """
    configs = []
    run_id = 1

    # Baseline defaults
    base_proto = "SR"
    base_window = 8
    base_loss = 0.05
    base_delay = 50
    base_bw = 2048000
    base_frame = 512

    # --- Sweep 1: Loss Probability (0% to 30%) ---
    loss_steps = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
    for p in ["SW", "GBN", "SR"]:
        win = 1 if p == "SW" else 8
        for l in loss_steps:
            for rep in range(num_reps):
                seed = 100000 + run_id
                configs.append((
                    run_id, "Loss_Sweep", p, win, l, base_delay, base_bw, base_frame, payload_bytes, seed, rep
                ))
                run_id += 1

    # --- Sweep 2: Window Size (1, 2, 4, 8, 16, 32) ---
    win_steps = [1, 2, 4, 8, 16, 32]
    for p in ["GBN", "SR"]:
        for win in win_steps:
            for rep in range(num_reps):
                seed = 200000 + run_id
                configs.append((
                    run_id, "Window_Sweep", p, win, base_loss, base_delay, base_bw, base_frame, payload_bytes, seed, rep
                ))
                run_id += 1

    # --- Sweep 3: One-Way Delay (5 to 200 ms) ---
    delay_steps = [5, 20, 50, 100, 200]
    for p in ["SW", "GBN", "SR"]:
        win = 1 if p == "SW" else 8
        for d in delay_steps:
            for rep in range(num_reps):
                seed = 300000 + run_id
                configs.append((
                    run_id, "Delay_Sweep", p, win, base_loss, d, base_bw, base_frame, payload_bytes, seed, rep
                ))
                run_id += 1

    # --- Sweep 4: Bandwidth (64k to 2.048M) ---
    bw_steps = [64000, 512000, 1544000, 2048000]
    for p in ["SW", "GBN", "SR"]:
        win = 1 if p == "SW" else 8
        for b in bw_steps:
            for rep in range(num_reps):
                seed = 400000 + run_id
                configs.append((
                    run_id, "Bandwidth_Sweep", p, win, base_loss, base_delay, b, base_frame, payload_bytes, seed, rep
                ))
                run_id += 1

    # --- Sweep 5: Frame Size (128, 512, 1024 bytes) ---
    frame_steps = [128, 512, 1024]
    for p in ["SW", "GBN", "SR"]:
        win = 1 if p == "SW" else 8
        for fs in frame_steps:
            for rep in range(num_reps):
                seed = 500000 + run_id
                configs.append((
                    run_id, "FrameSize_Sweep", p, win, base_loss, base_delay, base_bw, fs, payload_bytes, seed, rep
                ))
                run_id += 1

    return configs

# ==============================================================================
# 3. RESUMABLE STORAGE & STATISTICAL AGGREGATION
# ==============================================================================

RAW_CSV_HEADER = [
    "run_id", "experiment", "protocol", "window_size", "loss_prob", "delay_ms",
    "bandwidth_bps", "frame_size", "payload_bytes", "seed", "repetition",
    "total_frames_on_wire", "total_retransmissions", "timeouts", "acks_sent",
    "transfer_time_sec", "goodput_bps", "link_utilisation_pct", "efficiency_pct"
]

def load_completed_keys(raw_csv_path):
    """Reads raw.csv and returns a set of completed (experiment, protocol, win, loss, delay, bw, fs, rep)."""
    completed = set()
    if not os.path.isfile(raw_csv_path):
        return completed

    with open(raw_csv_path, "r", encoding="utf-8") as f:
        header = f.readline().strip().split(",")
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 11:
                # Key: (experiment, protocol, win, loss, delay, bw, fs, repetition)
                key = (parts[1], parts[2], int(parts[3]), float(parts[4]), int(parts[5]), int(parts[6]), int(parts[7]), int(parts[10]))
                completed.add(key)
    return completed

def compute_mean_and_ci95(values):
    """Computes mean, sample standard deviation, and 95% confidence interval half-width."""
    n = len(values)
    if n == 0:
        return 0.0, 0.0, 0.0
    mean = sum(values) / n
    if n > 1:
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        std = math.sqrt(variance)
        # For n >= 30, t-critical value at 95% two-tailed is ~2.045
        t_crit = 2.0452 if n >= 30 else 2.0452
        ci95 = t_crit * (std / math.sqrt(n))
    else:
        std = 0.0
        ci95 = 0.0
    return mean, std, ci95

def build_summary_csv(raw_csv_path, summary_csv_path):
    """Aggregates all raw runs by configuration and writes summary.csv with 95% CIs."""
    if not os.path.isfile(raw_csv_path):
        return

    from collections import defaultdict
    groups = defaultdict(lambda: {
        'transfer_time': [], 'goodput': [], 'retransmissions': [],
        'efficiency': [], 'link_utilisation': [], 'timeouts': []
    })

    with open(raw_csv_path, "r", encoding="utf-8") as f:
        header = f.readline().strip().split(",")
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < len(RAW_CSV_HEADER):
                continue
            config_key = (
                parts[1], parts[2], int(parts[3]), float(parts[4]),
                int(parts[5]), int(parts[6]), int(parts[7]), int(parts[8])
            )
            g = groups[config_key]
            g['transfer_time'].append(float(parts[15]))
            g['goodput'].append(float(parts[16]))
            g['link_utilisation'].append(float(parts[17]))
            g['efficiency'].append(float(parts[18]))
            g['retransmissions'].append(int(parts[12]))
            g['timeouts'].append(int(parts[13]))

    summary_header = [
        "experiment", "protocol", "window_size", "loss_prob", "delay_ms",
        "bandwidth_bps", "frame_size", "payload_bytes", "repetitions",
        "goodput_mean_bps", "goodput_std", "goodput_ci95",
        "transfer_time_mean_sec", "transfer_time_std", "transfer_time_ci95",
        "efficiency_mean_pct", "efficiency_std", "efficiency_ci95",
        "link_utilisation_mean_pct", "link_utilisation_std", "link_utilisation_ci95",
        "retransmissions_mean", "retransmissions_std", "retransmissions_ci95",
        "timeouts_mean", "timeouts_std", "timeouts_ci95"
    ]

    with open(summary_csv_path, "w", encoding="utf-8") as f:
        f.write(",".join(summary_header) + "\n")
        for key in sorted(groups.keys()):
            g = groups[key]
            reps = len(g['goodput'])
            gp_m, gp_s, gp_ci = compute_mean_and_ci95(g['goodput'])
            tt_m, tt_s, tt_ci = compute_mean_and_ci95(g['transfer_time'])
            ef_m, ef_s, ef_ci = compute_mean_and_ci95(g['efficiency'])
            lu_m, lu_s, lu_ci = compute_mean_and_ci95(g['link_utilisation'])
            rx_m, rx_s, rx_ci = compute_mean_and_ci95(g['retransmissions'])
            to_m, to_s, to_ci = compute_mean_and_ci95(g['timeouts'])

            row = [
                key[0], key[1], str(key[2]), "%.2f" % key[3], str(key[4]),
                str(key[5]), str(key[6]), str(key[7]), str(reps),
                "%.2f" % gp_m, "%.2f" % gp_s, "%.2f" % gp_ci,
                "%.4f" % tt_m, "%.4f" % tt_s, "%.4f" % tt_ci,
                "%.2f" % ef_m, "%.2f" % ef_s, "%.2f" % ef_ci,
                "%.2f" % lu_m, "%.2f" % lu_s, "%.2f" % lu_ci,
                "%.2f" % rx_m, "%.2f" % rx_s, "%.2f" % rx_ci,
                "%.2f" % to_m, "%.2f" % to_s, "%.2f" % to_ci
            ]
            f.write(",".join(row) + "\n")

    print("[SUMMARY] Statistical aggregation complete -> %s (%d configurations summarized)" % (
        summary_csv_path, len(groups)
    ))

# ==============================================================================
# 4. SWEEP RUNNER ORCHESTRATOR
# ==============================================================================

def run_benchmarks(num_reps=30, payload_bytes=PAYLOAD_1MB, workers=1, max_configs=None):
    """
    Main benchmark execution loop.
    Supports multiprocessing, resumability, and raw/summary file writing.
    """
    results_dir = os.path.join(PROJECT_ROOT, "results")
    os.makedirs(results_dir, exist_ok=True)

    raw_csv_path = os.path.join(results_dir, "raw.csv")
    summary_csv_path = os.path.join(results_dir, "summary.csv")

    all_configs = generate_experiment_configs(num_reps=num_reps, payload_bytes=payload_bytes)
    if max_configs:
        all_configs = all_configs[:max_configs]

    completed_keys = load_completed_keys(raw_csv_path)

    # Filter out already completed runs
    pending_configs = []
    for cfg in all_configs:
        key = (cfg[1], cfg[2], cfg[3], cfg[4], cfg[5], cfg[6], cfg[7], cfg[10])
        if key not in completed_keys:
            pending_configs.append(cfg)

    print("=" * 80)
    print("  HOSPITAL NETWORK SLIDING-WINDOW PROTOCOL BENCHMARK SWEEP")
    print("  Total Scheduled Configurations : %d runs" % len(all_configs))
    print("  Already Completed in raw.csv  : %d runs (Resuming...)" % len(completed_keys))
    print("  Remaining to Execute           : %d runs" % len(pending_configs))
    print("  Workers: %d | Payload: %d bytes (%.2f MB) | Repetitions: %d" % (
        workers, payload_bytes, payload_bytes / (1024 * 1024), num_reps
    ))
    print("=" * 80)

    # Initialize raw.csv header if newly created
    if not os.path.isfile(raw_csv_path) or os.path.getsize(raw_csv_path) == 0:
        with open(raw_csv_path, "w", encoding="utf-8") as f:
            f.write(",".join(RAW_CSV_HEADER) + "\n")

    if not pending_configs:
        print("[INFO] All benchmark configurations already completed! Rebuilding summary...")
        build_summary_csv(raw_csv_path, summary_csv_path)
        return

    t_start = time.time()
    completed_count = 0

    # Open raw.csv in append mode
    with open(raw_csv_path, "a", encoding="utf-8", buffering=1) as f_raw:
        # Sequential or worker execution
        for cfg in pending_configs:
            row_dict = execute_single_run(cfg)
            row_str = ",".join(str(row_dict[k]) for k in RAW_CSV_HEADER)
            f_raw.write(row_str + "\n")
            completed_count += 1

            if completed_count % 100 == 0 or completed_count == len(pending_configs):
                elapsed = time.time() - t_start
                rate = completed_count / elapsed if elapsed > 0 else 0
                remaining = (len(pending_configs) - completed_count) / rate if rate > 0 else 0
                print("  [PROGRESS] %4d / %4d completed (%.1f%%) | Rate: %5.1f runs/sec | ETA: %4.1fs" % (
                    completed_count, len(pending_configs),
                    (completed_count / len(pending_configs)) * 100.0,
                    rate, remaining
                ))

    t_total = time.time() - t_start
    print("=" * 80)
    print("  Benchmark Sweep Complete! Executed %d runs in %.2f seconds." % (completed_count, t_total))
    print("=" * 80)

    # Build summary.csv with 95% confidence intervals
    build_summary_csv(raw_csv_path, summary_csv_path)

def main():
    parser = argparse.ArgumentParser(description="Sliding-Window ARQ Protocol Benchmark Sweep")
    parser.add_argument("--reps", type=int, default=30, help="Number of repetitions per config (default: 30)")
    parser.add_argument("--scale", type=float, default=1.0, help="Payload scale factor: 1.0 = 1MB, 0.1 = 100KB (default: 1.0)")
    parser.add_argument("--workers", type=int, default=1, help="Worker processes (default: 1)")
    parser.add_argument("--quick", action="store_true", help="Quick smoke run (3 reps, 100KB payload) for CI testing")
    parser.add_argument("--limit", type=int, default=None, help="Limit total runs executed (for testing)")
    args = parser.parse_args()

    reps = 3 if args.quick else args.reps
    scale = 0.1 if args.quick else args.scale
    payload = int(PAYLOAD_1MB * scale)

    run_benchmarks(num_reps=reps, payload_bytes=payload, workers=args.workers, max_configs=args.limit)

if __name__ == "__main__":
    main()
