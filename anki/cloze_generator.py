"""
Anki Cloze Card Generator for Cherokee Example Sentences.
Generates fill-in-the-blank cards for all words in the dictionary sentences.
"""

from __future__ import annotations

import csv
import hashlib
import os
import random
import tempfile
import time
import unicodedata
from typing import Any

import genanki

from anki.models import ClozeCard

CLOZE_MODEL_ID = 1607392320
CLOZE_MODEL_NAME = "Cherokee Sentence Cloze"
CLOZE_DECK_NAME = "Cherokee Cloze Sentences"

# Sentence boundary punctuation to strip from word edges (colon ':' is intentionally excluded)
PUNCT_CHARS = '.,?!;""«»“”„…()[]{}/\\'

# Known OCR/typo fixes for raw officialdata.csv sentences to ensure perfect 1-to-1 word alignment
SENTENCE_CLEANUPS: dict[str, tuple[str, str]] = {
    "51.1": ("ᎠᏓᏍᏓᏴᏗ ᎠᏯᎠ ᏗᏖᎵᏙ ᏕᎬᏗᏰᎠ.", "ada:sdà:yhdi̋ à:yá’a di:te:li:dó de:gv́:dǐ:yé’a"),
    "56.1": ("ᎠᏓᏪᎳᎩᏍᎬ ᏚᎴᎢᏔᏅ ᎦᏐᎯᎢ.", "à:dawě:lágì:sgv̋: dù:lé:yhtanv́ ga:sohi̋:’i"),
    "61.1": ("ᎤᏪᏴ ᎠᏆᏓᏬᏍᏗ ᎤᎪᏓ ᎠᎩᎸᏉᏓ ᏏᏃ ᎠᏓᏬᏍᏗ ᎨᏒᎢ.", "ù:wé:yv̋: agwadawò:sdi̋: ù:gô:da à:gilv̌:kwda si:hnó: adawò:sdi̋ gè:sv̋:’i"),
    "91.1": ("ᎭᏢ ᎢᏴ ᎤᏞᏎᎢ?", "ha:hlv́ iyv̋: ù:dlé:sé:’i"),
    "96.1": ("ᎦᏙ ᎤᏍᏗ ᎠᏟᎠ? ᎠᎹ‚ ᎤᏅᏓᎨ?", "gado u:sdi à:dlí’a ama‚ u:nv̌:dáké?"),
    "104.1": ("ᎠᏢᏈᏍᎬᏊ ᎢᎦ ᎨᏐ ᏳᏬᏂᏌ.", "à:dlv̌:kwsgv̋:gwu i:ga̋ gè:só yǔ:wô:ni̋:sa"),
    "367.1": ("ᏧᎾᏍᏗ ᎠᏂᎨᏳᏣ ᏗᏁᏟᏗ ᏓᎾᏁᏟᏗᏍᎪᎢ.", "ju:nsdi̋: ani:gě:hű:ja di:né:hldi dà:ná:ne:lhdi:sgó:’i"),
    "391.1": ("ᎦᎦᎹ ᎤᏍᏗᎩᏍᏗ ᎤᏚᎵᎭ.", "gǎ:gáma usdi:gî:sdi̋ ù:du:lǐ:ha"),
    "398.1": ("ᏦᎢ ᏗᏍᏛᎭᏟ ᏚᎬᎢ.", "jo’i di:sdv̋:hahli dù:gv̌:’i"),
    "415.1": ("ᎠᏍᎦᏰᎬᏍᏓ ᏙᏛᎪᎵᏰᎢ ᎠᏂᏲᏍᎩ ᏚᎾᏄᏮᎢ.", "asgaye:gv:sdá do:dv:gó:lì:ye’i ani̋:yosgi dù:nahnúwv̋:’i"),
    "418.1": ("ᎠᏍᎪᎩᏍᎬ ᎦᎴᏴᏍᏗᏍᎪ ᏡᎬ ᏙᏯ.", "à:sgogí:sgv̋: gale:yv:sdǐ:sgó: dluhgv̋ do:ya"),
    "422.1": ("Ꮎ ᏗᏍᎪᎸᏗᏍᏗ ᏙᏗᏍᎬᏏ.", "ná disgó:lv̋:dì:sdi do:di:skv́si"),
    "448.1": ("ᏓᎿᏩ ᎠᏟᎲ ᎠᏥᏐᏅᏁ ᎠᏍᎦᏯ.", "da:hnawá à:hlíhv̋ à:jì:so:nv:hné asgayâ"),
    "483.1": ("ᏗᏖᎵᏙ ᏕᎬᏗᏰᎠ.", "di:te:li:dó de:gv́:dǐ:yé’a"),
    "527.1": ("Ꮭ ᎩᎶ ᏴᎬᏗᏍᎦᎳᏍ ᎠᏲᎱᎯᏍᏗ.", "hla kilő: yigv́:di:sgala:s ayo:hu:hisdi"),
    "538.1": ("ᎭᏢ ᏕᎯᏴᏫᏗ ᎠᏓ?", "ha:dlv̋: de:hí:yv:hwi:di ada?"),
    "707.1": ("ᏗᏤ ᏗᏆᎾᏲᏍᏗ ᏚᏲᎱᏏ.", "di:je̋ di:kwanyo:sdi dù:yo:hu:si"),
    "821.1": ("ᏦᎢᎭ ᎢᏯᏂᎢ ᏓᎾᏓᏁᏟᏴ ᏓᏂᎦᏪᏍᎬᎢ ᏥᏳ.", "jó’i:ha̋: iyáni̋:’i dà:ndane:dlí:yv dà:ni:gawé:sgv̋:’i ji:yu"),
    "826.1": ("ᎨᏛ ᏕᎦᏆᏲᎯᎭ ᏓᎳᎳ.", "ge:tv̋ de:gá:gwa:yo:hiha dala:la"),
    "827.1": ("ᏗᎦᎭᏘᏗ ᏚᏭᏔᏅ ᎨᏛᏍᏗ ᎠᏍᏡᏍᎬᎢ.", "digá:hatdi̋ dù:whtanv́ ge̋:tvsdi dà:sdlû:sgv̋:’i"),
    "844.1": ("ᎢᏤ ᎠᎿᏬ ᏥᏁᎭ.", "ije̋ ahnawó jí’neha"),
    "927.1": ("ᏗᏁᏍᎨᏍᎩ ᏂᎪᎯᎸ ᎦᏅᏙᎩ ᎬᏗᏍᎪ ᏓᏁᏍᎨᏍᎬᎢ.", "di:hnè:sge̋:sgi nigo:hí:lv̋: ganhdohgi kdǐ:sgô: dà:hne:sge:sgv̋:’i"),
    "953.1": ("ᏗᏓᏠᏍᏗ ᏧᏬᏢᏙᏗ ᎦᏃᏥ ᎤᏚᎵᎭ.", "di:da:dlǒ:sdi juwő:hlvhdohdi gano:ji ù:du:lǐ:ha"),
    "966.1": ("ᎦᏄᎸ ᎠᎦᎵᏍᏗ ᎣᏍᏓ ᏂᎬᏁᎭ.", "ganu:lv́ ágà:lsdi ő:sda nigv́:ne:ha"),
    "973.1": ("ᎦᏅᏆᎶᏍᏗ ᏥᎩ ᏗᏁᏍᎨᏍᎩ ᎤᏮᏔᏂᏓᏍᏗ.", "ganv:gwalő:sdi ji̋gi di:hnè:sge̋:sgi uwhtani̋:dà:sdi"),
    "980.1": ("ᎢᏤ ᎠᎿᏬ ᏥᏅᏁᎸᎢ.", "ije̋: ahnawó ji:nv́:ne:lv̌:’i"),
    "1012.1": ("ᏞᏍᏗ ᎦᏬᏂᏓ ᏯᏛᏓᏍᏗᏍᎨᏍᏗ.", "hlè:sdi gawò:nǐ:da hyahtv́:dà:sdǐ:sgé:sdi"),
    "1017.1": ("ᎠᎾᎦᎵᏍᎩ ᎠᏂᎩᏍᏗᏍᎩ ᎦᏰᏫᏍᎩ ᎤᏚᎵᎭ.", "anà:galǐ:sgi a:hnígì:sdi̋:sgi ga:ye:wsgi ù:du:lǐ:ha"),
    "1028.1": ("ᎪᎳ ᏧᎬᏩᎶᏗ ᏗᎨᎵᏍᏘᎩ?", "hilá: ju:gv̋:wahldi digeli̋:sgi?"),
    "1085.1": ("ᎯᎳ ᎢᎦ ᏗᎫᏢᏗ ᏕᏣᏚᎵᎭ?", "hilá: í:ga̋: digu:tlv̂:di de:jádu:lǐ:ha?"),
    "1089.1": ("ᎫᎴ ᏗᏍᎪᏂ ᎦᏃᎯᎵᏒ ᏥᎪᏩᏘ.", "gu:lé di:sgő:hni gano:hǐ:lî:sv̋: ji:gò:wahti"),
    "1342.1": ("ᎫᏩᏲ ᏫᏚᎸᏫᏍᏓᏁᎰ ᏦᏍᏓᏓᏅᏟ.", "kuwá:yő widù:lv̌:hwísdà:ne:hó jo:sdada:hnv̋:hli"),
    "1444.1": ("Ꮎ ᏗᏂᏲᏟ ᏍᏆᏞᏍᏗ ᏧᎾᏁᎶᏗ ᎤᎾᏚᎵᎭ.", "ná di:ni:yő:hli sgwà:hlé:sdi ju:na:né:lhdohdi̋: ù:nadulǐ:ha"),
    "1487.1": ("ᏒᎾᏙᏓᏆᏍᏗ Ꮭ ᎪᎯᏓ ᏱᎨᏐᎢ.", "sv:nadő:dagwà:sdi hla go:hi̋:da yigê:só:’i"),
    "1521.1": ("ᎪᎦ ᏂᎦᏪᏍᎬ ᏯᏛᎦᎾ ᎤᏒ‚ ᎤᏓᎴᎯ ᎠᎾᏗᏍᎪ ᎠᏂᏣᎳᎩ.", "kó:ga nigawè:sgv̋ yátv̋:gà:na usv̋ udalě:hi á:nadi:sgó: ani:jalagi"),
    "1546.1": ("ᎭᏢ ᎤᏗᏍᎦᏝ?", "ha:hlv̋: u:di:sgahla?"),
    "1601.1": ("ᎦᏙᎯ ᎤᎯᏌᏔ.", "ga:dő:hi ù:hí:sata"),
    "1678.1": ("ᎦᏙ ᏧᎵᏰᏗᎭ?", "gadò: julǐyê:di̋:ha?"),
    "1785.1": ("ᎩᏟ ᎤᎿᎸᎯ ᎤᏪᎧᎭ.", "gi:hli u:hna:lv̋:hi ù:we:kaha."),
}


