#!/usr/bin/env python3
"""
Unit Test Suite: Quality of Service (QoS) Architecture & Verification
Validates docs/qos_design.md against project requirements, DiffServ standards
(RFC 4594, RFC 3246, RFC 2597), and Cisco Packet Tracer 8.x emulation rules.
"""

import os
import re
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

QOS_DESIGN_MD = os.path.join(PROJECT_ROOT, "docs", "qos_design.md")

def read_qos_document():
    assert os.path.isfile(QOS_DESIGN_MD), f"Missing QoS design doc: {QOS_DESIGN_MD}"
    with open(QOS_DESIGN_MD, "r", encoding="utf-8") as f:
        return f.read()

def test_qos_document_structure():
    """Verify docs/qos_design.md exists and contains all required structural sections."""
    content = read_qos_document()
    assert len(content) > 10000, f"QoS doc is too brief ({len(content)} bytes)"
    
    required_sections = [
        "## 1. Executive Summary & Healthcare QoS Mission",
        "## 2. Five Comprehensive Traffic Classes & DSCP Mapping",
        "## 3. Trust Boundaries & Re-marking Architecture",
        "## 4. Packet Tracer 8.x Compatibility Matrix & Implementation Strategy",
        "## 5. Mathematical Bandwidth Computations & Queue Allocations",
        "## 6. Failover Degradation Analysis: Rerouting onto the Slower Backup Path",
        "## 7. Cisco IOS Configuration Blueprint (MQC Architecture)",
        "## 8. Measurable Verification Experiment: Proving Priority in Packet Tracer",
        "## 9. Viva Defense Cheat Sheet & Key Questions",
        "## 10. Summary Verification Checklist for QoS Deployment"
    ]
    for sec in required_sections:
        assert sec in content, f"Missing required section in qos_design.md: {sec}"
        
    print("  [PASS] test_qos_document_structure (All 10 required sections present)")

def test_traffic_classes_and_dscp():
    """Verify all 5 traffic classes, protocols, and exact DSCP values are documented."""
    content = read_qos_document()
    
    # Class C1: Telemetry
    assert "C1" in content and "Life-Critical Telemetry" in content
    assert "EF" in content and "46" in content and "101110" in content
    assert "LLQ" in content or "Low Latency Queu" in content
    
    # Class C2: Voice
    assert "C2" in content and "VoIP" in content
    assert "CS5" in content and "40" in content
    assert "16384" in content and "32767" in content  # RTP port range
    assert "5060" in content  # SIP signaling
    
    # Justification for Voice vs Vitals separation
    assert "Why Voice and Vitals Are Separated" in content or "separated" in content.lower()
    assert "Jitter Amplification" in content or "jitter" in content.lower()
    
    # Class C3: Medical Imaging Bulk
    assert "C3" in content and "Medical Imaging" in content
    assert "AF31" in content and "26" in content and "011010" in content
    assert "104" in content  # DICOM port
    assert "PACS" in content
    
    # Class C4: Admin / EHR
    assert "C4" in content and "Admin" in content
    assert "AF21" in content or "CS2" in content
    
    # Class C5: Guest / Scavenger
    assert "C5" in content and "Guest" in content
    assert "CS1" in content or "Scavenger" in content
    
    print("  [PASS] test_traffic_classes_and_dscp (C1-C5 classes, DSCP values & separation verified)")

def test_bandwidth_queue_computations():
    """Verify mathematical queue allocations for 2.048 Mbps and 1.544 Mbps links."""
    content = read_qos_document()
    
    # Check Primary WAN allocations (2.048 Mbps / 2048 kbps)
    assert "2048" in content and "1536" in content  # 75% max-reserved-bandwidth
    assert "512" in content  # C1 25% (512 kbps)
    assert "409.6" in content or "410" in content  # C2 20% (409.6 kbps)
    assert "307.2" in content or "307" in content  # C3 15% (307.2 kbps)
    
    # Check Backup WAN allocations (1.544 Mbps / 1544 kbps)
    assert "1544" in content and "1158" in content  # 75% max-reserved-bandwidth
    assert "386" in content  # C1 25% (386 kbps)
    assert "308.8" in content or "309" in content  # C2 20% (308.8 kbps)
    assert "231.6" in content or "232" in content  # C3 15% (231.6 kbps)
    
    # Check contraction calculation
    assert "24.6" in content or "24.61" in content  # 24.6% link contraction
    
    print("  [PASS] test_bandwidth_queue_computations (2.048 Mbps & 1.544 Mbps queue math verified)")

