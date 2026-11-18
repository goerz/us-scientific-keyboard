# CLAUDE.md

## What this is

The "US Scientific" keyboard layout (successor of the macOS-only "U.S. International - Scientific", github.com/goerz/USScientific.bundle). `layout.toml` is the single source of the layout; the `layoutgen` package (`src/layoutgen/`, run with `uv run layoutgen`) generates everything else. Never edit generated files by hand.

## layout.toml

The format is documented in the comment at its top. Key points: `[alternative]` (Option on macOS, AltGr on Windows/Linux) and the `[dead.<id>.map]` tables are keyed by the character a key types without that modifier (`q`, `Q` = Shift, `"1"`, `"!"`); dead keys declare their trigger with `key`; `[notes]` (keyed by character) are descriptions for the README. Characters that break the text (combining marks at the start of a string, invisible spaces) are written as `\uXXXX` with the Unicode name in a comment behind the line; everything else is literal.

Derived, not written in the TOML: the plain and Shift layers (US), Caps Lock (Shift for letters, also on the alternative layer when Shift+alternative is the uppercase form), dead key + Space = the dead key's symbol, and platform conventions for the ISO key (`§ ±` on macOS, `\ |` elsewhere; see `keys.py`).

## layoutgen

- `keys.py`: physical keys with their macOS, Keyman, and Windows codes and diagram positions.
- `model.py`: loads and validates `layout.toml`; `Layout.binding(key, layer, platform)` is what all generators use (layers include the derived `caps` and `caps-option`).
- `macos.py`: `.keylayout` (filled into `templates/macos.keylayout`, which holds the non-character keys, Command/Control layers, and JIS key maps) and the `.bundle`.
- `keyman.py`: `.kmn` and `.kps`. `windows.py`: native layout DLL source against `kbd.h` plus scripts from `templates/windows/` (CRLF, see `.gitattributes`; `@@DLL@@`/`@@NAME@@` placeholders). Native Windows dead keys can't produce non-BMP characters; those are dropped and reported.
- `svg.py`, `docs.py`, `cheatsheet.py`: keyboard diagrams, the generated README sections (between `<!-- BEGIN/END generated: NAME -->` markers), and the PDF cheat sheet.

## Make

- `make` builds into `build/`: `make macos` (bundle + zip), `make keyman` (needs `npx @keymanapp/kmc` and ImageMagick), `make windows` (zipped source; compiling needs Windows/MSVC), `make cheatsheet` (rsvg-convert + LuaLaTeX).
- `make docs` regenerates the README sections and `docs/*.svg`, which are committed so GitHub shows them.
- `make test`: the tests read the generated `.keylayout` back and simulate the Keyman rules and the Windows tables, checking every key, layer, and dead key against `layout.toml`; they also fail if the README or diagrams are stale (fix with `make docs`).

When bumping the version, change `version` in `layout.toml` (everything else follows it) and in `pyproject.toml`.
