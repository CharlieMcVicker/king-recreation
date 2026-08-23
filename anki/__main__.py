"""
CLI entry point for generating Cherokee Anki flashcards.

Usage:
    python -m anki [--initial-batch 5] [--interleave-batch 3] [--lag 25] [--sample-min 1] [--sample-max 2] [--filter-tag filtered]
"""

from __future__ import annotations

import argparse
import os
import sys

from anki.cloze_generator import generate_cloze_cards
from anki.generator import (
    DEFAULT_AUDIO_DIR,
    DEFAULT_CONJUGATIONS_CSV,
    DEFAULT_OFFICIAL_DATA_CSV,
    DEFAULT_SENTENCE_AUDIO_DIR,
    generate_anki_cards,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Anki flashcards for Cherokee Root Dictionary and Sentence Cloze."
    )
    parser.add_argument(
        "--initial-batch",
        type=int,
        default=5,
        help=(
            "Number of root cards to introduce per class before moving to next"
            " mascot (default: 5)"
        ),
    )
    parser.add_argument(
        "--interleave-batch",
        type=int,
        default=3,
        help=(
            "Batch size for round-robin interleaving of remaining roots"
            " (default: 3)"
        ),
    )
    parser.add_argument(
        "--lag",
        type=int,
        default=25,
        help=(
            "Lag buffer offset for scheduling practice cards behind root cards"
            " in unified deck (default: 25)"
        ),
    )
    parser.add_argument(
        "--sample-min",
        type=int,
        default=1,
        help="Minimum active practice cards to sample per verb (default: 1)",
    )
    parser.add_argument(
        "--sample-max",
        type=int,
        default=2,
        help="Maximum active practice cards to sample per verb (default: 2)",
    )
    parser.add_argument(
        "--filter-tag",
        type=str,
        default="filtered",
        help="Tag name applied to extra practice cards so they can be filtered/suspended (default: 'filtered')",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic sampling across runs (default: 42)",
    )
    parser.add_argument(
        "--conjugations-csv",
        type=str,
        default=None,
        help="Path to conjugations.csv mapping audio to entries (default: auto-detected in audiodownload/)",
    )
    parser.add_argument(
        "--audio-dir",
        type=str,
        default=None,
        help="Directory containing word audio files (default: auto-detected in audiodownload/audio_files/)",
    )
    parser.add_argument(
        "--officialdata-csv",
        type=str,
        default=None,
        help="Path to officialdata.csv containing example sentences (default: auto-detected in audiodownload/)",
    )
    parser.add_argument(
        "--sentence-audio-dir",
        type=str,
        default=None,
        help="Directory containing sentence audio files (default: auto-detected in audiodownload/sentence_audio/)",
    )
    parser.add_argument(
        "--cloze-only",
        action="store_true",
        help="Generate only the sentence cloze cards deck",
    )
    parser.add_argument(
        "--skip-cloze",
        action="store_true",
        help="Skip generating sentence cloze cards deck",
    )

    args = parser.parse_args()

    official_csv = args.officialdata_csv or DEFAULT_OFFICIAL_DATA_CSV
    sentence_audio = args.sentence_audio_dir or DEFAULT_SENTENCE_AUDIO_DIR
    output_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "artifacts", "anki")
    )
    font_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "Noto_Sans_Cherokee",
            "static",
            "NotoSansCherokee-Regular.ttf",
        )
    )

    print("=" * 60)
    print(" Cherokee Anki Flashcard Generator")
    print("=" * 60)

    # 1. Generate Aspect cards (unless --cloze-only is specified)
    if not args.cloze_only:
        print(
            f"Settings: initial_batch={args.initial_batch},"
            f" interleave_batch={args.interleave_batch}, lag={args.lag},"
            f" sample_range=[{args.sample_min}, {args.sample_max}],"
            f" filter_tag='{args.filter_tag}', seed={args.seed}"
        )

        kwargs = {
            "initial_batch_size": args.initial_batch,
            "interleave_batch_size": args.interleave_batch,
            "practice_lag_cards": args.lag,
            "sample_practice_min": args.sample_min,
            "sample_practice_max": args.sample_max,
            "filter_tag": args.filter_tag,
            "seed": args.seed,
        }
        if args.conjugations_csv:
            kwargs["conjugations_csv"] = args.conjugations_csv
        if args.audio_dir:
            kwargs["audio_dir"] = args.audio_dir
        if args.officialdata_csv:
            kwargs["official_data_csv"] = args.officialdata_csv
        if args.sentence_audio_dir:
            kwargs["sentence_audio_dir"] = args.sentence_audio_dir

        results = generate_anki_cards(**kwargs)

        word_audio_count = sum(
            1 for c in results["all_cards"] if "[sound:" in c.back
        )
        sentence_audio_count = sum(
            1 for c in results["all_cards"] if "[sound:" in c.extra_info
        )

        print("=" * 60)
        print(" Aspect Card Generation Summary:")
        print(f'  - Type 1 (Class Mascots):        {len(results["mascots"])} notes ({len(results["mascots"])*2} reversible cards)')
        print(f'  - Type 2 (Verb Roots):           {len(results["roots"])} notes ({len(results["roots"])*2} reversible cards)')
        print(
            f'  - Main Study Deck Total:         {len(results["mascots_and_roots"])}'
            f' notes ({len(results["mascots_and_roots"])*2} reversible cards)'
        )
        print(
            f'  - Type 3 (Active Sampled Tests): {len(results["practice_sampled"])}'
            f' notes ({len(results["practice_sampled"])*2} cards, untagged)'
        )
        print(
            f'  - Type 3 (Total Practice Tests): {len(results["practice"])} notes'
            f' ({len(results["practice"])*2} cards; {len(results["practice"]) - len(results["practice_sampled"])} tagged "{args.filter_tag}")'
        )
        print(
            f'  - Unified Interleaved Total:     {len(results["all_cards"])} notes'
            f' ({len(results["all_cards"])*2} reversible cards)'
        )
        print(
            f'  - Notes with Word Audio (Back):  {word_audio_count} notes'
            f' ({word_audio_count*2} reversible cards with word audio)'
        )
        print(
            f'  - Notes with Sentence Examples:  {sentence_audio_count} notes'
            f' ({sentence_audio_count*2} reversible cards with sentence audio listen buttons)'
        )

    # 2. Generate Sentence Cloze cards (unless --skip-cloze is specified)
    if not args.skip_cloze:
        print("=" * 60)
        print(" Generating Cherokee Sentence Cloze Cards...")
        print("=" * 60)
        cloze_cards = generate_cloze_cards(
            official_data_csv=official_csv,
            sentence_audio_dir=sentence_audio,
            output_dir=output_dir,
            font_path=font_path,
            seed=args.seed,
        )
        cloze_audio_count = sum(1 for c in cloze_cards if c.audio)
        print(" Cloze Generation Summary:")
        print(f"  - Total Sentence Cloze Cards:    {len(cloze_cards)} cards")
        print(
            f"  - Cards with Sentence Audio:     {cloze_audio_count}/{len(cloze_cards)}"
        )

    print("=" * 60)
    print("Artifacts (.apkg and .csv) written to artifacts/anki/")


if __name__ == "__main__":
    main()

