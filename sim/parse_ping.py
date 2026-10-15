#!/usr/bin/env python3
"""
================================================================================
Cisco Packet Tracer / Windows / IOS Raw Ping Parser & Outage Estimator
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
SCOPE, VIT Vellore
================================================================================
Parses raw pasted ping terminal outputs into:
  - Total sent, received, and lost echo counts
  - Packet loss percentage
  - Maximum consecutive packet loss run (outage window)
  - Estimated network convergence / outage duration (lost * interval)
  - Round-trip latency statistics (min, avg, max)
  - Sequence bitmask (1 = reply, 0 = loss/timeout)

Supports:
  1. Windows / Packet Tracer PC terminal format ("Reply from ...", "Request timed out.")
  2. Cisco IOS ping format ("!!!!.....!!!!!!")
  3. Linux / Unix format ("64 bytes from ...", "Request timeout")
  4. Raw comma/space-delimited binary bitstreams ("1, 1, 0, 0, 1")
================================================================================
"""

import os
import sys
import re
import json
import argparse
from typing import Dict, Any, List, Optional, Tuple


def parse_raw_ping_text(raw_text: str, ping_interval_s: float = 1.0) -> Dict[str, Any]:
    """
    Parses arbitrary ping console logs and extracts quantitative failover metrics.
    """
    lines = [line.strip() for line in raw_text.strip().splitlines() if line.strip()]
    
    # 1. Check for Cisco IOS style (e.g. !!!!!....!!!!!)
    ios_pattern = re.compile(r"^[!\.UQI&?]+$")
    ios_matches = [line for line in lines if ios_pattern.match(line)]
    if ios_matches:
        full_chars = "".join(ios_matches)
        sequence = [1 if c == "!" else 0 for c in full_chars]
        total_sent = len(sequence)
        received = sum(sequence)
        lost = total_sent - received
        latencies = []
        # Check if min/avg/max line exists
        for line in lines:
            m = re.search(r"min/avg/max\s*=\s*(\d+)/(\d+)/(\d+)", line)
            if m:
                latencies = [float(m.group(1)), float(m.group(2)), float(m.group(3))]
                break

        return _build_result(sequence, total_sent, received, lost, ping_interval_s, latencies)

    # 2. Check for Windows / Packet Tracer / Linux line-by-line
    sequence = []
    latencies = []
    
    for line in lines:
        lower = line.lower()
        # Windows Reply
        if "reply from" in lower:
            sequence.append(1)
            time_m = re.search(r"time[<=](\d+(?:\.\d+)?)ms", lower)
            if time_m:
                latencies.append(float(time_m.group(1)))
        # Linux reply
        elif "bytes from" in lower and ("icmp_seq" in lower or "time=" in lower):
            sequence.append(1)
            time_m = re.search(r"time=(\d+(?:\.\d+)?)", lower)
            if time_m:
                latencies.append(float(time_m.group(1)))
        # Timeouts & drops
        elif "request timed out" in lower or "destination host unreachable" in lower or "packet filtered" in lower or "request timeout" in lower:
            sequence.append(0)
        elif "100% packet loss" in lower:
            pass # Summary line
        # Binary stream line (e.g. "1, 1, 0, 0, 1")
        elif re.match(r"^[01\s,;]+$", line):
            bits = [int(b) for b in re.findall(r"[01]", line)]
            if bits:
                sequence.extend(bits)

    if not sequence:
        # Fallback check summary statistics if no individual lines
        sent_m = re.search(r"Sent\s*=\s*(\d+),\s*Received\s*=\s*(\d+),\s*Lost\s*=\s*(\d+)", raw_text, re.IGNORECASE)
        if sent_m:
            total_sent = int(sent_m.group(1))
            received = int(sent_m.group(2))
            lost = int(sent_m.group(3))
            sequence = [1] * received + [0] * lost
            return _build_result(sequence, total_sent, received, lost, ping_interval_s, latencies)
        raise ValueError("Could not parse any valid ICMP echo responses or timeouts from provided input.")

    total_sent = len(sequence)
    received = sum(sequence)
    lost = total_sent - received

    return _build_result(sequence, total_sent, received, lost, ping_interval_s, latencies)


