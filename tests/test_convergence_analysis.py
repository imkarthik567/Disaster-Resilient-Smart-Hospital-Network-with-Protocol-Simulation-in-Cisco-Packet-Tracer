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


if __name__ == "__main__":
    unittest.main()
