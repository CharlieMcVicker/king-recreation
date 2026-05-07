import base64
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from king_recreation.phases.group_hierarchical.artifacts import (
    load_derivational_connections,
    load_root_ids_overrides,
    save_hierarchical_dict,
    save_root_ids,
)
from king_recreation.phases.select_canonical_derivations.artifacts import (
    load_reconstructable_verbs as load_raw_reconstructable_verbs,
)
from king_recreation.reconstruction import ReconstructableVerb
from king_recreation.utils import EnhancedJSONEncoderFactory

EnhancedJSONEncoder = EnhancedJSONEncoderFactory(lambda d: d.pop("user_selected", None))


@dataclass
class RootClassNode:
    class_name: str
    verbs: list[ReconstructableVerb] = field(default_factory=list)


@dataclass
class RootNode:
    h_grade_root: str
    glottal_grade_root: str | None
    slug: str
    classes: list[RootClassNode] = field(default_factory=list)


def get_root_slug(h_grade: str, g_grade: str | None) -> str:
    key = f"{h_grade}|{g_grade or ''}"
    utf8_bytes = key.encode("utf-8")
    return base64.urlsafe_b64encode(utf8_bytes).decode("utf-8").replace("=", "")


def parse_ids(id_str: str) -> list[int]:
    if not id_str:
        return []
    return [int(x.strip()) for x in id_str.split(";") if x.strip().isdigit()]


def load_all_data() -> tuple[
    list[ReconstructableVerb],
    list[dict[str, str]],
    dict[str, str],
]:
    all_verbs = load_raw_reconstructable_verbs()
    derivational_connections = load_derivational_connections()
    root_ids = load_root_ids_overrides()

    return (
        all_verbs,
        derivational_connections,
        root_ids,
    )


def build_verb_index(
    all_verbs: list[ReconstructableVerb],
) -> dict[int, ReconstructableVerb]:
    verbs_by_id = {}
    for v in all_verbs:
        if v.corpus_id is not None:
            verbs_by_id[v.corpus_id] = v
    return verbs_by_id


def build_connection_graphs(
    derivational_connections: list[dict[str, str]],
    verbs_by_id: dict[int, ReconstructableVerb],
) -> tuple[dict[int, int], defaultdict[int, list[dict[str, Any]]]]:
    parent_map = {}
    children_map = defaultdict(list)

    def add_connection(from_ids_str: str, to_ids_str: str, conn_type: str) -> None:
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
    all_verbs: list[ReconstructableVerb], parent_map: dict[int, int]
) -> list[int]:
    top_level_ids = []
    for verb in all_verbs:
        cid = verb.corpus_id
        if cid is not None:
            if cid not in parent_map:
                top_level_ids.append(cid)
    return top_level_ids


def build_tree_node(
    verb_id: int,
    verbs_by_id: dict[int, ReconstructableVerb],
    children_map: defaultdict[int, list[dict[str, Any]]],
) -> ReconstructableVerb:
    verb = verbs_by_id[verb_id]

    children = children_map.get(verb_id, [])

    deriv_children = [c for c in children if c["type"] == "derivation"]

    for child in deriv_children:
        child_node = build_tree_node(child["id"], verbs_by_id, children_map)
        verb.derivations.append(child_node)

    return verb


def sync_root_ids(
    all_verbs: list[ReconstructableVerb],
    overrides: dict[str, str],
) -> tuple[dict[int, str], dict[str, str]]:

    # 1. Parse existing root_ids.csv to find user overrides
    # NOTE: overrides are now passed in via load_root_ids_map from utils

    # 2. Build rows for every verb
    csv_rows = []
    verb_to_root_id = {}
    synthetic_to_root_id = {}

    # Helper to clean strings
    def clean(s: str | None) -> str:
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
    csv_rows.sort(
        key=lambda x: (
            x["h_grade"] or "",
            x["g_grade"] or "",
            x["class"] or "",
            x["corpus_id"],
        )
    )

    # 4. Save CSV
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
    save_root_ids(csv_rows, fieldnames)

    return verb_to_root_id, synthetic_to_root_id


def group_roots_final(
    top_level_ids: list[int],
    all_verbs: list[ReconstructableVerb],
    verbs_by_id: dict[int, ReconstructableVerb],
    children_map: defaultdict[int, list[dict[str, Any]]],
    verb_to_root_id: dict[int, str],
    synthetic_to_root_id: dict[str, str],
) -> defaultdict[str, dict[str, Any]]:
    # dict[str, {"classes": dict[str,list]}]
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
    root_groups: dict[str, Any],
) -> list[RootNode]:

    # helper to format a single root node
    def format_node(
        key: tuple[str, str], override_root_id: str | None = None
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
    for root_id, data in root_groups.items():
        h, g = data["h"], data.get("g", "")
        final_output.append(format_node((h, g), override_root_id=root_id))

    # Sort final output
    final_output.sort(key=lambda x: x.h_grade_root)
    return final_output


def get_root_slug_from_id(root_id: str) -> str:
    utf8_bytes = root_id.encode("utf-8")
    return base64.urlsafe_b64encode(utf8_bytes).decode("utf-8").replace("=", "")


def group_hierarchical() -> None:
    """
    Group verbs into a hierarchy by root, class, pronominal config, and derivational suffix connections.

    Inputs:
    * RECONSTRUCTABLE_VERBS_PATH: canonical derivations for verbs.
    * ROOT_IDS_PATH: user-tuned canonical ids for roots for each corpus item.
    * DERIVATIONAL_CONNECTIONS_PATH: derivational connection data.

    Outputs:
    * HIERARCHICAL_DICT_PATH: a JSON dictionary nested by root -> class -> derivation.
    """

    # 1. Load Data
    (
        all_verbs,
        derivational_connections,
        existing_root_ids_overrides,
    ) = load_all_data()

    # 2. Sync Root IDs
    verb_to_root_id, synthetic_to_root_id = sync_root_ids(
        all_verbs, existing_root_ids_overrides
    )

    # 3. Build Verb Graphs
    verbs_by_id = build_verb_index(all_verbs)

    parent_map, children_map = build_connection_graphs(
        derivational_connections, verbs_by_id
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
    save_hierarchical_dict(final_output, EnhancedJSONEncoder)


if __name__ == "__main__":
    group_hierarchical()
