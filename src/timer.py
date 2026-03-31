# timer.py

from pathlib import Path
import sqlite3
import sys
import json
import time
import subprocess
import shutil
import os

# ------------------------
# Load settings
# ------------------------
with Path("settings.json").open("r", encoding="utf-8") as f:
    settings = json.load(f)

runner_commands = settings["runner_commands"]
db_path = settings["outfile"]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")

    return conn


def update_runtime(
    conn: sqlite3.Connection,
    model: str,
    runner: str,
    runtime: float,
    run_number: int,
    sat_closures: int,
) -> None:
    conn.execute(
        """
        INSERT INTO results (model, run_number)
        VALUES (?, ?)
        ON CONFLICT(model, run_number)
        DO NOTHING
        """,
        (model, run_number),
    )

    closure_col = f"{runner}_closures"

    if "sat" in runner.lower() or "conjure" in runner.lower() or sat_closures != -1:
        try:
            conn.execute(f'ALTER TABLE results ADD COLUMN "{runner}" REAL;')
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute(f'ALTER TABLE results ADD COLUMN "{closure_col}" INTEGER;')
        except sqlite3.OperationalError:
            pass

        query = f'UPDATE results SET "{runner}" = ?, "{closure_col}" = ? WHERE model = ? AND run_number = ?'
        conn.execute(query, (runtime, sat_closures, model, run_number))
    else:
        try:
            conn.execute(f'ALTER TABLE results ADD COLUMN "{runner}" REAL;')
        except sqlite3.OperationalError:
            pass
        query = f'UPDATE results SET "{runner}" = ? WHERE model = ? AND run_number = ?'
        conn.execute(query, (runtime, model, run_number))

    conn.commit()


def update_failure(
    conn: sqlite3.Connection,
    model: str,
    runner: str,
    error_msg: str,
    run_number: int,
) -> None:
    conn.execute(
        """
        INSERT INTO failures (model, runner, run_number, error_msg)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(model, runner, run_number)
        DO UPDATE SET error_msg = excluded.error_msg
        """,
        (model, runner, run_number, error_msg),
    )
    conn.commit()


def get_sat_closures(cnf_file: Path) -> int:
    if not cnf_file.exists():
        return -1
    try:
        with cnf_file.open("r") as f:
            for line in f:
                if line.startswith("p cnf"):
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        return int(parts[3])
    except Exception:
        pass
    return -1


def time_run(
    runner: str, model: str, collect_closures: bool
) -> tuple[float, int, str | None]:
    if runner not in runner_commands:
        raise ValueError(f"Unknown runner: {runner}")

    is_sat = collect_closures and (
        "sat" in runner.lower() or "sat" in runner_commands[runner].lower()
    )

    # Generate a unique filename using runner, sanitized model path, and PID
    safe_model = str(Path(model)).replace("/", "_").replace(".", "_")
    unique_id = f"{runner}_{safe_model}_{os.getpid()}"
    sat_file = Path(f"temp_{unique_id}.cnf")

    cmd = f"{runner_commands[runner]} ./{model}"
    if is_sat:
        cmd = f"{runner_commands[runner]} --save-solver-input-file {sat_file} ./{model}"

    print("Running:", cmd)

    start = time.perf_counter()
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            text=True,
            capture_output=True,
        )
        runtime = time.perf_counter() - start

        sat_closures = -1
        if is_sat:
            sat_closures = get_sat_closures(sat_file)

        error_msg: str | None = None
        if result.returncode == 0:
            print(f"Runtime: {runtime:.4f}s, Closures: {sat_closures}")
        else:
            print("Run failed. Recording -1.0")
            runtime = -1.0
            error_msg = result.stderr or result.stdout

        return runtime, sat_closures, error_msg
    finally:
        if is_sat and sat_file.exists():
            sat_file.unlink()


def time_conjure_run(
    runner: str, model: str, collect_closures: bool
) -> tuple[float, int, str, str | None]:
    if runner not in runner_commands:
        raise ValueError(f"Unknown runner: {runner}")

    cmd_str = runner_commands[runner]
    solver = "minion"
    if "--solver" in cmd_str:
        parts = cmd_str.split()
        try:
            idx = parts.index("--solver")
            solver = parts[idx + 1]
        except ValueError, IndexError:
            pass

    effective_runner = f"{runner}_{solver}" if runner == "conjure" else runner

    safe_model = str(Path(model)).replace("/", "_").replace(".", "_")
    unique_id = f"{effective_runner}_{safe_model}_{os.getpid()}"
    out_dir = Path(f"temp-conjure-{unique_id}")

    # Conjure solve to get eprime
    cmd = f"{cmd_str} -o {out_dir} ./{model}"
    print("Running:", cmd)

    start = time.perf_counter()
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            text=True,
            capture_output=True,
        )
        runtime = time.perf_counter() - start

        sat_closures = -1
        error_msg: str | None = None

        if result.returncode == 0:
            if collect_closures and runner == "conjure_sat":
                eprime_files = list(out_dir.glob("*.eprime"))
                if eprime_files:
                    eprime_file = eprime_files[0]
                    sat_file = out_dir / "temp_sat.cnf"
                    sr_cmd = f"savilerow -sat -out-sat {sat_file} {eprime_file}"
                    print("Running:", sr_cmd)
                    subprocess.run(sr_cmd, shell=True, capture_output=True)
                    sat_closures = get_sat_closures(sat_file)

            print(f"Runtime: {runtime:.4f}s, Closures: {sat_closures}")
        else:
            print("Run failed. Recording -1.0")
            runtime = -1.0
            error_msg = result.stderr or result.stdout

        return runtime, sat_closures, effective_runner, error_msg
    finally:
        if out_dir.exists():
            shutil.rmtree(out_dir)


if __name__ == "__main__":
    collect_closures = True
    if "--no-closures" in sys.argv:
        collect_closures = False
        sys.argv.remove("--no-closures")

    if len(sys.argv) != 4:
        print("Usage: python timer.py <runner> <model> <run_number> [--no-closures]")
        sys.exit(1)

    runner = sys.argv[1]
    model = str(Path(sys.argv[2]))
    run_number = int(sys.argv[3])

    conn = get_connection()
    if "conjure" not in runner.lower():
        runtime, sat_closures, error_msg = time_run(runner, model, collect_closures)
        effective_runner = runner
    else:
        runtime, sat_closures, effective_runner, error_msg = time_conjure_run(
            runner, model, collect_closures
        )

    update_runtime(conn, model, effective_runner, runtime, run_number, sat_closures)

    if error_msg:
        update_failure(conn, model, effective_runner, error_msg, run_number)

    conn.close()
