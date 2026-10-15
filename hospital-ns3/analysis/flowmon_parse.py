#!/usr/bin/env python3
"""
================================================================================
analysis/flowmon_parse.py - Universal NS-3 FlowMonitor XML Parser & Classifier
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
SCOPE, VIT Vellore
================================================================================
Parses any NS-3 FlowMonitor XML export into a clean, tidy CSV.
Classifies each network flow into its clinical traffic class:
  - ICU      : ICU vital telemetry (UDP, 200B, Port 5001/2100, Subnet 172.16.7.128/26)
  - VOICE    : Clinical VoIP SIP/RTP (UDP, 160B/20ms, Port 5060/6000, Subnet 172.16.6.0/25)
  - IMAGING  : Medical DICOM PACS bulk transfer (TCP, Port 104/8080/9000, Subnet 172.16.7.64/26)
  - ADMIN    : Hospital EHR & Reception Web (TCP, Port 80/443, Subnet 172.16.4.0/23, 172.16.8.0/27)
  - GUEST    : Untrusted public Wi-Fi (Subnet 172.16.0.0/22, Best Effort)
  - ATTACK   : Malicious UDP flood / stealth scan from compromised guest nodes
  - PROBE    : Continuous resilience probe (UDP, 10 Hz, Port 5001)
================================================================================
"""

import os
import sys
import argparse
import ipaddress
import xml.etree.ElementTree as ET
import pandas as pd


# ------------------------------------------------------------------------------
# Hospital VLSM Addressing & Subnet Definitions
# ------------------------------------------------------------------------------
SUBNET_SERVER   = ipaddress.ip_network("172.16.7.0/26")
SUBNET_ICU      = ipaddress.ip_network("172.16.7.128/26")
SUBNET_SURGERY  = ipaddress.ip_network("172.16.7.64/26")
SUBNET_ADMIN    = ipaddress.ip_network("172.16.4.0/23")
SUBNET_VOICE    = ipaddress.ip_network("172.16.6.0/25")
SUBNET_GUEST    = ipaddress.ip_network("172.16.0.0/22")

# Remote Clinic Subnets
SUBNET_CLINIC_ADMIN   = ipaddress.ip_network("172.16.8.0/27")
SUBNET_CLINIC_TRIAGE  = ipaddress.ip_network("172.16.8.32/27")
SUBNET_CLINIC_VOICE   = ipaddress.ip_network("172.16.7.224/27")
SUBNET_CLINIC_GUEST   = ipaddress.ip_network("172.16.6.128/25")

# WAN Point-to-Point Transit Subnets
SUBNET_PRIMARY_WAN = ipaddress.ip_network("172.16.8.80/30")
SUBNET_BACKUP_WAN  = ipaddress.ip_network("172.16.8.84/30")


def classify_flow(src_ip_str: str, src_port: int, dst_ip_str: str, dst_port: int, proto: int) -> str:
    """Classifies a flow into a clinical traffic category based on IPs, ports, and transport protocol."""
    try:
        src_ip = ipaddress.ip_address(src_ip_str)
        dst_ip = ipaddress.ip_address(dst_ip_str)
    except ValueError:
        return "OTHER"

    # Attack traffic identification
    if dst_port in [4444, 9999] or (dst_port >= 30000 and dst_port <= 30010):
        return "ATTACK"
    if src_ip in SUBNET_GUEST and dst_ip in SUBNET_ICU:
        return "ATTACK" # Unauthorized guest traversal into clinical ICU zone

    # ICU Telemetry & Health Monitoring
    if dst_port in [5001, 2100] or src_port in [5001, 2100]:
        if src_ip in SUBNET_ICU or dst_ip in SUBNET_ICU or src_ip in SUBNET_CLINIC_TRIAGE or dst_ip in SUBNET_CLINIC_TRIAGE:
            return "ICU"
        return "PROBE"

    # Clinical Voice VoIP (SIP 5060, RTP 6000+)
    if dst_port in [5060, 6000] or src_port in [5060, 6000]:
        return "VOICE"
    if src_ip in SUBNET_VOICE or dst_ip in SUBNET_VOICE or src_ip in SUBNET_CLINIC_VOICE or dst_ip in SUBNET_CLINIC_VOICE:
        if proto == 17: # UDP
            return "VOICE"

    # Radiology PACS DICOM Medical Imaging (TCP Bulk)
    if dst_port in [104, 8080, 9000] or src_port in [104, 8080, 9000]:
        if proto == 6: # TCP
            if src_ip in SUBNET_SURGERY or dst_ip in SUBNET_SURGERY or src_ip in SUBNET_CLINIC_TRIAGE or dst_ip in SUBNET_CLINIC_TRIAGE:
                return "IMAGING"

    # Hospital Administration & Web Queries (HTTP/HTTPS)
    if dst_port in [80, 443, 8000] or src_port in [80, 443, 8000]:
        if src_ip in SUBNET_ADMIN or dst_ip in SUBNET_ADMIN or src_ip in SUBNET_CLINIC_ADMIN or dst_ip in SUBNET_CLINIC_ADMIN:
            return "ADMIN"

    # Guest Wi-Fi Scavenger Traffic
    if src_ip in SUBNET_GUEST or dst_ip in SUBNET_GUEST or src_ip in SUBNET_CLINIC_GUEST or dst_ip in SUBNET_CLINIC_GUEST:
        return "GUEST"

    # Default fallback by port
    if proto == 17:
        return "ICU" if dst_port == 5001 else "GUEST"
    elif proto == 6:
        return "IMAGING" if dst_port in [104, 8080] else "ADMIN"

    return "OTHER"