def _build_result(sequence: List[int], total_sent: int, received: int, lost: int,
                  interval_s: float, latencies: List[float]) -> Dict[str, Any]:
    loss_pct = (lost / total_sent) * 100.0 if total_sent > 0 else 0.0
    
    # Calculate longest contiguous drop run
    max_consecutive_drops = 0
    current_run = 0
    for s in sequence:
        if s == 0:
            current_run += 1
            if current_run > max_consecutive_drops:
                max_consecutive_drops = current_run
        else:
            current_run = 0

    # Estimated outage based on max contiguous drop window
    estimated_outage_s = max_consecutive_drops * interval_s
    
    min_lat = min(latencies) if latencies else None
    max_lat = max(latencies) if latencies else None
    avg_lat = sum(latencies) / len(latencies) if latencies else None

    # Clinical SLA rating
    if estimated_outage_s <= 3.0:
        sla_rating = "ACCEPTABLE (Vitals SLA Compliant)"
    elif estimated_outage_s <= 15.0:
        sla_rating = "DEGRADED (EHR Compliant, Telemetry Degraded)"
    else:
        sla_rating = "UNACCEPTABLE (Clinical Outage Exceeded)"

    return {
        "total_sent": total_sent,
        "received": received,
        "lost": lost,
        "loss_pct": round(loss_pct, 2),
        "max_consecutive_drops": max_consecutive_drops,
        "ping_interval_s": interval_s,
        "estimated_convergence_outage_s": round(estimated_outage_s, 2),
        "rtt_min_ms": round(min_lat, 2) if min_lat is not None else None,
        "rtt_avg_ms": round(avg_lat, 2) if avg_lat is not None else None,
        "rtt_max_ms": round(max_lat, 2) if max_lat is not None else None,
        "sla_rating": sla_rating,
        "sequence_bitmask": "".join(str(x) for x in sequence),
    }


def format_report(result: Dict[str, Any], scenario: Optional[str] = None, config: Optional[str] = None) -> str:
    lines = []
    lines.append("=" * 72)
    lines.append("  ICMP PING FAILOVER ANALYSIS & CONVERGENCE REPORT")
    lines.append("=" * 72)
    if scenario:
        lines.append(f"  Scenario:               {scenario}")
    if config:
        lines.append(f"  Configuration:          {config}")
    lines.append(f"  Packets Transmitted:    {result['total_sent']}")
    lines.append(f"  Packets Received:       {result['received']}")
    lines.append(f"  Packets Dropped:        {result['lost']} ({result['loss_pct']}%)")
    lines.append(f"  Max Consecutive Loss:   {result['max_consecutive_drops']} packets")
    lines.append(f"  Ping Sample Interval:   {result['ping_interval_s']:.2f} seconds")
    lines.append(f"  Estimated Outage:       {result['estimated_convergence_outage_s']:.2f} seconds")
    if result["rtt_avg_ms"] is not None:
        lines.append(f"  RTT Latency (Min/Avg/Max): {result['rtt_min_ms']} / {result['rtt_avg_ms']} / {result['rtt_max_ms']} ms")
    lines.append(f"  Clinical SLA Rating:    {result['sla_rating']}")
    lines.append(f"  Sequence Bitmask:       {result['sequence_bitmask']}")
    lines.append("=" * 72)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Parse raw ping logs to quantify packet loss and convergence time.")
    parser.add_argument("--file", "-f", help="Path to text file containing raw ping output")
    parser.add_argument("--interval", "-i", type=float, default=1.0, help="Ping interval in seconds (default 1.0s)")
    parser.add_argument("--scenario", "-s", help="Optional scenario name/ID (e.g. SC-01 Primary WAN Cut)")
    parser.add_argument("--config", "-c", help="Optional protocol configuration (e.g. Tuned OSPF)")
    parser.add_argument("--json", "-j", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    if args.file:
        if not os.path.exists(args.file):
            print(f"[ERROR] File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            raw_text = f.read()
    else:
        print("[INFO] Paste ping output below, then press Enter and Ctrl+D (or Ctrl+Z on Windows):")
        try:
            raw_text = sys.stdin.read()
        except KeyboardInterrupt:
            sys.exit(0)

    if not raw_text.strip():
        print("[ERROR] No ping output received.", file=sys.stderr)
        sys.exit(1)

    try:
        res = parse_raw_ping_text(raw_text, ping_interval_s=args.interval)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(format_report(res, scenario=args.scenario, config=args.config))
    except Exception as e:
        print(f"[ERROR] Failed to parse ping output: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
