# show.py

from pathlib import Path
import sqlite3
import json
import pandas as pd

# ------------------------
# Load settings
# ------------------------
with Path("settings.json").open("r", encoding="utf-8") as f:
    settings = json.load(f)

db_path = settings["outfile"]


def main():
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM results", conn)
    conn.close()

    print(df)


if __name__ == "__main__":
    main()
