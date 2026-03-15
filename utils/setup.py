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

    conn.execute("DROP TABLE IF EXISTS results")
    conn.execute("DROP TABLE IF EXISTS failures")

    runner_columns = ", ".join([f'"{r}" REAL' for r in runner_names])

    conn.execute(f"""
        CREATE TABLE results (
            model TEXT PRIMARY KEY,
            {runner_columns}
        )
    """)
    conn.execute("""
        CREATE TABLE failures (
            model TEXT PRIMARY KEY,
            reason TEXT
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    confirm = input("Type 'I wanna nuke my testing.' to reset your testing db.\n")
    if confirm == "I wanna nuke my testing.":
        recreate_database()
        print("Database created/recreated successfully.")
    else:
        print("Aborted.")
