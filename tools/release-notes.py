# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Print the release notes for a version: the downloads, then the version's
section of CHANGELOG.md.

Usage: release-notes.py VERSION [--title]

VERSION is "4.1.0" or "v4.1.0" (it must match `version` in layout.toml), or
"Unreleased". With --title, print the release title instead.
"""

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DOWNLOADS = """\
## Downloads

* `us_scientific.bundle.zip`: macOS keyboard layout
* `us_scientific.kmp`: Keyman package, for Windows and Linux, with the complete layout
* `us_scientific-windows.zip`: native Windows layout, to install with its `install.ps1` (no math bold dead key, and only some math script and double-struck letters)
* `us_scientific-linux.zip`: native Linux layout (XKB and Compose), to install with its `install.py`
* `us-scientific.pdf`: cheat sheet

See the [README](https://github.com/goerz/us-scientific-keyboard#installation) for installation instructions.
"""


def section(changelog: str, version: str) -> str:
    """The body of the `## [version]` section, without its heading."""
    match = re.search(rf"^## \[{re.escape(version)}\].*?$(.*?)(?=^## |^\[|\Z)", changelog, re.M | re.S)
    if not match:
        sys.exit(f"CHANGELOG.md has no section for {version}")
    if not match.group(1).strip() and version != "Unreleased":  # empty right after a release
        sys.exit(f"CHANGELOG.md has no entries for {version}")
    return match.group(1).strip()  # "### Added" etc. go below "## Changes"


def main():
    args = [a for a in sys.argv[1:] if a != "--title"]
    if len(args) != 1:
        sys.exit(__doc__)
    version = args[0].removeprefix("v")
    layout = tomllib.loads((ROOT / "layout.toml").read_text(encoding="utf-8"))["layout"]
    released = layout["version"]
    if version != "Unreleased" and version != released:
        sys.exit(f"version {version} doesn't match layout.toml ({released})")
    if "--title" in sys.argv:
        print(f"{layout['name']} {version}")
        return
    changes = section((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), version)
    print(f"{DOWNLOADS}\n## Changes\n\n{changes}")


if __name__ == "__main__":
    main()