def make_anki_id(name: str) -> int:
    """Generates a deterministic 31-bit integer for Anki deck or model IDs."""
    return int(hashlib.md5(name.encode("utf-8")).hexdigest()[:8], 16) & 0x7FFFFFFF


def clean_asterisks(text: str) -> str:
    """Strips bolding asterisks from dictionary sentences."""
    return text.replace("*", "").strip()


def remove_tone_and_length(text: str) -> str:
    """
    Strips vowel length colons (':') and tone diacritics from Cherokee phonetic strings.
    Normalizes glottal stops to standard apostrophes.
    """
    # 1. Remove length colons ':'
    text_no_colon = text.replace(":", "")

    # 2. Normalize glottal stop variants to standard apostrophe
    text_normalized_glottal = text_no_colon.replace("ʔ", "'").replace("ʼ", "'")

    # 3. Decompose unicode characters into base letter + combining marks
    nfkd_form = unicodedata.normalize("NFKD", text_normalized_glottal)

    # 4. Filter out all combining diacritical marks (category 'Mn')
    stripped = "".join(c for c in nfkd_form if unicodedata.category(c) != "Mn")

    # 5. Normalize back to NFC
    return unicodedata.normalize("NFC", stripped)


def tokenize_cherokee(text: str) -> list[dict[str, str]]:
    """
    Splits Cherokee sentence text into word tokens, isolating leading and trailing punctuation.
    """
    cleaned = clean_asterisks(text)
    raw_tokens = cleaned.split()
    tokens: list[dict[str, str]] = []

    for raw in raw_tokens:
        lead_idx = 0
        while lead_idx < len(raw) and raw[lead_idx] in PUNCT_CHARS:
            lead_idx += 1
        prefix = raw[:lead_idx]
        rest = raw[lead_idx:]

        trail_idx = len(rest)
        while trail_idx > 0 and rest[trail_idx - 1] in PUNCT_CHARS:
            trail_idx -= 1
        word = rest[:trail_idx]
        suffix = rest[trail_idx:]

        if word:
            tokens.append(
                {
                    "raw": raw,
                    "prefix": prefix,
                    "word": word,
                    "suffix": suffix,
                }
            )
        elif prefix or suffix:
            extra_punct = prefix + suffix
            if tokens:
                tokens[-1]["suffix"] += extra_punct
                tokens[-1]["raw"] += extra_punct
    return tokens


