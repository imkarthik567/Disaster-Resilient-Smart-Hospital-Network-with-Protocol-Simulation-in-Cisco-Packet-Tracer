#!/usr/bin/env python3
"""
================================================================================
Test Suite: IPv6 Dual-Stack Architecture & Advanced Extensions Prioritization
Disaster-Resilient Smart Hospital Network
VIT Vellore — Computer Networks (CSE2004)
================================================================================
Validates:
  1. IPv6 addressing plan in docs/ipv6_dual_stack_design.md (2001:db8:acad::/48).
  2. Link-local address allocation (fe80::) across routers and multilayer switches.
  3. OSPFv3 protocol design, multi-area hierarchy (Area 0, 1, 2), and interface bindings.
  4. Dual-stack configuration snippets (R1, R2, SW-D1, SW-D2, SW-D3) in configs/ipv6_dual_stack/.
  5. Prioritization matrix in docs/advanced_extensions_prioritization.md (all 5 extensions evaluated).
================================================================================
"""

import os
import re
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IPV6_DOC = os.path.join(PROJECT_ROOT, "docs", "ipv6_dual_stack_design.md")
EXTENSIONS_DOC = os.path.join(PROJECT_ROOT, "docs", "advanced_extensions_prioritization.md")
IPV6_CONFIGS_DIR = os.path.join(PROJECT_ROOT, "configs", "ipv6_dual_stack")


