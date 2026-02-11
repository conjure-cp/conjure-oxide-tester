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

def update_by_run(df, essence_model, runner, new_value):
    # df.loc[df["models"] == essence_model, runner] = str(new_value)
    df.loc[df["models"] == essence_model, runner] = new_value

def find_essence_files(directory: str) -> List[str]:
    base = Path(directory)
    if not base.is_dir():
        raise ValueError(f"{directory} is not a directory")

    return [
        str(path.relative_to(base))
        for path in base.rglob("*")
        if path.is_file() and path.suffix in {".essence", ".eprime"}
    ]

