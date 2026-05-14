import os
from csv import DictReader, DictWriter
from typing import Any, cast

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from dictionary_pipeline.tone.analysis import (
    check_prediction,
    generate_underlying_forms,
    get_tonicity_for_form,
)
from dictionary_pipeline.tone.models import LocalHighTone, Tonicity
from dictionary_pipeline.tone.utils import strip_morpheme_boundaries


def diagnose_mismatch(
    verb, surface, expected_ending, tonicity: Tonicity = Tonicity.TONIC
):
    print(f"    Mismatch: {verb.definition[:30]}... | Surface: {surface}")

    underlying_candidates = generate_underlying_forms(surface, tonicity=tonicity)
    valid_candidates = [
        str(uf)
        for uf in underlying_candidates
        if check_prediction(str(uf), surface, tonicity=tonicity)
    ]

    # 1. Check for Length or quality Mismatch (Valid UF exists but different ending)
    if valid_candidates:
        print(f"      Found {len(valid_candidates)} valid underlying forms:")
        for uf in valid_candidates:
            print(f"        - {uf}")
        # Check if any is 'close' (e.g. length diff)
        # Simplify: just report them. User can see.

    # 2. Check for Start State Blocked (for Imperative/21 tone)
    # Try assuming PREVIOUS High (BLOCKED environment)
    candidates_blocked = generate_underlying_forms(
        surface, initial_lh=LocalHighTone.PREV, tonicity=tonicity
    )
    valid_blocked = [
        str(uf)
        for uf in candidates_blocked
        if check_prediction(
            str(uf),
            surface,
            initial_lh=LocalHighTone.PREV,
            tonicity=tonicity,
        )
    ]

    found_blocked_match = False
    for uf in valid_blocked:
        if uf.endswith(expected_ending):
            found_blocked_match = True
            break

    if found_blocked_match:
        print(
            f"      [DIAGNOSIS] Matches expected ending '{expected_ending}' IF we assume 'BLOCKED' environment (Preceding High Tone)."
        )
        return

    if not valid_candidates and not found_blocked_match:
        print(
            "      [DIAGNOSIS] No valid underlying forms found even with BLOCKED check."
        )


def analyze_class_coverage(verbs_with_forms):
    """
    Analyzes how well the underlying endings defined in data/classes_underlying.csv
    match the actual data for each class. Saves results to artifacts/reports/.
    """
    print("\n--- Class Coverage Analysis ---")

    # Load underlying class definitions
    underlying_classes_path = "data/classes_underlying.csv"
    if not os.path.exists(underlying_classes_path):
        print(f"File not found: {underlying_classes_path}")
        return

    class_defs = {}
    with open(underlying_classes_path, "r") as f:
        reader = DictReader(f)
        for row in reader:
            class_defs[row["class"]] = row

    reports_dir = "artifacts/reports"
    os.makedirs(reports_dir, exist_ok=True)

    # Process each class found in the definition file
    for class_name, target_def in class_defs.items():
        # Filter for verbs of the target class
        class_verbs = [
            (v, row) for v, row in verbs_with_forms if v.class_name == class_name
        ]

        total_verbs = len(class_verbs)
        if total_verbs == 0:
            print(f"Skipping class '{class_name}': No verbs found in data.")
            continue

        print(f"\nAnalyzing {total_verbs} verbs of class '{class_name}'")
        report_rows = []

        # Forms to check (intersection of FORMS and columns in CSV)
        forms_to_check = [
            f
            for f in [
                "present",
                "imperfective",
                "perfective",
                "imperative",
                "infinitive",
            ]
            if f in target_def and target_def[f].strip()
        ]

        for form_name in forms_to_check:
            # Get target endings
            raw_endings = target_def[form_name]
            target_endings = [e.strip() for e in raw_endings.split(";") if e.strip()]

            if not target_endings:
                continue

            print(f"  Form: {form_name}")

            for ending in target_endings:
                match_count = 0
                valid_verbs_for_form = 0

                for verb, row in class_verbs:
                    surface = row.get(form_name)
                    if not surface:
                        continue

                    valid_verbs_for_form += 1

                    # Generate underlying forms
                    tonicity = get_tonicity_for_form(verb, form_name)
                    underlying_candidates = generate_underlying_forms(
                        surface, tonicity=tonicity
                    )

                    # Check if ANY valid underlying form ends with the target ending
                    matches_ending = False
                    for uf in underlying_candidates:
                        # Check if candidate is valid (reconstructs surface)
                        if not check_prediction(str(uf), surface, tonicity=tonicity):
                            continue

                        # Check ending match
                        uf_str = str(uf)
                        if strip_morpheme_boundaries(uf_str).endswith(ending):
                            matches_ending = True
                            break
                    if matches_ending:
                        match_count += 1
                    else:
                        diagnose_mismatch(verb, surface, ending, tonicity=tonicity)

                if valid_verbs_for_form > 0:
                    percentage = (match_count / valid_verbs_for_form) * 100
                    print(
                        f"    Ending '{ending}': {match_count}/{valid_verbs_for_form} ({percentage:.1f}%)"
                    )
                    report_rows.append(
                        {
                            "class": class_name,
                            "form": form_name,
                            "expected_ending": ending,
                            "matches": match_count,
                            "total": valid_verbs_for_form,
                            "percentage": round(percentage, 1),
                        }
                    )
                else:
                    print(f"    Ending '{ending}': No valid surface forms found.")
                    report_rows.append(
                        {
                            "class": class_name,
                            "form": form_name,
                            "expected_ending": ending,
                            "matches": 0,
                            "total": 0,
                            "percentage": 0.0,
                        }
                    )

        if report_rows:
            csv_path = os.path.join(reports_dir, f"class_coverage_{class_name}.csv")
            with open(csv_path, "w", newline="") as f:
                writer = DictWriter(
                    f,
                    fieldnames=[
                        "class",
                        "form",
                        "expected_ending",
                        "matches",
                        "total",
                        "percentage",
                    ],
                )
                writer.writeheader()
                writer.writerows(report_rows)
            print(f"  Report saved to {csv_path}")


