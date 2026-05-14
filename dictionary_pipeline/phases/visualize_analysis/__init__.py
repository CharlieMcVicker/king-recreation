import argparse
import json
import os
import shutil
from typing import Any, cast

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def _plot_class_distribution(
    df: pd.DataFrame,
    value_vars: list[str],
    output_prefix: str,
    sort_by: str | None = None,
) -> None:
    # Filter for existing columns to avoid errors if some are missing
    value_vars = [v for v in value_vars if v in df.columns]

    df_melted = df.melt(
        id_vars="class",
        value_vars=value_vars,
        var_name="Match Type",
        value_name="Count",
    )

    # Determine full class order
    if sort_by and sort_by in df.columns:
        full_class_order = df.sort_values(by=sort_by, ascending=False)["class"].tolist()
    else:
        # Default: Sort by sum of displayed variables
        full_class_order = (
            df.set_index("class")[value_vars]
            .sum(axis=1)
            .sort_values(ascending=False)
            .index.tolist()
        )

    def create_plot(data: pd.DataFrame, suffix: str) -> None:
        # Filter order to only include classes present in the data
        present_classes = set(data["class"].unique())
        class_order = [c for c in full_class_order if c in present_classes]

        plt.figure(figsize=(12, 8))
        sns.barplot(
            data=cast(Any, data),
            x="class",
            y="Count",
            hue="Match Type",
            order=class_order,
        )
        plt.title(f"Verb Matches per Class ({suffix})")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(f"{output_prefix}_{suffix.lower()}.png")
        plt.close()

    # Full version
    create_plot(df_melted, "Full")

    # Filtered version (only classes with at least one match in any category)
    active_classes = df[(df[value_vars] > 0).any(axis=1)]["class"]
    df_filtered = df_melted[df_melted["class"].isin(cast(Any, active_classes))]
    if not df_filtered.empty:
        create_plot(cast(pd.DataFrame, df_filtered), "Filtered")


def plot_class_distribution(csv_path: str, output_prefix: str) -> None:
    """Generates a bar chart showing verbs matched by each class."""
    if not os.path.exists(csv_path):
        print(f"Warning: {csv_path} not found. Skipping class distribution plot.")
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    plots = [
        (
            "all",
            [
                "full",
                "reconstructs",
            ],
            "reconstructs",  # Sort by reconstructions
        ),
        ("reconstructs", ["reconstructs"], None),
    ]

    for prefix, vals, sort_col in plots:
        _plot_class_distribution(
            df, vals, output_prefix + "_" + prefix, sort_by=sort_col
        )


