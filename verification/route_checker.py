#!/usr/bin/env python3
"""
================================================================================
Cisco IOS 'show ip route' Analysis & Differential Verification Tool
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Parses pasted Cisco Packet Tracer / Cisco IOS 'show ip route' output and
validates it against expected routing profiles defined in YAML.

Detects and reports:
  1. Missing routes (expected in design but absent from actual RIB)
  2. Unexpected routes (present in actual RIB but unapproved in design)
  3. Wrong next-hop routes (expected gateway IP/interface mismatch)
  4. Wrong protocol routes (e.g., learned via EIGRP instead of OSPF, or vice-versa)

Supports route codes:
  - O     : OSPF Intra-Area
  - O IA  : OSPF Inter-Area
  - O*E2  : OSPF AS-External Type-2 default
  - D     : EIGRP Internal
  - D EX  : EIGRP External
  - C     : Directly Connected
  - L     : Local Interface Host Route (/32)
  - S* / S: Static Route / Candidate Default
================================================================================
"""

import argparse
import ipaddress
import json
import os
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

try:
    import yaml
except ImportError:
    yaml = None  # Fallback if PyYAML is absent

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_YAML_PATH = os.path.join(PROJECT_ROOT, "verification", "expected_routes.yaml")


class Route:
    """Represents a parsed Cisco IOS route entry."""
    def __init__(self, network: str, protocol: str, ad: Optional[int] = None,
                 metric: Optional[int] = None, nexthops: Optional[List[Dict[str, str]]] = None,
                 raw_text: str = ""):
        self.network = self._canonical_network(network)
        self.protocol = self._normalize_protocol(protocol)
        self.ad = ad
        self.metric = metric
        self.nexthops = nexthops or []
        self.raw_text = raw_text

    @staticmethod
    def _canonical_network(net_str: str) -> str:
        s = net_str.strip()
        try:
            if "/" in s:
                net = ipaddress.ip_network(s, strict=False)
                return f"{net.network_address}/{net.prefixlen}"
            else:
                net = ipaddress.ip_network(f"{s}/32", strict=False)
                return f"{net.network_address}/32"
        except ValueError:
            return s

    @staticmethod
    def _normalize_protocol(code: str) -> str:
        c = re.sub(r"\s+", " ", code.strip().upper())
        # Normalize OSPF external/default notations
        if c in ["O*E2", "O E2", "O*E1", "O E1"]:
            return "O*E2" if "2" in c else "O*E1"
        if c in ["S*", "S *", "*S"]:
            return "S*"
        if c in ["D*EX", "D EX", "*D EX"]:
            return "D EX"
        if c in ["O IA", "O*IA"]:
            return "O IA"
        return c

    def get_nexthop_ips(self) -> List[str]:
        return [nh["ip"] for nh in self.nexthops if nh.get("ip")]

    def get_interfaces(self) -> List[str]:
        return [normalize_interface(nh["interface"]) for nh in self.nexthops if nh.get("interface")]

    def __repr__(self) -> str:
        nhs = ", ".join([f"{nh.get('ip', 'conn')} on {nh.get('interface', 'none')}" for nh in self.nexthops])
        return f"<Route {self.protocol} {self.network} via [{nhs}]>"


def normalize_interface(iface: Optional[str]) -> str:
    """Normalizes interface abbreviations to standard shorthand (e.g. GigabitEthernet0/1 -> Gi0/1)."""
    if not iface:
        return ""
    s = iface.strip()
    replacements = [
        (r"^gigabitethernet", "Gi"),
        (r"^gig", "Gi"),
        (r"^fastethernet", "Fa"),
        (r"^fa", "Fa"),
        (r"^serial", "Se"),
        (r"^se", "Se"),
        (r"^port-channel", "Po"),
        (r"^po", "Po"),
        (r"^vlan", "Vl"),
        (r"^vl", "Vl"),
        (r"^loopback", "Lo"),
        (r"^lo", "Lo"),
    ]
    for pattern, repl in replacements:
        if re.search(pattern, s, re.IGNORECASE):
            return re.sub(pattern, repl, s, flags=re.IGNORECASE)
    return s