def get_cloze_css() -> str:
    """Returns CSS styles for Cherokee sentence cloze flashcards with light & dark mode."""
    return """/* Cherokee Anki Card Styles */
@font-face {
    font-family: 'Noto Sans Cherokee';
    src: url('_NotoSansCherokee-Regular.ttf');
}

.card {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans Cherokee", Helvetica, Arial, sans-serif;
    font-size: 16px;
    text-align: center;
    color: #1a202c;
    background-color: #ffffff;
    line-height: 1.5;
    padding: 16px;
}

.cloze-container {
    max-width: 620px;
    margin: 0 auto;
    text-align: center;
}

.cloze-sentence-syll {
    font-family: 'Noto Sans Cherokee', sans-serif;
    font-size: 1.8em;
    line-height: 1.6;
    color: #1a202c;
    margin-bottom: 12px;
}

.cloze-sentence-phon {
    font-size: 1.25em;
    color: #4a5568;
    line-height: 1.5;
    margin-bottom: 16px;
}

.cloze-blank {
    display: inline-block;
    background-color: #fef3c7;
    border-bottom: 3px solid #d97706;
    color: #92400e;
    font-weight: bold;
    padding: 0 8px;
    border-radius: 4px;
    min-width: 50px;
}

.cloze-target {
    display: inline-block;
    background-color: #d1fae5;
    border-bottom: 3px solid #059669;
    color: #065f46;
    font-weight: bold;
    padding: 0 6px;
    border-radius: 4px;
}

.cloze-english {
    font-size: 1.15em;
    color: #2b6cb0;
    font-weight: 500;
    margin-top: 14px;
    padding-top: 12px;
    border-top: 1px dashed #e2e8f0;
}

.cloze-answer-box {
    background: #f7fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 14px 16px;
    margin: 12px 0 16px 0;
    text-align: center;
}

.cloze-answer-label {
    font-size: 0.8em;
    color: #718096;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}

.cloze-answer-syll {
    font-family: 'Noto Sans Cherokee', sans-serif;
    font-size: 2.1em;
    font-weight: bold;
    color: #2c5282;
    margin-bottom: 2px;
}

.cloze-answer-phon {
    font-size: 1.25em;
    color: #4a5568;
    font-weight: 500;
}

hr#answer {
    border: 0;
    height: 1px;
    background: #e2e8f0;
    margin: 16px 0;
}

.cloze-audio-container {
    margin-top: 14px;
}

/* ==========================================================================
   Dark Mode / Night Mode Support for Anki
   ========================================================================== */
.nightMode.card,
.night_mode .card,
body.nightMode .card,
body.night_mode .card {
    background-color: #20262e;
    color: #e2e8f0;
}

.nightMode .cloze-sentence-syll,
.night_mode .cloze-sentence-syll,
body.nightMode .cloze-sentence-syll,
body.night_mode .cloze-sentence-syll {
    color: #f7fafc;
}

.nightMode .cloze-sentence-phon,
.night_mode .cloze-sentence-phon,
body.nightMode .cloze-sentence-phon,
body.night_mode .cloze-sentence-phon {
    color: #cbd5e0;
}

.nightMode .cloze-blank,
.night_mode .cloze-blank,
body.nightMode .cloze-blank,
body.night_mode .cloze-blank {
    background-color: #78350f;
    border-bottom: 3px solid #f59e0b;
    color: #fef3c7;
}

.nightMode .cloze-target,
.night_mode .cloze-target,
body.nightMode .cloze-target,
body.night_mode .cloze-target {
    background-color: #064e3b;
    border-bottom: 3px solid #34d399;
    color: #a7f3d0;
}

.nightMode .cloze-english,
.night_mode .cloze-english,
body.nightMode .cloze-english,
body.night_mode .cloze-english {
    color: #90cdf4;
    border-top: 1px dashed #4a5568;
}

.nightMode .cloze-answer-box,
.night_mode .cloze-answer-box,
body.nightMode .cloze-answer-box,
body.night_mode .cloze-answer-box {
    background: #2d3748;
    border: 1px solid #4a5568;
}

.nightMode .cloze-answer-label,
.night_mode .cloze-answer-label,
body.nightMode .cloze-answer-label,
body.night_mode .cloze-answer-label {
    color: #a0aec0;
}

.nightMode .cloze-answer-syll,
.night_mode .cloze-answer-syll,
body.nightMode .cloze-answer-syll,
body.night_mode .cloze-answer-syll {
    color: #63b3ed;
}

.nightMode .cloze-answer-phon,
.night_mode .cloze-answer-phon,
body.nightMode .cloze-answer-phon,
body.night_mode .cloze-answer-phon {
    color: #e2e8f0;
}

.nightMode hr#answer,
.night_mode hr#answer,
body.nightMode hr#answer,
body.night_mode hr#answer {
    background: #4a5568;
}

@media (prefers-color-scheme: dark) {
    .card {
        background-color: #20262e;
        color: #e2e8f0;
    }
    .cloze-sentence-syll {
        color: #f7fafc;
    }
    .cloze-sentence-phon {
        color: #cbd5e0;
    }
    .cloze-blank {
        background-color: #78350f;
        border-bottom: 3px solid #f59e0b;
        color: #fef3c7;
    }
    .cloze-target {
        background-color: #064e3b;
        border-bottom: 3px solid #34d399;
        color: #a7f3d0;
    }
    .cloze-english {
        color: #90cdf4;
        border-top: 1px dashed #4a5568;
    }
    .cloze-answer-box {
        background: #2d3748;
        border: 1px solid #4a5568;
    }
    .cloze-answer-label {
        color: #a0aec0;
    }
    .cloze-answer-syll {
        color: #63b3ed;
    }
    .cloze-answer-phon {
        color: #e2e8f0;
    }
    hr#answer {
        background: #4a5568;
    }
}
"""


