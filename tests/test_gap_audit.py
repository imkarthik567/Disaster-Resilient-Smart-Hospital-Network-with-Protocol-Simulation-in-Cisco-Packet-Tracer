#!/usr/bin/env python3
"""
================================================================================
Test Suite: Completeness & Gap Audit Report Verification
Disaster-Resilient Smart Hospital Network
VIT Vellore — Computer Networks (CSE2004)
================================================================================
Validates:
  1. Comprehensive Review-1 deliverable audit (D1 through D9).
  2. Cross-document consistency audit (Dual-campus IP space, VLAN IDs, protocols).
  3. Grade risk rankings (HIGH, MEDIUM, LOW) and concrete technical fixes.
  4. Chronologically ordered pre-submission checklist (Steps 1 to 5).
================================================================================
"""

import os
import re
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT_DOC = os.path.join(PROJECT_ROOT, "docs", "gap_audit.md")
TRACEABILITY_CSV = os.path.join(PROJECT_ROOT, "docs", "traceability_matrix.csv")


class TestGapAudit(unittest.TestCase):
    """Test suite validating completeness and gap audit documentation."""

    def setUp(self):
        self.assertTrue(os.path.isfile(AUDIT_DOC), f"Missing gap audit doc: {AUDIT_DOC}")
        self.assertTrue(os.path.isfile(TRACEABILITY_CSV), f"Missing traceability matrix CSV: {TRACEABILITY_CSV}")

        with open(AUDIT_DOC, "r", encoding="utf-8") as f:
            self.audit_content = f.read()

        with open(TRACEABILITY_CSV, "r", encoding="utf-8") as f:
            self.csv_content = f.read()

    def test_audit_document_exists_and_populated(self):
        """Verify audit document is populated with substantial analysis."""
        self.assertGreater(len(self.audit_content), 7000, "Gap audit document is unexpectedly short.")
        self.assertIn("Comprehensive Completeness & Gap Audit Report", self.audit_content)
        self.assertIn("PRODUCTION-READY", self.audit_content)

    def test_deliverable_verification_matrix_coverage(self):
        """Verify all 9 core deliverables (D1 to D9) are systematically audited."""
        expected_deliverables = [
            "D1: Packet Tracer Topology",
            "D2: Addressing & VLSM Plan",
            "D3: Hardened Device Configs",
            "D4: SBC IoT Python Code",
            "D5: Simulation Benchmark Engine",
            "D6: Network Design Document",
            "D7: Simulation Report",
            "D8: Verification Matrix",
            "D9: Review Slides & Viva Pack",
        ]
        for deliverable in expected_deliverables:
            self.assertIn(deliverable, self.audit_content, f"Missing deliverable audit: {deliverable}")

    def test_traceability_matrix_status_verified(self):
        """Verify all requirements in traceability_matrix.csv show VERIFIED status."""
        self.assertNotIn("Not started", self.csv_content, "Traceability matrix still contains 'Not started' entries.")
        self.assertIn("VERIFIED", self.csv_content, "Traceability matrix missing 'VERIFIED' status entries.")

    def test_cross_document_consistency_section(self):
        """Verify dual-campus IP address reconciliation and protocol parameters."""
        self.assertIn("Main Hospital Campus", self.audit_content)
        self.assertIn("Remote Emergency Clinic", self.audit_content)
        self.assertIn("172.16.7.128/26", self.audit_content)
        self.assertIn("172.16.8.32/27", self.audit_content)
        self.assertIn("172.16.8.80/30", self.audit_content)
        self.assertIn("Rapid-PVST+", self.audit_content)
        self.assertIn("HSRPv2", self.audit_content)

    def test_grade_risk_ranking(self):
        """Verify grade risk ranking contains HIGH, MEDIUM, and LOW risk categories."""
        self.assertIn("HIGH RISK", self.audit_content)
        self.assertIn("MEDIUM RISK", self.audit_content)
        self.assertIn("LOW RISK", self.audit_content)

        # Ensure critical gaps are listed
        self.assertIn("GAP-01", self.audit_content)  # .pkt file
        self.assertIn("GAP-02", self.audit_content)  # Placeholders
        self.assertIn("GAP-03", self.audit_content)  # Traceability status
        self.assertIn("GAP-04", self.audit_content)  # Dual-campus IP scope

    def test_prioritized_presubmission_checklist(self):
        """Verify 5-step chronological pre-submission checklist."""
        self.assertIn("Step 1: Automated Verification", self.audit_content)
        self.assertIn("Step 2: Packet Tracer Live Session", self.audit_content)
        self.assertIn("Step 3: Populate Live Measurement Placeholders", self.audit_content)
        self.assertIn("Step 4: Presentation & Viva Rehearsal", self.audit_content)
        self.assertIn("Step 5: Final Git Synchronization", self.audit_content)


if __name__ == "__main__":
    unittest.main()
