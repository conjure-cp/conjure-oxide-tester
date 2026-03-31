## uv

This repo uses uv as a project manager. To add new deps just do `uv add <depname>`. To run scripts do `uv run <path>`

## ty

This repo uses `ty` as a type checker. Highly reccomend to [dl ty](https://marketplace.visualstudio.com/items?itemName=astral-sh.ty) to your VScode to get updates on your types in real life

# view and update the db (for commenting)

This repo has a custom sql viewer where you can update the table from cli easily. Just run `src/view/view.py` and use it.

## Setup

If you want to reset the db, you can use `utils/setup.py` (this will **drop the existing results table**).

```bash
uv run src/setup.py
```

## Running the test runner

Refer to the usage comment in `runnner/run_tests.sh`. For instructions on running the test runner.

If the execution fails (non-zero exit code), the runtime is recorded as `-1.0` in the `results` table, and also it would put the captured error in the `failures` table.

