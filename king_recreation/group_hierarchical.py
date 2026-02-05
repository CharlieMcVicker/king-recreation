import base64
import csv
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, DefaultDict, Dict, List, Optional, Set, Tuple

from king_recreation.reconstruct_from_roots import (
    EnhancedJSONEncoder,
    ReconstructibleVerb,
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
    List[Dict[str, str]],
]:
    verbs_path = "artifacts/data/reconstructable_verbs.json"
    root_conn_path = "artifacts/connections/root_connections.csv"
    post_root_conn_path = "artifacts/connections/post_root_connections.csv"
    root_ids_path = "artifacts/data/root_ids.csv"

    all_verbs_raw = load_json(verbs_path)
    all_verbs = [ReconstructibleVerb.from_dict(v) for v in all_verbs_raw]
    root_connections = load_csv(root_conn_path)
    post_root_connections = load_csv(post_root_conn_path)
    root_ids = load_csv(root_ids_path)

    return (
        all_verbs,
        root_connections,
        post_root_connections,
        root_ids,
    )


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

    for child in deriv_children:
        child_node = build_tree_node(child["id"], verbs_by_id, children_map)
        verb.derivations.append(child_node)

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
        # Use the root ID assigned to the top-level verb
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


def get_base_root_key(
    verb: ReconstructibleVerb,
    verbs_by_id: Dict[int, ReconstructibleVerb],
    verb_parent_map: Dict[int, int],
    root_parent_map: Dict[Tuple[str, str], Tuple[str, str]],
) -> Tuple[str, str]:
    # 1. Traversed verb connections to find the top verb ancestor
    curr_vid = verb.corpus_id
    if curr_vid is None:
        # Verbs with no ID are always top level in their root
        curr_root = (verb.h_grade_root, verb.glottal_grade_root or "")
    else:
        while curr_vid in verb_parent_map:
            curr_vid = verb_parent_map[curr_vid]
        top_verb = verbs_by_id[curr_vid]
        curr_root = (top_verb.h_grade_root, top_verb.glottal_grade_root or "")

    # 2. Traverse root-to-root connections to find the base root ancestor
    visited = set()
    while curr_root in root_parent_map:
        if curr_root in visited:
            break
        visited.add(curr_root)
        curr_root = root_parent_map[curr_root]

    return curr_root


