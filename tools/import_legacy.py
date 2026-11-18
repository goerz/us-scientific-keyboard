# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""One-time import of the legacy Ukelele layout into layout.toml.

Usage:

    uv run tools/import_legacy.py ../USScientific > layout.toml

Reads USScientific.bundle (through the parser in windows/convert.py of the
legacy repository) and the key descriptions from its README.md.
"""

import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from layoutgen.keys import KEYS  # noqa: E402

DEAD_IDS = {
    "Dead Key State 15": "greek",
    "Subscript": "subscript",
    "Superscript": "superscript",
    "Math Script": "script",
    "mathbold": "bold",
    "Math Double Struck": "doublestruck",
    "1": "grave",
    "2": "acute",
    "9": "slash",
}

DEAD_INFO = {  # id -> (name, description)
    "acute": ("Acute", "letters with acute accent"),
    "grave": ("Grave", "letters with grave accent"),
    "slash": ("Slash", "letters with a slash through them"),
    "greek": ("Greek", "Greek letters, plus the first few Hebrew letters used in mathematics"),
    "subscript": ("Subscript", "subscripts"),
    "superscript": ("Superscript", "superscripts"),
    "script": ("Math Script", "letters from the math script alphabet, e.g., for superoperators"),
    "bold": ("Math Bold", "letters from the math bold alphabet, e.g., for vectors"),
    "doublestruck": ("Double-Struck", "letters from the double-struck alphabet, e.g., for number sets"),
}

# Native Windows dead keys need a BMP character as their symbol.
WINDOWS_SYMBOL = {"doublestruck": "ℍ"}


def toml_key(name: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]+", name):
        return name
    return toml_str(name)


def toml_str(text: str, escape: bool = True) -> str:
    out = []
    for c in text:
        if c == '"':
            out.append('\\"')
        elif c == "\\":
            out.append("\\\\")
        elif escape and (
            unicodedata.combining(c)
            or unicodedata.category(c) in ("Zs", "Cc", "Cf", "Mn", "Me")
        ) and c != " ":
            out.append(f"\\u{ord(c):04X}")
        else:
            out.append(c)
    return '"' + "".join(out) + '"'


def readme_descriptions(readme: Path) -> dict:
    """{(layer, key name): description} from the README key tables."""
    descs = {}
    for m in re.finditer(r"^\| `+(⌥⇧?)(.+?) ?`+ \|\s*(.*?)\s*\| (.*) \|$", readme.read_text(), re.M):
        mod, key, _, desc = m.groups()
        layer = "shift-option" if "⇧" in mod else "option"
        key = {"Space": "space"}.get(key, key)
        descs[(layer, key)] = desc
    return descs


def main() -> None:
    legacy = Path(sys.argv[1])
    sys.path.insert(0, str(legacy / "windows"))
    import convert as c

    L = c.parse_bundle(legacy / "USScientific.bundle")
    km = L.keymaps
    descs = readme_descriptions(legacy / "README.md")

    def result(entry, state="none"):
        r = c.resolve(L, entry, state)
        if isinstance(r, c.Next):
            return ("dead", DEAD_IDS[r.state])
        if isinstance(r, c.Output):
            return ("char", r.text)
        return None

    out = []
    w = out.append
    w("# US Scientific keyboard layout")
    w("#")
    w("# This file is the single source of the layout for all platforms.")
    w("#")
    w("# Without Option, every key types what it types on a US keyboard. The")
    w("# [option] table and the dead-key maps are keyed by the character a key")
    w("# types without Option: `q` is the Q key, `Q` is Shift+Q, `\"1\"` is the 1")
    w("# key and `\"!\"` is Shift+1. In [option], lowercase/unshifted names mean")
    w("# Option and uppercase/shifted names mean Shift+Option. Caps Lock acts like")
    w("# Shift for letters, also for Option+letter when Shift+Option gives its")
    w("# uppercase form.")
    w("#")
    w("# [notes] explains characters (keyed by the character) for the README;")
    w("# characters without a note are described by their Unicode name.")
    w("")
    w("[layout]")
    w('name = "US Scientific"')
    w('id = "us_scientific"')
    w('version = "4.0.0"')
    w('author = "Michael Goerz"')
    w('copyright = "2021-2026"')
    w('license = "MIT"')
    w('language = "en"')
    w('macos-bundle-id = "net.michaelgoerz.keyboardlayout.us-scientific"')
    w("macos-id = -18113  # unique negative id of a custom macOS layout")
    w('windows-dll = "kbdussci"')
    w("")
    w("[option]")

    triggers = {}
    notes = {}
    row = None
    row_names = {0: "number row", 1: "top row", 2: "home row", 3: "bottom row", 4: "space bar"}
    for key in KEYS:
        b, s = result(km[0].get(key.mac)), result(km[1].get(key.mac))
        if b != ("char", key.base) or s != ("char", key.shift):
            sys.exit(f"{key.name}: plain or Shift layer differs from US")
        if key.row != row:
            row = key.row
            w(f"# {row_names[row]}")
        typed_pairs = [(key.base, "option", 3)]
        if key.shift != key.base:
            typed_pairs.append((key.shift, "shift-option", 4))
        for typed, layer, index in typed_pairs:
            r = result(km[index].get(key.mac))
            if r is None:
                continue
            if r[0] == "dead":
                triggers[r[1]] = typed
                continue
            w(f"{toml_key(typed)} = {toml_str(r[1])}")
            desc = descs.get((layer, key.name))
            if desc and r[1] not in notes:
                notes[r[1]] = desc
        if key.name == "space":
            r = result(km[4].get(key.mac))
            if r != result(km[3].get(key.mac)):
                sys.exit("Option+Space and Shift+Option+Space differ")
    w("")

    # Dead keys, in the order of the README table
    order = ["acute", "grave", "slash", "greek", "subscript", "superscript", "script", "bold", "doublestruck"]
    states = {v: k for k, v in DEAD_IDS.items()}

    def sort_key(ch):
        if ch.isalpha() and ch.isascii():
            return (0 if ch.islower() else 1, ch.lower())
        if ch.isdigit():
            return (2, ch)
        return (3, ch)

    for dead in order:
        state = states[dead]
        name, desc = DEAD_INFO[dead]
        table = {}
        for key in KEYS:
            for index in (0, 1, 3, 4):
                entry = km[index].get(key.mac)
                typed = result(entry)
                r = c.resolve(L, entry, state)
                if typed is None or typed[0] != "char" or not isinstance(r, c.Output):
                    continue
                if typed[1] in table and table[typed[1]] != r.text:
                    sys.exit(f"Collision in {dead}: {typed[1]!r}")
                table[typed[1]] = r.text
        w(f"[dead.{dead}]")
        w(f"key = {toml_str(triggers[dead])}")
        w(f"name = {toml_str(name)}")
        w(f"desc = {toml_str(desc)}")
        w(f"symbol = {toml_str(L.terminators[state])}  # typed alone, or before a key without an entry")
        if dead in WINDOWS_SYMBOL:
            w(f"windows-symbol = {toml_str(WINDOWS_SYMBOL[dead])}  # Windows needs a BMP character")
        w("")
        w(f"[dead.{dead}.map]")
        for ch in sorted(table, key=sort_key):
            w(f"{toml_key(ch)} = {toml_str(table[ch])}")
        w("")

    w("[notes]")
    for ch, note in notes.items():
        w(f"{toml_str(ch)} = {toml_str(note, escape=False)}")
    print("\n".join(out).rstrip() + "\n")


if __name__ == "__main__":
    main()
