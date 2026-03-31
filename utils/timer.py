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

wall = settings["runsolver_cfg"]["walltime"]
cpus = settings["runsolver_cfg"]["cpus"]
mem = settings["runsolver_cfg"]["memory"]


def get_connection():
    conn = sqlite3.connect(db_path, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def update_runtime(conn, model, runner, runtime):
    conn.execute(
        """
        INSERT INTO results (model)
        VALUES (?)
        ON CONFLICT(model) DO NOTHING
    """,
        (model, ),
    )

    query = f'UPDATE results SET "{runner}" = ? WHERE model = ?'
    conn.execute(query, (runtime, model))

    conn.commit()


def update_failure(conn, model, runner, error_msg):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS failures (
            model TEXT,
            runner TEXT,
            error_msg TEXT,
            comment TEXT,
            PRIMARY KEY (model, runner)
        )
    """)
    conn.execute(
        """
        INSERT INTO failures (model, runner, error_msg)
        VALUES (?, ?, ?)
        ON CONFLICT(model, runner) DO UPDATE SET error_msg = excluded.error_msg
    """,
        (model, runner, error_msg),
    )
    conn.commit()


def time_rust_run(runner, model, runsolver_cfg):
    if runner not in runner_commands:
        raise ValueError(f"Unknown runner: {runner}")

    start = time.perf_counter()

    cmd = f"{runsolver_cfg} {runner_commands[runner]} ./{model}"
    print("Running:", cmd)

    result = subprocess.run(
        cmd,
        shell=True,
        text=True,
        capture_output=True,
    )

    runtime = time.perf_counter() - start
    error_msg = None

    if result.returncode == 0:
        print("Runtime:", runtime)
    else:
        print("Run failed. Recording -1.0")
        runtime = -1.0
        error_msg = result.stderr or result.stdout

    return runtime, error_msg

def time_conjure_run(runner, model, runsolver_cfg):
    if runner not in runner_commands:
        raise ValueError(f"Unknown runner: {runner}")

    start = time.perf_counter()

    cmd = f"{runsolver_cfg} {runner_commands[runner]} -o temp-{model} ./{model}"
    print("Running:", cmd)

    result = subprocess.run(
        cmd,
        shell=True,
        text=True,
        capture_output=True,
    )

    runtime = time.perf_counter() - start
    error_msg = None

    if result.returncode == 0:
        print("Runtime:", runtime)
    else:
        print("Run failed. Recording -1.0")
        runtime = -1.0
        error_msg = result.stderr or result.stdout

    return runtime, error_msg

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python timer.py <runner> <model>")
        sys.exit(1)

    runner = sys.argv[1]
    
    runsolver_cfg = f"runsolver -R {mem} -C {cpus} -W {wall}"

    model = str(Path(sys.argv[2]))

    conn = get_connection()
    if sys.argv[1] != "conjure":        # FIXME: Ideally, this check should actually grep on the command, not the runner name
        runtime, error_msg = time_rust_run(runner, model, runsolver_cfg)
    else:
        runtime, error_msg = time_conjure_run(runner, model, runsolver_cfg)
    update_runtime(conn, model, runner, runtime)

    if error_msg:
        update_failure(conn, model, runner, error_msg)

    conn.close()
