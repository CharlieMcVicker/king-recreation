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
            if form_name == "infinitive" or (form_name == "imperative" and not stative):
                new_forms.extend(["ts" + w, "ti" + w, "t" + w])
            else:
                new_forms.extend(["te" + w, "t" + w])
        current_forms = list(set(new_forms))

    if config.partitive:
        new_forms = []
        for w in current_forms:
            if form_name == "infinitive":
                new_forms.extend(["iy" + w, "i" + w, w])
            else:
                # Manual 'hn'/'hw' cases removed here as they are now handled
                # by the 'nh'/'wh' respelling reform in preprocessing.
                new_forms.extend(["ni" + w, "n" + w])
        current_forms = list(set(new_forms))

    if config.translocutive or (
        form_name == "imperative" and config.translocutiveImpOnly
    ):
        new_forms = []
        for w in current_forms:
            new_forms.extend(["wi" + w, "w" + w])
        current_forms = list(set(new_forms))

    return current_forms
