---
trigger: always_on
---

# General Project Rules

## Data & Artifacts
- **Input Data**: Files in `data/` are IMMUTABLE. Do not modify them programmatically.
- **Outputs**: All program outputs must be written to `artifacts/`.
- **Paths**: Use relative paths from the repository root (e.g., `./data/input.csv`, `./artifacts/output.json`).
- **Formats**: Artifacts must be easily diffable:
    - **JSON**: Use indentation (e.g., `indent=4`) and sort keys (`sort_keys=True`).
    - **CSV**: Ensure deterministic row ordering where possible.

## Documentation
- **README.md**: The `README.md` (and component-specific READMEs like `frontend/README.md`) are the source of truth for the project's state and interfaces.
- **Updating**:
    - Update documentation when adding wholly new features, scripts, or components.
    - Update documentation when clarifying important pre- or post-conditions.
    - **Avoid Bloat**: Fixing implementation to follow established contracts does not require documentation changes.

## Meta Rules
- **Agents and Rules**: Agents are NOT permitted to create, modify, or delete rule files within the `.agent/rules/` directory. All rule changes must be requested and approved by the USER, who will then handle the file operations.

## Scope creep and follow up work
- **Document and hand off** when problems are uncovered or new areas of the code need to be touched unexpectedly, write a follow up statement of work in the root directory. This can be handed off to a subagent down the line. Do not fall down rabbit holes. Dump context to disk and let the user decide how to proceed and if the problem is really what it seems.