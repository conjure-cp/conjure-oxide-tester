import os
import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def generate_charts(db_path, output_dir):
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)

    runner_map = {
        "conjure_sat_cadical": "conjure_sat",
        "conjure_minion": "conjure_minion",
        "oxide_main_minion": "oxide_minion",
        "oxide_main_sat": "oxide_sat",
        "oxide_main_sat_direct": "oxide_sat_direct",
        "oxide_main_sat_order": "oxide_sat_order",
        "oxide_main_smt": "oxide_smt",
    }

    summary_data = []
    raw_times = {}

    for internal_name, display_name in runner_map.items():
        query = f'SELECT "{internal_name}" FROM results WHERE "{internal_name}" > 0 AND run_number = 2'
        df_runner = pd.read_sql_query(query, conn)

        if not df_runner.empty:
            times = df_runner[internal_name]
            raw_times[display_name] = times
            summary_data.append(
                {"runner": display_name, "count": len(times), "avg_time": times.mean()}
            )

    conn.close()

    if not summary_data:
        print("No successful runs found for any runner in run_number = 2.")
        return

    df_summary = pd.DataFrame(summary_data).sort_values("count", ascending=False)

    plt.style.use("ggplot")

    # --- success Count ---
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    bars1 = ax1.bar(df_summary["runner"], df_summary["count"], color="skyblue")
    ax1.set_title("Number of Successful Tests (run_number = 2)")
    ax1.set_ylabel("Count")
    plt.xticks(rotation=45, ha="right")

    conjure_sat_count = df_summary[df_summary["runner"] == "conjure_sat"][
        "count"
    ].values
    if len(conjure_sat_count) > 0:
        conjure_sat_count = conjure_sat_count[0]
        for bar in bars1:
            yval = bar.get_height()
            percentage = (yval / conjure_sat_count) * 100
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                yval + 5,
                f"{int(yval)}\n({percentage:.1f}%)",
                ha="center",
                va="bottom",
                fontsize=9,
            )

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "success_count.png"))

    # --- Plot 2: Box Plot of Runtimes (Log Scale) ---
    fig2, ax2 = plt.subplots(figsize=(12, 7))

    # Prepare data for boxplot (sorted by median for clarity)
    sorted_runners = sorted(raw_times.keys(), key=lambda x: raw_times[x].median())
    plot_data = [raw_times[r] for r in sorted_runners]

    ax2.boxplot(
        plot_data,
        patch_artist=True,
        boxprops=dict(facecolor="lightblue", color="blue"),
        medianprops=dict(color="red"),
    )
    ax2.set_xticklabels(sorted_runners)

    ax2.set_yscale("log")
    ax2.set_title(
        "Runtime Distribution of Successful Tests (Log Scale, run_number = 2)"
    )
    ax2.set_ylabel("Time (s)")
    plt.xticks(rotation=45, ha="right")
    plt.grid(True, which="both", ls="-", alpha=0.2)

    plt.tight_layout()
    plt.savefig(
        os.path.join(output_dir, "src/analysis/graphs/runtime_distribution_box.png")
    )

    # --- Plot 3: Cumulative Distribution Function (CDF) ---
    # This shows how many problems are solved within X seconds
    fig3, ax3 = plt.subplots(figsize=(12, 7))
    for runner in sorted_runners:
        sorted_time = np.sort(raw_times[runner])
        yvals = np.arange(len(sorted_time)) / float(len(sorted_time) - 1)
        ax3.plot(sorted_time, yvals, label=runner, lw=2)

    ax3.set_xscale("log")
    ax3.set_title("Cumulative Distribution of Runtimes (run_number = 2)")
    ax3.set_xlabel("Time (s)")
    ax3.set_ylabel("Fraction of Problems Solved")
    ax3.legend()
    plt.grid(True, which="both", ls="-", alpha=0.2)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "src/analysis/graphs/runtime_cdf.png"))

    print(
        "Generated: src/analysis/graphs/success_count.png, src/analysis/graphs/runtime_distribution_box.png, src/analysis/graphs/runtime_cdf.png"
    )


if __name__ == "__main__":
    db_path = "res/db/testing_runsolver-4G-150proc-1800s.db"
    output_dir = "."
    generate_charts(db_path, output_dir)
