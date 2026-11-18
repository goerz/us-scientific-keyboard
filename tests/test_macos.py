"""The generated .keylayout does exactly what layout.toml says.

The .keylayout is read back and every character key is checked in every
layer (including the derived Caps Lock layers), in every dead-key state, and
every dead key's terminator.
"""

from pathlib import Path

import pytest

from layoutgen import macos, model
from layoutgen.keylayout_reader import KeyLayout, Next, Output
from layoutgen.macos import MAP_LAYERS

ROOT = Path(__file__).resolve().parent.parent
LAYOUT = model.load(ROOT / "layout.toml")


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    path = tmp_path_factory.mktemp("macos") / "generated.keylayout"
    path.write_text(macos.keylayout(LAYOUT), encoding="utf-8")
    return KeyLayout(path)


def expected(binding, state):
    if binding is None:
        return None
    if isinstance(binding, model.Dead):
        return Next(binding.id) if state == "none" else None
    if state == "none":
        return Output(binding.text)
    result = LAYOUT.dead[state].map.get(binding.text)
    return None if result is None else Output(result)


@pytest.mark.parametrize("state", ["none", *LAYOUT.dead])
def test_keys(generated, state):
    mismatches = []
    for key in LAYOUT.keys:
        for index, layer in MAP_LAYERS.items():
            want = expected(LAYOUT.binding(key, layer), state)
            got = generated.press(index, key.physical.mac, state)
            if want != got:
                mismatches.append((key.name, layer, want, got))
    assert mismatches == []


def test_terminators(generated):
    for dead in LAYOUT.dead.values():
        assert generated.terminators[dead.id] == dead.symbol
