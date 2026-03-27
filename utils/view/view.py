# view.py

import sys
import sqlite3
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header
from textual.binding import Binding
from edit_cell import EditCellModal


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

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DataTable()
        yield Footer()

    def on_mount(self) -> None:
        self.table = self.query_one(DataTable)
        self.table.cursor_type = "row"
        self.load_data()

    def load_data(self, order_by="model"):
        # clear(columns=True) wipes existing columns so we don't duplicate them on reload
        self.table.clear(columns=True)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()

                try:
                    cur.execute("ALTER TABLE results ADD COLUMN comment TEXT;")
                except sqlite3.OperationalError:
                    pass

                cur.execute(f"SELECT * FROM results ORDER BY {order_by}")

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
        self.notify("F2 pressed: Trigger sort on the active column.")

    def action_insert(self) -> None:
        if not self.table.row_count:
            return

        # Get coordinates
        row_index = self.table.cursor_coordinate.row
        col_index = self.table.cursor_coordinate.column

        # Get column names dynamically
        col_names = [col.label.plain for col in self.table.columns.values()]
        column_name = col_names[col_index]

        # Prevent editing the primary key
        if column_name.lower() == "model":
            self.notify("Cannot edit the primary key (model).", severity="warning")
            return

        # Get values
        model_name = self.table.get_cell_at((row_index, 0))
        current_value = self.table.get_cell_at((row_index, col_index))

        def check_and_save(new_value: str | None) -> None:
            if new_value is not None:
                self.save_cell(model_name, column_name, new_value)

        self.push_screen(
            EditCellModal(model_name, column_name, current_value), check_and_save
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
