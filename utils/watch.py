import sqlite3
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header
from textual.binding import Binding

class SQLiteViewer(App):
    # Setup the htop-style footer controls
    BINDINGS = [
        Binding("f1", "filter", "Filter"),
        Binding("f2", "sort", "Sort"),
        Binding("f3", "insert", "Edit Comment"),
        Binding("q", "quit", "Quit")
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DataTable()
        yield Footer()

    def on_mount(self) -> None:
        self.table = self.query_one(DataTable)
        self.table.cursor_type = "row"
        self.load_data()

    def load_data(self, order_by="model", filter_query=""):
        # Clear existing data when reloading
        self.table.clear(columns=True)
        
        # Connect to your DB (replace with your actual db path)
        # conn = sqlite3.connect("res/db/testing_runsolver-4G-150proc-1800s.db")
        # cur = conn.cursor()
        # cur.execute(f"SELECT model, runner, runtime, comment FROM results {filter_query} ORDER BY {order_by}")
        # rows = cur.fetchall()
        
        # Mock data for demonstration
        self.table.add_columns("Model", "Runner", "Runtime", "Comment")
        mock_rows = [
            ("model_1.essence", "oxide_main_minion", 12.4, ""),
            ("model_2.essence", "oxide_main_sat", 3.1, "Fast"),
        ]
        self.table.add_rows(mock_rows)

    def action_filter(self) -> None:
        self.notify("F1 pressed: Bring up an Input modal to write a WHERE clause.")

    def action_sort(self) -> None:
        self.notify("F2 pressed: Trigger sort on the active column.")

    def action_insert(self) -> None:
        # Get the currently highlighted row
        row_key, _ = self.table.coordinate_to_cell_key(self.table.cursor_coordinate)
        self.notify(f"F3 pressed: Edit comment for row {row_key}")

if __name__ == "__main__":
    app = SQLiteViewer()
    app.run()