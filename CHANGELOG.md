# Changelog

All notable changes to this project are documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html), applied to what the keys type:

- Major: something that worked before works differently, e.g., a key or dead key types something else or nothing anymore, Caps Lock or a modifier behaves differently, or the layout has to be reinstalled or selected again.
- Minor: additions that don't change anything existing, e.g., a character on a free key, a new dead key entry, or a new platform or package.
- Patch: fixes that don't change `layout.toml`, such as a platform that didn't do what `layout.toml` says, and fixes to the documentation, cheat sheet, or packaging.

## [Unreleased]

### Added

- Accent dead key on `⌥;`, pressed *after* the letter: a combining mark for the preceding character. Dot above (`.` or Space), diaeresis (`:`), acute (`'`), grave (`` ` ``), circumflex (`^`), caron (`v`), macron (`-`), ring above (`o`), breve (`u`), cedilla (`,`), comma below (`<`), ogonek (`;`), double acute (`"`), tilde (`~`), dot below (`!`), low line (`_`), long solidus overlay (`/`, strikes through any symbol, e.g., `⊂⌥;/` gives `⊄`), and for polytonic Greek, rough and smooth breathing (`(`, `)`) and iota subscript (`i`).
- Math dead key on `⌥6`: `∪` (`u`), `∩` (`n`), `⊂ ⊃` (`c`, `C`), `⊆ ⊇` (`s`, `S`), `∖` (`\`), `ℓ` (`l`), `⟂` (`p`), `∥` (`|`), `↦` (`m`), `↔` (`-`), `≲ ≳` (`<`, `>`), `≃` (`~`), `⊕` (`+`). Space gives `⋅`.
- Slash dead key: `æ Æ` (`a`), `đ Đ` (`d`), `œ Œ` (`e`), `ħ Ħ` (`h`), `ı İ` (`i`), `þ Þ` (`p`), `ß ẞ` (`s`), `ð Ð` (`y`), `„` (`,`), `« »` (`<`, `>`), `§ ¶` (`6`, `7`), `∓` (`+` or `⌥⇧=`), and the negations `≢ ∄ ≉ ≁ ≰ ≱ ↛ ⇏ ⇎` (after `⌥7`, `⌥⇧;`, `⌥=`, `⌥⇧7`, `⌥⇧,`, `⌥⇧.`, `⌥k`, `⌥⇧k`, `⌥⇧l`).
- Acute dead key: `ń Ń`, `ś Ś`, `ẃ Ẃ`. Grave dead key: `ǹ Ǹ`, `ẁ Ẁ`.
- Greek dead key: `ϑ` (`J`), the variant forms `ϐ ϖ ϱ` after `⌥b` (`β`), `⌥p` (`π`), `⌥r` (`ρ`), and the polytonic accents, typed after the letter like the Accent dead key: acute (`'`), grave (`` ` ``), perispomeni (`~`), rough and smooth breathing (`(`, `)`), diaeresis (`:`), and iota subscript (`|`).
- Superscript dead key: `ᵅ` (after `⌥q`). Math Bold dead key: bold Greek `𝛂 𝛃 𝛑 𝛒 𝛚 𝚪 𝚫 𝚽 𝚿` and `𝛁` after the alternative-layer Greek letters and `∇` (not on native Windows, which can't produce characters outside the BMP from dead keys).
- `⌥g` types `↓`, `⌥t` types `↑`, `⌥⇧7` types `∼`, `⌥⇧;` types `∃`.
- The README lists the entries of the Accent, Slash, Math, and Greek dead keys in tables, with what each accent or symbol is.

### Changed

- `⌥;` is the Accent dead key instead of the combining dot above: `x⌥;` followed by Space (or `.`) gives `ẋ`. The combining diaeresis on `⌥⇧;` moved into the Accent dead key as well (`x⌥;:` gives `ẍ`).
- `⌥t` (`†`) moved to `⌥⇧t`, `⌥⇧t` (`≡`) to `⌥7`, `⌥7` (`≠`) to the Slash dead key (`⌥/=`, where it already was), and `⌥⇧7` (`≢`) to the Slash dead key (`⌥/⌥7`).
- `ğ` is no longer on `⌥g`; type `g⌥;u`.
- `⌥6` is the Math dead key instead of `⋅`, which is still on `⌥⇧8` (and on `⌥6` followed by Space).
- The cheat sheet has six diagrams per page, slightly smaller, to fit the new dead keys on one sheet.

## [4.1.0] - 2026-11-18

### Added

- Native Linux layout (`us_scientific-linux.zip`): an XKB layout with a Compose file for the dead keys, which `install.py` (or `make install`) installs for the current user. It doesn't need Keyman.

### Changed

- The native Windows layout comes compiled, as `us_scientific-windows.zip` (replacing `kbdussci-src.zip`): unzip it and run `install.ps1`, without installing Visual Studio first.
- The cheat sheet fits on two pages, so it prints on one sheet double-sided.

### Fixed

- Windows can load the native Windows layout: it rejected the DLL that `build.cmd` from 4.0.0 compiled.

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

[unreleased]: https://github.com/goerz/us-scientific-keyboard/compare/v4.1.0...HEAD
[4.1.0]: https://github.com/goerz/us-scientific-keyboard/compare/v4.0.0...v4.1.0
[4.0.0]: https://github.com/goerz/us-scientific-keyboard/releases/tag/v4.0.0
