"""PDF cheat sheet: the keyboard diagrams on two pages (one sheet, printed
double-sided), five per page, each with its description beside it.

`write` puts the compact SVG diagrams and a LaTeX file into a directory; the
Makefile converts the SVGs to PDF (rsvg-convert) and runs LuaLaTeX.
"""

from pathlib import Path

from . import svg
from .model import Dead, Layout

PER_PAGE = 5

TEX = r"""\documentclass[10pt]{{article}}
\usepackage[letterpaper,margin=0.5in]{{geometry}}
\usepackage{{graphicx}}
\usepackage{{fontspec}}
\setmainfont{{{font_file}}}[Path={font_dir}/,Ligatures=TeXOff]
\pagestyle{{empty}}
\setlength{{\parindent}}{{0pt}}
\newcommand{{\row}}[2]{{%
  \begin{{minipage}}[c]{{\dimexpr\linewidth-5.45in-1em}}\raggedright #1\end{{minipage}}\hfill
  \begin{{minipage}}[c]{{5.45in}}\includegraphics[width=\linewidth]{{#2}}\end{{minipage}}\par}}
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
    return (
        rf"{{\large {tex_escape(dead.name)}}}\par\smallskip"
        rf" {tex_escape(trigger(layout, dead_id))}\par\smallskip"
        rf"\footnotesize {tex_escape(desc)}."
    )


def write(layout: Layout, outdir: Path, font: Path = svg.DEFAULT_FONT) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    diagrams = svg.all_diagrams(layout, font, compact=True)
    for name, content in diagrams.items():
        (outdir / name).write_text(content, encoding="utf-8")
    texts = [ALTERNATIVE] + [description(layout, dead_id) for dead_id in layout.dead]
    rows = []
    for i, (name, text) in enumerate(zip(diagrams, texts, strict=True)):
        rows.append(rf"\row{{{text}}}{{{Path(name).stem}.pdf}}")
        rows.append(r"\newpage\vfill" if (i + 1) % PER_PAGE == 0 else r"\vfill")
    (outdir / "cheatsheet.tex").write_text(
        TEX.format(
            name=layout.name,
            version=layout.version,
            rows="\n".join(rows),
            font_file=Path(font).name,
            font_dir=Path(font).resolve().parent.as_posix(),
        ),
        encoding="utf-8",
    )
