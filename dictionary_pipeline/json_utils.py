import dataclasses
import json
from enum import Enum
from typing import Any, Callable


def _default_encoder(
    o: Any, dict_modification: Callable[[dict[str, Any]], None] | None = None
) -> Any:
    if isinstance(o, Enum):
        return o.value

    if dataclasses.is_dataclass(o):
        # Use vars() for a shallow copy instead of asdict()
        # This allows the encoder to recursively call default()
        # on nested objects like Enums or other Dataclasses.
        d: dict[str, Any] = dict(vars(o))

        if dict_modification:
            dict_modification(d)
        return d

    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


def to_dict(
    o: Any, dict_modification: Callable[[dict[str, Any]], None] | None = None
) -> Any:
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
    dict_modification: Callable[[dict[str, Any]], None] | None = None,
) -> type[json.JSONEncoder]:

    class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, o):
            try:
                return _default_encoder(o, dict_modification)
            except TypeError:
                return super().default(o)

    return EnhancedJSONEncoder


EnhancedJSONEncoder = EnhancedJSONEncoderFactory()
