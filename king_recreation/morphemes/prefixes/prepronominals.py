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
    word: str, config: PrePronominalConfig, form_name: str, stative: bool
) -> List[str]:
    current_forms = [word]

    if config.distributive:
        new_forms = []
        for w in current_forms:
            for p in get_distributive_forms(form_name, stative):
                new_forms.append(p + "-" + w)
        current_forms = list(set(new_forms))

    if config.partitive:
        new_forms = []
        for w in current_forms:
            for p in get_partitive_forms(form_name):
                new_forms.append(p + "-" + w)
        current_forms = list(set(new_forms))

    if config.translocutive or (
        form_name == "imperative" and config.translocutiveImpOnly
    ):
        new_forms = []
        for w in current_forms:
            for p in get_translocutive_forms(form_name):
                new_forms.append(p + "-" + w)
        current_forms = list(set(new_forms))

    return current_forms


def get_translocutive_forms(form_name: str) -> List[str]:
    return ["wi", "w"]


def get_partitive_forms(form_name: str) -> List[str]:
    if form_name == "infinitive":
        return ["iy", "i", ">ø"]
    return ["ni", "n"]


def get_distributive_forms(form_name: str, stative: bool) -> List[str]:
    if form_name == "infinitive" or (form_name == "imperative" and not stative):
        return ["ts", "ti", "t"]
    return ["te", "t"]
