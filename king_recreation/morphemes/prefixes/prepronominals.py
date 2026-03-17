from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class PrePronominalConfig:
    translocutive: bool = False
    translocutiveImpOnly: bool = False
    partitive: bool = False
    distributive: bool = False

    @staticmethod
    def from_row(row: dict[str, str]):
        return PrePronominalConfig(
            translocutive=row["translocutive"] == "True",
            translocutiveImpOnly=row["translocutive_imp_only"] == "True",
            partitive=row["partitive"] == "True",
            distributive=row["distributive"] == "True",
        )

    @staticmethod
    def from_dict(data: dict) -> "PrePronominalConfig":
        return PrePronominalConfig(**data)

    def to_row(self) -> dict[str, str]:
        row = {}

        row["translocutive"] = str(self.translocutive)
        row["translocutive_imp_only"] = str(self.translocutiveImpOnly)
        row["partitive"] = str(self.partitive)
        row["distributive"] = str(self.distributive)

        return row


def apply_prepronominal(
    word: str, config: PrePronominalConfig, aspect: str, stative: bool
) -> List[str]:
    current_forms = [word]

    if config.distributive:
        new_forms = []
        for w in current_forms:
            for p in get_distributive_forms(aspect, stative):
                new_forms.append(p + "-" + w)
        current_forms = list(set(new_forms))

    if config.partitive:
        new_forms = []
        for w in current_forms:
            for p in get_partitive_forms(aspect):
                new_forms.append(p + "-" + w)
        current_forms = list(set(new_forms))

    if config.translocutive or (aspect == "imperative" and config.translocutiveImpOnly):
        new_forms = []
        for w in current_forms:
            for p in get_translocutive_forms(aspect):
                new_forms.append(p + "-" + w)
        current_forms = list(set(new_forms))

    return current_forms


def get_translocutive_forms(aspect: str) -> List[str]:
    return ["wi", "w"]


def get_partitive_forms(aspect: str) -> List[str]:
    if aspect == "infinitive":
        return ["iy", "i", ">ø"]
    return ["ni", "n"]


def get_distributive_forms(aspect: str, stative: bool) -> List[str]:
    if aspect == "infinitive" or (aspect == "imperative" and not stative):
        return ["ts", "ti", "t"]
    return ["te", "t"]
