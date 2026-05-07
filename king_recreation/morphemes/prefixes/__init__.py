from dataclasses import dataclass
from typing import Any

from king_recreation.morphemes.prefixes.prepronominals import (
    PrePronominalConfig,
    apply_prepronominal,
)
from king_recreation.morphemes.prefixes.pronominals import PronominalConfig
from king_recreation.morphology_types import Aspect


@dataclass
class PrefixConfig:
    pre: PrePronominalConfig
    pron: PronominalConfig
    stative: bool

    @staticmethod
    def from_row(stem_row: dict[str, str]) -> "PrefixConfig":
        pre_config = PrePronominalConfig.from_row(stem_row)
        pron_config = PronominalConfig.from_row(stem_row)

        return PrefixConfig(
            pre=pre_config, pron=pron_config, stative=stem_row["stative"] == "True"
        )

    def to_row(self) -> dict[str, str]:
        return {"stative": str(self.stative), **self.pre.to_row(), **self.pron.to_row()}

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "PrefixConfig":
        return PrefixConfig(
            pre=PrePronominalConfig.from_dict(data.get("pre", {})),
            pron=PronominalConfig.from_dict(data.get("pron", {})),
            stative=(data.get("stative", "") == "True"),
        )

    def apply_prepronominals(self, base: str, aspect: Aspect) -> list[str]:
        return apply_prepronominal(base, self.pre, aspect, self.stative)
