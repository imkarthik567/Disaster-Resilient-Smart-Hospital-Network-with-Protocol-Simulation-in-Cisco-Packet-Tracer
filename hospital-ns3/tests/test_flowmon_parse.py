"""
================================================================================
tests/test_flowmon_parse.py - Unit Test Suite for FlowMonitor XML Parsing & Stats
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
SCOPE, VIT Vellore
================================================================================
Tests:
  1. Parsing structure and column schema of FlowMonitor XML
  2. Traffic classification (ICU, IMAGING, VOICE, ATTACK)
  3. Correct calculation of throughput, delay, jitter, and packet loss
  4. Statistical module functions (Student t CI, Welch's t-test, Cohen's d)
================================================================================
"""

import os
import sys
import pytest
import numpy as np

# Ensure analysis module is importable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "analysis"))

from flowmon_parse import parse_flowmon_xml, classify_flow
from stats import calculate_summary_statistics, welch_t_test, cohens_d


@pytest.fixture
def sample_xml_path():
    return os.path.join(CURRENT_DIR, "sample_flowmon.xml")


def test_xml_parsing_structure(sample_xml_path):
    assert os.path.exists(sample_xml_path), "Sample XML file must exist"
    df = parse_flowmon_xml(sample_xml_path, exp_id="TEST-01", seed=42)

    assert len(df) == 4, "Sample XML contains exactly 4 flows"
    expected_columns = [
        "experiment", "seed", "flow_id", "source_ip", "source_port",
        "dest_ip", "dest_port", "protocol", "traffic_class",
        "tx_packets", "rx_packets", "lost_packets", "packet_loss_ratio",
        "tx_bytes", "rx_bytes", "throughput_kbps", "goodput_kbps",
        "mean_delay_ms", "p95_delay_ms", "mean_jitter_ms"
    ]
    for col in expected_columns:
        assert col in df.columns, f"Expected column {col} in parsed DataFrame"


def test_traffic_classification(sample_xml_path):
    df = parse_flowmon_xml(sample_xml_path, exp_id="TEST-01", seed=42)
    classes = dict(zip(df["flow_id"], df["traffic_class"]))

    # Flow 1: 172.16.7.130 (ICU) -> 172.16.7.10, port 5001 -> ICU
    assert classes[1] == "ICU", f"Flow 1 expected ICU, got {classes[1]}"

    # Flow 2: 172.16.8.45 (Clinic Imaging) -> 172.16.7.10, port 8080 (TCP) -> IMAGING
    assert classes[2] == "IMAGING", f"Flow 2 expected IMAGING, got {classes[2]}"

    # Flow 3: 172.16.6.10 (Voice) -> 172.16.7.228, port 5060 -> VOICE
    assert classes[3] == "VOICE", f"Flow 3 expected VOICE, got {classes[3]}"

    # Flow 4: 172.16.0.25 (Guest) -> 172.16.7.130 (ICU), port 4444 -> ATTACK
    assert classes[4] == "ATTACK", f"Flow 4 expected ATTACK, got {classes[4]}"


def test_metric_calculations(sample_xml_path):
    df = parse_flowmon_xml(sample_xml_path, exp_id="TEST-01", seed=42)
    f1 = df[df["flow_id"] == 1].iloc[0]

    # Flow 1: 100 tx, 100 rx, 0 lost
    assert f1["tx_packets"] == 100
    assert f1["rx_packets"] == 100
    assert f1["lost_packets"] == 0
    assert f1["packet_loss_ratio"] == 0.0

    # Delay: delaySum = 190000000 ns / 100 pkts / 1e6 = 1.9 ms
    assert np.isclose(f1["mean_delay_ms"], 1.9, atol=0.01)

    # Flow 3: 500 tx, 475 rx, 25 lost -> loss ratio = 25 / 500 = 0.05 (5%)
    f3 = df[df["flow_id"] == 3].iloc[0]
    assert f3["lost_packets"] == 25
    assert np.isclose(f3["packet_loss_ratio"], 0.05, atol=0.001)


def test_stats_module():
    # 1. Summary Statistics
    sample_data = [10.0, 12.0, 11.0, 13.0, 12.5, 11.5]
    res = calculate_summary_statistics(sample_data)
    assert res["n"] == 6
    assert np.isclose(res["mean"], 11.6667, atol=0.01)
    assert res["ci_low"] < res["mean"] < res["ci_high"]

    # 2. Welch's t-test
    group_a = [10.0, 10.5, 11.0, 10.2, 10.8]
    group_b = [25.0, 26.0, 24.5, 25.5, 26.5]
    t_res = welch_t_test(group_a, group_b)
    assert t_res["significant_alpha_0_05"] is True
    assert t_res["p_value"] < 0.001

    # 3. Cohen's d
    d_res = cohens_d(group_a, group_b)
    assert abs(d_res["cohens_d"]) > 5.0 # Massive separation