def plot_verb_coverage(json_path: str, output_path: str) -> None:
    """Generates a figure with two subplots: Match Counts and Coverage %."""
    if not os.path.exists(json_path):
        print(f"Warning: {json_path} not found. Skipping verb coverage plot.")
        return

    with open(json_path, "r") as f:
        data = json.load(f)

    # Convert to DataFrames
    count_rows = []
    pct_rows = []

    combinations = sorted(data.keys())

    for combo in combinations:
        counts = data[combo]
        for cat, val in counts.items():
            if cat == "coverage_pct":
                pct_rows.append({"Combination": combo, "Coverage": val})
            else:
                count_rows.append(
                    {"Combination": combo, "Match Count": cat, "Count": val}
                )

    df_counts = pd.DataFrame(count_rows)
    df_pct = pd.DataFrame(pct_rows)

    # Create two subplots: Left for counts, Right for percentage
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [2, 1]}
    )

    # 1. Match Counts (Grouped Bar Chart)
    sns.barplot(
        data=cast(Any, df_counts),
        x="Combination",
        y="Count",
        hue="Match Count",
        ax=ax1,
        palette="viridis",
        order=combinations,
    )
    ax1.set_title("Match Count Distribution")
    ax1.set_xlabel("Combination Strategy")
    ax1.set_ylabel("Count")
    ax1.tick_params(axis="x", rotation=15)
    ax1.legend(title="Matches per Verb")

    # 2. Coverage Percentage (Bar Chart)
    sns.barplot(
        data=cast(Any, df_pct),
        x="Combination",
        y="Coverage",
        ax=ax2,
        color="skyblue",
        order=combinations,
    )
    ax2.set_title("Coverage Percentage")
    ax2.set_xlabel("Combination Strategy")
    ax2.set_ylabel("Coverage (%)")
    ax2.set_ylim(0, 100)
    ax2.tick_params(axis="x", rotation=15)

    # Add text labels on the percentage bars
    for i, row in df_pct.iterrows():
        # Find the x-position for this combination
        # Since 'order=combinations', i corresponds to the x-tick
        ax2.text(
            float(cast(Any, i)),
            float(cast(Any, row["Coverage"])) + 1,
            f"{row['Coverage']:.1f}%",
            ha="center",
            color="black",
        )

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_near_miss_heatmap(csv_path: str, output_prefix: str) -> None:
    """Generates a heatmap of pass rates for stem-final checks."""
    if not os.path.exists(csv_path):
        print(f"Warning: {csv_path} not found. Skipping near-miss heatmap.")
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    rate_cols = [c for c in df.columns if c.endswith("_rate")]

    def create_heatmap(data: pd.DataFrame, filtered: bool) -> None:
        subset = data.copy()

        if filtered:
            subset = subset[subset["match_count"] > 0]
            filter_suffix = "filtered"
            title_suffix = "(Filtered)"
        else:
            filter_suffix = "full"
            title_suffix = "(Full)"

        # Set index to class + count for labeling
        subset["label"] = (
            subset["class"] + " (" + subset["match_count"].astype(str) + ")"
        )
        subset = subset.set_index("label")[rate_cols]

        # Shorten column names for the plot
        subset.columns = [c.replace("_rate", "") for c in subset.columns]

        # Calculate dynamic height
        height = min(20, len(subset) * 0.4 + 2)
        plt.figure(figsize=(12, height))

        sns.heatmap(subset, annot=True, cmap="YlGnBu", vmin=0, vmax=1)
        plt.title(f"Stem-Final Pass Rates {title_suffix}")
        plt.tight_layout()

        output_filename = f"{output_prefix}_{filter_suffix}.png"
        plt.savefig(output_filename)
        plt.close()

    # Generate 4 variations
    for filter_zeros in [True, False]:
        create_heatmap(df, filter_zeros)


