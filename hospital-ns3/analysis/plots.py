#!/usr/bin/env python3
"""
================================================================================
analysis/plots.py - Standardized Publication Chart Styling & Rendering Module
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
SCOPE, VIT Vellore
================================================================================
Ensures consistent visual design across all seven simulation experiments:
  - Labelled axes with explicit physical units [kbps, ms, %, bytes]
  - 95% Confidence Interval error bars
  - High-contrast, colorblind-friendly academic palettes
  - Simultaneous 300 DPI raster PNG and vector PDF exports
  - Standardized naming convention: <exp_id>_<metric_name>.[png|pdf]
================================================================================
"""

import os
from typing import List, Dict, Any, Optional, Tuple, Sequence
import numpy as np
import matplotlib.pyplot as plt


# Consistent color palette for clinical traffic classes
CLASS_COLORS = {
    "ICU": "#d62728",       # Crimson Red (Critical Life Safety)
    "VOICE": "#2ca02c",     # Forest Green (VoIP Telephony)
    "IMAGING": "#1f77b4",   # Steel Blue (Bulk DICOM PACS)
    "ADMIN": "#9467bd",     # Muted Purple (Hospital Web/EHR)
    "GUEST": "#ff7f0e",     # Amber Orange (Untrusted Public)
    "ATTACK": "#8c564b",    # Dark Brown/Maroon (Malicious)
    "PROBE": "#17becf"      # Cyan (Continuous Diagnostic Probe)
}


def apply_publication_style():
    """Applies clean, uniform matplotlib parameters for academic reports."""
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.labelweight": "bold",
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 9,
        "legend.frameon": True,
        "legend.framealpha": 0.85,
        "figure.titlesize": 13,
        "figure.titleweight": "bold",
        "grid.linestyle": "--",
        "grid.alpha": 0.6,
        "lines.linewidth": 2.0,
        "lines.markersize": 6.5,
        "savefig.dpi": 300,
        "savefig.bbox": "tight"
    })


def save_figure(fig: plt.Figure, output_dir: str, exp_id: str, plot_name: str) -> Tuple[str, str]:
    """Saves figure in both PNG (300 DPI) and PDF vector format with standardized filenames."""
    os.makedirs(output_dir, exist_ok=True)
    base_name = f"{exp_id}_{plot_name}".lower().replace(" ", "_").replace("-", "_")
    png_path = os.path.join(output_dir, f"{base_name}.png")
    pdf_path = os.path.join(output_dir, f"{base_name}.pdf")

    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Saved: {png_path} and {pdf_path}")
    return png_path, pdf_path


def plot_bar_with_error(categories: Sequence[str],
                        means: Sequence[float],
                        errors: Sequence[float],
                        title: str,
                        ylabel: str,
                        output_dir: str,
                        exp_id: str,
                        plot_name: str,
                        xlabel: str = "",
                        colors: Optional[Sequence[str]] = None,
                        baseline_val: Optional[float] = None,
                        baseline_label: str = "Baseline") -> Tuple[str, str]:
    """Renders a publication bar chart with error bars and value labels."""
    apply_publication_style()
    fig, ax = plt.subplots(figsize=(8.5, 5))

    bar_colors = colors if colors else ["#1f77b4"] * len(categories)
    x = np.arange(len(categories))
    width = 0.5

    bars = ax.bar(x, means, width, yerr=errors, capsize=5, color=bar_colors, alpha=0.88, edgecolor="black")

    if baseline_val is not None:
        ax.axhline(y=baseline_val, color="gray", linestyle=":", linewidth=1.8, label=baseline_label)

    # Value text labels on top of bars
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, h + 0.02 * max(means),
                f"{h:.2f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    if xlabel:
        ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(f"{exp_id.upper()}: {title}")
    if baseline_val is not None:
        ax.legend(loc="upper right")

    return save_figure(fig, output_dir, exp_id, plot_name)


def plot_line_sweep(x_values: Sequence[float],
                    series_dict: Dict[str, Tuple[Sequence[float], Sequence[float]]],
                    title: str,
                    xlabel: str,
                    ylabel: str,
                    output_dir: str,
                    exp_id: str,
                    plot_name: str,
                    threshold_val: Optional[float] = None,
                    threshold_label: str = "Limit",
                    log_y: bool = False) -> Tuple[str, str]:
    """
    Renders multi-line parameter sweep plot with error bars or shaded confidence regions.
    series_dict format: {series_name: (mean_values, error_values)}
    """
    apply_publication_style()
    fig, ax = plt.subplots(figsize=(9, 5.5))

    styles = ["-o", "-s", "-^", "-D", "-v", "-P"]
    for idx, (label, (y_means, y_errs)) in enumerate(series_dict.items()):
        color = CLASS_COLORS.get(label.upper(), None)
        fmt = styles[idx % len(styles)]
        ax.errorbar(x_values, y_means, yerr=y_errs, fmt=fmt, color=color,
                    linewidth=2.0, capsize=4, label=label)

    if threshold_val is not None:
        ax.axhline(y=threshold_val, color="black", linestyle="--", linewidth=1.5, label=threshold_label)

    if log_y:
        ax.set_yscale("log")

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(f"{exp_id.upper()}: {title}")
    ax.legend(loc="best")

    return save_figure(fig, output_dir, exp_id, plot_name)