CLOZE_FRONT_TEMPLATE = """<div class="cloze-container">
    <div class="cloze-sentence-syll">
        {{FrontSyllabary}}
    </div>
    
    <div class="cloze-sentence-phon">
        {{FrontPhonetics}}
    </div>
    
    <div class="cloze-english">
        {{English}}
    </div>
</div>
"""

CLOZE_BACK_TEMPLATE = """<div class="cloze-container">
    <div class="cloze-sentence-syll">
        {{BackSyllabary}}
    </div>
    
    <div class="cloze-sentence-phon">
        {{BackPhonetics}}
    </div>
    
    <div class="cloze-english">
        {{English}}
    </div>
    
    <hr id="answer">
    
    <div class="cloze-answer-box">
        <div class="cloze-answer-label">Missing Word</div>
        <div class="cloze-answer-syll">{{TargetWordSyllabary}}</div>
        {{#TargetWordPhonetics}}
        <div class="cloze-answer-phon">{{TargetWordPhonetics}}</div>
        {{/TargetWordPhonetics}}
    </div>
    
    {{#Audio}}
    <div class="cloze-audio-container">
        {{Audio}}
    </div>
    {{/Audio}}
</div>
"""


def get_cloze_model() -> genanki.Model:
    """Creates the Cherokee Sentence Cloze note model."""
    return genanki.Model(
        CLOZE_MODEL_ID,
        CLOZE_MODEL_NAME,
        fields=[
            {"name": "Id"},
            {"name": "Deck"},
            {"name": "SequenceOrder"},
            {"name": "EntryNo"},
            {"name": "WordIndex"},
            {"name": "TotalWords"},
            {"name": "English"},
            {"name": "FrontSyllabary"},
            {"name": "FrontPhonetics"},
            {"name": "TargetWordSyllabary"},
            {"name": "TargetWordPhonetics"},
            {"name": "BackSyllabary"},
            {"name": "BackPhonetics"},
            {"name": "Audio"},
        ],
        templates=[
            {
                "name": "Cherokee Cloze (Fill-in-the-Blank)",
                "qfmt": CLOZE_FRONT_TEMPLATE,
                "afmt": CLOZE_BACK_TEMPLATE,
            }
        ],
        css=get_cloze_css(),
    )


