"""Keyboard diagrams (SVG) of the alternative layer and of each dead key.

Every key shows what it types with Shift (top) and without (bottom), like
the legends on a keycap, with the key's US label small in the corner. Dead
keys show their symbol on a dark badge; in a dead key's diagram, the key
that triggers it is highlighted; with `option=True` (the cheat sheet), a
dead key's diagram has a second column on each key for what it gives with
Option. The diagrams show a US (ANSI) keyboard with macOS conventions.

All text is drawn as glyph outlines from a font file (JuliaMono), so the
diagrams look the same everywhere without the font being installed, and no
font software is distributed with them.
"""

import unicodedata
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

from .model import Char, Dead, Layout

DEFAULT_FONT = Path("fonts/JuliaMono-Regular.ttf")

U = 60  # key unit in pixels
GAP = 4
PAD = 8

# Keys without characters, for the outline of the keyboard: (row, col, width, label)
FRAME = [
    (0, 13, 2, "delete"),
    (1, 0, 1.5, "tab"),
    (2, 0, 1.75, "caps lock"),
    (2, 12.75, 2.25, "return"),
    (3, 0, 2.25, "shift"),
    (3, 12.25, 2.75, "shift"),
]
SPACE = (4, 3.75, 6.25)

STYLE = """
  .key { fill: #ffffff; stroke: #9a9a9a; stroke-width: 1; }
  .frame { fill: #ececec; stroke: #c4c4c4; stroke-width: 1; }
  .badge { fill: #4a4a4a; }
  .active { fill: #f6c445; stroke: #c99a17; }
  .marked { stroke: #111111; stroke-width: 1.5; }
  .unused { fill: #f4f4f4; stroke: #d6d6d6; }
  .out { fill: #111111; }
  .dead-out { fill: #ffffff; }
  .label { fill: #8a8a8a; }
  .note { fill: #5a5a5a; }
  .hint { fill: #bdbdbd; }
  .bg { fill: #f8f8f8; }
  @media (prefers-color-scheme: dark) {
    .bg { fill: #1e1e1e; }
    .key { fill: #2d2d2d; stroke: #5c5c5c; }
    .frame { fill: #262626; stroke: #444444; }
    .unused { fill: #232323; stroke: #3a3a3a; }
    .badge { fill: #c8c8c8; }
    .dead-out { fill: #111111; }
    .active { fill: #8a6a10; stroke: #c99a17; }
    .marked { stroke: #eeeeee; }
    .out { fill: #eeeeee; }
    .label { fill: #8a8a8a; }
    .note { fill: #b0b0b0; }
    .hint { fill: #5a5a5a; }
  }
"""


def display(text: str) -> str:
    """How a character is drawn: combining marks on a dotted circle."""
    if text and unicodedata.combining(text[0]):
        return "◌" + text
    return text


def short_note(text: str) -> str | None:
    """A small text label for characters that don't show up when drawn."""
    if text == " ":
        return "nbsp"
    return None


def _key_label(physical) -> str:
    if physical.name == "space":
        return ""
    if physical.base.isalpha():
        return physical.base.upper()
    return f"{physical.shift} {physical.base}"


def _box(x, y, w, cls):
    return (
        f'<rect class="{cls}" x="{x + GAP / 2:.1f}" y="{y + GAP / 2:.1f}" '
        f'width="{w * U - GAP:.1f}" height="{U - GAP}" rx="6"/>'
    )


# Glyphs that JuliaMono squeezes into one cell, so that they look like their
# short or binary counterparts (⟶ like →, ⨁ like ⊕): (horizontal, vertical)
# scale. The long arrows are stretched, the n-ary operators enlarged.
STRETCH = dict.fromkeys("⟵⟶⟷⟸⟹⟺⟻⟼", (1.6, 1.0)) | dict.fromkeys("⨀⨁⨂⨃⨄⋂⋃⋀⋁", (1.3, 1.3))

# Font sizes in pixels
SIZES = {"out": 22, "label": 10, "note": 10, "box": 20, "opt": 17, "hint": 10}


