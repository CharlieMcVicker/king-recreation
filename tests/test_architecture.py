import ast
import os


def get_imports(filepath):
    """Parses a Python file and returns a list of imported module names."""
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except SyntaxError:
            return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def test_morphology_architecture_boundary():
    """
    Ensures that the 'morphology' package never imports from
    'dictionary_pipeline' or 'tex_dictionary'.
    """
    morphology_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "morphology"
    )

    violations = []

    for root, _, files in os.walk(morphology_dir):
        for file in files:
            if not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)
            imports = get_imports(filepath)

            for imp in imports:
                if imp.startswith("dictionary_pipeline") or imp.startswith(
                    "tex_dictionary"
                ):
                    # Record relative path for cleaner output
                    rel_path = os.path.relpath(
                        filepath, start=os.path.dirname(morphology_dir)
                    )
                    violations.append((rel_path, imp))

    if violations:
        error_msg = "Architecture Violation! 'morphology' cannot import from pipeline packages:\n"
        for filepath, module in violations:
            error_msg += f"  - {filepath} imports '{module}'\n"
        assert False, error_msg