def plot_root_ambiguity_histogram(csv_path: str, output_path: str) -> None:
    """Generates a histogram of root ambiguity counts."""
    if not os.path.exists(csv_path):
        print(f"Warning: {csv_path} not found. Skipping root ambiguity histogram.")
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    # Count frequencies of each 'count' value (number of verbs per root pair)
    # df['count'] is the number of verbs sharing a root pair
    # We want to show how many root pairs have 1 verb, 2 verbs, etc.
    counts = (
        df["count"].value_counts().sort_index().reset_index(name="Number of Root Pairs")
    )
    counts.rename(columns={"count": "Verbs per Root"}, inplace=True)

    plt.figure(figsize=(10, 6))
    sns.barplot(
        data=cast(Any, counts),
        x="Verbs per Root",
        y="Number of Root Pairs",
        color="skyblue",
    )

    plt.title("Root Ambiguity Histogram")
    plt.xlabel("Number of Verbs Sharing a Root Pair")
    plt.ylabel("Frequency (Number of Root Pairs)")

    for index, row in counts.iterrows():
        plt.text(
            cast(float, index),
            float(cast(Any, row["Number of Root Pairs"])),
            str(row["Number of Root Pairs"]),
            color="black",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_class_match_histogram(csv_path: str, output_path: str) -> None:
    """Generates a histogram showing distribution of class sizes (by match count)."""
    if not os.path.exists(csv_path):
        print(f"Warning: {csv_path} not found. Skipping class match histogram.")
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    metric = "reconstructs"
    if metric not in df.columns:
        print(f"Column {metric} not found in {csv_path}")
        return

    # Create programmatic buckets
    # We'll use a few fixed ranges or log-ish ranges if the spread is high,
    # but for this data (max ~50-80), linear buckets of 10 usually work well.
    max_val = df[metric].max()
    if max_val <= 10:
        bins = list(range(max_val + 2))
    else:
        # Create bins of size 10 up to max
        bins = list(range(0, int(max_val) + 20, 10))

    # Bin the data
    df["bucket"] = pd.cut(df[metric], bins=bins, right=False)

    # Calculate counts per bucket
    bucket_counts = df["bucket"].value_counts().sort_index().reset_index()
    bucket_counts.columns = ["Bucket", "Class Count"]

    # Convert bucket intervals to strings for labeling
    bucket_counts["Bucket"] = bucket_counts["Bucket"].astype(str)

    plt.figure(figsize=(10, 6))

    # Use barplot for spacing (shrink/width control)
    sns.barplot(
        data=cast(Any, bucket_counts),
        x="Bucket",
        y="Class Count",
        color="skyblue",
        edgecolor="navy",
        alpha=0.8,
    )

    # Add spacing between bars (matplotlib adjustment)
    # Seaborn barplot uses internal spacing, but we can adjust width if needed.
    # By default bars have some spacing.

    plt.title("Distribution of Class Propensity")
    plt.xlabel("Number of Verbs Using Class")
    plt.ylabel("Number of Classes")
    plt.xticks(rotation=45)

    # Add count labels on top of bars
    for i, count in enumerate(bucket_counts["Class Count"]):
        plt.text(
            i, count + 0.1, str(count), ha="center", va="bottom", fontweight="bold"
        )

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_macro_variants(json_path: str, output_dir: str) -> None:
    """Generates a bar chart for each macro class showing variant frequency."""
    if not os.path.exists(json_path):
        print(f"Warning: {json_path} not found. Skipping macro variant plots.")
        return

    with open(json_path, "r") as f:
        data = json.load(f)

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    for macro_name, stats in data.items():
        if stats["total_matches"] == 0:
            continue

        # Skip macros that specify no variants (only 1 option for every slot)
        if all(count == 1 for count in stats["available_options"].values()):
            continue

        combinations = stats["combinations"]
        if not combinations:
            continue

        # Convert Counter to DataFrame
        df_variants = pd.DataFrame(
            list(combinations.items()), columns=cast(Any, ["Variant", "Count"])
        )
        df_variants = df_variants.sort_values(by="Count", ascending=False)

        plt.figure(figsize=(10, 6))
        sns.barplot(
            data=cast(Any, df_variants),
            x="Variant",
            y="Count",
            hue="Variant",
            palette="magma",
            legend=False,
        )

        plt.title(f"Variant Combinations Frequency: {macro_name}")
        plt.xlabel("Expanded Variant Pattern")
        plt.ylabel("Usage Count")
        plt.xticks(rotation=45, ha="right")

        # Add counts on top
        for i, count in enumerate(df_variants["Count"]):
            plt.text(i, count + 0.1, str(count), ha="center", va="bottom")

        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"{macro_name}_variants.png"))
        plt.close()


def plot_variant_match_histograms(csv_path: str, output_dir: str) -> None:
    """Generates histograms for variant match statistics."""
    if not os.path.exists(csv_path):
        print(f"Warning: {csv_path} not found. Skipping variant match histograms.")
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    # Filter out macro patterns with no subvariants
    if "can_have_variants" in df.columns:
        df = df[df["can_have_variants"] == True]

    if df.empty:
        print(
            f"Warning: No variadic macros found in {csv_path}. Skipping variant histograms."
        )
        return

    os.makedirs(output_dir, exist_ok=True)

    # 1. Histogram of Total Match Counts (Absolute)
    plt.figure(figsize=(10, 6))
    sns.histplot(
        cast(Any, df["match_count"]),
        kde=False,
        bins=30,
        color="skyblue",
        edgecolor="black",
    )
    plt.title("Distribution of Variant Match Counts (Absolute)")
    plt.xlabel("Number of Verbs Matched per Variant")
    plt.ylabel("Number of Variants")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "variant_match_histogram_counts.png"))
    plt.close()

    # 2. Histogram of Match Percentages
    plt.figure(figsize=(10, 6))
    sns.histplot(
        cast(Any, df["match_percent"]),
        kde=False,
        bins=20,
        color="salmon",
        edgecolor="black",
    )
    plt.title("Distribution of Variant Match Percentages")
    plt.xlabel("Percentage of Class Matches")
    plt.ylabel("Number of Variants")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "variant_match_histogram_percent.png"))
    plt.close()

    # 3. Histogram of Average Variant Match Count per Class
    # Group by class and calculate mean match count
    class_averages = cast(
        Any, df.groupby("macro_class")["match_count"].mean()
    ).reset_index(name="avg_matches")

    plt.figure(figsize=(10, 6))
    sns.histplot(
        cast(Any, class_averages["avg_matches"]),
        kde=False,
        bins=20,
        color="lightgreen",
        edgecolor="black",
    )
    plt.title("Distribution of Average Variant Match Counts per Class")
    plt.xlabel("Average Matches per Variant (by Class)")
    plt.ylabel("Number of Macro Classes")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "variant_match_histogram_class_averages.png"))
    plt.close()


