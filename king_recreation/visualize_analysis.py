import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
import argparse

def plot_class_distribution(csv_path, output_prefix):
    """Generates a bar chart showing verbs matched by each class."""
    if not os.path.exists(csv_path):
        print(f"Warning: {csv_path} not found. Skipping class distribution plot.")
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        return

    # Prepare data for plotting
    value_vars = ['strict_ending', 'strict_full', 'strict_reconstructs', 'loose_ending', 'loose_full']
    # Filter for existing columns to avoid errors if some are missing
    value_vars = [v for v in value_vars if v in df.columns]
    
    df_melted = df.melt(id_vars='class', 
                        value_vars=value_vars,
                        var_name='Match Type', value_name='Count')

    def create_plot(data, suffix):
        plt.figure(figsize=(12, 8))
        sns.barplot(data=data, x='class', y='Count', hue='Match Type')
        plt.title(f'Verb Matches per Class ({suffix})')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f'{output_prefix}_{suffix.lower()}.png')
        plt.close()

    # Full version
    create_plot(df_melted, 'Full')

    # Filtered version (only classes with at least one match in any category)
    active_classes = df[(df[value_vars] > 0).any(axis=1)]['class']
    df_filtered = df_melted[df_melted['class'].isin(active_classes)]
    if not df_filtered.empty:
        create_plot(df_filtered, 'Filtered')

def plot_verb_coverage(json_path, output_path):
    """Generates a bar chart for verb coverage summary."""
    if not os.path.exists(json_path):
        print(f"Warning: {json_path} not found. Skipping verb coverage plot.")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)

    # Convert to DataFrame
    rows = []
    for combo, counts in data.items():
        for cat, val in counts.items():
            rows.append({'Combination': combo, 'Coverage': cat, 'Count': val})
    
    df = pd.DataFrame(rows)

    plt.figure(figsize=(10, 6))
    sns.barplot(data=df, x='Combination', y='Count', hue='Coverage')
    plt.title('Verb Coverage Summary')
    plt.xticks(rotation=15)
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

    rate_cols = [c for c in df.columns if c.endswith('_rate')]
    
    def create_heatmap(data, strictness_level, filtered):
        # Base filter for strictness
        subset = data[data['strictness'] == strictness_level].copy()
        
        if filtered:
            subset = subset[subset['match_count'] > 0]
            filter_suffix = "filtered"
            title_suffix = "(Filtered)"
        else:
            filter_suffix = "full"
            title_suffix = "(Full)"

        if subset.empty:
            print(f"No match data for {strictness_level} ({filter_suffix}). Skipping.")
            return

        # Set index to class + count for labeling
        subset['label'] = subset['class'] + " (" + subset['match_count'].astype(str) + ")"
        subset = subset.set_index('label')[rate_cols]
        
        # Shorten column names for the plot
        subset.columns = [c.replace('_rate', '') for c in subset.columns]

        # Calculate dynamic height
        height = min(20, len(subset) * 0.4 + 2)
        plt.figure(figsize=(12, height))
        
        sns.heatmap(subset, annot=True, cmap="YlGnBu", vmin=0, vmax=1)
        plt.title(f'Stem-Final Pass Rates - {strictness_level.capitalize()} {title_suffix}')
        plt.tight_layout()
        
        output_filename = f'{output_prefix}_{strictness_level}_{filter_suffix}.png'
        plt.savefig(output_filename)
        plt.close()

    # Generate 4 variations
    for s in ['strict', 'loose']:
        for f in [True, False]:
            create_heatmap(df, s, f)

def run_all_visualizations():
    # Plots (images) go to visualizations
    output_dir = 'artifacts/visualizations'
    os.makedirs(output_dir, exist_ok=True)
    
    # Data comes from reports
    input_dir = 'artifacts/reports'
    
    print("Generating Class Distribution plots...")
    plot_class_distribution(os.path.join(input_dir, 'class_match_counts.csv'), 
                            os.path.join(output_dir, 'class_distribution'))
    
    print("Generating Verb Coverage plot...")
    plot_verb_coverage(os.path.join(input_dir, 'verb_coverage.json'), 
                       os.path.join(output_dir, 'verb_coverage.png'))
    
    print("Generating Near-Miss Heatmap plots...")
    plot_near_miss_heatmap(os.path.join(input_dir, 'class_near_misses.csv'), 
                           os.path.join(output_dir, 'near_miss_heatmap'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate visualizations for match data.")
    # The user said "no need to add a flag to the cli" for --hide-clutter, 
    # they want both generated by default.
    args = parser.parse_args()
    
    run_all_visualizations()
    print("Visualizations saved to artifacts/visualizations/")
