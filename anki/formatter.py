"""
HTML and text formatting for Cherokee Anki cards in Community Orthography.
"""

from __future__ import annotations

import html
import re
from typing import Any

from dictionary_pipeline.dictionary_forms import (
    DictionaryVerb,
    Prediction,
    build_wordspec,
)
from dictionary_pipeline.orthography import unrespell_consonants
from morphology.h_alternation import prevent_C_glottal_cluster
from morphology.morphology_types import PronominalSet
from tex_dictionary.companion_data import AspectClass
from anki.english_inflector import clean_pronouns

FORM_LABELS: list[tuple[str, str, str]] = [
    ("present", "Present", "ᎾᏛᏁᎭ"),
    ("imperfective", "Imperfective", "ᎾᏛᏁᎰᎢ"),
    ("perfective", "Perfective", "ᏄᏛᏁᎸᎢ"),
    ("present_1sg", "1st Present", "ᏂᎦᏛᏁᎭ"),
    ("imperative", "Imperative", "ᎿᏛᎦ"),
    ("infinitive", "Infinitive", "ᏳᏛᏁᏗ"),
]

FORM_MAP: dict[str, tuple[str, str]] = {
    fn: (eng, syl) for fn, eng, syl in FORM_LABELS
}


def format_segmented_verb_html(
    verb: DictionaryVerb,
    form_name: str,
    segmented_form: str,
) -> str:
    """
    Converts a segmented verb form into Community Orthography HTML with:
    - Colored pronoun prefix (Set A = red #c53030, Set B = royal blue #8888ff, Person-to-person = purple #6b46c1)
    - Bold and underlined aspect ending (#cc5555)
    - Clean community orthography
    """
    if not segmented_form or segmented_form == "---":
        return "---"

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

    chars_with_role: list[dict[str, Any]] = []
    for i, seg in enumerate(segments):
        role = 0
        if i == pronoun_idx:
            role = 1
        elif i == aspect_idx:
            role = 2
        for c in seg:
            chars_with_role.append({"char": c, "role": role})

    # Drop dropped phones
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

    temp_str = "".join([str(c["char"]) for c in chars_with_role])
    fixed_str = prevent_C_glottal_cluster(temp_str)

    if fixed_str != temp_str:
        new_chars: list[dict[str, Any]] = []
        for c in fixed_str:
            new_chars.append({"char": c, "role": 0})
        if len(new_chars) == len(chars_with_role):
            for idx in range(len(new_chars)):
                new_chars[idx]["role"] = chars_with_role[idx]["role"]
        chars_with_role = new_chars

    prediction = Prediction(
        str(verb.original_data.get("prediction") or "FullEventful")
    )
    spec = build_wordspec(prediction, config.pron, form_name)
    color_hex = "#1a202c"
    color_name = "default"

    if spec.pronominal_set == PronominalSet.SET_A:
        color_hex = "#c53030"
        color_name = "set-a"
    elif spec.pronominal_set == PronominalSet.SET_B:
        color_hex = "#8888ff"
        color_name = "set-b"
    elif spec.pronominal_set == PronominalSet.PERSON_TO_PERSON:
        color_hex = "#6b46c1"
        color_name = "person-to-person"

    role_groups: list[dict[str, Any]] = []
    if chars_with_role:
        cur_role = chars_with_role[0]["role"]
        cur_chars: list[str] = [chars_with_role[0]["char"]]
        for item in chars_with_role[1:]:
            if item["role"] == cur_role:
                cur_chars.append(item["char"])
            else:
                role_groups.append(
                    {"role": cur_role, "text": "".join(cur_chars)}
                )
                cur_role = item["role"]
                cur_chars = [item["char"]]
        role_groups.append({"role": cur_role, "text": "".join(cur_chars)})

    formatted_parts: list[str] = []
    for grp in role_groups:
        role = grp["role"]
        comm_text = unrespell_consonants(grp["text"])
        escaped = html.escape(comm_text)

        if role == 1:
            formatted_parts.append(
                f'<span class="pronoun pron-{color_name}" style="color:'
                f' {color_hex}; font-weight: 600;">{escaped}</span>'
            )
        elif role == 2:
            formatted_parts.append(
                f'<span class="aspect-suffix" style="font-weight: bold;'
                f' border-bottom: 2px solid #888888; color:'
                f' #cc5555;">{escaped}</span>'
            )
        else:
            formatted_parts.append(escaped)

    return "".join(formatted_parts)


