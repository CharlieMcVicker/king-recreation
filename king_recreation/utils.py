import os
import csv
import functools
from king_recreation.class_patterns import ClassPatterns

CLASSES_PATH = "data/classes.csv"


@functools.lru_cache()
def _get_class_order():
    """
    Loads the class order from data/classes.csv.
    Returns a dict mapping class_name -> index.
    """
    class_order = {}

    # Try to locate data/classes.csv relative to this file
    # utils.py is in <root>/king_recreation/utils.py
    # data is in <root>/data/classes.csv
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = CLASSES_PATH

    if not os.path.exists(csv_path):
        # Fallback to absolute path relative to project root if CWD stems fail
        candidate = os.path.join(base_dir, csv_path)
        if os.path.exists(candidate):
            csv_path = candidate

    try:
        patterns = ClassPatterns.from_csv(csv_path)
        # Note: from_csv returns a dict but preserves insertion order in Python 3.7+
        # which corresponds to CSV row order.
        for idx, p in enumerate(patterns.values()):
            if p.name:
                class_order[p.name] = idx
    except Exception as e:
        print(f"Warning: Could not load class order from {csv_path}: {e}")

    return class_order


def get_class_sort_key(class_name):
    """
    Returns a sort key for verb classes.
    Sorts based on the exact order in data/classes.csv.
    Classes not found in the CSV are sorted to the end.
    """
    if not class_name:
        return 9999

    order_map = _get_class_order()

    # If found, return index. If not, return a large number + lexical backup
    if class_name in order_map:
        return order_map[class_name]

    return 9999
