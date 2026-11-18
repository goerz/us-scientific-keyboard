"""The generated .keylayout behaves exactly like the reference layout.

tests/data/reference.keylayout is the last Ukelele-made version (3.0, with
the Caps Lock fix). Every key in every key map, in every dead-key state, and
every terminator must match. This proves layout.toml describes the layout
completely; when the layout changes on purpose, update the reference.
"""

from pathlib import Path

import pytest

from layoutgen import macos, model
from layoutgen.keylayout_reader import KeyLayout, Next

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def layouts(tmp_path_factory):
    layout = model.load(ROOT / "layout.toml")
    path = tmp_path_factory.mktemp("macos") / "generated.keylayout"
    path.write_text(macos.keylayout(layout), encoding="utf-8")
    return KeyLayout(ROOT / "tests" / "data" / "reference.keylayout"), KeyLayout(path)


def all_codes(*layouts):
    return sorted({code for kl in layouts for km in kl.keymaps.values() for code in km})


def state_mapping(ref, gen):
    """Pair up dead-key states of both layouts by the key that triggers them."""
    mapping = {}
    for index in ref.keymaps:
        for code in all_codes(ref, gen):
            r, g = ref.press(index, code), gen.press(index, code)
            if isinstance(r, Next) and isinstance(g, Next):
                assert mapping.setdefault(r.state, g.state) == g.state
    return mapping


def normalize(result, mapping):
    if isinstance(result, Next):
        return Next(mapping.get(result.state, "?" + result.state))
    return result


def test_same_keys_without_dead_keys(layouts):
    ref, gen = layouts
    mapping = state_mapping(ref, gen)
    mismatches = []
    for index in sorted(ref.keymaps):
        for code in all_codes(ref, gen):
            r = normalize(ref.press(index, code), mapping)
            g = gen.press(index, code)
            if r != g:
                mismatches.append((index, code, r, g))
    assert mismatches == []


def test_same_dead_keys(layouts):
    ref, gen = layouts
    mapping = state_mapping(ref, gen)
    assert len(mapping) == 9
    mismatches = []
    for ref_state, gen_state in mapping.items():
        for index in range(6):
            for code in all_codes(ref, gen):
                r = normalize(ref.press(index, code, ref_state), mapping)
                g = gen.press(index, code, gen_state)
                if r != g:
                    mismatches.append((ref_state, index, code, r, g))
    assert mismatches == []


def test_same_terminators(layouts):
    ref, gen = layouts
    mapping = state_mapping(ref, gen)
    for ref_state, gen_state in mapping.items():
        assert ref.terminators[ref_state] == gen.terminators[gen_state]