def generate_prediction_charts(overall_perc, form_stats):
    """
    Generates charts for prediction success rates.
    """
    output_dir = "artifacts/charts/diagnostics"
    os.makedirs(output_dir, exist_ok=True)

    # 1. Overall Full Coverage Chart
    plt.figure(figsize=(6, 6))
    plt.pie(
        [overall_perc, 100 - overall_perc],
        labels=["Full Coverage", "Incomplete"],
        autopct="%1.1f%%",
        startangle=140,
        colors=["#4CAF50", "#FFC107"],
    )
    plt.title(
        "Percentage of Verbs with Full Coverage\n(All recorded forms reconstructable)"
    )
    plt.savefig(f"{output_dir}/overall_coverage.png")
    plt.close()

    # 2. Success Rate by Form Chart
    if form_stats:
        df = pd.DataFrame(form_stats)
        plt.figure(figsize=(10, 6))
        ax = sns.barplot(
            x="form",
            y="success_rate",
            data=df,
            hue="form",
            palette="viridis",
            legend=False,
        )
        plt.title("Success Rate for Proposing Underlying Forms by Form Name")
        plt.ylabel("Success Rate (%)")
        plt.xlabel("Form Name")
        plt.ylim(0, 100)

        for i, p in enumerate(ax.patches):
            p_any = cast(Any, p)
            ax.annotate(
                f"{p_any.get_height():.1f}%",
                (p_any.get_x() + p_any.get_width() / 2.0, p_any.get_height()),
                ha="center",
                va="center",
                xytext=(0, 9),
                textcoords="offset points",
            )

        plt.savefig(f"{output_dir}/success_by_form.png")
        plt.close()
    print(f"Diagnostic charts saved to {output_dir}")


def calculate_prediction_stats(verbs_with_forms):
    """
    Calculates:
    1. % of verbs with at least one valid underlying form for EVERY recorded form.
    2. Success rate for proposing underlying forms by form name.
    """
    print("\n--- Prediction Statistics ---")

    # The standard set of forms to report on
    forms_to_check = [
        "present",
        "imperfective",
        "perfective",
        "imperative",
        "infinitive",
    ]

    total_verbs = 0
    fully_covered_verbs = 0

    success_by_form = {f: 0 for f in forms_to_check}
    total_by_form = {f: 0 for f in forms_to_check}

    for verb, row in verbs_with_forms:
        has_any_form = False
        all_forms_successful = True

        for form_name in forms_to_check:
            surface = row.get(form_name)
            if not surface:
                continue

            has_any_form = True
            total_by_form[form_name] += 1

            tonicity = get_tonicity_for_form(verb, form_name)
            candidates = generate_underlying_forms(surface, tonicity=tonicity)

            success = any(
                check_prediction(str(uf), surface, tonicity=tonicity)
                for uf in candidates
            )

            if success:
                success_by_form[form_name] += 1
            else:
                all_forms_successful = False

        if has_any_form:
            total_verbs += 1
            if all_forms_successful:
                fully_covered_verbs += 1

    overall_perc = 0
    if total_verbs > 0:
        overall_perc = (fully_covered_verbs / total_verbs) * 100
        print(
            f"Verbs with full coverage (all recorded forms have valid prediction): {fully_covered_verbs}/{total_verbs} ({overall_perc:.1f}%)"
        )

    print("\nSuccess rate by form:")
    form_stats = []
    for f in forms_to_check:
        if total_by_form[f] > 0:
            perc = (success_by_form[f] / total_by_form[f]) * 100
            print(f"  {f:15}: {success_by_form[f]}/{total_by_form[f]} ({perc:.1f}%)")
            form_stats.append({"form": f, "success_rate": perc})
        else:
            print(f"  {f:15}: No data")

    # Generate charts
    generate_prediction_charts(overall_perc, form_stats)

    # Save CSV report
    reports_dir = "artifacts/reports"
    os.makedirs(reports_dir, exist_ok=True)
    csv_path = os.path.join(reports_dir, "prediction_success_rates.csv")
    with open(csv_path, "w", newline="") as f:
        writer = DictWriter(f, fieldnames=["form", "successes", "total", "percentage"])
        writer.writeheader()
        for f in forms_to_check:
            total = total_by_form[f]
            successes = success_by_form[f]
            perc = (successes / total * 100) if total > 0 else 0
            writer.writerow(
                {
                    "form": f,
                    "successes": successes,
                    "total": total,
                    "percentage": round(perc, 1),
                }
            )
        # Add a row for overall
        writer.writerow(
            {
                "form": "OVERALL (Full Coverage)",
                "successes": fully_covered_verbs,
                "total": total_verbs,
                "percentage": round(overall_perc, 1),
            }
        )
    print(f"Prediction stats report saved to {csv_path}")
