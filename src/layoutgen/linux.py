"""Native Linux keyboard layout: an XKB symbols file for the keys and a
Compose file for the dead keys, plus a registry entry and install script.

XKB puts the alternative layer on AltGr (levels 3 and 4). It can't define new
dead keys: a dead key types one of the predefined dead_* keysyms, and the
Compose file says what that keysym does with the next key. Compose results
can be strings and characters outside the BMP.

GTK and IBus store the keysyms of Compose sequences in 16 bits, and they only
match a key if the sequence spells its keysym the same way the layout does.
So keys are written with their X11 keysym names where one exists (`Greek_pi`,
not `U03C0`, whose low 16 bits are the keysym `Amacron`), and sequences with a
key outside the BMP (𝕚, 𝟙) are left out.

The number pad keeps its keypad keysyms (`KP_Home`, `KP_7`) on the first two
levels, which Num Lock and Shift choose between as usual, and has the
alternative layer on levels 3 and 4: the digit keys use the type
FOUR_LEVEL_MIXED_KEYPAD (types/numpad, as in `keypad(ossnumber)`), which
picks them with AltGr whatever Num Lock is; the operators use FOUR_LEVEL.
"""

import unicodedata
from importlib.resources import files
from pathlib import Path
from xml.sax.saxutils import escape

from .model import CAPS_LAYERS, LAYERS, Char, Dead, Layout, LayoutError

# Dead keysyms for dead keys without a keysym named `dead_<id>`: old ones that
# every Compose implementation knows, and that don't start a longer sequence
# together with another dead key in the default (en_US.UTF-8) Compose table.
# Where they do, older libxkbcommon (1.6, but not 1.13) keeps waiting for a
# third key after two dead keys (`dead_stroke`, `dead_hook`, `dead_horn`).
DEAD_POOL = [
    "dead_belowring", "dead_belowmacron", "dead_belowcircumflex", "dead_belowtilde",
    "dead_belowbreve", "dead_belowdiaeresis", "dead_invertedbreve", "dead_belowcomma",
    "dead_currency",
]

# XKB key types from xkeyboard-config's types/extra: the modifiers a type
# looks at, the level for each combination of them (others: level 1), and
# the modifiers it preserves (doesn't consume) for a combination.
TYPES = {
    "FOUR_LEVEL": (
        {"Shift", "LevelThree"},
        {"Shift": 2, "LevelThree": 3, "Shift+LevelThree": 4},
        {},
    ),
    "FOUR_LEVEL_ALPHABETIC": (
        {"Shift", "Lock", "LevelThree"},
        {"Shift": 2, "Lock": 2, "Shift+Lock": 1, "LevelThree": 3, "Shift+LevelThree": 4,
         "Lock+LevelThree": 4, "Shift+Lock+LevelThree": 3},
        {},
    ),
    "FOUR_LEVEL_SEMIALPHABETIC": (
        {"Shift", "Lock", "LevelThree"},
        {"Shift": 2, "Lock": 2, "Shift+Lock": 1, "LevelThree": 3, "Shift+LevelThree": 4,
         "Lock+LevelThree": 3, "Shift+Lock+LevelThree": 4},
        {"Lock+LevelThree": {"Lock"}, "Shift+Lock+LevelThree": {"Lock"}},
    ),
    "FOUR_LEVEL_PLUS_LOCK": (
        {"Shift", "Lock", "LevelThree"},
        {"Shift": 2, "LevelThree": 3, "Shift+LevelThree": 4, "Lock": 5, "Shift+Lock": 2,
         "Lock+LevelThree": 3, "Shift+Lock+LevelThree": 4},
        {},
    ),
}
MOD_ORDER = ("Shift", "Lock", "LevelThree")

# Active modifiers in each layer of the model
LAYER_MODS = {
    "base": set(), "shift": {"Shift"}, "option": {"LevelThree"},
    "shift-option": {"Shift", "LevelThree"}, "caps": {"Lock"}, "caps-option": {"Lock", "LevelThree"},
}
ALL_LAYERS = LAYERS + CAPS_LAYERS


