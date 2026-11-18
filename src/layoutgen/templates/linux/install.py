#!/usr/bin/env python3
"""Install the @@NAME@@ keyboard layout for the current user (Linux).

    python3 install.py              install, or update an earlier install
    python3 install.py --uninstall  remove it again

Installs, from the folder of this script:

* the XKB symbols file as ~/.config/xkb/symbols/@@ID@@, with an entry in
  ~/.config/xkb/rules/evdev.xml so that settings programs list the layout,
* the Compose file for the dead keys as ~/.config/@@ID@@/Compose, included
  from your Compose file (~/.XCompose, created if you have none),
* on GNOME, the layout as an input source.

~/.config is $XDG_CONFIG_HOME if that is set. XKB files in ~/.config/xkb
work in Wayland sessions (GNOME, KDE Plasma, Sway, and others that use
libxkbcommon), but not in X11 sessions.
"""

import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ID = "@@ID@@"
NAME = "@@NAME@@"
HERE = Path(__file__).resolve().parent
HOME = Path.home()
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME") or HOME / ".config")
XKB = CONFIG / "xkb"
SYMBOLS = XKB / "symbols" / ID
REGISTRY = XKB / "rules" / "evdev.xml"
COMPOSE = CONFIG / ID / "Compose"
MARKER = f"# {NAME} keyboard layout: dead keys (added by its install script)"
CREATED = f"# Created by the install script of the {NAME} keyboard layout"


def include_line() -> str:
    try:
        return f'include "%H/{COMPOSE.relative_to(HOME)}"'
    except ValueError:
        return f'include "{COMPOSE}"'


def user_compose_files() -> list:
    """The user Compose files that some program reads: GTK, IBus,
    libxkbcommon (Qt, KDE, fcitx5, many terminals), and libX11."""
    candidates = [
        os.environ.get("XCOMPOSEFILE"),
        CONFIG / "ibus" / "Compose",
        CONFIG / "gtk-4.0" / "Compose",
        CONFIG / "gtk-3.0" / "Compose",
        CONFIG / "XCompose",
        HOME / ".XCompose",
    ]
    result = []
    for path in candidates:
        if path and Path(path).is_file() and Path(path) not in result:
            result.append(Path(path))
    return result


def install_compose() -> None:
    COMPOSE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HERE / f"{ID}.compose", COMPOSE)
    print(f"Installed {COMPOSE}")
    targets = user_compose_files()
    if not targets:
        path = HOME / ".XCompose"
        path.write_text(f'{CREATED}\ninclude "%L"\n\n{MARKER}\n{include_line()}\n', encoding="utf-8")
        print(f"Created {path}, which includes it")
        return
    for path in targets:
        text = path.read_text(encoding="utf-8")
        if include_line() in text.splitlines():
            path.touch()  # programs that cache the compiled file check its time
            continue
        if not text.endswith("\n"):
            text += "\n"
        path.write_text(f"{text}\n{MARKER}\n{include_line()}\n", encoding="utf-8")
        print(f"Added an include of it to {path}")
        if 'include "%L"' not in text:
            print(f'  ({path} has no include "%L": the standard Compose sequences are off)')


def uninstall_compose() -> None:
    for path in user_compose_files():
        lines = path.read_text(encoding="utf-8").splitlines()
        kept = [line for line in lines if line not in (MARKER, include_line())]
        if kept == lines:
            continue
        while kept and not kept[-1].strip():
            kept.pop()
        if CREATED in kept and [line for line in kept if line != CREATED] == ['include "%L"']:
            path.unlink()
            print(f"Removed {path}")
        else:
            path.write_text("\n".join(kept) + "\n", encoding="utf-8")
            print(f"Removed the include from {path}")
    if COMPOSE.exists():
        shutil.rmtree(COMPOSE.parent)
        print(f"Removed {COMPOSE.parent}")


def _layout_list(tree):
    root = tree.getroot()
    layouts = root.find("layoutList")
    if layouts is None:
        layouts = ET.SubElement(root, "layoutList")
    return layouts


