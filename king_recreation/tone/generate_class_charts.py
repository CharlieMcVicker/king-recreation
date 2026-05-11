import os
from typing import Any, cast

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from king_recreation.tone.models import (
    Consonant,
    GlottalPosition,
    HistoricalVowel,
    LexedForm,
    MorphemeBoundary,
)


def get_final_segment_str(lexed_form: LexedForm) -> str:
    if not lexed_form.tokens:
        return ""

    # Identify the last non-boundary token
    morpheme_boundaries = [
        i for i, t in enumerate(lexed_form.tokens) if isinstance(t, MorphemeBoundary)
    ]
    if not morpheme_boundaries:
        return ""

    last_token_idx = morpheme_boundaries[-1]

    new_lexed = LexedForm(lexed_form.tokens[last_token_idx:])

    pending_post_c = False

    for i, token in enumerate(lexed_form.tokens):
        if isinstance(token, MorphemeBoundary):
            continue

        if isinstance(token, Consonant):
            is_target = i == last_token_idx

            val = token.value
            if pending_post_c:
                val += "'"
                pending_post_c = False

            if is_target:
                return val

        elif isinstance(token, HistoricalVowel):
            is_target = i == last_token_idx

            prefix = ""
            if pending_post_c:
                prefix = "'"
                pending_post_c = False

            if is_target:
                s = prefix + str(token)
                if token.glottal_position == GlottalPosition.POST_C:
                    s += "'"
                return s

            if token.glottal_position == GlottalPosition.POST_C:
                pending_post_c = True
            else:
                pending_post_c = False

    return ""


def main():
    input_path = "artifacts/data/underlying_stems.csv"
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    df = pd.read_csv(input_path)

    if "class" not in df.columns:
        print("Error: 'class' column missing in DataFrame.")
        print("Columns found:", df.columns)
        return

    # Drop NaN
    df = df.dropna(subset=["class", "form", "underlying_stem"])

    print(f"Processing {len(df)} rows...")

    # Calculate segmented endings
    endings = []
    for stem in df["underlying_stem"]:
        try:
            ending = str(stem).split("-")[-1]
            endings.append(ending)
        except Exception as e:
            print(f"Error parsing {stem}: {e}")
            endings.append("ERROR")

    df["segmented_ending"] = endings

    # Create output directory
    output_dir = "artifacts/charts/class_endings"
    os.makedirs(output_dir, exist_ok=True)

    # Get unique classes and forms
    groups = df.groupby(["class", "form"])

    count = 0
    for (cls_name, form_name), group in cast(Any, groups):
        if group.empty:
            continue

        # Count unique verbs
        num_verbs = group["corpus_id"].nunique()

        # Count how many verbs have at least one underlying form with each ending
        unique_verb_endings = group[["corpus_id", "segmented_ending"]].drop_duplicates()
        ending_counts = unique_verb_endings["segmented_ending"].value_counts()
        ending_percs = (ending_counts / num_verbs) * 100

        # Plot
        plt.figure(figsize=(10, 6))
        ax = sns.barplot(x=ending_percs.index, y=ending_percs.values)

        plt.title(f"Class: {cls_name} | Form: {form_name}\n(N={num_verbs} verbs)")
        plt.ylabel("Percentage of Verbs (%)")
        plt.xlabel("Segmented Ending (Final Segment)")
        plt.ylim(0, 100)

        # Add values on bars
        for i, v in enumerate(ending_percs.values):
            ax.text(i, v + 1, f"{v:.1f}%", ha="center", va="bottom")

        # Sanitize filename
        safe_cls = "".join(c for c in str(cls_name) if c.isalnum() or c in ("_", "-"))
        safe_form = "".join(c for c in str(form_name) if c.isalnum() or c in ("_", "-"))
        filename = f"{output_dir}/class_{safe_cls}_form_{safe_form}.png"

        plt.savefig(filename)
        plt.close()
        count += 1

    print(f"Generated {count} charts in {output_dir}")


if __name__ == "__main__":
    main()
