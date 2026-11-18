"""Keyboard diagrams (SVG) of the alternative layer and of each dead key.

Every key shows what it types with Shift (top) and without (bottom), like
the legends on a keycap, with the key's US label small in the corner. Dead
keys show their symbol on a dark badge; in a dead key's diagram, the key
that triggers it is highlighted. The diagrams show a US (ANSI) keyboard with
macOS conventions.

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
  .unused { fill: #f4f4f4; stroke: #d6d6d6; }
  .out { fill: #111111; }
  .dead-out { fill: #ffffff; }
  .label { fill: #8a8a8a; }
  .note { fill: #5a5a5a; }
  .bg { fill: #f8f8f8; }
  @media (prefers-color-scheme: dark) {
    .bg { fill: #1e1e1e; }
    .key { fill: #2d2d2d; stroke: #5c5c5c; }
    .frame { fill: #262626; stroke: #444444; }
    .unused { fill: #232323; stroke: #3a3a3a; }
    .badge { fill: #c8c8c8; }
    .dead-out { fill: #111111; }
    .active { fill: #8a6a10; stroke: #c99a17; }
    .out { fill: #eeeeee; }
    .label { fill: #8a8a8a; }
    .note { fill: #b0b0b0; }
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


# Font sizes in pixels
SIZES = {"out": 22, "label": 10, "note": 10}


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
            self.glyphs[self.glyph(c)].width for c in text if not unicodedata.combining(c)
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
            if self.font.path(name):
                gid = self.used.setdefault(name, f"g{len(self.used)}")
                uses.append(f'<use href="#{gid}" transform="translate({gx:.1f} {y:.1f}) scale({scale:.5f} {-scale:.5f})"/>')
            if not mark:
                base_x = x
                x += self.font.glyphs[name].width * scale
        return f'<g class="{cls}">' + "".join(uses) + "</g>"

    def defs(self) -> str:
        paths = "".join(f'<path id="{gid}" d="{self.font.path(name)}"/>' for name, gid in self.used.items())
        return f"<defs>{paths}</defs>"


def diagram(layout: Layout, font: Font, title: str, legends, active=None) -> str:
    """SVG for one view. `legends(key)` gives (top, bottom) for a key, each
    None (nothing), ("char", text), or ("dead", DeadKey)."""
    drawing = Drawing(font)
    _text = drawing.text
    width, height = 15 * U + 2 * PAD, 5 * U + 2 * PAD + 26
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">',
        f"<title>{escape(title)}</title>",
        f"<style>{STYLE}</style>",
        f'<rect class="bg" x="0" y="0" width="{width}" height="{height}" rx="10"/>',
    ]
    top = PAD + 26
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
        upper, lower = legends(key)
        if active is not None and key.name == active:
            cls = "key active"
        elif upper is None and lower is None:
            cls = "key unused"
        else:
            cls = "key"
        parts.append(_box(x, y, w, cls))
        parts.append(_text(x + w * U - 7, y + 15, _key_label(physical), "label", "end"))
        for legend, ly in ((upper, y + 26), (lower, y + U - 12)):
            if legend is None:
                continue
            kind, value = legend
            if kind == "dead":
                parts.append(
                    f'<rect class="badge" x="{x + 5:.1f}" y="{ly - 19:.1f}" width="28" height="25" rx="5"/>'
                )
                parts.append(_text(x + 19, ly, display(value.symbol), "out dead-out", "middle"))
            elif short_note(value):
                parts.append(_text(x + 9, ly - 2, short_note(value), "note"))
            else:
                parts.append(_text(x + 9, ly, display(value), "out"))
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


def alternative(layout: Layout, font: Font) -> str:
    def legends(key):
        dead = lambda b: _legend(b) if not isinstance(b, Dead) else ("dead", layout.dead[b.id])  # noqa: E731
        upper = key.layers["shift-option"] if key.physical.shift != key.physical.base else None
        return dead(upper) if upper is not None else None, dead(key.layers["option"])

    return diagram(layout, font, "Alternative layer: Option (macOS) or AltGr (Windows, Linux); top: with Shift", legends)


def dead_key(layout: Layout, font: Font, dead_id: str) -> str:
    dead = layout.dead[dead_id]

    def legends(key):
        upper = key.layers["shift"] if key.physical.shift != key.physical.base else None
        lower = key.layers["base"]
        if key.name == "space":
            return None, ("char", dead.map[" "]) if " " in dead.map else None
        return _legend(upper, dead.map), _legend(lower, dead.map)

    trigger = next(
        key.name for key in layout.keys
        for layer in ("option", "shift-option")
        if isinstance(key.layers[layer], Dead) and key.layers[layer].id == dead_id
    )
    return diagram(layout, font, f"Dead key: {dead.name} ({dead.desc})", legends, active=trigger)


def all_diagrams(layout: Layout, font_path: Path = DEFAULT_FONT) -> dict:
    """{file name: SVG} for all diagrams."""
    font = Font(font_path)
    result = {"alternative.svg": alternative(layout, font)}
    for dead_id in layout.dead:
        result[f"dead-{dead_id}.svg"] = dead_key(layout, font, dead_id)
    return result
