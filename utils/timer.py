# timer.py

from pathlib import Path
import sqlite3
import sys
import json
import time
import subprocess

# ------------------------
# Load settings
# ------------------------
with Path("settings.json").open("r", encoding="utf-8") as f:
    settings = json.load(f)

runner_commands = settings["runner_commands"]
db_path = settings["outfile"]


def get_connection():
    conn = sqlite3.connect(db_path, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def update_runtime(conn, model, runner, runtime):
    # Ensure row exists
    conn.execute("""
        INSERT INTO results (model)
        VALUES (?)
        ON CONFLICT(model) DO NOTHING
    """, (model,))

    # Update specific runner column
    query = f'UPDATE results SET "{runner}" = ? WHERE model = ?'
    conn.execute(query, (runtime, model))

    conn.commit()


def time_run(runner, model):
    if runner not in runner_commands:
        raise ValueError(f"Unknown runner: {runner}")

    start = time.perf_counter()

    cmd = f"{runner_commands[runner]} ./{model}"
    print("Running:", cmd)

    result = subprocess.run(
        cmd,
        shell=True,
        text=True,
    )

    runtime = time.perf_counter() - start

    if result.returncode == 0:
        print("Runtime:", runtime)
    else:
        print("Run failed. Recording -1.0")
        runtime = -1.0

    return runtime


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python timer.py <runner> <model>")
        sys.exit(1)

    runner = sys.argv[1]
    # model = Path(sys.argv[2]).name  # normalize name
    model = str(Path(sys.argv[2]))

    conn = get_connection()
    runtime = time_run(runner, model)
    update_runtime(conn, model, runner, runtime)
    conn.close()
