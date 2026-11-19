"""Physical keys of a US keyboard and their codes on each platform."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class PhysicalKey:
    name: str  # name in layout.toml: the character the key types on a US layout
    mac: int  # macOS virtual key code
    keyman: str  # Keyman virtual key
    vk: str  # Windows virtual key (C expression)
    base: str  # US layout, no modifiers
    shift: str  # US layout, Shift
    row: int  # keyboard row for diagrams (0 = number row)
    col: float  # horizontal position in key widths, from the left edge
    # Platform conventions that differ from the above (macOS):
    pc_base: str | None = None  # Windows/Linux, no modifiers
    pc_shift: str | None = None  # Windows/Linux, Shift
    mac_alternative: tuple = (None, None)  # macOS Option, Shift+Option defaults
    xkb: str = ""  # XKB key name (Linux), set below
    # Number pad keys: XKB keysyms with Num Lock off and on
    xkb_syms: tuple = ()


def _row(row: int, start: float, specs):
    return [
        PhysicalKey(name, mac, keyman, vk, base, shift, row, start + i)
        for i, (name, mac, keyman, vk, base, shift) in enumerate(specs)
    ]


# In keyboard order. "iso" is the extra key next to the left Shift on ISO
# keyboards; "space" is the space bar.
KEYS = [
    *_row(0, 0, [
        ("`", 50, "K_BKQUOTE", "VK_OEM_3", "`", "~"),
        ("1", 18, "K_1", "'1'", "1", "!"),
        ("2", 19, "K_2", "'2'", "2", "@"),
        ("3", 20, "K_3", "'3'", "3", "#"),
        ("4", 21, "K_4", "'4'", "4", "$"),
        ("5", 23, "K_5", "'5'", "5", "%"),
        ("6", 22, "K_6", "'6'", "6", "^"),
        ("7", 26, "K_7", "'7'", "7", "&"),
        ("8", 28, "K_8", "'8'", "8", "*"),
        ("9", 25, "K_9", "'9'", "9", "("),
        ("0", 29, "K_0", "'0'", "0", ")"),
        ("-", 27, "K_HYPHEN", "VK_OEM_MINUS", "-", "_"),
        ("=", 24, "K_EQUAL", "VK_OEM_PLUS", "=", "+"),
    ]),
    *_row(1, 1.5, [
        ("q", 12, "K_Q", "'Q'", "q", "Q"),
        ("w", 13, "K_W", "'W'", "w", "W"),
        ("e", 14, "K_E", "'E'", "e", "E"),
        ("r", 15, "K_R", "'R'", "r", "R"),
        ("t", 17, "K_T", "'T'", "t", "T"),
        ("y", 16, "K_Y", "'Y'", "y", "Y"),
        ("u", 32, "K_U", "'U'", "u", "U"),
        ("i", 34, "K_I", "'I'", "i", "I"),
        ("o", 31, "K_O", "'O'", "o", "O"),
        ("p", 35, "K_P", "'P'", "p", "P"),
        ("[", 33, "K_LBRKT", "VK_OEM_4", "[", "{"),
        ("]", 30, "K_RBRKT", "VK_OEM_6", "]", "}"),
        ("\\", 42, "K_BKSLASH", "VK_OEM_5", "\\", "|"),
    ]),
    *_row(2, 1.75, [
        ("a", 0, "K_A", "'A'", "a", "A"),
        ("s", 1, "K_S", "'S'", "s", "S"),
        ("d", 2, "K_D", "'D'", "d", "D"),
        ("f", 3, "K_F", "'F'", "f", "F"),
        ("g", 5, "K_G", "'G'", "g", "G"),
        ("h", 4, "K_H", "'H'", "h", "H"),
        ("j", 38, "K_J", "'J'", "j", "J"),
        ("k", 40, "K_K", "'K'", "k", "K"),
        ("l", 37, "K_L", "'L'", "l", "L"),
        (";", 41, "K_COLON", "VK_OEM_1", ";", ":"),
        ("'", 39, "K_QUOTE", "VK_OEM_7", "'", '"'),
    ]),
    *_row(3, 1.25, [
        ("iso", 10, "K_oE2", "VK_OEM_102", "§", "±"),
        ("z", 6, "K_Z", "'Z'", "z", "Z"),
        ("x", 7, "K_X", "'X'", "x", "X"),
        ("c", 8, "K_C", "'C'", "c", "C"),
        ("v", 9, "K_V", "'V'", "v", "V"),
        ("b", 11, "K_B", "'B'", "b", "B"),
        ("n", 45, "K_N", "'N'", "n", "N"),
        ("m", 46, "K_M", "'M'", "m", "M"),
        (",", 43, "K_COMMA", "VK_OEM_COMMA", ",", "<"),
        (".", 47, "K_PERIOD", "VK_OEM_PERIOD", ".", ">"),
        ("/", 44, "K_SLASH", "VK_OEM_2", "/", "?"),
    ]),
    PhysicalKey("space", 49, "K_SPACE", "VK_SPACE", " ", " ", 4, 4.0),
]

# The ISO key types § ± on macOS (also with Option, as in Apple's US layout)
# and \ | on Windows and Linux.
KEYS = [
    replace(k, pc_base="\\", pc_shift="|", mac_alternative=("§", "±")) if k.name == "iso" else k
    for k in KEYS
]

# XKB key names, in keyboard order within each row
_XKB_ROWS = {
    0: ["TLDE", *(f"AE{i:02}" for i in range(1, 13))],
    1: [*(f"AD{i:02}" for i in range(1, 13)), "BKSL"],
    2: [f"AC{i:02}" for i in range(1, 12)],
    3: ["LSGT", *(f"AB{i:02}" for i in range(1, 11))],
    4: ["SPCE"],
}
KEYS = [
    replace(k, xkb=_XKB_ROWS[k.row][[j for j in KEYS if j.row == k.row].index(k)]) for k in KEYS
]

KEYS_BY_NAME = {k.name: k for k in KEYS}


# The number pad (on full-size keyboards), as on a PC: name, macOS code,
# Keyman key, Windows virtual key, the character it types (with Num Lock
# on), XKB key name, XKB keysyms (Num Lock off, on), and diagram position
# (row, col) on a grid of the number pad. Enter, Num Lock (Clear on a Mac),
# and the Mac's = key are left alone.
KEYPAD = [
    PhysicalKey(name, mac, keyman, vk, char, char, row, col, xkb=xkb, xkb_syms=syms)
    for name, mac, keyman, vk, char, xkb, syms, row, col in [
        ("kp/", 75, "K_NPSLASH", "VK_DIVIDE", "/", "KPDV", ("KP_Divide", "KP_Divide"), 0, 1),
        ("kp*", 67, "K_NPSTAR", "VK_MULTIPLY", "*", "KPMU", ("KP_Multiply", "KP_Multiply"), 0, 2),
        ("kp-", 78, "K_NPMINUS", "VK_SUBTRACT", "-", "KPSU", ("KP_Subtract", "KP_Subtract"), 0, 3),
        ("kp7", 89, "K_NP7", "VK_NUMPAD7", "7", "KP7", ("KP_Home", "KP_7"), 1, 0),
        ("kp8", 91, "K_NP8", "VK_NUMPAD8", "8", "KP8", ("KP_Up", "KP_8"), 1, 1),
        ("kp9", 92, "K_NP9", "VK_NUMPAD9", "9", "KP9", ("KP_Prior", "KP_9"), 1, 2),
        ("kp+", 69, "K_NPPLUS", "VK_ADD", "+", "KPAD", ("KP_Add", "KP_Add"), 1, 3),
        ("kp4", 86, "K_NP4", "VK_NUMPAD4", "4", "KP4", ("KP_Left", "KP_4"), 2, 0),
        ("kp5", 87, "K_NP5", "VK_NUMPAD5", "5", "KP5", ("KP_Begin", "KP_5"), 2, 1),
        ("kp6", 88, "K_NP6", "VK_NUMPAD6", "6", "KP6", ("KP_Right", "KP_6"), 2, 2),
        ("kp1", 83, "K_NP1", "VK_NUMPAD1", "1", "KP1", ("KP_End", "KP_1"), 3, 0),
        ("kp2", 84, "K_NP2", "VK_NUMPAD2", "2", "KP2", ("KP_Down", "KP_2"), 3, 1),
        ("kp3", 85, "K_NP3", "VK_NUMPAD3", "3", "KP3", ("KP_Next", "KP_3"), 3, 2),
        ("kp0", 82, "K_NP0", "VK_NUMPAD0", "0", "KP0", ("KP_Insert", "KP_0"), 4, 0),
        ("kp.", 65, "K_NPDOT", "VK_DECIMAL", ".", "KPDL", ("KP_Delete", "KP_Decimal"), 4, 2),
    ]
]
KEYPAD_BY_CHAR = {k.base: k for k in KEYPAD}
