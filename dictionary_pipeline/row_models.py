import csv
import os
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any


def flatten_to_dict(obj: Any) -> dict[str, Any]:
    """
    Recursively flattens a dataclass into a single-level dictionary.
    If a field is itself a dataclass, it flattens its fields into the result.
    If a field has a to_row() or to_dict() method, it uses that.
    """
    if not is_dataclass(obj):
        return obj

    result = {}
    for f in fields(obj):
        val = getattr(obj, f.name)
        if hasattr(val, "to_row"):
            result.update(val.to_row())
        elif val is None:
            # Handle optional nested dataclasses if needed
            # For now, just skip or add a placeholder
            continue
        elif hasattr(val, "to_dict") and not is_dataclass(val):
            result.update(val.to_dict())
        elif is_dataclass(val):
            result.update(flatten_to_dict(val))
        else:
            result[f.name] = val
    return result


def _resolve_type(field_type: Any) -> Any:
    if isinstance(field_type, str):
        if field_type == "VerbMeta":
            return VerbMeta
        elif field_type == "AspectInfo":
            return AspectInfo
        elif field_type == "CorpusForms":
            return CorpusForms
        elif field_type == "RootInfo":
            return RootInfo
        elif field_type == "UserCurationInfo":
            return UserCurationInfo
    return field_type


def get_all_fieldnames(cls: Any) -> list[str]:
    """
    Attempts to discover all fieldnames that will be produced by to_dict().
    This works by inspecting the dataclass fields and their types.
    """
    if not is_dataclass(cls):
        return []

    fieldnames = []
    for f in fields(cls):
        field_type = _resolve_type(f.type)

        if hasattr(field_type, "get_row_keys"):
            fieldnames.extend(field_type.get_row_keys())
        else:
            fieldnames.append(f.name)
    return fieldnames


class Prediction(str, Enum):
    FULL_EVENTFUL = "FullEventful"


@dataclass
class VerbMeta:
    corpus_id: str
    definition: str
    prediction: Prediction
    entry_no: str | None = None

    @classmethod
    def get_row_keys(cls) -> list[str]:
        return ["corpus_id", "definition", "entry_no", "prediction"]

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "VerbMeta":
        return cls(
            corpus_id=row.get("corpus_id", ""),
            definition=row.get("definition", ""),
            prediction=Prediction(row["prediction"]),
            entry_no=row.get("entry_no"),
        )


@dataclass
class UserCurationInfo:
    user_selected: str | None = None
    pipeline_selected: str | None = None

    @classmethod
    def get_row_keys(cls) -> list[str]:
        return ["user_selected", "pipeline_selected"]

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "UserCurationInfo":
        return cls(
            user_selected=row.get("user_selected"),
            pipeline_selected=row.get("pipeline_selected"),
        )


@dataclass
class AspectInfo:
    verb_class: str
    post_root_morpheme: str | None = None
    stative: bool = False

    def to_row(self) -> dict[str, Any]:
        return {
            "class": self.verb_class,
            "post_root_morpheme": self.post_root_morpheme or "",
            "stative": str(self.stative),
        }

    @classmethod
    def get_row_keys(cls) -> list[str]:
        return ["class", "post_root_morpheme", "stative"]

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "AspectInfo":
        return cls(
            verb_class=row.get("class", ""),
            post_root_morpheme=row.get("post_root_morpheme"),
            stative=row.get("stative") == "True",
        )


@dataclass
class CorpusForms:
    present: str = ""
    present_1sg: str = ""
    imperfective: str = ""
    perfective: str = ""
    imperative: str = ""
    infinitive: str = ""

    @classmethod
    def get_row_keys(cls) -> list[str]:
        return [
            "present",
            "present_1sg",
            "imperfective",
            "perfective",
            "imperative",
            "infinitive",
        ]

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "CorpusForms":
        return cls(
            present=row.get("present", ""),
            present_1sg=row.get("present_1sg", ""),
            imperfective=row.get("imperfective", ""),
            perfective=row.get("perfective", ""),
            imperative=row.get("imperative", ""),
            infinitive=row.get("infinitive", ""),
        )


@dataclass
class RootInfo:
    h_grade: str
    g_grade: str | None = None

    @classmethod
    def get_row_keys(cls) -> list[str]:
        return ["h_grade", "g_grade"]

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "RootInfo":
        return cls(
            h_grade=row.get("h_grade", ""),
            g_grade=row.get("g_grade"),
        )


@dataclass
class RowModelBase:
    def to_dict(self) -> dict[str, Any]:
        return flatten_to_dict(self)

    @classmethod
    def get_fieldnames(cls) -> list[str]:
        return get_all_fieldnames(cls)

    @classmethod
    def write_csv(cls, filename: str, data: Any) -> None:
        if not data:
            return
        fieldnames = cls.get_fieldnames()
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows([x.to_dict() for x in data])

    @classmethod
    def from_row(cls: type[Any], row: dict[str, str]) -> Any:
        """
        Generic from_row implementation that reconstructs the composed dataclass.
        """
        if not is_dataclass(cls):
            return row

        kwargs = {}
        for f in fields(cls):
            field_type = _resolve_type(f.type)

            if hasattr(field_type, "from_row"):
                kwargs[f.name] = field_type.from_row(row)
            else:
                # Basic field, try to find it in the row
                if f.name in row:
                    val = row[f.name]
                    # Handle basic type conversion
                    if f.type is bool:
                        kwargs[f.name] = val == "True"
                    else:
                        kwargs[f.name] = val
        return cls(**kwargs)
