"""PDF cheat sheet: the keyboard diagrams on two pages (one sheet, printed
double-sided), six per page, each with its description beside it, and the
number pad by itself on a third page.

`write` puts the compact SVG diagrams and a LaTeX file into a directory; the
Makefile converts the SVGs to PDF (rsvg-convert) and runs LuaLaTeX.
"""

from pathlib import Path

from . import svg
from .model import Char, Dead, Layout

PER_PAGE = 6
# Glyphs that JuliaMono squeezes into one cell, so that they look like
# their narrow counterparts (⟶ like →, ⨁ like ⊕): set in Latin Modern Math.
WIDE = set("⟵⟶⟷⟸⟹⟺⟻⟼⨀⨁⨂⨃⨄∑∏∐⋂⋃⋀⋁")
DIAGRAM_WIDTH = "4.6in"  # six diagrams fit in the height of a letter page
NUMPAD_WIDTH = "4in"  # alone on its page

TEX = r"""\documentclass[10pt]{{article}}
\usepackage[letterpaper,margin=0.5in]{{geometry}}
\usepackage{{graphicx}}
\usepackage{{xcolor}}
\usepackage{{tikz}}
% a key in the fine print, drawn as a key cap, followed by what it gives
\newcommand{{\keycap}}[1]{{\tikz[baseline=(k.base)]\node[draw=black!45,fill=black!6,rounded corners=1.5pt,inner xsep=1.2pt,inner ysep=0.5pt,text height=5.3pt,text depth=1.5pt,font=\scriptsize](k){{#1}};}}
\usepackage{{fontspec}}
\setmainfont{{{font_file}}}[Path={font_dir}/,Ligatures=TeXOff]
\newfontfamily\widefont{{latinmodern-math.otf}}
\pagestyle{{empty}}
\setlength{{\parindent}}{{0pt}}
\newcommand{{\row}}[2]{{%
  \begin{{minipage}}[c]{{\dimexpr\linewidth-{width}-1em}}\raggedright #1\end{{minipage}}\hfill
  \begin{{minipage}}[c]{{{width}}}\includegraphics[width=\linewidth]{{#2}}\end{{minipage}}\par}}
\newcommand{{\numpadrow}}[2]{{%
  \begin{{minipage}}[c]{{\dimexpr\linewidth-{numpad_width}-1em}}\raggedright #1\end{{minipage}}\hfill
  \begin{{minipage}}[c]{{{numpad_width}}}\includegraphics[width=\linewidth]{{#2}}\end{{minipage}}\par}}
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
    r"\footnotesize Box drawing. Left: single lines. Right: with Shift, double lines."
    r" Num Lock doesn't matter. Not in the native Windows layout."
    r" After a dead key, the number pad works like the main keys."
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
    """(keys, result) of the dead key's entries that follow an Option key,
    which the diagram can't show, e.g. ("⌥⇧e", "∌")."""
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
            entries.append((option_keys[typed], text))
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
        def entry(keys, result):
            font = r"\widefont" if result in WIDE else ""
            return rf"\mbox{{\keycap{{{tex_escape(keys)}}}\,{{\small{font} {tex_escape(result)}}}}}"

        entries = r"\quad ".join(entry(keys, result) for keys, result in hidden)
        text += rf"\par\smallskip After Option keys:\par\setlength{{\lineskiplimit}}{{1.5pt}}\setlength{{\lineskip}}{{2.5pt}}{entries}"
    return text


def write(layout: Layout, outdir: Path, font: Path = svg.DEFAULT_FONT) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    diagrams = svg.all_diagrams(layout, font, compact=True)
    for name, content in diagrams.items():
        (outdir / name).write_text(content, encoding="utf-8")
    numpad = diagrams.pop("numpad.svg", None)
    texts = [ALTERNATIVE] + [description(layout, dead_id) for dead_id in layout.dead]
    rows = []
    for i, (name, text) in enumerate(zip(diagrams, texts, strict=True)):
        rows.append(rf"\row{{{text}}}{{{Path(name).stem}.pdf}}")
        rows.append(r"\newpage\vfill" if (i + 1) % PER_PAGE == 0 else r"\vfill")
    if numpad is not None:
        if rows[-1].startswith(r"\newpage"):
            rows.pop()
        # \null: TeX drops glue (\vfill) at the top of a page
        rows += [r"\newpage\null\vfill", rf"\numpadrow{{{NUMPAD}}}{{numpad.pdf}}", r"\vfill"]
    (outdir / "cheatsheet.tex").write_text(
        TEX.format(
            name=layout.name,
            width=DIAGRAM_WIDTH,
            numpad_width=NUMPAD_WIDTH,
            version=layout.version,
            rows="\n".join(rows),
            font_file=Path(font).name,
            font_dir=Path(font).resolve().parent.as_posix(),
        ),
        encoding="utf-8",
    )
