"""Load and validate layout.toml."""

import tomllib
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from .keys import KEYS, PhysicalKey

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


@dataclass
class Key:
    physical: PhysicalKey
    layers: dict  # layer -> Char | Dead | None

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
    dead: dict = field(default_factory=dict)  # id -> DeadKey, in file order

    def binding(self, key: Key, layer: str):
        """What `key` does in `layer`, including the derived Caps Lock layers."""
        if layer == "caps":
            return key.layers["shift"] if _caps_shifts(key, "base", "shift") else key.layers["base"]
        if layer == "caps-option":
            if _caps_shifts(key, "option", "shift-option"):
                return key.layers["shift-option"]
            return key.layers["option"]
        return key.layers[layer]

    def dead_result(self, dead: DeadKey, binding):
        """Result of `binding` after the dead key: Char, or None (no entry)."""
        if isinstance(binding, Char) and binding.text in dead.map:
            return Char(dead.map[binding.text])
        return None

    @property
    def copyright_notice(self) -> str:
        return f"© {self.copyright} {self.author}"


def _caps_shifts(key: Key, lower: str, upper: str) -> bool:
    lo, up = key.layers[lower], key.layers[upper]
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
    unknown = set(data) - {"layout", "option", "dead", "notes"}
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

    for typed, text in data.get("option", {}).items():
        if not isinstance(text, str) or not text:
            raise LayoutError(f"[option] {typed!r}: expected a non-empty string")
        assign(typed, Char(text, notes.get(text, "")), f"[option] {typed!r}")

    for dead_id, spec in data.get("dead", {}).items():
        where = f"[dead.{dead_id}]"
        unknown = set(spec) - {"key", "name", "desc", "symbol", "windows-symbol", "map"}
        if unknown:
            raise LayoutError(f"{where}: unknown fields {sorted(unknown)}")
        for required in ("key", "symbol", "map"):
            if required not in spec:
                raise LayoutError(f"{where}: missing {required!r}")
        for typed in spec["map"]:
            if typed not in positions and not any(typed == v for v in data.get("option", {}).values()):
                raise LayoutError(f"{where}.map: no key types {typed!r}")
        layout.dead[dead_id] = DeadKey(
            id=dead_id,
            name=spec.get("name", dead_id),
            desc=spec.get("desc", ""),
            symbol=spec["symbol"],
            windows_symbol=spec.get("windows-symbol", spec["symbol"]),
            # Space after a dead key types its symbol, unless defined otherwise
            map={" ": spec["symbol"], **spec["map"]},
        )
        assign(spec["key"], Dead(dead_id), f"{where} key")

    for physical in KEYS:
        layers = {"base": Char(physical.base), "shift": Char(physical.shift)}
        for layer in ("option", "shift-option"):
            layers[layer] = bindings.get((physical.name, layer))
        layout.keys.append(Key(physical, layers))
    return layout
