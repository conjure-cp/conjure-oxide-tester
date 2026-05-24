# What is this repo

This is a utility repository for `conjure-oxide`. It contains a test suite composed of Savile Row, Conjure, and conjure-oxide tests, and a script that utilizes GNU parallel to execute Conjure or conjure-oxide runners on that test suite.

## Running the test runner

Refer to the usage comment in `runner/run_tests.sh` for instructions on running the test runner.

- If the execution fails (non-zero exit code), the runtime is recorded as `-1.0` in the `results` table, and the captured error is stored in the `failures` table.
- If a model is skipped (e.g., because a `.param` file is detected in its folder), the runtime is recorded as `-2.0`.

### Why .param is skipped

This is due to time constraints the development team faced. This utility was developed by the SAT team at a point when they did not yet support `lettings`, and they urgently needed to test their work on the test suite provided by this repository. Supporting `.param` files would have required more time than was available, so the decision was made to skip them temporarily.

## View and update the db

This repo implements a SQLite viewer for easy review. Why? Because we needed an easy way of looking up and commenting on database entries from the terminal when running tests on Dietrich. Refer to the [README in the view folder](src/view/README.md) for control documentation.

## Setup

If you want to reset the db, you can use `src/setup.py` (this will **drop the existing results table**).

```bash
uv run src/setup.py
```

## uv

This repo uses `uv` as a project manager. To add new dependencies, use `uv add <depname>`. To run scripts, use `uv run <path>`.

## ty

This repo uses `ty` as a type checker. It is highly recommended to [download ty](https://marketplace.visualstudio.com/items?itemName=astral-sh.ty) for VS Code to get real-time updates on your types.
