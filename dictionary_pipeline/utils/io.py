import csv
import os
from typing import Any

from dictionary_pipeline.paths import CHEROKEE_NATION_DICTIONARY_PATH


def read_original_cnd() -> list[dict[str, Any]]:
    if not os.path.exists(CHEROKEE_NATION_DICTIONARY_PATH):
        raise FileNotFoundError(
            f"Input file not found at {CHEROKEE_NATION_DICTIONARY_PATH}"
        )

    with open(CHEROKEE_NATION_DICTIONARY_PATH, mode="r", encoding="utf-8") as f:
        content = f.read()
        if content.startswith("﻿"):
            content = content[1:]
        import io

        return list(csv.DictReader(io.StringIO(content)))