def parse_show_ip_route(text: str) -> Tuple[Optional[str], Dict[str, Route]]:
    """
    Parses full 'show ip route' CLI text output into a dictionary of {canonical_network: Route}.
    Also extracts the hostname if present in the prompt (e.g. 'R1# show ip route').
    """
    detected_device = None
    routes: Dict[str, Route] = {}
    current_route: Optional[Route] = None

    lines = text.splitlines()

    # Regex patterns
    prompt_pattern = re.compile(r"^([A-Za-z0-9_-]+)[#>]")
    
    # Connected and Local routes:
    # C 172.16.8.80/30 is directly connected, Serial0/0/0
    # L 172.16.8.81/32 is directly connected, Serial0/0/0
    conn_pattern = re.compile(
        r"^\s*(?P<code>C|L)\s+(?P<prefix>\d+\.\d+\.\d+\.\d+(?:/\d+)?)\s+is\s+directly\s+connected,\s+(?P<iface>[A-Za-z0-9/._-]+)",
        re.IGNORECASE
    )

    # Routed entries with via:
    # S* 0.0.0.0/0 [1/0] via 172.16.8.101, GigabitEthernet0/2
    # O*E2 0.0.0.0/0 [110/20] via 172.16.8.81, 00:15:30, Serial0/0/0
    # O IA 172.16.6.128/25 [110/49] via 172.16.8.82, 00:14:10, Serial0/0/0
    # D 172.16.8.0/24 [120/2172416] via 172.16.8.86, 00:00:15, Serial0/0/1
    # D EX 10.0.0.0/24 [170/2172416] via 172.16.8.86, 00:00:15, Serial0/0/1
    # O 172.16.0.0/22 [110/2] via 172.16.8.93, 00:15:21, GigabitEthernet0/1
    routed_pattern = re.compile(
        r"^\s*(?P<code>O(?:\s+IA|\*IA|\*E[12]|\s+E[12]|\s+N[12])?|D(?:\s+EX|\*EX)?|S\*?)\s+"
        r"(?P<prefix>\d+\.\d+\.\d+\.\d+(?:/\d+)?)\s+"
        r"\[(?P<ad>\d+)/(?P<metric>\d+)\]\s+via\s+(?P<nexthop>\d+\.\d+\.\d+\.\d+)"
        r"(?:,\s*(?:[0-9:]+,?\s*)?(?P<iface>[A-Za-z0-9/._-]+))?",
        re.IGNORECASE
    )

    # Multipath continuation line:
    #   [110/2] via 172.16.8.89, 00:15:21, GigabitEthernet0/0
    multipath_pattern = re.compile(
        r"^\s+\[(?P<ad>\d+)/(?P<metric>\d+)\]\s+via\s+(?P<nexthop>\d+\.\d+\.\d+\.\d+)"
        r"(?:,\s*(?:[0-9:]+,?\s*)?(?P<iface>[A-Za-z0-9/._-]+))?",
        re.IGNORECASE
    )

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("!"):
            continue

        # Check prompt for device name
        pm = prompt_pattern.match(stripped)
        if pm and not detected_device:
            detected_device = pm.group(1)

        # Check header lines to ignore
        if stripped.startswith("Codes:") or stripped.startswith("Gateway of last resort"):
            continue
        if "variably subnetted" in stripped or "is subnetted" in stripped:
            continue

        # Check Connected / Local
        cm = conn_pattern.match(line)
        if cm:
            code = cm.group("code")
            prefix = cm.group("prefix")
            iface = cm.group("iface")
            route = Route(
                network=prefix,
                protocol=code,
                ad=0,
                metric=0,
                nexthops=[{"ip": None, "interface": iface}],
                raw_text=line
            )
            routes[route.network] = route
            current_route = route
            continue

        # Check Routed via
        rm = routed_pattern.match(line)
        if rm:
            code = rm.group("code")
            prefix = rm.group("prefix")
            ad = int(rm.group("ad"))
            metric = int(rm.group("metric"))
            nexthop = rm.group("nexthop")
            iface = rm.group("iface")
            route = Route(
                network=prefix,
                protocol=code,
                ad=ad,
                metric=metric,
                nexthops=[{"ip": nexthop, "interface": iface}],
                raw_text=line
            )
            routes[route.network] = route
            current_route = route
            continue

        # Check Multipath ECMP Continuation
        mm = multipath_pattern.match(line)
        if mm and current_route:
            nexthop = mm.group("nexthop")
            iface = mm.group("iface")
            current_route.nexthops.append({"ip": nexthop, "interface": iface})
            current_route.raw_text += "\n" + line
            continue

    return detected_device, routes