def parse_flowmon_xml(xml_path: str, exp_id: str = "EXP", seed: int = 1) -> pd.DataFrame:
    """Parses a FlowMonitor XML file and returns a structured pandas DataFrame."""
    if not os.path.exists(xml_path):
        raise FileNotFoundError(f"FlowMonitor XML file not found: {xml_path}")

    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Flow Classifier mapping: FlowId -> (src_ip, src_port, dst_ip, dst_port, proto)
    flow_classifier = {}
    classifier_elem = root.find("Ipv4FlowClassifier")
    if classifier_elem is not None:
        for flow in classifier_elem.findall("Flow"):
            flow_id = int(flow.attrib["flowId"])
            src_ip = flow.attrib.get("sourceAddress", "")
            src_port = int(flow.attrib.get("sourcePort", 0))
            dst_ip = flow.attrib.get("destinationAddress", "")
            dst_port = int(flow.attrib.get("destinationPort", 0))
            proto = int(flow.attrib.get("protocol", 0))
            flow_classifier[flow_id] = (src_ip, src_port, dst_ip, dst_port, proto)

    # Parse FlowStats: FlowId -> metrics
    records = []
    flow_stats_elem = root.find("FlowStats")
    if flow_stats_elem is not None:
        for flow in flow_stats_elem.findall("Flow"):
            flow_id = int(flow.attrib["flowId"])
            tx_pkts = int(flow.attrib.get("txPackets", 0))
            rx_pkts = int(flow.attrib.get("rxPackets", 0))
            lost_pkts = int(flow.attrib.get("lostPackets", 0))
            tx_bytes = int(flow.attrib.get("txBytes", 0))
            rx_bytes = int(flow.attrib.get("rxBytes", 0))

            # Timestamps (in nanoseconds)
            time_first_tx = float(flow.attrib.get("timeFirstTxPacket", "0ns").replace("ns", "")) / 1e9
            time_last_rx = float(flow.attrib.get("timeLastRxPacket", "0ns").replace("ns", "")) / 1e9
            duration = max(0.001, time_last_rx - time_first_tx)

            # Delay & Jitter
            delay_sum_ns = float(flow.attrib.get("delaySum", "0ns").replace("ns", ""))
            jitter_sum_ns = float(flow.attrib.get("jitterSum", "0ns").replace("ns", ""))

            mean_delay_ms = (delay_sum_ns / (rx_pkts * 1e6)) if rx_pkts > 0 else 0.0
            mean_jitter_ms = (jitter_sum_ns / (rx_pkts * 1e6)) if rx_pkts > 0 else 0.0

            # Approximation for p95 delay when histogram not enabled:
            p95_delay_ms = mean_delay_ms * 1.25

            # Throughput & Goodput (kbps)
            th_kbps = (rx_bytes * 8.0) / (duration * 1000.0) if rx_pkts > 0 else 0.0
            # Goodput (excluding estimated 28B TCP/IP or 28B UDP/IP headers):
            header_overhead = rx_pkts * 28.0
            goodput_bytes = max(0.0, rx_bytes - header_overhead)
            goodput_kbps = (goodput_bytes * 8.0) / (duration * 1000.0) if rx_pkts > 0 else 0.0

            loss_ratio = (lost_pkts / (tx_pkts + 1e-9)) if tx_pkts > 0 else 0.0

            # Classifier lookup
            if flow_id in flow_classifier:
                src_ip, src_port, dst_ip, dst_port, proto = flow_classifier[flow_id]
            else:
                src_ip, src_port, dst_ip, dst_port, proto = ("0.0.0.0", 0, "0.0.0.0", 0, 0)

            traffic_class = classify_flow(src_ip, src_port, dst_ip, dst_port, proto)

            records.append({
                "experiment": exp_id,
                "seed": seed,
                "flow_id": flow_id,
                "source_ip": src_ip,
                "source_port": src_port,
                "dest_ip": dst_ip,
                "dest_port": dst_port,
                "protocol": "TCP" if proto == 6 else ("UDP" if proto == 17 else str(proto)),
                "traffic_class": traffic_class,
                "tx_packets": tx_pkts,
                "rx_packets": rx_pkts,
                "lost_packets": lost_pkts,
                "packet_loss_ratio": round(loss_ratio, 6),
                "tx_bytes": tx_bytes,
                "rx_bytes": rx_bytes,
                "throughput_kbps": round(th_kbps, 2),
                "goodput_kbps": round(goodput_kbps, 2),
                "mean_delay_ms": round(mean_delay_ms, 3),
                "p95_delay_ms": round(p95_delay_ms, 3),
                "mean_jitter_ms": round(mean_jitter_ms, 3)
            })

    return pd.DataFrame(records)


def main():
    parser = argparse.ArgumentParser(description="Convert NS-3 FlowMonitor XML into tidy classified CSV.")
    parser.add_argument("xml_file", help="Input FlowMonitor XML path")
    parser.add_argument("-o", "--out-csv", default="", help="Output CSV path (default: <xml_file>.csv)")
    parser.add_argument("--exp-id", default="EXP", help="Experiment identifier")
    parser.add_argument("--seed", type=int, default=1, help="RNG Seed number")
    args = parser.parse_args()

    out_csv = args.out_csv if args.out_csv else os.path.splitext(args.xml_file)[0] + ".csv"
    os.makedirs(os.path.dirname(os.path.abspath(out_csv)), exist_ok=True)

    df = parse_flowmon_xml(args.xml_file, exp_id=args.exp_id, seed=args.seed)
    df.to_csv(out_csv, index=False)
    print(f"[OK] Parsed {len(df)} flows -> {out_csv}")


if __name__ == "__main__":
    main()
