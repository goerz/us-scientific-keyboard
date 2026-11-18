# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""One-time extraction of the macOS .keylayout template from the legacy layout.

Usage:

    uv run tools/import_skeleton.py ../USScientific > src/layoutgen/macos_skeleton.keylayout

Keeps everything layout.toml doesn't describe (non-character keys, keypad,
Command and Control layers, JIS keyboards) and replaces the character keys of
the plain/Shift/Caps/Option layers, the actions, and the terminators with
@@...@@ placeholders. Action references outside those layers are replaced by
the action's plain output.
"""

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from layoutgen.keys import KEYS  # noqa: E402

CHAR_CODES = {k.mac for k in KEYS}


def xml_escape(text: str) -> str:
    return "".join(
        c if c.isprintable() and c not in "&<>\"'" else f"&#x{ord(c):04X};" for c in text
    )


def main() -> None:
    legacy = Path(sys.argv[1])
    sys.path.insert(0, str(legacy / "windows"))
    import convert as c

    bundle = legacy / "USScientific.bundle"
    layout = c.parse_bundle(bundle)
    lines = c.find_keylayout(bundle).read_text(encoding="utf-8").split("\n")

    out = []
    mapset = index = None
    in_actions = in_terminators = False
    for line in lines:
        if "<actions>" in line:
            in_actions = True
            out.append("    <actions>\n@@ACTIONS@@    </actions>")
            continue
        if "</actions>" in line:
            in_actions = False
            continue
        if "<terminators>" in line:
            in_terminators = True
            out.append("    <terminators>\n@@TERMINATORS@@    </terminators>")
            continue
        if "</terminators>" in line:
            in_terminators = False
            continue
        if in_actions or in_terminators:
            continue
        if line.startswith("<keyboard "):
            out.append('<keyboard group="126" id="@@ID@@" name="@@NAME@@" maxout="@@MAXOUT@@">')
            continue
        if line.startswith("<!--"):
            continue  # Ukelele header comments
        if line.startswith("<?xml"):
            out.append('<?xml version="1.1" encoding="UTF-8"?>')
            continue
        if line.startswith("<!DOCTYPE"):
            out.append(line)
            out.append("<!-- Generated from layout.toml by layoutgen. Do not edit. -->")
            continue
        m = re.search(r'<keyMapSet id="([^"]+)"', line)
        if m:
            mapset = m.group(1)
        m = re.search(r'<keyMap index="(\d+)"', line)
        if m:
            index = int(m.group(1))
        if "</keyMap>" in line and mapset == "16c" and index <= 5:
            out.append(f"@@KEYS_{index}@@")
        m = re.search(r'<key code="(\d+)" (output|action)="([^"]*)"/>', line)
        if m:
            code, kind, value = int(m.group(1)), m.group(2), m.group(3)
            if mapset == "16c" and index <= 5 and code in CHAR_CODES:
                continue
            if kind == "action":
                r = layout.actions[html.unescape(value)].get("none")
                if not isinstance(r, c.Output):
                    continue
                line = line[: m.start()] + f'<key code="{code}" output="{xml_escape(r.text)}"/>'
        out.append(line)
    print("\n".join(out).rstrip() + "\n")


if __name__ == "__main__":
    main()
