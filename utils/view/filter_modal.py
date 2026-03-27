from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Grid
from textual.widgets import Input, Button, Label


class FilterModal(ModalScreen[str]):
    """Screen with a dialog to input a SQL WHERE clause."""

    CSS = """
    FilterModal {
        align: center middle;
    }
    #filter_dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 1 2;
        width: 60;
        height: 15;
        border: thick $background 80%;
        background: $surface;
    }
    #filter_label { column-span: 2; height: 1fr; width: 1fr; content-align: center middle; }
    #filter_input { column-span: 2; }
    Button { width: 100%; }
    """

    def __init__(self, current_filter: str):
        super().__init__()
        self.current_filter = current_filter

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(
                "Enter SQL WHERE clause (e.g., [i]conjure > 5[/i] or [i]model LIKE '%min%'[/i]):\nLeave blank to clear.",
                id="filter_label",
            ),
            Input(value=self.current_filter, id="filter_input"),
            Button("Apply Filter", variant="success", id="apply"),
            Button("Cancel", variant="error", id="cancel"),
            id="filter_dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "apply":
            self.dismiss(self.query_one("#filter_input", Input).value)
        else:
            self.dismiss(None)
