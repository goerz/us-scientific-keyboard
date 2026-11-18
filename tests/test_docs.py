"""README.md and the diagrams in docs/ are up to date with layout.toml.

If this fails after changing layout.toml or layoutgen, run `make docs`.
"""

import re
from pathlib import Path

import pytest

from layoutgen import docs, model, svg

ROOT = Path(__file__).resolve().parent.parent
LAYOUT = model.load(ROOT / "layout.toml")
FONT = ROOT / svg.DEFAULT_FONT


def test_readme_up_to_date():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert docs.update_readme(readme, LAYOUT) == readme, "run `make docs`"


@pytest.mark.skipif(not FONT.exists(), reason="run `make fonts`")
def test_diagrams_up_to_date():
    diagram_dir = ROOT / docs.DIAGRAM_DIR
    expected = svg.all_diagrams(LAYOUT, FONT)
    assert sorted(p.name for p in diagram_dir.glob("*.svg")) == sorted(expected), "run `make docs`"
    for name, content in expected.items():
        assert (diagram_dir / name).read_text(encoding="utf-8") == content, f"{name}: run `make docs`"


def test_readme_links():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    anchors = {docs.anchor(h) for h in re.findall(r"^#+ (.*)$", readme, re.M)}
    for target in re.findall(r"\]\(#([^)]+)\)", readme):
        assert target in anchors, target
    for path in re.findall(r"\]\((docs/[^)]+)\)", readme):
        assert (ROOT / path).exists(), path
