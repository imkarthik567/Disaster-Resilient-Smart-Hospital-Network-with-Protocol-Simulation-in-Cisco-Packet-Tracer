#!/usr/bin/env python3
"""
Unit Test Suite: Dynamic Routing Architecture & Verification
Validates docs/routing_design.md and sim/routing_model.py against the project
requirements and Packet Tracer 8.x emulation rules.
"""

import os
import re
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from sim.routing_model import (
    simulate_administrative_distance_failover,
    simulate_mutual_redistribution,
    simulate_abr_summarization
)

ROUTING_DESIGN_MD = os.path.join(PROJECT_ROOT, "docs", "routing_design.md")

def test_routing_model_ad_simulation():
    """Verify AD simulation correctly predicts RIB election in all 3 scenarios."""
    results = simulate_administrative_distance_failover()
    assert len(results) == 15, f"Expected 15 results, got {len(results)}"
    
    # Scenario 1 (Default): EIGRP wins
    s1 = [r for r in results if "Default Cisco Distances" in r["Scenario"]]
    for r in s1:
        assert "EIGRP" in r["RIB Winner"], f"Expected EIGRP to win in flawed default scenario: {r}"
        
    # Scenario 2 (Tuned Primary UP): OSPF wins
    s2 = [r for r in results if "Tuned Distances" in r["Scenario"] and r["Primary (Se0/0/0)"] == "UP"]
    for r in s2:
        assert "OSPF" in r["RIB Winner"], f"Expected OSPF to win in tuned primary UP scenario: {r}"
        
    # Scenario 3 (Tuned Primary DOWN): EIGRP takes over
    s3 = [r for r in results if "Primary Link DOWN" in r["Scenario"]]
    for r in s3:
        assert "EIGRP" in r["RIB Winner"], f"Expected EIGRP to take over in failover scenario: {r}"
        
    print("  [PASS] test_routing_model_ad_simulation (AD election behavior verified)")

def test_routing_model_loop_prevention():
    """Verify route tagging prevents mutual redistribution routing loops."""
    loop_with_tags, _ = simulate_mutual_redistribution(with_tagging=True)
    assert not loop_with_tags, "Routing loop incorrectly detected when tags are enabled"
    
    loop_no_tags, _ = simulate_mutual_redistribution(with_tagging=False)
    assert loop_no_tags, "Routing loop failed to be detected when tags are disabled"
    
    print("  [PASS] test_routing_model_loop_prevention (tag 110/200 filtering verified)")

def test_routing_model_abr_summarization():
    """Verify ABR route summarization reduces advertised LSAs by 50%."""
    data = simulate_abr_summarization()
    assert data["unsummarised_count"] == 6, f"Expected 6 unsummarized, got {data['unsummarised_count']}"
    assert data["summarised_count"] == 3, f"Expected 3 summarized, got {data['summarised_count']}"
    assert data["reduction_pct"] == 50.0, f"Expected 50% reduction, got {data['reduction_pct']}"
    print("  [PASS] test_routing_model_abr_summarization (50.0% LSDB reduction verified)")

def test_routing_design_document_contents():
    """Verify docs/routing_design.md contains all required technical sections and commands."""
    assert os.path.exists(ROUTING_DESIGN_MD), f"{ROUTING_DESIGN_MD} missing"
    with open(ROUTING_DESIGN_MD, "r", encoding="utf-8") as f:
        content = f.read()
        
    required_keywords = [
        r"area\s+1\s+range",
        r"distance\s+eigrp\s+120\s+170",
        r"match\s+tag\s+110",
        r"set\s+tag\s+200",
        r"ip\s+ospf\s+hello-interval\s+1",
        r"ip\s+ospf\s+dead-interval\s+4",
        r"ip\s+ospf\s+network\s+point-to-point",
        r"passive-interface\s+default",
        r"timers\s+throttle\s+spf",
        r"default-information\s+originate",
        r"ip\s+ospf\s+authentication\s+message-digest",
        r"ip\s+ospf\s+message-digest-key\s+1\s+md5",
        r"key\s+chain\s+EIGRP_AUTH",
    ]
    for pat in required_keywords:
        assert re.search(pat, content, re.IGNORECASE), f"Pattern '{pat}' missing in routing_design.md"
        
    print("  [PASS] test_routing_design_document_contents (all 13 required design sections verified)")

def run_all():
    print("Executing Dynamic Routing Design & Verification Suite...")
    test_routing_model_ad_simulation()
    test_routing_model_loop_prevention()
    test_routing_model_abr_summarization()
    test_routing_design_document_contents()
    print("\nALL 4 ROUTING DESIGN TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_all()
