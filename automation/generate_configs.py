#!/usr/bin/env python3
"""
================================================================================
Infrastructure-as-Code (IaC) Configuration Generator Pipeline
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
VIT Vellore — Computer Networks Project
================================================================================
Renders production-ready, hardened Cisco IOS configurations from a single YAML
Source of Truth (SSOT) using Jinja2 templates.
================================================================================
"""

import os
import sys
import yaml
import jinja2

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AUTOMATION_DIR = os.path.join(PROJECT_ROOT, "automation")
TEMPLATES_DIR = os.path.join(AUTOMATION_DIR, "templates")
SSOT_YAML = os.path.join(AUTOMATION_DIR, "network_source_of_truth.yaml")
GENERATED_DIR = os.path.join(AUTOMATION_DIR, "generated_configs")


def render_all_configs(ssot_path: str = SSOT_YAML, out_dir: str = GENERATED_DIR) -> int:
    """Renders all device configurations from YAML SSOT."""
    if not os.path.exists(ssot_path):
        raise FileNotFoundError(f"Source of Truth YAML file not found: {ssot_path}")

    with open(ssot_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    os.makedirs(out_dir, exist_ok=True)
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
        trim_blocks=True,
        lstrip_blocks=True
    )

    templates = {
        "router": env.get_template("router.j2"),
        "distribution_switch": env.get_template("distribution_switch.j2"),
        "access_switch": env.get_template("access_switch.j2")
    }

    count = 0
    print("=" * 80)
    print("NETDEVOPS CONFIGURATION GENERATION PIPELINE (JINJA2 + YAML SSOT)")
    print(f"Source of Truth: {ssot_path}")
    print(f"Output Directory: {out_dir}")
    print("=" * 80)

    for dev in data.get("devices", []):
        dev_name = dev["name"]
        dev_type = dev["type"]

        if dev_type not in templates:
            print(f"[SKIP] Unknown device type '{dev_type}' for {dev_name}")
            continue

        template = templates[dev_type]
        rendered = template.render({
            "dev": dev,
            "global": data.get("global", {}),
            "vlans": data.get("vlans", [])
        })

        out_file = os.path.join(out_dir, f"{dev_name}.cfg")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(rendered.strip() + "\n")

        print(f"  [RENDERED] {dev_name:10s} ({dev_type:20s}) -> {out_file}")
        count += 1

    print("=" * 80)
    print(f"SUCCESS: {count} configurations successfully generated from SSOT.")
    print("=" * 80)
    return count


def main():
    render_all_configs()


if __name__ == "__main__":
    main()
