"""
Anki flashcard generation for Cherokee Root Dictionary.
"""

from anki.english_inflector import inflect_english_definition
from anki.generator import generate_anki_cards
from anki.models import AnkiCard

__all__ = ["AnkiCard", "generate_anki_cards", "inflect_english_definition"]