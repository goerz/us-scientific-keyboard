"""The generated Linux layout does what layout.toml says, in libxkbcommon.

This loads the generated symbols file and Compose file into the real
libxkbcommon (through ctypes), presses every key in every layer, alone and
after every dead key, and compares what comes out with layout.toml. It needs
libxkbcommon and xkeyboard-config (on Linux) and is skipped without them.
"""

import ctypes
import ctypes.util
import os
from pathlib import Path

import pytest

from layoutgen import linux, model

ROOT = Path(__file__).resolve().parent.parent
LAYOUT = model.load(ROOT / "layout.toml")


def _library():
    candidates = [ctypes.util.find_library("xkbcommon"), "libxkbcommon.so.0", "/opt/homebrew/lib/libxkbcommon.dylib"]
    for name in candidates:
        if name:
            try:
                return ctypes.CDLL(name)
            except OSError:
                pass
    return None


LIB = _library()
pytestmark = pytest.mark.skipif(LIB is None, reason="needs libxkbcommon")


class RuleNames(ctypes.Structure):
    _fields_ = [(f, ctypes.c_char_p) for f in ("rules", "model", "layout", "variant", "options")]


if LIB is not None:
    p, u32, i = ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int
    for name, res, args in [
        ("xkb_context_new", p, [i]),
        ("xkb_context_include_path_append", i, [p, ctypes.c_char_p]),
        ("xkb_context_include_path_append_default", i, [p]),
        ("xkb_keymap_new_from_names", p, [p, ctypes.POINTER(RuleNames), i]),
        ("xkb_keymap_key_by_name", u32, [p, ctypes.c_char_p]),
        ("xkb_state_new", p, [p]),
        ("xkb_state_update_key", i, [p, u32, i]),
        ("xkb_state_key_get_one_sym", u32, [p, u32]),
        ("xkb_state_key_get_utf8", i, [p, u32, ctypes.c_char_p, ctypes.c_size_t]),
        ("xkb_keysym_get_name", i, [u32, ctypes.c_char_p, ctypes.c_size_t]),
        ("xkb_compose_table_new_from_buffer", p, [p, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, i, i]),
        ("xkb_compose_state_new", p, [p, i]),
        ("xkb_compose_state_feed", i, [p, u32]),
        ("xkb_compose_state_reset", None, [p]),
        ("xkb_compose_state_get_status", i, [p]),
        ("xkb_compose_state_get_utf8", i, [p, ctypes.c_char_p, ctypes.c_size_t]),
    ]:
        getattr(LIB, name).restype = res
        getattr(LIB, name).argtypes = args

COMPOSING, COMPOSED, CANCELLED = 1, 2, 3
DOWN, UP = 1, 0


