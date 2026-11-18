"""The generated native Windows layout does what layout.toml says, as far as
native Windows dead keys allow.

MSVC doesn't run here, so this parses the character table, dead-key
translations, and ligatures from the generated C source and simulates how
Windows uses them: CAPLOK/CAPLOKALTGR for Caps Lock, WCH_DEAD followed by a
row with the dead character, and, after a dead key, the DEADTRANS entry for
the next character or else the dead character followed by that character.
"""

import re
from pathlib import Path

import pytest

from layoutgen import model, windows

ROOT = Path(__file__).resolve().parent.parent
LAYOUT = model.load(ROOT / "layout.toml")
DEAD_CHAR, TRANS, _ = windows.tables(LAYOUT)

COLUMN = {"base": 0, "shift": 1, "option": 4, "shift-option": 5}


def value(cell: str):
    return cell if cell.startswith("WCH_") else chr(int(cell, 16))


@pytest.fixture(scope="module")
def tables():
    source, _ = windows.c_source(LAYOUT)
    body = source[source.index("vk_to_wchar6[] = {"):source.index("static VK_TO_WCHARS3")]
    rows = re.findall(r"\{(\S+), ([A-Z_ |0]+), \{([^}]*)\}\}", body)
    keys = {}
    for i, (vk, attrs, cells) in enumerate(rows):
        cells = [value(c.strip()) for c in cells.split(",")]
        if vk == "VK__none_":
            continue
        dead_row = rows[i + 1] if i + 1 < len(rows) and rows[i + 1][0] == "VK__none_" else None
        dead_cells = [value(c.strip()) for c in dead_row[2].split(",")] if dead_row else None
        keys[vk] = (set(attrs.split(" | ")), cells, dead_cells)
    deadtrans = {
        (chr(int(a, 16)), chr(int(b, 16))): chr(int(c, 16))
        for a, b, c in re.findall(r"DEADTRANS\(0x(\w+), 0x(\w+), 0x(\w+), 0x0000\)", source)
    }
    ligatures = {
        (vk, int(col)): "".join(chr(int(u, 16)) for u in units.split(", ")).encode(
            "utf-16-le", "surrogatepass").decode("utf-16-le")
        for vk, col, units in re.findall(r"\{(\S+), (\d), \{(0x\w+, 0x\w+)\}\}", source[source.index("ligatures[]"):])
    }
    return keys, deadtrans, ligatures


def press(tables, vk, layer):
    """("char", text) | ("dead", dead character) | None"""
    keys, _, ligatures = tables
    attrs, cells, dead_cells = keys[vk]
    if layer == "caps":
        col = 1 if "CAPLOK" in attrs else 0
    elif layer == "caps-option":
        col = 5 if "CAPLOKALTGR" in attrs else 4
    else:
        col = COLUMN[layer]
    cell = cells[col]
    if cell == "WCH_NONE":
        return None
    if cell == "WCH_DEAD":
        return ("dead", dead_cells[col])
    if cell == "WCH_LGTR":
        return ("char", ligatures[(vk, col)])
    return ("char", cell)


def expected(binding, dead_id):
    """What native Windows should type for `binding` (after dead key `dead_id`)."""
    if binding is None:
        return None
    if isinstance(binding, model.Dead):
        if dead_id is not None:
            return "skip"  # two dead keys in a row: not modeled
        return ("dead", DEAD_CHAR[binding.id]) if binding.id in DEAD_CHAR else None
    if dead_id is None:
        return ("char", binding.text)
    if binding.text in TRANS[dead_id]:
        return ("char", TRANS[dead_id][binding.text])
    return ("char", DEAD_CHAR[dead_id] + binding.text)


@pytest.mark.parametrize("dead_id", [None, *DEAD_CHAR])
def test_keys(tables, dead_id):
    _, deadtrans, _ = tables
    mismatches = []
    for key in LAYOUT.keys:
        for layer in ("base", "caps", "shift", "option", "caps-option", "shift-option"):
            want = expected(LAYOUT.binding(key, layer, "pc"), dead_id)
            if want == "skip":
                continue
            got = press(tables, key.physical.vk, layer)
            if dead_id is not None and got is not None and got[0] == "char" and len(got[1]) == 1:
                dc = DEAD_CHAR[dead_id]
                got = ("char", deadtrans.get((got[1], dc), dc + got[1]))
            elif dead_id is not None and got is not None and got[0] == "char":
                got = ("char", DEAD_CHAR[dead_id] + got[1])  # a ligature after a dead key
            if want != got:
                mismatches.append((key.name, layer, want, got))
    assert mismatches == []


def test_whats_missing_on_windows():
    """Only results outside the BMP, and so the bold dead key, are lost."""
    for dead in LAYOUT.dead.values():
        kept = TRANS.get(dead.id, {})
        for typed, result in dead.map.items():
            if typed not in kept:
                assert not windows.is_bmp_char(result if result != dead.symbol else dead.windows_symbol)
    assert set(LAYOUT.dead) - set(DEAD_CHAR) == {"bold"}
