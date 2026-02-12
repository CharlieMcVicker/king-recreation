import os
import shutil
import subprocess
import sys

from king_recreation.paths import TEX_DIR
from tex_dictionary.generator import generate_tex_files


def run_xelatex():
    if shutil.which("xelatex"):
        print("XeLaTeX found. Compiling main.tex...")
        # Change to the tex directory to run xelatex
        original_cwd = os.getcwd()
        os.chdir(TEX_DIR)
        try:
            # Run twice to resolve TOC
            for _ in range(2):
                subprocess.run(
                    ["xelatex", "-interaction=batchmode", "main.tex"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            if os.path.exists("main.pdf"):
                print(f"PDF generated at {os.path.abspath('main.pdf')}")
            else:
                print("XeLaTeX finished but main.pdf was not found.")
        except subprocess.CalledProcessError as e:
            print(f"Error during XeLaTeX compilation: {e}")
        finally:
            os.chdir(original_cwd)
    else:
        print("XeLaTeX not found. TeX files are available in artifacts/tex/")


def main():
    # 1. Generate TeX files
    print("Generating TeX files...")
    if generate_tex_files():
        # 2. Compile if XeLaTeX is available
        run_xelatex()
    else:
        print("Generation failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
