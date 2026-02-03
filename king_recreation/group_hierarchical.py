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

    all_verbs = load_json(verbs_path)
    root_connections = load_csv(root_conn_path)
    mv_connections = load_csv(mv_conn_path)

    return all_verbs, root_connections, mv_connections


def build_verb_index(all_verbs: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    verbs_by_id = {}
    for v in all_verbs:
        if v.get("corpus_id") is not None:
            verbs_by_id[v["corpus_id"]] = v
    return verbs_by_id


def build_connection_graphs(
    root_connections: List[Dict[str, str]],
    mv_connections: List[Dict[str, str]],
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
) -> DefaultDict[Tuple[str, Optional[str]], DefaultDict[str, List[Dict[str, Any]]]]:
    root_groups = defaultdict(lambda: defaultdict(list))

    # Process graph-based top level verbs
    for vid in top_level_ids:
        verb = verbs_by_id[vid]
        h = verb["h_grade_root"]
        g = verb["glottal_grade_root"]
        cls = verb["class_name"]

        tree_node = build_tree_node(vid, verbs_by_id, children_map)
        root_groups[(h, g)][cls].append(tree_node)

    # Process verbs with null corpus_ids (always top level, no children)
    for verb in all_verbs:
        if verb.get("corpus_id") is None:
            h = verb["h_grade_root"]
            g = verb["glottal_grade_root"]
            cls = verb["class_name"]
            node = {**verb, "derivations": [], "middle_voice": []}
            root_groups[(h, g)][cls].append(node)

    return root_groups


def merge_compatible_groups(
    root_groups: DefaultDict[
        Tuple[str, Optional[str]], DefaultDict[str, List[Dict[str, Any]]]
    ],
) -> DefaultDict[Tuple[str, Optional[str]], DefaultDict[str, List[Dict[str, Any]]]]:
    # We want to merge (h, None) into (h, g) if (h, g) exists and is unique.
    all_keys = list(root_groups.keys())

    # Map h_grade to list of full keys (h, g) where g is NOT None
    h_to_keys_map = defaultdict(list)
    for h, g in all_keys:
        if g is not None:
            h_to_keys_map[h].append((h, g))

    # Process floaters (g is None)
    for h, g in all_keys:
        if g is None:
            candidates = h_to_keys_map.get(h, [])
            if len(candidates) == 1:
                target_key = candidates[0]
                # Merge content from source to target
                source_map = root_groups[(h, None)]
                target_map = root_groups[target_key]

                for cls_name, verbs in source_map.items():
                    target_map[cls_name].extend(verbs)

                # Remove source
                del root_groups[(h, None)]

    return root_groups


def format_output(
    root_groups: DefaultDict[
        Tuple[str, Optional[str]], DefaultDict[str, List[Dict[str, Any]]]
    ],
) -> List[Dict[str, Any]]:
    final_output = []

    for (h, g), class_map in root_groups.items():
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
    return final_output


def save_output(data: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Hierarchical dictionary saved to {path}")


def main() -> None:
    print("Grouping verbs hierarchically...")
    output_path = "artifacts/data/hierarchical-dict.json"

    # 1. Load Data
    all_verbs, root_connections, mv_connections = load_all_data()

    # 2. Build Index and Graph
    verbs_by_id = build_verb_index(all_verbs)
    parent_map, children_map = build_connection_graphs(
        root_connections, mv_connections, verbs_by_id
    )

    # 3. Identify Top Level Nodes
    top_level_ids = identify_top_level_nodes(all_verbs, parent_map)

    # 4. Construct Hierarchy & Group
    root_groups = group_roots_initial(
        top_level_ids, all_verbs, verbs_by_id, children_map
    )

    # 5. Merge Compatible Groups
    root_groups = merge_compatible_groups(root_groups)

    # 6. Format and Save
    final_output = format_output(root_groups)
    save_output(final_output, output_path)


if __name__ == "__main__":
    main()
