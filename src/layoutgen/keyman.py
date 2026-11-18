"""Keyman keyboard source (.kmn) and package definition (.kps).

The alternative layer is on Right Alt (AltGr), so Left Alt keeps working for
menu shortcuts. Keys follow Windows/Linux conventions (platform "pc").
"""

from xml.sax.saxutils import escape

from .model import Char, Dead, Layout

# (Keyman modifiers, layer), when Caps Lock doesn't matter for a key
PLAIN_SPECS = [("", "base"), ("SHIFT", "shift"), ("RALT", "option"), ("SHIFT RALT", "shift-option")]
# ... and when it does
CAPS_SPECS = [
    ("NCAPS", "base"), ("CAPS", "caps"), ("SHIFT", "shift"),
    ("NCAPS RALT", "option"), ("CAPS RALT", "caps-option"), ("SHIFT RALT", "shift-option"),
]


def kmn_string(text: str) -> str:
    return " ".join(f"U+{ord(c):04X}" for c in text) if text else "nul"


def shown(text: str) -> str:
    """Text for a comment. A backslash at the end of a line would continue
    the comment onto the next line, so it is written as U+005C."""
    return "".join(
        c if c.isprintable() and not _is_mark(c) and c != "\\" else f"U+{ord(c):04X}" for c in text
    )


def _is_mark(c: str) -> bool:
    import unicodedata

    return unicodedata.category(c) in ("Mn", "Me", "Zs") and c != " "


def key_specs(layout: Layout, key):
    """[(vkey expression, binding)] for every layer of a key."""
    b = lambda layer: layout.binding(key, layer, "pc")  # noqa: E731
    caps_matters = b("caps") != b("base") or b("caps-option") != b("option")
    result = []
    for mods, layer in CAPS_SPECS if caps_matters else PLAIN_SPECS:
        binding = b(layer)
        if binding is not None:
            vkey = f"[{mods + ' ' if mods else ''}{key.physical.keyman}]"
            result.append((vkey, binding))
    return result


def rhs(binding) -> tuple[str, str]:
    """(Keyman output, comment) for a binding without a dead key before it."""
    if isinstance(binding, Dead):
        return f"dk({binding.id})", f"<{binding.id}>"
    return kmn_string(binding.text), shown(binding.text)


def kmn(layout: Layout, bitmap: str | None = None) -> str:
    specs = [spec for key in layout.keys for spec in key_specs(layout, key)]
    lines = [
        f"c {layout.name}",
        "c",
        "c Generated from layout.toml by layoutgen. Do not edit.",
        "",
        "store(&VERSION) '10.0'",
        f"store(&NAME) '{layout.name}'",
        f"store(&COPYRIGHT) '{layout.copyright_notice}'",
        f"store(&KEYBOARDVERSION) '{layout.version}'",
        "store(&TARGETS) 'windows macosx linux'",
    ]
    if bitmap:
        lines.append(f"store(&BITMAP) '{bitmap}'")
    lines += ["", "begin Unicode > use(main)", "", "group(main) using keys", ""]

    for dead in layout.dead.values():
        lines.append(f"c ---- dead key {dead.id} ----")
        for vkey, binding in specs:
            if isinstance(binding, Char) and binding.text in dead.map:
                result = dead.map[binding.text]
                out, note = kmn_string(result), shown(result)
            else:
                # No entry: the dead key's symbol, then the key's own output
                out, note = rhs(binding)
                out, note = f"{kmn_string(dead.symbol)} {out}", f"{shown(dead.symbol)} {note}"
            lines.append(f"dk({dead.id}) + {vkey} > {out}  c {note}")
        lines.append("")

    lines.append("c ---- keys ----")
    for vkey, binding in specs:
        out, note = rhs(binding)
        lines.append(f"+ {vkey} > {out}  c {note}")
    return "\n".join(lines) + "\n"


def kps(layout: Layout, kmx: str, icon: str, license_file: str) -> str:
    def file(name, desc, ftype):
        return (
            "    <File>\n"
            f"      <Name>{escape(name)}</Name>\n"
            f"      <Description>{escape(desc)}</Description>\n"
            "      <CopyLocation>0</CopyLocation>\n"
            f"      <FileType>{ftype}</FileType>\n"
            "    </File>\n"
        )

    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<Package>\n"
        "  <System>\n"
        "    <KeymanDeveloperVersion>18.0</KeymanDeveloperVersion>\n"
        "    <FileVersion>7.0</FileVersion>\n"
        "  </System>\n"
        "  <Options>\n"
        "    <FollowKeyboardVersion/>\n"
        f"    <LicenseFile>{escape(license_file)}</LicenseFile>\n"
        "  </Options>\n"
        "  <Info>\n"
        f'    <Name URL="">{escape(layout.name)}</Name>\n'
        f'    <Copyright URL="">{escape(layout.copyright_notice)}</Copyright>\n'
        f'    <Author URL="">{escape(layout.author)}</Author>\n'
        "  </Info>\n"
        "  <Files>\n"
        + file(kmx, f"Keyboard {layout.name}", ".kmx")
        + file(icon, "Keyboard icon", ".ico")
        + file(license_file, f"{layout.license} License", "")
        + "  </Files>\n"
        "  <Keyboards>\n"
        "    <Keyboard>\n"
        f"      <Name>{escape(layout.name)}</Name>\n"
        f"      <ID>{layout.id}</ID>\n"
        f"      <Version>{layout.version}</Version>\n"
        "      <Languages>\n"
        f'        <Language ID="{layout.language}">English</Language>\n'
        "      </Languages>\n"
        "    </Keyboard>\n"
        "  </Keyboards>\n"
        "</Package>\n"
    )