def load_expected_routes_yaml(yaml_path: str) -> dict:
    """Loads expected routes from a YAML file."""
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"Expected routes YAML file not found: {yaml_path}")
    
    with open(yaml_path, "r", encoding="utf-8") as f:
        if yaml:
            data = yaml.safe_load(f)
        else:
            raise RuntimeError("PyYAML library is required to load expected routes YAML.")
            
    return data.get("devices", {})


def compare_routes(actual_routes: Dict[str, Route],
                   expected_list: List[dict],
                   ignore_unexpected: bool = False,
                   ignore_connected: bool = False) -> dict:
    """
    Compares parsed actual routes against expected route entries.
    Categorizes results into:
      - matches: list of successfully matched routes
      - missing: list of expected routes absent from actual table
      - wrong_protocol: list of routes found with unexpected protocol code
      - wrong_nexthop: list of routes with unexpected next-hop IP or interface
      - unexpected: list of routes found in table but not expected
    """
    matches = []
    missing = []
    wrong_protocol = []
    wrong_nexthop = []
    unexpected = []

    actual_checked_nets: Set[str] = set()

    for exp in expected_list:
        raw_net = exp["network"]
        exp_net = Route._canonical_network(raw_net)
        exp_proto = Route._normalize_protocol(exp["protocol"])
        exp_desc = exp.get("description", "")
        
        # Check if connected/local and filtering enabled
        if ignore_connected and exp_proto in ["C", "L"]:
            continue

        # Prepare expected next hops
        exp_nexthops = []
        if "next_hop" in exp and exp["next_hop"]:
            exp_nexthops.append(str(exp["next_hop"]).strip())
        if "next_hops" in exp and isinstance(exp["next_hops"], list):
            exp_nexthops.extend([str(h).strip() for h in exp["next_hops"]])

        exp_iface = normalize_interface(exp.get("interface"))

        # Look up in actual
        if exp_net not in actual_routes:
            missing.append({
                "network": exp_net,
                "expected_protocol": exp_proto,
                "expected_nexthop": exp_nexthops or None,
                "expected_interface": exp_iface or None,
                "description": exp_desc,
            })
            continue

        act_route = actual_routes[exp_net]
        actual_checked_nets.add(exp_net)

        # Protocol check
        if act_route.protocol != exp_proto:
            # Special case: allow S* and S to match for default route
            if not (exp_proto == "S*" and act_route.protocol in ["S*", "S"]):
                wrong_protocol.append({
                    "network": exp_net,
                    "expected_protocol": exp_proto,
                    "actual_protocol": act_route.protocol,
                    "actual_route": act_route,
                    "description": exp_desc,
                })
                continue

        # Next hop check
        nh_mismatch = False
        act_ips = act_route.get_nexthop_ips()
        act_ifaces = act_route.get_interfaces()

        if exp_nexthops:
            for enh in exp_nexthops:
                if enh not in act_ips:
                    nh_mismatch = True
                    break

        if exp_iface and not nh_mismatch:
            if exp_iface not in act_ifaces:
                nh_mismatch = True

        if nh_mismatch:
            wrong_nexthop.append({
                "network": exp_net,
                "protocol": act_route.protocol,
                "expected_nexthop": exp_nexthops or None,
                "actual_nexthop": act_ips or None,
                "expected_interface": exp_iface or None,
                "actual_interface": act_ifaces or None,
                "description": exp_desc,
            })
            continue

        # Perfect match
        matches.append({
            "network": exp_net,
            "protocol": act_route.protocol,
            "nexthops": act_route.nexthops,
            "description": exp_desc,
        })

    # Detect unexpected routes
    if not ignore_unexpected:
        for net, act_route in actual_routes.items():
            if ignore_connected and act_route.protocol in ["C", "L"]:
                continue
            if net not in actual_checked_nets:
                unexpected.append({
                    "network": net,
                    "protocol": act_route.protocol,
                    "nexthops": act_route.nexthops,
                    "raw_text": act_route.raw_text,
                })

    return {
        "matches": matches,
        "missing": missing,
        "wrong_protocol": wrong_protocol,
        "wrong_nexthop": wrong_nexthop,
        "unexpected": unexpected,
    }


