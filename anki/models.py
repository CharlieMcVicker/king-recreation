"""
Data models for Cherokee Anki cards and deck exports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnkiCard:
    card_id: str
    card_type: str  # 'mascot_tense', 'verb_root', 'practice_test'
    deck: str       # 'Cherokee Roots::Roots & Mascots' or 'Cherokee Roots::Practice'
    sequence_order: int
    class_name: str
    verb_id: str
    definition: str
    root: str
    tense: str
    front: str
    back: str
    extra_info: str
    tags: list[str] = field(default_factory=list)

    def to_csv_row(self) -> dict[str, str]:
        return {
            "Id": self.card_id,
            "CardType": self.card_type,
            "Deck": self.deck,
            "SequenceOrder": str(self.sequence_order),
            "Class": self.class_name,
            "VerbId": self.verb_id,
            "Definition": self.definition,
            "Root": self.root,
            "Tense": self.tense,
            "Front": self.front,
            "Back": self.back,
            "ExtraInfo": self.extra_info,
            "Tags": " ".join(self.tags),
        }

    @classmethod
    def get_csv_fieldnames(cls) -> list[str]:
        return [
            "Id",
            "CardType",
            "Deck",
            "SequenceOrder",
            "Class",
            "VerbId",
            "Definition",
            "Root",
            "Tense",
            "Front",
            "Back",
            "ExtraInfo",
            "Tags",
        ]

    def to_genanki_note(self, model: Any) -> Any:
        import genanki

        fields = [
            self.card_id,
            self.card_type,
            self.deck,
            str(self.sequence_order),
            self.class_name,
            self.verb_id,
            self.definition,
            self.root,
            self.tense,
            self.front,
            self.back,
            self.extra_info,
        ]
        return genanki.Note(
            model=model,
            fields=fields,
            tags=list(self.tags),
            due=self.sequence_order,
            guid=genanki.guid_for(self.card_id),
        )


@dataclass
class ClozeCard:
    card_id: str
    deck: str
    sequence_order: int
    entry_no: str
    word_index: int
    total_words: int
    english: str
    front_syllabary: str
    front_phonetics: str
    target_word_syllabary: str
    target_word_phonetics: str
    back_syllabary: str
    back_phonetics: str
    audio: str
    tags: list[str] = field(default_factory=list)

    def to_csv_row(self) -> dict[str, str]:
        return {
            "Id": self.card_id,
            "Deck": self.deck,
            "SequenceOrder": str(self.sequence_order),
            "EntryNo": self.entry_no,
            "WordIndex": str(self.word_index),
            "TotalWords": str(self.total_words),
            "English": self.english,
            "FrontSyllabary": self.front_syllabary,
            "FrontPhonetics": self.front_phonetics,
            "TargetWordSyllabary": self.target_word_syllabary,
            "TargetWordPhonetics": self.target_word_phonetics,
            "BackSyllabary": self.back_syllabary,
            "BackPhonetics": self.back_phonetics,
            "Audio": self.audio,
            "Tags": " ".join(self.tags),
        }

    @classmethod
    def get_csv_fieldnames(cls) -> list[str]:
        return [
            "Id",
            "Deck",
            "SequenceOrder",
            "EntryNo",
            "WordIndex",
            "TotalWords",
            "English",
            "FrontSyllabary",
            "FrontPhonetics",
            "TargetWordSyllabary",
            "TargetWordPhonetics",
            "BackSyllabary",
            "BackPhonetics",
            "Audio",
            "Tags",
        ]

    def to_genanki_note(self, model: Any) -> Any:
        import genanki

        fields = [
            self.card_id,
            self.deck,
            str(self.sequence_order),
            self.entry_no,
            str(self.word_index),
            str(self.total_words),
            self.english,
            self.front_syllabary,
            self.front_phonetics,
            self.target_word_syllabary,
            self.target_word_phonetics,
            self.back_syllabary,
            self.back_phonetics,
            self.audio,
        ]
        return genanki.Note(
            model=model,
            fields=fields,
            tags=list(self.tags),
            due=self.sequence_order,
            guid=genanki.guid_for(self.card_id),
        )

