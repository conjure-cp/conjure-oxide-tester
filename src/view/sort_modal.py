# view/sort_modal

from textual.widgets import Select
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Grid
from textual.widgets import Button, Label


class SortModal(ModalScreen[tuple[str, str]]):
    """Screen with a dialog to select sort column and order."""

    CSS = """
    SortModal {
        align: center middle;
    }
    #sort_dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 1fr 1fr;
        padding: 1 2;
        width: 60;
        height: 15;
        border: thick $background 80%;
        background: $surface;
    }
    #sort_label { column-span: 2; content-align: center middle; width: 100%; height: 100%; }
    Button, Select { width: 100%; }
    """

    def __init__(self, columns: list[str]):
        super().__init__()
        self.columns = columns

    def compose(self) -> ComposeResult:
        col_options = [(col, col) for col in self.columns]
        order_options = [("Ascending", "ASC"), ("Descending", "DESC")]

        yield Grid(
            Label("Select column and order to sort by:", id="sort_label"),
            Select(col_options, id="col_select", value=self.columns[0]),
            Select(order_options, id="order_select", value="ASC"),
            Button("Apply Sort", variant="success", id="apply"),
            Button("Cancel", variant="error", id="cancel"),
            id="sort_dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "apply":
            col = self.query_one("#col_select", Select).value
            order = self.query_one("#order_select", Select).value
            self.dismiss((col, order))
        else:
            self.dismiss(None)
