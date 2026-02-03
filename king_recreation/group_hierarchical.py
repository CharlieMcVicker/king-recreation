import json
import csv
import os
import sys
from collections import defaultdict


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_ids(id_str):
    if not id_str:
        return []
    return [int(x.strip()) for x in id_str.split(";") if x.strip().isdigit()]


def main():
    print("Grouping verbs hierarchically...")

    verbs_path = "artifacts/data/reconstructable_verbs.json"
    root_conn_path = "artifacts/data/root_connections.csv"
    mv_conn_path = "artifacts/data/middle_voice_connections.csv"
    output_path = "artifacts/data/hierarchical-dict.json"

    # 1. Load Data
    all_verbs = load_json(verbs_path)
    root_connections = load_csv(root_conn_path)
    mv_connections = load_csv(mv_conn_path)

    # Index verbs by corpus_id
    verbs_by_id = {}
    for v in all_verbs:
        if v.get("corpus_id") is not None:
            verbs_by_id[v["corpus_id"]] = v

    # 2. Build Graph
    # child_id -> parent_id (assuming single parent for hierarchy)
    # parent_id -> list of child_ids
    # Also track connection type: "root" or "mv"

    parent_map = {}
    children_map = defaultdict(list)

    # Helper to add connection
    def add_connection(from_ids_str, to_ids_str, conn_type):
        children = parse_ids(from_ids_str)  # "from" is derived (child)
        parents = parse_ids(to_ids_str)  # "to" is base (parent)

        # We need to map specific child instance to specific parent instance.
        # The CSV gives lists of IDs. Usually 1-to-1 or 1-to-many.
        # We will assume that if there are multiple parents, they are effectively the same "node" conceptually,
        # but for tree building we need to pick one or handle it.
        # Actually, if "Visiting" (208) comes from "Finding" (207), 207 is parent of 208.

        for child_id in children:
            if child_id not in verbs_by_id:
                continue

            # Find a valid parent
            parent_id = None
            for pid in parents:
                if pid in verbs_by_id:
                    parent_id = pid
                    break

            if parent_id is not None:
                # Store connection
                # Check for cycles or existing parent (tree constraint)
                if child_id in parent_map:
                    # Already has parent.
                    # Prefer "root" connection over "mv"? Or just first one?
                    # Since we want a tree, we stick with first valid parent.
                    continue

                parent_map[child_id] = parent_id
                children_map[parent_id].append({"id": child_id, "type": conn_type})

    # Add Root Connections (Derivational)
    for row in root_connections:
        if row.get("user_approved", None) == "x":
            add_connection(row["from_corpus_ids"], row["to_corpus_ids"], "derivation")

    # Add Middle Voice Connections
    for row in mv_connections:
        if row.get("user_approved", None) == "x":
            add_connection(row["from_corpus_ids"], row["to_corpus_ids"], "middle_voice")

    # 3. Identify Top Level Nodes
    # Nodes that have no parent in the graph are top level.
    # Note: verbs with no connections at all are also top level.

    top_level_ids = []
    for verb in all_verbs:
        cid = verb.get("corpus_id")
        if cid is not None:
            if cid not in parent_map:
                top_level_ids.append(cid)
        # verbs with null corpus_id are ignored for graph (can't be connected),
        # but maybe we should list them if they are roots?
        # The prompt says: "roots that can't be explained by any connection will be top level nodes"
        # If corpus_id is null, it can't be in connections, so it is top level.
        # But we need a way to group them.
        # For now, let's treat null IDs as top level but they can't have children.

    # Include null ids
    for verb in all_verbs:
        if verb.get("corpus_id") is None:
            # handle null ids?
            # For grouping logic, we need objects.
            # We can treat them as top level.
            pass

    # 4. Construct Hierarchy
    # We first group Top Level Nodes by (h_grade_root, glottal_grade_root).

    root_groups = defaultdict(lambda: defaultdict(list))

    # Recursive function to build tree for a verb
    def build_tree(verb_id):
        verb = verbs_by_id[verb_id]

        node = {**verb, "derivations": [], "middle_voice": []}

        # Get children
        children = children_map.get(verb_id, [])

        # Group children by class to form "Group Nodes"?
        # The prompt: "root/g_grade -> class -> (class ->) -> middle voice -> pronoun set"
        # Since we are building the JSON for the "class" level or "verb" level?
        # "roots that can't be explained... will be top level nodes... then we will traverse to make a tree underneath the word"

        # Let's group children by connection type first
        deriv_children = [c for c in children if c["type"] == "derivation"]
        mv_children = [c for c in children if c["type"] == "middle_voice"]

        # Process Derivations
        # They should be grouped by class.
        # However, multiple children might have same class.
        # We recursively build their trees.

        # To match "class -> (class ->)", we should probably return a list of Verb Objects (which contain their own class info).
        # The consumer of this JSON will likely render them.

        for child in deriv_children:
            child_node = build_tree(child["id"])
            node["derivations"].append(child_node)

        for child in mv_children:
            child_node = build_tree(child["id"])
            node["middle_voice"].append(child_node)

        return node

    # Process all top level verbs
    for vid in top_level_ids:
        verb = verbs_by_id[vid]
        h = verb["h_grade_root"]
        g = verb["glottal_grade_root"]
        cls = verb["class_name"]

        # We group by Root Strings first
        # But inside, we might want to group by "Same Verb Config".
        # e.g. "Finding" (Set A) and "Finding" (Set B).
        # They are separate "Top Level Nodes" but belong to same "Atomic Verb Concept".
        # The prompt: "Group by the following order: root/g_grade -> class -> ..."

        # So we add to a structure:
        # root_groups[(h,g)][class].append(tree_node)

        tree_node = build_tree(vid)
        root_groups[(h, g)][cls].append(tree_node)

    # Also handle null corpus_ids
    for verb in all_verbs:
        if verb.get("corpus_id") is None:
            h = verb["h_grade_root"]
            g = verb["glottal_grade_root"]
            cls = verb["class_name"]
            # Create a simple node
            node = {**verb, "derivations": [], "middle_voice": []}
            root_groups[(h, g)][cls].append(node)

    # Transform into list format
    # [ { h_grade, glottal_grade, slug, classes: [ { class_name, verbs: [ ... ] } ] } ]

    final_output = []

    for (h, g), class_map in root_groups.items():
        # Create Slug
        # Logic from data.ts: if exactly 2 grades and one is null, merge?
        # The Python logic in analyze_matches does this.
        # But here h/g are keys.
        # We can replicate standard slug generation or just use h_grade if g is null.
        # Let's create a unique slug for the (h, g) pair.
        slug = f"{h}|{g}" if g else h
        # Ideally parsing logic for slug is consistent with frontend.
        # Frontend uses base64url(h|g).
        # We can just output h/g and let frontend handle slug, or generate it.
        # Let's just output data.

        classes_list = []
        for cls_name, verbs in class_map.items():
            classes_list.append({"class_name": cls_name, "verbs": verbs})

        # Sort classes by name
        classes_list.sort(key=lambda x: x["class_name"])

        final_output.append(
            {"h_grade_root": h, "glottal_grade_root": g, "classes": classes_list}
        )

    # Sort roots
    final_output.sort(key=lambda x: x["h_grade_root"])

    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    print(f"Hierarchical dictionary saved to {output_path}")


if __name__ == "__main__":
    main()
