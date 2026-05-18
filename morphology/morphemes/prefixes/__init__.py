from dataclasses import dataclass
from typing import Any

from morphology.morphemes.prefixes.prepronominals import (
    PrePronominalConfig,
    apply_prepronominal,
)
from morphology.morphemes.prefixes.pronominals import PronominalConfig
from morphology.word_spec import WordSpec


@dataclass
class PrefixConfig:
    pre: PrePronominalConfig
    pron: PronominalConfig

    @staticmethod
    def from_row(stem_row: dict[str, str]) -> "PrefixConfig":
        pre_config = PrePronominalConfig.from_row(stem_row)
        pron_config = PronominalConfig.from_row(stem_row)

        return PrefixConfig(pre=pre_config, pron=pron_config)

    def to_row(self) -> dict[str, str]:
        return {**self.pre.to_row(), **self.pron.to_row()}

    @classmethod
    def get_row_keys(cls) -> list[str]:
        return PrePronominalConfig.get_row_keys() + PronominalConfig.get_row_keys()

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "PrefixConfig":
        return PrefixConfig(
            pre=PrePronominalConfig.from_dict(data.get("pre", {})),
            pron=PronominalConfig.from_dict(data.get("pron", {})),
        )

    def apply_prepronominals(self, base: str, spec: WordSpec) -> list[str]:
        return apply_prepronominal(base, self.pre, spec)
