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

KEYS_BY_NAME = {k.name: k for k in KEYS}
