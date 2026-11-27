"""The generated Keyman rules do what layout.toml says.

Keyman's compiler doesn't run here, so this parses the generated rules and
evaluates them the way Keyman matches a keystroke: same modifiers, with
CAPS/NCAPS checked only when a rule mentions them.
"""

import re
from pathlib import Path

import pytest

from layoutgen import keyman, model

ROOT = Path(__file__).resolve().parent.parent
LAYOUT = model.load(ROOT / "layout.toml")
STATES = {dead.id: dead for dead in LAYOUT.states}

# layer -> (held modifiers, Caps Lock on)
LAYER_STATE = {
    "base": (frozenset(), False),
    "caps": (frozenset(), True),
    "shift": (frozenset({"SHIFT"}), False),
    "option": (frozenset({"RALT"}), False),
    "caps-option": (frozenset({"RALT"}), True),
    "shift-option": (frozenset({"SHIFT", "RALT"}), False),
}

RULE = re.compile(r"^(?:dk\((\w+)\) )?\+ \[([A-Z ]*?) ?(K_\w+)\] > (.*?)  c ")
WINDOWS_RULE = re.compile(r"^platform\('windows'\) \+ \[(K_\w+)\] > (.*?)  c ")


@pytest.fixture(scope="module")
def rules():
    parsed = []
    for line in keyman.kmn(LAYOUT).splitlines():
        m = RULE.match(line)
        if m:
            dead, mods, vkey, out = m.groups()
            mods = set(mods.split())
            caps = True if "CAPS" in mods else False if "NCAPS" in mods else None
            parsed.append((dead, frozenset(mods - {"CAPS", "NCAPS"}), caps, vkey, out.split()))
        elif line.startswith(("+", "dk(", "platform(")) and not WINDOWS_RULE.match(line):
            pytest.fail(f"unparsed rule: {line}")
    return parsed


def test_windows_numpad():
    """On Windows, the plain number pad keys have rules typing their own
    character (Keyman would swallow them otherwise; see keyman.py)."""
    got = {}
    for line in keyman.kmn(LAYOUT).splitlines():
        if m := WINDOWS_RULE.match(line):
            got[m[1]] = m[2].split()
    want = {key.physical.keyman: tokens(LAYOUT.binding(key, "base", "pc")) for key in LAYOUT.keypad}
    assert got == want


def press(rules, dead, vkey, layer):
    held, caps_on = LAYER_STATE[layer]
    matches = [
        out for d, mods, caps, k, out in rules
        if d == dead and k == vkey and mods == held and caps in (None, caps_on)
    ]
    assert len(matches) <= 1, (dead, vkey, layer)
    return matches[0] if matches else None


def tokens(binding):
    if isinstance(binding, model.Dead):
        return [f"dk({binding.id})"]
    return [f"U+{ord(c):04X}" for c in binding.text]


@pytest.mark.parametrize("dead", [None, *STATES])
def test_rules(rules, dead):
    mismatches = []
    for key in LAYOUT.keys + LAYOUT.keypad:
        for layer in LAYER_STATE:
            binding = LAYOUT.binding(key, layer, "pc")
            if binding is None:
                want = None
            elif dead is None and key in LAYOUT.keypad and layer in ("base", "caps"):
                want = None  # no rule: the number pad does what the system does
            elif dead is None:
                want = tokens(binding)
            elif isinstance(binding, model.Char) and binding.text in STATES[dead].map:
                want = tokens(model.Char(STATES[dead].map[binding.text]))
            elif chain := LAYOUT.chain(dead, binding):
                want = [f"dk({chain.id})"]
            else:
                want = tokens(model.Char(STATES[dead].symbol)) + tokens(binding)
            got = press(rules, dead, key.physical.keyman, layer)
            if want != got:
                mismatches.append((key.name, layer, want, got))
    assert mismatches == []


def test_no_comment_ends_in_backslash():
    assert not [line for line in keyman.kmn(LAYOUT).splitlines() if line.endswith("\\")]