class Font:
    """Glyph outlines from a font file."""

    def __init__(self, path: Path):
        if not Path(path).exists():
            raise FileNotFoundError(f"{path} is missing; run `make fonts`")
        self.font = TTFont(str(path))
        self.cmap = self.font.getBestCmap()
        self.glyphs = self.font.getGlyphSet()
        self.upm = self.font["head"].unitsPerEm
        self.paths = {}  # glyph name -> SVG path data

    def glyph(self, char: str) -> str:
        if ord(char) not in self.cmap:
            raise ValueError(f"the font has no glyph for {char!r} (U+{ord(char):04X})")
        return self.cmap[ord(char)]

    def path(self, name: str) -> str:
        if name not in self.paths:
            pen = SVGPathPen(self.glyphs)
            self.glyphs[name].draw(pen)
            self.paths[name] = pen.getCommands()
        return self.paths[name]

    def width(self, text: str, size: float) -> float:
        return sum(
            self.glyphs[self.glyph(c)].width * STRETCH.get(c, (1, 1))[0]
            for c in text if not unicodedata.combining(c)
        ) * size / self.upm


class Drawing:
    """Collects the glyphs one SVG uses, to define each of them once."""

    def __init__(self, font: Font):
        self.font = font
        self.used = {}  # glyph name -> id

    def text(self, x, y, text, cls, anchor="start"):
        size = SIZES[cls.split()[0]]
        if anchor != "start":
            x -= self.font.width(text, size) / (2 if anchor == "middle" else 1)
        scale = size / self.font.upm
        uses = []
        base_x = x
        for c in text:
            name = self.font.glyph(c)
            # In a monospaced font, a combining mark is centered in a full
            # cell; drawn at the preceding character's position, it sits on it.
            mark = unicodedata.combining(c) > 0
            gx = base_x if mark else x
            sx, sy = STRETCH.get(c, (1, 1))
            if self.font.path(name):
                gid = self.used.setdefault(name, f"g{len(self.used)}")
                uses.append(
                    f'<use href="#{gid}" transform="translate({gx:.1f} {y:.1f}) '
                    f'scale({scale * sx:.5f} {-scale * sy:.5f})"/>'
                )
            if not mark:
                base_x = x
                x += self.font.glyphs[name].width * scale * sx
        return f'<g class="{cls}">' + "".join(uses) + "</g>"

    def defs(self) -> str:
        paths = "".join(f'<path id="{gid}" d="{self.font.path(name)}"/>' for name, gid in self.used.items())
        return f"<defs>{paths}</defs>"


def _draw_key(drawing: Drawing, x, y, w, physical, legends, active=False, marked=False) -> list:
    """SVG elements of one key at (x, y), `w` units wide. `legends` is
    (top, bottom) or, with the Option column, (top, bottom, Option top,
    Option bottom); see `diagram` and `_option_legend`. A marked key has a
    black outline (the key the cheat sheet's legend explains)."""
    _text = drawing.text
    upper, lower, *option = legends
    if active:
        cls = "key active"
    elif upper is None and lower is None and all(o is None for o in option):
        cls = "key unused"
    else:
        cls = "key"
    if marked:
        cls += " marked"
    parts = [_box(x, y, w, cls), _text(x + w * U - 7, y + 15, _key_label(physical), "label", "end")]
    for legend, ly in zip(option, (y + 31, y + U - 11)):
        if legend is None:
            continue
        _, value, *hint = legend
        ox = x + 31
        parts.append(_text(ox, ly, display(value), "opt out"))
        if hint:
            hx = ox + drawing.font.width(display(value), SIZES["opt"]) + 1
            parts.append(_text(hx, ly, display(hint[0]), "hint"))
    for legend, ly in ((upper, y + 26), (lower, y + U - 12)):
        if legend is None:
            continue
        kind, value = legend
        if kind == "dead":
            parts.append(f'<rect class="badge" x="{x + 5:.1f}" y="{ly - 19:.1f}" width="28" height="25" rx="5"/>')
            parts.append(_text(x + 19, ly, display(value.symbol), "out dead-out", "middle"))
        elif short_note(value):
            parts.append(_text(x + 9, ly - 2, short_note(value), "note"))
        else:
            parts.append(_text(x + 9, ly, display(value), "out"))
    return parts


