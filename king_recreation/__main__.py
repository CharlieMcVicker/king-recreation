import argparse

from king_recreation.phases.analyze_pipeline_run import analyze_pipeline_run
from king_recreation.phases.check_tone_consistency import check_tone_consistency
from king_recreation.phases.group_hierarchical import group_hierarchical
from king_recreation.phases.identify_aspect_classes import identify_aspect_classes
from king_recreation.phases.identify_derived_verbs import identify_derived_verbs
from king_recreation.phases.identify_prefixes import identify_prefixes
from king_recreation.phases.preprocess_ced import create_corpus_from_cn_dict
from king_recreation.phases.reconstruct_and_validate import reconstruct_and_validate
from king_recreation.phases.select_canonical_derivations import (
    select_canonical_derivations,
)
from king_recreation.phases.select_canonical_derivations.artifacts import (
    commit_selection_snapshot,
)
from king_recreation.phases.visualize_analysis import visualize_all


def main():
    parser = argparse.ArgumentParser(description="King Recreation Pipeline")
    parser.add_argument("--classes", help="Path to custom classes CSV file")
    parser.add_argument(
        "-d",
        "--allow-dropping",
        action="store_true",
        help="Allow user selected rows to be dropped during reconstruction validation. If not set, aborts run if rows would be dropped.",
    )
    parser.add_argument(
        "-c",
        "--commit-snapshot",
        action="store_true",
        help="Commit the selection snapshot to data/",
    )
    args = parser.parse_args()

    print("[1/10] Creating corpus from Cherokee Nation Dictionary...")
    create_corpus_from_cn_dict()

    print("\n[2/10] Identifying aspect endings")
    identify_aspect_classes(args.classes)

    print("\n[3/10] Identifying prefixes...")
    identify_prefixes()

    print("\n[4/10] Validating derivations via reconstruction...")
    reconstruct_and_validate(classes_path=args.classes, allow_drops=args.allow_dropping)

    print("\n[5/10] Selecting cannonical derivations...")
    select_canonical_derivations()

    if args.commit_snapshot:
        commit_selection_snapshot()

    print("\n[6/10] Identifying derivational suffix connections...")
    identify_derived_verbs(args.classes)

    print("\n[7/10] Grouping dictionary hierarchically...")
    group_hierarchical()

    print("\n[8/10] Checking tone consistency and generating profiles...")
    check_tone_consistency(interactive=False)

    print("\n[9/10] Analyzing pipeline run...")
    analyze_pipeline_run(args.classes)

    print("\n[10/10] Visualizing analysis...")
    visualize_all()


if __name__ == "__main__":
    main()
