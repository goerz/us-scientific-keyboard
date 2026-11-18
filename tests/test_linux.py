"""The generated native Linux layout does what layout.toml says.

XKB doesn't run here (see test_linux_xkbcommon.py for that), so this parses
the generated symbols file and Compose file and simulates how they're used:
the key type picks a level from Shift, Lock (Caps Lock), and LevelThree
(AltGr), a Lock that the type doesn't consume uppercases the result, and a
dead keysym followed by another keysym gives the Compose sequence's string.
It also runs install.py against a temporary home folder.
"""

import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from layoutgen import linux, model

ROOT = Path(__file__).resolve().parent.parent
LAYOUT = model.load(ROOT / "layout.toml")

# Key types from xkeyboard-config's types/extra: consumed modifiers, levels,
# preserved modifiers
TYPES = {
    "FOUR_LEVEL": (
        {"Shift", "LevelThree"},
        {(): 1, ("Shift",): 2, ("LevelThree",): 3, ("LevelThree", "Shift"): 4},
        {},
    ),
    "FOUR_LEVEL_ALPHABETIC": (
        {"Shift", "Lock", "LevelThree"},
        {(): 1, ("Shift",): 2, ("Lock",): 2, ("LevelThree",): 3, ("LevelThree", "Shift"): 4,
         ("LevelThree", "Lock"): 4},
        {},
    ),
    "FOUR_LEVEL_SEMIALPHABETIC": (
        {"Shift", "Lock", "LevelThree"},
        {(): 1, ("Shift",): 2, ("Lock",): 2, ("LevelThree",): 3, ("LevelThree", "Shift"): 4,
         ("LevelThree", "Lock"): 3},
        {("LevelThree", "Lock"): {"Lock"}},
    ),
    "FOUR_LEVEL_PLUS_LOCK": (
        {"Shift", "Lock", "LevelThree"},
        {(): 1, ("Shift",): 2, ("Lock",): 5, ("LevelThree",): 3, ("LevelThree", "Shift"): 4,
         ("LevelThree", "Lock"): 3},
        {},
    ),
}
LAYER_MODS = {
    "base": (), "shift": ("Shift",), "option": ("LevelThree",), "shift-option": ("LevelThree", "Shift"),
    "caps": ("Lock",), "caps-option": ("LevelThree", "Lock"),
}
KEYSYMS = {}  # keysym name -> character, from the vendored X11 table
for line in (ROOT / "src/layoutgen/keysyms.txt").read_text(encoding="utf-8").splitlines():
    if not line.startswith("#"):
        value, name, *uni = line.split()
        KEYSYMS[name] = (int(value, 16), chr(int(uni[0][2:], 16)) if uni else None)

KEY_LINE = re.compile(r'^    key <(\w+)> \{ type\[Group1\] = "(\w+)", symbols\[Group1\] = \[ ([^\]]*) \] \};')
SEQUENCE = re.compile(r'^<(\w+)> <(\w+)> : "((?:[^"\\]|\\.)*)"$')


@pytest.fixture(scope="module")
def symbols():
    keys = {}
    for line in linux.symbols(LAYOUT).splitlines():
        m = KEY_LINE.match(line)
        if m:
            keys[m.group(1)] = (m.group(2), [s.strip() for s in m.group(3).split(",")])
        elif line.lstrip().startswith("key "):
            pytest.fail(f"unparsed key: {line}")
    return keys


@pytest.fixture(scope="module")
def sequences():
    result = {}
    for line in linux.compose(LAYOUT).splitlines():
        if not line or line.startswith("#"):
            continue
        m = SEQUENCE.match(line)
        assert m, f"unparsed line: {line}"
        assert (m.group(1), m.group(2)) not in result, f"duplicate: {line}"
        result[(m.group(1), m.group(2))] = re.sub(r"\\(.)", r"\1", m.group(3))
    return result