def _remove_ours(layouts) -> bool:
    removed = False
    for layout in list(layouts):
        if layout.findtext("configItem/name") == ID:
            layouts.remove(layout)
            removed = True
    return removed


def _write_registry(tree) -> None:
    if hasattr(ET, "indent"):  # Python 3.9+
        ET.indent(tree)
    body = ET.tostring(tree.getroot(), encoding="unicode")
    REGISTRY.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE xkbConfigRegistry SYSTEM "xkb.dtd">\n' + body + "\n",
        encoding="utf-8",
    )


def install_registry() -> None:
    ours = ET.parse(HERE / "evdev.xml")
    if not REGISTRY.exists():
        REGISTRY.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(HERE / "evdev.xml", REGISTRY)
        print(f"Installed {REGISTRY}")
        return
    tree = ET.parse(REGISTRY)
    layouts = _layout_list(tree)
    _remove_ours(layouts)
    layouts.extend(_layout_list(ours))
    _write_registry(tree)
    print(f"Added the layout to {REGISTRY}")


def uninstall_registry() -> None:
    if not REGISTRY.exists():
        return
    tree = ET.parse(REGISTRY)
    layouts = _layout_list(tree)
    if not _remove_ours(layouts):
        return
    root = tree.getroot()
    if len(layouts) == 0:
        root.remove(layouts)
    if len(root) == 0:
        REGISTRY.unlink()
        print(f"Removed {REGISTRY}")
    else:
        _write_registry(tree)
        print(f"Removed the layout from {REGISTRY}")


GNOME_SCHEMA = "org.gnome.desktop.input-sources"


def gnome_sources():
    """GNOME's input sources, or None if this isn't GNOME."""
    if not shutil.which("gsettings"):
        return None
    try:
        schemas = subprocess.run(["gsettings", "list-schemas"], capture_output=True, text=True, check=True).stdout
        if GNOME_SCHEMA not in schemas.split():
            return None
        value = subprocess.run(
            ["gsettings", "get", GNOME_SCHEMA, "sources"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    if value.startswith("@a(ss)"):
        value = value[len("@a(ss)"):].strip()
    import ast

    return [tuple(s) for s in ast.literal_eval(value)]


def set_gnome_sources(sources) -> None:
    value = "[" + ", ".join(f"('{a}', '{b}')" for a, b in sources) + "]"
    subprocess.run(["gsettings", "set", GNOME_SCHEMA, "sources", value], check=True)


def install() -> None:
    SYMBOLS.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HERE / ID, SYMBOLS)
    print(f"Installed {SYMBOLS}")
    install_registry()
    install_compose()
    sources = gnome_sources()
    if sources is not None and ("xkb", ID) not in sources:
        set_gnome_sources(sources + [("xkb", ID)])
        print("Added the layout to GNOME's input sources; switch to it with Super+Space.")
    elif sources is None:
        print(f'Add the layout "English ({NAME})" in your desktop\'s keyboard settings,')
        print(f"or use the XKB layout name {ID} (e.g. in Sway: xkb_layout {ID}).")
    print("Log out and back in, so that all programs read the new Compose file.")
    if os.environ.get("XDG_SESSION_TYPE") == "x11":
        print("This is an X11 session, where the X server doesn't read ~/.config/xkb. To use")
        print("the layout in this session (until you log out), run:")
        print(f"    setxkbmap -I{XKB} {ID} -print | xkbcomp -I{XKB} - $DISPLAY")


def uninstall() -> None:
    sources = gnome_sources()
    if sources is not None and ("xkb", ID) in sources:
        set_gnome_sources([s for s in sources if s != ("xkb", ID)])
        print("Removed the layout from GNOME's input sources.")
    if SYMBOLS.exists():
        SYMBOLS.unlink()
        print(f"Removed {SYMBOLS}")
    uninstall_registry()
    uninstall_compose()


if __name__ == "__main__":
    if sys.argv[1:] == []:
        install()
    elif sys.argv[1:] == ["--uninstall"]:
        uninstall()
    else:
        sys.exit(__doc__)
