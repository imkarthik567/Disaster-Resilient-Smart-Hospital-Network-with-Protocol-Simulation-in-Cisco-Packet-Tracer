#!/usr/bin/env python3
"""
================================================================================
Unit Tests: TCP vs. UDP Comparative Study & Design Justification Verification
Disaster-Resilient Smart Hospital Network
================================================================================
Validates that /docs/tcp_vs_udp_comparison.md contains:
  1. 5 MB experimental setup comparing TCP (HTTP/FTP) and UDP vitals under competing load.
  2. Observation metrics: cwnd fluctuations, retransmissions, latency, and goodput.
  3. Comprehensive two-column quantitative comparison table.
  4. Cross-layer synthesis connecting Layer 4 TCP/UDP to Phase 8 Data-Link ARQ.
  5. Verbatim one-page Design Justification for Master Project Report and Viva.
================================================================================
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMPARISON_DOC_PATH = os.path.join(PROJECT_ROOT, "docs", "tcp_vs_udp_comparison.md")


class TestTcpVsUdpComparison(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(COMPARISON_DOC_PATH):
            raise FileNotFoundError(f"Missing TCP vs UDP comparison document at: {COMPARISON_DOC_PATH}")
        with open(COMPARISON_DOC_PATH, "r", encoding="utf-8") as f:
            cls.content = f.read()

    def test_file_exists_and_substantial(self):
        """Verifies that the document exists and has comprehensive depth (>10KB)."""
        self.assertGreater(len(self.content), 10000, "Comparison document must be comprehensive (>10KB)")

    def test_experimental_design_and_competing_load(self):
        """Verifies 5 MB transfer setup, TCP (HTTP/FTP), UDP vitals, and competing load generator."""
        self.assertIn("5 MB", self.content)
        self.assertIn("HTTP", self.content)
        self.assertIn("FTP", self.content)
        self.assertIn("Competing Congestion Load", self.content)
        self.assertIn("1.544 Mbps", self.content)  # T1 Serial WAN bottleneck
        self.assertIn("VLAN 60", self.content)

    def test_observation_metrics_specified(self):
        """Verifies observation of window changes, retransmission penalties, and latency."""
        self.assertIn("Congestion Window ($cwnd$)", self.content)
        self.assertIn("Fast Retransmits", self.content)
        self.assertIn("Retransmission Timeouts (RTO)", self.content)
        self.assertIn("Head-of-Line (HoL) Blocking", self.content)
        self.assertIn("Transit Latency & Jitter", self.content)
        self.assertIn("Effective Application Goodput", self.content)

    def test_two_column_comparison_matrix(self):
        """Verifies comprehensive comparison table between TCP and UDP."""
        self.assertIn("Quantitative Comparison Matrix: TCP versus UDP", self.content)
        self.assertIn("Protocol Header Size", self.content)
        self.assertIn("20 to 60 Bytes", self.content)
        self.assertIn("8 Bytes fixed", self.content)
        self.assertIn("Head-of-Line Blocking", self.content)
        self.assertIn("Average Latency (5% Loss)", self.content)
        self.assertIn("12 ms - 28 ms", self.content)
        self.assertIn("380 ms - 1,450 ms", self.content)

    def test_cross_layer_synthesis_to_phase8_arq(self):
        """Verifies scale-invariant mapping between Layer 2 ARQ and Layer 4 TCP/UDP."""
        self.assertIn("Cross-Layer Synthesis: Connecting Transport Layer to Phase 8 Data-Link ARQ", self.content)
        self.assertIn("SCALE-INVARIANT ARQ MECHANISMS", self.content)
        self.assertIn("Layer 2: Data-Link ARQ (Phase 8)", self.content)
        self.assertIn("Layer 4: End-to-End Transport (TCP / RFC 793)", self.content)
        self.assertIn("Go-Back-N", self.content)
        self.assertIn("Selective Repeat", self.content)
        self.assertIn("Selective ACKs (SACK)", self.content)
        self.assertIn("Hop-by-Hop vs. End-to-End", self.content)

    def test_verbatim_design_justification(self):
        """Verifies one-page design justification for report and viva defense."""
        self.assertIn("Formal Design Justification (Verbatim Thesis & Viva Defense Formulation)", self.content)
        self.assertIn("The Clinical Dilemma", self.content)
        self.assertIn("Why Raw UDP is Inadequate", self.content)
        self.assertIn("The Engineered Architectural Solution", self.content)
        self.assertIn("CRC-16-CCITT", self.content)
        self.assertIn("Two-Dimensional Parity Matrix", self.content)
        self.assertIn("1-bit self-healing", self.content)
        self.assertIn("3.0-second vitals outage SLA", self.content)


if __name__ == "__main__":
    unittest.main()
