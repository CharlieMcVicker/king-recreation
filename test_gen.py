from morphology.morphemes.prefixes.pronominals import (
    Number,
    Person,
    PronominalConfig,
    PronominalSet,
    StemType,
    detach_prefix,
)

config = PronominalConfig(set_type=PronominalSet.SET_A, stem_type=StemType.CONSONANT)
key = (Person.THIRD, Number.SINGULAR, PronominalSet.SET_A)
stem, meta = detach_prefix("awoni", key, config)
print(stem, meta)