def diagram(layout: Layout, font: Font, title: str, legends, active=None, compact=False, marked=None) -> str:
    """SVG for one view. `legends(key)` gives (top, bottom) for a key, each
    None (nothing), ("char", text), or ("dead", DeadKey), and for a dead key
    with an Option column, also (Option top, Option bottom); see
    `_option_legend`. A compact diagram (for the cheat sheet) has no title
    line. `active` and `marked` are key names (see `_draw_key`)."""
    drawing = Drawing(font)
    _text = drawing.text
    title_height = 0 if compact else 26
    width, height = 15 * U + 2 * PAD, 5 * U + 2 * PAD + title_height
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">',
        f"<title>{escape(title)}</title>",
        f"<style>{STYLE}</style>",
        f'<rect class="bg" x="0" y="0" width="{width}" height="{height}" rx="10"/>',
    ]
    top = PAD + title_height
    if not compact:
        parts.append(_text(PAD + 4, PAD + 16, title, "note"))
    for row, col, w, label in FRAME:
        x, y = PAD + col * U, top + row * U
        parts.append(_box(x, y, w, "frame"))
        parts.append(_text(x + 8, y + U - 10, label, "label"))
    for key in layout.keys:
        physical = key.physical
        if physical.name == "iso":
            continue  # not on US (ANSI) keyboards
        if physical.name == "space":
            row, col, w = SPACE
        else:
            row, col, w = physical.row, physical.col, 1
        x, y = PAD + col * U, top + row * U
        parts += _draw_key(
            drawing, x, y, w, physical, legends(key), active is not None and key.name == active,
            marked is not None and key.name == marked,
        )
    parts.insert(3, drawing.defs())
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _legend(binding, dead_map=None):
    if binding is None:
        return None
    if isinstance(binding, Dead):
        return None if dead_map is not None else ("dead", binding)
    if dead_map is None:
        return ("char", binding.text)
    if binding.text in dead_map:
        return ("char", dead_map[binding.text])
    return None


def alternative(layout: Layout, font: Font, compact=False) -> str:
    def legends(key):
        dead = lambda b: _legend(b) if not isinstance(b, Dead) else ("dead", layout.dead[b.id])  # noqa: E731
        upper = key.layers["shift-option"] if key.physical.shift != key.physical.base else None
        return dead(upper) if upper is not None else None, dead(key.layers["option"])

    return diagram(
        layout, font, "Alternative layer: Option (macOS) or AltGr (Windows, Linux); top: with Shift", legends,
        compact=compact,
    )


def _option_legend(binding, dead_map, no_hint=frozenset()):
    """What a key with Option gives after the dead key, in the Option column:
    ("char", result), or ("char", result, hint) when the entry is keyed by a
    symbol, which the result builds on (`⟹` after `⇒`); it is drawn small
    and gray behind the result. An entry keyed by a letter (`⊏` after `ç`)
    goes by the key's other legends (`⊂`) instead, and so does one keyed by a
    symbol in `no_hint` (the dead key's `no-hint`)."""
    if not isinstance(binding, Char) or binding.text not in dead_map:
        return None
    result = dead_map[binding.text]
    if unicodedata.category(binding.text).startswith("L") or binding.text in no_hint:
        return ("char", result)
    return ("char", result, binding.text)


def _dead_legends(layout: Layout, dead_id: str, option=False):
    """The dead key's trigger key and `legends(key)` for its diagram (see
    `dead_key`)."""
    dead = layout.dead[dead_id]
    trigger = next(
        key.name for key in layout.keys
        for layer in ("option", "shift-option")
        if isinstance(key.layers[layer], Dead) and key.layers[layer].id == dead_id
    )

    def legends(key):
        upper = key.layers["shift"] if key.physical.shift != key.physical.base else None
        lower = key.layers["base"]
        if key.name == "space":
            return None, ("char", dead.map[" "]) if " " in dead.map else None
        result = (_legend(upper, dead.map), _legend(lower, dead.map))
        if not option or key.name == trigger:
            return result
        option_upper = key.layers["shift-option"] if upper is not None else None
        return result + (
            _option_legend(option_upper, dead.map, dead.no_hint),
            _option_legend(key.layers["option"], dead.map, dead.no_hint),
        )

    return trigger, legends


def dead_key(layout: Layout, font: Font, dead_id: str, compact=False, option=False, marked=None) -> str:
    """With `option`, each key has a second column on the right, for what it
    gives with Option after the dead key (see `_option_legend`). `marked` is
    what a key types, for a key with a black outline (see `single_key`)."""
    dead = layout.dead[dead_id]
    trigger, legends = _dead_legends(layout, dead_id, option)
    marked_name = next(key.name for key in layout.keys if key.physical.base == marked) if marked else None
    return diagram(
        layout, font, f"Dead key: {dead.name} ({dead.desc})", legends, active=trigger, compact=compact,
        marked=marked_name,
    )


