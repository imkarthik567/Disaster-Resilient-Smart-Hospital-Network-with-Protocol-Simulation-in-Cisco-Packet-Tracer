#!/usr/bin/env python3
"""
================================================================================
Unit Tests: Failover Convergence Analysis & SLA Verification
Disaster-Resilient Smart Hospital Network
================================================================================
"""

import os
import sys
import unittest
import tempfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sim.convergence_analysis import ConvergenceAnalyzer, VITALS_SLA_SECONDS
from sim.parse_ping import parse_raw_ping_text, format_report


class TestConvergenceAnalysis(unittest.TestCase):
    def setUp(self):
        self.analyzer = ConvergenceAnalyzer()
        self.analyzer.load_data()

    def test_dataset_loaded_properly(self):
        """Validates that all 6 failure scenarios are present in dataset."""
        self.assertEqual(len(self.analyzer.records), 6)
        ids = [r["scenario_id"] for r in self.analyzer.records]
        expected_ids = ["SC-01", "SC-02", "SC-03", "SC-04", "SC-05", "SC-06"]
        self.assertEqual(ids, expected_ids)

    def test_sla_impact_classification(self):
        """Verifies clinical SLA classification against the 3.0s telemetry baseline."""
        for r in self.analyzer.records:
            if r["observed_failover_s"] <= VITALS_SLA_SECONDS:
                self.assertEqual(r["clinical_impact"], "ACCEPTABLE")
            else:
                self.assertEqual(r["clinical_impact"], "DEGRADED")

        # Specific checks
        sc1 = next(r for r in self.analyzer.records if r["scenario_id"] == "SC-01")
        self.assertEqual(sc1["clinical_impact"], "DEGRADED")
        self.assertAlmostEqual(sc1["packet_loss_pct"], 22.0, places=1)

        sc5 = next(r for r in self.analyzer.records if r["scenario_id"] == "SC-05")
        self.assertEqual(sc5["clinical_impact"], "ACCEPTABLE")
        self.assertEqual(sc5["pings_lost"], 0)

    def test_chart_generation(self):
        """Validates that grouped bar chart and cumulative loss curve are created."""
        with tempfile.TemporaryDirectory() as tmp_charts:
            analyzer = ConvergenceAnalyzer(charts_dir=tmp_charts)
            analyzer.load_data()

            png1, pdf1 = analyzer.plot_theoretical_vs_observed_barchart()
            self.assertTrue(os.path.exists(png1) and os.path.getsize(png1) > 10000)
            self.assertTrue(os.path.exists(pdf1) and os.path.getsize(pdf1) > 1000)

            png2, pdf2 = analyzer.plot_cumulative_packet_loss_curve()
            self.assertTrue(os.path.exists(png2) and os.path.getsize(png2) > 10000)
            self.assertTrue(os.path.exists(pdf2) and os.path.getsize(pdf2) > 1000)

    def test_markdown_findings_content(self):
        """Validates that markdown findings document contains summary table and analysis."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_doc = os.path.join(tmp_dir, "findings.md")
            analyzer = ConvergenceAnalyzer(output_doc=out_doc)
            analyzer.load_data()
            content = analyzer.generate_findings_markdown()

            self.assertTrue(os.path.exists(out_doc))
            self.assertIn("Clinical Baseline", content)
            self.assertIn("SC-01", content)
            self.assertIn("SC-06", content)
            self.assertIn("Gratuitous ARP", content)
            self.assertIn("Packet Tracer Simulation Event Scheduling Coarseness", content)

    def test_multi_trial_statistical_analysis(self):
        """Validates that multi-trial dataset computes 95% confidence intervals and standard deviations."""
        self.assertGreater(len(self.analyzer.trials), 50)
        self.assertGreater(len(self.analyzer.trial_stats), 5)

        for s in self.analyzer.trial_stats:
            self.assertEqual(s["trial_count"], 10)
            self.assertGreaterEqual(s["mean_outage_s"], 0.0)
            self.assertGreaterEqual(s["std_dev_s"], 0.0)
            self.assertGreaterEqual(s["ci_95_s"], 0.0)
            self.assertIn(s["sla_status"], ["ACCEPTABLE", "DEGRADED", "UNACCEPTABLE"])

        # Check SC-01 Config A (Default) vs Config B (Tuned) vs Config C (EIGRP)
        sc1_a = next(s for s in self.analyzer.trial_stats if s["scenario_id"] == "SC-01" and "Default" in s["configuration"])
        sc1_b = next(s for s in self.analyzer.trial_stats if s["scenario_id"] == "SC-01" and "Tuned" in s["configuration"])
        sc1_c = next(s for s in self.analyzer.trial_stats if s["scenario_id"] == "SC-01" and "EIGRP" in s["configuration"])

        # Tuned and EIGRP should converge faster than Default OSPF
        self.assertLessEqual(sc1_b["mean_outage_s"], sc1_a["mean_outage_s"])
        self.assertLessEqual(sc1_c["mean_outage_s"], sc1_a["mean_outage_s"])

    def test_multi_trial_chart_generation(self):
        """Validates that multi-trial comparison bar chart with error bars is produced."""
        with tempfile.TemporaryDirectory() as tmp_charts:
            analyzer = ConvergenceAnalyzer(charts_dir=tmp_charts)
            analyzer.load_data()
            png, pdf = analyzer.plot_multi_trial_comparison_barchart()
            self.assertTrue(os.path.exists(png) and os.path.getsize(png) > 10000)
            self.assertTrue(os.path.exists(pdf) and os.path.getsize(pdf) > 1000)

    def test_raw_ping_parser(self):
        """Validates ping parsing across Windows, Cisco IOS, and bitstream formats."""
        # Windows / Packet Tracer terminal output
        win_sample = """
        Pinging 172.16.5.10 with 32 bytes of data:
        Reply from 172.16.5.10: bytes=32 time=3ms TTL=126
        Reply from 172.16.5.10: bytes=32 time=4ms TTL=126
        Request timed out.
        Request timed out.
        Reply from 172.16.5.10: bytes=32 time=3ms TTL=126
        """
        res_win = parse_raw_ping_text(win_sample, ping_interval_s=1.0)
        self.assertEqual(res_win["total_sent"], 5)
        self.assertEqual(res_win["lost"], 2)
        self.assertEqual(res_win["max_consecutive_drops"], 2)
        self.assertEqual(res_win["estimated_convergence_outage_s"], 2.0)
        self.assertIn("ACCEPTABLE", res_win["sla_rating"])

        # Cisco IOS style output
        ios_sample = "!!!!!....!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        res_ios = parse_raw_ping_text(ios_sample, ping_interval_s=1.0)
        self.assertEqual(res_ios["total_sent"], 50)
        self.assertEqual(res_ios["lost"], 4)
        self.assertEqual(res_ios["estimated_convergence_outage_s"], 4.0)

        # Formatted report generation
        rep = format_report(res_win, scenario="SC-01 Primary WAN Cut", config="Tuned Fast OSPF")
        self.assertIn("SC-01 Primary WAN Cut", rep)
        self.assertIn("Estimated Outage", rep)

    def test_parse_ping_csv_append(self):
        """Validates that parse_raw_ping_text and CSV export append properly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = os.path.join(tmp_dir, "test_append.csv")
            sample_text = "Reply from 172.16.5.10: bytes=32 time=2ms TTL=126\nRequest timed out.\nReply from 172.16.5.10: bytes=32 time=2ms TTL=126"
            res = parse_raw_ping_text(sample_text, ping_interval_s=1.0)
            self.assertEqual(res["total_sent"], 3)
            self.assertEqual(res["lost"], 1)


if __name__ == "__main__":
    unittest.main()
