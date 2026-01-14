import csv
import subprocess
import io
import sys


def get_reconstructed_verbs(csv_content):
    verbs = set()
    reader = csv.DictReader(io.StringIO(csv_content))
    for row in reader:
        # We want strict reconstructs
        if row["strictness"] == "strict" and row["scope"] == "reconstructs":
            verbs.add(row["definition"])
    return verbs


def main():
    # 1. Read Current Branch matches
    try:
        with open("artifacts/data/matches.csv", "r", encoding="utf-8") as f:
            current_content = f.read()
    except FileNotFoundError:
        print("Error: artifacts/data/matches.csv not found.")
        sys.exit(1)

    # 2. Read Main Branch matches
    try:
        main_content = subprocess.check_output(
            ["git", "show", "main:artifacts/data/matches.csv"], encoding="utf-8"
        )
    except subprocess.CalledProcessError:
        print("Error: Could not read artifacts/data/matches.csv from main branch.")
        sys.exit(1)

    current_verbs = get_reconstructed_verbs(current_content)
    main_verbs = get_reconstructed_verbs(main_content)

    lost_verbs = main_verbs - current_verbs
    gained_verbs = current_verbs - main_verbs

    print(f"Verbs on Main: {len(main_verbs)}")
    print(f"Verbs on Current: {len(current_verbs)}")
    print(f"Lost Verbs: {len(lost_verbs)}")
    print(f"Gained Verbs: {len(gained_verbs)}")

    # Write Lost Verbs to file
    with open("artifacts/reports/lost_verbs.csv", "w", encoding="utf-8") as f:
        f.write("definition\n")
        for v in sorted(list(lost_verbs)):
            f.write(f'"{v}"\n')

    print("\nTop 10 Lost Verbs:")
    for v in sorted(list(lost_verbs))[:10]:
        print(f"- {v}")

    # Write Gained Verbs to file
    with open("artifacts/reports/gained_verbs.csv", "w", encoding="utf-8") as f:
        f.write("definition\n")
        for v in sorted(list(gained_verbs)):
            f.write(f'"{v}"\n')


if __name__ == "__main__":
    main()
