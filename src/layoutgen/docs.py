"""Generated parts of README.md: the key tables and the dead-key sections.

README.md is written by hand except between marker comments

    <!-- BEGIN generated: NAME -->
    ...
    <!-- END generated: NAME -->

whose content `update_readme` replaces.
"""

import re
import sys
import unicodedata

from .model import Char, Dead, Layout
from .svg import display

DIAGRAM_DIR = "docs"


def code(text: str) -> str:
    """Markdown code span for `text`, also inside a table cell."""
    longest = max((len(m) for m in re.findall(r"`+", text)), default=0)
    fence = "`" * (longest + 1)
    pad = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{pad}{text}{pad}{fence}".replace("|", "\\|")


def keys(physical, shifted: bool) -> str:
    """Key notation like ⌥q, ⌥⇧q, ⌥Space."""
    label = "Space" if physical.name == "space" else physical.base
    return "⌥" + ("⇧" if shifted else "") + label


def describe(layout: Layout, text: str, dead=None, pair: bool = False) -> str:
    """Description of `text`: from the dead key's notes, the notes of the
    alternative layer, or the Unicode name (for an uppercase/lowercase
    `pair`, without "small")."""
    if dead is not None and text in dead.notes:
        return dead.notes[text]
    if len(text) == 1:
        note = layout_notes(layout).get(text)
        if note:
            return note
        name = unicodedata.name(text, "").lower()
        if pair:
            name = name.replace(" small ", " ").removeprefix("latin letter ")
        return re.sub(r"^greek (small |capital )?(letter )?", "Greek ", name)
    return ""


def layout_notes(layout: Layout) -> dict:
    notes = {}
    for key in layout.keys:
        for binding in key.layers.values():
            if isinstance(binding, Char) and binding.desc:
                notes[binding.text] = binding.desc
    return notes


def anchor(text: str) -> str:
    """GitHub's anchor for a heading."""
    return re.sub(r"[^\w\- ]", "", text.lower()).replace(" ", "-")


def dead_heading(dead) -> str:
    return f"{dead.name} dead key"


def character_cell(text: str) -> str:
    if text == " ":
        return ""
    return code(display(text))


def alternative_tables(layout: Layout) -> str:
    out = []
    for shifted, title in ((False, "Option or AltGr"), (True, "Shift with Option or AltGr")):
        out += [f"#### {title}", "", "| Keys | Character | Description |", "|------|-----------|-------------|"]
        for key in layout.keys:
            physical = key.physical
            if shifted and physical.shift == physical.base:
                continue
            binding = key.layers["shift-option" if shifted else "option"]
            if binding is None or physical.name == "iso":
                continue
            if isinstance(binding, Dead):
                dead = layout.dead[binding.id]
                desc = f"dead key for {dead.desc} (see [{dead.name}](#{anchor(dead_heading(dead))}))"
                out.append(f"| {code(keys(physical, shifted))} | | {desc} |")
            else:
                out.append(
                    f"| {code(keys(physical, shifted))} | {character_cell(binding.text)} | "
                    f"{describe(layout, binding.text)} |"
                )
        out.append("")
    return "\n".join(out)


def dead_key_sections(layout: Layout) -> str:
    out = []
    # The keys the diagrams show (not the ISO key)
    drawn = [k for k in layout.keys if k.physical.name != "iso"]
    typed_on_keys = {k.physical.base for k in drawn} | {k.physical.shift for k in drawn}
    for dead in layout.dead.values():
        trigger = next(
            (key, layer) for key in layout.keys for layer in ("option", "shift-option")
            if isinstance(key.layers[layer], Dead) and key.layers[layer].id == dead.id
        )
        trigger_keys = keys(trigger[0].physical, trigger[1] == "shift-option")
        out += [
            f"### {dead_heading(dead)}",
            "",
            f"{code(trigger_keys)}, then a key: {dead.desc}. Space types {code(display(dead.symbol))}.",
            "",
            f"![{dead.name} dead key]({DIAGRAM_DIR}/dead-{dead.id}.svg)",
            "",
        ]
        if dead.readme:
            out += [dead.readme, ""]
        if dead.table:
            out += [dead_entries_table(layout, dead, drawn, typed_on_keys), ""]
            continue
        extras = []
        for typed, result in dead.map.items():
            if typed in typed_on_keys:
                continue
            for key in drawn:
                for layer in ("option", "shift-option"):
                    b = key.layers[layer]
                    if isinstance(b, Char) and b.text == typed:
                        extras.append(
                            f"{code(keys(key.physical, layer == 'shift-option'))} ({code(typed)}) "
                            f"gives {code(display(result))}"
                        )
        if extras:
            out += ["With an alternative character after the dead key: " + ", ".join(extras) + ".", ""]
    return "\n".join(out)


