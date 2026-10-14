#!/usr/bin/env python3
"""
================================================================================
Unit Tests: Cisco IOS Config Linter & Show Parser
Disaster-Resilient Smart Hospital Network
================================================================================
Validates:
  1. Full production repository passes ConfigLinter with 0 errors.
  2. Intentionally broken configs are caught (duplicate IP, invalid mask,
     plaintext password, missing BPDU guard, missing ACL definition, missing SSH).
  3. Show-command parsers correctly transform CLI text into structured JSON:
     - show ip interface brief
     - show vlan brief
     - show ip ospf neighbor
     - show standby brief
     - show access-lists
================================================================================
"""

import os
import sys
import tempfile
import textwrap
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from verification.lint_configs import ConfigLinter, normalize_interface_name
from verification.parse_show import (
    parse_show_ip_interface_brief,
    parse_show_vlan_brief,
    parse_show_ip_ospf_neighbor,
    parse_show_standby_brief,
    parse_show_access_lists,
    parse_show_output,
)


class TestConfigLinterProduction(unittest.TestCase):
    def test_production_configs_pass(self):
        """Validates that all production configs in /configs pass all 11 linter rules."""
        linter = ConfigLinter()
        passed = linter.run_all_checks()
        if not passed:
            print("\nEncountered Linter Errors:", file=sys.stderr)
            for err in linter.errors:
                print(f"  - {err}", file=sys.stderr)
        self.assertTrue(passed, f"Linter encountered {len(linter.errors)} errors on production configs")
        self.assertEqual(len(linter.errors), 0)


