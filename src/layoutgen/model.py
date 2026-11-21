"""Load and validate layout.toml."""

import re
import tomllib
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from .keys import KEYPAD, KEYPAD_BY_CHAR, KEYS, PhysicalKey

LAYERS = ("base", "shift", "option", "shift-option")
# Caps Lock layers, derived from the others
CAPS_LAYERS = ("caps", "caps-option")


class LayoutError(ValueError):
    pass


@dataclass(frozen=True)
class Char:
    text: str
    desc: str = ""

    @property
    def combining(self) -> bool:
        return len(self.text) == 1 and unicodedata.combining(self.text) > 0


@dataclass(frozen=True)
class Dead:
    id: str


@dataclass
class DeadKey:
    id: str
    name: str
    desc: str
    symbol: str
    windows_symbol: str
    map: dict  # typed character -> result
    table: bool = False  # list the entries in a table in the README
    notes: dict = field(default_factory=dict)  # result -> description
    readme: str = ""  # paragraph for the README section
    # typed characters (after Option) whose result doesn't build on them, so
    # the cheat sheet doesn't show them small and gray behind it
    no_hint: frozenset = frozenset()


@dataclass
class Key:
    physical: PhysicalKey
    layers: dict  # layer -> Char | Dead | None, on macOS
    pc_layers: dict  # the same on Windows and Linux

    @property
    def name(self) -> str:
        return self.physical.name


@dataclass
class Layout:
    name: str
    id: str
    version: str
    author: str
    copyright: str
    license: str
    language: str
    macos_bundle_id: str
    macos_id: int
    windows_dll: str
    keys: list = field(default_factory=list)  # Key, in keyboard order
    keypad: list = field(default_factory=list)  # Key of the number pad (layer "shift": Shift+digit, macOS)
    dead: dict = field(default_factory=dict)  # id -> DeadKey, in file order

    @property
    def numeric_version(self) -> str:
        """`version` without a "-dev" or "+dev" suffix, for the platforms that
        only take numbers (macOS bundle, Keyman, Windows file version)."""
        return re.sub(r"[+-]dev$", "", self.version)

    def binding(self, key: Key, layer: str, platform: str = "mac"):
        """What `key` does in `layer` on `platform` ("mac" or "pc"),
        including the derived Caps Lock layers."""
        layers = key.layers if platform == "mac" else key.pc_layers
        if layer == "caps":
            return layers["shift"] if _caps_shifts(layers, "base", "shift") else layers["base"]
        if layer == "caps-option":
            if _caps_shifts(layers, "option", "shift-option"):
                return layers["shift-option"]
            return layers["option"]
        return layers[layer]

    def dead_result(self, dead: DeadKey, binding):
        """Result of `binding` after the dead key: Char, or None (no entry)."""
        if isinstance(binding, Char) and binding.text in dead.map:
            return Char(dead.map[binding.text])
        return None

    @property
    def copyright_notice(self) -> str:
        return f"© {self.copyright} {self.author}"


def _caps_shifts(layers: dict, lower: str, upper: str) -> bool:
    lo, up = layers[lower], layers[upper]
    return (
        isinstance(lo, Char)
        and isinstance(up, Char)
        and len(lo.text) == 1
        and lo.text.islower()
        and up.text == lo.text.upper()
    )


