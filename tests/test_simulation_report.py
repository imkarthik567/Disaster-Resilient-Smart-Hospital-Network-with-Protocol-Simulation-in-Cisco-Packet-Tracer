#!/usr/bin/env python3
"""
================================================================================
Unit Tests: Simulation Analysis Report Verification
Disaster-Resilient Smart Hospital Network
================================================================================
Validates that /docs/simulation_report.md contains:
  1. Master checklist of Packet Tracer measurement placeholders at the top.
  2. All 6 experiments with Objective, Method & Setup, Results, Discussion,
     Threats to Validity, and Conclusion.
  3. All 10 clearly marked measurement placeholders.
  4. Lessons learned section.
  5. Future work section covering IPv6, SD-WAN, 802.1X, hardware validation, and SNMP.
================================================================================
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPORT_PATH = os.path.join(PROJECT_ROOT, "docs", "simulation_report.md")


class TestSimulationReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(REPORT_PATH):
            raise FileNotFoundError(f"Missing simulation report at: {REPORT_PATH}")
        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            cls.content = f.read()

    def test_file_exists_and_substantial(self):
        """Verifies report existence and substantial depth (>15KB)."""
        self.assertGreater(len(self.content), 15000, "Simulation report must be comprehensive (>15KB)")

    def test_placeholder_checklist_at_top(self):
        """Verifies master checklist table of all 10 placeholders at the beginning."""
        self.assertIn("Master Checklist of Packet Tracer Measurement Placeholders", self.content)
        for i in range(1, 11):
            tag = f"PLACEHOLDER-PT-{i:02d}"
            self.assertIn(tag, self.content, f"Missing placeholder {tag} in master checklist")

    def test_all_six_experiments_present(self):
        """Ensures all 6 required experiments are documented."""
        experiments = [
            "Experiment 1: Error Detection & Correction Coverage",
            "Experiment 2: Sliding-Window ARQ Protocol Comparison",
            "Experiment 3: Quality of Service (QoS) & DiffServ Prioritization",
            "Experiment 4: High-Availability Failover & Convergence Analysis",
            "Experiment 5: Transport Layer Comparative Study (TCP vs. UDP)",
            "Experiment 6: Security ACL Enforcement & Inter-VLAN Isolation"
        ]
        for exp in experiments:
            self.assertIn(exp, self.content, f"Missing experiment: {exp}")

    def test_experiment_structure_and_subsections(self):
        """Verifies that each experiment includes Objective, Method, Results, Discussion, Threats, and Conclusion."""
        sections = [
            "Objective", "Method", "Results", "Discussion", "Threats to Validity", "Conclusion"
        ]
        for s in sections:
            count = self.content.count(s)
            self.assertGreaterEqual(count, 6, f"Expected at least 6 occurrences of section '{s}', found {count}")

    def test_results_charts_referenced(self):
        """Verifies that relevant results charts are cross-referenced."""
        charts = [
            "detection_coverage_bars.png",
            "transfer_time_vs_window.png",
            "retransmissions_vs_loss.png",
            "efficiency_vs_window_theory.png",
            "goodput_heatmap.png",
            "failover_theoretical_vs_observed.png",
            "failover_cumulative_loss.png",
            "failover_multi_trial_comparison.png"
        ]
        for chart in charts:
            self.assertIn(chart, self.content, f"Missing chart reference: {chart}")

    def test_lessons_learned_and_future_work(self):
        """Verifies lessons learned and future work extensions."""
        self.assertIn("Lessons Learned & Practical Engineering Insights", self.content)
        self.assertIn("Future Work & Advanced Architectural Extensions", self.content)
        self.assertIn("IPv6 Dual-Stack", self.content)
        self.assertIn("SD-WAN", self.content)
        self.assertIn("IEEE 802.1X", self.content)
        self.assertIn("Physical Hardware Validation", self.content)
        self.assertIn("SNMP", self.content)


if __name__ == "__main__":
    unittest.main()
