"""
Card sequencing and interleaving logic for Cherokee Anki flashcards.
"""

from __future__ import annotations

from typing import Any

from anki.models import AnkiCard
from dictionary_pipeline.dictionary_forms import DictionaryVerb
from tex_dictionary.companion_data import AspectClass


class AnkiSequencer:
    """
    Implements intelligent spaced interleaving:
    1. Introduces class mascot verb tense cards first.
    2. Introduces the first batch (4-6) of member verb root cards.
    3. Moves to the next class mascot and initial batch.
    4. Interleaves subsequent batches of root cards across all active classes.
    5. Paces practice test cards strictly after the corresponding root card.
    """

    def __init__(
        self,
        initial_batch_size: int = 5,
        interleave_batch_size: int = 3,
        practice_lag_cards: int = 25,
    ) -> None:
        self.initial_batch_size = initial_batch_size
        self.interleave_batch_size = interleave_batch_size
        self.practice_lag_cards = practice_lag_cards

    def sequence_cards(
        self,
        ordered_class_names: list[str],
        class_member_verbs: dict[str, list[DictionaryVerb]],
        mascot_cards_by_class: dict[str, list[AnkiCard]],
        root_cards_by_verb_id: dict[str, AnkiCard],
        practice_cards_by_verb_id: dict[str, list[AnkiCard]],
    ) -> tuple[
        list[AnkiCard],
        list[AnkiCard],
        list[AnkiCard],
        list[AnkiCard],
        list[AnkiCard],
    ]:
        """
        Returns:
            all_interleaved_cards: Unified list sorted by SequenceOrder.
            mascots_and_roots_cards: Main study deck (Type 1 + Type 2).
            mascot_cards: Type 1 cards.
            root_cards: Type 2 cards.
            practice_cards: Type 3 cards (ordered to match learning progression).
        """
        main_deck: list[AnkiCard] = []
        verb_intro_order: list[str] = (
            []
        )  # verb_ids in order of root card introduction

        # Partition non-mascot verbs for each class into chunks
        class_chunks: dict[str, list[list[DictionaryVerb]]] = {}
        for c_name in ordered_class_names:
            verbs = class_member_verbs.get(c_name, [])
            if not verbs:
                class_chunks[c_name] = []
                continue

            chunks: list[list[DictionaryVerb]] = []
            # Chunk 0: initial batch
            chunks.append(verbs[: self.initial_batch_size])
            # Remaining chunks
            idx = self.initial_batch_size
            while idx < len(verbs):
                chunks.append(verbs[idx : idx + self.interleave_batch_size])
                idx += self.interleave_batch_size
            class_chunks[c_name] = chunks

        # Phase 1 & 2: Introduce classes and interleave roots
        active_classes: list[str] = []
        class_chunk_idx: dict[str, int] = {
            c_name: 0 for c_name in ordered_class_names
        }

        for c_name in ordered_class_names:
            chunks = class_chunks.get(c_name, [])
            m_cards = mascot_cards_by_class.get(c_name, [])

            if not chunks and not m_cards:
                continue

            # 1. Add mascot cards for this class
            main_deck.extend(m_cards)

            # 2. Add chunk 0 of root cards
            if chunks:
                for v in chunks[0]:
                    vid = str(v.corpus_id or v.definition)
                    rc = root_cards_by_verb_id.get(vid)
                    if rc:
                        main_deck.append(rc)
                        verb_intro_order.append(vid)
                class_chunk_idx[c_name] = 1

            active_classes.append(c_name)

            # 3. Interleave next batch for previously active classes
            for prev_name in active_classes[:-1]:
                p_chunks = class_chunks.get(prev_name, [])
                c_idx = class_chunk_idx[prev_name]
                if c_idx < len(p_chunks):
                    for v in p_chunks[c_idx]:
                        vid = str(v.corpus_id or v.definition)
                        rc = root_cards_by_verb_id.get(vid)
                        if rc:
                            main_deck.append(rc)
                            verb_intro_order.append(vid)
                    class_chunk_idx[prev_name] += 1

        # Drain any remaining root chunks across all classes round-robin
        remaining = True
        while remaining:
            remaining = False
            for c_name in ordered_class_names:
                chunks = class_chunks.get(c_name, [])
                c_idx = class_chunk_idx.get(c_name, 0)
                if c_idx < len(chunks):
                    remaining = True
                    for v in chunks[c_idx]:
                        vid = str(v.corpus_id or v.definition)
                        rc = root_cards_by_verb_id.get(vid)
                        if rc:
                            main_deck.append(rc)
                            verb_intro_order.append(vid)
                    class_chunk_idx[c_name] += 1

        # Assign sequence order numbers to main deck
        for seq, card in enumerate(main_deck, start=1):
            card.sequence_order = seq

        # Order practice deck cards matching the exact order verbs were introduced
        practice_deck: list[AnkiCard] = []
        p_seq = 1
        for vid in verb_intro_order:
            p_cards = practice_cards_by_verb_id.get(vid, [])
            for pc in p_cards:
                pc.sequence_order = p_seq
                practice_deck.append(pc)
                p_seq += 1

        # Also collect verbs that might not have been in member verbs
        for vid, p_cards in practice_cards_by_verb_id.items():
            if vid not in verb_intro_order:
                for pc in p_cards:
                    pc.sequence_order = p_seq
                    practice_deck.append(pc)
                    p_seq += 1

        # Create unified interleaved list (all cards with spaced practice cards)
        all_interleaved: list[AnkiCard] = []

        # Build map of verb_id -> introduction sequence in main deck
        verb_intro_seq: dict[str, int] = {}
        for card in main_deck:
            if card.card_type == "verb_root":
                verb_intro_seq[card.verb_id] = card.sequence_order

        # Create an event schedule of (target_order, card)
        schedule: list[tuple[float, AnkiCard]] = []
        for card in main_deck:
            schedule.append((float(card.sequence_order), card))

        for vid, p_cards in practice_cards_by_verb_id.items():
            intro_pos = verb_intro_seq.get(vid, len(main_deck))
            for p_idx, pc in enumerate(p_cards):
                # Schedule after intro_pos + lag
                target_pos = (
                    float(intro_pos)
                    + float(self.practice_lag_cards)
                    + (float(p_idx) * 0.1)
                )
                schedule.append((target_pos, pc))

        # Sort schedule and assign global sequence numbers
        schedule.sort(key=lambda x: x[0])
        for global_seq, (_, card) in enumerate(schedule, start=1):
            c_copy = AnkiCard(
                card_id=card.card_id,
                card_type=card.card_type,
                deck=card.deck,
                sequence_order=global_seq,
                class_name=card.class_name,
                verb_id=card.verb_id,
                definition=card.definition,
                root=card.root,
                tense=card.tense,
                front=card.front,
                back=card.back,
                extra_info=card.extra_info,
                tags=list(card.tags),
            )
            all_interleaved.append(c_copy)

        # Break down specific lists
        mascot_cards = [c for c in main_deck if c.card_type == "mascot_tense"]
        root_cards = [c for c in main_deck if c.card_type == "verb_root"]

        return (
            all_interleaved,
            main_deck,
            mascot_cards,
            root_cards,
            practice_deck,
        )