def load(path: Path) -> Layout:
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    unknown = set(data) - {"layout", "alternative", "dead", "notes", "numpad"}
    if unknown:
        raise LayoutError(f"unknown tables {sorted(unknown)}")
    meta = data.get("layout", {})
    try:
        layout = Layout(
            name=meta["name"],
            id=meta["id"],
            version=meta["version"],
            author=meta["author"],
            copyright=str(meta["copyright"]),
            license=meta["license"],
            language=meta["language"],
            macos_bundle_id=meta["macos-bundle-id"],
            macos_id=int(meta["macos-id"]),
            windows_dll=meta["windows-dll"],
        )
    except KeyError as exc:
        raise LayoutError(f"[layout] is missing {exc}") from None
    # A release, or between releases "+dev" (after the last release) or "-dev" (before the next)
    if not re.fullmatch(r"\d+\.\d+\.\d+([+-]dev)?", layout.version):
        raise LayoutError(f"version {layout.version!r} is not X.Y.Z, X.Y.Z+dev, or X.Y.Z-dev")

    # Typed character (without Option) -> (physical key, Option layer)
    positions = {}
    for physical in KEYS:
        positions.setdefault(physical.base, []).append((physical, "option"))
        positions.setdefault(physical.shift, []).append((physical, "shift-option"))
    notes = data.get("notes", {})

    bindings = {}  # (key name, layer) -> Char | Dead

    def assign(typed, binding, where):
        if typed not in positions:
            raise LayoutError(f"{where}: no key types {typed!r} without Option")
        for physical, layer in positions[typed]:
            if (physical.name, layer) in bindings:
                raise LayoutError(f"{where}: Option+{typed!r} is defined twice")
            bindings[(physical.name, layer)] = binding

    for typed, text in data.get("alternative", {}).items():
        if not isinstance(text, str) or not text:
            raise LayoutError(f"[alternative] {typed!r}: expected a non-empty string")
        assign(typed, Char(text, notes.get(text, "")), f"[alternative] {typed!r}")

    for dead_id, spec in data.get("dead", {}).items():
        where = f"[dead.{dead_id}]"
        unknown = set(spec) - {"key", "name", "desc", "symbol", "windows-symbol", "map", "table", "notes", "readme", "no-hint"}
        if unknown:
            raise LayoutError(f"{where}: unknown fields {sorted(unknown)}")
        for required in ("key", "symbol", "map"):
            if required not in spec:
                raise LayoutError(f"{where}: missing {required!r}")
        alternatives = [*data.get("alternative", {}).values()]
        alternatives += [v for layer in data.get("numpad", {}).values() for v in layer.values()]
        for typed in spec["map"]:
            if typed not in positions and typed not in alternatives:
                raise LayoutError(f"{where}.map: no key types {typed!r}")
        layout.dead[dead_id] = DeadKey(
            id=dead_id,
            name=spec.get("name", dead_id),
            desc=spec.get("desc", ""),
            symbol=spec["symbol"],
            windows_symbol=spec.get("windows-symbol", spec["symbol"]),
            # Space after a dead key types its symbol, unless defined otherwise
            map={" ": spec["symbol"], **spec["map"]},
            table=bool(spec.get("table", False)),
            notes=spec.get("notes", {}),
            readme=spec.get("readme", "").strip(),
            no_hint=frozenset(spec.get("no-hint", [])),
        )
        for typed in layout.dead[dead_id].no_hint:
            if typed not in spec["map"]:
                raise LayoutError(f"{where}.no-hint: {typed!r} is not in the map")
        for result in layout.dead[dead_id].notes:
            if result not in spec["map"].values():
                raise LayoutError(f"{where}.notes: {result!r} is not a result of the dead key")
        assign(spec["key"], Dead(dead_id), f"{where} key")

    for physical in KEYS:
        pc_layers = {
            "base": Char(physical.pc_base or physical.base),
            "shift": Char(physical.pc_shift or physical.shift),
        }
        layers = {"base": Char(physical.base), "shift": Char(physical.shift)}
        for layer, default in zip(("option", "shift-option"), physical.mac_alternative):
            binding = bindings.get((physical.name, layer))
            pc_layers[layer] = binding
            layers[layer] = binding if binding is not None or default is None else Char(default)
        layout.keys.append(Key(physical, layers, pc_layers))

    # The number pad: the plain layer types the key's character (digits with
    # Num Lock on); Shift does too on macOS, but switches Num Lock on Windows
    # and Linux, so it isn't a character layer there.
    numpad = data.get("numpad", {})
    unknown = set(numpad) - {"option", "shift-option"}
    if unknown:
        raise LayoutError(f"[numpad]: unknown layers {sorted(unknown)}")
    for layer, table in numpad.items():
        for typed, text in table.items():
            if typed not in KEYPAD_BY_CHAR:
                raise LayoutError(f"[numpad.{layer}]: no number pad key types {typed!r}")
            if not isinstance(text, str) or not text:
                raise LayoutError(f"[numpad.{layer}] {typed!r}: expected a non-empty string")
    for physical in KEYPAD:
        option = {
            layer: Char(numpad[layer][physical.base], notes.get(numpad[layer][physical.base], ""))
            if physical.base in numpad.get(layer, {}) else None
            for layer in ("option", "shift-option")
        }
        char = Char(physical.base)
        layout.keypad.append(Key(
            physical,
            {"base": char, "shift": char, **option},
            {"base": char, "shift": None, **option},
        ))
    return layout
