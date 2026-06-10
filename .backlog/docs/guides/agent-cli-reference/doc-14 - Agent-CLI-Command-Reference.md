---
id: doc-14
title: Agent CLI Command Reference
type: guide
created_date: "2026-06-10 16:42"
updated_date: "2026-06-10 16:42"
---

## Complete CLI Command Reference

### Task Creation

| Action              | Command                                                                                                                                            |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Create task         | `backlog task create "Title"`                                                                                                                      |
| With description    | `backlog task create "Title" -d "Description"`                                                                                                     |
| With AC             | `backlog task create "Title" --ac "Criterion 1" --ac "Criterion 2"`                                                                                |
| With final summary  | `backlog task create "Title" --final-summary "PR-style summary"`                                                                                   |
| With references     | `backlog task create "Title" --ref src/api.ts --ref https://github.com/issue/123`                                                                  |
| With documentation  | `backlog task create "Title" --doc https://design-docs.example.com`                                                                                |
| With modified files | `backlog task create "Title" --modified-file src/api.ts --modified-file src/ui.ts`                                                                 |
| With all options    | `backlog task create "Title" -d "Desc" -a @sara -s "To Do" -l auth --priority high --ref src/api.ts --doc docs/spec.md --modified-file src/api.ts` |
| Create draft        | `backlog task create "Title" --draft`                                                                                                              |
| Create subtask      | `backlog task create "Title" -p 42`                                                                                                                |

### Task Modification

| Action           | Command                                     |
| ---------------- | ------------------------------------------- |
| Edit title       | `backlog task edit 42 -t "New Title"`       |
| Edit description | `backlog task edit 42 -d "New description"` |
| Change status    | `backlog task edit 42 -s "In Progress"`     |
| Assign           | `backlog task edit 42 -a @sara`             |
| Add labels       | `backlog task edit 42 -l backend,api`       |
| Set priority     | `backlog task edit 42 --priority high`      |

### Acceptance Criteria Management

| Action              | Command                                                                     |
| ------------------- | --------------------------------------------------------------------------- |
| Add AC              | `backlog task edit 42 --ac "New criterion" --ac "Another"`                  |
| Remove AC #2        | `backlog task edit 42 --remove-ac 2`                                        |
| Remove multiple ACs | `backlog task edit 42 --remove-ac 2 --remove-ac 4`                          |
| Check AC #1         | `backlog task edit 42 --check-ac 1`                                         |
| Check multiple ACs  | `backlog task edit 42 --check-ac 1 --check-ac 3`                            |
| Uncheck AC #3       | `backlog task edit 42 --uncheck-ac 3`                                       |
| Mixed operations    | `backlog task edit 42 --check-ac 1 --uncheck-ac 2 --remove-ac 3 --ac "New"` |

### Task Content

| Action               | Command                                                                         |
| -------------------- | ------------------------------------------------------------------------------- |
| Add plan             | `backlog task edit 42 --plan "1. Step one\n2. Step two"`                        |
| Add notes            | `backlog task edit 42 --notes "Implementation details"`                         |
| Add final summary    | `backlog task edit 42 --final-summary "PR-style summary"`                       |
| Append final summary | `backlog task edit 42 --append-final-summary "More details"`                    |
| Clear final summary  | `backlog task edit 42 --clear-final-summary`                                    |
| Add dependencies     | `backlog task edit 42 --dep task-1 --dep task-2`                                |
| Add references       | `backlog task edit 42 --ref src/api.ts --ref https://github.com/issue/123`      |
| Add documentation    | `backlog task edit 42 --doc https://design-docs.example.com --doc docs/spec.md` |
| Set modified files   | `backlog task edit 42 --modified-file src/api.ts --modified-file src/ui.ts`     |

### Multi‑line Input (Description/Plan/Notes/Final Summary)

The CLI preserves input literally — shells do not convert `\n` inside normal quotes. Use one of the following forms, listed in order of preference for AI agents:

**1. Repeat `--append-*` for each line (works in every shell, including sandboxes that block other forms):**

```bash
backlog task edit 42 --notes "First line"
backlog task edit 42 --append-notes "Second line"
backlog task edit 42 --append-notes "Third line"
```

**2. Real newlines inside double quotes (single command — pass an actual line break inside the string):**

```bash
backlog task edit 42 --notes "First line
Second line

Final paragraph"
```

The same shape works for `--desc`, `--plan`, `--final-summary`, and the `--append-*` variants.

**3. Shell-specific shorthand (interactive shells only — some AI agent sandboxes reject these):**

- Bash/Zsh (ANSI‑C quoting):

  ```bash
  backlog task edit 42 --notes $'Line1\nLine2'
  ```

- POSIX sh (command substitution + printf):

  ```bash
  backlog task edit 42 --notes "$(printf 'Line1\nLine2')"
  ```

