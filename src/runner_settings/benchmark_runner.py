# benchmark_runner.py

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import NamedTuple

from database_manager import DatabaseManager
from settings import config


class RunResult(NamedTuple):
    runtime: float
    var_count: int
    sat_closures: int
    effective_runner: str
    error_msg: str | None = None


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


def check_if_param(folder: Path) -> bool:
    """
    Checks if a folder contains at least one .essence or .eprime file,
    AND at least one .param file.
    """
    if not folder.is_dir():
        return False

    extensions = {f.suffix for f in folder.iterdir() if f.is_file()}

    has_model = ".essence" in extensions or ".eprime" in extensions
    has_param = ".param" in extensions

    return has_model and has_param


def time_run(runner: str, model: str, collect_closures: bool) -> RunResult:
    """
    Runs conjure-oxide with runnersolver that is config-ed in settings.json

    returns:
        - time
        - number of sat variabels (optional, -1 if collect_closures is false)
        - number of sat closures (optional, -1 if collect_closures is false)
        - error message
    """
    if "conjure-oxide" not in config.runner_commands[runner]:
        raise ValueError(
            f"time_run expects a conjure-oxide runner. Command found: {config.runner_commands[runner]}"
        )

    is_sat = collect_closures and (
        "sat" in runner.lower() or "sat" in config.runner_commands[runner].lower()
    )

    # Generate a unique filename using runner, sanitized model path, and PID
    safe_model = str(Path(model)).replace("/", "_").replace(".", "_")
    unique_id = f"{runner}_{safe_model}_{os.getpid()}"
    sat_file = Path(f"temp_{unique_id}.cnf")
    solution_json = Path(f"solution_{unique_id}.json")

    model_path = Path(model)
    solution_file = Path(f"{model_path.stem}.solution")
    if solution_file.exists():
        solution_file.unlink()

    # build command
    cmd = f"{config.runsolver_cmd} {config.runner_commands[runner]} ./{model}"

    if is_sat:
        cmd = f"{config.runsolver_cmd} {config.runner_commands[runner]} -o {solution_json} --save-solver-input-file {sat_file} ./{model}"

    print("Running:", cmd)

    var_count = -1
    sat_closures = -1
    start = time.perf_counter()
    try:
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        runtime = time.perf_counter() - start

        if is_sat:
            var_count, sat_closures = get_dimacs_stats(sat_file)

        error_msg: str | None = None
        # Always check for solution if the runner was supposed to find one
        found_solution = solution_file.exists() and solution_file.stat().st_size > 0

        # child status check to record fails on conjure-oxide run
        child_failed = (
            "Child status:" in result.stdout and "Child status: 0" not in result.stdout
        )
        if result.returncode == 0 and not child_failed:
            if not found_solution:
                print(f"Runtime: {runtime:.4f}s. (No solution found; likely UNSAT)")
            else:
                print(
                    f"Runtime: {runtime:.4f}s, Sat var number: {var_count} Closures: {sat_closures}"
                )
        else:
            print("Run failed (non-zero exit). Recording -1.0")
            runtime = -1.0
            error_msg = (
                result.stderr.strip() or result.stdout.strip() or "Silent failure"
            )
            print(f"Error captured: {error_msg[:200]}...")

        return RunResult(
            runtime,
            var_count,
            sat_closures,
            runner,
            error_msg,
        )
    finally:
        if sat_file.exists():
            sat_file.unlink()
        if solution_file.exists():
            solution_file.unlink()
        if solution_json.exists():
            solution_json.unlink()


def time_conjure_run(runner: str, model: str, collect_closures: bool) -> RunResult:
    """
    Runs a given model with conjure with runnersolver that is configured
    in settings.json

    returns:
        - time
        - number of sat variabels (optional, -1 if collect_closures is false)
        - number of sat closures (optional, -1 if collect_closures is false)
        - effective_runner
        - error message
    """

    if "conjure " not in config.runner_commands[runner]:
        raise ValueError(
            f"time_run expects a conjure runner. Command found: {config.runner_commands[runner]}"
        )

    cmd_str = config.runner_commands[runner]
    solver = "minion"
    if "--solver" in cmd_str:
        parts = cmd_str.split()
        idx = parts.index("--solver")
        solver = parts[idx + 1]

    # get solver
    effective_runner = f"{runner}_{solver}"

    # create a unique output directory for savile row/conjure.
    # this prevents file conflicts and race conditions that would occur
    # if multiple threads wrote to the same folder simultaneously.
    safe_model = str(Path(model)).replace("/", "_").replace(".", "_")
    unique_id = f"{effective_runner}_{safe_model}_{os.getpid()}"
    out_dir = Path(f"temp-conjure-{unique_id}")

    cmd = f"{config.runsolver_cmd} {cmd_str} -o {out_dir} ./{model}"
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

        # check if conjure process gives an error
        child_failed = (
            "Child status:" in result.stdout and "Child status: 0" not in result.stdout
        )
        if result.returncode == 0 and not child_failed:
            solution_files = list(out_dir.glob("*.solution"))
            found_solution = any(f.stat().st_size > 0 for f in solution_files)

            if not found_solution:
                print(
                    f"Runtime: {runtime:.4f}s. (No solution file found; likely UNSAT)"
                )

            if collect_closures and runner == "conjure_sat":
                eprime_files = list(out_dir.glob("*.eprime"))
                if eprime_files:
                    eprime_file = eprime_files[0]
                    sat_file = out_dir / "temp_sat.cnf"
                    sr_cmd = f"savilerow -sat -out-sat {sat_file} {eprime_file}"
                    print("Running:", sr_cmd)
                    subprocess.run(sr_cmd, shell=True, capture_output=True)
                    var_count, sat_closures = get_dimacs_stats(sat_file)

            if found_solution:
                print(
                    f"Runtime: {runtime:.4f}s, Sat var number: {var_count} Closures: {sat_closures}"
                )
        else:
            print("Run failed (non-zero exit). Recording -1.0")
            runtime = -1.0
            error_msg = result.stderr or result.stdout

        return RunResult(runtime, var_count, sat_closures, effective_runner, error_msg)
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

    # FIXME: now we skip all folders with .param because I'm in a rush to test
    # SAT that doesn't work on any .param anyways. Later on we should make a refactor
    # that would run the problem on all the .param files in the folder 
    if check_if_param(model_path.parent):
        print(f"Skipping {model} because a .param file was detected in its folder.")
        db = DatabaseManager(config.db_path)
        db.update_runtime(model, runner, -2.0, run_number, -1, -1)
        sys.exit(0)

    if "conjure" not in runner.lower():
        runtime, var_count, sat_closures, runner, error_msg = time_run(
            runner, model, collect_closures
        )
        effective_runner = runner
    else:
        runtime, var_count, sat_closures, effective_runner, error_msg = (
            time_conjure_run(runner, model, collect_closures)
        )

    db = DatabaseManager(config.db_path)
    db.update_runtime(
        model, effective_runner, runtime, run_number, var_count, sat_closures
    )

    if error_msg:
        db.update_failure(model, effective_runner, error_msg, run_number)
