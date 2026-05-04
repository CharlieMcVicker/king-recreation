import atexit
import dataclasses
import json
import time
from enum import Enum
from functools import partial, wraps
from typing import Callable, Dict


def _default_encoder(o, dict_modification: Callable[[Dict], None] = None):
    if isinstance(o, Enum):
        return o.value

    if dataclasses.is_dataclass(o):
        # Use vars() for a shallow copy instead of asdict()
        # This allows the encoder to recursively call default()
        # on nested objects like Enums or other Dataclasses.
        d = dict(vars(o))

        if dict_modification:
            dict_modification(d)
        return d

    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


def to_dict(o, dict_modification: Callable[[Dict], None] = None):
    try:
        converted = _default_encoder(o, dict_modification)
    except TypeError:
        converted = o

    if isinstance(converted, dict):
        return {k: to_dict(v, dict_modification) for k, v in converted.items()}
    if isinstance(converted, (list, tuple, set)):
        return type(converted)(to_dict(v, dict_modification) for v in converted)
    return converted


def EnhancedJSONEncoderFactory(
    dict_modification: Callable[[Dict], None] = None,
) -> type[json.JSONEncoder]:

    class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, o):
            try:
                return _default_encoder(o, dict_modification)
            except TypeError:
                return super().default(o)

    return EnhancedJSONEncoder


EnhancedJSONEncoder = EnhancedJSONEncoderFactory()


class track_performance:
    def __init__(self, func):
        wraps(func)(self)
        self.func = func
        self.total_time = 0
        self.call_count = 0
        # Register the report method to run when the script ends
        atexit.register(self.print_report)

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return partial(self, obj)

    def __call__(self, *args, **kwargs):
        start = time.perf_counter()
        result = self.func(*args, **kwargs)
        end = time.perf_counter()

        # Accumulate stats from "natural" execution
        self.total_time += end - start
        self.call_count += 1
        return result

    def print_report(self):
        if self.call_count > 0:
            avg = self.total_time / self.call_count
            print(f"\n--- Final Performance Report: {self.func.__name__} ---")
            print(f"Total Calls:   {self.call_count}")
            print(f"Total Time:    {self.total_time:.6f}s")
            print(f"Average Time:  {avg:.6f}s")
