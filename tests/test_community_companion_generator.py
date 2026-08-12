from tex_dictionary.community_companion_generator import (
    generate_community_companion_tex,
)


def test_community_companion_generator_execution():
    assert generate_community_companion_tex() is True
