#!/usr/bin/env python3
"""
================================================================================
Unit Tests: PDU Analysis Evidence Pack Guide Verification
Disaster-Resilient Smart Hospital Network
================================================================================
Validates that /docs/pdu_analysis_guide.md contains:
  1. All 11 mandatory simulation capture items.
  2. Exact event list filters for each item.
  3. Hop-by-hop L2 header rewrite vs L3 IP constancy table.
  4. Textbook-grade 'What This Proves' paragraphs for every item.
  5. Caption templates and screenshot capture checklists for every item.
  6. Master PDU-to-OSI and Proposal Section 4.2 Traceability Matrix.
================================================================================
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PDU_GUIDE_PATH = os.path.join(PROJECT_ROOT, "docs", "pdu_analysis_guide.md")


class TestPduAnalysisGuide(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(PDU_GUIDE_PATH):
            raise FileNotFoundError(f"Missing PDU analysis guide at: {PDU_GUIDE_PATH}")
        with open(PDU_GUIDE_PATH, "r", encoding="utf-8") as f:
            cls.content = f.read()

    def test_file_exists_and_substantial(self):
        """Verifies that the guide exists and is populated with exhaustive documentation."""
        self.assertGreater(len(self.content), 15000, "PDU Analysis Guide must be comprehensive (>15KB)")

    def test_all_11_capture_items_present(self):
        """Ensures all 11 required PDU simulation items are explicitly defined."""
        required_items = [
            "PDU Capture Item 1: Address Resolution Protocol (ARP)",
            "PDU Capture Item 2: Dynamic Host Configuration Protocol (DHCP) DORA",
            "PDU Capture Item 3: DNS Query & Response",
            "PDU Capture Item 4: TCP Three-Way Handshake",
            "PDU Capture Item 5: TCP Connection Teardown",
            "PDU Capture Item 6: UDP Patient Vitals Stream",
            "PDU Capture Item 7: OSPF Routing Protocol Exchanges",
            "PDU Capture Item 8: Hot Standby Router Protocol (HSRP)",
            "PDU Capture Item 9: Spanning Tree Protocol (STP)",
            "PDU Capture Item 10: ICMP Traceroute Showing TTL Decrement",
            "PDU Capture Item 11: Security Access Control List (ACL) Drop"
        ]
        for item in required_items:
            self.assertIn(item, self.content, f"Missing required PDU item: {item}")

    def test_arp_hop_by_hop_l2_rewrite_and_l3_constancy(self):
        """Verifies ARP L2 rewrite table and end-to-end IP constancy demonstration."""
        self.assertIn("Hop-by-Hop L2 Header Rewrite vs. L3 Invariance Demonstration", self.content)
        self.assertIn("0000.0C07.AC0A", self.content)  # HSRP VMAC
        self.assertIn("172.16.8.40", self.content)      # Host IP
        self.assertIn("172.16.5.10", self.content)      # Server IP
        self.assertIn("L3 IP completely unchanged", self.content)

    def test_tcp_handshake_and_teardown_details(self):
        """Verifies TCP sequence numbers, acknowledgment numbers, flags, and window sizing."""
        self.assertIn("Seq=0, Ack=0, Win=16384", self.content)
        self.assertIn("Seq=0, Ack=1", self.content)
        self.assertIn("Seq=1, Ack=1", self.content)
        self.assertIn("FIN-ACK", self.content)
        self.assertIn("TIME_WAIT", self.content)

    def test_udp_vitals_telemetry_fields(self):
        """Verifies UDP connectionless behavior and DSCP Expedited Forwarding priority marking."""
        self.assertIn("DSCP `EF`", self.content)
        self.assertIn("0xB8", self.content)
        self.assertIn("5004", self.content)
        self.assertIn("Handshake: **None**", self.content)
        self.assertIn("Acknowledgment: **None**", self.content)

    def test_ospf_packet_types_and_event_flood(self):
        """Verifies all 5 OSPF packet types (Hello, DBD, LSR, LSU, LSAck) and link cut flood."""
        self.assertIn("Hello", self.content)
        self.assertIn("Database Description (DBD)", self.content)
        self.assertIn("Link-State Request (LSR)", self.content)
        self.assertIn("Link-State Update (LSU)", self.content)
        self.assertIn("Link-State Ack (LSAck)", self.content)
        self.assertIn("224.0.0.5", self.content)

    def test_acl_drop_red_x_and_osi_layer(self):
        """Verifies Red X visual indicator, matching ACE rule, and Layer 3/4 filtering engine."""
        self.assertIn("Red 'X'", self.content)
        self.assertIn("access-list 102 deny ip 172.16.7.0", self.content)
        self.assertIn("Layer 3 / Layer 4 Filtering", self.content)

    def test_textbook_paragraphs_and_caption_templates(self):
        """Ensures every item includes a 'What This Proves' paragraph and Caption Template."""
        proves_count = self.content.count("What This Proves (Textbook Analysis)")
        caption_count = self.content.count("Caption Template:")
        self.assertEqual(proves_count, 11, f"Expected 11 'What This Proves' sections, found {proves_count}")
        self.assertEqual(caption_count, 11, f"Expected 11 'Caption Template' entries, found {caption_count}")

    def test_master_proposal_mapping_matrix(self):
        """Verifies master matrix mapping to OSI layers and Section 4.2 Proposal Objectives."""
        self.assertIn("Master PDU-to-OSI Mapping & Proposal Objectives Matrix", self.content)
        self.assertIn("Proposal Section 4.2 Objective Addressed", self.content)
        for i in range(1, 12):
            self.assertIn(f"| **{i:02d}** |", self.content)


if __name__ == "__main__":
    unittest.main()
