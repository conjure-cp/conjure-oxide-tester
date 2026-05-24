# database_manager.py

import sqlite3
from contextlib import closing


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def update_runtime(
        self,
        model: str,
        runner: str,
        runtime: float,
        run_number: int,
        var_count: int,
        sat_closures: int,
    ) -> None:
        with closing(self._get_connection()) as conn:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO results (model, run_number)
                    VALUES (?, ?)
                    ON CONFLICT(model, run_number) DO NOTHING
                    """,
                    (model, run_number),
                )

                closure_col = f"{runner}_closures"
                var_col = f"{runner}_variables"

                if (
                    "sat" in runner.lower()
                    or "conjure" in runner.lower()
                    or sat_closures != -1
                ):
                    # Dynamically add columns if they don't exist
                    for col in [
                        (runner, "REAL"),
                        (var_col, "INTEGER"),
                        (closure_col, "INTEGER"),
                    ]:
                        try:
                            conn.execute(
                                f'ALTER TABLE results ADD COLUMN "{col[0]}" {col[1]};'
                            )
                        except sqlite3.OperationalError:
                            pass

                    query = f'UPDATE results SET "{runner}" = ?, "{var_col}" = ?, "{closure_col}" = ? WHERE model = ? AND run_number = ?'
                    conn.execute(
                        query, (runtime, var_count, sat_closures, model, run_number)
                    )
                else:
                    try:
                        conn.execute(f'ALTER TABLE results ADD COLUMN "{runner}" REAL;')
                    except sqlite3.OperationalError:
                        pass

                    query = f'UPDATE results SET "{runner}" = ? WHERE model = ? AND run_number = ?'
                    conn.execute(query, (runtime, model, run_number))

    def update_failure(
        self, model: str, runner: str, error_msg: str, run_number: int
    ) -> None:
        with closing(self._get_connection()) as conn:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO failures (model, runner, run_number, error_msg)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(model, runner, run_number)
                    DO UPDATE SET error_msg = excluded.error_msg
                    """,
                    (model, runner, run_number, error_msg),
                )
