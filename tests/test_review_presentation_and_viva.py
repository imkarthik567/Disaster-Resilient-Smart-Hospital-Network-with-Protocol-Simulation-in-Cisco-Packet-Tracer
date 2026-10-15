#!/usr/bin/env python3
"""
================================================================================
Test Suite: Review Presentation Slides & Viva Voce Examination Defense Guide
Disaster-Resilient Smart Hospital Network
VIT Vellore — Computer Networks (CSE2004)
================================================================================
Validates:
  1. Review slides outline (12-15 slides, visual asset refs, ~100-word speaker notes).
  2. Viva question bank (60+ questions, all 13 topics, complete model answers).
  3. Mathematical proofs (CRC division, 2D parity matrix, SR window limit W <= 2^{k-1}).
  4. Architectural trade-offs ("Why Choose X over Y?").
  5. 5-minute live demonstration script with timed phases, spoken scripts, and fallback runbook.
================================================================================
"""

import os
import re
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLIDES_PATH = os.path.join(PROJECT_ROOT, "docs", "review_slides.md")
VIVA_PATH = os.path.join(PROJECT_ROOT, "docs", "viva_questions.md")


class TestReviewPresentationAndViva(unittest.TestCase):
    """Test suite validating Review Slides and Viva Question Bank documents."""

    def setUp(self):
        self.assertTrue(os.path.isfile(SLIDES_PATH), f"Missing review slides: {SLIDES_PATH}")
        self.assertTrue(os.path.isfile(VIVA_PATH), f"Missing viva questions: {VIVA_PATH}")

        with open(SLIDES_PATH, "r", encoding="utf-8") as f:
            self.slides_content = f.read()

        with open(VIVA_PATH, "r", encoding="utf-8") as f:
            self.viva_content = f.read()

    def test_review_slides_structure_and_count(self):
        """Verify review slides document contains between 12 and 15 slides with required structure."""
        self.assertGreater(len(self.slides_content), 10000, "Review slides document is unexpectedly short.")

        # Match slide headers e.g. ## Slide 1:
        slide_headers = re.findall(r"^##\s+Slide\s+(\d+):", self.slides_content, re.MULTILINE)
        slide_count = len(slide_headers)
        self.assertGreaterEqual(slide_count, 12, f"Slide count {slide_count} is less than minimum 12.")
        self.assertLessEqual(slide_count, 15, f"Slide count {slide_count} exceeds maximum 15.")

        # Check each slide has Title, Visual Asset, and Speaker Notes
        slides = re.split(r"^##\s+Slide\s+\d+:", self.slides_content, flags=re.MULTILINE)[1:]
        self.assertEqual(len(slides), slide_count)

        for i, slide in enumerate(slides, start=1):
            self.assertIn("Slide Title:", slide, f"Slide {i} missing 'Slide Title:'")
            self.assertIn("Visual Asset:", slide, f"Slide {i} missing 'Visual Asset:'")
            self.assertIn("Speaker Notes", slide, f"Slide {i} missing 'Speaker Notes'")

            # Check speaker notes word count (~100 words, at least 60 words)
            notes_match = re.search(r"Speaker Notes[^\n]*\n\s*>\s*\"([^\"]+)\"", slide, re.DOTALL)
            self.assertIsNotNone(notes_match, f"Slide {i} speaker notes quote block not found.")
            notes_text = notes_match.group(1).strip()
            word_count = len(notes_text.split())
            self.assertGreaterEqual(
                word_count, 60,
                f"Slide {i} speaker notes too brief ({word_count} words; expected ~100 words)."
            )

    def test_viva_questions_count_and_topics(self):
        """Verify viva questions bank contains at least 60 questions covering all 13 core topics."""
        self.assertGreater(len(self.viva_content), 30000, "Viva document is unexpectedly short.")

        # Count questions: ### Q1: ...
        questions = re.findall(r"^###\s+Q(\d+):", self.viva_content, re.MULTILINE)
        self.assertGreaterEqual(len(questions), 60, f"Found {len(questions)} questions; minimum 60 required.")

        # Verify all 13 topic headings are present
        expected_topics = [
            "VLSM Calculation",
            "Spanning Tree Protocols",
            "First-Hop Redundancy Protocols",
            "OSPF Architecture",
            "EIGRP Architecture",
            "Administrative Distance",
            "Access Control Lists",
            "Network Address Translation",
            "Quality of Service",
            "Error Detection",
            "Sliding-Window Flow Control",
            "Transport Layer",
            "Architectural Trade-Offs",
        ]
        for topic in expected_topics:
            self.assertIn(topic, self.viva_content, f"Required topic '{topic}' not found in viva guide.")

    def test_worked_mathematical_proofs(self):
        """Verify worked mathematical proofs exist with explicit derivations."""
        # 1. CRC division derivation
        self.assertIn("1011 ) 110101000", self.viva_content, "CRC-16 binary division proof missing.")
        self.assertIn("110101111", self.viva_content, "CRC transmitted codeword calculation missing.")

        # 2. 2D parity matrix syndrome intersection
        self.assertIn("syndrome intersection", self.viva_content.lower(), "2D parity syndrome proof missing.")
        self.assertIn("Horizontal Parity", self.viva_content, "2D parity horizontal component missing.")
        self.assertIn("Vertical Parity", self.viva_content, "2D parity vertical component missing.")

        # 3. Selective repeat window constraint W <= 2^{k-1}
        self.assertIn("2^{k-1}", self.viva_content, "Selective Repeat window bound formula missing.")
        self.assertIn("W_s + W_r", self.viva_content, "SR window proof derivation step missing.")

        # 4. Bandwidth-Delay Product (BDP)
        self.assertIn("BDP", self.viva_content, "Bandwidth-Delay Product missing.")

        # 5. EIGRP feasibility condition
        self.assertIn("Feasibility Condition", self.viva_content, "EIGRP FC heading missing.")
        self.assertIn("Reported Distance", self.viva_content, "EIGRP RD missing.")
        self.assertIn("Feasible Distance", self.viva_content, "EIGRP FD missing.")

    def test_architectural_tradeoffs_section(self):
        """Verify architectural trade-offs ("Why Choose X over Y?") are fully detailed."""
        tradeoffs_section = re.search(
            r"## Topic 13: Architectural Trade-Offs.*?## 5-Minute Live Demonstration",
            self.viva_content, re.DOTALL
        )
        self.assertIsNotNone(tradeoffs_section, "Topic 13 Architectural Trade-Offs section not found.")
        text = tradeoffs_section.group(0)

        # Ensure major protocol trade-offs are evaluated
        self.assertIn("OSPF over EIGRP or RIP", text)
        self.assertIn("HSRP over VRRP or GLBP", text)
        self.assertIn("Rapid-PVST+ over standard 802.1D", text)
        self.assertIn("Selective Repeat selected over Go-Back-N", text)
        self.assertIn("custom application framing layer for UDP", text)

    def test_live_demo_script_and_fallback_runbook(self):
        """Verify 5-minute live demonstration script with timed milestones and fallback runbook."""
        self.assertIn("5-Minute Live Demonstration Script", self.viva_content)
        self.assertIn("Emergency Fallback Runbook", self.viva_content)

        # Check time milestones
        self.assertIn("0:00 - 1:00", self.viva_content)
        self.assertIn("1:00 - 2:30", self.viva_content)
        self.assertIn("2:30 - 3:30", self.viva_content)
        self.assertIn("3:30 - 4:30", self.viva_content)
        self.assertIn("4:30 - 5:00", self.viva_content)

        # Check spoken scripts and actions
        self.assertIn("ping -t 172.16.5.10", self.viva_content)
        self.assertIn("show ip ospf neighbor", self.viva_content)
        self.assertIn("show standby brief", self.viva_content)
        self.assertIn("Spoken Script:", self.viva_content)

        # Check fallback runbook table rows
        self.assertIn("Pings fail after link delete", self.viva_content)
        self.assertIn("Packet Tracer freezes / crashes", self.viva_content)
        self.assertIn("SBC Python script throws error", self.viva_content)
        self.assertIn("passing 29/29", self.viva_content)
        self.assertIn("HSRP fails to preempt", self.viva_content)


if __name__ == "__main__":
    unittest.main()
