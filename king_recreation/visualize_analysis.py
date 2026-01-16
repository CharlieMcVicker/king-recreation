import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
import argparse


def _plot_class_distribution(
    df, value_vars: list[str], output_prefix: str, sort_by: str = None
):
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

    def create_plot(data, suffix):
        # Filter order to only include classes present in the data
        present_classes = set(data["class"].unique())
        class_order = [c for c in full_class_order if c in present_classes]

        plt.figure(figsize=(12, 8))
        sns.barplot(
            data=data, x="class", y="Count", hue="Match Type", order=class_order
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
    df_filtered = df_melted[df_melted["class"].isin(active_classes)]
    if not df_filtered.empty:
        create_plot(df_filtered, "Filtered")


def plot_class_distribution(csv_path, output_prefix):
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
                "strict_full",
                "strict_reconstructs",
            ],
            "strict_reconstructs",  # Sort by reconstructions
        ),
        ("reconstructs", ["strict_reconstructs"], None),
    ]

    for prefix, vals, sort_col in plots:
        _plot_class_distribution(
            df, vals, output_prefix + "_" + prefix, sort_by=sort_col
        )


def plot_verb_coverage(json_path, output_path):
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
        data=df_counts,
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
        data=df_pct,
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
            i,
            row["Coverage"] + 1,
            f"{row['Coverage']:.1f}%",
            ha="center",
            color="black",
        )

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_near_miss_heatmap(csv_path, output_prefix):
    """Generates a heatmap of pass rates for stem-final checks."""
    if not os.path.exists(csv_path):
        print(f"Warning: {csv_path} not found. Skipping near-miss heatmap.")
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    rate_cols = [c for c in df.columns if c.endswith("_rate")]

    def create_heatmap(data, strictness_level, filtered):
        # Base filter for strictness
        subset = data[data["strictness"] == strictness_level].copy()

        if filtered:
            subset = subset[subset["match_count"] > 0]
            filter_suffix = "filtered"
            title_suffix = "(Filtered)"
        else:
            filter_suffix = "full"
            title_suffix = "(Full)"

        if subset.empty:
            print(f"No match data for {strictness_level} ({filter_suffix}). Skipping.")
            return

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
        plt.title(
            f"Stem-Final Pass Rates - {strictness_level.capitalize()} {title_suffix}"
        )
        plt.tight_layout()

        output_filename = f"{output_prefix}_{strictness_level}_{filter_suffix}.png"
        plt.savefig(output_filename)
        plt.close()

    # Generate 4 variations
    for s in ["strict", "loose"]:
        for f in [True, False]:
            create_heatmap(df, s, f)


def plot_root_ambiguity_histogram(csv_path, output_path):
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
        data=counts, x="Verbs per Root", y="Number of Root Pairs", color="skyblue"
    )

    plt.title("Root Ambiguity Histogram")
    plt.xlabel("Number of Verbs Sharing a Root Pair")
    plt.ylabel("Frequency (Number of Root Pairs)")

    # Add value labels on top of bars
    for index, row in counts.iterrows():
        plt.text(
            index,
            row["Number of Root Pairs"],
            str(row["Number of Root Pairs"]),
            color="black",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def run_all_visualizations():
    # Plots (images) go to visualizations
    output_dir = "artifacts/visualizations"
    os.makedirs(output_dir, exist_ok=True)

    # Data comes from reports
    input_dir = "artifacts/reports"

    print("Generating Class Distribution plots...")
    plot_class_distribution(
        os.path.join(input_dir, "class_match_counts.csv"),
        os.path.join(output_dir, "class_distribution"),
    )

    print("Generating Verb Coverage plot...")
    plot_verb_coverage(
        os.path.join(input_dir, "verb_coverage.json"),
        os.path.join(output_dir, "verb_coverage.png"),
    )

    print("Generating Near-Miss Heatmap plots...")
    plot_near_miss_heatmap(
        os.path.join(input_dir, "class_near_misses.csv"),
        os.path.join(output_dir, "near_miss_heatmap"),
    )

    print("Generating Root Ambiguity Histogram...")
    plot_root_ambiguity_histogram(
        os.path.join(input_dir, "root_ambiguity_counts.csv"),
        os.path.join(output_dir, "root_ambiguity_histogram.png"),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate visualizations for match data."
    )
    # The user said "no need to add a flag to the cli" for --hide-clutter,
    # they want both generated by default.
    args = parser.parse_args()

    run_all_visualizations()
    print("Visualizations saved to artifacts/visualizations/")
