# show.py

from pathlib import Path
import sqlite3
import json
import pandas as pd
import sys


# ------------------------
# Load settings
# ------------------------
with Path("settings.json").open("r", encoding="utf-8") as f:
    settings = json.load(f)

db_path = settings["outfile"]


def main():
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM results", conn)

    print(df)

    if len(sys.argv) == 2 and sys.argv[1] == "with-fails":

        dfails = pd.read_sql("SELECT * FROM failures", conn)

        print(dfails)

    conn.close()

if __name__ == "__main__":
    main()
