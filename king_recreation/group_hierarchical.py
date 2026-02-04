import json
import csv
import os
import sys
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple, DefaultDict


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_csv(path: str) -> List[Dict[str, str]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_ids(id_str: str) -> List[int]:
    if not id_str:
        return []
    return [int(x.strip()) for x in id_str.split(";") if x.strip().isdigit()]


def load_all_data() -> (
    Tuple[List[Dict[str, Any]], List[Dict[str, str]], List[Dict[str, str]]]
):
    verbs_path = "artifacts/data/reconstructable_verbs.json"
    root_conn_path = "artifacts/data/root_connections.csv"
    mv_conn_path = "artifacts/data/middle_voice_connections.csv"
    post_root_conn_path = "artifacts/data/post_root_connections.csv"

    all_verbs = load_json(verbs_path)
    root_connections = load_csv(root_conn_path)
    mv_connections = load_csv(mv_conn_path)
    post_root_connections = load_csv(post_root_conn_path)

    return all_verbs, root_connections, mv_connections, post_root_connections


def build_verb_index(all_verbs: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    verbs_by_id = {}
    for v in all_verbs:
        if v.get("corpus_id") is not None:
            verbs_by_id[v["corpus_id"]] = v
    return verbs_by_id


def build_connection_graphs(
    root_connections: List[Dict[str, str]],
    mv_connections: List[Dict[str, str]],
    post_root_connections: List[Dict[str, str]],
    verbs_by_id: Dict[int, Dict[str, Any]],
) -> Tuple[Dict[int, int], DefaultDict[int, List[Dict[str, Any]]]]:
    parent_map = {}
    children_map = defaultdict(list)

    def add_connection(from_ids_str, to_ids_str, conn_type):
        children = parse_ids(from_ids_str)
        parents = parse_ids(to_ids_str)

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
                # Check for cycles or existing parent (tree constraint)
                if child_id in parent_map:
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

    return parent_map, children_map


def build_root_graph(
    post_root_connections: List[Dict[str, str]],
) -> Tuple[
    Dict[Tuple[str, str], Tuple[str, str]],
    DefaultDict[Tuple[str, str], List[Tuple[str, str]]],
]:
    # Map ChildRoot -> ParentRoot
    # Root Key: (h_grade, g_grade or "")
    parent_map = {}
    children_map = defaultdict(list)

    for row in post_root_connections:
        if row.get("user_approved", None) == "x":
            child_h = row["from_h_grade"]
            child_g = row["from_g_grade"]
            parent_h = row["to_h_grade"]
            parent_g = row["to_g_grade"]

            child_key = (child_h, child_g)
            parent_key = (parent_h, parent_g)

            # Prevent cycles
            if child_key in parent_map:
                continue

            parent_map[child_key] = parent_key
            children_map[parent_key].append(child_key)

    return parent_map, children_map


def identify_top_level_nodes(
    all_verbs: List[Dict[str, Any]], parent_map: Dict[int, int]
) -> List[int]:
    top_level_ids = []
    for verb in all_verbs:
        cid = verb.get("corpus_id")
        if cid is not None:
            if cid not in parent_map:
                top_level_ids.append(cid)
    return top_level_ids


def build_tree_node(
    verb_id: int,
    verbs_by_id: Dict[int, Dict[str, Any]],
    children_map: DefaultDict[int, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    verb = verbs_by_id[verb_id]
    node = {**verb, "derivations": [], "middle_voice": []}

    children = children_map.get(verb_id, [])

    deriv_children = [c for c in children if c["type"] == "derivation"]
    mv_children = [c for c in children if c["type"] == "middle_voice"]

    for child in deriv_children:
        child_node = build_tree_node(child["id"], verbs_by_id, children_map)
        node["derivations"].append(child_node)

    for child in mv_children:
        child_node = build_tree_node(child["id"], verbs_by_id, children_map)
        node["middle_voice"].append(child_node)

    return node


def group_roots_initial(
    top_level_ids: List[int],
    all_verbs: List[Dict[str, Any]],
    verbs_by_id: Dict[int, Dict[str, Any]],
    children_map: DefaultDict[int, List[Dict[str, Any]]],
) -> DefaultDict[Tuple[str, str], Dict[str, Any]]:
    # Returns Dict: (h, g) -> { "classes": {name: [verbs...]}, "post_root_derivations": [] }
    # Note: g can be empty string for consistency with build_root_graph

    root_groups = defaultdict(
        lambda: {"classes": defaultdict(list), "post_root_derivations": []}
    )

    def get_key(h, g):
        return (h, g if g else "")

    # Process graph-based top level verbs
    for vid in top_level_ids:
        verb = verbs_by_id[vid]
        h = verb["h_grade_root"]
        g = verb["glottal_grade_root"]
        cls = verb["class_name"]

        tree_node = build_tree_node(vid, verbs_by_id, children_map)
        root_groups[get_key(h, g)]["classes"][cls].append(tree_node)

    # Process verbs with null corpus_ids (always top level, no children)
    for verb in all_verbs:
        if verb.get("corpus_id") is None:
            h = verb["h_grade_root"]
            g = verb["glottal_grade_root"]
            cls = verb["class_name"]
            node = {**verb, "derivations": [], "middle_voice": []}
            root_groups[get_key(h, g)]["classes"][cls].append(node)

    return root_groups


def merge_compatible_groups(
    root_groups: DefaultDict[Tuple[str, str], Dict[str, Any]],
) -> DefaultDict[Tuple[str, str], Dict[str, Any]]:
    # We want to merge (h, "") into (h, g) if (h, g) exists and is unique.
    all_keys = list(root_groups.keys())

    # Map h_grade to list of full keys (h, g) where g is NOT empty
    h_to_keys_map = defaultdict(list)
    for h, g in all_keys:
        if g:
            h_to_keys_map[h].append((h, g))

    # Process floaters (g is empty)
    for h, g in all_keys:
        if not g:
            candidates = h_to_keys_map.get(h, [])
            if len(candidates) == 1:
                target_key = candidates[0]
                # Merge content from source to target
                source_data = root_groups[(h, "")]
                target_data = root_groups[target_key]

                # Merge classes
                for cls_name, verbs in source_data["classes"].items():
                    target_data["classes"][cls_name].extend(verbs)

                # Merge post_root_derivations (though unlikely to exist yet at this stage)
                target_data["post_root_derivations"].extend(
                    source_data["post_root_derivations"]
                )

                # Remove source
                del root_groups[(h, "")]

    return root_groups


def format_root_recursive(
    h: str,
    g: str,
    root_data: Dict[str, Any],
) -> Dict[str, Any]:
    # Format classes
    classes_list = []
    for cls_name, verbs in root_data["classes"].items():
        classes_list.append({"class_name": cls_name, "verbs": verbs})
    classes_list.sort(key=lambda x: x["class_name"])

    # Format children (already nested in construct_root_hierarchy, but we need to ensure they are formatted?)
    # Actually, construct_root_hierarchy builds the structure using references to root_groups values.
    # So if we format recursively here, we might need to be careful.
    # A better approach: construct_root_hierarchy builds the 'logical' nesting using the dicts.
    # This function converts that dict-based tree into the final JSON list format.

    formatted_children = []
    for child in root_data["post_root_derivations"]:
        # Child is a dict {child_h, child_g, classes, post_root_derivations}
        # We need to format it strictly.
        # But wait, the child in 'post_root_derivations' is the raw root_data reference?
        # Yes, see construct_root_hierarchy below.

        # We need to reconstruct the h/g from somewhere?
        # The root_data doesn't store its own h/g keys inside itself explicitly until formatting.
        # We should probably store h/g inside the root_group value during creation or iteration.
        # Let's assume passed-in 'child' is the formatted object or the raw data?
        # Let's handle formatting in a unified pass.
        pass

    return {
        "h_grade_root": h,
        "glottal_grade_root": g,
        "classes": classes_list,
        "post_root_derivations": [],  # Placeholder, will fill
    }


def build_final_hierarchy(
    root_groups: Dict[Tuple[str, str], Dict[str, Any]],
    root_parent_map: Dict[Tuple[str, str], Tuple[str, str]],
    root_children_map: DefaultDict[Tuple[str, str], List[Tuple[str, str]]],
) -> List[Dict[str, Any]]:

    # helper to format a single root node
    def format_node(key: Tuple[str, str]) -> Dict[str, Any]:
        h, g = key
        data = root_groups.get(key)
        # If data is missing (e.g. root exists in graph but no verbs in it?), create empty
        if not data:
            data = {"classes": {}, "post_root_derivations": []}

        classes_list = []
        for cls_name, verbs in data["classes"].items():
            classes_list.append({"class_name": cls_name, "verbs": verbs})
        classes_list.sort(key=lambda x: x["class_name"])

        node = {
            "h_grade_root": h,
            "glottal_grade_root": g,
            "classes": classes_list,
            "post_root_derivations": [],
        }

        # Recurse children
        children_keys = root_children_map.get(key, [])
        for child_key in children_keys:
            node["post_root_derivations"].append(format_node(child_key))

        # Sort children by h-grade
        node["post_root_derivations"].sort(key=lambda x: x["h_grade_root"])

        return node

    final_output = []

    # Identify top level roots
    # A root is top level if it's in root_groups AND not in root_parent_map
    # However, root_groups might contain roots that ARE in root_parent_map (children).
    # We only want to process roots that are NOT children as top-level.

    # Also, we must include roots that are in root_parent_map but NOT in root_groups?
    # (Intermediate roots that have no verbs but connect things?)
    # Generally, we iterate keys in root_groups.

    # Valid Top Level:
    # 1. Any key in root_groups that is NOT a child in root_parent_map.
    # 2. Any key in root_children_map that is a parent but NOT a child (roots with no verbs but have children).

    all_known_roots = (
        set(root_groups.keys())
        | set(root_parent_map.keys())
        | set(root_parent_map.values())
    )

    for key in all_known_roots:
        if key not in root_parent_map:
            # Top level
            final_output.append(format_node(key))

    # Sort final output
    final_output.sort(key=lambda x: x["h_grade_root"])
    return final_output


def save_output(data: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Hierarchical dictionary saved to {path}")


def main() -> None:
    print("Grouping verbs hierarchically...")
    output_path = "artifacts/data/hierarchical-dict.json"

    # 1. Load Data
    all_verbs, root_connections, mv_connections, post_root_connections = load_all_data()

    # 2. Build Verb Graphs
    verbs_by_id = build_verb_index(all_verbs)
    parent_map, children_map = build_connection_graphs(
        root_connections, mv_connections, post_root_connections, verbs_by_id
    )

    # 3. Build Root Graphs
    root_parent_map, root_children_map = build_root_graph(post_root_connections)

    # 4. Identify Top Level Verbs
    top_level_ids = identify_top_level_nodes(all_verbs, parent_map)

    # 5. Group Verbs into Roots
    root_groups = group_roots_initial(
        top_level_ids, all_verbs, verbs_by_id, children_map
    )

    # 6. Merge Compatible Groups
    root_groups = merge_compatible_groups(root_groups)

    # 7. Construct Final Hierarchy
    final_output = build_final_hierarchy(
        root_groups, root_parent_map, root_children_map
    )

    # 8. Save
    save_output(final_output, output_path)


if __name__ == "__main__":
    main()
