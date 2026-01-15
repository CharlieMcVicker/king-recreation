import os
import csv
import functools

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

    if os.path.exists(csv_path):
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader):
                    cls_name = row.get("class", "").strip()
                    if cls_name:
                        class_order[cls_name] = idx
        except Exception as e:
            # Fallback: log error if possible, or just proceed empty
            print(f"Warning: Could not load class order from {csv_path}: {e}")
            pass

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