def format_report(results: dict, device: str, input_path: str, yaml_path: str) -> str:
    """Formats verification findings into a human-readable CLI report."""
    missing = results["missing"]
    wrong_proto = results["wrong_protocol"]
    wrong_nh = results["wrong_nexthop"]
    unexpected = results["unexpected"]
    matches = results["matches"]

    total_issues = len(missing) + len(wrong_proto) + len(wrong_nh) + len(unexpected)
    passed = total_issues == 0

    lines = []
    lines.append("=" * 80)
    lines.append("  CISCO IOS 'SHOW IP ROUTE' AUDITOR & VERIFICATION REPORT")
    lines.append(f"  Target Device Profile: {device}")
    lines.append(f"  CLI Input File:        {input_path}")
    lines.append(f"  Expected Routes YAML:  {yaml_path}")
    lines.append("=" * 80)

    if passed:
        lines.append(f"\n[PASS] ALL ROUTES MATCH DESIGN EXPECTATIONS ({len(matches)} / {len(matches)} verified)")
        lines.append("       Zero missing, wrong-protocol, wrong-next-hop, or unexpected routes detected.")
    else:
        lines.append(f"\n[FAIL] ROUTING TABLE DEVIATIONS DETECTED ({total_issues} violation{'s' if total_issues > 1 else ''} found)\n")

        if missing:
            lines.append(f"1. MISSING ROUTES ({len(missing)} item{'s' if len(missing) > 1 else ''}):")
            for m in missing:
                exp_via = ", ".join(m["expected_nexthop"] or [])
                exp_if = f" ({m['expected_interface']})" if m["expected_interface"] else ""
                desc = f" - {m['description']}" if m["description"] else ""
                lines.append(f"   ! {m['network']:<18} Expected: [{m['expected_protocol']}] via {exp_via or 'connected'}{exp_if}{desc}")
            lines.append("")

        if wrong_proto:
            lines.append(f"2. WRONG PROTOCOL ROUTES ({len(wrong_proto)} item{'s' if len(wrong_proto) > 1 else ''}):")
            for wp in wrong_proto:
                desc = f" - {wp['description']}" if wp['description'] else ""
                lines.append(f"   ! {wp['network']:<18} Expected: [{wp['expected_protocol']}] | Found: [{wp['actual_protocol']}]{desc}")
            lines.append("")

        if wrong_nh:
            lines.append(f"3. WRONG NEXT-HOP / INTERFACE ROUTES ({len(wrong_nh)} item{'s' if len(wrong_nh) > 1 else ''}):")
            for wnh in wrong_nh:
                exp_nh = ", ".join(wnh["expected_nexthop"] or [])
                act_nh = ", ".join(wnh["actual_nexthop"] or [])
                exp_if = f" [{wnh['expected_interface']}]" if wnh["expected_interface"] else ""
                act_if = f" [{', '.join(wnh['actual_interface'] or [])}]" if wnh["actual_interface"] else ""
                desc = f" - {wnh['description']}" if wnh['description'] else ""
                lines.append(f"   ! {wnh['network']:<18} Protocol: [{wnh['protocol']}]")
                lines.append(f"       Expected Next-Hop: {exp_nh or 'connected'}{exp_if}")
                lines.append(f"       Actual Next-Hop:   {act_nh or 'connected'}{act_if}{desc}")
            lines.append("")

        if unexpected:
            lines.append(f"4. UNEXPECTED / ROGUE ROUTES ({len(unexpected)} item{'s' if len(unexpected) > 1 else ''}):")
            for u in unexpected:
                act_nhs = ", ".join([f"{nh.get('ip', 'conn')} ({nh.get('interface', '')})" for nh in u["nexthops"]])
                lines.append(f"   ! {u['network']:<18} Protocol: [{u['protocol']}] via {act_nhs}")
            lines.append("")

    lines.append("-" * 80)
    lines.append("SUMMARY STATISTICS:")
    lines.append(f"  Expected Routes Matched: {len(matches)}")
    lines.append(f"  Missing Routes:          {len(missing)}")
    lines.append(f"  Wrong Protocol Routes:   {len(wrong_proto)}")
    lines.append(f"  Wrong Next-Hop Routes:   {len(wrong_nh)}")
    lines.append(f"  Unexpected Routes:       {len(unexpected)}")
    lines.append(f"  Overall Status:          {'[PASS]' if passed else '[FAIL]'}")
    lines.append("=" * 80)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Audit Cisco Packet Tracer / Cisco IOS 'show ip route' output against expected design YAML."
    )
    parser.add_argument("input_file", nargs="?", help="Path to text file containing 'show ip route' output.")
    parser.add_argument("-d", "--device", help="Target device profile name in expected YAML (e.g. R1, R2, SW-D1).")
    parser.add_argument("-e", "--expected", default=DEFAULT_YAML_PATH, help=f"Path to expected routes YAML (default: {DEFAULT_YAML_PATH}).")
    parser.add_argument("--ignore-unexpected", action="store_true", help="Ignore unexpected routes in the actual table.")
    parser.add_argument("--ignore-connected", action="store_true", help="Ignore directly connected (C) and local (L) routes.")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format.")

    args = parser.parse_args()

    if not args.input_file:
        parser.print_help()
        sys.exit(2)

    if not os.path.exists(args.input_file):
        print(f"[ERROR] Input file does not exist: {args.input_file}", file=sys.stderr)
        sys.exit(2)

    # Read input file
    with open(args.input_file, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Parse route output
    detected_dev, actual_routes = parse_show_ip_route(raw_text)

    # Determine device
    device_name = args.device or detected_dev
    if not device_name:
        # Fallback: check filename
        base = os.path.splitext(os.path.basename(args.input_file))[0].upper()
        for cand in ["R1_FAILOVER", "R1", "R2_FAILOVER", "R2", "SW-D1", "SW-D2", "SW-D3", "SW-D4"]:
            if cand in base:
                device_name = cand
                break

    if not device_name:
        print("[ERROR] Could not auto-detect target device. Please specify with --device <DEVICE>.", file=sys.stderr)
        sys.exit(2)

    # Load YAML
    try:
        devices_data = load_expected_routes_yaml(args.expected)
    except Exception as ex:
        print(f"[ERROR] Failed to load expected YAML: {ex}", file=sys.stderr)
        sys.exit(2)

    # Resolve device profile (case-insensitive)
    matched_profile = None
    for prof in devices_data.keys():
        if prof.lower() == device_name.lower():
            matched_profile = prof
            break

    if not matched_profile:
        print(f"[ERROR] Device profile '{device_name}' not found in {args.expected}.", file=sys.stderr)
        print(f"Available device profiles: {', '.join(devices_data.keys())}", file=sys.stderr)
        sys.exit(2)

    expected_routes_list = devices_data[matched_profile].get("routes", [])

    # Perform comparison
    results = compare_routes(
        actual_routes=actual_routes,
        expected_list=expected_routes_list,
        ignore_unexpected=args.ignore_unexpected,
        ignore_connected=args.ignore_connected,
    )

    if args.json:
        out = {
            "device": matched_profile,
            "input_file": args.input_file,
            "passed": len(results["missing"]) == 0 and len(results["wrong_protocol"]) == 0 and len(results["wrong_nexthop"]) == 0 and len(results["unexpected"]) == 0,
            "matches_count": len(results["matches"]),
            "missing": results["missing"],
            "wrong_protocol": results["wrong_protocol"],
            "wrong_nexthop": results["wrong_nexthop"],
            "unexpected": results["unexpected"],
        }
        print(json.dumps(out, indent=2, default=str))
    else:
        report = format_report(results, matched_profile, args.input_file, args.expected)
        print(report)

    is_success = (len(results["missing"]) == 0 and
                  len(results["wrong_protocol"]) == 0 and
                  len(results["wrong_nexthop"]) == 0 and
                  len(results["unexpected"]) == 0)

    sys.exit(0 if is_success else 1)


if __name__ == "__main__":
    main()
