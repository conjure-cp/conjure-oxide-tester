# setup.py

from pathlib import Path
import sqlite3
import json

# ------------------------
# Load settings
# ------------------------
with Path("settings.json").open("r", encoding="utf-8") as f:
    settings = json.load(f)

db_path = settings["outfile"]
runner_names = list(settings["runner_commands"].keys())


def recreate_database():
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")

    # Drop existing table
    conn.execute("DROP TABLE IF EXISTS results")

    # Build runner columns dynamically
    runner_columns = ", ".join([f'"{r}" REAL' for r in runner_names])

    conn.execute(f"""
        CREATE TABLE results (
            model TEXT PRIMARY KEY,
            {runner_columns}
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    recreate_database()
    print("Database created/recreated successfully.")
