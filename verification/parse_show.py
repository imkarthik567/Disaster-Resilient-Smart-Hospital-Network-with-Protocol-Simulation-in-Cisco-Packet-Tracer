#!/usr/bin/env python3
"""
================================================================================
Cisco IOS Show-Command Output Parser
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Parses raw terminal show command outputs from Cisco IOS / Packet Tracer into
structured JSON and Python dictionaries.

Supported show commands:
  1. show ip interface brief
  2. show vlan brief
  3. show ip ospf neighbor
  4. show standby brief
  5. show access-lists
================================================================================
"""

import sys
import re
import json
import argparse
from typing import List, Dict, Any, Optional


def parse_show_ip_interface_brief(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parses 'show ip interface brief' output.
    Header format:
    Interface              IP-Address      OK? Method Status                Protocol
    FastEthernet0/1        unassigned      YES manual up                    up
    """
    results = []
    lines = raw_text.strip().splitlines()
    header_found = False

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        if re.search(r"Interface\s+IP-Address", line, re.I):
            header_found = True
            continue

        if not header_found:
            # Check if this line looks like an interface row directly
            if not re.match(r"^(?:[A-Za-z]+[\d/\.:]+|Vlan\d+|Loopback\d+|Tunnel\d+)", line_clean):
                continue

        # Cisco IOS interface brief line:
        # e.g.: GigabitEthernet0/0  172.16.8.98  YES NVRAM  up  up
        # e.g.: FastEthernet0/24   unassigned    YES unset  administratively down down
        m = re.match(
            r"^(\S+)\s+(\d+\.\d+\.\d+\.\d+|unassigned)\s+(\S+)\s+(\S+)\s+(administratively down|up|down)\s+(up|down)",
            line_clean,
            re.I
        )
        if m:
            results.append({
                "interface": m.group(1),
                "ip_address": None if m.group(2).lower() == "unassigned" else m.group(2),
                "ok": m.group(3).upper() == "YES",
                "method": m.group(4),
                "status": m.group(5).lower(),
                "protocol": m.group(6).lower()
            })
    return results


def parse_show_vlan_brief(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parses 'show vlan brief' output. Handles multi-line wrapped port lists.
    Format:
    VLAN Name                             Status    Ports
    ---- -------------------------------- --------- -------------------------------
    1    default                          active    Fa0/1, Fa0/2, Fa0/3, Fa0/4
                                                    Fa0/5, Fa0/6
    10   ICU_TELEMETRY                    active    Fa0/1, Fa0/2
    """
    results = []
    lines = raw_text.strip().splitlines()
    current_vlan = None

    for line in lines:
        line_str = line.rstrip()
        if not line_str or line_str.startswith("----") or "VLAN Name" in line_str:
            continue

        # Check if line starts with a numeric VLAN ID
        m = re.match(r"^\s*(\d+)\s+(\S+)\s+(active|act/unsup|suspend)\s*(.*)$", line_str, re.I)
        if m:
            if current_vlan:
                results.append(current_vlan)

            vlan_id = int(m.group(1))
            name = m.group(2)
            status = m.group(3).lower()
            ports_str = m.group(4).strip()
            ports = [p.strip() for p in ports_str.split(",") if p.strip()] if ports_str else []

            current_vlan = {
                "vlan_id": vlan_id,
                "name": name,
                "status": status,
                "ports": ports
            }
        elif current_vlan is not None:
            # Continuation line of ports: e.g. "                               Fa0/5, Fa0/6"
            cont_ports = [p.strip() for p in line_str.split(",") if p.strip()]
            # Filter out non-port tokens
            valid_ports = [p for p in cont_ports if re.match(r"^[A-Za-z]+[\d/]+$", p)]
            if valid_ports:
                current_vlan["ports"].extend(valid_ports)

    if current_vlan:
        results.append(current_vlan)

    return results


def parse_show_ip_ospf_neighbor(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parses 'show ip ospf neighbor' output.
    Format:
    Neighbor ID     Pri   State           Dead Time   Address         Interface
    172.16.8.106      1   FULL/BDR        00:00:34    172.16.8.98     GigabitEthernet0/1
    172.16.8.107      1   FULL/  -        00:00:31    172.16.8.82     Serial0/0/0
    """
    results = []
    lines = raw_text.strip().splitlines()

    for line in lines:
        line_clean = line.strip()
        if not line_clean or "Neighbor ID" in line_clean or line_clean.startswith("----"):
            continue

        # Match neighbor line (handles FULL/-, FULL/  -, FULL/DR, etc.)
        m = re.match(
            r"^(\d+\.\d+\.\d+\.\d+)\s+(\d+)\s+(.+?)\s+(\d{2}:\d{2}:\d{2})\s+(\d+\.\d+\.\d+\.\d+)\s+(\S+)$",
            line_clean
        )
        if m:
            state_raw = m.group(3)
            # Separate state and role (e.g. FULL/DR, FULL/BDR, FULL/-)
            state_parts = [p.strip() for p in state_raw.split("/")]
            state = state_parts[0]
            role = state_parts[1] if len(state_parts) > 1 else None
            if role == "-":
                role = "POINT_TO_POINT"

            results.append({
                "neighbor_id": m.group(1),
                "priority": int(m.group(2)),
                "state": state,
                "role": role,
                "dead_time": m.group(4),
                "address": m.group(5),
                "interface": m.group(6)
            })
    return results


def parse_show_standby_brief(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parses 'show standby brief' output.
    Format:
    Interface   Grp  Pri P State   Active          Standby         Virtual IP
    Vl10        10   120 P Active  local           172.16.8.35     172.16.8.33
    Vl20        20   110   Standby 172.16.8.49     local           172.16.8.49
    """
    results = []
    lines = raw_text.strip().splitlines()

    for line in lines:
        line_clean = line.strip()
        if not line_clean or "Interface" in line_clean and "Grp" in line_clean:
            continue

        # P (Preempt) is optional or may be a single char 'P' or ' '
        # Regex captures: Interface, Grp, Pri, optional P, State, Active, Standby, Virtual IP
        m = re.match(
            r"^(\S+)\s+(\d+)\s+(\d+)\s+([P\s]?)\s*(Active|Standby|Speak|Listen|Init)\s+(\S+)\s+(\S+)\s+(\d+\.\d+\.\d+\.\d+|unknown)$",
            line_clean,
            re.I
        )
        if m:
            preempt = m.group(4).strip().upper() == "P"
            results.append({
                "interface": m.group(1),
                "group": int(m.group(2)),
                "priority": int(m.group(3)),
                "preempt": preempt,
                "state": m.group(5).capitalize(),
                "active": m.group(6),
                "standby": m.group(7),
                "virtual_ip": m.group(8)
            })
    return results


def parse_show_access_lists(raw_text: str) -> Dict[str, Dict[str, Any]]:
    """
    Parses 'show access-lists' output.
    Format:
    Standard IP access list 10
        10 permit 172.16.8.64 0.0.0.15 (14 matches)
        20 deny any (5 matches)
    Extended IP access list ACL-CLINIC-INSPECT
        10 permit tcp any any established (1284 matches)
        20 permit udp host 172.16.1.10 host 172.16.5.10 eq 5004 (482 matches)
        30 deny ip any any (12 matches)
    """
    acls: Dict[str, Dict[str, Any]] = {}
    lines = raw_text.strip().splitlines()
    current_acl = None

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        # Detect ACL Header: '(Standard|Extended) IP access list <name>'
        header_match = re.match(r"^(Standard|Extended)\s+IP\s+access\s+list\s+(\S+)", line_clean, re.I)
        if header_match:
            acl_type = header_match.group(1).capitalize()
            acl_name = header_match.group(2)
            current_acl = acl_name
            acls[acl_name] = {
                "name": acl_name,
                "type": f"{acl_type} IP",
                "rules": []
            }
            continue

        if current_acl and current_acl in acls:
            # Rule entry, e.g. "10 permit tcp any any eq 80 (5 matches)" or "permit udp 172.16.0.0 0.0.255.255 any"
            # Sequence number optional
            rule_match = re.match(r"^(?:(\d+)\s+)?(permit|deny)\s+(.*?)(?:\s+\((\d+)\s+matches\))?$", line_clean, re.I)
            if rule_match:
                seq = int(rule_match.group(1)) if rule_match.group(1) else None
                action = rule_match.group(2).lower()
                body = rule_match.group(3).strip()
                matches = int(rule_match.group(4)) if rule_match.group(4) else 0

                # Extract protocol if extended
                body_tokens = body.split()
                protocol = body_tokens[0] if acls[current_acl]["type"].startswith("Extended") and body_tokens else "ip"

                acls[current_acl]["rules"].append({
                    "sequence": seq,
                    "action": action,
                    "protocol": protocol,
                    "rule_text": f"{action} {body}",
                    "matches": matches
                })

    return acls


def parse_show_output(command: str, raw_text: str) -> Any:
    """Dispatches show command text to the appropriate parser."""
    cmd_norm = command.lower().strip()

    if "ip" in cmd_norm and "int" in cmd_norm and "br" in cmd_norm:
        return parse_show_ip_interface_brief(raw_text)
    elif "vlan" in cmd_norm and "br" in cmd_norm:
        return parse_show_vlan_brief(raw_text)
    elif "ospf" in cmd_norm and "neigh" in cmd_norm:
        return parse_show_ip_ospf_neighbor(raw_text)
    elif "standby" in cmd_norm:
        return parse_show_standby_brief(raw_text)
    elif "access-list" in cmd_norm or "access-lists" in cmd_norm:
        return parse_show_access_lists(raw_text)
    else:
        raise ValueError(
            f"Unsupported command '{command}'. Supported: 'show ip int brief', 'show vlan brief', "
            f"'show ip ospf neighbor', 'show standby brief', 'show access-lists'"
        )


def main():
    parser = argparse.ArgumentParser(description="Parse Cisco IOS show commands to JSON.")
    parser.add_argument("--command", "-c", required=True, help="Command name (e.g. 'show ip int brief')")
    parser.add_argument("--input", "-i", help="Path to input text file containing output (reads stdin if omitted)")
    parser.add_argument("--pretty", action="store_true", default=True, help="Pretty print JSON")
    args = parser.parse_args()

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            raw_text = f.read()
    else:
        raw_text = sys.stdin.read()

    try:
        parsed = parse_show_output(args.command, raw_text)
        indent = 2 if args.pretty else None
        print(json.dumps(parsed, indent=indent))
    except Exception as e:
        print(f"Error parsing output: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
