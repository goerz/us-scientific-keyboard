"""The chained dead key Math Bold Greek follows the Greek dead key: every key
gives the bold version of what it gives after Greek, wherever Unicode has
one, and nothing else."""

import unicodedata
from pathlib import Path

from layoutgen import model

ROOT = Path(__file__).resolve().parent.parent
LAYOUT = model.load(ROOT / "layout.toml")


def bold(char: str) -> str | None:
    """The math bold version of a Greek letter or symbol, if there is one."""
    if len(char) != 1 or unicodedata.combining(char):
        return None
    name = unicodedata.name(char)
    name = {"GREEK LUNATE EPSILON SYMBOL": "GREEK EPSILON SYMBOL"}.get(name, name)
    if not name.startswith("GREEK "):
        return None
    name = "MATHEMATICAL BOLD " + name.removeprefix("GREEK ").replace("LETTER ", "")
    try:
        return unicodedata.lookup(name)
    except KeyError:
        return None


def test_bold_greek():
    greek = LAYOUT.dead["greek"].map
    chain = LAYOUT.chains[("bold", "greek")].map
    want = {typed: bold(result) for typed, result in greek.items() if typed != " " and bold(result)}
    got = {typed: result for typed, result in chain.items() if typed != " "}
    assert got == want


def test_negated_math():
    """Slash, then Math: every Math result with a precomposed negation
    (the result with a combining long solidus) gives that."""
    math = LAYOUT.dead["math"].map
    chain = LAYOUT.chains[("slash", "math")].map
    solidus = chr(0x0338)  # combining long solidus overlay
    negated = {typed: unicodedata.normalize("NFC", result + solidus) for typed, result in math.items()}
    want = {typed: n for typed, n in negated.items() if typed != " " and len(n) == 1}
    got = {typed: result for typed, result in chain.items() if typed != " "}
    assert got == want


def greek_word(char: str) -> str:
    """The name of a Greek letter without its form: "BETA", "PHI"."""
    word = unicodedata.name(char).removesuffix(" SYMBOL").split()[-1]
    return word


def test_small_and_double_struck_greek():
    """Subscript, Superscript, and Double-Struck, then Greek: every entry is
    a version of the Greek letter on the same key (Unicode names the
    superscript epsilon after the open e, its Latin form)."""
    greek = LAYOUT.dead["greek"].map
    for first in ("subscript", "superscript", "doublestruck"):
        chain = LAYOUT.chains[(first, "greek")]
        for typed, result in chain.map.items():
            if typed == " ":
                continue
            letter = greek[typed]
            name = unicodedata.name(result)
            if letter in "εϵ":
                assert result == "ᵋ", (chain.id, typed, result)
            else:
                assert name.endswith(" " + greek_word(letter)), (chain.id, typed, letter, result)
                assert ("CAPITAL" in name) == letter.isupper(), (chain.id, typed, letter, result)
