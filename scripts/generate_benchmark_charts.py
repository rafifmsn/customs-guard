#!/usr/bin/env python3
"""Generate publication-quality visual charts for CustomsGuard benchmarks.

Creates a dual-panel figure illustrating:
1. Ground Truth Classification Accuracy (3-Way Ablation Study)
2. Latency & Tail Throughput Percentiles (k6 Load Test vs SLA Limits)
"""

import matplotlib.pyplot as plt
import numpy as np


def main():
    # Base aesthetic configuration
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
    plt.rcParams["axes.edgecolor"] = "#d1d5db"
    plt.rcParams["axes.linewidth"] = 0.8
    plt.rcParams["text.color"] = "#1f2937"
    plt.rcParams["axes.labelcolor"] = "#374151"
    plt.rcParams["xtick.color"] = "#4b5563"
    plt.rcParams["ytick.color"] = "#4b5563"

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.2), dpi=300)

    # Clean border spines
    for ax in (ax1, ax2):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#d1d5db")
        ax.spines["bottom"].set_color("#d1d5db")

    # -------------------------------------------------------------
    # Panel 1: Accuracy Benchmark
    # -------------------------------------------------------------
    tiers = [
        "Tier 1: Keyword\n(Baseline BM25)",
        "Tier 2: Dense Vector\n(all-minilm 384-d)",
        "Tier 3: Hybrid + LLM\n(Qwen 2.5 3B)",
    ]

    top1 = [12.0, 22.0, 24.0]
    top3 = [26.0, 50.0, 48.0]
    chapter = [40.0, 74.0, 76.0]

    x = np.arange(len(tiers))
    width = 0.24

    # Cohesive corporate palette
    c_top1 = "#1e3a8a"     # Deep slate blue
    c_top3 = "#0284c7"     # Muted sky blue
    c_chap = "#94a3b8"     # Neutral cool gray

    rects1 = ax1.bar(x - width, top1, width, label="Top-1 Subheading (HS-6)", color=c_top1)
    rects2 = ax1.bar(x, top3, width, label="Top-3 Subheading (HS-6)", color=c_top3)
    rects3 = ax1.bar(x + width, chapter, width, label="Chapter Accuracy (HS-2)", color=c_chap)

    ax1.set_ylabel("Accuracy (%)", fontsize=10.5)
    ax1.set_title("Tariff Classification Accuracy (50 Ground Truth Items)", fontsize=11.5, pad=14)
    ax1.set_xticks(x)
    ax1.set_xticklabels(tiers, fontsize=9)
    ax1.set_ylim(0, 95)
    ax1.grid(axis="y", linestyle=":", alpha=0.6, color="#cbd5e1")
    ax1.set_axisbelow(True)
    ax1.legend(loc="upper left", frameon=False, fontsize=8.5)

    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax1.annotate(
                f"{height:.1f}%",
                xy=(rect.get_x() + rect.get_width() / 2, height),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                color="#374151",
            )

    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3)

    # -------------------------------------------------------------
    # Panel 2: Latency & Tail Percentiles (Linear Scale)
    # -------------------------------------------------------------
    measured_metrics = ["p50 (Median)", "p90", "p95 (Tail)"]
    measured_latencies = [24.08, 33.14, 36.93]

    x2 = np.arange(len(measured_metrics))
    bar_width = 0.45

    bars = ax2.bar(x2, measured_latencies, color="#0f766e", width=bar_width)

    ax2.set_ylabel("Response Latency (ms)", fontsize=10.5)
    ax2.set_title("Audit Latency Percentiles (k6 Benchmark)", fontsize=11.5, pad=14)
    ax2.set_xticks(x2)
    ax2.set_xticklabels(measured_metrics, fontsize=9)
    ax2.set_ylim(0, 50)
    ax2.grid(axis="y", linestyle=":", alpha=0.6, color="#cbd5e1")
    ax2.set_axisbelow(True)

    for bar, val in zip(bars, measured_latencies):
        height = bar.get_height()
        ax2.annotate(
            f"{val:.1f} ms",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            color="#134e4a",
        )

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()