def keysym_char(name):
    """The character a keysym types, or None for a dead keysym."""
    if name.startswith("dead_"):
        assert name in KEYSYMS, name
        return None
    if re.fullmatch(r"U[0-9A-F]{4,6}", name):
        return chr(int(name[1:], 16))
    return KEYSYMS[name][1]


def press(symbols, xkb_name, layer):
    """The keysym name the key types in the layer, or None."""
    type_name, syms = symbols[xkb_name]
    consumed, levels, preserve = TYPES[type_name]
    active = tuple(m for m in LAYER_MODS[layer] if m in consumed)
    level = levels.get(active, 1)
    sym = syms[level - 1] if level <= len(syms) else "NoSymbol"
    if sym in ("NoSymbol", "VoidSymbol"):
        return None
    lock_consumed = "Lock" in consumed and "Lock" not in preserve.get(active, set())
    if "Lock" in LAYER_MODS[layer] and not lock_consumed:
        char = keysym_char(sym)
        if char is not None and char.upper() != char:
            return f"uppercased {sym}"  # depends on the case mapping; never wanted
    return sym


def binding_of(sym):
    if sym is None:
        return None
    if sym.startswith("dead_"):
        dead_ids = {v: k for k, v in linux.dead_keysyms(LAYOUT).items()}
        return model.Dead(dead_ids[sym])
    return model.Char(keysym_char(sym))


def plain(binding):
    """`binding` without its description."""
    return model.Char(binding.text) if isinstance(binding, model.Char) else binding


def test_keys(symbols):
    mismatches = []
    for key in LAYOUT.keys:
        for layer in LAYER_MODS:
            want = plain(LAYOUT.binding(key, layer, "pc"))
            got = binding_of(press(symbols, key.physical.xkb, layer))
            if want != got:
                mismatches.append((key.name, layer, want, got))
    assert mismatches == []


@pytest.mark.parametrize("dead_id", list(LAYOUT.dead))
def test_dead_keys(symbols, sequences, dead_id):
    dead = LAYOUT.dead[dead_id]
    dead_sym = linux.dead_keysyms(LAYOUT)[dead_id]
    mismatches = []
    for key in LAYOUT.keys:
        for layer in LAYER_MODS:
            binding = LAYOUT.binding(key, layer, "pc")
            if binding is None:
                continue
            sym = press(symbols, key.physical.xkb, layer)
            got = sequences.get((dead_sym, sym))
            if isinstance(binding, model.Dead):
                want = dead.symbol + LAYOUT.dead[binding.id].symbol
            elif ord(binding.text) > 0xFFFF:
                want = None  # GTK and IBus can't match it; left out
            else:
                want = dead.map.get(binding.text, dead.symbol + binding.text)
            if want != got:
                mismatches.append((key.name, layer, want, got))
    assert mismatches == []


def test_no_extra_sequences(symbols, sequences):
    typed = {press(symbols, key.physical.xkb, layer) for key in LAYOUT.keys for layer in LAYER_MODS}
    dead_syms = set(linux.dead_keysyms(LAYOUT).values())
    for first, second in sequences:
        assert first in dead_syms and second in typed, (first, second)


def test_keysyms_for_gtk_and_ibus(sequences):
    """GTK and IBus keep the keysyms of a sequence in 16 bits. A `Uxxxx` name
    only matches if no named keysym has the value xxxx (so named keysyms are
    used where they exist), and the strings that aren't single characters
    below U+8000 have to fit in 32 KB in GTK, together with the default
    table's (2 KB for en_US.UTF-8)."""
    by_value = {value: name for name, (value, _) in KEYSYMS.items()}
    chars = {char: name for name, (_, char) in reversed(list(KEYSYMS.items())) if char}
    size = 0
    for (first, second), result in sequences.items():
        for sym in (first, second):
            if re.fullmatch(r"U[0-9A-F]{4,6}", sym):
                cp = int(sym[1:], 16)
                assert cp <= 0xFFFF and cp not in by_value and chr(cp) not in chars, sym
            else:
                assert sym in KEYSYMS, sym
        if len(result) > 1 or ord(result) >= 0x8000:
            size += len(result.encode()) + 1
    assert size < 0x8000 - 0x2000


