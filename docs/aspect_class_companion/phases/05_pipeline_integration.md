# Phase 5: Pipeline Integration & Compilation

## Goal
Integrate the fully functioning companion generator into the primary dictionary build process.

## Context
The companion document (`companion.pdf`) derives its page numbers directly from `main.toc`. Therefore, the `companion.tex` generation and compilation must strictly run *after* `main.tex` has been fully generated and `xelatex main.tex` has completed its passes.

## Step-by-Step Implementation
1. **Main Entry Point Modification:**
   - Open `tex_dictionary/__main__.py`.
   - Locate the function `run_xelatex()` and `main()`.
2. **Execution Timing:**
   - Inside `run_xelatex()`, immediately after `main.tex` is successfully compiled and `main.pdf` is verified to exist on disk:
     - Call the new `generate_companion_tex()` orchestration function (which internally runs Phase 1-4 logic).
     - Print a console message: `Companion TeX generated. Compiling companion.tex...`
3. **XeLaTeX Compilation Trigger:**
   - Replicate the `subprocess.run(["xelatex", "-interaction=batchmode", "companion.tex"])` call blocks.
   - Like `main.tex`, it may require two passes to resolve internal links or formatting safely.
   - Verify `companion.pdf` exists.
4. **Error Handling:**
   - Ensure that if `companion.tex` generation fails (e.g., due to a syntax error in formatting), it does not mask the successful compilation of `main.pdf`, but safely prints a warning and exits correctly.
5. **Validation:**
   - Run `python -m tex_dictionary`.
   - Observe the CLI output reflecting the sequential build of `main.pdf`, `booklet.pdf`, and finally `companion.pdf`. Inspect the final `artifacts/tex/companion.pdf` visual output for accuracy.
