"""PDF cheat sheet: the keyboard diagrams on two pages (one sheet, printed
double-sided), six per page, each with its description beside it, and the
number pad by itself on a third page.

`write` puts the compact SVG diagrams and a LaTeX file into a directory; the
Makefile converts the SVGs to PDF (rsvg-convert) and runs LuaLaTeX.
"""

from pathlib import Path

from . import svg
from .model import Dead, Layout

PER_PAGE = 6
DIAGRAM_WIDTH = "4.6in"  # six diagrams fit in the height of a letter page
NUMPAD_WIDTH = "4in"  # alone on its page

TEX = r"""\documentclass[10pt]{{article}}
\usepackage[letterpaper,margin=0.5in]{{geometry}}
\usepackage{{graphicx}}
\usepackage{{fontspec}}
\setmainfont{{{font_file}}}[Path={font_dir}/,Ligatures=TeXOff]
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
