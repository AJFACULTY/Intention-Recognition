#!/usr/bin/env python3
"""
scripts/analyze_trial_data.py — Statistical Analysis & Publication Plot Generator
Autonomous Mobile Robot Intention Recognition Workspace (ROS 2 Humble)

This script implements Domino 2 of the Overleaf Feedback Action Plan:
1. Ingests empirical CSV trial logs from experiment_logs/trial_data.csv.
2. Computes descriptive statistics: Mean, Median, Standard Deviation, Interquartile
   Range (IQR), and 95% Confidence Intervals for latency and accuracy.
3. Conducts inferential hypothesis testing:
   - One-Way ANOVA across operational distances (1.0m, 1.75m, 2.5m).
   - Two-Sample Student's t-test across lighting environments (Daylight vs. Fluorescent).
4. Generates publication-grade figures for Chapter 4 in write_up/figures/:
   - fig_latency_boxplot.png (Latency distribution boxplots with jitter points)
   - fig_accuracy_by_condition.png (Accuracy error-bar comparisons)
5. Formats summary data for direct inclusion in thesis LaTeX tables.

Usage:
  python3 scripts/analyze_trial_data.py
  python3 scripts/analyze_trial_data.py --csv experiment_logs/trial_data.csv --output-dir write_up/figures
"""

import argparse
import os
import sys
import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use("Agg")  # Headless backend for server/CLI execution
import matplotlib.pyplot as plt


DEFAULT_CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "experiment_logs",
    "trial_data.csv"
)

DEFAULT_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "write_up",
    "figures"
)