- PowerShell (backtick‑n):

  ```powershell
  backlog task edit 42 --notes "Line1`nLine2"
  ```

Prefer forms **1** and **2** when running under Claude Code, Codex, or any agent harness that screens commands through a tree‑sitter AST walker — those harnesses reject ANSI‑C strings, command substitutions, and heredoc forms (see issue [#595](https://github.com/MrLesk/Backlog.md/issues/595)).

Do not expect the literal sequence `\n` inside double quotes to become a newline. The CLI stores the backslash and `n` as written.

### Implementation Notes Formatting

- Keep implementation notes concise and time-ordered; focus on progress, decisions, and blockers.
- Use short paragraphs or bullet lists instead of a single long line.
- Use Markdown bullets (`-` for unordered, `1.` for ordered) for readability.
- When using CLI flags like `--append-notes`, remember to include explicit
  newlines. Either repeat the flag once per line:

  ```bash
  backlog task edit 42 --append-notes "- Added new API endpoint" \
    --append-notes "- Updated tests" \
    --append-notes "- TODO: monitor staging deploy"
  ```

  Or pass real newlines inside the quoted argument:

  ```bash
  backlog task edit 42 --append-notes "- Added new API endpoint
  - Updated tests
  - TODO: monitor staging deploy"
  ```

### Final Summary Formatting

- Treat the Final Summary as a PR description: lead with the outcome, then add key changes and tests.
- Keep it clean and structured so it can be pasted directly into GitHub.
- Prefer short paragraphs or bullet lists and avoid raw progress logs.
- Aim to cover: **what changed**, **why**, **user impact**, **tests run**, and **risks/follow‑ups** when relevant.
- Avoid single‑line summaries unless the change is truly tiny.

**Example (good, not rigid):**

```
Added Final Summary support across CLI/MCP/Web/TUI to separate PR summaries from progress notes.

Changes:
- Added `finalSummary` to task types and markdown section parsing/serialization (ordered after notes).
- CLI/MCP/Web/TUI now render and edit Final Summary; plain output includes it.

Tests:
- bun test src/test/final-summary.test.ts
- bun test src/test/cli-final-summary.test.ts
```

### Task Images (Local Assets)

Tasks may include images for screenshots, diagrams, or visual references. Local images are served automatically when using `backlog browser`.

**Storage location:**

- Place image files under the `assets/` folder inside your backlog directory (e.g., `backlog/assets/images/screenshot.png`)

**Supported formats:**

- png, jpg, jpeg, gif, svg, webp, avif (served with correct Content-Type)

**Markdown syntax in tasks:**

```markdown
![example](assets/images/screenshot.png)
```

**Workflow when adding images to tasks:**

1. Move or copy the image file into the `assets/` folder inside your backlog directory (e.g., `backlog/assets/images/screenshot.png`)
2. Then add or edit the task content via CLI, referencing the image using the `assets/<relative-path>` path

**Key points:**

- The path in Markdown starts with `assets/` and maps to the backlog directory's `assets/` folder; do **not** include the backlog directory name itself
- When `backlog browser` is running, these files are automatically available at `assets/<relative-path>`
- You can add images to descriptions, implementation notes, or final summaries using the standard CLI commands

### Document Management

> Docs are used for long-term project reference information, such as development standards, configuration guides, architecture documentation, etc. They differ from `tasks/` (specific tasks), `decisions/` (decision records), and `drafts/` (drafts).

Use Backlog.md public interfaces for document creation and updates so IDs, frontmatter, paths, and search metadata stay consistent.

#### CLI Usage

The CLI supports creating, updating, listing, and viewing documents.

```bash
# Create a new doc (saved under backlog/docs/ by default)
backlog doc create "API Guidelines"

# Create in a subdirectory (nested paths supported)
backlog doc create "Setup Guide" -p guides/setup

# Specify type at creation time
backlog doc create "Architecture" -t guide

# Update content while preserving omitted metadata
backlog doc update doc-1 --content "Updated markdown"

# Update metadata or move a doc within backlog/docs/
backlog doc update doc-1 --title "Setup Handbook" -t guide --tags setup,runbook -p guides

# List all docs (searched globally across subdirectories)
backlog doc list

# View a specific doc
backlog doc view doc-1
```

#### MCP / API Usage

- Use `document_create` to create documents with title, content, optional type/tags, and optional docs-directory-relative path.
- Use `document_update` to update document content, title, type, tags, or path while preserving document metadata.
- Document responses include the persisted docs-relative file path so agents can reference the created file without scanning source internals.

#### Key Rules

- Document paths are relative to `backlog/docs/`; absolute paths and `..` traversal are rejected.
- Supported document types are `readme`, `guide`, `specification`, and `other`.
- Document IDs are global across the entire docs tree, including nested subfolders.
- Prefer CLI, MCP, or Web document APIs over ad-hoc file writes so frontmatter and metadata remain valid.

### Task Operations

| Action                  | Command                                             |
| ----------------------- | --------------------------------------------------- |
| View task               | `backlog task 42 --plain`                           |
| List tasks              | `backlog task list --plain`                         |
| Search tasks            | `backlog search "topic" --plain`                    |
| Search with filter      | `backlog search "api" --status "To Do" --plain`     |
| Search by modified file | `backlog search --modified-file src/api.ts --plain` |
| Filter by status        | `backlog task list -s "In Progress" --plain`        |
| Filter by assignee      | `backlog task list -a @sara --plain`                |
| Archive task            | `backlog task archive 42`                           |
| Demote to draft         | `backlog task demote 42`                            |

---

## Common Issues

| Problem              | Solution                                                           |
| -------------------- | ------------------------------------------------------------------ |
| Task not found       | Check task ID with `backlog task list --plain`                     |
| AC won't check       | Use correct index: `backlog task 42 --plain` to see AC numbers     |
| Changes not saving   | Ensure you're using CLI, not editing files                         |
| Metadata out of sync | Re-edit via CLI to fix: `backlog task edit 42 -s <current-status>` |

---
