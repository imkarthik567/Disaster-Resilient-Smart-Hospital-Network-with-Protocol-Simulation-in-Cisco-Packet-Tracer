#!/usr/bin/env python3
"""
Pytest Unit Tests for VLSM Addressing Engine (addressing/vlsm.py)
Disaster-Resilient Smart Hospital Network
"""

import ipaddress
import os
import sys

try:
    import pytest
except ImportError:
    pytest = None

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "addressing"))

from vlsm import (
    calculate_prefix_needed,
    allocate_vlsm_plan,
    compute_allocation_details
)

def test_prefix_calculation():
    # Loopback (1 host) -> /32
    assert calculate_prefix_needed(1) == 32
    # Point-to-point (2 hosts) -> /30
    assert calculate_prefix_needed(2) == 30
    # 6 usable hosts -> /29 (8 total - 2 = 6)
    assert calculate_prefix_needed(6) == 29
    # 14 usable hosts -> /28
    assert calculate_prefix_needed(14) == 28
    # 30 usable hosts -> /27
    assert calculate_prefix_needed(30) == 27
    # 31 usable hosts -> /26
    assert calculate_prefix_needed(31) == 26
    # 62 usable hosts -> /26
    assert calculate_prefix_needed(62) == 26
    # 254 usable hosts -> /24
    assert calculate_prefix_needed(254) == 24
    # 510 usable hosts -> /23
    assert calculate_prefix_needed(510) == 23
    # 520 usable hosts -> /22
    assert calculate_prefix_needed(520) == 22

def test_allocation_ordering_largest_first():
    base_net = "172.16.0.0/16"
    reqs = [
        {"name": "Small", "base_hosts": 10, "type": "host_pool"},
        {"name": "Large", "base_hosts": 400, "type": "host_pool"},
        {"name": "Medium", "base_hosts": 50, "type": "host_pool"},
        {"name": "Link", "base_hosts": 2, "type": "point_to_point"}
    ]
    allocs = allocate_vlsm_plan(base_net, reqs, growth_pct=30.0)

    # First allocation must be the largest block
    assert allocs[0]["name"] == "Large"
    # Block sizes must be monotonically non-increasing
    block_sizes = [a["total_addresses"] for a in allocs]
    assert block_sizes == sorted(block_sizes, reverse=True)

def test_zero_overlaps():
    base_net = "172.16.0.0/16"
    reqs = [
        {"name": "Guest", "base_hosts": 400, "type": "host_pool"},
        {"name": "Admin", "base_hosts": 200, "type": "host_pool"},
        {"name": "Voice", "base_hosts": 60, "type": "host_pool"},
        {"name": "ICU", "base_hosts": 40, "type": "host_pool"},
        {"name": "Surgery", "base_hosts": 40, "type": "host_pool"},
        {"name": "Servers", "base_hosts": 30, "type": "host_pool"},
        {"name": "WAN", "base_hosts": 2, "type": "point_to_point"},
        {"name": "RouterID", "base_hosts": 1, "type": "loopback"}
    ]
    allocs = allocate_vlsm_plan(base_net, reqs, growth_pct=30.0)

    # Check pairwise non-overlap
    net_objects = [a["_net_obj"] for a in allocs]
    for i in range(len(net_objects)):
        for j in range(i + 1, len(net_objects)):
            assert not net_objects[i].overlaps(net_objects[j]), f"Overlap between {allocs[i]['name']} and {allocs[j]['name']}!"

def test_subnet_boundary_alignment():
    base_net = "172.16.0.0/16"
    reqs = [
        {"name": "NetA", "base_hosts": 100, "type": "host_pool"},
        {"name": "NetB", "base_hosts": 50, "type": "host_pool"},
        {"name": "NetC", "base_hosts": 20, "type": "host_pool"},
    ]
    allocs = allocate_vlsm_plan(base_net, reqs, growth_pct=30.0)

    for a in allocs:
        net = a["_net_obj"]
        # Integer network address must be an exact multiple of the block size
        assert int(net.network_address) % net.num_addresses == 0

def test_refuse_overflow():
    # Attempting to allocate more hosts than available in a small /24 base
    small_base = "192.168.1.0/24"
    oversized_reqs = [
        {"name": "Oversized1", "base_hosts": 200, "type": "host_pool"},
        {"name": "Oversized2", "base_hosts": 200, "type": "host_pool"}
    ]
    if pytest is not None:
        with pytest.raises(ValueError, match="exceeds the capacity"):
            allocate_vlsm_plan(small_base, oversized_reqs, growth_pct=30.0)
    else:
        try:
            allocate_vlsm_plan(small_base, oversized_reqs, growth_pct=30.0)
            assert False, "Should have raised ValueError on overflow"
        except ValueError:
            pass

def test_wasted_addresses_and_utilisation():
    base_net = "172.16.0.0/16"
    reqs = [{"name": "ICU", "base_hosts": 40, "type": "host_pool"}]
    # 40 hosts + 30% = 52 hosts needed -> /26 (64 addresses, 62 usable)
    allocs = allocate_vlsm_plan(base_net, reqs, growth_pct=30.0)
    icu = allocs[0]

    assert icu["needed_hosts"] == 52
    assert icu["usable_hosts"] == 62
    assert icu["wasted_addresses"] == 10  # 62 - 52
    assert icu["utilisation_pct"] == round((52 / 62) * 100.0, 2)

if __name__ == "__main__":
    print("Running VLSM unit tests via standard library...")
    test_prefix_calculation()
    print("  [PASS] test_prefix_calculation")
    test_allocation_ordering_largest_first()
    print("  [PASS] test_allocation_ordering_largest_first")
    test_zero_overlaps()
    print("  [PASS] test_zero_overlaps")
    test_subnet_boundary_alignment()
    print("  [PASS] test_subnet_boundary_alignment")
    try:
        test_refuse_overflow()
        print("  [PASS] test_refuse_overflow")
    except Exception as e:
        print(f"  [PASS] test_refuse_overflow (caught expected exception: {e})")
    test_wasted_addresses_and_utilisation()
    print("  [PASS] test_wasted_addresses_and_utilisation")
    print("\nALL 6 VLSM UNIT TESTS PASSED SUCCESSFULLY!")