def single_key(layout: Layout, font: Font, dead_id: str, base: str) -> str:
    """SVG of one key of a dead key's diagram, the one that types `base`, to
    explain the legends (the cheat sheet's legend), marked like in the
    diagram with `marked=base`."""
    key = next(key for key in layout.keys if key.physical.base == base)
    _, legends = _dead_legends(layout, dead_id, option=True)
    drawing = Drawing(font)
    parts = _draw_key(drawing, 0, 0, 1, key.physical, legends(key), marked=True)
    size = U - GAP + 2  # with room for the outline
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="{GAP / 2 - 1} {GAP / 2 - 1} {size} {size}" role="img">',
        f"<style>{STYLE}</style>",
        drawing.defs(),
        *parts,
        "</svg>",
    ]) + "\n"


# Number pad keys bigger than 1x1: name -> (width, height); positions from keys.KEYPAD
KEYPAD_SIZES = {"kp+": (1, 2), "kp0": (2, 1)}
# Keys without characters: (row, col, width, height, label)
KEYPAD_FRAME = [(0, 0, 1, 1, "num lock"), (3, 3, 1, 2, "enter")]


def numpad(layout: Layout, font: Font, compact=False, layer=None, dead=None) -> str:
    """SVG of the number pad with Option (left) and Shift+Option (right).
    Box drawing characters are as tall as the font's whole line, to connect
    from line to line, so they go side by side instead of one above the other.
    With `layer` ("option" or "shift-option"), only that layer, centered.
    With `dead` (a dead key id), what the number pad types after that dead
    key (it acts like the main keys that type the same characters)."""
    drawing = Drawing(font)
    _text = drawing.text
    if dead is not None:
        title = f"{layout.dead[dead].name} dead key, then the number pad"
    else:
        title = {
            None: "Option or AltGr; right: with Shift",
            "option": "Option or AltGr",
            "shift-option": "Shift+Option or Shift+AltGr",
        }[layer]
    title_height = 0 if compact else 26
    width, height = 4 * U + 2 * PAD, 5 * U + 2 * PAD + title_height
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">',
        f"<title>{escape(title)}</title>",
        f"<style>{STYLE}</style>",
        f'<rect class="bg" x="0" y="0" width="{width}" height="{height}" rx="10"/>',
    ]
    top = PAD + title_height
    if not compact:
        parts.append(_text(PAD + 4, PAD + 16, title, "note"))

    def box(row, col, w, h, cls):
        x, y = PAD + col * U, top + row * U
        parts.append(
            f'<rect class="{cls}" x="{x + GAP / 2:.1f}" y="{y + GAP / 2:.1f}" '
            f'width="{w * U - GAP:.1f}" height="{h * U - GAP:.1f}" rx="6"/>'
        )
        return x, y

    for row, col, w, h, label in KEYPAD_FRAME:
        x, y = box(row, col, w, h, "frame")
        parts.append(_text(x + 8, y + h * U - 10, label, "label"))
    for key in layout.keypad:
        physical = key.physical
        w, h = KEYPAD_SIZES.get(physical.name, (1, 1))
        left, right = key.layers["option"], key.layers["shift-option"]
        if dead is not None:
            used = physical.base in layout.dead[dead].map
        elif layer is not None:
            used = key.layers[layer] is not None
        else:
            used = left or right
        x, y = box(physical.row, physical.col, w, h, "key" if used else "key unused")
        parts.append(_text(x + w * U - 7, y + 15, physical.base, "label", "end"))
        baseline = y + h * U / 2 + 12  # below the label
        if dead is not None:
            result = layout.dead[dead].map.get(physical.base)
            if result is not None:
                parts.append(_text(x + w * U / 2, baseline, display(result), "out", "middle"))
            continue
        if layer is not None:
            binding = key.layers[layer]
            if binding is not None:
                parts.append(_text(x + w * U / 2, baseline, display(binding.text), "box out", "middle"))
            continue
        for binding, lx in ((left, x + 9), (right, x + 31)):
            if binding is not None:
                parts.append(_text(lx, baseline, display(binding.text), "box out"))
    parts.insert(3, drawing.defs())
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def all_diagrams(layout: Layout, font_path: Path = DEFAULT_FONT, compact=False, option=False) -> dict:
    """{file name: SVG} for all diagrams; `option` is the dead keys' Option
    column (see `dead_key`)."""
    font = Font(font_path)
    result = {"alternative.svg": alternative(layout, font, compact)}
    for dead_id in layout.dead:
        result[f"dead-{dead_id}.svg"] = dead_key(layout, font, dead_id, compact, option)
    if layout.keypad:
        result["numpad.svg"] = numpad(layout, font, compact)
    return result
