## uv

This repo uses uv as a project manager. To add new deps just do `uv add <depname>`. To run scripts do `uv run <path>`

## Setup

The database will be created automatically if it does not exist. However, if you want to reset it, you can use `utils/setup.py` (this will **drop the existing results table**).

```bash
uv run utils/setup.py
```

## Running the Timer

To time a model with a specific runner, use `utils/timer.py`. The script will execute the command defined in `settings.json`, measure the wall-clock time, and store it in the database.

### Usage
```bash
uv run utils/timer.py <runner_name> <path_to_model>
```

### Example
```bash
uv run utils/timer.py oxide_main_sat ./models/basic/bool/01/bool-01.essence
```

If the execution fails (non-zero exit code), the runtime is recorded as `-1.0` in the `results` table, and also it would put the captured error in the `failures` table.

## Database Schema

The results are stored in a table named `results` with the following structure:
- `model`: (Primary Key) The path to the essence model.
- One column for each runner defined in `settings.json` (e.g., `oxide_main_sat`, `cat`), storing the runtime as a `REAL`.

