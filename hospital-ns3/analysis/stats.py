#!/usr/bin/env python3
"""
================================================================================
analysis/stats.py - Rigorous Statistical Analysis & Hypothesis Testing Module
Disaster-Resilient Smart Hospital Network
Team: Rohit Kathiravan (24BCE0441), Karthikeyan S (24BCT0332)
SCOPE, VIT Vellore
================================================================================
Provides scientific statistical primitives:
  - Sample Mean & Sample Standard Deviation
  - 95% Confidence Interval using Student's t-distribution
  - Welch's t-test (two-sample unequal variances)
  - Cohen's d & Hedges' g Effect Sizes
================================================================================
"""

import math
from typing import Tuple, Dict, Any, Sequence
import numpy as np
from scipy import stats


def calculate_summary_statistics(data: Sequence[float]) -> Dict[str, float]:
    """
    Computes comprehensive sample statistics including mean, standard deviation,
    min, max, median, standard error, and 95% confidence interval using Student's t-distribution.
    """
    arr = np.asarray(data, dtype=float)
    arr = arr[~np.isnan(arr)]
    n = len(arr)

    if n == 0:
        return {
            "n": 0, "mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0,
            "median": 0.0, "sem": 0.0, "ci_95_low": 0.0, "ci_95_high": 0.0, "ci_margin": 0.0
        }

    mean_val = float(np.mean(arr))
    if n == 1:
        return {
            "n": 1, "mean": mean_val, "std": 0.0, "min": mean_val, "max": mean_val,
            "median": mean_val, "sem": 0.0, "ci_95_low": mean_val, "ci_95_high": mean_val, "ci_margin": 0.0
        }

    std_val = float(np.std(arr, ddof=1)) # Sample standard deviation (ddof=1)
    min_val = float(np.min(arr))
    max_val = float(np.max(arr))
    med_val = float(np.median(arr))
    sem_val = std_val / math.sqrt(n)

    # 95% Confidence Interval via Student's t-distribution
    t_critical = float(stats.t.ppf(0.975, df=n - 1))
    margin = t_critical * sem_val
    ci_low = mean_val - margin
    ci_high = mean_val + margin

    return {
        "n": n,
        "mean": round(mean_val, 4),
        "std": round(std_val, 4),
        "min": round(min_val, 4),
        "max": round(max_val, 4),
        "median": round(med_val, 4),
        "sem": round(sem_val, 4),
        "ci_95_low": round(ci_low, 4),
        "ci_95_high": round(ci_high, 4),
        "ci_low": round(ci_low, 4),
        "ci_high": round(ci_high, 4),
        "ci_margin": round(margin, 4)
    }


def welch_t_test(group1: Sequence[float], group2: Sequence[float]) -> Dict[str, Any]:
    """
    Performs Welch's t-test for two independent samples with unequal variances.
    Returns t-statistic, degrees of freedom, p-value, and statistical significance.
    """
    g1 = np.asarray(group1, dtype=float)
    g2 = np.asarray(group2, dtype=float)
    g1 = g1[~np.isnan(g1)]
    g2 = g2[~np.isnan(g2)]

    n1, n2 = len(g1), len(g2)
    if n1 < 2 or n2 < 2:
        return {"t_stat": 0.0, "p_value": 1.0, "df": 0.0, "significant_alpha_0_05": False}

    m1, m2 = float(np.mean(g1)), float(np.mean(g2))
    v1, v2 = float(np.var(g1, ddof=1)), float(np.var(g2, ddof=1))

    # Welch-Satterthwaite degrees of freedom
    denom_df = ((v1 / n1) ** 2 / (n1 - 1)) + ((v2 / n2) ** 2 / (n2 - 1))
    if denom_df <= 0:
        df = float(n1 + n2 - 2)
    else:
        df = ((v1 / n1) + (v2 / n2)) ** 2 / denom_df

    # t-statistic
    se_diff = math.sqrt((v1 / n1) + (v2 / n2))
    if se_diff == 0:
        t_stat = 0.0
        p_val = 1.0
    else:
        t_stat = (m1 - m2) / se_diff
        p_val = 2.0 * float(1.0 - stats.t.cdf(abs(t_stat), df=df))

    return {
        "mean1": round(m1, 4),
        "mean2": round(m2, 4),
        "diff": round(m1 - m2, 4),
        "t_stat": round(t_stat, 4),
        "df": round(df, 2),
        "p_value": float(p_val),
        "significant_alpha_0_05": bool(p_val < 0.05)
    }


def cohens_d(group1: Sequence[float], group2: Sequence[float]) -> Dict[str, float]:
    """
    Computes Cohen's d and Hedges' g effect sizes between two configurations.
    Interpretation:
      |d| < 0.2  : Negligible
      0.2 <= |d| < 0.5 : Small
      0.5 <= |d| < 0.8 : Medium
      |d| >= 0.8 : Large
    """
    g1 = np.asarray(group1, dtype=float)
    g2 = np.asarray(group2, dtype=float)
    g1 = g1[~np.isnan(g1)]
    g2 = g2[~np.isnan(g2)]

    n1, n2 = len(g1), len(g2)
    if n1 < 2 or n2 < 2:
        return {"cohens_d": 0.0, "hedges_g": 0.0}

    m1, m2 = float(np.mean(g1)), float(np.mean(g2))
    v1, v2 = float(np.var(g1, ddof=1)), float(np.var(g2, ddof=1))

    # Pooled standard deviation
    s_pooled = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
    if s_pooled == 0:
        return {"cohens_d": 0.0, "hedges_g": 0.0}

    d = (m1 - m2) / s_pooled
    # Hedges' g correction factor for sample size
    j = 1.0 - (3.0 / (4.0 * (n1 + n2) - 9.0))
    g = d * j

    return {
        "cohens_d": round(d, 4),
        "hedges_g": round(g, 4)
    }
