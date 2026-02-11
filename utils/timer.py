from utils import *

from pathlib import Path
from typing import List
import pandas as pd
import sys
import json
import time
import subprocess

with Path("settings.json").open("r", encoding="utf-8") as f:
    settings = json.load(f)

runner_commands = dict(settings["runner_commands"])
csvpath = settings["outfile"]

# def update_by_run(df, essence_model, runner, new_value):
#     # df.loc[df["models"] == essence_model, runner] = str(new_value)
#     df.loc[df["models"] == essence_model, runner] = new_value

# def find_essence_files(directory: str) -> List[str]:
#     base = Path(directory)
#     if not base.is_dir():
#         raise ValueError(f"{directory} is not a directory")

#     return [
#         str(path.relative_to(base))
#         for path in base.rglob("*")
#         if path.is_file() and path.suffix in {".essence", ".eprime"}
#     ]


def time_oxide_run(df, runner, essence_model):
    start = time.perf_counter()
    # run commands
    cmd = f"{runner_commands[runner]} ./{essence_model}"

    print(cmd)

    result = subprocess.run(
        cmd,
        shell=True,
        text=True,
    )

    end = time.perf_counter()

    runtime = end - start

    print(result.returncode)

    if (result.returncode == 0):
        print("runtime:",runtime)
        update_by_run(df, essence_model, runner, runtime)
    else:
        print("fail runtime:",runtime)
        update_by_run(df, essence_model, runner, -1.0)

models = find_essence_files(".");

df = pd.read_csv(settings["outfile"], index_col=False)

time_oxide_run(df, sys.argv[1], sys.argv[2]) 

df.to_csv(csvpath, index=False)
