---
trigger: model_decision
description: When working in root module on python files and data
---

# Python Project Structure & Style Rules

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
- All code must be runnable from the repository root (e.g., `python3 -m king_recreation.script_name`).
- Do not rely on being inside the `king_recreation/` subdirectory.

## Virtual Environment & Dependencies
- **Environment**: A virtual environment named `.venv` is expected at the project root.
- **Activation**: Always activate the virtual environment before running scripts (e.g., `source .venv/bin/activate`).
- **Dependencies**: Manage dependencies via `requirements.txt`.
- **Exclusion**: Do not commit `.venv` to version control.
