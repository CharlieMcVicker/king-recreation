import csv
import json
import os
import re

from pylatex import Tabular
from pylatex.utils import bold
from pylatexenc.latexencode import unicode_to_latex

# Paths
ROOT_DIR = os.getcwd()
HIERARCHICAL_DICT_PATH = os.path.join(ROOT_DIR, "artifacts/data/hierarchical-dict.json")
CORPUS_TO_CND_PATH = os.path.join(ROOT_DIR, "artifacts/corpora/corpus_to_cnd.csv")
CND_PATH = os.path.join(ROOT_DIR, "data/cherokee_nation_dictionary.csv")
UNDERLYING_STEMS_PATH = os.path.join(ROOT_DIR, "artifacts/data/underlying_stems.csv")
OUTPUT_DIR = os.path.join(ROOT_DIR, "artifacts/tex/roots")
MAIN_TEX_PATH = os.path.join(ROOT_DIR, "artifacts/tex/main.tex")


def strip_tone(s):
    if not s:
        return ""
    # Strip all digits which represent tones in this transcription system
    return re.sub(r"\d", "", s)


def load_underlying_stems():
    stems = {}
    if not os.path.exists(UNDERLYING_STEMS_PATH):
        return stems
    with open(UNDERLYING_STEMS_PATH, "r", encoding="utf-8") as f:
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
    if not os.path.exists(CND_PATH):
        return cnd
    with open(CND_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entry_no = row["Entry No."]
            cnd[entry_no] = row["Syllabary"]
    return cnd


def get_syllabary(cid, form_name, corpus_to_cnd, cnd):
    if str(cid) not in corpus_to_cnd:
        return ""
    entry_ref = corpus_to_cnd[str(cid)].get(form_name)
    if not entry_ref:
        return ""
    return cnd.get(entry_ref, "")


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

    table = Tabular("|l|l|l|l|")
    table.add_hline()
    table.add_row(
        (bold("Form"), bold("Syllabary"), bold("With Tone"), bold("Toneless"))
    )
    table.add_hline()

    cid = verb.get("corpus_id")
    json_forms = verb.get("segmented_forms", {})

    for fn in forms:
        label = form_labels[fn]
        syllabary = get_syllabary(cid, fn, corpus_to_cnd, cnd)

        surface = ""
        toneless = ""

        stem_key = (str(cid), fn)
        if cid and stem_key in underlying_stems:
            candidates = underlying_stems[stem_key]
            surface = candidates[0][0]
            toneless = strip_tone(surface)
        else:
            surface = json_forms.get(fn, "")
            toneless = strip_tone(surface)

        table.add_row((label, syllabary, surface, toneless))

    table.add_hline()
    return table


def main():
    print("Loading data...")
    with open(HIERARCHICAL_DICT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    underlying_stems = load_underlying_stems()
    corpus_to_cnd = load_corpus_to_cnd()
    cnd = load_cnd()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    root_files = []

    print(f"Generating TeX files for {len(data)} roots...")
    for root_node in data:
        slug = root_node["slug"]
        h_grade = root_node["h_grade_root"]
        g_grade = root_node["glottal_grade_root"]

        content = []
        # Header with Root info
        header_text = f"Root: {h_grade}"
        if g_grade:
            header_text += f" / {g_grade}"
        content.append(r"\section*{" + unicode_to_latex(header_text) + "}")

        for cls in root_node["classes"]:
            content.append(r"\subsection*{" + unicode_to_latex(cls["class_name"]) + "}")

            for verb in cls["verbs"]:
                content.append(
                    r"\textbf{Definition: } " + unicode_to_latex(verb["definition"])
                )
                content.append(r"\\[0.5em]")

                table = generate_verb_table(verb, underlying_stems, corpus_to_cnd, cnd)
                content.append(table.dumps())
                content.append(r"\\[1em]")

        tex_path = os.path.join(OUTPUT_DIR, f"root_{slug}.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        root_files.append(f"root_{slug}.tex")

    print(f"Generating main.tex...")
    main_tex_content = [
        r"\documentclass{article}",
        r"\usepackage{fontspec}",
        r"\usepackage{booktabs}",
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

    with open(MAIN_TEX_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(main_tex_content))

    print(f"Generated {len(root_files)} root files and {MAIN_TEX_PATH}")
    print("Done!")


if __name__ == "__main__":
    main()
