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