def _load_keysyms():
    by_char, by_value = {}, {}
    for line in files("layoutgen").joinpath("keysyms.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            continue
        value, name, *uni = line.split()
        by_value[int(value, 16)] = name
        if uni:
            by_char.setdefault(chr(int(uni[0][2:], 16)), name)
    return by_char, by_value


KEYSYM_BY_CHAR, KEYSYM_BY_VALUE = _load_keysyms()
KEYSYM_NAMES = set(KEYSYM_BY_VALUE.values())


def char_keysym(char: str) -> str:
    if len(char) != 1:
        raise LayoutError(f"XKB: a key can only type one character, not {char!r}")
    return KEYSYM_BY_CHAR.get(char, f"U{ord(char):04X}")


def in_compose_tables(char: str) -> bool:
    """Whether GTK and IBus can match `char`'s keysym in a Compose sequence."""
    return char in KEYSYM_BY_CHAR or (ord(char) <= 0xFFFF and ord(char) not in KEYSYM_BY_VALUE)


def dead_keysyms(layout: Layout) -> dict:
    """Dead key id -> dead keysym name."""
    result = {}
    pool = [name for name in DEAD_POOL if name[5:] not in layout.dead]
    for dead in layout.dead.values():
        name = f"dead_{dead.id}"
        if name not in KEYSYM_NAMES:
            if not pool:
                raise LayoutError("XKB: not enough dead keysyms (see linux.DEAD_POOL)")
            name = pool.pop(0)
        result[dead.id] = name
    return result


def binding_keysym(binding, dead_syms: dict) -> str:
    if binding is None:
        return "VoidSymbol"  # NoSymbol would keep what `pc` puts there
    if isinstance(binding, Dead):
        return dead_syms[binding.id]
    return char_keysym(binding.text)


def _type_result(type_name: str, levels: list, layer: str):
    """What a key of type `type_name` with `levels` types in `layer`: a
    binding, or "?" if Caps Lock may change it (a cased character with Lock
    not consumed; libxkbcommon then applies its own case mapping)."""
    mods, levelmap, preserve = TYPES[type_name]
    active = LAYER_MODS[layer] & mods
    combo = "+".join(m for m in MOD_ORDER if m in active)
    level = levelmap.get(combo, 1) if combo else 1
    binding = levels[level - 1] if level <= len(levels) else None
    lock_consumed = "Lock" in mods and "Lock" not in preserve.get(combo, set())
    if "Lock" in LAYER_MODS[layer] and not lock_consumed and isinstance(binding, Char):
        if binding.text.upper() != binding.text:
            return "?"
    return binding


def key_type(layout: Layout, key) -> tuple[str, list]:
    """(XKB type, bindings per level) that give every layer of `key`."""
    b = {layer: layout.binding(key, layer, "pc") for layer in ALL_LAYERS}
    four = [b["base"], b["shift"], b["option"], b["shift-option"]]
    if b["caps"] != b["base"]:
        candidates = ["FOUR_LEVEL_ALPHABETIC", "FOUR_LEVEL_SEMIALPHABETIC", "FOUR_LEVEL_PLUS_LOCK"]
    else:
        candidates = ["FOUR_LEVEL", "FOUR_LEVEL_PLUS_LOCK"]
    for type_name in candidates:
        levels = four + [b["caps"]] if type_name == "FOUR_LEVEL_PLUS_LOCK" else four
        if all(_type_result(type_name, levels, layer) == b[layer] for layer in ALL_LAYERS):
            return type_name, levels
    raise LayoutError(f"XKB: no key type fits key {key.name!r}")


def shown(binding) -> str:
    """A binding for a comment."""
    if binding is None:
        return "-"
    if isinstance(binding, Dead):
        return f"<{binding.id}>"
    return "".join(
        c if c.isprintable() and unicodedata.category(c) not in ("Mn", "Me", "Zs") else f"U+{ord(c):04X}"
        for c in binding.text
    )


def symbols(layout: Layout) -> str:
    """The XKB symbols file."""
    dead_syms = dead_keysyms(layout)
    lines = [
        f"// {layout.name} keyboard layout for XKB",
        "//",
        "// Generated from layout.toml by layoutgen. Do not edit.",
        "//",
        f"// {layout.copyright_notice}. {layout.license} License.",
        "//",
        "// The alternative layer is on AltGr (right Alt). Dead keys type dead_*",
        f"// keysyms; the Compose file {layout.id}.compose defines what they do.",
        "",
        "default partial alphanumeric_keys modifier_keys",
        'xkb_symbols "basic" {',
        f'    name[Group1] = "{xkb_description(layout)}";',
        "",
    ]
    for key in layout.keys:
        type_name, levels = key_type(layout, key)
        syms = ", ".join(binding_keysym(b, dead_syms) for b in levels)
        note = " ".join(shown(b) for b in levels)
        lines.append(
            f'    key <{key.physical.xkb}> {{ type[Group1] = "{type_name}", '
            f"symbols[Group1] = [ {syms} ] }};  // {note}"
        )
    lines.append("")
    for key in layout.keypad:
        type_name, syms = keypad_levels(key, dead_syms)
        note = " ".join(shown(key.pc_layers[layer]) for layer in ("option", "shift-option"))
        lines.append(
            f'    key <{key.physical.xkb}> {{ type[Group1] = "{type_name}", '
            f"symbols[Group1] = [ {', '.join(syms)} ] }};  // {note}"
        )
    lines += ["", '    include "level3(ralt_switch)"', "};"]
    return "\n".join(lines) + "\n"


KEYPAD_TYPE = "FOUR_LEVEL_MIXED_KEYPAD"


def keypad_levels(key, dead_syms: dict) -> tuple[str, list]:
    """(XKB type, keysyms per level) for a number pad key."""
    nav, char = key.physical.xkb_syms
    type_name = KEYPAD_TYPE if nav != char else "FOUR_LEVEL"
    extra = [binding_keysym(key.pc_layers[layer], dead_syms) for layer in ("option", "shift-option")]
    return type_name, [nav, char, *extra]


def xkb_description(layout: Layout) -> str:
    return f"English ({layout.name})"


def typed_keysyms(layout: Layout) -> list:
    """[(keysym, binding)] for everything a key types, without duplicates,
    in keyboard order."""
    dead_syms = dead_keysyms(layout)
    seen, result = set(), []
    for key in layout.keys:
        for layer in ALL_LAYERS:
            binding = layout.binding(key, layer, "pc")
            if binding is None:
                continue
            keysym = binding_keysym(binding, dead_syms)
            if keysym not in seen:
                seen.add(keysym)
                result.append((keysym, binding))
    # The number pad: its character with Num Lock on, and the alternative layer
    for key in layout.keypad:
        for layer, binding in key.pc_layers.items():
            if binding is None or layer == "shift":
                continue
            keysym = key.physical.xkb_syms[1] if layer == "base" else binding_keysym(binding, dead_syms)
            if keysym not in seen:
                seen.add(keysym)
                result.append((keysym, binding))
    return result


def compose_result(layout: Layout, dead, binding) -> str:
    """What the dead key followed by `binding` types."""
    if isinstance(binding, Dead):
        return dead.symbol + layout.dead[binding.id].symbol
    if binding.text in dead.map:
        return dead.map[binding.text]
    return dead.symbol + binding.text


def compose_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def compose(layout: Layout) -> str:
    """The Compose file for the dead keys."""
    dead_syms = dead_keysyms(layout)
    typed = typed_keysyms(layout)
    lines = [
        f"# {layout.name} keyboard layout: dead keys",
        "#",
        "# Generated from layout.toml by layoutgen. Do not edit.",
        "#",
        f"# {layout.copyright_notice}. {layout.license} License.",
        "#",
        "# Include this file from your Compose file (~/.XCompose), after",
        '# include "%L". Every key typed after a dead key has a sequence: the',
        "# dead key's result for it, or else the dead key's symbol followed by",
        "# the key's character.",
    ]
    for dead in layout.dead.values():
        lines += ["", f"# {dead.name} ({dead_syms[dead.id]}): {dead.desc}"]
        for keysym, binding in typed:
            if isinstance(binding, Char) and not in_compose_tables(binding.text):
                continue
            if layout.chain(dead.id, binding):
                continue  # starts a chained dead key: its sequences are below
            result = compose_result(layout, dead, binding)
            lines.append(f"<{dead_syms[dead.id]}> <{keysym}> : {compose_string(result)}")
    # A chained dead key: its two dead keysyms, then every key
    for (first, second), chain in layout.chains.items():
        prefix = f"<{dead_syms[first]}> <{dead_syms[second]}>"
        lines += ["", f"# {chain.name} ({dead_syms[first]}, then {dead_syms[second]}): {chain.desc}"]
        for keysym, binding in typed:
            if isinstance(binding, Char) and not in_compose_tables(binding.text):
                continue
            result = compose_result(layout, chain, binding)
            lines.append(f"{prefix} <{keysym}> : {compose_string(result)}")
    return "\n".join(lines) + "\n"


def registry(layout: Layout) -> str:
    """rules/evdev.xml entry, so that settings programs list the layout."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE xkbConfigRegistry SYSTEM "xkb.dtd">\n'
        '<xkbConfigRegistry version="1.1">\n'
        "  <layoutList>\n"
        "    <layout>\n"
        "      <configItem>\n"
        f"        <name>{layout.id}</name>\n"
        f"        <shortDescription>{layout.language}</shortDescription>\n"
        f"        <description>{escape(xkb_description(layout))}</description>\n"
        "        <languageList>\n"
        "          <iso639Id>eng</iso639Id>\n"
        "        </languageList>\n"
        "      </configItem>\n"
        "    </layout>\n"
        "  </layoutList>\n"
        "</xkbConfigRegistry>\n"
    )


def write(layout: Layout, output: Path) -> None:
    """Symbols, Compose file, registry, install script, and README in `output`."""
    output.mkdir(parents=True, exist_ok=True)
    (output / layout.id).write_text(symbols(layout), encoding="utf-8")
    (output / f"{layout.id}.compose").write_text(compose(layout), encoding="utf-8")
    (output / "evdev.xml").write_text(registry(layout), encoding="utf-8")
    templates = files("layoutgen").joinpath("templates/linux")
    for name in ("install.py", "README.txt"):
        text = templates.joinpath(name).read_text(encoding="utf-8")
        text = text.replace("@@ID@@", layout.id).replace("@@NAME@@", layout.name)
        (output / name).write_text(text, encoding="utf-8")
    (output / "install.py").chmod(0o755)
