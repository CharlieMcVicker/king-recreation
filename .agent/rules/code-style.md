---
trigger: always_on
---

# Code Style & Project Structure Rules

## Project Structure
The project is organized to be run as a Python module from the repository root.

```text
king-recreation/ (Repo Root)
├── king_recreation/        # Main Python Package
│   ├── __init__.py
│   └── ...
├── tests/                  # Unit tests
├── data/                   # Immutable input data
├── artifacts/              # Program outputs
├── requirements.txt        # Dependencies
└── .venv/                  # Virtual Environment
```

## Running Code
-   All code must be runnable from the repository root (e.g., `python3 -m king_recreation.script_name`).
-   Do not rely on being inside the `king_recreation/` subdirectory.

## Data & Artifacts
-   **Input Data**: Files in `data/` are IMMUTABLE. Do not modify them programmatically.
-   **Outputs**: All program outputs must be written to `artifacts/`.
-   **Paths**: Scripts should assume they are running from the repo root. Use relative paths like `./data/input.csv` and `./artifacts/output.json`.
-   **Formats**: Artifacts must be easily diffable:
    -   **JSON**: Use indentation (e.g., `indent=4`) and sort keys (`sort_keys=True`).
    -   **CSV**: Ensure deterministic row ordering where possible.

## Virtual Environment & Dependencies
-   **Environment**: A virtual environment named `.venv` is expected at the project root.
-   **Activation**: Always activate the virtual environment before running scripts (e.g., `source .venv/bin/activate`).
-   **Dependencies**: Manage dependencies via `requirements.txt`.
-   **Exclusion**: Do not commit `.venv` to version control.

## Documentation
-   **README.md**: The `README.md` is the source of truth for the project's process and script interfaces.
-   **Updating**:
    -   Update `README.md` when adding wholly new features or top-level scripts.
    -   Update `README.md` when clarifying important pre- or post-conditions of processing steps.
    -   **Avoid Bloat**: Fixing implementation to follow established contracts in `README.md` does not require documentation changes.