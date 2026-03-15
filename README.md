## uv

This repo uses uv as a project manager. To add new deps just do `uv add <depname>`. To run scripts do `uv run <path>`

## Setup

Before running tests, you may need to initialize or reset the database. Note that `utils/setup.py` will **drop the existing results table**.

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
uv run utils/timer.py conjure-oxide ./models/basic/bool/01/bool-01.essence
```

If the execution fails (non-zero exit code), the runtime is recorded as `-1.0`.

## Database Schema

The results are stored in a table named `results` with the following structure:
- `model`: (Primary Key) The path to the essence model.
- One column for each runner defined in `settings.json` (e.g., `conjure-oxide`, `cat`), storing the runtime as a `REAL`.