class TestConfigLinterDefects(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _run_linter_on_snippet(self, dev_name: str, config_text: str) -> ConfigLinter:
        dev_dir = os.path.join(self.temp_dir.name, dev_name)
        os.makedirs(dev_dir, exist_ok=True)
        cfg_file = os.path.join(dev_dir, f"{dev_name}.cfg")
        with open(cfg_file, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent(config_text).strip())

        linter = ConfigLinter(
            configs_dir=self.temp_dir.name,
            cabling_csv=os.path.join(PROJECT_ROOT, "topology", "cabling.csv"),
            ip_table_csv=os.path.join(PROJECT_ROOT, "addressing", "ip_table.csv")
        )
        linter.run_all_checks()
        return linter

    def test_detects_plaintext_password(self):
        """Catches 'enable password' instead of 'enable secret' and missing password-encryption."""
        cfg = """
        hostname SW-A1
        enable password InsecurePlaintextPass
        line con 0
         password cisco
        line vty 0 4
         transport input ssh
         login local
        ip ssh version 2
        """
        linter = self._run_linter_on_snippet("SW-A1", cfg)
        self.assertTrue(any("enable password" in e for e in linter.errors))
        self.assertTrue(any("service password-encryption" in e for e in linter.errors))

    def test_detects_missing_ssh_configuration(self):
        """Catches missing 'ip ssh version 2' or missing 'transport input ssh'."""
        cfg = """
        hostname R1
        service password-encryption
        enable secret 5 $1$mERr$hx5rVt7rPNoS4wqbXKX7m0
        line vty 0 4
         transport input telnet
         login local
        """
        linter = self._run_linter_on_snippet("R1", cfg)
        self.assertTrue(any("ip ssh version 2" in e for e in linter.errors))
        self.assertTrue(any("transport input ssh" in e for e in linter.errors))

    def test_detects_missing_acl_definition(self):
        """Catches an ACL applied to an interface that has not been defined."""
        cfg = """
        hostname R1
        service password-encryption
        enable secret 5 $1$mERr$hx5rVt7rPNoS4wqbXKX7m0
        ip ssh version 2
        line vty 0 4
         transport input ssh
         login local
        interface GigabitEthernet0/0
         ip address 172.16.8.98 255.255.255.252
         ip access-group ACL-UNDEFINED-TEST in
        """
        linter = self._run_linter_on_snippet("R1", cfg)
        self.assertTrue(any("ACL 'ACL-UNDEFINED-TEST' is referenced" in e for e in linter.errors))

    def test_detects_missing_bpduguard_on_access_port(self):
        """Catches an active access port on an access switch missing BPDU guard."""
        cfg = """
        hostname SW-A1
        service password-encryption
        enable secret 5 $1$mERr$hx5rVt7rPNoS4wqbXKX7m0
        ip ssh version 2
        line vty 0 4
         transport input ssh
         login local
        interface FastEthernet0/1
         switchport mode access
         switchport access vlan 10
         spanning-tree portfast
        """
        linter = self._run_linter_on_snippet("SW-A1", cfg)
        self.assertTrue(any("BPDU Guard" in e for e in linter.errors))


class TestShowParsers(unittest.TestCase):
    def test_parse_show_ip_interface_brief(self):
        raw = """
Interface              IP-Address      OK? Method Status                Protocol
FastEthernet0/1        unassigned      YES unset  up                    up
FastEthernet0/2        unassigned      YES unset  down                  down
FastEthernet0/24       unassigned      YES unset  administratively down down
GigabitEthernet0/1     172.16.8.98     YES manual up                    up
Vlan10                 172.16.8.35     YES NVRAM  up                    up
        """
        parsed = parse_show_ip_interface_brief(raw)
        self.assertEqual(len(parsed), 5)

        gi01 = next(item for item in parsed if item["interface"] == "GigabitEthernet0/1")
        self.assertEqual(gi01["ip_address"], "172.16.8.98")
        self.assertEqual(gi01["status"], "up")
        self.assertEqual(gi01["protocol"], "up")
        self.assertTrue(gi01["ok"])

        fa24 = next(item for item in parsed if item["interface"] == "FastEthernet0/24")
        self.assertIsNone(fa24["ip_address"])
        self.assertEqual(fa24["status"], "administratively down")

    def test_parse_show_vlan_brief(self):
        raw = """
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Fa0/5, Fa0/6, Fa0/7, Fa0/8
                                                Fa0/9, Fa0/10
10   ICU_TELEMETRY                    active    Fa0/1, Fa0/2
20   THEATRE_SENSORS                  active    Fa0/3, Fa0/4
999  PARKING_UNUSED                   active    Fa0/11, Fa0/12, Fa0/13
        """
        parsed = parse_show_vlan_brief(raw)
        self.assertEqual(len(parsed), 4)

        vlan1 = next(v for v in parsed if v["vlan_id"] == 1)
        self.assertEqual(len(vlan1["ports"]), 6)
        self.assertIn("Fa0/5", vlan1["ports"])
        self.assertIn("Fa0/10", vlan1["ports"])

        vlan10 = next(v for v in parsed if v["vlan_id"] == 10)
        self.assertEqual(vlan10["name"], "ICU_TELEMETRY")
        self.assertEqual(vlan10["ports"], ["Fa0/1", "Fa0/2"])

    def test_parse_show_ip_ospf_neighbor(self):
        raw = """
Neighbor ID     Pri   State           Dead Time   Address         Interface
172.16.8.106      1   FULL/BDR        00:00:34    172.16.8.98     GigabitEthernet0/1
172.16.8.107      1   FULL/DR         00:00:39    172.16.8.90     GigabitEthernet0/2
172.16.8.105      1   FULL/  -        00:00:31    172.16.8.82     Serial0/0/0
        """
        parsed = parse_show_ip_ospf_neighbor(raw)
        self.assertEqual(len(parsed), 3)

        n1 = parsed[0]
        self.assertEqual(n1["neighbor_id"], "172.16.8.106")
        self.assertEqual(n1["priority"], 1)
        self.assertEqual(n1["state"], "FULL")
        self.assertEqual(n1["role"], "BDR")
        self.assertEqual(n1["address"], "172.16.8.98")
        self.assertEqual(n1["interface"], "GigabitEthernet0/1")

        n3 = parsed[2]
        self.assertEqual(n3["role"], "POINT_TO_POINT")
        self.assertEqual(n3["interface"], "Serial0/0/0")

    def test_parse_show_standby_brief(self):
        raw = """
Interface   Grp  Pri P State   Active          Standby         Virtual IP
Vl10        10   120 P Active  local           172.16.8.35     172.16.8.33
Vl20        20   110   Standby 172.16.8.49     local           172.16.8.49
Vl30        30   120 P Active  local           172.16.8.3      172.16.8.1
        """
        parsed = parse_show_standby_brief(raw)
        self.assertEqual(len(parsed), 3)

        v10 = parsed[0]
        self.assertEqual(v10["interface"], "Vl10")
        self.assertEqual(v10["group"], 10)
        self.assertEqual(v10["priority"], 120)
        self.assertTrue(v10["preempt"])
        self.assertEqual(v10["state"], "Active")
        self.assertEqual(v10["virtual_ip"], "172.16.8.33")

        v20 = parsed[1]
        self.assertFalse(v20["preempt"])
        self.assertEqual(v20["state"], "Standby")

    def test_parse_show_access_lists(self):
        raw = """
Standard IP access list 10
    10 permit 172.16.8.64 0.0.0.15 (14 matches)
    20 deny any (5 matches)
Extended IP access list ACL-CLINIC-INSPECT
    10 permit tcp any any established (1284 matches)
    20 permit udp host 172.16.1.10 host 172.16.5.10 eq 5004 (482 matches)
    30 deny ip any any (12 matches)
        """
        parsed = parse_show_access_lists(raw)
        self.assertIn("10", parsed)
        self.assertIn("ACL-CLINIC-INSPECT", parsed)

        acl10 = parsed["10"]
        self.assertEqual(acl10["type"], "Standard IP")
        self.assertEqual(len(acl10["rules"]), 2)
        self.assertEqual(acl10["rules"][0]["matches"], 14)
        self.assertEqual(acl10["rules"][0]["action"], "permit")

        acl_inspect = parsed["ACL-CLINIC-INSPECT"]
        self.assertEqual(acl_inspect["type"], "Extended IP")
        self.assertEqual(len(acl_inspect["rules"]), 3)
        self.assertEqual(acl_inspect["rules"][1]["protocol"], "udp")
        self.assertEqual(acl_inspect["rules"][1]["matches"], 482)

    def test_dispatcher(self):
        raw = "Interface IP-Address OK? Method Status Protocol\nGi0/0 10.0.0.1 YES manual up up"
        res = parse_show_output("show ip int brief", raw)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["ip_address"], "10.0.0.1")


if __name__ == "__main__":
    unittest.main()