def format_template_html(verb: DictionaryVerb) -> str:
    """
    Renders the morphological template breakdown in HTML with colored Set A/Set B spans.
    """
    config = verb.morphology.config
    parts: list[str] = []

    if config.pre.translocutive:
        parts.append("wi")
    if config.pre.partitive:
        parts.append("ni")
    if config.pre.distributive:
        parts.append("te")

    ka_label = "Set A (ga)" if config.pron.use_ka_variant else "Set A"
    if config.pron.plural_pronouns:
        ka_label += " (pl)"

    if config.pron.set_type == PronominalSet.SET_A:
        parts.append(
            f'<span style="color: #c53030; font-weight: 600;">{ka_label}</span>'
        )
    elif config.pron.set_type == PronominalSet.SET_B:
        set_b_lbl = "Set B (pl)" if config.pron.plural_pronouns else "Set B"
        parts.append(
            f'<span style="color: #8888ff; font-weight: 600;">{set_b_lbl}</span>'
        )

    if config.pron.middle_voice.value != "none":
        mv = config.pron.middle_voice.value.replace("_", "/").lower()
        parts.append(f'<span style="color: #4a5568; font-style: italic;">{mv}</span>')

    root_str = verb.morphology.h_grade_root
    if (
        verb.morphology.glottal_grade_root
        and verb.morphology.glottal_grade_root != verb.morphology.h_grade_root
    ):
        root_str += f" / {verb.morphology.glottal_grade_root}"

    comm_root = unrespell_consonants(root_str)
    parts.append(f"<strong>{html.escape(comm_root)}</strong>")

    if verb.morphology.post_root_morpheme:
        parts.append(html.escape(verb.morphology.post_root_morpheme))

    parts.append(
        f'<span style="color: #2d3748; font-weight:'
        f' bold;">[{html.escape(verb.morphology.class_name)}]</span>'
    )

    return "-".join(parts)


def build_verb_table_html(
    class_name: str,
    verb: DictionaryVerb,
    is_mascot: bool = False,
    aspect_class: AspectClass | None = None,
) -> str:
    """
    Generates the complete HTML paradigm table for a verb (mascot or member verb).
    """
    verb_forms: dict[str, str] = {}
    for fn, _, _ in FORM_LABELS:
        seg = verb.segmented_forms.get(fn, "---")
        verb_forms[fn] = format_segmented_verb_html(verb, fn, seg)

    verb_def = html.escape(clean_pronouns(verb.definition, "3rd_she"))
    verb_root = unrespell_consonants(verb.morphology.h_grade_root)
    verb_template = format_template_html(verb)
    label = "Mascot:" if is_mascot else "Verb:"

    table_html = f"""
<div class="class-card-header" style="background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 5px; padding: 12px; margin-top: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: left;">
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #cbd5e0; padding-bottom: 6px; margin-bottom: 8px;">
        <span style="font-size: 1.05em; font-weight: bold; color: #2d3748;">Class: <span style="color: #2b6cb0;">{html.escape(class_name)}</span></span>
    </div>
    <div style="font-size: 0.8em; margin-bottom: 8px; color: #4a5568;">
      <span style="font-size: 1.2em;">{label}</span> <span style="font-size: 1.2em; font-weight: 700;">{html.escape(verb_root)}</span> | <em>{verb_def}</em> | <code>{verb_template}</code>
    </div>
    <table style="width: 100%; border-collapse: collapse; font-size: 0.88em; text-align: center;">
        <thead>
            <tr style="background: #edf2f7; color: #8d97a8;">
                <th style="padding: 4px 6px; border: 1px solid #cbd5e0; font-size: 0.85em;"><i>Present</i><br></th>
                <th style="padding: 4px 6px; border: 1px solid #cbd5e0; font-size: 0.85em;"><i>Imperfective</i><br></th>
                <th style="padding: 4px 6px; border: 1px solid #cbd5e0; font-size: 0.85em;"><i>Perfective</i><br></th>
            </tr>
        </thead>
        <tbody>
            <tr style="background: #ffffff; color: #555555;">
                <td style="padding: 6px; border: 1px solid #cbd5e0;">{verb_forms['present']}</td>
                <td style="padding: 6px; border: 1px solid #cbd5e0;">{verb_forms['imperfective']}</td>
                <td style="padding: 6px; border: 1px solid #cbd5e0;">{verb_forms['perfective']}</td>
            </tr>
            <tr style="background: #edf2f7; color: #8d97a8;">
                <th style="padding: 4px 6px; border: 1px solid #cbd5e0; font-size: 0.85em;"><i>1st Present</i><br></th>
                <th style="padding: 4px 6px; border: 1px solid #cbd5e0; font-size: 0.85em;"><i>Imperative</i><br></th>
                <th style="padding: 4px 6px; border: 1px solid #cbd5e0; font-size: 0.85em;"><i>Infinitive</i><br></th>
            </tr>
            <tr style="background: #ffffff; color: #555555;">
                <td style="padding: 6px; border: 1px solid #cbd5e0;">{verb_forms['present_1sg']}</td>
                <td style="padding: 6px; border: 1px solid #cbd5e0;">{verb_forms['imperative']}</td>
                <td style="padding: 6px; border: 1px solid #cbd5e0;">{verb_forms['infinitive']}</td>
            </tr>
        </tbody>
    </table>
</div>
"""
    return table_html.strip()


