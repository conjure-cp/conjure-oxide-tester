## Running the test runner

Refer to the usage comment in `runnner/run_tests.sh`. For instructions on running the test runner.

- If the execution fails (non-zero exit code), the runtime is recorded as `-1.0` in the `results` table, and the captured error is stored in the `failures` table.
- If a model is skipped (e.g., because a `.param` file is detected in its folder), the runtime is recorded as `-2.0`.

## View and update the db

This repo implements sqlite viewer for easy review. Why? Because we needed an easy way of looking up, and commenting in the database entries from the terminal when running tests on dietrich. Refer to the [README in view folder](src/view/README.md) for control documentation. 

## Setup

If you want to reset the db, you can use `utils/setup.py` (this will **drop the existing results table**).

```bash
uv run src/setup.py
```

## uv

This repo uses uv as a project manager. To add new dependencies just do `uv add <depname>`. To run scripts do `uv run <path>`

## ty

This repo uses `ty` as a type checker. Highly reccomend to [download ty](https://marketplace.visualstudio.com/items?itemName=astral-sh.ty) to your VScode to get updates on your types in real life