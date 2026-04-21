# show.py

import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd

# ------------------------
# Load settings
# ------------------------
with Path("settings.json").open("r", encoding="utf-8") as f:
    settings = json.load(f)

db_path = settings["outfile"]


def main() -> None:
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM results", conn)

    print(df)

    if len(sys.argv) == 2 and sys.argv[1] == "with-fails":

        dfails = pd.read_sql("SELECT * FROM failures", conn)

        print(dfails)

    conn.close()

if __name__ == "__main__":
    main()
