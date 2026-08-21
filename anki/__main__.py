"""
CLI entry point for generating Cherokee Anki flashcards.

Usage:
    python -m anki [--initial-batch 5] [--interleave-batch 3] [--lag 25] [--sample-min 1] [--sample-max 2] [--filter-tag filtered]
"""

from __future__ import annotations

import argparse
import sys

from anki.generator import generate_anki_cards


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Anki flashcards for Cherokee Root Dictionary."
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

    args = parser.parse_args()

    print("=" * 60)
    print(" Cherokee Anki Flashcard Generator")
    print("=" * 60)
    print(
        f"Settings: initial_batch={args.initial_batch},"
        f" interleave_batch={args.interleave_batch}, lag={args.lag},"
        f" sample_range=[{args.sample_min}, {args.sample_max}],"
        f" filter_tag='{args.filter_tag}', seed={args.seed}"
    )

    results = generate_anki_cards(
        initial_batch_size=args.initial_batch,
        interleave_batch_size=args.interleave_batch,
        practice_lag_cards=args.lag,
        sample_practice_min=args.sample_min,
        sample_practice_max=args.sample_max,
        filter_tag=args.filter_tag,
        seed=args.seed,
    )

    print("=" * 60)
    print(" Generation Summary:")
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
    print("=" * 60)
    print("Artifacts (.apkg and .csv) written to artifacts/anki/")


if __name__ == "__main__":
    main()