def build_class_table_html(
    class_name: str,
    mascot_verb: DictionaryVerb,
    aspect_class: AspectClass | None = None,
) -> str:
    """Alias for backwards compatibility."""
    return build_verb_table_html(
        class_name, mascot_verb, is_mascot=True, aspect_class=aspect_class
    )


def build_card_front_html(
    card_type: str,
    definition: str,
    tense_name: str | None = None,
    syllabary_header: str | None = None,
    class_name: str | None = None,
) -> str:
    """
    Builds the Front HTML matching user test card format:
    - Mascot words: color #ff8888
    - Non-mascot words: color #88ff88
    """
    def_escaped = html.escape(definition)

    if card_type == "mascot_tense":
        t_esc = html.escape(tense_name or "")
        syl_esc = html.escape(syllabary_header or "")
        return f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; font-size: 1.4em; font-weight: bold; line-height: 1.3; color: #ff8888;">
  {def_escaped}
</div>
<div style="font-size: 1em; padding: 6px 16px; color: rgb(120, 120, 120); text-align: center">
  <i><strong>{t_esc}</strong> ({syl_esc})</i>
</div>
""".strip()

    elif card_type == "verb_root":
        return f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; font-size: 1.4em; font-weight: bold; line-height: 1.3; color: #88ff88;">
  {def_escaped}
</div>
<div style="font-size: 1em; padding: 6px 16px; color: rgb(120, 120, 120); text-align: center">
  <i><strong>Root</strong></i>
</div>
""".strip()

    elif card_type == "practice_test":
        t_esc = html.escape(tense_name or "")
        syl_esc = html.escape(syllabary_header or "")
        return f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; font-size: 1.4em; font-weight: bold; line-height: 1.3; color: #88ff88;">
  {def_escaped}
</div>
<div style="font-size: 1em; padding: 6px 16px; color: rgb(120, 120, 120); text-align: center">
  <i><strong>{t_esc}</strong> ({syl_esc})</i>
</div>
""".strip()

    return def_escaped


def build_card_back_html(
    card_type: str,
    verb: DictionaryVerb,
    form_name: str | None = None,
    segmented_form: str | None = None,
) -> str:
    """
    Builds the Back HTML matching user test card format:
    - Mascot words: color #ff8888
    - Non-mascot root cards: -{root}- with color #ff8888
    - Non-mascot practice cards: color #ff8888
    """
    root_str = verb.morphology.h_grade_root
    if (
        verb.morphology.glottal_grade_root
        and verb.morphology.glottal_grade_root != verb.morphology.h_grade_root
    ):
        root_str += f" / {verb.morphology.glottal_grade_root}"
    comm_root = unrespell_consonants(root_str)

    if card_type == "mascot_tense":
        fn = form_name or "present"
        seg = segmented_form or verb.segmented_forms.get(fn, "---")
        surface_html = format_segmented_verb_html(verb, fn, seg)

        return f"""
<div class="card-back form-back" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 16px;">
    <div class="cherokee-word" style="font-size: 1.8em; font-weight: 500; margin-bottom: 8px; color: #ff8888;">
        {surface_html}
    </div>
</div>
""".strip()

    elif card_type == "verb_root":
        return f"""
<div class="card-back form-back" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 16px;">
    <div class="cherokee-word" style="font-size: 1.8em; font-weight: 500; margin-bottom: 8px; color: #ff8888;">
        -{html.escape(comm_root)}-
    </div>
</div>
""".strip()

    elif card_type == "practice_test":
        fn = form_name or "present"
        seg = segmented_form or verb.segmented_forms.get(fn, "---")
        surface_html = format_segmented_verb_html(verb, fn, seg)

        return f"""
<div class="card-back form-back" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 16px;">
    <div class="cherokee-word" style="font-size: 1.8em; font-weight: 500; margin-bottom: 8px; color: #ff8888;">
        {surface_html}
    </div>
</div>
""".strip()

    return ""
