"""Command line interface: `layoutgen <target> [options]`."""

import argparse
import sys
from pathlib import Path

from . import cheatsheet, docs, keyman, macos, model, svg, windows


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="layoutgen", description=__doc__)
    parser.add_argument("--layout", type=Path, default=Path("layout.toml"))
    sub = parser.add_subparsers(dest="target", required=True)

    p = sub.add_parser("keylayout", help="macOS .keylayout file")
    p.add_argument("output", type=Path)

    p = sub.add_parser("bundle", help="installable macOS .bundle")
    p.add_argument("output", type=Path)
    p.add_argument("--icon", type=Path, default=Path("icon.icns"))

    p = sub.add_parser("keyman", help="Keyman source (.kmn, .kps) in a directory")
    p.add_argument("output", type=Path)
    p.add_argument("--icon", default=None, help="icon file name (.ico) next to the .kmn")
    p.add_argument("--license", default="LICENSE", help="license file, relative to the .kps")

    p = sub.add_parser("windows", help="native Windows layout source in a directory")
    p.add_argument("output", type=Path)

    p = sub.add_parser("docs", help="update the generated parts of README.md and the diagrams")
    p.add_argument("--readme", type=Path, default=Path("README.md"))
    p.add_argument("--diagrams", type=Path, default=Path(docs.DIAGRAM_DIR))

    p = sub.add_parser("cheatsheet", help="diagrams and LaTeX source of the cheat sheet")
    p.add_argument("output", type=Path)

    args = parser.parse_args(argv)
    try:
        layout = model.load(args.layout)
    except model.LayoutError as exc:
        sys.exit(f"{args.layout}: {exc}")

    if args.target == "keylayout":
        args.output.write_text(macos.keylayout(layout), encoding="utf-8")
    elif args.target == "bundle":
        macos.bundle(layout, args.output, args.icon)
    elif args.target == "keyman":
        args.output.mkdir(parents=True, exist_ok=True)
        icon = args.icon or f"{layout.id}.ico"
        (args.output / f"{layout.id}.kmn").write_text(keyman.kmn(layout, icon), encoding="utf-8")
        (args.output / f"{layout.id}.kps").write_text(
            keyman.kps(layout, f"{layout.id}.kmx", icon, args.license), encoding="utf-8"
        )
    elif args.target == "windows":
        for line in windows.write_source(layout, args.output):
            print(f"{layout.windows_dll}: {line}", file=sys.stderr)
    elif args.target == "docs":
        args.readme.write_text(docs.update_readme(args.readme.read_text(encoding="utf-8"), layout), encoding="utf-8")
        args.diagrams.mkdir(parents=True, exist_ok=True)
        for name, content in svg.all_diagrams(layout).items():
            (args.diagrams / name).write_text(content, encoding="utf-8")
    elif args.target == "cheatsheet":
        cheatsheet.write(layout, args.output)
