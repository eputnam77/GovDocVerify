import re

from documentcheckertool.config.boilerplate_texts import BOILERPLATE_PARAGRAPHS

_NORMALISE = re.compile(r"\s+")


def _norm(text: str) -> str:
    return _NORMALISE.sub(" ", text.strip()).lower()


_NORMALISED = {_norm(p) for p in BOILERPLATE_PARAGRAPHS}


def is_boilerplate(text: str) -> bool:
    """
    True if *text* matches a protected boiler-plate paragraph.
    Matching ignores case and collapses repeated whitespace.
    """
    return _norm(text) in _NORMALISED
