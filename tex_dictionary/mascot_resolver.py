import csv
import json
import os
from typing import Any

from dictionary_pipeline.dictionary_forms import DictionaryVerb
from dictionary_pipeline.paths import (
    ASPECT_CLASS_MASCOTS_PATH,
    RECONSTRUCTABLE_VERBS_PATH,
)
from tex_dictionary.generator import (
    get_cnd_entry,
    load_cnd,
    load_corpus_to_cnd,
    strip_tone,
)


class MascotResolver:
    all_verbs: list[DictionaryVerb]
    corpus_to_cnd: dict[int, dict[str, str]]
    cnd: dict[str, dict[str, str]]
    manual_mascots: dict[tuple[str, str], int]

    def __init__(self) -> None:
        self.all_verbs = self._load_all_verbs()
        self.corpus_to_cnd = load_corpus_to_cnd()
        self.cnd = load_cnd()
        self.manual_mascots = self._load_manual_mascots()

    def _load_all_verbs(self) -> list[DictionaryVerb]:
        if not os.path.exists(RECONSTRUCTABLE_VERBS_PATH):
            return []
        with open(RECONSTRUCTABLE_VERBS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        verbs: list[DictionaryVerb] = []

        def collect_verbs(v_list: list[dict[str, Any]]) -> None:
            for item in v_list:
                verb = DictionaryVerb.from_dict(item)
                verbs.append(verb)
                if "derivations" in item and isinstance(item["derivations"], list):
                    collect_verbs(item["derivations"])

        if isinstance(data, list):
            collect_verbs(data)
        return verbs

    def _load_manual_mascots(self) -> dict[tuple[str, str], int]:
        mapping: dict[tuple[str, str], int] = {}
        if not os.path.exists(ASPECT_CLASS_MASCOTS_PATH):
            return mapping
        with open(ASPECT_CLASS_MASCOTS_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cls = row.get("class", "")
                sub = row.get("subclass", "")
                full_cls = f"{cls}-{sub}" if sub else cls
                variant = row.get("variant", "Plain")
                cid = row.get("mascot_corpus_id")
                if cid:
                    mapping[(full_cls, variant)] = int(cid)
        return mapping

    def get_variant_label(self, verb: DictionaryVerb) -> str:
        parts: list[str] = []
        config = verb.morphology.config
        if config.pre.translocutive:
            parts.append("Translocutive")
        if config.pre.partitive:
            parts.append("Partitive")
        if config.pre.distributive:
            parts.append("Distributive")
        if config.pron.middle_voice.value != "none":
            label = config.pron.middle_voice.value.replace("_", "/").title()
            parts.append(label)

        if not parts:
            return "Plain"
        return " + ".join(parts)

    def get_verbs_for_class(self, class_name: str) -> list[DictionaryVerb]:
        """
        Returns all verbs whose class_name matches the given class_name (ignoring [tags]).
        """
        matching: list[DictionaryVerb] = []
        for v in self.all_verbs:
            # Match 'cause' to 'cause' and 'cause[perf2]'
            v_base_class = v.morphology.class_name.split("[")[0]
            if v_base_class == class_name:
                matching.append(v)
        return matching

    def resolve_mascot(self, class_name: str, variant: str) -> DictionaryVerb | None:
        # 1. Manual override
        manual_cid = self.manual_mascots.get((class_name, variant))
        if manual_cid:
            for verb in self.all_verbs:
                if verb.corpus_id == manual_cid:
                    return verb

        # 2. Filter verbs by class and variant
        matching_verbs = [
            v
            for v in self.get_verbs_for_class(class_name)
            if self.get_variant_label(v) == variant and v.corpus_id is not None
        ]

        if not matching_verbs:
            return None

        # 3. Alphabetical sort by toneless Present form
        def get_sort_key(verb: DictionaryVerb) -> str:
            if verb.corpus_id is None:
                return "zzz"
            cnd_entry = get_cnd_entry(
                verb.corpus_id, "present", self.corpus_to_cnd, self.cnd
            )
            toneless = str(cnd_entry.get("no_tone", "zzz"))
            return strip_tone(toneless).lower()

        matching_verbs.sort(key=get_sort_key)
        return matching_verbs[0]

    def get_mascot_data(self, verb: DictionaryVerb) -> dict[str, Any]:
        forms = [
            "present",
            "present_1sg",
            "imperfective",
            "perfective",
            "imperative",
            "infinitive",
        ]
        form_data: dict[str, dict[str, str]] = {}
        for fn in forms:
            if verb.corpus_id is not None:
                cnd_entry = get_cnd_entry(
                    verb.corpus_id, fn, self.corpus_to_cnd, self.cnd
                )
                form_data[fn] = {
                    "syllabary": str(cnd_entry.get("syllabary", "---")),
                    "tone": str(cnd_entry.get("tone", "---")),
                    "no_tone": str(cnd_entry.get("no_tone", "---")),
                }
            else:
                form_data[fn] = {
                    "syllabary": "---",
                    "tone": "---",
                    "no_tone": "---",
                }

        return {
            "corpus_id": verb.corpus_id,
            "definition": verb.definition,
            "forms": form_data,
            "verb": verb,  # Keep the verb object for later use if needed
        }


def resolve_all_mascots() -> dict[str, dict[str, dict[str, Any]]]:
    """
    Returns a mapping: class_name -> variant_label -> mascot_data
    """
    from tex_dictionary.companion_data import load_aspect_classes

    resolver = MascotResolver()
    classes = load_aspect_classes()

    results: dict[str, dict[str, dict[str, Any]]] = {}
    for cls in classes:
        full_name = cls.full_name
        verbs = resolver.get_verbs_for_class(full_name)
        variants = sorted(list(set(resolver.get_variant_label(v) for v in verbs)))

        if not variants:
            continue

        results[full_name] = {}
        for var in variants:
            mascot = resolver.resolve_mascot(full_name, var)
            if mascot:
                results[full_name][var] = resolver.get_mascot_data(mascot)

    return results


if __name__ == "__main__":
    import sys

    # Simple CLI for testing
    if len(sys.argv) > 1:
        target_class = sys.argv[1]
        resolver = MascotResolver()
        verbs = resolver.get_verbs_for_class(target_class)
        variants = sorted(list(set(resolver.get_variant_label(v) for v in verbs)))
        print(f"Variants for '{target_class}': {variants}")
        for var in variants:
            mascot = resolver.resolve_mascot(target_class, var)
            if mascot:
                data = resolver.get_mascot_data(mascot)
                print(
                    f"  Variant: {var} -> Mascot: {data['definition']} (ID: {data['corpus_id']})"
                )
            else:
                print(
                    f"  Variant: {var} -> No mascot found (no verbs with corpus data)"
                )
    else:
        print("Resolving all mascots...")
        all_mascots = resolve_all_mascots()
        print(f"Resolved mascots for {len(all_mascots)} classes.")
        if "cause" in all_mascots:
            print(f"Cause variants: {list(all_mascots['cause'].keys())}")
