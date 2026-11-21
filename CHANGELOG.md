# Changelog

All notable changes to this project are documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html), applied to what the keys type:

- Major: something that worked before works differently, e.g., a key or dead key types something else or nothing anymore, Caps Lock or a modifier behaves differently, or the layout has to be reinstalled or selected again.
- Minor: additions that don't change anything existing, e.g., a character on a free key, a new dead key entry, or a new platform or package.
- Patch: fixes that don't change `layout.toml`, such as a platform that didn't do what `layout.toml` says, and fixes to the documentation, cheat sheet, or packaging.

Between releases, the version (`version` in `layout.toml` and `pyproject.toml`) follows [these recommendations](https://michaelgoerz.net/notes/inter-release-versioning-recommendations.html): right after releasing `X.Y.Z`, it is `X.Y.Z+dev`; the first change under [Unreleased] sets it to the version that change implies, with `-dev` (e.g., `5.1.0-dev`), and a later change that implies a bigger step raises it (e.g., to `6.0.0-dev`). The cheat sheet shows the full version; the macOS bundle, the Keyman package, and the Windows file version get it without the suffix, since they only take numbers.

## [Unreleased]

### Added

- Double-Struck dead key: the double angle brackets `⟪ ⟫` (`⌥⇧m⌥[` and `⌥⇧m⌥]`, after the keys of `⟨ ⟩`), for vectors in Liouville space.
- Math dead key (`⌥6`, then the key): the squared `⊞ ⊟` (`+`, `_`), the triangles `◁ ▷` (`⌥[` and `⌥]`, the keys of `⟨ ⟩`; series product in SLH), and the square versions of the set symbols, `⊏ ⊑ ⊐ ⊒` (`⌥c`, `⌥d`, `⌥⇧c`, `⌥⇧d`, the keys of `⊂ ⊆ ⊃ ⊇` with Option) and `⊓ ⊔` (`⌥n`, `⌥u`, the keys of `∩ ∪` with Option).

### Changed

- Math dead key: `⊆ ⊇` moved from `s` and `S` to `d` and `D`, the key above `c` and `C` (`⊂ ⊃`); `⊇` looks like a D. `⌥6s` and `⌥6S` type `⋅s` and `⋅S` now, like other keys without an entry.
- Cheat sheet: the dead keys' entries that follow an Option key are in the diagrams, in a second column on each key, instead of in a list below the description; a result that builds on what the key types with Option has that symbol small and gray behind it (e.g., `⟹⇒` on `K`). The Slash dead key's description has a legend.

## [5.2.0] - 2026-11-19

### Added

- Box drawing on the number pad, in the shape of the keys: with Option (AltGr), `┌ ┬ ┐ ├ ┼ ┤ └ ┴ ┘` on the digits, `─` (`-`), `│` (`+`), and the rounded corners `╭ ╮ ╰ ╯` (`/ * 0 .`); with Shift+Option, the double lines `╔ ╦ ╗ ╠ ╬ ╣ ╚ ╩ ╝ ═ ║` and the tees `╟ ╢ ╞ ╡` that join a single and a double line. Not in the native Windows layout.
- Math dead key: arrows on the digits, in the directions they have on the number pad: `↖ ↑ ↗ ← ↔ → ↙ ↓ ↘` (`7` to `1`) and `↕` (`0`); with the number pad after `⌥6`, too. After `⌥6`, the keys of the short arrows give the long ones: `⟵ ⟶ ⟸ ⟹ ⟺` (`⌥j` `←`, `⌥k` `→`, `⌥⇧j` `⇐`, `⌥⇧k` `⇒`, `⌥⇧l` `⇔`).
- After a dead key, a number pad key works like the key of the main keyboard that types the same character (e.g., `⌥z` followed by number pad `2` gives `₂`). This was already the case in the native Windows layout.
- The README has a section for the number pad, and the cheat sheet a third page, with the Math dead key on the number pad as an example.
- The README has a table of contents.
- The cheat sheet lists the dead-key entries that follow an Option key (e.g., `⌥6⌥⇧k` for `⟹`), which the diagrams can't show.
- Math dead key (`⌥6`, then the key): the Unicode operators of Julia's Base that the layout didn't have, `⊻` (`x`, `xor`), `⊼` and `⊽` (`⌥⇧v` and `⌥v`, the keys of `∧` and `∨`; `nand` and `nor`), `∋` and `∌` (`⌥e` and `⌥⇧e`, the keys of `∈` and `∉`), `⊊` and `⊋` (`(` and `)`), and `∛` and `∜` (`#` and `$`).
- Math dead key: operators that registered Julia packages use, `≅` (`=`), `⊙` (`⌥⇧8`, the key of `⋅`), `⊖` (`⌥-`, `–`), `⊠` (`⌥x`, `×`), `⊡` (`[`), `⋆` (`*`), `⨟` (`⌥⇧w`, `∘`), `¬` (`!`), `≺` and `≻` (`{` and `}`), and `⪯` and `⪰` (`⌥⇧,` and `⌥⇧.`, `≤` and `≥`).

### Fixed

- `⌥9` types `Å` LATIN CAPITAL LETTER A WITH RING ABOVE (U+00C5) instead of the ANGSTROM SIGN (U+212B), which Unicode normalization (NFC) replaces with U+00C5, so text could contain either.

## [5.1.0] - 2026-11-19

### Added

- Math dead key: `⋯` (`.`), `⋮` (`:`), `⋱` (`;`), `≊` (`⌥=`), and the n-ary `⨁ ⨂` after the binary `⊕ ⊗` (`⌥⇧q`, `⌥⇧x`).
- Slash dead key: the fractions `½ ⅓ ¼ ⅕` (`2` to `5`, 1/n) and `⅔ ¾ ⅘ ⅚` (with Shift, n/(n+1)).
- Slash dead key: `©` (`g`), `™` (`G`), and `®` (`r`). Apple's US layout has `©` and `®` on `⌥g` and `⌥r`.
- Subscript dead key: `ᵧ ᵩ ᵪ` (`G`, `F`, `X`, the keys of `γ ϕ χ` in the Greek dead key).

### Changed

- The README's dead-key tables say when an entry is also on its own `⌥` key, e.g., `ß` on the Slash dead key is also on `⌥s`.

### Fixed

- Math `|` types the double vertical line `‖` (the norm, `\|` in Julia) instead of `∥` (parallel), which moved to Math `P`, next to `⟂` on Math `p`.
- `⌥⇧q` types the binary circled plus `⊕`, the counterpart of `⊗` on `⌥⇧x`, instead of the n-ary `⨁`, which is now `⌥6⌥⇧q`. `⨁` can't be used as an infix operator in Julia. Math `+` no longer types `⊕`, which was only there because `⌥⇧q` didn't.

## [5.0.0] - 2026-11-18

### Added

- Accent dead key on `⌥;`, pressed *after* the letter: a combining mark for the preceding character. Dot above (`.` or Space), diaeresis (`:`), acute (`'`), grave (`` ` ``), circumflex (`^`), caron (`v`), macron (`-`), ring above (`o`), breve (`u`), cedilla (`,`), comma below (`<`), ogonek (`;`), double acute (`"`), tilde (`~`), dot below (`!`), low line (`_`), long solidus overlay (`/`, strikes through any symbol, e.g., `⊂⌥;/` gives `⊄`), and for polytonic Greek, rough and smooth breathing (`(`, `)`) and iota subscript (`i`).
- Math dead key on `⌥6`: `∪` (`u`), `∩` (`n`), `⊂ ⊃` (`c`, `C`), `⊆ ⊇` (`s`, `S`), `∖` (`\`), `ℓ` (`l`), `⟂` (`p`), `∥` (`|`), `↦` (`m`), `↔` (`-`), `≲ ≳` (`<`, `>`), `≃` (`~`), `⊕` (`+`). Space gives `⋅`.
- Slash dead key: `æ Æ` (`a`), `đ Đ` (`d`), `œ Œ` (`e`), `ħ Ħ` (`h`), `ı İ` (`i`), `þ Þ` (`p`), `ß ẞ` (`s`), `ð Ð` (`y`), `„` (`,`), `« »` (`<`, `>`), `§ ¶` (`6`, `7`), `∓` (`+` or `⌥⇧=`), and the negations `≢ ∄ ≉ ≁ ≰ ≱ ↛ ⇏ ⇎` (after `⌥7`, `⌥⇧;`, `⌥=`, `⌥⇧7`, `⌥⇧,`, `⌥⇧.`, `⌥k`, `⌥⇧k`, `⌥⇧l`).
- Acute dead key: `ń Ń`, `ś Ś`, `ẃ Ẃ`. Grave dead key: `ǹ Ǹ`, `ẁ Ẁ`.
- Greek dead key: `ϑ` (`J`), the variant forms `ϐ ϖ ϱ` after `⌥b` (`β`), `⌥p` (`π`), `⌥r` (`ρ`), and the polytonic accents, typed after the letter like the Accent dead key: acute (`'`), grave (`` ` ``), perispomeni (`~`), rough and smooth breathing (`(`, `)`), diaeresis (`:`), and iota subscript (`|`).
- Superscript dead key: `ᵅ` (after `⌥q`). Math Bold dead key: bold Greek `𝛂 𝛃 𝛑 𝛒 𝛚 𝚪 𝚫 𝚽 𝚿` and `𝛁` after the alternative-layer Greek letters and `∇` (not on native Windows, which can't produce characters outside the BMP from dead keys).
- `⌥g` types `↓`, `⌥t` types `↑`, `⌥⇧7` types `∼`, `⌥⇧;` types `∃`.
- The README lists the entries of the Accent, Slash, Math, and Greek dead keys in tables, with what each accent or symbol is.
- The README says how many characters the layout types (generated from `layout.toml`).

### Changed

- `⌥;` is the Accent dead key instead of the combining dot above: `x⌥;` followed by Space (or `.`) gives `ẋ`. The combining diaeresis on `⌥⇧;` moved into the Accent dead key as well (`x⌥;:` gives `ẍ`).
- `⌥t` (`†`) moved to `⌥⇧t`, `⌥⇧t` (`≡`) to `⌥7`, `⌥7` (`≠`) to the Slash dead key (`⌥/=`, where it already was), and `⌥⇧7` (`≢`) to the Slash dead key (`⌥/⌥7`).
- `ğ` is no longer on `⌥g`; type `g⌥;u`.
- `⌥6` is the Math dead key instead of `⋅`, which is still on `⌥⇧8` (and on `⌥6` followed by Space).
- The cheat sheet has six diagrams per page, slightly smaller, to fit the new dead keys on one sheet.

### Fixed

- `make install` on macOS no longer adds another "U.S. Scientific" entry to the input sources each time it runs in the same login session.

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

[unreleased]: https://github.com/goerz/us-scientific-keyboard/compare/v5.2.0...HEAD
[5.2.0]: https://github.com/goerz/us-scientific-keyboard/compare/v5.1.0...v5.2.0
[5.1.0]: https://github.com/goerz/us-scientific-keyboard/compare/v5.0.0...v5.1.0
[5.0.0]: https://github.com/goerz/us-scientific-keyboard/compare/v4.1.0...v5.0.0
[4.1.0]: https://github.com/goerz/us-scientific-keyboard/compare/v4.0.0...v4.1.0
[4.0.0]: https://github.com/goerz/us-scientific-keyboard/releases/tag/v4.0.0
