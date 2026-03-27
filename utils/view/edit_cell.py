from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Grid
from textual.widgets import Input, Button, Label


class EditCellModal(ModalScreen[str]):
    """Screen with a dialog to edit any cell."""

    CSS = """
    EditCellModal {
        align: center middle;
    }
    #dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 1 2;
        width: 60;
        height: 15;
        border: thick $background 80%;
        background: $surface;
    }
    #question { column-span: 2; height: 1fr; width: 1fr; content-align: center middle; }
    #cell_input { column-span: 2; }
    Button { width: 100%; }
    """

    def __init__(self, model_name: str, column_name: str, current_value: str):
        super().__init__()
        self.model_name = model_name
        self.column_name = column_name
        self.current_value = current_value

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(
                f"Edit [b]{self.column_name}[/b] for:\n[b]{self.model_name}[/b]",
                id="question",
            ),
            Input(value=str(self.current_value), id="cell_input"),
            Button("Save", variant="success", id="save"),
            Button("Cancel", variant="error", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.dismiss(self.query_one(Input).value)
        else:
            self.dismiss(None)
