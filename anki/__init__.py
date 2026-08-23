"""
Anki flashcard generation for Cherokee Root Dictionary.
"""

from anki.cloze_generator import generate_cloze_cards
from anki.english_inflector import inflect_english_definition
from anki.generator import generate_anki_cards
from anki.models import AnkiCard, ClozeCard

__all__ = [
    "AnkiCard",
    "ClozeCard",
    "generate_anki_cards",
    "generate_cloze_cards",
    "inflect_english_definition",
]