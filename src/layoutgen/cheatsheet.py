"""PDF cheat sheet: the keyboard diagrams, three per page.

`write` puts the SVG diagrams and a LaTeX file into a directory; the
Makefile converts the SVGs to PDF (rsvg-convert) and runs LuaLaTeX.
"""

from pathlib import Path

from . import svg
from .model import Layout

TEX = r"""\documentclass[11pt]{{article}}
\usepackage[letterpaper,margin=1.5cm]{{geometry}}
\usepackage{{graphicx}}
\usepackage{{fontspec}}
\setmainfont{{{font_file}}}[Path={font_dir}/]
\pagestyle{{empty}}
\setlength{{\parindent}}{{0pt}}
\begin{{document}}
{{\Large {name}}}\hfill version {version}\par
\vspace{{1ex}}
\small Alternative layer: Option on macOS, AltGr (right Alt) on Windows and Linux.
Each key shows what it types with Shift (top) and without (bottom).
Dead keys show their symbol on a dark badge: press and release the dead key,
then press another key. Space after a dead key types its symbol.\par
\vspace{{2ex}}
{diagrams}
\end{{document}}
"""


def write(layout: Layout, outdir: Path, font: Path = svg.DEFAULT_FONT) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    diagrams = svg.all_diagrams(layout, font)
    for name, content in diagrams.items():
        (outdir / name).write_text(content, encoding="utf-8")
    includes = []
    for i, name in enumerate(diagrams):
        includes.append(rf"\includegraphics[width=\linewidth]{{{Path(name).stem}.pdf}}\par")
        includes.append(r"\vspace{2ex}" if (i + 2) % 3 else r"\newpage")
    (outdir / "cheatsheet.tex").write_text(
        TEX.format(
            name=layout.name,
            version=layout.version,
            diagrams="\n".join(includes),
            font_file=Path(font).name,
            font_dir=Path(font).resolve().parent.as_posix(),
        ),
        encoding="utf-8",
    )
