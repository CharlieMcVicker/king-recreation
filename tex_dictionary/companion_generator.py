import csv
import re
from typing import Any

from pylatex import (  # type: ignore[import-untyped]
    Command,
    Document,
    NoEscape,
    Package,
    Tabularx,
)
from pylatex.utils import bold, italic  # type: ignore[import-untyped]
from pylatexenc.latexencode import unicode_to_latex  # type: ignore[import-untyped]

from dictionary_pipeline.dictionary_forms import DictionaryVerb, build_wordspec
from dictionary_pipeline.paths import (
    CLASSES_DATA_PATH,
    COMPANION_TEX_PATH,
    MAIN_TOC_PATH,
)
from morphology.h_alternation import prevent_C_glottal_cluster
from morphology.morphemes.aspect.class_patterns import ClassMacro, ExpandedClassPattern
from morphology.morphemes.middle_voice import MiddleVoice
from morphology.morphology_types import PronominalSet
from morphology.reconstruction import drop_dropped_phones
from tex_dictionary.companion_data import (
    AspectClass,
    load_aspect_classes,
    sort_classes_by_frequency,
)
from tex_dictionary.generator import verb_config_to_tex
from tex_dictionary.mascot_resolver import MascotResolver
from tex_dictionary.toc_parser import parse_main_toc


def clean_latex_text(text: str) -> str:
    """
    Replaces non-ASCII punctuation that pylatexenc might over-encode
    with standard ASCII equivalents.
    """
    if not text:
        return ""
    return (
        text.replace("\u201a", ",")  # Low single quote -> comma
        .replace("\u2019", "'")  # Smart right quote -> apostrophe
        .replace("\u2018", "'")  # Smart left quote -> apostrophe
        .replace("\u201c", '"')  # Smart left double quote -> quote
        .replace("\u201d", '"')  # Smart right double quote -> quote
    )


def get_base_endings(
    aspect_classes: list[AspectClass], class_name: str
) -> dict[str, str] | None:
    """
    Finds the base endings for a class (where subclass is empty).
    """
    # 1. Try exact match first (handles hyphenated base classes like ih-vh)
    for cls in aspect_classes:
        if cls.full_name == class_name and not cls.subclass:
            return {
                "present": cls.present.split(";")[0],
                "imperfective": cls.imperfective.split(";")[0],
                "perfective": cls.perfective.split(";")[0],
                "imperative": cls.imperative.split(";")[0],
                "infinitive": cls.infinitive.split(";")[0],
            }

    # 2. Fallback: split by hyphen (handles derived classes like a-b -> a)
    base_name = class_name.split("-")[0]
    for cls in aspect_classes:
        if cls.name == base_name and not cls.subclass:
            return {
                "present": cls.present.split(";")[0],
                "imperfective": cls.imperfective.split(";")[0],
                "perfective": cls.perfective.split(";")[0],
                "imperative": cls.imperative.split(";")[0],
                "infinitive": cls.infinitive.split(";")[0],
            }
    return None


