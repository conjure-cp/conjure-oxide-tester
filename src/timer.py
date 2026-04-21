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

wall = settings["runsolver_cfg"]["walltime"]
cpus = settings["runsolver_cfg"]["cpus"]
mem = settings["runsolver_cfg"]["memory"]

def check_runsolver() -> bool:
    """Check if runsolver is available and works."""
    if shutil.which("runsolver") is None:
        return False
    try:
        # Simple test to see if it runs
        subprocess.run("runsolver --version", shell=True, capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

HAS_RUNSOLVER = check_runsolver()
if HAS_RUNSOLVER:
    runsolver_cfg = f"runsolver -R {mem} -C {cpus} -W {wall}"
else:
    print("Warning: 'runsolver' is not installed or broken. Running solvers directly without limits.")
    runsolver_cfg = ""

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
    var_count: int,
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
    var_col = f"{runner}_variables"

    if "sat" in runner.lower() or "conjure" in runner.lower() or sat_closures != -1:
        try:
            conn.execute(f'ALTER TABLE results ADD COLUMN "{runner}" REAL;')
        except sqlite3.OperationalError:
            pass
        
        try:
            conn.execute(f'ALTER TABLE results ADD COLUMN "{var_col}" INTEGER;')
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute(f'ALTER TABLE results ADD COLUMN "{closure_col}" INTEGER;')
        except sqlite3.OperationalError:
            pass

        query = f'UPDATE results SET "{runner}" = ?, "{var_col}" = ?, "{closure_col}" = ? WHERE model = ? AND run_number = ?'
        conn.execute(query, (runtime, var_count, sat_closures, model, run_number))

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


def get_dimacs_stats(cnf_file: Path) -> tuple[int, int]:
    """
    gets dimacs file and returns:
        - number of variables
        - number of closures
    if error we return -1 
    """
    if not cnf_file.exists():
        return -1, -1
    try:
        with cnf_file.open("r") as f:
            for line in f:
                if line.startswith("p cnf"):
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        return int(parts[2]), int(parts[3])
    except Exception:
        pass
    return -1, -1


def time_run(
    runner: str, model: str, collect_closures: bool
) -> tuple[float, int, int, str | None]:
    """
    Runs conjure-oxide with runnersolver that is config-ed in settings.json

    returns:
        - time
        - number of sat variabels (optional, -1 if collect_closures is false)
        - number of sat closures (optional, -1 if collect_closures is false)
        - error message
    """
    if runner not in runner_commands:
        raise ValueError(f"Unknown runner: {runner}")

    is_sat = collect_closures and (
        "sat" in runner.lower() or "sat" in runner_commands[runner].lower()
    )

    # Generate a unique filename using runner, sanitized model path, and PID
    safe_model = str(Path(model)).replace("/", "_").replace(".", "_")
    unique_id = f"{runner}_{safe_model}_{os.getpid()}"
    sat_file = Path(f"temp_{unique_id}.cnf")
    solution_json = Path(f"solution_{unique_id}.json")

    # Ensure no old solution file exists (for conjure-style runners)
    model_path = Path(model)
    solution_file = Path(f"{model_path.stem}.solution")
    if solution_file.exists():
        solution_file.unlink()

    # Build command
    base_cmd = runner_commands[runner]
    cmd = f"{runsolver_cfg} {base_cmd} ./{model}"
    
    # If it's conjure-oxide, add -o for solution verification
    if "conjure-oxide" in base_cmd:
        cmd = f"{runsolver_cfg} {base_cmd} -o {solution_json} ./{model}"

    if is_sat:
        # If it's conjure-oxide and we need SAT closures, we need to handle it carefully
        if "conjure-oxide" in base_cmd:
            cmd = f"{runsolver_cfg} {base_cmd} -o {solution_json} --save-solver-input-file {sat_file} ./{model}"
        else:
            cmd = f"{runsolver_cfg} {base_cmd} --save-solver-input-file {sat_file} ./{model}"

    print("Running:", cmd)

    var_count = -1
    sat_closures = -1
    start = time.perf_counter()
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            text=True,
            capture_output=True,
        )
        runtime = time.perf_counter() - start

        if is_sat:
            var_count, sat_closures = get_dimacs_stats(sat_file)

        error_msg: str | None = None
        # Always check for solution if the runner was supposed to find one
        found_solution = False
        if "conjure-oxide" in base_cmd:
            # check that it's not empty (i.e., not just '[]')
            found_solution = solution_json.exists() and solution_json.stat().st_size > 2
        else:
            # check that it exists and is not empty
            found_solution = solution_file.exists() and solution_file.stat().st_size > 0

        if result.returncode == 0 and found_solution:
            print(f"Runtime: {runtime:.4f}s, Sat var number: {var_count} Closures: {sat_closures}")
        else:
            print("Run failed (non-zero exit or no solution). Recording -1.0")
            runtime = -1.0
            # Prioritize stderr, but if empty, use stdout
            error_msg = result.stderr.strip() or result.stdout.strip()
            if not error_msg and not found_solution:
                error_msg = "No solution found (likely UNSAT or silent failure)"
            
            # Print the error for immediate feedback in logs
            if error_msg:
                print(f"Error captured: {error_msg[:200]}...")

        return runtime, var_count, sat_closures, error_msg
    finally:
        if sat_file.exists():
            sat_file.unlink()
        if solution_file.exists():
            solution_file.unlink()
        if solution_json.exists():
            solution_json.unlink()


