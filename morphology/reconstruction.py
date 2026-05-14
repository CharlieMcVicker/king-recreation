import dataclasses
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, cast

from morphology.h_alternation import possible_alternates, prevent_C_glottal_cluster
from morphology.morphemes.aspect.pattern_registry import PatternRegistry
from morphology.morphemes.post_root_morphemes import PostRootMorphemeRegistry
from morphology.morphemes.prefixes import PrefixConfig
from morphology.morphemes.prefixes.pronominals import (
    PronominalConfig,
    get_prefix_details,
    use_glottal_grade,
)
from morphology.morphology_types import Aspect, Number, Person, PronominalSet
from morphology.word_spec import WordSpec


def drop_dropped_phones(s: str) -> str:
    s = re.sub(">.", "", s)
    s = re.sub("..@", "", s)
    s = re.sub(".\\*", "", s)
    s = re.sub(":", "", s)
    return s


def desegment(s: str) -> str:
    """"""
    s = s.replace("-", "")
    s = drop_dropped_phones(s)
    s = prevent_C_glottal_cluster(s)
    return s


@dataclass
class MorphologicalVerb:
    h_grade_root: str
    glottal_grade_root: str | None
    post_root_morpheme: str | None
    class_name: str
    config: PrefixConfig

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "MorphologicalVerb":
        clean_data = data.copy()
        if "config" in clean_data:
            clean_data["config"] = PrefixConfig.from_dict(clean_data["config"])
        if "post_root_morpheme" in clean_data:
            val = clean_data["post_root_morpheme"]
            clean_data["post_root_morpheme"] = val if val else None
        return MorphologicalVerb(**clean_data)


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(cast(Any, o))
        if isinstance(o, Enum):
            return o.value
        return super().default(o)


class ReconstructionEngine:
    def __init__(self, classes_path: str | None) -> None:
        registry = PatternRegistry.get_instance()
        registry.load_from_csv(classes_path)
        # Create the name -> pattern map for class lookups
        self.classes = {p.name: p for p in registry.expanded_patterns}

    # _load_classes_raw removed as it is replaced by ClassPatterns.from_csv

    def generate_pronominal_forms(
        self,
        stem: str,
        key: tuple[Person, Number, PronominalSet],
        config: PronominalConfig,
    ) -> list[str]:
        prefix = get_prefix_details(key, config)

        stems_to_try = [(stem, False)]

        candidates = []
        for stem, dropped in stems_to_try:
            res = prefix.attach(stem, config.allow_h_metathesis)
            if res:
                candidates.append(res)
        return candidates

    def root_for_form(self, verb: MorphologicalVerb, glottal_grade: bool) -> str | None:
        # Determine Grade
        # Default: h-grade
        root = verb.glottal_grade_root if glottal_grade else verb.h_grade_root

        if glottal_grade and root is None:
            # Missing required root for this form
            return None

        if root is None:
            return None

        # apply middle voice
        root = verb.config.pron.middle_voice.apply(
            root, glottal_grade, verb.config.pron.middle_voice_h_metathesis
        )

        if verb.post_root_morpheme:
            reg = PostRootMorphemeRegistry.get_instance()
            root = root + "-" + reg.morphemes_by_name[verb.post_root_morpheme].form

        return root

    def get_base_stems_for_form(
        self, verb: MorphologicalVerb, aspect: Aspect, glottal_grade: bool
    ) -> list[str] | None:
        class_info = self.classes.get(verb.class_name)
        if not class_info:
            return []

        root = self.root_for_form(verb, glottal_grade)

        if root is None:
            return None

        # apply aspect suffix — ExpandedClassPattern fields are named by aspect value
        ending_pattern = class_info.get(aspect.value, "")

        # just phonological content of ending
        literal_ending = ending_pattern.replace("*", "").replace("@", "")

        # truncate if pattern calls for it
        if "*" in ending_pattern:
            if len(root) >= 1:
                root = root + "*"
        elif "@" in ending_pattern:
            if len(root) >= 2:
                root = root + "@"

        # if we need to /h/ alternate but there wasnt an h in the h grade root
        # we need to try to drop it from the ending
        if glottal_grade and not "h" in verb.h_grade_root:
            return [
                root + "-" + literal_ending
                for literal_ending in possible_alternates(
                    literal_ending, fix_clusters=False
                )
            ]
        else:
            return [root + "-" + literal_ending]

    def reconstruct_spec(self, verb: MorphologicalVerb, spec: WordSpec) -> list[str]:
        # 1. Get the base stems (stem + aspect suffix)
        stems = self.get_base_stems_for_form(
            verb,
            aspect=spec.aspect,
            glottal_grade=use_glottal_grade(
                spec.person, spec.number, spec.pronominal_set
            ),
        )
        if not stems:
            return []

        # 2. Attach pronominal prefixes
        final_forms = []
        for stem in stems:
            # key = (person, number, p_set)
            key = (spec.person, spec.number, spec.pronominal_set)
            candidates = self.generate_pronominal_forms(stem, key, verb.config.pron)

            # 3. Attach pre-pronominal prefixes
            for c in candidates:
                # verb.config.apply_prepronominals handles translocutive/partitive/distributive
                final_forms.extend(verb.config.apply_prepronominals(c, spec.aspect))

        return list(set(final_forms))