def generate_cloze_cards(
    official_data_csv: str,
    sentence_audio_dir: str,
    output_dir: str,
    font_path: str | None = None,
    seed: int = 42,
) -> list[ClozeCard]:
    """
    Generates sentence cloze cards for every word in all dictionary sentences.
    Phonetics have tone diacritics and length colons stripped for clean display.
    Cards are randomized across sentences and vocabulary with a deterministic seed.
    Exports cloze_sentences.csv and cloze_sentences.apkg to output_dir.
    """
    if not os.path.exists(official_data_csv):
        print(f"Warning: officialdata.csv not found at {official_data_csv}")
        return []

    # Map available sentence audio files
    audio_files_on_disk: dict[str, str] = {}
    if os.path.exists(sentence_audio_dir):
        for f in os.listdir(sentence_audio_dir):
            if f.endswith(".m4a") or f.endswith(".mp3"):
                audio_files_on_disk[f] = os.path.join(sentence_audio_dir, f)

    # Load unique sentences from CSV
    sentences: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    with open(official_data_csv, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for num in ["1", "2", "3"]:
                syll = row.get(f"Sentence-{num} SYLL", "").strip()
                phon = row.get(f"Sentence-{num} PHON", "").strip()
                engl = row.get(f"Sentence-{num} ENGL", "").strip()
                audio = row.get(f"Sentence {num} audio", "").strip()
                entry_no = (
                    row.get("Entry No.")
                    or row.get("﻿Entry No.")
                    or row.get("No.")
                    or ""
                ).strip()

                if (syll or phon or engl) and (syll, engl) not in seen:
                    seen.add((syll, engl))

                    if entry_no in SENTENCE_CLEANUPS:
                        fix_s, fix_p = SENTENCE_CLEANUPS[entry_no]
                        syll = fix_s
                        phon = fix_p

                    # Strip tone diacritics and length colons from phonetics
                    clean_phon = remove_tone_and_length(phon)

                    sentences.append(
                        {
                            "entry_no": entry_no,
                            "num": num,
                            "syll": syll,
                            "phon": clean_phon,
                            "engl": engl,
                            "audio": audio if audio in audio_files_on_disk else "",
                        }
                    )

    print(f"Loaded {len(sentences)} unique sentences from {official_data_csv}")

    model = get_cloze_model()
    deck_id = make_anki_id(CLOZE_DECK_NAME)
    deck = genanki.Deck(deck_id, CLOZE_DECK_NAME)

    cards: list[ClozeCard] = []
    used_audio_files: set[str] = set()

    for s in sentences:
        syll_tokens = tokenize_cherokee(s["syll"])
        phon_tokens = tokenize_cherokee(s["phon"])

        if not syll_tokens and not phon_tokens:
            continue

        num_words = len(syll_tokens) if syll_tokens else len(phon_tokens)

        for w_idx in range(num_words):
            # Format Syllabary front and back
            if syll_tokens and w_idx < len(syll_tokens):
                target_syll = syll_tokens[w_idx]["word"]
                front_syll_parts: list[str] = []
                back_syll_parts: list[str] = []
                for i, tok in enumerate(syll_tokens):
                    if i == w_idx:
                        front_syll_parts.append(
                            f"{tok['prefix']}<span class='cloze-blank'>______</span>{tok['suffix']}"
                        )
                        back_syll_parts.append(
                            f"{tok['prefix']}<span class='cloze-target'>{tok['word']}</span>{tok['suffix']}"
                        )
                    else:
                        front_syll_parts.append(
                            f"{tok['prefix']}{tok['word']}{tok['suffix']}"
                        )
                        back_syll_parts.append(
                            f"{tok['prefix']}{tok['word']}{tok['suffix']}"
                        )
                front_syll = " ".join(front_syll_parts)
                back_syll = " ".join(back_syll_parts)
            else:
                target_syll = ""
                front_syll = ""
                back_syll = ""

            # Format Phonetics front and back
            if phon_tokens and w_idx < len(phon_tokens):
                target_phon = phon_tokens[w_idx]["word"]
                front_phon_parts: list[str] = []
                back_phon_parts: list[str] = []
                for i, tok in enumerate(phon_tokens):
                    if i == w_idx:
                        front_phon_parts.append(
                            f"{tok['prefix']}<span class='cloze-blank'>______</span>{tok['suffix']}"
                        )
                        back_phon_parts.append(
                            f"{tok['prefix']}<span class='cloze-target'>{tok['word']}</span>{tok['suffix']}"
                        )
                    else:
                        front_phon_parts.append(
                            f"{tok['prefix']}{tok['word']}{tok['suffix']}"
                        )
                        back_phon_parts.append(
                            f"{tok['prefix']}{tok['word']}{tok['suffix']}"
                        )
                front_phon = " ".join(front_phon_parts)
                back_phon = " ".join(back_phon_parts)
            else:
                target_phon = ""
                front_phon = ""
                back_phon = ""

            clean_engl = clean_asterisks(s["engl"])
            audio_str = f"[sound:{s['audio']}]" if s["audio"] else ""
            if s["audio"] and s["audio"] in audio_files_on_disk:
                used_audio_files.add(audio_files_on_disk[s["audio"]])

            card_id = f"cloze_{s['entry_no']}_s{s['num']}_w{w_idx+1}"
            entry_tag = (
                f"entry_{s['entry_no'].split('.')[0]}"
                if s["entry_no"]
                else "entry_unknown"
            )
            tags = ["cloze", "sentence", entry_tag]

            card = ClozeCard(
                card_id=card_id,
                deck=CLOZE_DECK_NAME,
                sequence_order=0,  # Will be assigned after deterministic randomization
                entry_no=s["entry_no"],
                word_index=w_idx + 1,
                total_words=num_words,
                english=clean_engl,
                front_syllabary=front_syll,
                front_phonetics=front_phon,
                target_word_syllabary=target_syll,
                target_word_phonetics=target_phon,
                back_syllabary=back_syll,
                back_phonetics=back_phon,
                audio=audio_str,
                tags=tags,
            )
            cards.append(card)

    # Sort deterministically by card_id before shuffling with seed
    cards.sort(key=lambda c: c.card_id)
    rng = random.Random(seed)
    rng.shuffle(cards)

    # Re-assign sequential sequence_order / due numbers to the shuffled cards
    for idx, card in enumerate(cards, start=1):
        card.sequence_order = idx
        deck.add_note(card.to_genanki_note(model))

    os.makedirs(output_dir, exist_ok=True)

    # 1. Export CSV
    csv_path = os.path.join(output_dir, "cloze_sentences.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ClozeCard.get_csv_fieldnames())
        writer.writeheader()
        for card in cards:
            writer.writerow(card.to_csv_row())
    print(f"Exported {len(cards)} deterministically randomized cloze cards (seed={seed}) to {csv_path}")

    # 2. Export HTML Templates
    front_template_path = os.path.join(output_dir, "cloze_front.html")
    with open(front_template_path, "w", encoding="utf-8") as f:
        f.write(CLOZE_FRONT_TEMPLATE)

    back_template_path = os.path.join(output_dir, "cloze_back.html")
    with open(back_template_path, "w", encoding="utf-8") as f:
        f.write(CLOZE_BACK_TEMPLATE)

    # 3. Export APKG package with embedded audio and font
    media_files: list[str] = list(used_audio_files)
    if font_path and os.path.exists(font_path):
        tmp_font = os.path.join(
            tempfile.gettempdir(), "_NotoSansCherokee-Regular.ttf"
        )
        with open(font_path, "rb") as f_in, open(tmp_font, "wb") as f_out:
            f_out.write(f_in.read())
        media_files.append(tmp_font)

    apkg_path = os.path.join(output_dir, "cloze_sentences.apkg")
    pkg = genanki.Package(deck)
    pkg.media_files = media_files
    pkg.write_to_file(apkg_path)
    print(
        f"Exported {len(cards)} cloze cards with {len(media_files)} media files to {apkg_path}"
    )

    return cards