def test_registry():
    root = ET.fromstring(linux.registry(LAYOUT).split("\n", 2)[2])
    assert root.findtext("layoutList/layout/configItem/name") == LAYOUT.id
    assert f'name[Group1] = "{root.findtext("layoutList/layout/configItem/description")}";' in linux.symbols(LAYOUT)


@pytest.fixture
def installer(tmp_path):
    out = tmp_path / "linux"
    linux.write(LAYOUT, out)
    home = tmp_path / "home"
    home.mkdir()
    (tmp_path / "bin").mkdir()
    env = {"HOME": str(home), "PATH": str(tmp_path / "bin")}  # no gsettings

    def run(*args):
        subprocess.run([sys.executable, str(out / "install.py"), *args], env=env, check=True, capture_output=True)

    return home, run


def test_install_fresh(installer):
    home, run = installer
    run()
    config = home / ".config"
    assert (config / "xkb/symbols" / LAYOUT.id).read_text(encoding="utf-8") == linux.symbols(LAYOUT)
    assert (config / LAYOUT.id / "Compose").read_text(encoding="utf-8") == linux.compose(LAYOUT)
    xcompose = (home / ".XCompose").read_text(encoding="utf-8").splitlines()
    assert xcompose[1] == 'include "%L"'
    assert xcompose[-1] == f'include "%H/.config/{LAYOUT.id}/Compose"'
    registry = ET.parse(config / "xkb/rules/evdev.xml")
    assert [e.text for e in registry.iterfind("layoutList/layout/configItem/name")] == [LAYOUT.id]
    run()  # again: nothing doubled
    assert (home / ".XCompose").read_text(encoding="utf-8").splitlines() == xcompose
    run("--uninstall")
    assert sorted(p.relative_to(home).as_posix() for p in home.rglob("*")) == [
        ".config", ".config/xkb", ".config/xkb/rules", ".config/xkb/symbols"
    ]


def test_install_into_existing_files(installer):
    home, run = installer
    xcompose = '# mine\ninclude "%L"\n<Multi_key> <a> <a> : "å"\n'
    (home / ".XCompose").write_text(xcompose, encoding="utf-8")
    ibus = home / ".config/ibus/Compose"
    ibus.parent.mkdir(parents=True)
    ibus.write_text('include "%L"\n', encoding="utf-8")
    rules = home / ".config/xkb/rules"
    rules.mkdir(parents=True)
    (rules / "evdev.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xkbConfigRegistry SYSTEM "xkb.dtd">\n'
        '<xkbConfigRegistry version="1.1"><layoutList><layout><configItem><name>mine</name>'
        "</configItem></layout></layoutList></xkbConfigRegistry>\n",
        encoding="utf-8",
    )
    run()
    include = f'include "%H/.config/{LAYOUT.id}/Compose"'
    assert (home / ".XCompose").read_text(encoding="utf-8").startswith(xcompose)
    assert (home / ".XCompose").read_text(encoding="utf-8").splitlines()[-1] == include
    assert ibus.read_text(encoding="utf-8").splitlines()[-1] == include
    names = [e.text for e in ET.parse(rules / "evdev.xml").iterfind("layoutList/layout/configItem/name")]
    assert names == ["mine", LAYOUT.id]
    run("--uninstall")
    assert (home / ".XCompose").read_text(encoding="utf-8") == xcompose
    assert ibus.read_text(encoding="utf-8") == 'include "%L"\n'
    names = [e.text for e in ET.parse(rules / "evdev.xml").iterfind("layoutList/layout/configItem/name")]
    assert names == ["mine"]