class TestIPv6DualStack(unittest.TestCase):
    """Test suite validating IPv6 dual-stack design, configs, and extensions."""

    def setUp(self):
        self.assertTrue(os.path.isfile(IPV6_DOC), f"Missing IPv6 design doc: {IPV6_DOC}")
        self.assertTrue(os.path.isfile(EXTENSIONS_DOC), f"Missing extensions doc: {EXTENSIONS_DOC}")
        self.assertTrue(os.path.isdir(IPV6_CONFIGS_DIR), f"Missing IPv6 configs dir: {IPV6_CONFIGS_DIR}")

        with open(IPV6_DOC, "r", encoding="utf-8") as f:
            self.ipv6_content = f.read()

        with open(EXTENSIONS_DOC, "r", encoding="utf-8") as f:
            self.ext_content = f.read()

    def test_ipv6_addressing_plan_consistency(self):
        """Validate base /48 allocation, subnet breakdown, and link-local architecture."""
        # Check RFC 3849 documentation prefix
        self.assertIn("2001:db8:acad::/48", self.ipv6_content)

        # Validate all clinical VLANs have /64 subnets
        vlan_prefixes = [
            ("VLAN 10", "2001:db8:acad:10::/64"),
            ("VLAN 20", "2001:db8:acad:20::/64"),
            ("VLAN 30", "2001:db8:acad:30::/64"),
            ("VLAN 40", "2001:db8:acad:40::/64"),
            ("VLAN 50", "2001:db8:acad:50::/64"),
            ("VLAN 60", "2001:db8:acad:60::/64"),
        ]
        for vlan_label, prefix in vlan_prefixes:
            self.assertIn(prefix, self.ipv6_content, f"Missing IPv6 subnet {prefix} for {vlan_label}")

        # Validate WAN & Routed interconnects
        self.assertIn("2001:db8:acad:80::/64", self.ipv6_content)  # Primary Serial WAN
        self.assertIn("2001:db8:acad:84::/64", self.ipv6_content)  # Backup Serial WAN
        self.assertIn("2001:db8:acad:88::/64", self.ipv6_content)  # R1 to SW-D1
        self.assertIn("2001:db8:acad:92::/64", self.ipv6_content)  # R1 to SW-D2

        # Validate link-local addresses
        self.assertIn("fe80::1", self.ipv6_content)
        self.assertIn("fe80::2", self.ipv6_content)
        self.assertIn("fe80::d1", self.ipv6_content)
        self.assertIn("fe80::d2", self.ipv6_content)
        self.assertIn("fe80::d3", self.ipv6_content)

    def test_ospfv3_protocol_architecture(self):
        """Validate OSPFv3 protocol design, RFC 5340 concepts, and multi-area topology."""
        self.assertIn("RFC 5340", self.ipv6_content)
        self.assertIn("Type-8 (Link LSA)", self.ipv6_content)
        self.assertIn("Type-9 (Intra-Area-Prefix LSA)", self.ipv6_content)
        self.assertIn("ipv6 router ospf", self.ipv6_content)
        self.assertIn("ipv6 ospf 1 area", self.ipv6_content)

    def test_ipv6_config_files_present_and_valid(self):
        """Validate all 5 Cisco IOS IPv6 configuration snippets exist and contain valid directives."""
        expected_configs = [
            "R1_ipv6.cfg",
            "R2_ipv6.cfg",
            "SW-D1_ipv6.cfg",
            "SW-D2_ipv6.cfg",
            "SW-D3_ipv6.cfg",
        ]
        for cfg_name in expected_configs:
            cfg_path = os.path.join(IPV6_CONFIGS_DIR, cfg_name)
            self.assertTrue(os.path.isfile(cfg_path), f"Missing IPv6 config: {cfg_name}")

            with open(cfg_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("ipv6 unicast-routing", content, f"Missing ipv6 unicast-routing in {cfg_name}")
            self.assertIn("ipv6 router ospf 1", content, f"Missing ipv6 router ospf 1 in {cfg_name}")
            self.assertIn("router-id", content, f"Missing OSPFv3 router-id in {cfg_name}")
            self.assertIn("link-local", content, f"Missing link-local address in {cfg_name}")

        # Check Router R1 specific directives
        with open(os.path.join(IPV6_CONFIGS_DIR, "R1_ipv6.cfg"), "r", encoding="utf-8") as f:
            r1 = f.read()
        self.assertIn("fe80::1 link-local", r1)
        self.assertIn("ipv6 ospf cost 64", r1)
        self.assertIn("ipv6 ospf cost 500", r1)

        # Check Switch SW-D1 specific directives
        with open(os.path.join(IPV6_CONFIGS_DIR, "SW-D1_ipv6.cfg"), "r", encoding="utf-8") as f:
            d1 = f.read()
        self.assertIn("sdm prefer dual-ipv4-and-ipv6 default", d1)
        self.assertIn("passive-interface Vlan10", d1)
        self.assertIn("passive-interface Vlan50", d1)

        # Check Switch SW-D2 specific directives
        with open(os.path.join(IPV6_CONFIGS_DIR, "SW-D2_ipv6.cfg"), "r", encoding="utf-8") as f:
            d2 = f.read()
        self.assertIn("sdm prefer dual-ipv4-and-ipv6 default", d2)
        self.assertIn("passive-interface Vlan20", d2)
        self.assertIn("passive-interface Vlan40", d2)
        self.assertIn("passive-interface Vlan60", d2)

    def test_extensions_prioritization_matrix(self):
        """Validate that all 5 advanced extensions are systematically evaluated."""
        required_extensions = [
            "Python Jinja2 Infrastructure-as-Code (IaC) Pipeline",
            "IPv6 Dual-Stack with OSPFv3 Core Routing",
            "SNMPv3 & Syslog Centralized NMS Monitoring",
            "DHCP Snooping & Dynamic ARP Inspection (DAI)",
            "Lightweight AP Wireless Guest with WPA2-Enterprise",
        ]
        for ext in required_extensions:
            self.assertIn(ext, self.ext_content, f"Extension '{ext}' not found in prioritization table.")

        # Check dimensions evaluated
        self.assertIn("Effort (Hours)", self.ext_content)
        self.assertIn("Academic Marks Value", self.ext_content)
        self.assertIn("Implementation Risks", self.ext_content)
        self.assertIn("Cisco Packet Tracer Support", self.ext_content)

        # Check top two selections explicitly declared
        self.assertIn("SELECTED & IMPLEMENTED (Extension 1)", self.ext_content)
        self.assertIn("SELECTED & IMPLEMENTED (Extension 2)", self.ext_content)


if __name__ == "__main__":
    unittest.main()
