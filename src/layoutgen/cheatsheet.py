"""PDF cheat sheet: the keyboard diagrams on two pages (one sheet, printed
double-sided), six per page, each with its description beside it, and the
number pad by itself on a third page.

`write` puts the compact SVG diagrams and a LaTeX file into a directory; the
Makefile converts the SVGs to PDF (rsvg-convert) and runs LuaLaTeX.
"""

import re
from pathlib import Path

from . import svg
from .model import Char, Dead, Layout

PER_PAGE = 6
# Glyphs that JuliaMono squeezes into one cell, so that they look like
# their narrow counterparts (⟶ like →, ⨁ like ⊕): set in Latin Modern Math.
WIDE = set("⟵⟶⟷⟸⟹⟺⟻⟼⨀⨁⨂⨃⨄∑∏∐⋂⋃⋀⋁")
DIAGRAM_WIDTH = 4.6  # inches; six diagrams fit in the height of a letter page

TEX = r"""\documentclass[10pt]{{article}}
\usepackage[letterpaper,margin=0.5in]{{geometry}}
\usepackage{{graphicx}}
\usepackage{{xcolor}}
\usepackage{{tikz}}
% a key in the fine print: its keystroke (small, top) and what it types without the dead key
\newcommand{{\keycap}}[2]{{\tikz[baseline={{([yshift=2.9pt]k.south)}}]\node[draw=black!45,fill=white,rounded corners=1.5pt,inner xsep=1.2pt,inner ysep=1.3pt,align=center,minimum width=12pt](k){{{{\fontsize{{5pt}}{{5.5pt}}\selectfont\color{{black!55}}\rule{{0pt}}{{5pt}}#1}}\\[-0.5pt]{{\footnotesize\rule[-1.6pt]{{0pt}}{{6.4pt}}#2}}}};}}
\usepackage{{fontspec}}
\setmainfont{{{font_file}}}[Path={font_dir}/,Ligatures=TeXOff]
\newfontfamily\widefont{{latinmodern-math.otf}}
\pagestyle{{empty}}
\setlength{{\parindent}}{{0pt}}
\newcommand{{\row}}[2]{{%
  \begin{{minipage}}[c]{{\dimexpr\linewidth-{width}-1em}}\raggedright #1\end{{minipage}}\hfill
  \begin{{minipage}}[c]{{{width}}}\includegraphics[width=\linewidth]{{#2}}\end{{minipage}}\par}}
% the number pad: description, then its two layers side by side, each with a caption
\newcommand{{\numpadrow}}[5]{{%
  \begin{{minipage}}[c]{{\dimexpr\linewidth-{width}-1em}}\raggedright #1\end{{minipage}}\hfill
  \begin{{minipage}}[c]{{{width}}}\hfill
    \begin{{tabular}}[c]{{@{{}}c@{{}}}}\includegraphics[width={numpad_width}]{{#2}}\\[2pt]\footnotesize #3\end{{tabular}}\hspace{{1.5em}}%
    \begin{{tabular}}[c]{{@{{}}c@{{}}}}\includegraphics[width={numpad_width}]{{#4}}\\[2pt]\footnotesize #5\end{{tabular}}%
  \end{{minipage}}\par}}
% a single number pad diagram, under the two layers
\newcommand{{\numpadsinglerow}}[2]{{%
  \begin{{minipage}}[c]{{\dimexpr\linewidth-{width}-1em}}\raggedright #1\end{{minipage}}\hfill
  \begin{{minipage}}[c]{{{width}}}\hfill\includegraphics[width={numpad_width}]{{#2}}\end{{minipage}}\par}}
\begin{{document}}
{{\large {name}}} keyboard layout\hfill version {version}\par
\vfill
{rows}
\end{{document}}
"""

ALTERNATIVE = (
    r"{\large Alternative layer}\par\smallskip"
    r" Option (macOS) or AltGr (right Alt; Windows, Linux).\par\smallskip"
    r"\footnotesize Top: with Shift. Bottom: without."
    r" Dark badge: dead key. Press and release it, then press another key."
    r" Space after a dead key types its symbol."
)


NUMPAD = (
    r"{\large Number pad}\par\smallskip"
    r" Option (macOS) or AltGr (right Alt; Linux, Keyman), on keyboards with a number pad.\par\smallskip"
    r"\footnotesize Box drawing in the shape of the keys: single lines, and with Shift, double lines"
    r" and the tees that join a single and a double line."
    r" Num Lock doesn't matter. Not in the native Windows layout."
)


# The dead key whose number pad entries the cheat sheet shows as an example.
NUMPAD_DEAD = "math"


def numpad_dead(layout: Layout) -> str:
    dead = layout.dead[NUMPAD_DEAD]
    return (
        rf"{{\large {tex_escape(dead.name)}, then the number pad}}\par\smallskip"
        rf" {tex_escape(trigger(layout, NUMPAD_DEAD))}, then a number pad key.\par\smallskip"
        r"\footnotesize After a dead key, a number pad key types what the main key"
        r" with the same character does: with the Math dead key, the digits give"
        r" arrows in their directions on the number pad."
    )


