"""Read a macOS .keylayout file and evaluate what keys type.

Used by the tests to check generated layouts against a reference.
"""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

_CONTROL_OFFSET = 0xF0000  # control characters, smuggled past the XML 1.0 parser


@dataclass(frozen=True)
class Output:
    text: str


@dataclass(frozen=True)
class Next:
    state: str


def _smuggle(match) -> str:
    ref = match.group(1)
    cp = int(ref[1:], 16) if ref[0] in "xX" else int(ref)
    if cp < 0x20 and cp not in (0x9, 0xA, 0xD):
        return chr(_CONTROL_OFFSET + cp)
    return match.group(0)


def _unsmuggle(text):
    if text is None:
        return None
    return "".join(
        chr(ord(c) - _CONTROL_OFFSET) if _CONTROL_OFFSET <= ord(c) < _CONTROL_OFFSET + 0x20 else c
        for c in text
    )


class KeyLayout:
    def __init__(self, path: Path, mapset: str = "16c"):
        text = Path(path).read_text(encoding="utf-8")
        text = text.replace('<?xml version="1.1"', '<?xml version="1.0"', 1)
        text = re.sub(r"&#(x[0-9A-Fa-f]+|[0-9]+);", _smuggle, text)
        root = ET.fromstring(text)
        self.name = root.get("name")
        self.keymaps = {}
        for km in root.find(f"keyMapSet[@id='{mapset}']").findall("keyMap"):
            keys = {}
            for key in km.findall("key"):
                if key.get("output") is not None:
                    keys[int(key.get("code"))] = ("output", _unsmuggle(key.get("output")))
                else:
                    keys[int(key.get("code"))] = ("action", _unsmuggle(key.get("action")))
            self.keymaps[int(km.get("index"))] = keys
        self.actions = {}
        for action in root.find("actions").findall("action"):
            whens = {}
            for when in action.findall("when"):
                if when.get("next") is not None:
                    whens[when.get("state")] = Next(when.get("next"))
                else:
                    whens[when.get("state")] = Output(_unsmuggle(when.get("output", "")))
            self.actions[_unsmuggle(action.get("id"))] = whens
        self.terminators = {
            w.get("state"): _unsmuggle(w.get("output", ""))
            for w in root.find("terminators").findall("when")
        }

    def press(self, index: int, code: int, state: str = "none"):
        """Output | Next | None for a key in key map `index` and dead state."""
        entry = self.keymaps.get(index, {}).get(code)
        if entry is None:
            return None
        kind, value = entry
        if kind == "output":
            return Output(value) if state == "none" else None
        return self.actions[value].get(state)