def time_conjure_run(
    runner: str, model: str, collect_closures: bool
) -> tuple[float, int, int, str, str | None]:
    """
    Runs a given model with conjure with runnersolver that is configured
    in settings.json

    returns:
        - time
        - number of sat variabels (optional, -1 if collect_closures is false)
        - number of sat closures (optional, -1 if collect_closures is false)
        - 
        - error message
    """
    if runner not in runner_commands:
        raise ValueError(f"Unknown runner: {runner}")

    cmd_str = runner_commands[runner]
    solver = "minion"
    if "--solver" in cmd_str:
        parts = cmd_str.split()
        try:
            idx = parts.index("--solver")
            solver = parts[idx + 1]
        except (ValueError, IndexError):
            pass

    effective_runner = f"{runner}_{solver}" if runner == "conjure" else runner

    
    # create a unique output directory for savile row/conjure.
    # this prevents file conflicts and race conditions that would occur 
    # if multiple threads wrote to the same folder simultaneously.
    safe_model = str(Path(model)).replace("/", "_").replace(".", "_")
    unique_id = f"{effective_runner}_{safe_model}_{os.getpid()}"
    out_dir = Path(f"temp-conjure-{unique_id}")

    # Conjure solve to get eprime
    cmd = f"{runsolver_cfg} {cmd_str} -o {out_dir} ./{model}"
    print("Running:", cmd)

    var_count = -1
    sat_closures = -1
    start = time.perf_counter()
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            text=True,
            capture_output=True,
        )
        runtime = time.perf_counter() - start

        error_msg: str | None = None

        if result.returncode == 0:
            # check if a solution exists in the out_dir and it is not empty.
            solution_files = list(out_dir.glob("*.solution"))
            
            found_solution = any(f.stat().st_size > 0 for f in solution_files)

            if not found_solution:
                print("No solution file found in conjure out_dir. Recording -1.0")
                runtime = -1.0
                error_msg = "No solution found in output directory"
            else:
                if collect_closures and runner == "conjure_sat":
                    eprime_files = list(out_dir.glob("*.eprime"))
                    if eprime_files:
                        eprime_file = eprime_files[0]
                        sat_file = out_dir / "temp_sat.cnf"
                        sr_cmd = f"savilerow -sat -out-sat {sat_file} {eprime_file}"
                        print("Running:", sr_cmd)
                        subprocess.run(sr_cmd, shell=True, capture_output=True)
                        var_count, sat_closures = get_dimacs_stats(sat_file)

                print(f"Runtime: {runtime:.4f}s, Sat var number: {var_count} Closures: {sat_closures}")
        else:
            print("Run failed. Recording -1.0")
            runtime = -1.0
            error_msg = result.stderr or result.stdout

        return runtime, var_count, sat_closures, effective_runner, error_msg
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
    model_path = Path(sys.argv[2])
    if not model_path.is_file():
        print(f"Error: Model file '{model_path}' not found.")
        sys.exit(1)
    model = str(model_path)
    run_number = int(sys.argv[3])

    conn = get_connection()
    if "conjure" not in runner.lower():
        runtime, var_count, sat_closures, error_msg = time_run(runner, model, collect_closures)
        effective_runner = runner
    else:
        runtime, var_count, sat_closures, effective_runner, error_msg = time_conjure_run(
            runner, model, collect_closures
        )

    update_runtime(conn, model, effective_runner, runtime, run_number, var_count, sat_closures)

    if error_msg:
        update_failure(conn, model, effective_runner, error_msg, run_number)

    conn.close()
