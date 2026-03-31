# view/view.py

import sys
import sqlite3
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header
from textual.coordinate import Coordinate
from textual.binding import Binding
from edit_cell import EditCellModal
from sort_modal import SortModal
from filter_modal import FilterModal


class SQLiteViewer(App):
    table: DataTable

    BINDINGS = [
        Binding("t", "switch_table", "Next Table"),
        Binding("f1", "filter", "Filter"),
        Binding("f2", "sort", "Sort"),
        Binding("f3", "insert", "Edit Comment"),
        Binding("q", "quit", "Quit"),
        Binding("shift+right", "fast_right", "Fast Right", show=False),
        Binding("shift+left", "fast_left", "Fast Left", show=False),
    ]

    def __init__(self, db_path: str):
        super().__init__()
        self.db_path = db_path
        self.current_sort = "model ASC"
        self.current_filter = ""
        self.tables = []
        self.current_table_index = 0
        self.current_table = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DataTable()
        yield Footer()

    def on_mount(self) -> None:
        self.table = self.query_one(DataTable)
        self.table.cursor_type = "row"

        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
                self.tables = [row[0] for row in cur.fetchall()]

            if self.tables:
                self.current_table = self.tables[0]
            else:
                self.tables = ["results"]
                self.current_table = "results"
        except Exception as e:
            self.notify(f"Could not read tables: {e}", severity="error")

        self.load_data()

    def load_data(self):
        self.table.clear(columns=True)
        self.sub_title = f"Table: {self.current_table}"  # Updates the header

        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                try:
                    cur.execute(
                        f"ALTER TABLE {self.current_table} ADD COLUMN comment TEXT;"
                    )
                except sqlite3.OperationalError:
                    pass

                # Build the query dynamically
                query = f"SELECT * FROM {self.current_table}"
                if self.current_filter.strip():
                    query += f" WHERE {self.current_filter}"
                query += f" ORDER BY {self.current_sort}"

                cur.execute(query)

                col_names = [description[0] for description in cur.description]
                self.table.add_columns(*col_names)

                for row in cur.fetchall():
                    clean_row = [str(item) if item is not None else "" for item in row]
                    self.table.add_row(*clean_row)

        except Exception as e:
            self.notify(f"Query Error: {e}", severity="error")

    def action_switch_table(self) -> None:
        if not self.tables:
            return

        self.current_table_index = (self.current_table_index + 1) % len(self.tables)
        self.current_table = self.tables[self.current_table_index]

        # Reset states for the new table
        self.current_sort = "model ASC"
        self.current_filter = ""

        self.load_data()
        self.notify(f"Switched to table: {self.current_table}")

    def action_filter(self) -> None:
        def apply_filter(new_filter: str | None) -> None:
            if new_filter is not None:
                self.current_filter = new_filter.strip()
                self.load_data()
                if self.current_filter:
                    self.notify(f"Filter applied: {self.current_filter}")
                else:
                    self.notify("Filter cleared.")

        self.push_screen(FilterModal(self.current_filter), apply_filter)

    def action_sort(self) -> None:
        if not self.table.columns:
            return

        col_names = [col.label.plain for col in self.table.columns.values()]

        def apply_sort(result: tuple[str, str] | None) -> None:
            if result is not None:
                col, order = result
                self.current_sort = f'"{col}" {order}'
                self.load_data()
                self.notify(f"Sorted by {col} ({order})")

        self.push_screen(SortModal(col_names), apply_sort)

    def action_insert(self) -> None:
        if not self.table.row_count:
            return

        row_index = self.table.cursor_coordinate.row

        col_names = [col.label.plain for col in self.table.columns.values()]
        if "comment" not in col_names:
            self.notify("Comment column not found.", severity="error")
            return

        comment_col_idx = col_names.index("comment")
        model_name = self.table.get_cell_at(Coordinate(row_index, 0))
        current_value = self.table.get_cell_at(Coordinate(row_index, comment_col_idx))

        def check_and_save(new_value: str | None) -> None:
            if new_value is not None:
                self.save_cell(model_name, "comment", new_value)

        self.push_screen(
            EditCellModal(model_name, "comment", current_value), check_and_save
        )

    def save_cell(self, model: str, column: str, value: str) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    f'UPDATE {self.current_table} SET "{column}" = ? WHERE model = ?',
                    (value, model),
                )
            self.notify(f"Updated {column} for {model}")

            current_coord = self.table.cursor_coordinate
            self.load_data()
            self.table.move_cursor(row=current_coord.row, column=current_coord.column)

        except Exception as e:
            self.notify(f"Failed to save: {e}", severity="error")

    def action_fast_right(self) -> None:
        self.table.scroll_to(x=self.table.scroll_x + 30, animate=False)

    def action_fast_left(self) -> None:
        self.table.scroll_to(x=max(0, self.table.scroll_x - 30), animate=False)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python view.py <path_to_db>")
        sys.exit(1)

    app = SQLiteViewer(db_path=sys.argv[1])
    app.run()
