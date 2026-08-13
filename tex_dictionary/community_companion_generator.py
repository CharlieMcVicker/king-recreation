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
from dictionary_pipeline.orthography import unrespell_consonants
from dictionary_pipeline.paths import (
    CLASSES_DATA_PATH,
    COMMUNITY_COMPANION_TEX_PATH,
    MAIN_TOC_PATH,
)
from morphology.h_alternation import prevent_C_glottal_cluster
from morphology.morphemes.aspect.class_patterns import ClassMacro, ExpandedClassPattern
from morphology.morphemes.middle_voice import MiddleVoice
from morphology.morphology_types import PronominalSet
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
        text.replace("\u201a", ",")
        .replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )


def load_expanded_patterns() -> dict[str, ExpandedClassPattern]:
    patterns: dict[str, ExpandedClassPattern] = {}
    with open(CLASSES_DATA_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            macro = ClassMacro.from_row(row)
            for exp in macro.expand():
                patterns[exp.name] = exp
    return patterns


def format_segmented_verb_community(
    verb: DictionaryVerb, form_name: str, segmented_form: str
) -> NoEscape:
    """
    Applies phonological reductions (drops - and handles operators)
    while preserving pronoun coloring and aspect bolding, converting to community orthography.
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
    if form_name == "imperative":
        aspect_idx = len(segments) - 1
    else:
        aspect_idx = len(segments) - 2

    if verb.morphology.class_name == "stative":
        aspect_idx = None

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

    # Build grouped segments by role to pass through community orthography conversion
    role_groups: list[dict[str, Any]] = []
    if chars_with_role:
        cur_role = chars_with_role[0]["role"]
        cur_chars: list[str] = [chars_with_role[0]["char"]]
        for item in chars_with_role[1:]:
            if item["role"] == cur_role:
                cur_chars.append(item["char"])
            else:
                role_groups.append({"role": cur_role, "text": "".join(cur_chars)})
                cur_role = item["role"]
                cur_chars = [item["char"]]
        role_groups.append({"role": cur_role, "text": "".join(cur_chars)})

    formatted_parts: list[str] = []
    for grp in role_groups:
        role = grp["role"]
        comm_text = unrespell_consonants(grp["text"])
        c = str(unicode_to_latex(str(comm_text)))

        if role == 1:
            formatted_parts.append(r"\textcolor{" + color + "}{" + c + "}")
        elif role == 2:
            formatted_parts.append(r"\textbf{" + c + "}")
        else:
            formatted_parts.append(c)

    return NoEscape("".join(formatted_parts))


def render_verb_minipage_community(
    verb: DictionaryVerb,
    resolver: MascotResolver,
    toc_data: dict[str, list[dict[str, str]]],
) -> str:
    """
    Renders a verb as a 3-line minipage for 3-column multicol display:
    Line 1: Community Orthography Form (Bold aspect / colored pronoun)
    Line 2: Template String (Main dictionary format with Set A (ga), converted to community orthography)
    Line 3: Italic Gloss (with page reference)
    """
    p = "???"
    v_base_class = verb.morphology.class_name.split("[")[0]
    if v_base_class in toc_data:
        for entry in toc_data[v_base_class]:
            if entry["definition"].strip() == verb.definition.strip():
                p = entry["page"]
                break

    # Line 1: Present form in community orthography
    seg_pres = verb.segmented_forms.get("present", "---")
    l1_tex = format_segmented_verb_community(verb, "present", seg_pres)

    # Line 2: Template string from main dictionary generator with Set A (ga) & community orthography
    root_str = f"{verb.morphology.h_grade_root}"
    if (
        verb.morphology.glottal_grade_root
        and not verb.morphology.glottal_grade_root == verb.morphology.h_grade_root
    ):
        root_str += f" / {verb.morphology.glottal_grade_root}"

    comm_root_str = unrespell_consonants(root_str)
    template_tex = verb_config_to_tex(
        verb, root_str=comm_root_str, parent_classes=[], ka_label="Set A (ga)"
    )
    # Convert any raw 'kh' or 'hs' in the template LaTeX string without corrupting LaTeX macros
    comm_template_tex = re.sub(
        r"(?<!\\)(kh|Kh|hs)",
        lambda m: "sh" if m.group(1) == "hs" else "k",
        template_tex,
    )
    l2_tex = r"{\small \textsf{" + comm_template_tex + r"}}"

    # Line 3: Italic gloss with page ref
    cleaned_def = clean_latex_text(verb.definition)
    l3_tex = f"\\textit{{{unicode_to_latex(cleaned_def)}}} (p.~{p})"

    minipage_tex = (
        r"\begin{minipage}[t]{\linewidth}"
        "\n"
        r"\raggedright\noindent "
        f"{l1_tex}\\\\\n"
        r"\noindent "
        f"{l2_tex}\\\\\n"
        r"\noindent "
        f"{l3_tex}\n"
        r"\end{minipage}"
    )
    return minipage_tex


def generate_community_companion_tex() -> bool:
    print("Initializing Community Companion Document...")
    doc = Document(
        default_filepath=COMMUNITY_COMPANION_TEX_PATH.replace(".tex", ""),
        documentclass="book",
        document_options=["oneside", "openany"],
        lmodern=False,
    )

    doc.packages.append(Package("fontspec"))
    doc.packages.append(Package("xcolor", options=["dvipsnames"]))
    doc.packages.append(Package("booktabs"))
    doc.packages.append(Package("tabularx"))
    doc.packages.append(Package("needspace"))
    doc.packages.append(Package("ragged2e"))
    doc.packages.append(Package("multicol"))
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
                r"Cherokee Root-based Dictionary: Community Companion\\[1ex]\large DRAFT DO NOT CIRCULATE"
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

    expanded_patterns = load_expanded_patterns()
    mascot_forms = [
        "present",
        "present_1sg",
        "imperfective",
        "perfective",
        "imperative",
        "infinitive",
    ]
    rule_forms = ["present", "imperfective", "perfective", "imperative", "infinitive"]

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

        class_groups: dict[str, list[DictionaryVerb]] = {}
        for fn in relevant_full_names:
            for v in resolver.get_verbs_for_class(fn):
                class_groups.setdefault(v.morphology.class_name, []).append(v)

        sorted_class_names = sorted(class_groups.keys())

        # Resolve mascots for variants using MascotResolver
        class_mascots: dict[str, tuple[DictionaryVerb, dict[str, Any]]] = {}
        for class_name in sorted_class_names:
            group_verbs = class_groups[class_name]
            variants = sorted(
                list(set(resolver.get_variant_label(v) for v in group_verbs))
            )
            # Default variant is Plain if available, else first
            variant = "Plain" if "Plain" in variants else variants[0]
            mascot_verb = resolver.resolve_mascot(class_name, variant)

            if not mascot_verb:
                group_verbs_with_cid = [v for v in group_verbs if v.corpus_id]
                if not group_verbs_with_cid:
                    mascot_verb = sorted(
                        group_verbs, key=lambda v: v.definition.lower()
                    )[0]
                else:
                    mascot_verb = sorted(
                        group_verbs_with_cid, key=lambda v: v.definition.lower()
                    )[0]

            class_mascots[class_name] = (
                mascot_verb,
                resolver.get_mascot_data(mascot_verb),
            )

        # Render member verb listings in 3 columns per subclass, with subclass mascot table first
        for class_name in sorted_class_names:
            group_verbs: list[DictionaryVerb] = class_groups[class_name]
            doc.append(NoEscape(r"\needspace{1.5in}"))
            doc.append(
                NoEscape(r"\subsection*{" + str(unicode_to_latex(class_name)) + "}")
            )

            # Mascot table for this subclass
            mascot_verb, mascot_data = class_mascots[class_name]
            mascot_page = "???"
            cls_base = class_name.split("[")[0]
            if cls_base in toc_data:
                for entry in toc_data[cls_base]:
                    if entry["definition"].strip() == mascot_data["definition"].strip():
                        mascot_page = entry["page"]
                        break

            col_spec_mascot = (
                r">{\hsize=1.5\hsize\RaggedRight}X "
                r">{\hsize=0.9\hsize}X "
                r">{\hsize=0.9\hsize}X "
                r">{\hsize=0.9\hsize}X "
                r">{\hsize=0.9\hsize}X "
                r">{\hsize=0.9\hsize}X "
                r">{\hsize=0.9\hsize}X"
            )
            mascot_table = Tabularx(
                NoEscape(col_spec_mascot), width_argument=NoEscape(r"\textwidth")
            )
            _ = mascot_table.append(NoEscape(r"\toprule"))
            _ = mascot_table.add_row(
                (
                    bold("ᎠᏅᏔᏗᏍᏙᏗ ᎧᏁᎢᏍᏗ"),
                    bold("ᎾᏛᏁᎭ"),
                    bold("ᏂᎦᏛᏁᎭ"),
                    bold("ᎿᏛᎦ"),
                    bold("ᏄᏛᏁᎸᎢ"),
                    bold("ᎾᏛᏁᎰᎢ"),
                    bold("ᏳᏛᏁᏗ"),
                )
            )
            _ = mascot_table.append(NoEscape(r"\midrule"))
            mascot_label = mascot_data["definition"] + f" (p. {mascot_page})"
            mascot_row: list[Any] = [
                NoEscape(str(unicode_to_latex(clean_latex_text(mascot_label))))
            ]
            for fn in mascot_forms:
                segmented = mascot_verb.segmented_forms.get(fn, "---")
                mascot_row.append(
                    format_segmented_verb_community(mascot_verb, fn, segmented)
                )
            _ = mascot_table.add_row(mascot_row)
            _ = mascot_table.append(NoEscape(r"\bottomrule"))
            doc.append(mascot_table)
            doc.append(NoEscape(r"\vspace{0.8em}"))

            sorted_group_verbs = sorted(
                group_verbs,
                key=lambda v: (
                    v.morphology.h_grade_root,
                    v.morphology.glottal_grade_root,
                    not v.morphology.config.pron.middle_voice == MiddleVoice.NONE,
                ),
            )

            doc.append(NoEscape(r"\noindent\begin{multicols}{3}"))
            for v in sorted_group_verbs:
                mp_tex = render_verb_minipage_community(v, resolver, toc_data)
                doc.append(NoEscape(mp_tex + r"\\[1em]"))
            doc.append(NoEscape(r"\end{multicols}"))
            doc.append(NoEscape(r"\vspace{1em}"))

    print(f"Saving community companion TeX to {COMMUNITY_COMPANION_TEX_PATH}...")
    doc.generate_tex()
    return True


if __name__ == "__main__":
    generate_community_companion_tex()
