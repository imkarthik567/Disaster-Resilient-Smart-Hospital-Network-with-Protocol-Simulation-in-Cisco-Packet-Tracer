#!/usr/bin/env python3
"""
================================================================================
Unit Tests: NetDevOps Jinja2 Configuration Pipeline
Disaster-Resilient Smart Hospital Network
================================================================================
"""

import os
import sys
import unittest
import tempfile
import yaml

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from automation.generate_configs import render_all_configs, SSOT_YAML


class TestAutomationPipeline(unittest.TestCase):
    def test_ssot_yaml_structure(self):
        """Validates that network_source_of_truth.yaml has required schema keys."""
        self.assertTrue(os.path.exists(SSOT_YAML))
        with open(SSOT_YAML, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.assertIn("global", data)
        self.assertIn("vlans", data)
        self.assertIn("devices", data)
        self.assertGreater(len(data["devices"]), 3)
        self.assertGreater(len(data["vlans"]), 5)

    def test_render_all_configs(self):
        """Validates that Jinja2 templates compile valid Cisco IOS configurations."""
        with tempfile.TemporaryDirectory() as tmp_out:
            count = render_all_configs(ssot_path=SSOT_YAML, out_dir=tmp_out)
            self.assertGreaterEqual(count, 5)

            # Check Router R1
            r1_cfg = os.path.join(tmp_out, "R1.cfg")
            self.assertTrue(os.path.exists(r1_cfg))
            with open(r1_cfg, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("hostname R1", content)
            self.assertIn("service password-encryption", content)
            self.assertIn("router ospf 1", content)
            self.assertIn("ip ssh version 2", content)
            self.assertIn("transport input ssh", content)

            # Check Distribution Switch SW-D1
            sw_d1_cfg = os.path.join(tmp_out, "SW-D1.cfg")
            self.assertTrue(os.path.exists(sw_d1_cfg))
            with open(sw_d1_cfg, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("hostname SW-D1", content)
            self.assertIn("standby 10 ip 172.16.8.33", content)
            self.assertIn("standby 10 priority 120", content)
            self.assertIn("spanning-tree mode rapid-pvst", content)

            # Check Access Switch SW-A1
            sw_a1_cfg = os.path.join(tmp_out, "SW-A1.cfg")
            self.assertTrue(os.path.exists(sw_a1_cfg))
            with open(sw_a1_cfg, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("hostname SW-A1", content)
            self.assertIn("spanning-tree portfast default", content)
            self.assertIn("spanning-tree portfast bpduguard default", content)
            self.assertIn("switchport trunk native vlan 999", content)


if __name__ == "__main__":
    unittest.main()
