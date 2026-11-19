"""macOS keyboard layout (.keylayout) and installable bundle."""

import plistlib
import shutil
from importlib.resources import files
from pathlib import Path

from .model import Char, Dead, Layout

# Key map index in the template's modifier map -> layer
MAP_LAYERS = {0: "base", 1: "shift", 2: "caps", 3: "option", 4: "shift-option", 5: "caps-option"}


def xml_escape(text: str) -> str:
    return "".join(
        c if c.isprintable() and c not in "&<>\"'" and not _is_mark(c) else f"&#x{ord(c):04X};"
        for c in text
    )


def _is_mark(c: str) -> bool:
    import unicodedata

    return unicodedata.category(c) in ("Mn", "Me", "Zs") and c != " "


def action_id(binding) -> str:
    if isinstance(binding, Dead):
        return f"dead:{binding.id}"
    return binding.text


def keylayout(layout: Layout) -> str:
    """The .keylayout XML."""
    keys = {index: [] for index in MAP_LAYERS}
    actions = {}  # action id -> list of (state, attribute, value)
    outputs = []
    for key in layout.keys:
        for index, layer in MAP_LAYERS.items():
            binding = layout.binding(key, layer)
            code = key.physical.mac
            if binding is None:
                continue
            if isinstance(binding, Dead):
                aid = action_id(binding)
                actions[aid] = [("none", "next", binding.id)]
            else:
                whens = [
                    (dead.id, "output", dead.map[binding.text])
                    for dead in layout.dead.values()
                    if binding.text in dead.map
                ]
                outputs.append(binding.text)
                if not whens:
                    keys[index].append(f'            <key code="{code}" output="{xml_escape(binding.text)}"/>')
                    continue
                aid = action_id(binding)
                actions[aid] = [("none", "output", binding.text), *whens]
                outputs.extend(value for _, _, value in whens)
            keys[index].append(f'            <key code="{code}" action="{xml_escape(aid)}"/>')

    action_lines = []
    for aid, whens in sorted(actions.items()):
        action_lines.append(f'        <action id="{xml_escape(aid)}">')
        for state, attr, value in whens:
            action_lines.append(f'            <when state="{state}" {attr}="{xml_escape(value)}"/>')
        action_lines.append("        </action>")

    terminators = [
        f'        <when state="{dead.id}" output="{xml_escape(dead.symbol)}"/>'
        for dead in layout.dead.values()
    ]
    outputs.extend(dead.symbol for dead in layout.dead.values())
    maxout = max(len(text.encode("utf-16-le")) // 2 for text in outputs)

    text = files("layoutgen").joinpath("templates", "macos.keylayout").read_text(encoding="utf-8")
    replacements = {
        "@@ID@@": str(layout.macos_id),
        "@@NAME@@": xml_escape(layout.name),
        "@@MAXOUT@@": str(maxout),
        "@@ACTIONS@@": "\n".join(action_lines) + "\n",
        "@@TERMINATORS@@": "\n".join(terminators) + "\n",
    }
    for index, lines in keys.items():
        replacements[f"@@KEYS_{index}@@\n"] = "".join(line + "\n" for line in lines)
    for placeholder, value in replacements.items():
        if placeholder not in text:
            raise RuntimeError(f"template is missing {placeholder!r}")
        text = text.replace(placeholder, value)
    return text


def bundle(layout: Layout, path: Path, icon: Path) -> None:
    """Write the installable .bundle directory."""
    if path.exists():
        shutil.rmtree(path)
    resources = path / "Contents" / "Resources"
    (resources / "en.lproj").mkdir(parents=True)
    (resources / f"{layout.id}.keylayout").write_text(keylayout(layout), encoding="utf-8")
    shutil.copyfile(icon, resources / f"{layout.id}.icns")
    strings = f'"{layout.name}" = "{layout.name}";\n'
    (resources / "en.lproj" / "InfoPlist.strings").write_bytes(strings.encode("utf-16"))
    info = {
        "CFBundleIdentifier": layout.macos_bundle_id,
        "CFBundleName": layout.name,
        "CFBundleVersion": layout.numeric_version,
        "CFBundleShortVersionString": layout.numeric_version,
        # Keyed by the layout's name (the name attribute of the .keylayout)
        f"KLInfo_{layout.name}": {
            "TICapsLockLanguageSwitchCapable": False,
            "TISInputSourceID": f"{layout.macos_bundle_id}.{layout.id}",
            "TISIntendedLanguage": layout.language,
        },
    }
    with open(path / "Contents" / "Info.plist", "wb") as fh:
        plistlib.dump(info, fh)
