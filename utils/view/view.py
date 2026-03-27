# view/view.py

import sys
import sqlite3
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header
from textual.binding import Binding
from edit_cell import EditCellModal
from sort_modal import SortModal


class SQLiteViewer(App):
    # Setup the htop-style footer controls
    BINDINGS = [
        Binding("f1", "filter", "Filter"),
        Binding("f2", "sort", "Sort"),
        Binding("f3", "insert", "Edit Comment"),
        Binding("q", "quit", "Quit"),
        Binding("shift+right", "fast_right", "Fast Right", show=False),
        Binding("shift+left", "fast_left", "Fast Left", show=False),
    ]

    def action_fast_right(self) -> None:
        # Pan the viewport right by 30 characters
        self.table.scroll_to(x=self.table.scroll_x + 30, animate=False)

    def action_fast_left(self) -> None:
        # Pan the viewport left by 30 characters
        self.table.scroll_to(x=max(0, self.table.scroll_x - 30), animate=False)

    def __init__(self, db_path: str):
        super().__init__()
        self.db_path = db_path
        # Track the current sort state so it persists across edits
        self.current_sort = "model ASC"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DataTable()
        yield Footer()

    def on_mount(self) -> None:
        self.table = self.query_one(DataTable)
        self.table.cursor_type = "row"
        self.load_data()

    def load_data(self):
        self.table.clear(columns=True)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                try:
                    cur.execute("ALTER TABLE results ADD COLUMN comment TEXT;")
                except sqlite3.OperationalError:
                    pass

                # Use self.current_sort instead of a hardcoded parameter
                cur.execute(f"SELECT * FROM results ORDER BY {self.current_sort}")

                col_names = [description[0] for description in cur.description]
                self.table.add_columns(*col_names)

                for row in cur.fetchall():
                    clean_row = [str(item) if item is not None else "" for item in row]
                    self.table.add_row(*clean_row)

        except Exception as e:
            self.notify(f"Error loading DB: {e}", severity="error")

    def action_filter(self) -> None:
        self.notify("F1 pressed: Bring up an Input modal to write a WHERE clause.")

    def action_sort(self) -> None:
        if not self.table.columns:
            return

        col_names = [col.label.plain for col in self.table.columns.values()]

        def apply_sort(result: tuple[str, str] | None) -> None:
            if result is not None:
                col, order = result
                # Wrap column in quotes in case of special characters
                self.current_sort = f'"{col}" {order}'
                self.load_data()
                self.notify(f"Sorted by {col} ({order})")

        self.push_screen(SortModal(col_names), apply_sort)

    def action_insert(self) -> None:
        if not self.table.row_count:
            return

        # Get the current row
        row_index = self.table.cursor_coordinate.row

        # Find the exact index of the comment column
        col_names = [col.label.plain for col in self.table.columns.values()]
        if "comment" not in col_names:
            self.notify("Comment column not found.", severity="error")
            return

        comment_col_idx = col_names.index("comment")

        # Get values for the model and its current comment
        model_name = self.table.get_cell_at((row_index, 0))
        current_value = self.table.get_cell_at((row_index, comment_col_idx))

        def check_and_save(new_value: str | None) -> None:
            if new_value is not None:
                self.save_cell(model_name, "comment", new_value)

        self.push_screen(
            EditCellModal(model_name, "comment", current_value), check_and_save
        )

    def save_cell(self, model: str, column: str, value: str) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Wrap column name in quotes in case it has special characters
                conn.execute(
                    f'UPDATE results SET "{column}" = ? WHERE model = ?', (value, model)
                )
            self.notify(f"Updated {column} for {model}")

            # Save cursor position, reload, and restore position
            current_coord = self.table.cursor_coordinate
            self.load_data()
            self.table.move_cursor(row=current_coord.row, column=current_coord.column)

        except Exception as e:
            self.notify(f"Failed to save: {e}", severity="error")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python watch.py <path_to_db>")
        sys.exit(1)

    app = SQLiteViewer(db_path=sys.argv[1])
    app.run()
