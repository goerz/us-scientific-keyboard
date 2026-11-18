# Changelog

All notable changes to this project are documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Native Linux layout (`us_scientific-linux.zip`): an XKB layout with a Compose file for the dead keys, which `install.py` (or `make install`) installs for the current user. It doesn't need Keyman.

### Changed

- The native Windows layout comes compiled, as `us_scientific-windows.zip` (replacing `kbdussci-src.zip`): unzip it and run `install.ps1`, without installing Visual Studio first.
- The cheat sheet fits on two pages, so it prints on one sheet double-sided.

## [4.0.0] - 2026-11-18

First release of U.S. Scientific, the successor of the macOS-only "U.S. International - Scientific" layout ([USScientific.bundle](https://github.com/goerz/USScientific.bundle)). The whole layout is now defined in `layout.toml` and generated for every platform. The changes are relative to "U.S. International - Scientific" 3.0.

### Added

- Windows support, through Keyman (the complete layout) and as a native layout (compiled from source on Windows; no math bold, script, or double-struck dead keys).
- The subscript and superscript dead keys have every subscript and superscript in Unicode (e.g., `ᵢ ⱼ ᵣ`, `ᵃ ᵇ ᶜ`, `ᴬ ᴮ ᴰ`).
- Space after a dead key types the dead key's symbol.
- Slash dead key: `Ȼ`.

### Fixed

- Caps Lock uppercases letters consistently, also after dead keys and on the alternative layer, and no longer turns `'` and `` ` `` into dead keys.
- Grave dead key: removed the stray `c` and `C` entries.

[unreleased]: https://github.com/goerz/us-scientific-keyboard/compare/v4.0.0...HEAD
[4.0.0]: https://github.com/goerz/us-scientific-keyboard/releases/tag/v4.0.0
