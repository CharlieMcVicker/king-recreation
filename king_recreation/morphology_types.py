"""
Core morphological types for the Cherokee verb analysis system.

This module has NO dependencies on other king_recreation modules,
ensuring it can be imported anywhere without circular import issues.
"""

from enum import Enum


class Aspect(Enum):
    """Morphological aspect categories for Cherokee verb forms."""

    PRESENT = "present"
    IMPERFECTIVE = "imperfective"
    PERFECTIVE = "perfective"
    IMPERATIVE = "imperative"
    INFINITIVE = "infinitive"

    @property
    def allows_h_alternation(self) -> bool:
        """Present and imperative forms permit h-alternation in aspect suffixes."""
        return self in (Aspect.PRESENT, Aspect.IMPERATIVE)
