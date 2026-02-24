import csv
from dataclasses import dataclass
from typing import Dict, List, Set

from king_recreation.paths import POST_ROOT_MORPHEMES_PATH


@dataclass
class PostRootMorpheme:
    name: str
    form: str
    classes: List[str]

    @staticmethod
    def from_row(row):
        return PostRootMorpheme(
            name=f'{row["name"]}[{row["subcase"]}]' if row["subcase"] else row["name"],
            form=row["form"],
            classes=row["classes"].split(";"),
        )


def load_post_root_morphemes():
    # Load Morphemes
    morphemes = []
    with open(POST_ROOT_MORPHEMES_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            morphemes.append(PostRootMorpheme.from_row(row))

    return morphemes


class PostRootMorphemeRegistry:
    _instance = None

    def __init__(self):
        self.morphemes: List[PostRootMorpheme] = load_post_root_morphemes()
        self.morphemes_by_name = {m.name: m for m in self.morphemes}
        self.class_map = self.create_class_map()

    @classmethod
    def get_instance(cls) -> "PostRootMorphemeRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def create_class_map(self):
        class_map: Dict[str, Set[str]] = {}
        for prm in self.morphemes:
            for verb_class in prm.classes:
                if verb_class not in class_map:
                    class_map[verb_class] = set()
                class_map[verb_class].add(prm.name)
        return class_map


def match_post_root_morphemes(row: dict[str, str]) -> List[dict[str, str]]:
    reg = PostRootMorphemeRegistry.get_instance()
    rows = [row]
    forms = [
        "h_grade",
        "g_grade",
    ]

    verb_class = row["class"]
    verb_macro = verb_class.split("[")[0]
    macro_wildcard = f"{verb_macro}[*]"

    morphemes_to_check = set()
    if verb_class in reg.class_map:
        morphemes_to_check.update(reg.class_map[verb_class])
    if macro_wildcard in reg.class_map:
        morphemes_to_check.update(reg.class_map[macro_wildcard])

    if morphemes_to_check:
        for m_name in morphemes_to_check:
            morpheme = reg.morphemes_by_name[m_name]

            match_row = row.copy()
            match_row["post_root_morpheme"] = morpheme.name

            for form in forms:
                form_val = match_row[form]
                if form_val is not None:
                    if form_val.endswith(morpheme.form):
                        match_row[form] = form_val[: -len(morpheme.form)]
                    else:
                        break
                else:
                    match_row[form] = None
            else:
                rows.append(match_row)
    return rows