def load_expanded_patterns() -> dict[str, ExpandedClassPattern]:
    patterns: dict[str, ExpandedClassPattern] = {}
    with open(CLASSES_DATA_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            macro = ClassMacro.from_row(row)
            for exp in macro.expand():
                patterns[exp.name] = exp
    return patterns


def format_segmented_verb(
    verb: DictionaryVerb, form_name: str, segmented_form: str
) -> NoEscape:
    """
    Applies phonological reductions (drops - and handles operators)
    while preserving pronoun coloring and aspect bolding.
    """
    if not segmented_form or segmented_form == "---":
        return NoEscape("---")

    # 1. Map pronoun/aspect indices
    parts = re.split(r"(-|->)", segmented_form)
    segments = parts[0::2]

    config = verb.morphology.config
    num_pre = sum(
        [config.pre.translocutive, config.pre.partitive, config.pre.distributive]
    )
    if (
        form_name == "imperative"
        and config.pre.translocutiveImpOnly
        and not config.pre.translocutive
    ):
        num_pre += 1
    pronoun_idx = num_pre
    aspect_idx = len(segments) - 1

    # 2. Build list of (char, formatting_role)
    chars_with_role: list[dict[str, Any]] = []
    for i, seg in enumerate(segments):
        role = 0
        if i == pronoun_idx:
            role = 1
        elif i == aspect_idx:
            role = 2
        for c in seg:
            chars_with_role.append({"char": c, "role": role})

    # 3. Apply drop_dropped_phones logic safely
    i = 0
    while i < len(chars_with_role):
        if chars_with_role[i]["char"] == ">":
            chars_with_role.pop(i)
            if i < len(chars_with_role):
                chars_with_role.pop(i)
            continue
        i += 1
    i = 0
    while i < len(chars_with_role):
        if chars_with_role[i]["char"] == "@":
            chars_with_role.pop(i)
            if i > 0:
                chars_with_role.pop(i - 1)
                i -= 1
            if i > 0:
                chars_with_role.pop(i - 1)
                i -= 1
            continue
        i += 1
    i = 0
    while i < len(chars_with_role):
        if chars_with_role[i]["char"] == "*":
            chars_with_role.pop(i)
            if i > 0:
                chars_with_role.pop(i - 1)
                i -= 1
            continue
        i += 1
    i = 0
    while i < len(chars_with_role):
        if chars_with_role[i]["char"] == ":":
            chars_with_role.pop(i)
            continue
        i += 1

    # 4. Apply prevent_C_glottal_cluster logic
    temp_str = "".join([str(c["char"]) for c in chars_with_role])
    fixed_str = prevent_C_glottal_cluster(temp_str)

    if fixed_str != temp_str:
        new_chars: list[dict[str, Any]] = []
        for c in fixed_str:
            new_chars.append({"char": c, "role": 0})
        if len(new_chars) == len(chars_with_role):
            for i in range(len(new_chars)):
                new_chars[i]["role"] = chars_with_role[i]["role"]
        chars_with_role = new_chars

    from dictionary_pipeline.dictionary_forms import Prediction

    prediction = Prediction(str(verb.original_data.get("prediction") or "FullEventful"))
    spec = build_wordspec(prediction, config.pron, form_name)
    color = "black"
    if spec.pronominal_set == PronominalSet.SET_A:
        color = "Red"
    elif spec.pronominal_set == PronominalSet.SET_B:
        color = "RoyalBlue"
    elif spec.pronominal_set == PronominalSet.PERSON_TO_PERSON:
        color = "Purple"

    formatted_parts: list[str] = []
    current_role = -1
    for item in chars_with_role:
        c = str(unicode_to_latex(str(item["char"])))
        role = int(item["role"])

        if role != current_role:
            if current_role == 1 or current_role == 2:
                formatted_parts.append("}")
            if role == 1:
                formatted_parts.append(r"\textcolor{" + color + "}{")
            elif role == 2:
                formatted_parts.append(r"\textbf{")
            current_role = role

        formatted_parts.append(c)

    if current_role == 1 or current_role == 2:
        formatted_parts.append("}")

    return NoEscape("".join(formatted_parts))


def generate_companion_tex() -> bool:
    print("Initializing Companion Document...")
    doc = Document(
        default_filepath=COMPANION_TEX_PATH.replace(".tex", ""),
        documentclass="book",
        document_options=["oneside", "openany"],
    )

    doc.packages.append(Package("fontspec"))
    doc.packages.append(Package("xcolor", options=["dvipsnames"]))
    doc.packages.append(Package("booktabs"))
    doc.packages.append(Package("tabularx"))
    doc.packages.append(Package("needspace"))
    doc.packages.append(Package("ragged2e"))
    doc.packages.append(
        Package(
            "geometry",
            options=[
                "paperwidth=8.5in",
                "paperheight=11in",
                "margin=0.5in",
                "headheight=14pt",
            ],
        )
    )
    doc.packages.append(Package("fancyhdr"))
    doc.packages.append(Package("titlesec"))

    doc.preamble.append(
        NoEscape(r"\titleformat{\subsection}{\normalfont\large\bfseries}{}{0pt}{}")
    )
    doc.preamble.append(
        NoEscape(
            r"\titleformat{\subsubsection}[hang]{\normalfont\normalsize\bfseries}{}{0pt}{}"
        )
    )
    doc.preamble.append(NoEscape(r"\setcounter{tocdepth}{4}"))
    doc.preamble.append(
        NoEscape(
            r"\setmainfont{NotoSansCherokee-Regular}[Path=../../Noto_Sans_Cherokee/static/, Extension=.ttf, BoldFont=NotoSansCherokee-Bold, AutoFakeSlant=0.2]"
        )
    )

    doc.preamble.append(
        Command(
            "title",
            NoEscape(
                r"Cherokee Root-based Dictionary: Aspect class companion\\[1ex]\large DRAFT DO NOT CIRCULATE"
            ),
        )
    )
    doc.preamble.append(Command("author", "Charlie ᏣᎵ McVicker"))

    doc.append(NoEscape(r"\maketitle"))
    doc.append(NoEscape(r"\tableofcontents"))
    doc.append(NoEscape(r"\newpage"))

    print("Loading Aspect Classes and Mascots...")
    aspect_classes = load_aspect_classes()
    sorted_classes = sort_classes_by_frequency(aspect_classes)

    resolver = MascotResolver()

    print(f"Parsing {MAIN_TOC_PATH} for cross-references...")
    known_class_names = [c.full_name for c in aspect_classes]
    toc_data = parse_main_toc(MAIN_TOC_PATH, known_class_names)

    from collections import defaultdict

    groups: dict[str, list[AspectClass]] = defaultdict(list)
    for c in sorted_classes:
        groups[c.name].append(c)

    sorted_group_names = sorted(
        groups.keys(), key=lambda n: sum(c.frequency for c in groups[n]), reverse=True
    )

    for group_name in sorted_group_names:
        group_members = groups[group_name]
        total_freq = sum(c.frequency for c in group_members)
        if total_freq == 0:
            continue

        anchor = next((c for c in group_members if not c.subclass), None)
        if not anchor:
            anchor = sorted(group_members, key=lambda c: c.frequency, reverse=True)[0]

        base_cls = anchor

        doc.append(NoEscape(r"\needspace{3in}"))
        doc.append(
            NoEscape(
                r"\section*{" + str(unicode_to_latex(f"Class: {group_name}")) + "}"
            )
        )
        doc.append(
            NoEscape(
                r"\addcontentsline{toc}{section}{"
                + str(unicode_to_latex(f"Class: {group_name}"))
                + "}"
            )
        )

        relevant_full_names = [c.full_name for c in group_members]

        all_verbs_for_class: list[DictionaryVerb] = []
        for fn in relevant_full_names:
            all_verbs_for_class.extend(resolver.get_verbs_for_class(fn))

        if not all_verbs_for_class:
            continue

        doc.append(NoEscape(r"\needspace{3in}"))

        col_spec = (
            r">{\hsize=1.5\hsize\RaggedRight}X "
            r">{\hsize=0.9\hsize}X "
            r">{\hsize=0.9\hsize}X "
            r">{\hsize=0.9\hsize}X "
            r">{\hsize=0.9\hsize}X "
            r">{\hsize=0.9\hsize}X"
        )
        summary_table = Tabularx(
            NoEscape(col_spec), width_argument=NoEscape(r"\textwidth")
        )
        _ = summary_table.append(NoEscape(r"\toprule"))
        _ = summary_table.add_row(
            (
                bold("Variant / Mascot"),
                bold("Present"),
                bold("Imperf."),
                bold("Perf."),
                bold("Imper."),
                bold("Infin."),
            )
        )
        _ = summary_table.append(NoEscape(r"\midrule"))

        class_groups: dict[str, list[DictionaryVerb]] = {}
        for fn in relevant_full_names:
            for v in resolver.get_verbs_for_class(fn):
                class_groups.setdefault(v.morphology.class_name, []).append(v)

        sorted_class_names = sorted(class_groups.keys())

        expanded_patterns = load_expanded_patterns()
        class_mascots: dict[str, tuple[DictionaryVerb, dict[str, Any]]] = {}
        for class_name in sorted_class_names:
            group_verbs = class_groups[class_name]

            def get_mascot_score(verb: DictionaryVerb) -> tuple[int, str]:
                label = resolver.get_variant_label(verb)
                return (0 if label == "Plain" else 1, verb.definition.lower())

            group_verbs_with_cid = [v for v in group_verbs if v.corpus_id]
            if not group_verbs_with_cid:
                mascot_verb = sorted(group_verbs, key=lambda v: v.definition.lower())[0]
            else:
                mascot_verb = sorted(group_verbs_with_cid, key=get_mascot_score)[0]
            class_mascots[class_name] = (
                mascot_verb,
                resolver.get_mascot_data(mascot_verb),
            )

        forms = ["present", "imperfective", "perfective", "imperative", "infinitive"]

        for i, class_name in enumerate(sorted_class_names):
            pattern = expanded_patterns.get(class_name)
            if not pattern:
                current_cls_full_name = class_name.split("[")[0]
                current_cls = next(
                    (c for c in aspect_classes if c.full_name == current_cls_full_name),
                    base_cls,
                )
            else:
                current_cls_full_name = pattern.name.split("[")[0]

            section_base_pattern = expanded_patterns.get(base_cls.full_name)
            is_derived = class_name != base_cls.full_name

            rule_row: list[Any] = [italic(class_name)]
            for f in forms:
                if pattern:
                    ending = pattern.get(f)
                else:
                    tags: dict[str, int] = {}
                    tag_match = re.search(r"\[(.*)\]", class_name)
                    if tag_match:
                        for t in tag_match.group(1).split("-"):
                            m = re.match(r"([a-z]+)(\d+)", t)
                            if m:
                                tags[m.group(1)] = int(m.group(2)) - 1

                    def get_ending_legacy(form: str, idx: int = 0) -> str:
                        val = getattr(current_cls, form)
                        opts: list[str] = val.split(";")
                        return opts[idx] if idx < len(opts) else opts[0]

                    shorthands = {
                        "present": "pres",
                        "imperfective": "imperf",
                        "perfective": "perf",
                        "imperative": "imp",
                        "infinitive": "inf",
                    }
                    idx = tags.get(shorthands.get(f, ""), 0)
                    ending = get_ending_legacy(f, idx)

                base_ending = (
                    section_base_pattern.get(f) if section_base_pattern else None
                )

                if is_derived and base_ending is not None and ending == base_ending:
                    rule_row.append(NoEscape(""))
                else:
                    rule_row.append(
                        NoEscape(bold(str(unicode_to_latex(clean_latex_text(ending)))))
                    )
            _ = summary_table.add_row(rule_row)
            _ = summary_table.append(NoEscape(r"\midrule"))

            mascot_verb, mascot_data = class_mascots[class_name]
            mascot_page = "???"
            if current_cls_full_name in toc_data:
                for entry in toc_data[current_cls_full_name]:
                    if entry["definition"].strip() == mascot_data["definition"].strip():
                        mascot_page = entry["page"]
                        break

            mascot_label = mascot_data["definition"] + f" (p. {mascot_page})"
            mascot_row: list[Any] = [
                NoEscape(str(unicode_to_latex(clean_latex_text(mascot_label))))
            ]
            for fn in forms:
                segmented = mascot_verb.segmented_forms.get(fn, "---")
                mascot_row.append(format_segmented_verb(mascot_verb, fn, segmented))
            _ = summary_table.add_row(mascot_row)

            if i < len(sorted_class_names) - 1:
                _ = summary_table.append(NoEscape(r"\specialrule{1.5pt}{2pt}{2pt}"))

        _ = summary_table.append(NoEscape(r"\bottomrule"))
        doc.append(summary_table)
        doc.append(NoEscape(r"\vspace{1em}"))

        for class_name in sorted_class_names:
            group_verbs: list[DictionaryVerb] = class_groups[class_name]
            doc.append(NoEscape(r"\needspace{1in}"))
            doc.append(
                NoEscape(r"\subsection*{" + str(unicode_to_latex(class_name)) + "}")
            )
            sorted_group_verbs = sorted(
                group_verbs,
                key=lambda v: (
                    v.morphology.h_grade_root,
                    v.morphology.glottal_grade_root,
                    not v.morphology.config.pron.middle_voice == MiddleVoice.NONE,
                ),
            )
            for v in sorted_group_verbs:
                p = "???"
                v_base_class = v.morphology.class_name.split("[")[0]
                if v_base_class in toc_data:
                    for entry in toc_data[v_base_class]:
                        if entry["definition"].strip() == v.definition.strip():
                            p = entry["page"]

                            clean_toc = re.sub(
                                r"\\textcolor\s*\{[^}]*\}\s*\{", "", entry["verb_tex"]
                            )
                            clean_toc = re.sub(r"\\textbf\s*\{", "", clean_toc)
                            clean_toc = (
                                clean_toc.replace("}", "")
                                .replace("-", "")
                                .replace(" ", "")
                                .strip()
                            )

                            found_form = "present"
                            for fn in [
                                "present",
                                "imperfective",
                                "perfective",
                                "imperative",
                                "infinitive",
                            ]:
                                seg = v.segmented_forms.get(fn, "")
                                if not seg:
                                    continue
                                clean_seg = (
                                    seg.replace("-", "").replace("->", "").strip()
                                )
                                clean_seg = drop_dropped_phones(clean_seg)
                                clean_seg = clean_seg.replace(" ", "")
                                if clean_seg == clean_toc:
                                    found_form = fn
                                    break

                            cleaned_def = clean_latex_text(entry["definition"])
                            root_str = f"{v.morphology.h_grade_root}"
                            if (
                                v.morphology.glottal_grade_root
                                and not v.morphology.glottal_grade_root
                                == v.morphology.h_grade_root
                            ):
                                root_str += f" / {v.morphology.glottal_grade_root}"
                            tex_to_use = verb_config_to_tex(
                                v, root_str=root_str, parent_classes=[]
                            )
                            line = f"{tex_to_use} \\textit{{{unicode_to_latex(cleaned_def)}}} \\dotfill {p}\\\\"
                            doc.append(NoEscape(line))
                            break
            doc.append(NoEscape(r"\vspace{1em}"))

    print(f"Saving companion TeX to {COMPANION_TEX_PATH}...")
    doc.generate_tex()
    return True


if __name__ == "__main__":
    generate_companion_tex()
