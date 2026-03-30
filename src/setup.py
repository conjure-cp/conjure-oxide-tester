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
            model TEXT,
            run_number INTEGER,
            {runner_columns},
            PRIMARY KEY (model, run_number)
        )
    """)

    conn.execute("""
        CREATE TABLE failures (
            model TEXT,
            runner TEXT,
            run_number INTEGER,
            error_msg TEXT,
            comment TEXT,
            PRIMARY KEY (model, runner, run_number)
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    conf_str = "Yes, I want to reset my database"

    print(
        "\033[31;1;4m Abandon all hope [of recovering old results], ye who enter here \033[0m"
    )
    print(
        "You are running a python script that will look for your output database and wipe it if it exists. All tables and previous results will be deleted forever."
    )
    confirm = input("Type '" + conf_str + "' to reset your testing db.\n")
    if confirm == conf_str:
        recreate_database()
        print("Database created/recreated successfully.")
    else:
        print("Aborted.")
