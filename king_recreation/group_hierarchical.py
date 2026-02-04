import json
import csv
import os
import sys
import base64
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple, DefaultDict, Set
from dataclasses import dataclass, field
from king_recreation.reconstruct_from_roots import (
    ReconstructibleVerb,
    EnhancedJSONEncoder,
)


@dataclass
class RootClassNode:
    class_name: str
    verbs: List[ReconstructibleVerb] = field(default_factory=list)


@dataclass
class RootNode:
    h_grade_root: str
    glottal_grade_root: Optional[str]
    slug: str
    classes: List[RootClassNode] = field(default_factory=list)
    post_root_derivations: List["RootNode"] = field(default_factory=list)
    morpheme_name: Optional[str] = None
    morpheme_subcase: Optional[str] = None


def get_root_slug(h_grade: str, g_grade: Optional[str]) -> str:
    key = f"{h_grade}|{g_grade or ''}"
    utf8_bytes = key.encode("utf-8")
    return base64.urlsafe_b64encode(utf8_bytes).decode("utf-8").replace("=", "")


def load_json(path: str) -> Any:
    if not os.path.exists(path):
        return []
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


def load_all_data() -> Tuple[
    List[ReconstructibleVerb],
    List[Dict[str, str]],
    List[Dict[str, str]],
    List[Dict[str, str]],
]:
    verbs_path = "artifacts/data/reconstructable_verbs.json"
    root_conn_path = "artifacts/connections/root_connections.csv"
    mv_connections_path = "artifacts/connections/middle_voice_connections.csv"
    post_root_conn_path = "artifacts/connections/post_root_connections.csv"

    all_verbs_raw = load_json(verbs_path)
    all_verbs = [ReconstructibleVerb.from_dict(v) for v in all_verbs_raw]
    root_connections = load_csv(root_conn_path)
    mv_connections = load_csv(mv_connections_path)
    post_root_connections = load_csv(post_root_conn_path)

    return all_verbs, root_connections, mv_connections, post_root_connections


def build_verb_index(
    all_verbs: List[ReconstructibleVerb],
) -> Dict[int, ReconstructibleVerb]:
    verbs_by_id = {}
    for v in all_verbs:
        if v.corpus_id is not None:
            verbs_by_id[v.corpus_id] = v
    return verbs_by_id


def build_connection_graphs(
    root_connections: List[Dict[str, str]],
    mv_connections: List[Dict[str, str]],
    verbs_by_id: Dict[int, ReconstructibleVerb],
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
    Dict[Tuple[str, str], Dict[str, str]],
]:
    # Map ChildRoot -> ParentRoot
    # Root Key: (h_grade, g_grade or "")
    parent_map = {}
    children_map = defaultdict(list)
    morpheme_info = {}

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
            morpheme_info[child_key] = {
                "name": row.get("morpheme_name", ""),
                "subcase": row.get("morpheme_subcase", ""),
            }

    return parent_map, children_map, morpheme_info


def identify_top_level_nodes(
    all_verbs: List[ReconstructibleVerb], parent_map: Dict[int, int]
) -> List[int]:
    top_level_ids = []
    for verb in all_verbs:
        cid = verb.corpus_id
        if cid is not None:
            if cid not in parent_map:
                top_level_ids.append(cid)
    return top_level_ids


def build_tree_node(
    verb_id: int,
    verbs_by_id: Dict[int, ReconstructibleVerb],
    children_map: DefaultDict[int, List[Dict[str, Any]]],
) -> ReconstructibleVerb:
    verb = verbs_by_id[verb_id]

    children = children_map.get(verb_id, [])

    deriv_children = [c for c in children if c["type"] == "derivation"]
    mv_children = [c for c in children if c["type"] == "middle_voice"]

    for child in deriv_children:
        child_node = build_tree_node(child["id"], verbs_by_id, children_map)
        verb.derivations.append(child_node)

    for child in mv_children:
        child_node = build_tree_node(child["id"], verbs_by_id, children_map)
        verb.middle_voice.append(child_node)

    return verb


