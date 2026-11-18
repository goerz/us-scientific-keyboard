"""Command line interface: `layoutgen <target> [options]`."""

import argparse
import sys
from pathlib import Path

from . import macos, model


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="layoutgen", description=__doc__)
    parser.add_argument("--layout", type=Path, default=Path("layout.toml"))
    sub = parser.add_subparsers(dest="target", required=True)

    p = sub.add_parser("keylayout", help="macOS .keylayout file")
    p.add_argument("output", type=Path)

    p = sub.add_parser("bundle", help="installable macOS .bundle")
    p.add_argument("output", type=Path)
    p.add_argument("--icon", type=Path, default=Path("icon.icns"))

    args = parser.parse_args(argv)
    try:
        layout = model.load(args.layout)
    except model.LayoutError as exc:
        sys.exit(f"{args.layout}: {exc}")

    if args.target == "keylayout":
        args.output.write_text(macos.keylayout(layout), encoding="utf-8")
    elif args.target == "bundle":
        macos.bundle(layout, args.output, args.icon)
