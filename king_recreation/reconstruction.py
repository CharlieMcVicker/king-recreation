import dataclasses
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from king_recreation.h_alternation import possible_alternates, prevent_C_glottal_cluster
from king_recreation.morphemes.aspect.pattern_registry import PatternRegistry
from king_recreation.morphemes.post_root_morphemes import PostRootMorphemeRegistry
from king_recreation.morphemes.prefixes import PrefixConfig
from king_recreation.morphemes.prefixes.pronominals import (
    PronominalConfig,
    get_prefix_details,
    use_glottal_grade,
)
from king_recreation.word_spec import WordSpec, build_wordspec


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
class ReconstructableVerb:
    definition: str
    h_grade_root: str
    glottal_grade_root: Optional[str]
    post_root_morpheme: Optional[str]
    class_name: str
    config: PrefixConfig
    corpus_id: Optional[int] = None
    entry_no: Optional[int] = None
    derivations: List["ReconstructableVerb"] = field(default_factory=list)
    original_data: dict = field(
        default_factory=dict, repr=False, hash=False, compare=False
    )
    segmented_forms: dict = field(
        default_factory=dict,
    )

    # TODO: IS THIS DEAD?
    @staticmethod
    def from_dict(data: dict) -> "ReconstructableVerb":
        clean_data = data.copy()
        if "config" in clean_data:
            clean_data["config"] = PrefixConfig.from_dict(clean_data["config"])
        if "post_root_morpheme" in clean_data:
            val = clean_data["post_root_morpheme"]
            # turn "" to None
            clean_data["post_root_morpheme"] = val if val else None
        if "derivations" in clean_data:
            clean_data["derivations"] = [
                ReconstructableVerb.from_dict(d) for d in clean_data["derivations"]
            ]
        return ReconstructableVerb(**clean_data)


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, Enum):
            return o.value
        return super().default(o)


class ReconstructionEngine:
    def __init__(self, classes_path: Optional[str]):
        registry = PatternRegistry.get_instance()
        registry.load_from_csv(classes_path)
        # Create the name -> pattern map expected by reconstruct_verb
        self.classes = {p.name: p for p in registry.expanded_patterns}

    # _load_classes_raw removed as it is replaced by ClassPatterns.from_csv

    def generate_pronominal_forms(
        self, stem: str, set_name: str, config: PronominalConfig
    ) -> List[str]:
        prefix = get_prefix_details(set_name, config)

        stems_to_try = [(stem, False)]

        candidates = []
        for stem, dropped in stems_to_try:
            res = prefix.attach(stem, config.allow_h_metathesis)
            if res:
                candidates.append(res)
        return candidates

    def root_for_form(
        self, verb: ReconstructableVerb, glottal_grade: bool
    ) -> Optional[str]:
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

    def get_base_stems_for_form(self, verb: ReconstructableVerb, spec: WordSpec):
        class_info = self.classes.get(verb.class_name)
        if not class_info:
            return []

        glottal_grade = use_glottal_grade(spec.set_name)
        root = self.root_for_form(verb, glottal_grade)

        if root is None:
            return None

        # apply aspect suffix

        ending_pattern = class_info.get(spec.aspect, "")

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

    def reconstruct_spec(self, verb: ReconstructableVerb, spec: WordSpec) -> List[str]:
        # 1. Get the base stems (stem + aspect suffix)
        stems = self.get_base_stems_for_form(verb, spec)
        if not stems:
            return []

        # 2. Attach pronominal prefixes
        final_forms = []
        for stem in stems:
            # Note: spec.set_name is already resolved by build_wordspec or provided manually
            candidates = self.generate_pronominal_forms(
                stem, spec.set_name, verb.config.pron
            )

            # 3. Attach pre-pronominal prefixes
            for c in candidates:
                # verb.config.apply_prepronominals handles translocutive/partitive/distributive
                final_forms.extend(verb.config.apply_prepronominals(c, spec.aspect))

        return list(set(final_forms))

    def reconstruct_verb(self, verb: ReconstructableVerb) -> List[Dict[str, str]]:
        form_options = {}

        for fn in [
            "present",
            "present_1sg",
            "imperfective",
            "perfective",
            "imperative",
            "infinitive",
        ]:
            spec = build_wordspec(fn, verb.config.pron, verb.config.stative)
            options = self.reconstruct_spec(verb, spec)
            if options:
                form_options[fn] = options

        return [{fn: set(opts or []) for fn, opts in form_options.items()}]