def group_roots_initial(
    top_level_ids: List[int],
    all_verbs: List[ReconstructibleVerb],
    verbs_by_id: Dict[int, ReconstructibleVerb],
    children_map: DefaultDict[int, List[Dict[str, Any]]],
) -> DefaultDict[
    Tuple[str, str], Dict[str, DefaultDict[str, List[ReconstructibleVerb]]]
]:
    # Returns Dict: (h, g) -> { "classes": {name: [verbs...]} }

    root_groups = defaultdict(lambda: {"classes": defaultdict(list)})

    def get_key(h, g):
        return (h, g if g else "")

    # Process graph-based top level verbs
    for vid in top_level_ids:
        verb = verbs_by_id[vid]
        h = verb.h_grade_root
        g = verb.glottal_grade_root
        cls = verb.class_name

        tree_node = build_tree_node(vid, verbs_by_id, children_map)
        root_groups[get_key(h, g)]["classes"][cls].append(tree_node)

    # Process verbs with null corpus_ids (always top level, no children)
    for verb in all_verbs:
        if verb.corpus_id is None:
            h = verb.h_grade_root
            g = verb.glottal_grade_root
            cls = verb.class_name
            root_groups[get_key(h, g)]["classes"][cls].append(verb)

    return root_groups


def build_final_hierarchy(
    root_groups: Dict[Tuple[str, str], Any],
    root_parent_map: Dict[Tuple[str, str], Tuple[str, str]],
    root_children_map: DefaultDict[Tuple[str, str], List[Tuple[str, str]]],
    morpheme_info: Dict[Tuple[str, str], Dict[str, str]],
) -> List[RootNode]:

    # helper to format a single root node
    def format_node(key: Tuple[str, str]) -> RootNode:
        h, g = key
        data = root_groups.get(key)
        # If data is missing (e.g. root exists in graph but no verbs in it?), create empty
        if not data:
            data = {"classes": {}}

        classes_list = []
        for cls_name, verbs in data["classes"].items():
            classes_list.append(RootClassNode(class_name=cls_name, verbs=verbs))
        classes_list.sort(key=lambda x: x.class_name)

        minfo = morpheme_info.get(key, {})

        node = RootNode(
            h_grade_root=h,
            glottal_grade_root=g,
            slug=get_root_slug(h, g),
            classes=classes_list,
            morpheme_name=minfo.get("name"),
            morpheme_subcase=minfo.get("subcase"),
        )

        # Recurse children
        children_keys = root_children_map.get(key, [])
        for child_key in children_keys:
            node.post_root_derivations.append(format_node(child_key))

        # Sort children by h-grade
        node.post_root_derivations.sort(
            key=lambda x: f"{x.h_grade_root}|{x.glottal_grade_root}"
        )

        return node

    final_output = []

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
    final_output.sort(key=lambda x: x.h_grade_root)
    return final_output


def save_output(data: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder)
    print(f"Hierarchical dictionary saved to {path}")


def main() -> None:
    print("Grouping verbs hierarchically...")
    output_path = "artifacts/data/hierarchical-dict.json"

    # 1. Load Data
    all_verbs, root_connections, mv_connections, post_root_connections = load_all_data()

    # 2. Build Verb Graphs
    verbs_by_id = build_verb_index(all_verbs)
    parent_map, children_map = build_connection_graphs(
        root_connections, mv_connections, verbs_by_id
    )

    # 3. Build Root Graphs
    root_parent_map, root_children_map, morpheme_info = build_root_graph(
        post_root_connections
    )

    # 4. Identify Top Level Verbs
    top_level_ids = identify_top_level_nodes(all_verbs, parent_map)

    # 5. Group Verbs into Roots
    root_groups = group_roots_initial(
        top_level_ids, all_verbs, verbs_by_id, children_map
    )

    # 8. Construct Final Hierarchy
    final_output = build_final_hierarchy(
        root_groups, root_parent_map, root_children_map, morpheme_info
    )

    # 9. Save
    save_output(final_output, output_path)


if __name__ == "__main__":
    main()
