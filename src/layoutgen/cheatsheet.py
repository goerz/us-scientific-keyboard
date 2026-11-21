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
# The key that explains the dead keys' Option column (see `svg.dead_key`):
# (dead key, what the key types), a key with all four legends and a gray
# hint, outlined in its dead key's diagram. The legend is right above that
# dead key's description, in the space the description before leaves free
# (it has to be short).
LEGEND_KEY = ("slash", "=")
DIAGRAM_WIDTH = 4.6  # inches; six diagrams fit in the height of a letter page

TEX = r"""\documentclass[10pt]{{article}}
\usepackage[letterpaper,margin=0.5in]{{geometry}}
\usepackage{{graphicx}}
\usepackage{{xcolor}}
\usepackage{{tikz}}
% the legend of the Option column, in the column of the descriptions: a key,
% with what each of its legends is; without height, hanging up from where it
% is, into the space below the description before
% a keystroke in the legend, in a rounded box
\newcommand{{\keybox}}[1]{{\tikz[baseline=(b.base)]\node[draw=black!35,rounded corners=1pt,inner xsep=1pt,inner ysep=0.7pt](b){{\vphantom{{⌥⇧/=}}#1}};}}
% the width of the widest key's box, so that the labels' columns line up
\newlength{{\legendkeywidth}}
% the labels are typeset before the picture, so that their boxes aren't nested in it
\newsavebox{{\legendshift}}\newsavebox{{\legendbase}}\newsavebox{{\legendshiftoption}}\newsavebox{{\legendoption}}\newsavebox{{\legendhints}}
\newcommand{{\legendkey}}[1]{{%
  \settowidth{{\legendkeywidth}}{{\tiny\keybox{{{legend_widest}}}}}%
  \sbox{{\legendshift}}{{\tiny {legend_shift}}}\sbox{{\legendbase}}{{\tiny {legend_base}}}%
  \sbox{{\legendshiftoption}}{{\tiny {legend_shift_option}}}\sbox{{\legendoption}}{{\tiny {legend_option}}}\sbox{{\legendhints}}{{\tiny {legend_hints}}}%
  \nointerlineskip\vbox to 0pt{{\vss\hbox{{\begin{{tikzpicture}}[every node/.style={{font=\tiny,inner sep=1pt}}]
  \node[inner sep=0,anchor=north west] (k) at (0,0) {{\includegraphics[width={legend_width}in]{{#1}}}};
  % what each legend is, next to the key: right-aligned on its left, left-aligned on its right
  \node[anchor=east] (ws) at ([xshift=-2pt,yshift=-{legend_top}in]k.north west) {{with Shift}};
  \node[anchor=east] (wb) at ([xshift=-2pt,yshift=-{legend_bottom}in]k.north west) {{without Shift}};
  \coordinate (left) at ([xshift=-0.6em]current bounding box.west);
  \node[anchor=west] (wso) at ([xshift=2pt,yshift=-{legend_top}in]k.north east) {{with Shift+Option}};
  \node[anchor=west] (wo) at ([xshift=2pt,yshift=-{legend_bottom}in]k.north east) {{with Option}};
  \coordinate (right) at ([xshift=0.6em]current bounding box.east);
  % the keystrokes, all equally wide, in a column on each side
  \node[anchor=base east] at (left |- ws.base) {{\usebox{{\legendshift}}}};
  \node[anchor=base east] at (left |- wb.base) {{\usebox{{\legendbase}}}};
  \node[anchor=base west] at (right |- wso.base) {{\usebox{{\legendshiftoption}}}};
  \node[anchor=base west] at (right |- wo.base) {{\usebox{{\legendoption}}}};
  \node[anchor=south west,inner sep=0,font=\tiny\bfseries] at ([yshift=4pt]current bounding box.west |- k.north) {{Legend}};
  \node[anchor=north west,inner sep=0,text width=\dimexpr\linewidth-{width}-1em-10pt\relax,align=left]
    at ([yshift=-4pt]current bounding box.west |- k.south) {{Small and gray: what the key types with Option, if the result builds on it: \usebox{{\legendhints}}}};
  \draw[black!30,rounded corners=3pt] ([shift={{(-4pt,-4pt)}}]current bounding box.south west)
    rectangle ([shift={{(4pt,4pt)}}]current bounding box.north east);
\end{{tikzpicture}}}}\vskip 8pt}}\nointerlineskip}}
\usepackage{{fontspec}}
% bold (for the legend's title) as JuliaMono Regular with a thicker outline
\setmainfont{{{font_file}}}[Path={font_dir}/,Ligatures=TeXOff,BoldFont={font_file},BoldFeatures={{FakeBold=1.5}}]
\pagestyle{{empty}}
\setlength{{\parindent}}{{0pt}}
% a description beside its diagram, their tops aligned
\newcommand{{\row}}[2]{{%
  \begin{{minipage}}[t]{{\dimexpr\linewidth-{width}-1em}}\vspace{{0pt}}\raggedright #1\end{{minipage}}\hfill
  \begin{{minipage}}[t]{{{width}}}\vspace{{0pt}}\includegraphics[width=\linewidth]{{#2}}\end{{minipage}}\par}}
% the number pad: description, then its two layers side by side, each with a caption
\newcommand{{\numpadrow}}[5]{{%
  \begin{{minipage}}[t]{{\dimexpr\linewidth-{width}-1em}}\vspace{{0pt}}\raggedright #1\end{{minipage}}\hfill
  \begin{{minipage}}[t]{{{width}}}\vspace{{0pt}}\hfill
    \begin{{tabular}}[c]{{@{{}}c@{{}}}}\includegraphics[width={numpad_width}]{{#2}}\\[2pt]\footnotesize #3\end{{tabular}}\hspace{{1.5em}}%
    \begin{{tabular}}[c]{{@{{}}c@{{}}}}\includegraphics[width={numpad_width}]{{#4}}\\[2pt]\footnotesize #5\end{{tabular}}%
  \end{{minipage}}\par}}
% a single number pad diagram, under the two layers
\newcommand{{\numpadsinglerow}}[2]{{%
  \begin{{minipage}}[t]{{\dimexpr\linewidth-{width}-1em}}\vspace{{0pt}}\raggedright #1\end{{minipage}}\hfill
  \begin{{minipage}}[t]{{{width}}}\vspace{{0pt}}\hfill\includegraphics[width={numpad_width}]{{#2}}\end{{minipage}}\par}}
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


def description(layout: Layout, dead_id: str) -> str:
    dead = layout.dead[dead_id]
    desc = dead.desc[0].upper() + dead.desc[1:]
    text = (
        rf"{{\large {tex_escape(dead.name)}}}\par\smallskip"
        rf" {tex_escape(trigger(layout, dead_id))}\par\smallskip"
        rf"\footnotesize {tex_escape(desc)}."
    )
    # chained dead keys that start with this one: what the second dead key
    # gives that the chain has a version of, lowercase first
    for (first, second), chain in layout.chains.items():
        if first == dead_id:
            letters = sorted(
                {layout.dead[second].map[typed] for typed in chain.map if typed != " "},
                key=lambda c: (c.isupper(), ord(c)),
            )
            text += (
                rf"\par\smallskip Combines with {tex_escape(layout.dead[second].name)}"
                rf" ({tex_escape(trigger(layout, second))}): {' '.join(letters)}"
            )
    return text


def legend_labels(layout: Layout, dead_id: str, base: str) -> dict:
    """The legend's labels for the four legends of the key that types
    `base`: the keystrokes, each in a box, and their result (`⌥/ ⌥= ≉`);
    and what the key types with Option where the diagram shows that small
    and gray (`⌥= ≈`), for the end of the note about it."""
    key = next(key for key in layout.keys if key.physical.base == base)
    dead = layout.dead[dead_id]
    trigger = next(
        prefix + k.physical.base
        for k in layout.keys
        for layer, prefix in (("option", "⌥"), ("shift-option", "⌥⇧"))
        if isinstance(k.layers[layer], Dead) and k.layers[layer].id == dead_id
    )
    labels, hints = {}, []
    layers = (("shift", "⇧"), ("base", ""), ("shift-option", "⌥⇧"), ("option", "⌥"))
    for layer, prefix in layers:
        typed = key.layers[layer].text
        keys = prefix + key.physical.base
        labels[f"legend_{layer.replace('-', '_')}"] = (
            rf"\keybox{{{tex_escape(trigger)}}}\,"
            rf"\makebox[\legendkeywidth][l]{{\keybox{{{tex_escape(keys)}}}}}\,{tex_escape(dead.map[typed])}"
        )
        if layer.endswith("option") and len(svg._option_legend(key.layers[layer], dead.map, dead.no_hint)) == 3:
            hints.append(rf"\keybox{{{tex_escape(keys)}}}\,{tex_escape(typed)}")
    labels["legend_hints"] = ", ".join(hints) + "."
    # JuliaMono is monospaced: the most characters make the widest box
    labels["legend_widest"] = tex_escape(max((prefix + key.physical.base for _, prefix in layers), key=len))
    return labels


def svg_width(content: str) -> float:
    return float(re.search(r'<svg [^>]*width="([\d.]+)"', content).group(1))


def write(layout: Layout, outdir: Path, font: Path = svg.DEFAULT_FONT) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    diagrams = svg.all_diagrams(layout, font, compact=True, option=True, chains=False)
    # the key that the legend explains, marked in its dead key's diagram
    diagrams[f"dead-{LEGEND_KEY[0]}.svg"] = svg.dead_key(
        layout, svg.Font(font), LEGEND_KEY[0], compact=True, option=True, marked=LEGEND_KEY[1]
    )
    for name, content in diagrams.items():
        (outdir / name).write_text(content, encoding="utf-8")
    legend_key = svg.single_key(layout, svg.Font(font), *LEGEND_KEY)
    (outdir / "legend-key.svg").write_text(legend_key, encoding="utf-8")
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
    legend_width = svg_width(legend_key) * scale  # the size of the keys in the diagrams
    texts = [ALTERNATIVE] + [description(layout, dead_id) for dead_id in layout.dead]
    rows = []
    for i, (name, text) in enumerate(zip(diagrams, texts, strict=True)):
        if name == f"dead-{LEGEND_KEY[0]}.svg":
            rows.append(r"\legendkey{legend-key.pdf}")
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
            legend_width=f"{legend_width:.3f}",
            **legend_labels(layout, *LEGEND_KEY),
            # the rows of legends, from the top of the key (see svg._draw_key)
            legend_top=f"{legend_width * 0.30:.3f}",
            legend_bottom=f"{legend_width * 0.70:.3f}",
            version=layout.version,
            rows="\n".join(rows),
            font_file=Path(font).name,
            font_dir=Path(font).resolve().parent.as_posix(),
        ),
        encoding="utf-8",
    )
