import csv
import json
import os
import re
from typing import Dict, List

from pylatex import Tabularx
from pylatex.utils import NoEscape, bold, italic
from pylatexenc.latexencode import unicode_to_latex

from king_recreation.group_hierarchical import RootClassNode, RootNode
from king_recreation.morphemes.post_root_morphemes import PostRootMorphemeRegistry
from king_recreation.paths import (
    CHEROKEE_NATION_DICTIONARY_PATH,
    CORPUS_TO_CND_PATH,
    HIERARCHICAL_DICT_PATH,
    MAIN_TEX_PATH,
    TEX_ROOTS_DIR,
)
from king_recreation.reconstruction import ReconstructableVerb


def strip_tone(s):
    if not s:
        return ""
    # Strip all digits which represent tones in this transcription system
    return re.sub(r"\d", "", s)


def load_corpus_to_cnd():
    mapping = {}
    if not os.path.exists(CORPUS_TO_CND_PATH):
        return mapping
    with open(CORPUS_TO_CND_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["corpus_id"]
            mapping[cid] = row
    return mapping


def load_cnd():
    cnd = {}
    if not os.path.exists(CHEROKEE_NATION_DICTIONARY_PATH):
        return cnd
    with open(CHEROKEE_NATION_DICTIONARY_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entry_no = row["Entry No."]
            cnd[entry_no] = {
                "syllabary": row["Syllabary"],
                "tone": row["Tone and length 2"],
                "no_tone": row["Practical"],
            }
    return cnd


def get_cnd_entry(cid, form_name, corpus_to_cnd, cnd) -> Dict[str, str]:
    if str(cid) not in corpus_to_cnd:
        return {}
    entry_ref = corpus_to_cnd[str(cid)].get(form_name)
    if not entry_ref:
        return {}
    return cnd.get(entry_ref, {})


def generate_verb_table(verb: ReconstructableVerb, corpus_to_cnd, cnd):
    forms = [
        "present",
        "present_1sg",
        "imperfective",
        "perfective",
        "imperative",
        "infinitive",
    ]
    form_labels = {
        "present": "Present",
        "present_1sg": "1st Present",
        "imperfective": "Imperfective",
        "perfective": "Perfective",
        "imperative": "Imperative",
        "infinitive": "Infinitive",
    }

    table = Tabularx("l X X X", width_argument=NoEscape(r"\textwidth"))
    table.append(NoEscape(r"\toprule"))
    table.add_row(
        (bold("Form"), bold("Syllabary"), bold("With Tone"), bold("Toneless"))
    )
    table.append(NoEscape(r"\midrule"))

    cid = verb.corpus_id

    for fn in forms:
        label = form_labels[fn]
        cnd_entry = get_cnd_entry(cid, fn, corpus_to_cnd, cnd)

        syllabary = cnd_entry.get("syllabary", "---")
        surface = cnd_entry.get("tone", "---")
        toneless = cnd_entry.get("no_tone", "---")

        table.add_row((label, syllabary, surface, toneless))

    table.append(NoEscape(r"\bottomrule"))
    return table


def verb_config_to_tex(
    verb: ReconstructableVerb, root_str: str, parent_classes: list[str]
):
    if not parent_classes:
        parent_classes = []

    parts = []

    config = verb.config

    if config.pre.translocutive:
        parts.append("wi")

    if config.pre.partitive:
        parts.append("ni")

    if config.pre.distributive:
        parts.append("de")

    pronoun_map = {
        ("a", False, False): "a",
        ("a", True, False): "ka",
        ("a", False, True): "ani",
        ("b", False, False): "u",
        ("b", True, False): "u",
        ("b", False, True): "uni",
    }

    set_flaire = pronoun_map[
        config.pron.set_type,
        config.pron.use_ka_variant,
        config.pron.plural_pronouns,
    ]

    parts.append(italic(set_flaire))

    if not config.pron.middle_voice.value == "none":
        parts.append(config.pron.middle_voice.value.replace("_", "/").lower())

    parts.append(bold(root_str.replace(" ", "")))

    if verb.post_root_morpheme:
        prm = PostRootMorphemeRegistry.get_instance().morphemes_by_name.get(
            verb.post_root_morpheme
        )
        if prm:
            parts.append(prm.form)

    for class_name in parent_classes:
        parts.append("[" + class_name + "]")

    parts.append("[" + verb.class_name + "]")

    return "{-}".join(
        p if isinstance(p, NoEscape) else unicode_to_latex(p) for p in parts
    )


def load_hierarchical_data(path: str) -> List[RootNode]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    roots = []
    for root_data in data:
        classes = []
        for cls_data in root_data.get("classes", []):
            verbs = []
            for v_data in cls_data.get("verbs", []):
                verbs.append(ReconstructableVerb.from_dict(v_data))

            classes.append(
                RootClassNode(class_name=cls_data["class_name"], verbs=verbs)
            )

        roots.append(
            RootNode(
                h_grade_root=root_data["h_grade_root"],
                glottal_grade_root=root_data.get("glottal_grade_root"),
                slug=root_data["slug"],
                classes=classes,
            )
        )
    return roots


def render_verb_entry(
    verb: ReconstructableVerb, root_str: str, corpus_to_cnd, cnd, parent_classes=None
) -> List[str]:
    if parent_classes is None:
        parent_classes = []

    level = len(parent_classes)
    content = []
    verb_tex = verb_config_to_tex(verb, root_str, parent_classes)

    if level == 0:
        header_cmd = r"\subsubsection*"
        toc_level = "subsection"
    else:
        # Use paragraph for derivations
        header_cmd = r"\paragraph*"
        toc_level = "subsubsection"

    if level > 0:
        content.append(r"\needspace{1in}")
    else:
        content.append(r"\needspace{2in}")

    content.append(header_cmd + "{" + verb_tex + "}")
    content.append(r"\nopagebreak")

    content.append(r"\textbf{Definition: } " + unicode_to_latex(verb.definition))

    label = verb_tex + unicode_to_latex(" (" + verb.definition + ")")

    content.append(r"\addcontentsline{toc}{" + toc_level + "}{" + label + "}")
    content.append(r"\\[0.5em]")

    table = generate_verb_table(verb, corpus_to_cnd, cnd)
    content.append(table.dumps())
    content.append(r"\\[1em]")

    if verb.derivations:
        for derivation in verb.derivations:
            content.extend(
                render_verb_entry(
                    derivation,
                    root_str,
                    corpus_to_cnd,
                    cnd,
                    parent_classes=parent_classes + [verb.class_name],
                )
            )

    return content


def generate_tex_files():
    print("Loading data...")
    if not os.path.exists(HIERARCHICAL_DICT_PATH):
        print(f"Error: {HIERARCHICAL_DICT_PATH} not found.")
        return

    data = load_hierarchical_data(HIERARCHICAL_DICT_PATH)
    corpus_to_cnd = load_corpus_to_cnd()
    cnd = load_cnd()

    os.makedirs(TEX_ROOTS_DIR, exist_ok=True)

    root_files = []

    print(f"Generating TeX files for {len(data)} roots...")
    for root_node in data:
        slug = root_node.slug
        h_grade = root_node.h_grade_root
        g_grade = root_node.glottal_grade_root

        content = []
        # Header with Root info
        root_str = f"{h_grade}"
        if g_grade and not g_grade == h_grade:
            root_str += f" / {g_grade}"

        header_text = "Root: " + root_str
        content.append(r"\needspace{4in}")
        content.append(r"\section*{" + unicode_to_latex(header_text) + "}")
        content.append(
            r"\markboth{"
            + unicode_to_latex(root_str)
            + "}{"
            + unicode_to_latex(root_str)
            + "}"
        )
        content.append(r"\nopagebreak")
        content.append(
            r"\addcontentsline{toc}{section}{" + unicode_to_latex(root_str) + "}"
        )

        for cls in root_node.classes:

            content.append(r"\needspace{3in}")
            content.append(
                r"\subsection*{" + unicode_to_latex("Class: " + cls.class_name) + "}"
            )
            content.append(r"\nopagebreak")

            for verb in cls.verbs:
                content.extend(render_verb_entry(verb, root_str, corpus_to_cnd, cnd))

        tex_path = os.path.join(TEX_ROOTS_DIR, f"root_{slug}.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        root_files.append(f"root_{slug}.tex")

    print(f"Generating main.tex and booklet.tex...")
    main_tex_content = [
        r"\documentclass[oneside,openany]{book}",
        r"\usepackage{fontspec}",
        r"\usepackage{booktabs}",
        r"\usepackage{tabularx}",
        r"\usepackage{needspace}",
        r"\usepackage[paperwidth=5.5in, paperheight=8.5in, margin=0.5in, headheight=14pt]{geometry}",
        r"\usepackage{fancyhdr}",
        r"\usepackage{titlesec}",
        r"\titleformat{\subsection}{\normalfont\large\bfseries}{}{0pt}{}",
        r"\titleformat{\subsubsection}[hang]{\normalfont\normalsize\bfseries}{}{0pt}{}",
        r"\titleformat{\paragraph}[hang]{\normalfont\normalsize\bfseries}{}{0pt}{}",
        r"\setcounter{tocdepth}{4}",
        r"\setmainfont{Noto Sans Cherokee}[AutoFakeBold=1.5, AutoFakeSlant=0.2]",
        r"\title{Cherokee Root-based Dictionary}",
        r"\author{Charlie ᏣᎵ McVicker}",
        r"\pagestyle{fancy}",
        r"\fancyhf{}",
        r"\fancyhead[L]{\rightmark}",
        r"\fancyhead[R]{\leftmark}",
        r"\fancyfoot[C]{\thepage}",
        r"\begin{document}",
        r"\maketitle",
        r"\tableofcontents",
        r"\newpage",
        r"\chapter{Verb tables by root}",
    ]

    for rf in sorted(root_files):
        main_tex_content.append(r"\input{roots/" + rf + "}")

    main_tex_content.append(r"\end{document}")

    with open(MAIN_TEX_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(main_tex_content))

    # Generate booklet.tex
    booklet_tex_path = os.path.join(os.path.dirname(MAIN_TEX_PATH), "booklet.tex")
    booklet_tex_content = [
        r"\documentclass[letterpaper]{article}",
        r"\usepackage[margin=0.25in]{geometry}",
        r"\usepackage{pdfpages}",
        r"\begin{document}",
        r"\includepdf[pages=-, nup=2x1, landscape, booklet=true]{main.pdf}",
        r"\end{document}",
    ]
    with open(booklet_tex_path, "w", encoding="utf-8") as f:
        f.write("\n".join(booklet_tex_content))

    print(
        f"Generated {len(root_files)} root files, {MAIN_TEX_PATH}, and {booklet_tex_path}"
    )
    return True
