"""The installed native Windows layout does what layout.toml says, as far as
native Windows dead keys allow.

This loads the layout that install.ps1 installed with LoadKeyboardLayout and
asks Windows, through ToUnicodeEx, what each key types in each layer, alone
and after each dead key. The expectations are the same as in test_windows.py,
which simulates the generated tables. It runs on Windows with the layout
installed (CI does that) and is skipped elsewhere; with
REQUIRE_INSTALLED_LAYOUT=1, it fails instead of skipping.
"""

import ctypes
import itertools
import os
import sys

import pytest

from layoutgen import model
from test_windows import DEAD_CHAR, LAYOUT, expected

LAYERS = ("base", "caps", "shift", "option", "caps-option", "shift-option")

VK_CODES = {
    "VK_SPACE": 0x20, "VK_OEM_1": 0xBA, "VK_OEM_PLUS": 0xBB, "VK_OEM_COMMA": 0xBC,
    "VK_OEM_MINUS": 0xBD, "VK_OEM_PERIOD": 0xBE, "VK_OEM_2": 0xBF, "VK_OEM_3": 0xC0,
    "VK_OEM_4": 0xDB, "VK_OEM_5": 0xDC, "VK_OEM_6": 0xDD, "VK_OEM_7": 0xDE, "VK_OEM_102": 0xE2,
}
VK_SHIFT, VK_CONTROL, VK_MENU, VK_CAPITAL = 0x10, 0x11, 0x12, 0x14
VK_LSHIFT, VK_LCONTROL, VK_RMENU = 0xA0, 0xA2, 0xA5
SHIFT = (VK_SHIFT, VK_LSHIFT)
ALTGR = (VK_CONTROL, VK_LCONTROL, VK_MENU, VK_RMENU)  # AltGr is Ctrl+Alt to Windows
MODIFIERS = {
    "base": (), "caps": (), "shift": SHIFT,
    "option": ALTGR, "caps-option": ALTGR, "shift-option": SHIFT + ALTGR,
}
KLF_NOTELLSHELL = 0x80


def vk_code(vk: str) -> int:
    return ord(vk[1]) if vk.startswith("'") else VK_CODES[vk]


def unavailable(reason: str):
    if os.environ.get("REQUIRE_INSTALLED_LAYOUT") == "1":
        pytest.fail(reason)
    pytest.skip(reason)


def installed_klid():
    """The keyboard layout identifier that install.ps1 registered, or None."""
    import winreg

    dll = f"{LAYOUT.windows_dll}.dll".lower()
    path = r"SYSTEM\CurrentControlSet\Control\Keyboard Layouts"
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as layouts:
        for i in itertools.count():
            try:
                klid = winreg.EnumKey(layouts, i)
            except OSError:
                return None
            with winreg.OpenKey(layouts, klid) as key:
                try:
                    layout_file, _ = winreg.QueryValueEx(key, "Layout File")
                except OSError:
                    continue
            if layout_file.lower() == dll:
                return klid


class Keyboard:
    def __init__(self, klid):
        self.user32 = user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.LoadKeyboardLayoutW.restype = ctypes.c_void_p
        user32.LoadKeyboardLayoutW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint]
        user32.MapVirtualKeyExW.restype = ctypes.c_uint
        user32.MapVirtualKeyExW.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p]
        user32.ToUnicodeEx.restype = ctypes.c_int
        user32.ToUnicodeEx.argtypes = [
            ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_ubyte),
            ctypes.c_wchar_p, ctypes.c_int, ctypes.c_uint, ctypes.c_void_p,
        ]
        hkl = user32.LoadKeyboardLayoutW(klid, KLF_NOTELLSHELL)
        # On failure, Windows quietly loads the plain US layout (0x04090409)
        assert hkl and (hkl >> 16) & 0xFFFF != 0x0409, f"LoadKeyboardLayout({klid}) gave {hkl or 0:#x}"
        self.hkl = hkl

    def press(self, vk: str, layer: str):
        """("char", text) | ("dead", dead character) | None, as in test_windows.py"""
        code = vk_code(vk)
        state = (ctypes.c_ubyte * 256)()
        for modifier in MODIFIERS[layer]:
            state[modifier] = 0x80
        if layer.startswith("caps"):
            state[VK_CAPITAL] = 0x01  # toggled on
        scan = self.user32.MapVirtualKeyExW(code, 0, self.hkl)  # MAPVK_VK_TO_VSC
        buf = ctypes.create_unicode_buffer(16)
        n = self.user32.ToUnicodeEx(code, scan, state, buf, len(buf), 0, self.hkl)
        if n < 0:
            return ("dead", ctypes.wstring_at(buf, 1))
        if n == 0:
            return None
        return ("char", ctypes.wstring_at(buf, n))  # joins surrogate pairs

    def clear(self):
        """Drop a pending dead key from the keyboard state."""
        for _ in range(2):
            self.press("VK_SPACE", "base")


@pytest.fixture(scope="module")
def keyboard():
    if sys.platform != "win32":
        unavailable("needs Windows")
    klid = installed_klid()
    if klid is None:
        unavailable(f"{LAYOUT.windows_dll}.dll isn't installed (run install.ps1)")
    return Keyboard(klid)


def trigger(dead_id):
    """(virtual key, layer) of the key that types dead key `dead_id`."""
    for key, layer in itertools.product(LAYOUT.keys, LAYERS):
        binding = LAYOUT.binding(key, layer, "pc")
        if isinstance(binding, model.Dead) and binding.id == dead_id:
            return key.physical.vk, layer
    raise LookupError(dead_id)


@pytest.mark.parametrize("dead_id", [None, *DEAD_CHAR])
def test_keys(keyboard, dead_id):
    mismatches = []
    for key, layer in itertools.product(LAYOUT.keys, LAYERS):
        want = expected(LAYOUT.binding(key, layer, "pc"), dead_id)
        if want == "skip":
            continue
        keyboard.clear()
        if dead_id is not None:
            dead = keyboard.press(*trigger(dead_id))
            assert dead == ("dead", DEAD_CHAR[dead_id])
        got = keyboard.press(key.physical.vk, layer)
        if want != got:
            mismatches.append((key.name, layer, want, got))
    keyboard.clear()
    assert mismatches == []
