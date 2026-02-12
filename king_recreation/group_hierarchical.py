import base64
import csv
import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, DefaultDict, Dict, List, Optional, Tuple

from king_recreation.morphemes.prefixes.pronominals import StemType
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


from king_recreation.paths import (
    DERIVATIONAL_CONNECTIONS_PATH,
    HIERARCHICAL_DICT_PATH,
    RECONSTRUCTABLE_VERBS_PATH,
    ROOT_IDS_PATH,
)


def load_all_data() -> Tuple[
    List[ReconstructibleVerb],
    List[Dict[str, str]],
    List[Dict[str, str]],
]:
    verbs_path = RECONSTRUCTABLE_VERBS_PATH
    deriv_conn_path = DERIVATIONAL_CONNECTIONS_PATH
    r_ids_path = ROOT_IDS_PATH

    all_verbs_raw = load_json(verbs_path)
    all_verbs = [ReconstructibleVerb.from_dict(v) for v in all_verbs_raw]
    derivational_connections = load_csv(deriv_conn_path)
    root_ids = load_csv(r_ids_path)

    return (
        all_verbs,
        derivational_connections,
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
    derivational_connections: List[Dict[str, str]],
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

    # Add Derivational Connections
    for row in derivational_connections:
        if row.get("user_approved", None) == "x":
            add_connection(row["from_corpus_ids"], row["to_corpus_ids"], "derivation")

    return parent_map, children_map


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


def sync_root_ids(
    all_verbs: List[ReconstructibleVerb],
    verbs_by_id: Dict[int, ReconstructibleVerb],
    verb_parent_map: Dict[int, int],
    existing_root_ids: List[Dict[str, str]],
) -> Tuple[Dict[int, str], Dict[str, str]]:

    # 1. Parse existing root_ids.csv to find user overrides
    # We need to handle the previous format where 'corpus_ids' was a list
    # and map EACH corpus_id to the override if 'user_edited' was set.
    overrides = {}  # corpus_id_str -> root_id

    for row in existing_root_ids:
        # Check if this is a user edited row
        if row.get("user_edited") == "x":
            rid = row.get("root_id")
            # Old format (or intermediate format) had 'corpus_ids' column
            if "corpus_ids" in row:
                cids = [x.strip() for x in row["corpus_ids"].split(";") if x.strip()]
                for cid in cids:
                    overrides[cid] = rid
            # Check for new format (corpus_id column) just in case we run this on already-migrated file
            elif "corpus_id" in row:
                overrides[row["corpus_id"]] = rid

    # 2. Build rows for every verb
    csv_rows = []
    verb_to_root_id = {}
    synthetic_to_root_id = {}

    # Helper to clean strings
    def clean(s):
        return s if s is not None else ""

    for i, verb in enumerate(all_verbs):
        h = verb.h_grade_root
        g = verb.glottal_grade_root
        cls = verb.class_name
        morph = verb.post_root_morpheme
        defn = verb.definition

        # Determine Corpus ID Key
        if verb.corpus_id is not None:
            cid_key = str(verb.corpus_id)
        else:
            cid_key = f"synthetic-{i}"

        # Determine Root ID
        default_id = f"{h}|{g or ''}"

        # Check override
        root_id = default_id
        is_edited = ""

        if cid_key in overrides:
            root_id = overrides[cid_key]
            is_edited = "x"

        # Populate Maps
        if verb.corpus_id is not None:
            verb_to_root_id[verb.corpus_id] = root_id
        else:
            synthetic_to_root_id[cid_key] = root_id

        # Add to CSV rows
        csv_rows.append(
            {
                "corpus_id": cid_key,
                "definition": defn,
                "h_grade": h,
                "g_grade": clean(g),
                "class": cls,
                "post_root_morpheme": clean(morph),
                "root_id": root_id,
                "user_edited": is_edited,
            }
        )

    # 3. Sort rows for stability
    # Sort by (h_grade, g_grade, class, corpus_id)
    csv_rows.sort(
        key=lambda x: (
            x["h_grade"] or "",
            x["g_grade"] or "",
            x["class"] or "",
            # Handle synthetic IDs in sort carefully? using string sort is fine
            x["corpus_id"],
        )
    )

    # 4. Save CSV
    r_ids_path = ROOT_IDS_PATH
    fieldnames = [
        "corpus_id",
        "definition",
        "h_grade",
        "g_grade",
        "class",
        "post_root_morpheme",
        "root_id",
        "user_edited",
    ]
    with open(r_ids_path, "w", encoding="utf-8", newline="") as f:
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

        node = RootNode(
            h_grade_root=data["h"],
            glottal_grade_root=data["g"],
            slug=get_root_slug_from_id(root_id),
            classes=classes_list,
        )

        return node

    final_output = []

    # Identify top-level root IDs
    # Now that we removed root-to-root logic, all grouped roots are "top level" in this context
    for root_id, data in root_groups.items():
        h, g = data["h"], data.get("g", "")
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
    output_path = HIERARCHICAL_DICT_PATH

    # 1. Load Data
    (
        all_verbs,
        derivational_connections,
        existing_root_ids,
    ) = load_all_data()

    # 2. Build Verb Graphs
    verbs_by_id = build_verb_index(all_verbs)
    parent_map, children_map = build_connection_graphs(
        derivational_connections, verbs_by_id
    )

    # 3. Sync Root IDs
    # We need to assign stable IDs to verbs and group them accordingly
    # This also saves the root_ids.csv for user maintenance
    verb_to_root_id, synthetic_to_root_id = sync_root_ids(
        all_verbs, verbs_by_id, parent_map, existing_root_ids
    )

    # 4. Identify Top Level Verbs
    top_level_ids = identify_top_level_nodes(all_verbs, parent_map)

    # 5. Group Verbs into Roots by ID
    root_groups = group_roots_final(
        top_level_ids,
        all_verbs,
        verbs_by_id,
        children_map,
        verb_to_root_id,
        synthetic_to_root_id,
    )

    # 6. Construct Final Hierarchy
    final_output = build_final_hierarchy(root_groups)

    # 7. Save
    save_output(final_output, output_path)


if __name__ == "__main__":
    main()
