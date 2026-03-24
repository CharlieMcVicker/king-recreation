import os
import re
from typing import Dict, List


def _extract_balanced(content: str, pos: int):
    """Extracts a balanced { } block starting from pos."""
    while pos < len(content) and content[pos] != "{":
        pos += 1
    if pos >= len(content):
        return "", pos

    start = pos
    depth = 0
    for i in range(pos, len(content)):
        if content[i] == "{":
            depth += 1
        elif content[i] == "}":
            depth -= 1
            if depth == 0:
                return content[start + 1 : i], i + 1
    return "", len(content)


def _extract_tags(label: str) -> List[str]:
    """Extracts tags inside square brackets, handling nested brackets."""
    tags = []
    i = 0
    while i < len(label):
        if label[i] == "[":
            start = i
            depth = 0
            for j in range(i, len(label)):
                if label[j] == "[":
                    depth += 1
                elif label[j] == "]":
                    depth -= 1
                    if depth == 0:
                        tags.append(label[start + 1 : j])
                        i = j
                        break
            else:
                # Unbalanced bracket
                break
        i += 1
    return tags


def parse_main_toc(
    toc_path: str, known_class_names: List[str]
) -> Dict[str, List[Dict]]:
    """
    Parses the main.toc file to extract verb definitions, TeX representations,
    and their page numbers, grouped by aspect class.
    """
    if not os.path.exists(toc_path):
        return {}

    with open(toc_path, "r", encoding="utf-8") as f:
        content = f.read()

    results = {}

    pos = 0
    while True:
        pos = content.find("\\contentsline", pos)
        if pos == -1:
            break

        pos += len("\\contentsline")

        # First argument: {subsection} or {subsubsection}
        arg1, pos = _extract_balanced(content, pos)
        if arg1 not in ["subsection", "subsubsection"]:
            continue

        # Second argument: The label string
        label, pos = _extract_balanced(content, pos)

        # Third argument: The page number
        page, pos = _extract_balanced(content, pos)

        # Extract tags
        tags = _extract_tags(label)

        # Extract definition
        definition_match = re.search(r"\\textit\s*{(.*)}", label)
        definition = definition_match.group(1) if definition_match else ""

        # Extract verb_tex (everything before the tags and definition)
        first_tag_pos = label.find("[")
        if first_tag_pos != -1:
            verb_tex = label[:first_tag_pos].strip()
        elif definition_match:
            verb_tex = label[: definition_match.start()].strip()
        else:
            verb_tex = label.strip()

        # Clean up trailing dashes/punctuation
        verb_tex = re.sub(r"[- ]+$", "", verb_tex)

        found_classes = []
        for tag in tags:
            # Check if tag is or starts with a known class
            for class_name in known_class_names:
                if tag == class_name:
                    found_classes.append(class_name)
                    continue
                if tag.startswith(class_name + "["):
                    found_classes.append(class_name)
                    continue

        for cls in set(found_classes):
            if cls not in results:
                results[cls] = []
            results[cls].append(
                {
                    "verb_tex": verb_tex,
                    "definition": definition,
                    "page": page,
                    "tags": tags,
                }
            )

    return results


if __name__ == "__main__":
    from king_recreation.paths import MAIN_TOC_PATH
    from tex_dictionary.companion_data import load_aspect_classes

    classes = load_aspect_classes()
    class_names = [c.full_name for c in classes]

    print(f"Parsing {MAIN_TOC_PATH}...")
    results = parse_main_toc(MAIN_TOC_PATH, class_names)

    print(f"Found {len(results)} classes with verbs.")

    # Validation: Assert we found verbs for 'cause' and 'stative' (or variants)
    for target in ["cause", "stative"]:
        found = False
        for cls_name in results.keys():
            if cls_name.startswith(target):
                print(
                    f"Success: Found {len(results[cls_name])} verbs for class {cls_name}"
                )
                found = True
        if not found:
            print(f"Warning: No verbs found for class {target}")

    # Sample output
    if "cause" in results:
        sample = results["cause"][0]
        print(
            f"Sample 'cause' verb: {sample['verb_tex']} -> {sample['definition']} (p. {sample['page']})"
        )
