import os
import sqlite3

import matplotlib.pyplot as plt
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

    internal_names = list(runner_map.keys())

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

    where_clause = " AND ".join([f'"{name}" > 0' for name in internal_names])
    intersection_query = f"SELECT {', '.join([f'"{name}"' for name in internal_names])} FROM results WHERE run_number = 2 AND {where_clause}"
    df_intersection = pd.read_sql_query(intersection_query, conn)

    conn.close()

    if df_intersection.empty:
        print("No models were solved by all runners simultaneously.")
        common_data = []
    else:
        common_data = []
        for internal_name in internal_names:
            display_name = runner_map[internal_name]
            common_data.append(
                {
                    "runner": display_name,
                    "avg_time": df_intersection[internal_name].mean(),
                }
            )
        print(f"Found {len(df_intersection)} instances solved by all runners.")

    plt.style.use("ggplot")

    # --- Plot 1: Success Count (Individual) ---
    df_summary = pd.DataFrame(summary_data).sort_values("count", ascending=False)
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    bars1 = ax1.bar(df_summary["runner"], df_summary["count"], color="skyblue")
    ax1.set_title("Total Number of Successful Tests (run_number = 2)")
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

    # --- Plot 2: Common Success Average Time ---
    if common_data:
        df_common = pd.DataFrame(common_data).sort_values("avg_time")
        fig2, ax2 = plt.subplots(figsize=(12, 7))
        bars2 = ax2.bar(df_common["runner"], df_common["avg_time"], color="lightgreen")
        ax2.set_title(
            f"Average Runtime on Common Instances (N={len(df_intersection)}, run_number = 2)"
        )
        ax2.set_ylabel("Average Time (s)")
        plt.xticks(rotation=45, ha="right")

        conjure_sat_time = df_common[df_common["runner"] == "conjure_sat"][
            "avg_time"
        ].values[0]
        for bar in bars2:
            yval = bar.get_height()
            ratio = yval / conjure_sat_time
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                yval + 0.02,
                f"{yval:.3f}s\n({ratio:.2f}x)",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "common_success_average_time.png"))

    # --- Plot 3: Box Plot of Runtimes (Log Scale, Individual) ---
    fig3, ax3 = plt.subplots(figsize=(12, 7))
    sorted_runners = sorted(raw_times.keys(), key=lambda x: raw_times[x].median())
    plot_data = [raw_times[r] for r in sorted_runners]
    ax3.boxplot(
        plot_data,
        tick_labels=sorted_runners,
        patch_artist=True,
        boxprops=dict(facecolor="lightblue", color="blue"),
        medianprops=dict(color="red"),
    )
    ax3.set_yscale("log")
    ax3.set_title("Runtime Distribution (Individual Successful Tests, Log Scale)")
    ax3.set_ylabel("Time (s)")
    plt.xticks(rotation=45, ha="right")
    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "runtime_distribution_box.png"))

    print(
        "Generated: success_count.png, common_success_average_time.png, runtime_distribution_box.png"
    )


if __name__ == "__main__":
    db_path = "res/db/testing_runsolver-4G-150proc-1800s.db"
    output_dir = "src/analysis/graphs"
    generate_charts(db_path, output_dir)