def dead_entries_table(layout: Layout, dead, drawn: list, typed_on_keys: set) -> str:
    """The entries of a dead key as a table, one row per result; a lowercase
    result and its uppercase form on the uppercase key share a row."""

    def typed_cell(typed: str) -> str:
        if typed in typed_on_keys:
            return code(typed)
        for key in drawn:
            for layer in ("option", "shift-option"):
                b = key.layers[layer]
                if isinstance(b, Char) and b.text == typed:
                    return f"{code(keys(key.physical, layer == 'shift-option'))} ({code(typed)})"
        raise ValueError(f"{dead.id}: no key types {typed!r}")

    # Results the alternative layer also types directly, with the key
    direct = {}
    for key in drawn:
        for layer in ("option", "shift-option"):
            b = key.layers[layer]
            if isinstance(b, Char):
                direct.setdefault(b.text, code(keys(key.physical, layer == "shift-option")))

    def also(results: list) -> str:
        on = [r for r in results if r in direct]
        if not on:
            return ""
        if len(results) == 1:
            return f"; also on {direct[on[0]]}"
        return "; " + ", ".join(f"{code(display(r))} also on {direct[r]}" for r in on)

    position = {typed: i for i, typed in enumerate(dead.map)}

    def rank(typed: str):
        """Map order, with an uppercase key right after its lowercase key."""
        return (position.get(typed.lower(), position[typed]), typed != typed.lower())

    by_result = {}  # result -> typed characters
    for typed, result in sorted(dead.map.items(), key=lambda item: rank(item[0])):
        if typed != " ":
            by_result.setdefault(result, []).append(typed)
    out = ["| Key | Symbol | Description |", "|-----|--------|-------------|"]
    done = set()
    for result, typed in by_result.items():
        if result in done:
            continue
        upper = result.upper()
        pair = (
            len(result) == 1 and len(upper) == 1 and upper != result
            and by_result.get(upper) == [t.upper() for t in typed]
        )
        results = [result, upper] if pair else [result]
        done.update(results)
        cells = [", ".join(typed_cell(t) for t in by_result[r]) for r in results]
        out.append(
            f"| {' / '.join(cells)} | {' '.join(code(display(r)) for r in results)} | "
            f"{describe(layout, result, dead, pair)}{also(results)} |"
        )
    return "\n".join(out)


def character_count(layout: Layout) -> str:
    """How many characters beyond ASCII the layout types, on every platform
    (the ISO key aside), and how many more Unicode composes from those
    letters and combining accents."""
    typed, direct = set(), set()
    for key in layout.keys:
        if key.physical.name == "iso":
            continue
        for layer in ("base", "shift", "option", "shift-option"):
            binding = layout.binding(key, layer, "pc")
            if isinstance(binding, Char):
                typed.add(binding.text)
                if layer in ("option", "shift-option"):
                    direct.add(binding.text)
    for dead in layout.dead.values():
        typed |= set(dead.map.values())

    def is_ascii(c):
        return len(c) == 1 and ord(c) < 128

    beyond = {c for c in typed if not is_ascii(c)}
    direct = {c for c in direct if not is_ascii(c)}
    marks = {c for c in typed if len(c) == 1 and unicodedata.combining(c)}
    bases = {c for c in typed if len(c) == 1 and not unicodedata.combining(c)}
    # Characters with a canonical decomposition into a typed base and typed marks
    composed = {"Latin": 0, "Greek": 0, "other": 0}
    for cp in range(sys.maxunicode + 1):
        c = chr(cp)
        decomposition = unicodedata.decomposition(c)
        if not decomposition or decomposition.startswith("<") or c in typed:
            continue
        d = unicodedata.normalize("NFD", c)
        # at least one mark: singletons like the Ohm sign are only duplicates
        if len(d) > 1 and d[0] in bases and all(m in marks for m in d[1:]):
            script = unicodedata.name(c).split()[0].capitalize()
            composed[script if script in composed else "other"] += 1
    total = sum(composed.values())
    return (
        f"It types **about {about(len(beyond))} characters beyond ASCII**, {about(len(direct))} of them directly "
        f"with Option or AltGr and the rest through dead keys. {len(marks)} are combining accents, which go on "
        f"any letter (`ǖ`, `ṩ`, `x̲`), so you can also type the roughly {about(total)} accented characters "
        f"that Unicode has as single characters ({about(composed['Latin'])} Latin, {about(composed['Greek'])} "
        f"Greek, and a few symbols such as `≮`): **about {about(len(beyond) + total)} in all**."
    )


def about(n: int) -> str:
    """`n` rounded for prose: to tens below 1000, to hundreds above."""
    return f"{round(n, -1 if n < 1000 else -2):,}"


def dead_key_table(layout: Layout) -> str:
    out = ["| Keys | Symbol | Dead key for |", "|------|--------|--------------|"]
    for dead in layout.dead.values():
        for key in layout.keys:
            for layer in ("option", "shift-option"):
                b = key.layers[layer]
                if isinstance(b, Dead) and b.id == dead.id:
                    out.append(
                        f"| {code(keys(key.physical, layer == 'shift-option'))} | {code(display(dead.symbol))} | "
                        f"[{dead.desc}](#{anchor(dead_heading(dead))}) |"
                    )
    return "\n".join(out) + "\n"


SECTIONS = {
    "count": character_count,
    "alternative": alternative_tables,
    "dead-key-table": dead_key_table,
    "dead-keys": dead_key_sections,
}


def update_readme(text: str, layout: Layout) -> str:
    for name, func in SECTIONS.items():
        pattern = re.compile(
            rf"(<!-- BEGIN generated: {name} -->\n).*?(<!-- END generated: {name} -->)", re.S
        )
        if not pattern.search(text):
            raise ValueError(f"README.md has no generated section {name!r}")
        text = pattern.sub(lambda m: m.group(1) + "\n" + func(layout).rstrip("\n") + "\n\n" + m.group(2), text)
    return text