def tex_escape(text: str) -> str:
    special = {c: "\\" + c for c in "#$%&_{}"}
    special |= {"~": r"\textasciitilde{}", "^": r"\textasciicircum{}", "\\": r"\textbackslash{}"}
    return "".join(special.get(c, c) for c in text)


def trigger(layout: Layout, dead_id: str) -> str:
    """How to type a dead key, e.g. "Option+Shift+R"."""
    for key in layout.keys:
        for layer, prefix in (("option", "Option+"), ("shift-option", "Option+Shift+")):
            binding = key.layers[layer]
            if isinstance(binding, Dead) and binding.id == dead_id:
                base = key.physical.base
                return prefix + (base.upper() if base.isalpha() else base)
    raise ValueError(f"dead key {dead_id} has no trigger")


def hidden_entries(layout: Layout, dead_id: str) -> list:
    """(keys, typed, result) of the dead key's entries that follow an Option
    key, which the diagram can't show, e.g. ("⌥⇧e", "∉", "∌")."""
    option_keys = {}
    for key in layout.keys:
        for layer, prefix in (("option", "⌥"), ("shift-option", "⌥⇧")):
            binding = key.layers[layer]
            if isinstance(binding, Char):
                option_keys.setdefault(binding.text, prefix + key.physical.base)
    entries = []
    for typed, result in layout.dead[dead_id].map.items():
        if typed in option_keys:
            text = result.text if isinstance(result, Char) else str(result)
            entries.append((option_keys[typed], typed, text))
    return entries


def description(layout: Layout, dead_id: str) -> str:
    dead = layout.dead[dead_id]
    desc = dead.desc[0].upper() + dead.desc[1:]
    text = (
        rf"{{\large {tex_escape(dead.name)}}}\par\smallskip"
        rf" {tex_escape(trigger(layout, dead_id))}\par\smallskip"
        rf"\footnotesize {tex_escape(desc)}."
    )
    hidden = hidden_entries(layout, dead_id)
    if hidden:
        def entry(keys, typed, result):
            font = r"\widefont" if result in WIDE else ""
            return rf"\mbox{{\keycap{{{tex_escape(keys)}}}{{{tex_escape(typed)}}}\,{{\small{font} {tex_escape(result)}}}}}"

        entries = r"\hspace{0.8em plus 0.4em minus 0.2em}".join(entry(*e) for e in hidden)
        text += rf"\par\smallskip Then a key with Option:\par\setlength{{\lineskiplimit}}{{1.5pt}}\setlength{{\lineskip}}{{2pt}}{entries}"
    return text


def svg_width(content: str) -> float:
    return float(re.search(r'<svg [^>]*width="([\d.]+)"', content).group(1))


def write(layout: Layout, outdir: Path, font: Path = svg.DEFAULT_FONT) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    diagrams = svg.all_diagrams(layout, font, compact=True)
    for name, content in diagrams.items():
        (outdir / name).write_text(content, encoding="utf-8")
    numpad = diagrams.pop("numpad.svg", None)
    if numpad is not None:  # on the cheat sheet, each layer by itself
        (outdir / "numpad.svg").unlink()
        for layer in ("option", "shift-option"):
            content = svg.numpad(layout, svg.Font(font), compact=True, layer=layer)
            (outdir / f"numpad-{layer}.svg").write_text(content, encoding="utf-8")
        content = svg.numpad(layout, svg.Font(font), compact=True, dead=NUMPAD_DEAD)
        (outdir / f"numpad-{NUMPAD_DEAD}.svg").write_text(content, encoding="utf-8")
    # the number pad at the scale of the other diagrams, so its keys have the same size
    scale = DIAGRAM_WIDTH / svg_width(next(iter(diagrams.values())))
    numpad_width = svg_width(numpad) * scale if numpad is not None else 0
    texts = [ALTERNATIVE] + [description(layout, dead_id) for dead_id in layout.dead]
    rows = []
    for i, (name, text) in enumerate(zip(diagrams, texts, strict=True)):
        rows.append(rf"\row{{{text}}}{{{Path(name).stem}.pdf}}")
        rows.append(r"\newpage\vfill" if (i + 1) % PER_PAGE == 0 else r"\vfill")
    if numpad is not None:
        if rows[-1].startswith(r"\newpage"):
            rows.pop()
        # at the top of its page, in the columns of the other pages
        layers = r"{numpad-option.pdf}{Option}{numpad-shift-option.pdf}{Shift+Option}"
        rows += [
            r"\newpage",
            rf"\numpadrow{{{NUMPAD}}}{layers}",
            r"\bigskip\bigskip",
            rf"\numpadsinglerow{{{numpad_dead(layout)}}}{{numpad-{NUMPAD_DEAD}.pdf}}",
            r"\vfill\null",
        ]
    (outdir / "cheatsheet.tex").write_text(
        TEX.format(
            name=layout.name,
            width=f"{DIAGRAM_WIDTH}in",
            numpad_width=f"{numpad_width:.3f}in",
            version=layout.version,
            rows="\n".join(rows),
            font_file=Path(font).name,
            font_dir=Path(font).resolve().parent.as_posix(),
        ),
        encoding="utf-8",
    )