def sync_root_ids(
    all_verbs: List[ReconstructibleVerb],
    verbs_by_id: Dict[int, ReconstructibleVerb],
    verb_parent_map: Dict[int, int],
    root_parent_map: Dict[Tuple[str, str], Tuple[str, str]],
    existing_root_ids: List[Dict[str, str]],
) -> Tuple[Dict[int, str], Dict[str, str]]:
    # Map from corpus_id (or synthetic negative ID for null-id verbs) to RootID
    verb_to_root_id = {}
    synthetic_to_root_id = {}

    # Map existing approvals: (corpus_id) -> approved_id
    approved_map = {}
    for row in existing_root_ids:
        cid_str = row.get("corpus_id")
        if cid_str and row.get("user_approved") == "x":
            approved_map[cid_str] = row.get("proposed_root_id")

    # We need to assign IDs to every verb.
    # For verbs without corpus_id, we'll use their index in all_verbs as a temporary identifier for the CSV
    csv_rows = []

    for i, verb in enumerate(all_verbs):
        base_h, base_g = get_base_root_key(
            verb, verbs_by_id, verb_parent_map, root_parent_map
        )
        default_id = f"{base_h}|{base_g}"

        cid_key = (
            str(verb.corpus_id) if verb.corpus_id is not None else f"synthetic-{i}"
        )

        assigned_id = approved_map.get(cid_key, default_id)

        if verb.corpus_id is not None:
            verb_to_root_id[verb.corpus_id] = assigned_id
        else:
            synthetic_to_root_id[cid_key] = assigned_id

        # Prepare CSV row
        csv_rows.append(
            {
                "definition": verb.definition,
                "verb_root": f"{verb.h_grade_root}|{verb.glottal_grade_root or ''}",
                "corpus_id": cid_key,
                "base_root_h": base_h,
                "base_root_g": base_g,
                "proposed_root_id": assigned_id,
                "user_approved": "x" if cid_key in approved_map else "",
            }
        )

    # Save the CSV
    root_ids_path = "artifacts/data/root_ids.csv"
    fieldnames = [
        "corpus_id",
        "definition",
        "verb_root",
        "base_root_h",
        "base_root_g",
        "proposed_root_id",
        "user_approved",
    ]
    with open(root_ids_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    return verb_to_root_id, synthetic_to_root_id


def group_roots_with_ids(
    top_level_ids: List[int],
    all_verbs: List[ReconstructibleVerb],
    verbs_by_id: Dict[int, ReconstructibleVerb],
    children_map: DefaultDict[int, List[Dict[str, Any]]],
    verb_to_root_id: Dict[int, str],
) -> DefaultDict[str, Dict[str, Any]]:
    # Returns Dict: root_id -> { "h": h, "g": g, "classes": {name: [verbs...]} }

    root_groups = defaultdict(lambda: {"classes": defaultdict(list)})

    # Process graph-based top level verbs
    for vid in top_level_ids:
        verb = verbs_by_id[vid]
        root_id = verb_to_root_id.get(vid)
        if not root_id:
            # Should not happen with proper sync
            root_id = f"{verb.h_grade_root}|{verb.glottal_grade_root or ''}"

        h = verb.h_grade_root
        g = verb.glottal_grade_root
        cls = verb.class_name

        tree_node = build_tree_node(vid, verbs_by_id, children_map)

        if "h" not in root_groups[root_id]:
            root_groups[root_id]["h"] = h
            root_groups[root_id]["g"] = g or ""

        root_groups[root_id]["classes"][cls].append(tree_node)

    # Process verbs with null corpus_ids
    for i, verb in enumerate(all_verbs):
        if verb.corpus_id is None:
            # We need to find the ID assigned in sync_root_ids
            # Since we don't store synthetic IDs in ReconstructibleVerb, we'll recalculate
            # but ideally we'd pass the mapping we just built.
            # However, the verb itself doesn't have an ID, so we use its index in all_verbs
            # that we used in sync_root_ids.
            # Actually, let's just use the default logic here for simplicity if it's not approved.
            # But we want to support splitting even these.

            # Re-fetch or calculate
            cid_key = f"synthetic-{i}"
            # This is a bit hacky. Let's make sync_root_ids return a mapping for synthetic ones too.
            # Or better, let's change the parameters.
            pass

    return root_groups


def group_roots_final(
    top_level_ids: List[int],
    all_verbs: List[ReconstructibleVerb],
    verbs_by_id: Dict[int, ReconstructibleVerb],
    children_map: DefaultDict[int, List[Dict[str, Any]]],
    verb_to_root_id: Dict[int, str],
    synthetic_to_root_id: Dict[str, str],
) -> DefaultDict[str, Dict[str, Any]]:
    root_groups = defaultdict(lambda: {"classes": defaultdict(list)})

    for vid in top_level_ids:
        verb = verbs_by_id[vid]
        root_id = verb_to_root_id.get(vid)
        h = verb.h_grade_root
        g = verb.glottal_grade_root
        cls = verb.class_name
        tree_node = build_tree_node(vid, verbs_by_id, children_map)

        if "h" not in root_groups[root_id]:
            root_groups[root_id]["h"] = h
            root_groups[root_id]["g"] = g or ""
        root_groups[root_id]["classes"][cls].append(tree_node)

    for i, verb in enumerate(all_verbs):
        if verb.corpus_id is None:
            root_id = synthetic_to_root_id.get(f"synthetic-{i}")
            h = verb.h_grade_root
            g = verb.glottal_grade_root
            cls = verb.class_name
            if "h" not in root_groups[root_id]:
                root_groups[root_id]["h"] = h
                root_groups[root_id]["g"] = g or ""
            root_groups[root_id]["classes"][cls].append(verb)

    return root_groups


def build_final_hierarchy(
    root_groups: Dict[str, Any],
    root_parent_map: Dict[Tuple[str, str], Tuple[str, str]],
    root_children_map: DefaultDict[Tuple[str, str], List[Tuple[str, str]]],
    morpheme_info: Dict[Tuple[str, str], Dict[str, str]],
) -> List[RootNode]:

    # helper to format a single root node
    def format_node(
        key: Tuple[str, str], override_root_id: Optional[str] = None
    ) -> RootNode:
        h, g = key
        # Use root_id for grouping if provided, otherwise reconstruct it
        root_id = override_root_id or f"{h}|{g}"

        data = root_groups.get(root_id)
        # If data is missing (e.g. root exists in graph but no verbs in it?), create empty
        if not data:
            data = {"classes": {}, "h": h, "g": g}

        classes_list = []
        for cls_name, verbs in data["classes"].items():
            classes_list.append(RootClassNode(class_name=cls_name, verbs=verbs))
        classes_list.sort(key=lambda x: x.class_name)

        minfo = morpheme_info.get(key, {})

        node = RootNode(
            h_grade_root=data["h"],
            glottal_grade_root=data["g"],
            slug=get_root_slug_from_id(root_id),
            classes=classes_list,
            morpheme_name=minfo.get("name"),
            morpheme_subcase=minfo.get("subcase"),
        )

        # Recurse children
        # Note: Root children are currently linked by (h, g).
        # We need to decide how to handle splitting children.
        # For now, if a root is split, its children stay with it unless they themselves are reassigned?
        # Actually, if a root is split into ID1 and ID2, both have the same (h, g).
        # The children will be linked to (h, g) in the connections.
        # This means BOTH ID1 and ID2 will show the same children?
        # That's probably correct for now, as splitting children is harder.
        children_keys = root_children_map.get(key, [])
        for child_key in children_keys:
            node.post_root_derivations.append(format_node(child_key))

        # Sort children by h-grade
        node.post_root_derivations.sort(
            key=lambda x: f"{x.h_grade_root}|{x.glottal_grade_root}"
        )

        return node

    final_output = []

    # Identify top-level root IDs
    # A root ID is top-level if its (h, g) is not a child in root_parent_map
    for root_id, data in root_groups.items():
        h, g = data["h"], data.get("g", "")
        if (h, g) not in root_parent_map:
            final_output.append(format_node((h, g), override_root_id=root_id))

    # Sort final output
    final_output.sort(key=lambda x: x.h_grade_root)
    return final_output


def get_root_slug_from_id(root_id: str) -> str:
    utf8_bytes = root_id.encode("utf-8")
    return base64.urlsafe_b64encode(utf8_bytes).decode("utf-8").replace("=", "")


def save_output(data: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder)
    print(f"Hierarchical dictionary saved to {path}")


def main() -> None:
    print("Grouping verbs hierarchically...")
    output_path = "artifacts/data/hierarchical-dict.json"

    # 1. Load Data
    (
        all_verbs,
        root_connections,
        post_root_connections,
        existing_root_ids,
    ) = load_all_data()

    # 2. Build Verb Graphs
    verbs_by_id = build_verb_index(all_verbs)
    parent_map, children_map = build_connection_graphs(root_connections, verbs_by_id)

    # 3. Build Root Graphs
    root_parent_map, root_children_map, morpheme_info = build_root_graph(
        post_root_connections
    )

    # 4. Sync Root IDs
    # We need to assign stable IDs to verbs and group them accordingly
    # This also saves the root_ids.csv for user maintenance
    verb_to_root_id, synthetic_to_root_id = sync_root_ids(
        all_verbs, verbs_by_id, parent_map, root_parent_map, existing_root_ids
    )

    # 5. Identify Top Level Verbs
    top_level_ids = identify_top_level_nodes(all_verbs, parent_map)

    # 6. Group Verbs into Roots by ID
    root_groups = group_roots_final(
        top_level_ids,
        all_verbs,
        verbs_by_id,
        children_map,
        verb_to_root_id,
        synthetic_to_root_id,
    )

    # 8. Construct Final Hierarchy
    final_output = build_final_hierarchy(
        root_groups, root_parent_map, root_children_map, morpheme_info
    )

    # 9. Save
    save_output(final_output, output_path)


if __name__ == "__main__":
    main()
