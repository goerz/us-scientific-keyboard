#!/usr/bin/env python3
"""Extract the X11 keysym table that layoutgen needs from keysymdef.h.

Usage: python3 tools/update-keysyms.py /path/to/X11/keysymdef.h

keysymdef.h comes with xorgproto (e.g. /usr/include/X11/keysymdef.h, or
/opt/homebrew/include/X11/keysymdef.h with Homebrew's xorgproto). The output,
src/layoutgen/keysyms.txt, lists every keysym with a value up to 0xFFFF by its
canonical name (aliases and deprecated names are skipped), with the Unicode
character it stands for where that is a one-to-one mapping.
"""

import re
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "src/layoutgen/keysyms.txt"
DEFINE = re.compile(r"^#define XK_(\w+)\s+0x([0-9a-fA-F]+)\s*(?:/\*(.*?)\*/)?")
EXACT = re.compile(r"^ U\+([0-9A-F]{4,6}) ")


def main(path: str) -> None:
    seen = set()
    lines = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = DEFINE.match(line)
        if not m:
            continue
        name, value, comment = m.group(1), int(m.group(2), 16), m.group(3) or ""
        if value > 0xFFFF or value in seen or "alias" in comment or "deprecated" in comment:
            continue
        seen.add(value)
        exact = EXACT.match(comment)
        lines.append(f"0x{value:04x} {name}" + (f" U+{exact.group(1)}" if exact else ""))
    header = [
        "# X11 keysyms up to 0xFFFF: value, canonical name, and the Unicode character",
        "# for one-to-one mappings. Extracted from xorgproto's keysymdef.h",
        "# (Copyright 1987, 1994, 1998 The Open Group; Copyright 1987 Digital Equipment",
        "# Corporation) by tools/update-keysyms.py. Do not edit.",
    ]
    OUT.write_text("\n".join(header + lines) + "\n", encoding="utf-8")
    print(f"{OUT}: {len(lines)} keysyms")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