@pytest.fixture(scope="module")
def xkb(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("xkb")
    (tmp / "symbols").mkdir()
    (tmp / "symbols" / LAYOUT.id).write_text(linux.symbols(LAYOUT), encoding="utf-8")
    ctx = LIB.xkb_context_new(1)  # no default include paths
    assert LIB.xkb_context_include_path_append(ctx, str(tmp).encode())
    assert LIB.xkb_context_include_path_append_default(ctx)
    names = RuleNames(b"evdev", b"pc105", LAYOUT.id.encode(), b"", b"")
    keymap = LIB.xkb_keymap_new_from_names(ctx, ctypes.byref(names), 0)
    if not keymap:
        pytest.skip("libxkbcommon can't compile the keymap (is xkeyboard-config installed?)")
    return ctx, keymap


class Keyboard:
    def __init__(self, keymap):
        self.keymap = keymap
        self.state = LIB.xkb_state_new(keymap)

    def code(self, name):
        code = LIB.xkb_keymap_key_by_name(self.keymap, name.encode())
        assert code != 0xFFFFFFFF, name
        return code

    def press(self, xkb_name, layer):
        """(keysym, UTF-8 text) of the key in the layer."""
        mods = {"shift": ["LFSH"], "option": ["RALT"], "shift-option": ["LFSH", "RALT"],
                "caps-option": ["RALT"]}.get(layer, [])
        caps = layer in ("caps", "caps-option")
        if caps:
            self.tap("CAPS")
        for m in mods:
            LIB.xkb_state_update_key(self.state, self.code(m), DOWN)
        code = self.code(xkb_name)
        keysym = LIB.xkb_state_key_get_one_sym(self.state, code)
        buf = ctypes.create_string_buffer(64)
        LIB.xkb_state_key_get_utf8(self.state, code, buf, 64)
        for m in reversed(mods):
            LIB.xkb_state_update_key(self.state, self.code(m), UP)
        if caps:
            self.tap("CAPS")
        return keysym, buf.value.decode()

    def keypad(self, key, layer, numlock):
        """(keysym, text) of a number pad key, with Num Lock on or off."""
        if numlock:
            self.tap("NMLK")
        result = self.press(key.physical.xkb, layer)
        if numlock:
            self.tap("NMLK")
        return result

    def tap(self, name):
        LIB.xkb_state_update_key(self.state, self.code(name), DOWN)
        LIB.xkb_state_update_key(self.state, self.code(name), UP)


def keysym_name(keysym):
    buf = ctypes.create_string_buffer(64)
    LIB.xkb_keysym_get_name(keysym, buf, 64)
    return buf.value.decode()


def test_keys(xkb):
    kb = Keyboard(xkb[1])
    mismatches = []
    for key in LAYOUT.keys:
        for layer in linux.ALL_LAYERS:
            binding = LAYOUT.binding(key, layer, "pc")
            keysym, text = kb.press(key.physical.xkb, layer)
            if binding is None:
                want, got = None, (keysym, text)
                ok = keysym in (0, 0xFFFFFF) and text == ""  # NoSymbol, VoidSymbol
            elif isinstance(binding, model.Dead):
                want, got = linux.dead_keysyms(LAYOUT)[binding.id], keysym_name(keysym)
                ok = want == got
            else:
                want, got = binding.text, text
                ok = want == got
            if not ok:
                mismatches.append((key.name, layer, want, got))
    assert mismatches == []


def keypad_expected(key, layer, numlock):
    """Text of a number pad key: the alternative layer with AltGr, whatever
    Num Lock is; without AltGr, the digit with Num Lock on and nothing (a
    navigation key) with Num Lock off."""
    if layer in ("option", "shift-option"):
        binding = key.pc_layers[layer]
        return binding.text if binding is not None else ""
    if layer == "base":
        return key.physical.base if numlock or key.physical.xkb_syms[0] == key.physical.xkb_syms[1] else ""
    return None  # not checked


def test_keypad(xkb):
    kb = Keyboard(xkb[1])
    mismatches = []
    for key in LAYOUT.keypad:
        for numlock in (True, False):
            for layer in ("base", "option", "shift-option"):
                want = keypad_expected(key, layer, numlock)
                got = kb.keypad(key, layer, numlock)[1]
                if want != got:
                    mismatches.append((key.name, layer, numlock, want, got))
    assert mismatches == []


def compose_table(ctx, with_locale):
    text = linux.compose(LAYOUT)
    if with_locale:
        text = 'include "%L"\n' + text
    data = text.encode()
    table = LIB.xkb_compose_table_new_from_buffer(ctx, data, len(data), b"en_US.UTF-8", 1, 0)
    if not table:
        pytest.skip("libxkbcommon can't load the Compose file with the en_US.UTF-8 locale")
    return table


def expected(dead, binding):
    """What the dead key followed by `binding` types: the dead key's result,
    or else its symbol and what the key types (for a second dead key, its
    symbol). Keys outside the BMP have no sequences (see linux.py), so the
    dead key cancels."""
    if isinstance(binding, model.Dead):
        return dead.symbol + LAYOUT.dead[binding.id].symbol
    if ord(binding.text[0]) > 0xFFFF:
        return CANCELLED
    return dead.map.get(binding.text, dead.symbol + binding.text)


@pytest.mark.parametrize("with_locale",[False, True], ids=["alone", "after-%L"])
@pytest.mark.parametrize("dead_id", list(LAYOUT.dead))
def test_dead_keys(xkb, dead_id, with_locale):
    ctx, keymap = xkb
    kb = Keyboard(keymap)
    compose = LIB.xkb_compose_state_new(compose_table(ctx, with_locale), 0)
    dead = LAYOUT.dead[dead_id]
    trigger = next(
        (key, layer) for key in LAYOUT.keys for layer in model.LAYERS
        if LAYOUT.binding(key, layer, "pc") == model.Dead(dead_id)
    )
    mismatches = []
    for key in LAYOUT.keys:
        for layer in linux.ALL_LAYERS:
            binding = LAYOUT.binding(key, layer, "pc")
            if binding is None:
                continue
            LIB.xkb_compose_state_reset(compose)
            LIB.xkb_compose_state_feed(compose, kb.press(trigger[0].physical.xkb, trigger[1])[0])
            assert LIB.xkb_compose_state_get_status(compose) == COMPOSING
            LIB.xkb_compose_state_feed(compose, kb.press(key.physical.xkb, layer)[0])
            status = LIB.xkb_compose_state_get_status(compose)
            buf = ctypes.create_string_buffer(64)
            LIB.xkb_compose_state_get_utf8(compose, buf, 64)
            got = buf.value.decode() if status == COMPOSED else status
            want = expected(dead, binding)
            if want != got:
                mismatches.append((key.name, layer, want, got))
    for key in LAYOUT.keypad:  # with Num Lock on
        for layer in ("base", "option", "shift-option"):
            binding = key.pc_layers[layer]
            if binding is None:
                continue
            LIB.xkb_compose_state_reset(compose)
            LIB.xkb_compose_state_feed(compose, kb.press(trigger[0].physical.xkb, trigger[1])[0])
            LIB.xkb_compose_state_feed(compose, kb.keypad(key, layer, numlock=True)[0])
            status = LIB.xkb_compose_state_get_status(compose)
            buf = ctypes.create_string_buffer(64)
            LIB.xkb_compose_state_get_utf8(compose, buf, 64)
            got = buf.value.decode() if status == COMPOSED else status
            want = expected(dead, binding)
            if want != got:
                mismatches.append((key.name, layer, want, got))
    assert mismatches == []
