import argparse

from noun_pipeline.phases.create_corpus import create_corpus


def main():
    parser = argparse.ArgumentParser(description="Cherokee Noun Pipeline Runner")
    # For now, we only run the corpus creation phase.
    print("[1/2] Creating noun corpus from Cherokee Nation Dictionary...")
    create_corpus()
    print("Done!")


if __name__ == "__main__":
    main()