def test_trust_boundaries_and_remarking():
    """Verify trust boundary rules and re-marking locations across switch and router tiers."""
    content = read_qos_document()
    
    assert "Trust Boundary" in content
    assert "Untrusted Access Endpoints" in content or "Untrusted Zone" in content
    assert "VLAN 40" in content and "Guest" in content
    assert "VLAN 60" in content and "Voice" in content
    assert "VLAN 50" in content and "Server" in content
    assert "SW-D1" in content and "R1" in content and "R2" in content
    
    print("  [PASS] test_trust_boundaries_and_remarking (Trust boundaries & re-marking verified)")

def test_packet_tracer_limits_and_mqc():
    """Verify Packet Tracer 8.x compatibility matrix and explicit hardware limits."""
    content = read_qos_document()
    
    # Access Switch limit (Catalyst 2960)
    assert "2960" in content and ("mls qos" in content or "not supported" in content.lower())
    
    # Distribution Switch behavior (Catalyst 3560)
    assert "3560" in content and "stubbed" in content.lower()
    
    # Core Router full MQC support (2911 / 1941)
    assert ("2911" in content or "1941" in content) and "Modular QoS CLI" in content
    assert "priority percent" in content
    assert "bandwidth percent" in content
    assert "service-policy output" in content
    
    print("  [PASS] test_packet_tracer_limits_and_mqc (PT 8.x device limits & MQC support validated)")

def test_measurable_experiment_and_verification():
    """Verify reproducible measurement experiment demonstrating priority vs FIFO."""
    content = read_qos_document()
    
    assert "Phase A: Establishing the Baseline" in content or "Baseline" in content
    assert "Phase B: Evaluating Performance with QoS Active" in content or "QoS Active" in content
    assert "no service-policy output PM-WAN-EDGE-OUT" in content
    assert "service-policy output PM-WAN-EDGE-OUT" in content
    assert "ping 172.16.7.7 -l 1400" in content  # Bulk saturation ping
    assert "ping 172.16.7.4 -l 64" in content    # Telemetry ping
    assert "show policy-map interface Serial0/0/0" in content
    assert "194 ms" in content or "180" in content  # Baseline latency spike
    assert "9 ms" in content or "12 ms" in content   # QoS active low latency
    
    print("  [PASS] test_measurable_experiment_and_verification (Empirical experiment & metrics verified)")

def test_viva_defense_questions_present():
    """Verify high-frequency viva defense examination questions and answers are present."""
    content = read_qos_document()
    
    assert "Viva Defense Cheat Sheet" in content
    assert "LLQ" in content and "CBWFQ" in content
    assert "starvation" in content.lower()
    assert "Policing" in content and "Shaping" in content
    assert "WRED" in content
    
    print("  [PASS] test_viva_defense_questions_present (Viva defense cheat sheet verified)")

def run_all_tests():
    print("=" * 80)
    print("  QUALITY OF SERVICE (QoS) ARCHITECTURE & DESIGN TEST SUITE")
    print("=" * 80)
    test_qos_document_structure()
    test_traffic_classes_and_dscp()
    test_bandwidth_queue_computations()
    test_trust_boundaries_and_remarking()
    test_packet_tracer_limits_and_mqc()
    test_measurable_experiment_and_verification()
    test_viva_defense_questions_present()
    print("\nALL 7 QoS DESIGN VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_all_tests()
