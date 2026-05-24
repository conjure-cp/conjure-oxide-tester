## How use view.py

Usage: `uv run python view.py <path_to_db>`

### Controls

#### Navigation & General
- **`<-` / `->` (Arrow Keys)**: Move the cursor horizontally between columns.
- **`Page Up` / `Page Down`**: Scroll vertically through the data quickly.
- **`Shift` + `->` / `<-`**: Fast horizontal scroll (jumps 30 units).
- **`t`**: Switch to the next table in the database.
- **`q`**: Quit the application.

#### Filtering (`f1`)
- **Open**: Press `f1` to open the **Filter Modal**.
- **Usage**: Enter a valid SQL `WHERE` clause.
    - *Example*: `conjure > 5` or `model LIKE '%min%'`.
- **Clear**: Leave the input blank and press **Apply Filter** to remove the active filter.
- **Confirm/Cancel**: Click **Apply Filter** (or press Enter) to refresh the view, or **Cancel** to discard changes.

#### Sorting (`f2`)
- **Open**: Press `f2` to open the **Sort Modal**.
- **Usage**:
    1.  Select the **Column** to sort by from the first dropdown.
    2.  Select the **Order** (`Ascending` or `Descending`) from the second dropdown.
- **Confirm/Cancel**: Click **Apply Sort** to refresh the table, or **Cancel** to exit.

#### Editing Comments (`f3`)
Allows attaching persistent notes to rows (uses the `model` column as a unique identifier).
- **Open**: Highlight a row and press `f3`.
- **Automatic Setup**: If a `comment` column does not exist, it will be added automatically.
- **Save**: Enter your text and click **Save**.
