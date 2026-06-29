import argparse

from noun_pipeline.phases.create_corpus import create_corpus
from noun_pipeline.phases.generate_hypotheses import phase_2_generate_hypotheses


def main():
    parser = argparse.ArgumentParser(description="Cherokee Noun Pipeline Runner")
    print("[1/5] Creating noun corpus from Cherokee Nation Dictionary...")
    create_corpus()
    print("[2/5] Generating hypotheses for noun structures...")
    phase_2_generate_hypotheses()
    print("Done!")


if __name__ == "__main__":
    main()
