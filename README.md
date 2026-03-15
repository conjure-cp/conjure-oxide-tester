## uv

This repo uses uv as a project manager. To add new deps just do `uv add <depname>`. To run scripts do `uv run <path>`

## Setup

If you want to reset the db, you can use `utils/setup.py` (this will **drop the existing results table**).

```bash
uv run utils/setup.py
```

## Running the test runner

Refer to the usage comment in `scripts/run.sh` for instructions on running the test runner.

If the execution fails (non-zero exit code), the runtime is recorded as `-1.0` in the `results` table, and also it would put the captured error in the `failures` table.