def load_dataset(csv_path):
    """Load and validate the CSV trial dataset."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV dataset not found at: {csv_path}")

    df = pd.read_csv(csv_path)

    # Clean and parse types
    df["distance_m"] = df["distance_m"].astype(float)
    df["e2e_latency_ms"] = df["e2e_latency_ms"].astype(float)
    df["confidence"] = df["confidence"].astype(float)
    df["min_lidar_m"] = df["min_lidar_m"].astype(float)
    df["is_correct"] = df["is_correct"].astype(str).str.strip().str.lower().isin(["true", "1"])

    return df


def compute_statistics(df):
    """Compute comprehensive descriptive and inferential statistics."""
    results = {}

    total_n = len(df)
    correct_n = df["is_correct"].sum()
    overall_acc = (correct_n / total_n) * 100.0

    # Latency central tendencies and dispersion
    lat = df["e2e_latency_ms"]
    lat_mean = lat.mean()
    lat_std = lat.std()
    lat_median = lat.median()
    lat_iqr = stats.iqr(lat)
    lat_sem = stats.sem(lat)
    ci_95 = stats.t.interval(0.95, df=len(lat)-1, loc=lat_mean, scale=lat_sem)

    results["sample_size"] = total_n
    results["overall_accuracy"] = overall_acc
    results["latency"] = {
        "mean": lat_mean,
        "std": lat_std,
        "median": lat_median,
        "iqr": lat_iqr,
        "ci_95_lower": ci_95[0],
        "ci_95_upper": ci_95[1],
        "min": lat.min(),
        "max": lat.max(),
    }

    # Per-gesture accuracy breakdown
    gesture_stats = []
    for g in ["Stop", "Follow", "Go", "Left", "Right", "Back"]:
        gdf = df[df["ground_truth"] == g]
        gn = len(gdf)
        gc = gdf["is_correct"].sum()
        g_acc = (gc / gn) * 100.0 if gn > 0 else 0.0
        g_lat = gdf["e2e_latency_ms"].mean()
        g_conf = gdf["confidence"].mean()
        gesture_stats.append({
            "gesture": g,
            "trials": gn,
            "correct": gc,
            "accuracy": g_acc,
            "mean_latency": g_lat,
            "mean_conf": g_conf
        })
    results["gestures"] = gesture_stats

    # Distance Breakdown & One-Way ANOVA
    dist_groups = {}
    for d in sorted(df["distance_m"].unique()):
        sub = df[df["distance_m"] == d]
        dist_groups[d] = {
            "n": len(sub),
            "correct": sub["is_correct"].sum(),
            "accuracy": (sub["is_correct"].sum() / len(sub)) * 100.0,
            "lat_mean": sub["e2e_latency_ms"].mean(),
            "lat_std": sub["e2e_latency_ms"].std(),
            "lat_values": sub["e2e_latency_ms"].values
        }
    results["distance_groups"] = dist_groups

    # One-Way ANOVA across distances
    dist_lat_arrays = [dist_groups[d]["lat_values"] for d in sorted(dist_groups.keys())]
    f_stat, anova_p = stats.f_oneway(*dist_lat_arrays)
    results["anova_distance"] = {
        "f_stat": f_stat,
        "p_value": anova_p,
        "significant": anova_p < 0.05
    }

    # Lighting Breakdown & Two-Sample t-test
    light_groups = {}
    for l in df["lighting"].unique():
        sub = df[df["lighting"] == l]
        light_groups[l] = {
            "n": len(sub),
            "correct": sub["is_correct"].sum(),
            "accuracy": (sub["is_correct"].sum() / len(sub)) * 100.0,
            "lat_mean": sub["e2e_latency_ms"].mean(),
            "lat_std": sub["e2e_latency_ms"].std(),
            "lat_values": sub["e2e_latency_ms"].values
        }
    results["lighting_groups"] = light_groups

    # Independent two-sample t-test (Welch's t-test)
    l_keys = list(light_groups.keys())
    if len(l_keys) >= 2:
        t_stat, t_p = stats.ttest_ind(
            light_groups[l_keys[0]]["lat_values"],
            light_groups[l_keys[1]]["lat_values"],
            equal_var=False
        )
        results["ttest_lighting"] = {
            "t_stat": t_stat,
            "p_value": t_p,
            "significant": t_p < 0.05
        }

    return results


def print_statistical_report(results):
    """Print an exhaustive, publication-grade academic report to terminal."""
    lat = results["latency"]
    anova = results["anova_distance"]
    ttest = results.get("ttest_lighting", {})

    print("\n" + "=" * 78)
    print("        INFERENTIAL & DESCRIPTIVE STATISTICAL ANALYSIS REPORT")
    print("                  Autonomous Mobile Robot Cognition")
    print("=" * 78)
    print(f"Sample Size (N)              : {results['sample_size']} physical trials")
    print(f"Aggregate Observed Accuracy  : {results['overall_accuracy']:.2f}%")
    print(f"End-to-End Latency Mean (SD) : {lat['mean']:.2f} ms (±{lat['std']:.2f} ms)")
    print(f"Latency Median (IQR)         : {lat['median']:.2f} ms (IQR: {lat['iqr']:.2f} ms)")
    print(f"95% Confidence Interval      : [{lat['ci_95_lower']:.2f} ms, {lat['ci_95_upper']:.2f} ms]")
    print(f"Nominal Design Budget        : 132.0 ms (ERQ 1 Deadline: 150.0 ms)")

    print("\n" + "-" * 78)
    print("PER-GESTURE CLASSIFICATION & LATENCY BREAKDOWN")
    print("-" * 78)
    print(f"{'Gesture':<10} | {'Trials':<8} | {'Correct':<8} | {'Accuracy':<10} | {'Mean Latency':<14} | {'Mean Conf':<10}")
    print("-" * 78)
    for g in results["gestures"]:
        print(f"{g['gesture']:<10} | {g['trials']:<8} | {g['correct']:<8} | {g['accuracy']:>7.1f}%   | {g['mean_latency']:>8.2f} ms    | {g['mean_conf']:>8.3f}")

    print("\n" + "-" * 78)
    print("OPERATIONAL DISTANCE INVARIANCE ANALYSIS (ANOVA)")
    print("-" * 78)
    for d, data in results["distance_groups"].items():
        print(f" Distance {d:.2f} m: N = {data['n']:2d} | Accuracy = {data['accuracy']:5.1f}% | Latency = {data['lat_mean']:.2f} ± {data['lat_std']:.2f} ms")
    print(f"\n One-Way ANOVA F-Statistic : F = {anova['f_stat']:.3f}")
    print(f" One-Way ANOVA p-value     : p = {anova['p_value']:.4f} " + ("(NOT SIGNIFICANT, p > 0.05 -> Invariant)" if not anova['significant'] else "(SIGNIFICANT)"))

    if ttest:
        print("\n" + "-" * 78)
        print("AMBIENT LIGHTING ROBUSTNESS ANALYSIS (Welch's t-test)")
        print("-" * 78)
        for l, data in results["lighting_groups"].items():
            print(f" Lighting {l:<11}: N = {data['n']:2d} | Accuracy = {data['accuracy']:5.1f}% | Latency = {data['lat_mean']:.2f} ± {data['lat_std']:.2f} ms")
        print(f"\n Two-Sample t-Statistic    : t = {ttest['t_stat']:.3f}")
        print(f" Two-Sample p-value        : p = {ttest['p_value']:.4f} " + ("(NOT SIGNIFICANT, p > 0.05 -> Robust)" if not ttest['significant'] else "(SIGNIFICANT)"))

    print("=" * 78 + "\n")


def generate_publication_figures(df, results, output_dir):
    """Generate high-DPI publication figures matching IEEE/Springer standards."""
    os.makedirs(output_dir, exist_ok=True)

    # Style configuration
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.titlesize": 13,
        "figure.dpi": 300
    })

    # ── Figure 1: Latency Distribution Boxplots with Jitter ──
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8), gridspec_kw={"width_ratios": [1.1, 1]})

    distances = sorted(df["distance_m"].unique())
    dist_data = [df[df["distance_m"] == d]["e2e_latency_ms"].values for d in distances]
    labels_dist = [f"{d:.2f} m\n(N={len(arr)})" for d, arr in zip(distances, dist_data)]

    # Boxplot 1: By Distance
    bp1 = ax1.boxplot(
        dist_data,
        tick_labels=labels_dist,
        patch_artist=True,
        widths=0.45,
        boxprops=dict(facecolor="#D9E2EC", color="#102A43", linewidth=1.5),
        medianprops=dict(color="#0B69A3", linewidth=2.0),
        whiskerprops=dict(color="#102A43", linewidth=1.2),
        capprops=dict(color="#102A43", linewidth=1.2),
        flierprops=dict(marker="o", color="#0B69A3", alpha=0.5)
    )

    # Add jittered scatter points
    np.random.seed(42)
    for idx, vals in enumerate(dist_data):
        x = np.random.normal(idx + 1, 0.05, size=len(vals))
        ax1.scatter(x, vals, alpha=0.35, color="#102A43", edgecolors="none", s=22, zorder=3)

    # Add reference lines
    ax1.axhline(132.0, color="#2B6CB0", linestyle="--", linewidth=1.2, label="Nominal Budget (132.0 ms)")
    ax1.axhline(150.0, color="#C53030", linestyle=":", linewidth=1.5, label="ERQ 1 Bound (150.0 ms)")
    ax1.set_ylabel("End-to-End Latency (ms)", fontweight="bold")
    ax1.set_xlabel("Operational Distance", fontweight="bold")
    ax1.set_title(f"(a) Latency vs. Distance\n(One-Way ANOVA: F={results['anova_distance']['f_stat']:.2f}, p={results['anova_distance']['p_value']:.3f})", pad=10)
    ax1.set_ylim(118, 155)
    ax1.grid(True, linestyle="--", alpha=0.4, axis="y")
    ax1.legend(loc="upper left", framealpha=0.9)

    # Boxplot 2: By Lighting
    light_names = sorted(df["lighting"].unique())
    light_data = [df[df["lighting"] == l]["e2e_latency_ms"].values for l in light_names]
    labels_light = [f"{l}\n(N={len(arr)})" for l, arr in zip(light_names, light_data)]

    bp2 = ax2.boxplot(
        light_data,
        tick_labels=labels_light,
        patch_artist=True,
        widths=0.45,
        boxprops=dict(facecolor="#E2E8F0", color="#2D3748", linewidth=1.5),
        medianprops=dict(color="#3182CE", linewidth=2.0),
        whiskerprops=dict(color="#2D3748", linewidth=1.2),
        capprops=dict(color="#2D3748", linewidth=1.2),
        flierprops=dict(marker="o", color="#3182CE", alpha=0.5)
    )

    for idx, vals in enumerate(light_data):
        x = np.random.normal(idx + 1, 0.05, size=len(vals))
        ax2.scatter(x, vals, alpha=0.35, color="#2D3748", edgecolors="none", s=22, zorder=3)

    ax2.axhline(132.0, color="#2B6CB0", linestyle="--", linewidth=1.2)
    ax2.axhline(150.0, color="#C53030", linestyle=":", linewidth=1.5)
    ttest = results.get("ttest_lighting", {})
    t_str = f"t={ttest.get('t_stat', 0):.2f}, p={ttest.get('p_value', 0):.3f}" if ttest else "N/A"
    ax2.set_xlabel("Ambient Lighting Environment", fontweight="bold")
    ax2.set_title(f"(b) Latency vs. Lighting\n(Two-Sample t-test: {t_str})", pad=10)
    ax2.set_ylim(118, 155)
    ax2.grid(True, linestyle="--", alpha=0.4, axis="y")

    plt.tight_layout()
    fig1_path = os.path.join(output_dir, "fig_latency_boxplot.png")
    plt.savefig(fig1_path, bbox_inches="tight")
    plt.close()
    print(f"[SAVED] Publication Latency Boxplot -> {fig1_path}")

    # ── Figure 2: Classification Accuracy by Gesture & Operating Conditions ──
    fig, (ax3, ax4) = plt.subplots(1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1.2, 0.9]})

    # Subplot 2a: Per-Gesture Observed Physical Accuracy
    gestures = [g["gesture"] for g in results["gestures"]]
    accuracies = [g["accuracy"] for g in results["gestures"]]
    colors = ["#2B6CB0" if acc >= 95.0 else "#DD6B20" for acc in accuracies]

    bars = ax3.bar(gestures, accuracies, color=colors, width=0.55, edgecolor="#1A202C", linewidth=1.1)
    ax3.axhline(96.67, color="#C53030", linestyle="--", linewidth=1.4, label="Aggregate Mean (96.67%)")
    ax3.set_ylabel("Observed Physical Accuracy (%)", fontweight="bold")
    ax3.set_xlabel("Gesture Vocabulary Class", fontweight="bold")
    ax3.set_title("(a) Per-Gesture Accuracy Across All 180 Trials", pad=10)
    ax3.set_ylim(75, 105)
    ax3.grid(True, linestyle="--", alpha=0.4, axis="y")
    ax3.legend(loc="lower right", framealpha=0.9)

    for bar in bars:
        h = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2.0, h + 1.0, f"{h:.1f}%", ha="center", va="bottom", fontsize=9.5, fontweight="bold")

    # Subplot 2b: Accuracy Across Operating Distance & Lighting Regimes
    cond_labels = ["1.00 m", "1.75 m", "2.50 m", "Daylight", "Fluorescent"]
    cond_accs = [
        results["distance_groups"][1.00]["accuracy"],
        results["distance_groups"][1.75]["accuracy"],
        results["distance_groups"][2.50]["accuracy"],
        results["lighting_groups"]["Daylight"]["accuracy"],
        results["lighting_groups"]["Fluorescent"]["accuracy"],
    ]
    cond_colors = ["#319795", "#319795", "#319795", "#805AD5", "#805AD5"]

    bars2 = ax4.bar(cond_labels, cond_accs, color=cond_colors, width=0.52, edgecolor="#1A202C", linewidth=1.1)
    ax4.axhline(96.67, color="#C53030", linestyle="--", linewidth=1.4)
    ax4.set_ylabel("Observed Physical Accuracy (%)", fontweight="bold")
    ax4.set_xlabel("Experimental Condition", fontweight="bold")
    ax4.set_title("(b) Accuracy by Distance & Lighting Regimes", pad=10)
    ax4.set_ylim(75, 105)
    ax4.grid(True, linestyle="--", alpha=0.4, axis="y")

    for bar in bars2:
        h = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2.0, h + 1.0, f"{h:.1f}%", ha="center", va="bottom", fontsize=9.5, fontweight="bold")

    plt.tight_layout()
    fig2_path = os.path.join(output_dir, "fig_accuracy_by_condition.png")
    plt.savefig(fig2_path, bbox_inches="tight")
    plt.close()
    print(f"[SAVED] Publication Accuracy Breakdown -> {fig2_path}")


def main():
    parser = argparse.ArgumentParser(description="Statistical Analysis of Robotic Trial Data")
    parser.add_argument("--csv", type=str, default=DEFAULT_CSV_PATH, help="Path to trial_data.csv")
    parser.add_argument("--output-dir", type=str, default=DEFAULT_OUTPUT_DIR, help="Destination directory for plots")

    args = parser.parse_args()

    print(f"[INFO] Ingesting empirical trial logs: {args.csv}")
    df = load_dataset(args.csv)

    print("[INFO] Computing descriptive and inferential statistics...")
    results = compute_statistics(df)

    print_statistical_report(results)

    print("[INFO] Generating publication-grade figures...")
    generate_publication_figures(df, results, args.output_dir)

    print("[SUCCESS] Domino 2 completed successfully!")


if __name__ == "__main__":
    main()
