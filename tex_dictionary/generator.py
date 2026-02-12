import csv
import json
import os
import re
from typing import Dict

from pylatex import Tabularx
from pylatex.utils import NoEscape, bold
from pylatexenc.latexencode import unicode_to_latex

from king_recreation import paths


def strip_tone(s):
    if not s:
        return ""
    # Strip all digits which represent tones in this transcription system
    return re.sub(r"\d", "", s)


def load_underlying_stems():
    stems = {}
    if not os.path.exists(paths.underlying_stems_path):
        return stems
    with open(paths.underlying_stems_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["corpus_id"]
            fn = row["form"]
            key = (cid, fn)
            if key not in stems:
                stems[key] = []
            stems[key].append((row["surface_stem"], row["underlying_stem"]))
    return stems


def load_corpus_to_cnd():
    mapping = {}
    if not os.path.exists(paths.corpus_to_cnd_path):
        return mapping
    with open(paths.corpus_to_cnd_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["corpus_id"]
            mapping[cid] = row
    return mapping


def load_cnd():
    cnd = {}
    if not os.path.exists(paths.cherokee_nation_dictionary_path):
        return cnd
    with open(paths.cherokee_nation_dictionary_path, "r", encoding="utf-8-sig") as f:
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


def generate_verb_table(verb, underlying_stems, corpus_to_cnd, cnd):
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

    cid = verb.get("corpus_id")

    for fn in forms:
        label = form_labels[fn]
        cnd_entry = get_cnd_entry(cid, fn, corpus_to_cnd, cnd)

        syllabary = cnd_entry.get("syllabary", "---")
        surface = cnd_entry.get("tone", "---")
        toneless = cnd_entry.get("no_tone", "---")

        table.add_row((label, syllabary, surface, toneless))

    table.append(NoEscape(r"\bottomrule"))
    return table


def verb_config_to_str(config: dict):
    set_flaire = "Set " + config["pron"]["set_type"]

    if config["pron"]["plural_pronouns"]:
        set_flaire += " (plural)"

    middle_flaire = None
    if not config["pron"]["middle_voice"] == "none":
        middle_flaire = config["pron"]["middle_voice"].replace("_", "/").lower()

    return ", ".join(f for f in [set_flaire, middle_flaire] if f is not None)


def generate_tex_files():
    print("Loading data...")
    if not os.path.exists(paths.hierarchical_dict_path):
        print(f"Error: {paths.hierarchical_dict_path} not found.")
        return

    with open(paths.hierarchical_dict_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    underlying_stems = load_underlying_stems()
    corpus_to_cnd = load_corpus_to_cnd()
    cnd = load_cnd()

    os.makedirs(paths.TEX_ROOTS_DIR, exist_ok=True)

    root_files = []

    print(f"Generating TeX files for {len(data)} roots...")
    for root_node in data:
        slug = root_node["slug"]
        h_grade = root_node["h_grade_root"]
        g_grade = root_node["glottal_grade_root"]

        content = []
        # Header with Root info
        root_str = f"{h_grade}"
        if g_grade and not g_grade == h_grade:
            root_str += f" / {g_grade}"

        header_text = "Root: " + root_str
        content.append(r"\section*{" + unicode_to_latex(header_text) + "}")
        content.append(
            r"\addcontentsline{toc}{section}{" + unicode_to_latex(root_str) + "}"
        )

        for cls in root_node["classes"]:
            content.append(
                r"\subsection*{" + unicode_to_latex("Class: " + cls["class_name"]) + "}"
            )

            for verb in cls["verbs"]:
                verb_str = verb_config_to_str(verb["config"])
                content.append(
                    r"\subsubsection*{With... " + unicode_to_latex(verb_str) + "}"
                )
                content.append(
                    r"\textbf{Definition: } " + unicode_to_latex(verb["definition"])
                )
                content.append(
                    r"\addcontentsline{toc}{subsection}{"
                    + unicode_to_latex(
                        verb["definition"]
                        + " ("
                        + verb["class_name"]
                        + ", "
                        + verb_str
                        + ")"
                    )
                    + "}"
                )
                content.append(r"\\[0.5em]")

                table = generate_verb_table(verb, underlying_stems, corpus_to_cnd, cnd)
                content.append(table.dumps())
                content.append(r"\\[1em]")

        tex_path = os.path.join(paths.TEX_ROOTS_DIR, f"root_{slug}.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        root_files.append(f"root_{slug}.tex")

    print(f"Generating main.tex...")
    main_tex_content = [
        r"\documentclass{article}",
        r"\usepackage{fontspec}",
        r"\usepackage{booktabs}",
        r"\usepackage{tabularx}",
        r"\usepackage[margin=1in]{geometry}",
        r"\setmainfont{Plantagenet Cherokee}",
        r"\title{Cherokee Hierarchical Dictionary}",
        r"\author{King Recreation}",
        r"\begin{document}",
        r"\maketitle",
        r"\tableofcontents",
        r"\newpage",
    ]

    for rf in sorted(root_files):
        main_tex_content.append(r"\input{roots/" + rf + "}")

    main_tex_content.append(r"\end{document}")

    with open(paths.MAIN_TEX_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(main_tex_content))

    print(f"Generated {len(root_files)} root files and {paths.MAIN_TEX_PATH}")
    return True