def plot_variation_match_histograms(csv_path: str, output_dir: str) -> None:
    """Generates histograms for variation match statistics."""
    if not os.path.exists(csv_path):
        print(f"Warning: {csv_path} not found. Skipping variation match histograms.")
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    # Filter out macro patterns with no subvariants
    if "can_have_variants" in df.columns:
        df = df[df["can_have_variants"] == True]

    if df.empty:
        print(
            f"Warning: No variadic macros found in {csv_path}. Skipping variation histograms."
        )
        return

    os.makedirs(output_dir, exist_ok=True)

    # 1. Histogram of Total Match Counts (Absolute)
    plt.figure(figsize=(10, 6))
    sns.histplot(
        cast(Any, df["match_count"]),
        kde=False,
        bins=30,
        color="skyblue",
        edgecolor="black",
    )
    plt.title("Distribution of Variation Match Counts (Absolute)")
    plt.xlabel("Number of Verbs Matched per Variation")
    plt.ylabel("Number of Variations")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "variation_match_histogram_counts.png"))
    plt.close()

    # 2. Histogram of Match Percentages
    plt.figure(figsize=(10, 6))
    sns.histplot(
        cast(Any, df["match_percent"]),
        kde=False,
        bins=20,
        color="salmon",
        edgecolor="black",
    )
    plt.title("Distribution of Variation Match Percentages")
    plt.xlabel("Percentage of Class Matches")
    plt.ylabel("Number of Variations")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "variation_match_histogram_percent.png"))
    plt.close()

    # 3. Histogram of Average Variation Match Count per Class
    # Group by class and calculate mean match count
    class_averages = cast(
        Any, df.groupby("macro_class")["match_count"].mean()
    ).reset_index(name="avg_matches")

    plt.figure(figsize=(10, 6))
    sns.histplot(
        cast(Any, class_averages["avg_matches"]),
        kde=False,
        bins=20,
        color="lightgreen",
        edgecolor="black",
    )
    plt.title("Distribution of Average Variation Match Counts per Class")
    plt.xlabel("Average Matches per Variation (by Class)")
    plt.ylabel("Number of Macro Classes")
    plt.tight_layout()
    plt.savefig(
        os.path.join(output_dir, "variation_match_histogram_class_averages.png")
    )
    plt.close()


