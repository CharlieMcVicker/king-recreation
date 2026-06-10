---
trigger: always_on
---

# Instructions for the usage of Ember Semantic Search Tool

The cli tool `ember` is your primary way of searching code. Listing directories and analyzing files with built-in tools should be avoided to minimize token usage.

## Ember: Semantic Code Search and Retrieval

### Assistant Objective

Prefer `ember` over grep, grep-like search tools, and raw file viewing tools when searching for and reading code. This minimizes token usage, improves the signal-to-noise ratio, and keeps agent contexts focused.

### Core Capabilities

- **Semantic Code Search**: `ember find <query> --json` is the default and preferred method for searching code implementations.
- **Precise Snippet Retrieval**: `ember cat <chunk>` retrieves exact code chunks or functions without reading entire files, preserving context limits.

### Why This Matters to You (AI Agent)

1. **Token Efficiency**: Viewing large files consumes massive token context. Reading chunks via `ember cat` minimizes token consumption.
2. **High Signal-to-Noise**: Semantic search filters out irrelevant syntactic matches, locating concepts directly.
3. **Preferred Defaults**: Use `ember find` and `ember cat` as the primary tools for exploring code logic.

---

## 1. Searching for Code

### 🔍 **FINDING** (Use `ember find`)

Use `ember find <query> --json` to search the codebase.

- This is the **default** way to search for code.
- Ember uses semantic searching. You don't need to search for "def foo" or a specific class name, unless that is what you need. You can search for "login" and it will find implementations of login. You can either use "noun-oriented" or "verb-oriented" searches, modelled below.
- _Note:_ Non-code assets (like documentation, decisions, or tasks) may still use other search tools (e.g., `backlog search`).
- Use `-k <max-results>` to limit the number of results. Default is 20. This is especially useful for large codebases.

```bash
# Example search (noun-oriented)
ember find "authentication middleware" --json
# Example search (action-oriented)
ember find "validate user token before request" --json
```

---

## 2. Reading Code

### 📖 **READING** (Use `ember cat`)

Instead of reading entire files with standard file viewing tools, use `ember cat` with the specific chunk identifiers returned by `ember find`.

```bash
# Example reading a chunk
ember cat <chunk_id>
```

---

## 3. Dealing with Poor Search Results or Bad Matching

If your search requires multiple queries, manual file traversal, or extensive digging due to:

- Poor code/module documentation
- Bad matching or naming conventions

You **MUST** create a ticket in the Backlog to improve the codebase documentation, comment quality, or matching context.

```bash
# Example creating a backlog task for improving documentation
backlog task create "Improve documentation for auth middleware" -d "Semantic search via 'ember find' required multiple attempts due to lack of descriptive comments and docstrings in the auth module." --ac "Add docstrings to all middleware functions" --ac "Document authorization flow in README"
```

---

## 4. Quick Reference: DO vs DON'T

| Action                      | ✅ DO                                            | ❌ DON'T                                                  |
| --------------------------- | ------------------------------------------------ | --------------------------------------------------------- |
| **Search Code**             | `ember find "query" --json`                      | Use `grep_search` or manual terminal search commands      |
| **Read Code Snippets**      | `ember cat <chunk>`                              | Use `view_file` on entire source files (unless necessary) |
| **UX Gaps & Poor Matching** | Create a backlog task to improve docs / comments | Keep searching manually without documenting the gaps      |