def plot_class_sequence_counts(csv_path: str, output_path: str) -> None:
    """Generates a histogram of how many unique surface sequences each class has."""
    if not os.path.exists(csv_path):
        print(f"Warning: {csv_path} not found. Skipping class sequence counts plot.")
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    # Count rows per class
    sequence_counts = cast(Any, df.groupby("class").size()).reset_index(
        name="Sequence Count"
    )

    plt.figure(figsize=(10, 6))
    # histogram of the counts
    sns.histplot(
        cast(Any, sequence_counts["Sequence Count"]),
        kde=False,
        bins=range(1, int(sequence_counts["Sequence Count"].max()) + 2),
        color="skyblue",
        edgecolor="navy",
    )

    plt.title("Distribution of Surface Sequences per Class")
    plt.xlabel("Number of Unique Surface Sequences")
    plt.ylabel("Number of Classes")

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_sequence_match_percentage(csv_path: str, output_path: str) -> None:
    """Generates a histogram of what percentage of a class's matches each sequence makes up."""
    if not os.path.exists(csv_path):
        print(
            f"Warning: {csv_path} not found. Skipping sequence match percentage plot."
        )
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    # Calculate total count per class
    class_totals = df.groupby("class")["count"].transform("sum")
    df["percentage"] = (df["count"] / class_totals) * 100

    plt.figure(figsize=(10, 6))
    sns.histplot(
        cast(Any, df["percentage"]),
        kde=False,
        bins=20,
        color="salmon",
        edgecolor="brown",
    )

    plt.title("Distribution of Sequence Match Percentages")
    plt.xlabel("Percentage of Class Matches (%)")
    plt.ylabel("Number of Sequences")

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


from dictionary_pipeline.phases.visualize_analysis.artifacts import (
    get_class_ending_profiles_path,
    get_class_match_counts_path,
    get_class_near_misses_path,
    get_macro_variant_data_path,
    get_root_ambiguity_counts_path,
    get_variant_match_counts_path,
    get_variation_match_counts_path,
    get_verb_coverage_path,
    get_visualizations_dir,
)


def visualize_all() -> None:
    """
    Generate visualizations of data from pipeline runs.

    Inputs:
    * CLASS_ENDING_PROFILES_CSV_PATH
    * CLASS_MATCH_COUNTS_PATH
    * CLASS_NEAR_MISSES_PATH
    * MACRO_VARIANT_DATA_PATH
    * ROOT_AMBIGUITY_COUNTS_PATH
    * VARIANT_MATCH_COUNTS_PATH
    * VARIATION_MATCH_COUNTS_PATH
    * VERB_COVERAGE_PATH

    Outputs:
    * VISUALIZATIONS_PATH: many visualizations
    """

    # Plots (images) go to visualizations
    output_dir = get_visualizations_dir()

    print("Generating Class Distribution plots...")
    plot_class_distribution(
        get_class_match_counts_path(),
        os.path.join(output_dir, "class_distribution"),
    )

    print("Generating Verb Coverage plot...")
    plot_verb_coverage(
        get_verb_coverage_path(),
        os.path.join(output_dir, "verb_coverage.png"),
    )

    print("Generating Near-Miss Heatmap plots...")
    plot_near_miss_heatmap(
        get_class_near_misses_path(),
        os.path.join(output_dir, "near_miss_heatmap"),
    )

    print("Generating Root Ambiguity Histogram...")
    plot_root_ambiguity_histogram(
        get_root_ambiguity_counts_path(),
        os.path.join(output_dir, "root_ambiguity_histogram.png"),
    )

    print("Generating Class Match Histogram...")
    plot_class_match_histogram(
        get_class_match_counts_path(),
        os.path.join(output_dir, "class_match_histogram.png"),
    )

    print("Generating Macro Variant plots...")
    plot_macro_variants(
        get_macro_variant_data_path(),
        os.path.join(output_dir, "macro_variants"),
    )

    print("Generating Variant Match Histograms...")
    plot_variant_match_histograms(
        get_variant_match_counts_path(),
        os.path.join(output_dir, "variant_match_histograms"),
    )

    print("Generating Variation Match Histograms...")
    plot_variation_match_histograms(
        get_variation_match_counts_path(),
        os.path.join(output_dir, "variation_match_histograms"),
    )

    print("Generating Class Ending Profile plots...")
    plot_class_sequence_counts(
        get_class_ending_profiles_path(),
        os.path.join(output_dir, "class_sequence_counts_histogram.png"),
    )
    plot_sequence_match_percentage(
        get_class_ending_profiles_path(),
        os.path.join(output_dir, "sequence_match_percentage_histogram.png"),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate visualizations for match data."
    )
    # The user said "no need to add a flag to the cli" for --hide-clutter,
    # they want both generated by default.
    args = parser.parse_args()

    visualize_all()
    print(f"Visualizations saved.")
